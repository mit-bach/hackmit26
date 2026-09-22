from __future__ import annotations

import json
from pathlib import Path

import pytest

from models import APCaseEvidence, Invoice, PurchaseOrder
from tools import (
    DATA_DIR,
    DataFileError,
    _read_json,
    collect_case_evidence,
    exception_types_for,
    invoice_amount_matches_po,
    invoice_po_amount_difference,
    load_duplicate_invoices,
    load_goods_receipt,
    load_invoice,
    load_policies,
    load_prior_cases,
    load_purchase_order,
    match_prior_cases,
    po_exists,
    po_is_approved,
    receipt_status_for,
    vendors_match,
    within_amount_tolerance,
)
from tools import vendor_alias_established
from workflow import _blocking_approve_violations, _needs_investigation
from models import PreparerRecommendation


def test_json_files_are_arrays():
    for name in [
        "invoices.json",
        "purchase_orders.json",
        "goods_receipts.json",
        "company_policies.json",
        "prior_cases.json",
    ]:
        payload = json.loads((DATA_DIR / name).read_text())
        assert isinstance(payload, list), name
        assert payload, name


def test_po_and_receipt_alignment():
    invoices = json.loads((DATA_DIR / "invoices.json").read_text())
    po_ids = {item["po_id"] for item in json.loads((DATA_DIR / "purchase_orders.json").read_text())}
    gr_ids = {item["po_id"] for item in json.loads((DATA_DIR / "goods_receipts.json").read_text())}

    no_po = [item["invoice_id"] for item in invoices if item["po_id"] is None]
    assert no_po == ["INV-016"]

    for item in invoices:
        if item["po_id"] is None:
            continue
        assert item["po_id"] in po_ids, item["invoice_id"]

    assert "PO-114" not in gr_ids
    assert load_goods_receipt("PO-114") is None
    assert receipt_status_for("PO-114") == "missing"


def test_exact_three_way_match():
    evidence = collect_case_evidence("INV-001")
    assert evidence.exception_types == []
    assert evidence.amount_matches
    assert evidence.vendor_exact_match
    assert evidence.po_exists
    assert evidence.po_approved
    assert evidence.receipt_status == "full"
    assert evidence.duplicate_detected is False
    assert invoice_po_amount_difference("INV-001") == 0


def test_amount_mismatch_within_policy():
    evidence = collect_case_evidence("INV-011")
    assert evidence.amount_difference == 250
    assert invoice_amount_matches_po("INV-011") is False
    assert evidence.within_amount_tolerance is True
    assert evidence.exception_types == ["small_amount_discrepancy"]


def test_material_amount_mismatch():
    evidence = collect_case_evidence("INV-013")
    assert evidence.amount_difference == 200
    assert evidence.within_amount_tolerance is False
    assert "material_amount_mismatch" in evidence.exception_types


def test_vendor_mismatch_is_not_exact_match():
    evidence = collect_case_evidence("INV-017")
    assert vendors_match("INV-017") is False
    assert evidence.vendor_exact_match is False
    assert evidence.vendors_are_similar is True
    assert evidence.exception_types == ["vendor_mismatch"]
    assert evidence.invoice.vendor == "Acme Supply Co."
    assert evidence.purchase_order.vendor == "Acme Supplies"
    assert vendor_alias_established(evidence) is True


def test_duplicate_detection():
    dups = load_duplicate_invoices("INV-010")
    assert [item.invoice_id for item in dups] == ["INV-018"]
    evidence = collect_case_evidence("INV-018")
    assert evidence.duplicate_detected is True
    assert evidence.duplicate_invoice_ids == ["INV-010"]
    assert "duplicate" in evidence.exception_types


def test_missing_po():
    evidence = collect_case_evidence("INV-016")
    assert evidence.invoice.po_id is None
    assert po_exists(None) is False
    assert evidence.po_exists is False
    assert evidence.exception_types == ["missing_po"]
    assert evidence.receipt_status == "not_applicable"


