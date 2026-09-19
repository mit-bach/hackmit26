from __future__ import annotations

from invoice_ingestion.edi import parse_edi_document, parse_ubl_xml
from invoice_ingestion.sources import (
    run_bank_card_source,
    run_document_source,
    run_edi_source,
    run_email_source,
    run_employee_source,
    run_erp_source,
    run_procurement_source,
    run_vendor_portal_source,
)
from invoice_ingestion.store import get_email
from invoice_ingestion.validate import validate_candidate
from invoice_ingestion.workflow import ingest_invoices
from tools import collect_case_evidence, load_invoice


def _by_number(report, number: str):
    return next(
        item
        for item in report.canonical_invoices
        if item.vendor_invoice_number == number
    )


def test_email_extracts_invoices_and_rejects_non_invoices():
    run = run_email_source("2026-09")
    assert run.records_checked == 4
    numbers = {item.vendor_invoice_number for item in run.candidates}
    assert numbers == {"INV-9001", "QL-4412"}
    classes = {item.classification: item.reason for item in run.traces}
    assert "marketing" in classes
    assert "quote" in classes
    assert get_email("MSG-E01")["from"] == "no-reply@amazon.com"


def test_erp_normalizes_netsuite_and_sap_records():
    run = run_erp_source("2026-09")
    assert run.records_checked == 2
    assert run.invoices_found == 2
    numbers = {item.vendor_invoice_number: item.vendor for item in run.candidates}
    assert numbers["ACM-2026-4410"] == "Acme Supplies"
    assert numbers["SNOW-ERP-SEP26"] == "Snowflake"


def test_procurement_keeps_po_context_and_rejects_requests():
    run = run_procurement_source("2026-09")
    assert run.records_checked == 2
    assert run.invoices_found == 1
    invoice = run.candidates[0]
    assert invoice.vendor == "Office Depot"
    assert invoice.po_id == "PO-104"
    assert invoice.source_context["purchase_request"] == "PR-4410"
    assert invoice.source_context["receiving"]["receipt_id"] == "GR-104"
    assert any(item.classification != "invoice" for item in run.traces)


def test_vendor_portal_extracts_invoices_not_statements():
    run = run_vendor_portal_source("2026-09")
    assert run.records_checked == 3
    numbers = {item.vendor_invoice_number for item in run.candidates}
    assert numbers == {"INV-9001", "MS-AZURE-926-441"}
    assert any(item.classification == "statement" for item in run.traces)


def test_employee_accepts_invoice_and_rejects_receipt():
    run = run_employee_source("2026-09")
    assert run.records_checked == 2
    assert run.invoices_found == 1
    assert run.candidates[0].vendor_invoice_number == "FIG-EMP-SEP26"
    assert any(item.classification == "receipt" for item in run.traces)


def test_document_agent_extracts_scanned_helios_invoice():
    run = run_document_source("2026-09")
    assert run.records_checked == 1
    invoice = run.candidates[0]
    assert invoice.vendor == "Helios Hardware"
    assert invoice.vendor_invoice_number == "HEL-INV-6200"
    assert invoice.po_id == "PO-201"
    assert invoice.amount == 6200
    assert "page 1" in invoice.page_refs
    assert "page 2" in invoice.page_refs


def test_edi_parses_structured_810_without_llm():
    run = run_edi_source("2026-09")
    assert run.records_checked == 1
    invoice = run.candidates[0]
    assert invoice.vendor == "CleanSpace Facilities"
    assert invoice.vendor_invoice_number == "CS-2026-09-810"
    assert invoice.amount == 2400.0
    assert invoice.classification_reason.startswith("Structured EDI")


