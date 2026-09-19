from __future__ import annotations

from invoice_ingestion.identity import canonical_invoice_key, identity_keys
from invoice_ingestion.sources import run_document_source, run_edi_source, run_erp_source, run_procurement_source
from invoice_ingestion.workflow import ingest_invoices
from tools import all_invoices, load_invoice


def _by_number(report, number: str):
    return next(item for item in report.canonical_invoices if item.vendor_invoice_number == number)


def test_canonical_invoice_key_is_source_independent():
    from invoice_ingestion.models import InvoiceCandidate

    email = InvoiceCandidate(
        source_type="email",
        source_id="MSG-E01",
        vendor="Amazon Web Services",
        vendor_invoice_number="INV-9001",
    )
    portal = InvoiceCandidate(
        source_type="vendor_portal",
        source_id="VP-AWS-9001",
        vendor="Amazon Web Services",
        vendor_invoice_number="inv-9001",
    )
    assert canonical_invoice_key(email) == canonical_invoice_key(portal)
    assert canonical_invoice_key(email) is not None
    assert canonical_invoice_key(email).endswith(":INV-9001")
    keys = identity_keys(email)
    assert any(item.startswith("invoice:") for item in keys)
    assert any(item.startswith("source:email:") for item in keys)


def test_aws_email_portal_card_is_one_canonical():
    report = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    aws = _by_number(report, "INV-9001")
    assert {ref.source_type for ref in aws.sources} == {"email", "vendor_portal", "bank_card"}
    assert [item.vendor_invoice_number for item in report.canonical_invoices].count("INV-9001") == 1
    assert aws.forwarded_to_ap is True
    assert report.duplicates_removed == 2
    aws_traces = [
        item
        for item in report.traces
        if item.canonical_id == aws.canonical_id and item.candidate_produced
    ]
    statuses = [item.status for item in aws_traces]
    assert statuses.count("new_invoice") == 1
    assert statuses.count("duplicate_within_run") == 2


def test_repeat_ingestion_creates_zero_new_payables():
    first = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    second = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=False)

    assert [item.vendor_invoice_number for item in first.canonical_invoices].count("INV-9001") == 1
    assert [item.vendor_invoice_number for item in second.canonical_invoices].count("INV-9001") == 1
    assert second.new_canonical_count == 0
    assert second.new_ap_handoffs == 0
    assert all(item.forwarded_to_ap is False for item in second.canonical_invoices)

    aws = _by_number(second, "INV-9001")
    assert {ref.source_type for ref in aws.sources} == {"email", "vendor_portal", "bank_card"}
    first_aws = _by_number(first, "INV-9001")
    assert aws.canonical_id == first_aws.canonical_id


def test_helios_is_forwarded_once_across_runs():
    first = ingest_invoices("2026-09", sources=["document"], forward_to_ap=True, reset_overlay=True)
    helios = _by_number(first, "HEL-INV-6200")
    assert helios.forwarded_to_ap is True
    canonical_id = helios.canonical_id
    assert load_invoice(canonical_id) is not None

    second = ingest_invoices("2026-09", sources=["document"], forward_to_ap=True, reset_overlay=False)
    again = _by_number(second, "HEL-INV-6200")
    assert again.canonical_id == canonical_id
    assert again.forwarded_to_ap is False
    assert second.new_ap_handoffs == 0
    overlay = [item for item in all_invoices() if item.vendor_invoice_number == "HEL-INV-6200"]
    assert len(overlay) == 1


def test_acme_maps_to_existing_ap_and_never_creates_a_payable():
    first = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    acme = _by_number(first, "ACM-2026-4410")
    assert acme.already_in_ap_inbox is True
    assert acme.existing_ap_invoice_id == "INV-001"
    assert acme.forwarded_to_ap is False

    second = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=False)
    acme2 = _by_number(second, "ACM-2026-4410")
    assert acme2.existing_ap_invoice_id == "INV-001"
    assert acme2.forwarded_to_ap is False
    payables = [
        item
        for item in all_invoices()
        if item.vendor_invoice_number == "ACM-2026-4410"
    ]
    assert [item.invoice_id for item in payables] == ["INV-001"]