def test_missing_and_incomplete_receipts():
    assert receipt_status_for("PO-114") == "missing"
    assert collect_case_evidence("INV-014").exception_types == ["goods_not_received"]
    assert receipt_status_for("PO-115") == "not_received"
    assert collect_case_evidence("INV-015").exception_types == ["goods_not_received"]


def test_partial_receipt():
    evidence = collect_case_evidence("INV-019")
    assert evidence.receipt_status == "partial"
    assert evidence.goods_receipt.quantity_ordered == 10
    assert evidence.goods_receipt.quantity_received == 4
    assert evidence.exception_types == ["partial_receipt"]


def test_unapproved_po():
    assert po_is_approved("PO-120") is False
    evidence = collect_case_evidence("INV-020")
    assert evidence.po_approved is False
    assert "po_not_approved" in evidence.exception_types


def test_policies_and_prior_cases_load():
    policies = {item.policy_id: item for item in load_policies()}
    assert policies["P-002"].action == "must_hold"
    assert policies["P-009"].conditions["max_percent_variance"] == 0.03
    cases = match_prior_cases(exception_type="vendor_mismatch", vendor="Acme Supply Co.")
    assert [item.case_id for item in cases] == ["CASE-001"]


def test_unknown_invoice():
    assert load_invoice("INV-999") is None
    evidence = collect_case_evidence("INV-999")
    assert evidence.exception_types == ["unknown_invoice"]


def test_malformed_json(tmp_path: Path):
    bad = tmp_path / "broken.json"
    bad.write_text("{not json")
    with pytest.raises(DataFileError):
        _read_json(bad)


def test_clean_case_skips_investigator():
    evidence = collect_case_evidence("INV-001")
    preparer = PreparerRecommendation(
        invoice_id="INV-001",
        recommendation="APPROVE",
        confidence=0.9,
        reasons=["clean"],
        evidence_used=["INV-001"],
        exception_types=[],
    )
    assert _needs_investigation(evidence, preparer) is False


def test_exception_case_runs_investigator():
    evidence = collect_case_evidence("INV-017")
    preparer = PreparerRecommendation(
        invoice_id="INV-017",
        recommendation="INVESTIGATE",
        confidence=0.7,
        reasons=["vendor mismatch"],
        evidence_used=["INV-017"],
        exception_types=["vendor_mismatch"],
    )
    assert _needs_investigation(evidence, preparer) is True


def test_duplicate_cannot_be_approved():
    evidence = collect_case_evidence("INV-018")
    assert any("P-002" in item for item in _blocking_approve_violations(evidence))


def test_missing_po_cannot_be_approved():
    evidence = collect_case_evidence("INV-016")
    assert any("P-008" in item for item in _blocking_approve_violations(evidence))


def test_unknown_vendor_without_prior_case_is_blocked():
    evidence = APCaseEvidence(
        invoice_id="INV-FAKE",
        invoice=Invoice(
            invoice_id="INV-FAKE",
            vendor="Mystery Vendor LLC",
            po_id="PO-FAKE",
            amount=100,
            invoice_date="2026-09-01",
            due_date="2026-09-30",
            vendor_invoice_number="X-1",
        ),
        purchase_order=PurchaseOrder(
            po_id="PO-FAKE",
            vendor="Mystery Vendor",
            authorized_amount=100,
            status="approved",
        ),
        vendor_exact_match=False,
        po_exists=True,
        po_approved=True,
        receipt_status="full",
        exception_types=["vendor_mismatch"],
    )
    assert vendor_alias_established(evidence) is False
    assert any("P-006" in item for item in _blocking_approve_violations(evidence))


def test_acme_alias_is_not_blocked_by_safety_net():
    evidence = collect_case_evidence("INV-017")
    assert vendor_alias_established(evidence) is True
    assert not any("P-006" in item for item in _blocking_approve_violations(evidence))
