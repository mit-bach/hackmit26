from accrual.discovery import discover_period, discover_vendor, missing_bill_candidates
from accrual.models import AccrualDecision, DiscoveryResult
from accrual.store import list_expected_vendors
from accrual.workflow import finalize_vendor_close, run_accrual_workflow
from tools import collect_case_evidence, load_invoice


def _by_name(period: str = "2026-09"):
    return {item.vendor: item for item in discover_period(period).results}


def _patch_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)


def test_monthly_missing_invoice_is_discovered():
    result = discover_vendor("Aether Compute", "2026-09")
    assert result.expense_expected is True
    assert result.invoice_received is False
    assert result.missing_bill_candidate is True
    assert result.expectation_confidence >= 0.9
    assert any(signal.type == "monthly_cadence" for signal in result.signals)


def test_monthly_received_invoice_is_not_missing():
    result = discover_vendor("Amazon Web Services", "2026-09")
    assert result.expense_expected is True
    assert result.invoice_received is True
    assert result.missing_bill_candidate is False
    assert "INV-002" in result.current_invoice_ids


def test_quarterly_vendor_only_in_billing_month():
    september = discover_vendor("Pulse Recruiting", "2026-09")
    august = discover_vendor("Pulse Recruiting", "2026-08")
    assert september.expense_expected is True
    assert september.missing_bill_candidate is True
    assert august.expense_expected is False
    assert august.missing_bill_candidate is False


def test_contract_retainer_is_discovered():
    result = discover_vendor("Lindholm & Ruiz LLP", "2026-09")
    assert result.expense_expected is True
    assert result.missing_bill_candidate is True
    assert any(signal.type == "recurring_contract" for signal in result.signals)
    assert result.expectation_confidence >= 0.95


def test_goods_receipt_without_invoice_is_discovered():
    result = discover_vendor("Helios Hardware", "2026-09")
    assert result.expense_expected is True
    assert result.missing_bill_candidate is True
    assert result.expectation_confidence == 1.0
    assert any(signal.type == "goods_receipt" for signal in result.signals)


def test_isolated_old_invoice_is_not_recurring():
    result = discover_vendor("Brightline Catering", "2026-09")
    assert result.expense_expected is False
    assert result.invoice_received is False
    assert result.missing_bill_candidate is False
    assert result.expectation_confidence <= 0.1
    assert any(signal.type == "isolated_invoice" for signal in result.signals)
    assert "Brightline Catering" not in _by_name()
    assert "Brightline Catering" not in {item.vendor for item in list_expected_vendors("2026-09")}


def test_draft_po_does_not_get_high_expectation_confidence():
    result = discover_vendor("NewForge Consulting", "2026-09")
    assert result.expectation_confidence < 0.5
    assert any(signal.type == "draft_purchase_order" for signal in result.signals)


def test_expectation_and_estimate_confidence_are_separate(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    found = discover_vendor("Aether Compute", "2026-09")
    assert "estimate_confidence" not in DiscoveryResult.model_fields
    assert found.expectation_confidence >= 0.9
    raw = AccrualDecision(
        vendor="Aether Compute",
        period="2026-09",
        status="accrual_required",
        estimated_amount=11849.90,
        confidence=0.91,
        estimation_method="usage_run_rate",
        evidence=["September usage"],
        reasoning_summary="Usage times the committed rate.",
    )
    decision, trace = finalize_vendor_close(
        "Aether Compute", "2026-09", raw, run_id="sep", discovery=found
    )
    assert trace.expectation_confidence == found.expectation_confidence
    assert trace.estimate_confidence == decision.confidence
    assert decision.discovery_trace_id == found.discovery_trace_id
    assert trace.discovery_trace_id == found.discovery_trace_id


def test_discovery_feeds_existing_accrual_workflow(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    report = run_accrual_workflow(
        "2026-09",
        vendors=["Amazon Web Services", "Orbit Analytics"],
        reset=True,
        run_id="disc-feed",
    )
    assert report.discovery is not None
    missing = {item.vendor for item in missing_bill_candidates(report.discovery)}
    assert missing == set()
    assert report.accruals_created == []
    assert {item.vendor for item in report.no_accrual_needed} == {
        "Amazon Web Services",
        "Orbit Analytics",
    }
    assert all(item.discovery_trace_id for item in report.no_accrual_needed)
    discovered = {
        item.vendor
        for item in discover_period("2026-09").results
        if item.expense_expected or item.missing_bill_candidate or item.invoice_received
    }
    assert discovered == {item.vendor for item in list_expected_vendors("2026-09")}
    assert "Acme Supplies" not in discovered


def test_ap_invoice_lookup_is_unchanged():
    invoice = load_invoice("INV-001")
    assert invoice is not None
    assert invoice.vendor == "Acme Supplies"
    assert collect_case_evidence("INV-001").exception_types == []