def test_ubl_xml_parser():
    xml = """
    <Invoice>
      <ID>UBL-100</ID>
      <IssueDate>2026-09-01</IssueDate>
      <DueDate>2026-09-30</DueDate>
      <DocumentCurrencyCode>USD</DocumentCurrencyCode>
      <AccountingSupplierParty><RegistrationName>GitHub</RegistrationName></AccountingSupplierParty>
      <LegalMonetaryTotal>
        <TaxExclusiveAmount>100.00</TaxExclusiveAmount>
        <TaxAmount>0.00</TaxAmount>
        <PayableAmount>100.00</PayableAmount>
      </LegalMonetaryTotal>
    </Invoice>
    """
    parsed = parse_ubl_xml(xml, source_id="UBL-TEST")
    assert parsed.vendor == "GitHub"
    assert parsed.vendor_invoice_number == "UBL-100"
    assert parsed.amount == 100.0


def test_bank_recovers_documented_charge_only():
    run = run_bank_card_source("2026-09")
    assert run.records_checked == 2
    assert run.invoices_found == 1
    assert run.missing_documentation == 1
    assert run.candidates[0].vendor_invoice_number == "INV-9001"
    missing = next(item for item in run.discovery if item.transaction_id == "CC-4412")
    assert missing.status == "invoice_missing"
    assert missing.candidate is None


def test_cross_source_aws_invoice_is_deduped():
    report = ingest_invoices("2026-09", forward_to_ap=False)
    aws = _by_number(report, "INV-9001")
    source_types = {ref.source_type for ref in aws.sources}
    assert source_types == {"email", "vendor_portal", "bank_card"}
    assert report.duplicates_removed == 2
    numbers = [item.vendor_invoice_number for item in report.canonical_invoices]
    assert numbers.count("INV-9001") == 1


def test_card_charge_without_docs_is_not_a_payable():
    report = ingest_invoices("2026-09", forward_to_ap=True)
    numbers = {item.vendor_invoice_number for item in report.canonical_invoices}
    assert "INV-9001" in numbers
    assert all("WEWORK" not in (item.vendor or "").upper() for item in report.canonical_invoices)
    assert load_invoice("CC-4412") is None


def test_broken_source_does_not_stop_others(monkeypatch):
    def boom(period: str, use_llm: bool = False):
        raise RuntimeError("source unavailable")

    from invoice_ingestion.workflow import SOURCE_RUNNERS

    monkeypatch.setitem(SOURCE_RUNNERS, "email", boom)
    report = ingest_invoices("2026-09", sources=["email", "edi"], forward_to_ap=False)
    assert any("email" in item for item in report.errors)
    assert any(item.vendor_invoice_number == "CS-2026-09-810" for item in report.canonical_invoices)


def test_forwarded_canonical_invoices_are_visible_to_ap():
    report = ingest_invoices("2026-09", forward_to_ap=True)
    helios = _by_number(report, "HEL-INV-6200")
    assert helios.forwarded_to_ap is True
    evidence = collect_case_evidence(helios.canonical_id)
    assert evidence.exception_types == []
    assert evidence.amount_matches
    assert evidence.receipt_status == "full"

    acme = _by_number(report, "ACM-2026-4410")
    assert acme.already_in_ap_inbox is True
    assert acme.existing_ap_invoice_id == "INV-001"
    assert acme.forwarded_to_ap is False

    aws = _by_number(report, "INV-9001")
    assert aws.forwarded_to_ap is True
    assert load_invoice(aws.canonical_id) is not None


def test_existing_ap_inbox_is_unchanged():
    ingest_invoices("2026-09", forward_to_ap=True)
    invoice = load_invoice("INV-001")
    assert invoice is not None
    assert invoice.vendor == "Acme Supplies"
    assert invoice.vendor_invoice_number == "ACM-2026-4410"


def test_parse_edi_document_from_fixture():
    from invoice_ingestion.store import get_edi_document

    parsed = parse_edi_document(get_edi_document("EDI-810-CS-09"))
    assert parsed.amount == 2400.0
    assert validate_candidate(parsed).status == "valid"


def test_unknown_vendor_is_flagged_but_can_be_canonical():
    report = ingest_invoices("2026-09", forward_to_ap=True)
    quokka = _by_number(report, "QL-4412")
    assert any(item.startswith("unknown_vendor") for item in quokka.warnings)
    assert quokka.validation_status == "valid"
    assert quokka.forwarded_to_ap is True