def test_source_replay_does_not_create_a_new_canonical():
    first = ingest_invoices("2026-09", sources=["email"], forward_to_ap=True, reset_overlay=True)
    aws = _by_number(first, "INV-9001")
    replay = ingest_invoices("2026-09", sources=["email"], forward_to_ap=True, reset_overlay=False)
    aws2 = _by_number(replay, "INV-9001")
    assert aws2.canonical_id == aws.canonical_id
    assert replay.new_canonical_count == 0
    email_traces = [item for item in replay.traces if item.source_id == "MSG-E01" and item.candidate_produced]
    assert email_traces
    assert email_traces[0].status == "source_replay"


def test_document_hash_replay_is_one_canonical():
    first = ingest_invoices("2026-09", sources=["document"], forward_to_ap=True, reset_overlay=True)
    helios = _by_number(first, "HEL-INV-6200")
    assert helios.document_hash
    second = ingest_invoices("2026-09", sources=["document"], forward_to_ap=True, reset_overlay=False)
    again = _by_number(second, "HEL-INV-6200")
    assert again.canonical_id == helios.canonical_id
    assert again.document_hash == helios.document_hash
    assert second.new_canonical_count == 0


def test_new_source_adds_provenance_without_new_payable():
    first = ingest_invoices("2026-09", sources=["email"], forward_to_ap=True, reset_overlay=True)
    aws = _by_number(first, "INV-9001")
    assert {ref.source_type for ref in aws.sources} == {"email"}
    assert aws.forwarded_to_ap is True
    canonical_id = aws.canonical_id

    second = ingest_invoices(
        "2026-09", sources=["vendor_portal"], forward_to_ap=True, reset_overlay=False
    )
    aws2 = _by_number(second, "INV-9001")
    assert aws2.canonical_id == canonical_id
    assert {ref.source_type for ref in aws2.sources} == {"email", "vendor_portal"}
    assert aws2.forwarded_to_ap is False
    assert aws2.provenance_added is True
    aws_payables = [item for item in all_invoices() if item.vendor_invoice_number == "INV-9001"]
    assert [item.invoice_id for item in aws_payables] == [canonical_id]
    portal_traces = [
        item for item in second.traces if item.source_id == "VP-AWS-9001" and item.candidate_produced
    ]
    assert portal_traces
    assert portal_traces[0].status == "new_provenance"
    assert portal_traces[0].ap_handoff is False


def test_wework_never_becomes_an_invoice_on_repeat():
    first = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    second = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=False)
    for report in (first, second):
        assert all("WEWORK" not in (item.vendor or "").upper() for item in report.canonical_invoices)
        missing = next(item for item in report.discovery if item.transaction_id == "CC-4412")
        assert missing.status == "invoice_missing"
        assert missing.candidate is None
        traces = [item for item in report.traces if item.source_id == "CC-4412"]
        assert traces
        assert traces[0].status == "missing_supporting_documentation"
    assert load_invoice("CC-4412") is None


def test_structured_parsers_are_deterministic_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    erp = run_erp_source("2026-09", use_llm=True)
    procurement = run_procurement_source("2026-09", use_llm=True)
    edi = run_edi_source("2026-09", use_llm=True)
    assert erp.extraction_method == "deterministic"
    assert procurement.extraction_method == "deterministic"
    assert edi.extraction_method == "deterministic"
    assert {item.vendor_invoice_number for item in erp.candidates} == {"ACM-2026-4410", "SNOW-ERP-SEP26"}
    assert procurement.candidates[0].vendor_invoice_number == "OD-COUPA-SEP26"
    assert edi.candidates[0].amount == 2400.0


def test_scanned_document_runner_is_unstructured():
    run = run_document_source("2026-09")
    assert run.extraction_method == "unstructured"
    assert run.candidates[0].vendor_invoice_number == "HEL-INV-6200"
