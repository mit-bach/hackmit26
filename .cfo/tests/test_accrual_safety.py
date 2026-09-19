from accrual.ledger import create_accrual, get_open_accruals, reconcile_accrual
from accrual.trace import save_reconciliation, save_trace, vendor_slug
from accrual.models import AccrualDecision, JournalEntry, JournalLine
from accrual.report import format_vendor_trace
from accrual.store import build_estimate_context
from accrual.estimation import candidates_for
from accrual.validate import validate_agent_decision
from accrual.workflow import finalize_vendor_close


def _patch_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)


def _decision(**overrides) -> AccrualDecision:
    payload = {
        "vendor": "Aether Compute",
        "period": "2026-09",
        "status": "accrual_required",
        "estimated_amount": 11849.90,
        "confidence": 0.96,
        "estimation_method": "usage_run_rate",
        "evidence": ["September usage"],
        "reasoning_summary": "Usage times the committed rate.",
    }
    payload.update(overrides)
    return AccrualDecision(**payload)


def test_invoice_received_never_accrues(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        vendor="Orbit Analytics",
        status="accrual_required",
        estimated_amount=3100,
        estimation_method="contract_commitment",
        reasoning_summary="I tried to accrue a billed vendor.",
    )
    decision, trace = finalize_vendor_close("Orbit Analytics", "2026-09", raw, run_id="t1")
    assert decision.status == "no_accrual_needed"
    assert decision.journal_entry is None
    assert get_open_accruals(vendor="Orbit Analytics") == []
    assert "invoice_already_received" in trace.safety_rules_triggered


def test_unbilled_goods_receipt_cannot_be_skipped(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        vendor="Helios Hardware",
        status="no_accrual_needed",
        estimated_amount=None,
        estimation_method=None,
        reasoning_summary="I skipped a received shipment.",
    )
    decision, trace = finalize_vendor_close("Helios Hardware", "2026-09", raw, run_id="t2")
    assert decision.status == "accrual_required"
    assert decision.estimation_method == "goods_receipt"
    assert decision.estimated_amount == 6200
    assert decision.journal_entry is not None
    assert decision.journal_entry.debit.amount == decision.journal_entry.credit.amount
    assert "unbilled_goods_receipt" in trace.safety_rules_triggered


def test_no_candidate_is_insufficient_evidence(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        vendor="NewForge Consulting",
        status="insufficient_evidence",
        estimated_amount=None,
        estimation_method=None,
        reasoning_summary="No reliable incurred expense.",
    )
    decision, _trace = finalize_vendor_close("NewForge Consulting", "2026-09", raw, run_id="t3")
    assert decision.status == "insufficient_evidence"
    assert decision.journal_entry is None
    assert get_open_accruals(vendor="NewForge Consulting") == []


def test_draft_po_alone_does_not_accrue(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        vendor="NewForge Consulting",
        status="accrual_required",
        estimated_amount=4000,
        estimation_method="purchase_order",
        reasoning_summary="Draft PO is not evidence of incurred work.",
    )
    decision, trace = finalize_vendor_close("NewForge Consulting", "2026-09", raw, run_id="t4")
    assert decision.status == "insufficient_evidence"
    assert decision.journal_entry is None
    assert trace.validation_errors
    assert get_open_accruals(vendor="NewForge Consulting") == []


def test_amount_must_match_deterministic_candidate():
    context = build_estimate_context("Aether Compute", "2026-09")
    raw = _decision(estimated_amount=99999, estimation_method="usage_run_rate")
    errors = validate_agent_decision(raw, candidates_for(context))
    assert errors
    assert any("does not match" in item for item in errors)


def test_valid_usage_amount_is_accepted(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    decision, trace = finalize_vendor_close(
        "Aether Compute", "2026-09", _decision(), run_id="t5"
    )
    assert decision.status == "accrual_required"
    assert decision.estimated_amount == 11849.90
    assert decision.estimation_method == "usage_run_rate"
    assert decision.journal_entry is not None
    assert decision.journal_entry.debit.amount == decision.journal_entry.credit.amount
    assert trace.agent_selection.method == "usage_run_rate"
    assert trace.final_amount == 11849.90


def test_skip_cannot_include_a_journal():
    journal = JournalEntry(
        entry_id="JE-FAKE",
        period="2026-09",
        vendor="CleanSpace Facilities",
        memo="should not post",
        debit=JournalLine(account="Facilities Expense", amount=2400),
        credit=JournalLine(account="Accrued Expenses", amount=2400),
    )
    raw = _decision(
        vendor="CleanSpace Facilities",
        status="no_accrual_needed",
        estimated_amount=None,
        estimation_method=None,
        journal_entry=journal,
        reasoning_summary="Skip with a fake journal.",
    )
    errors = validate_agent_decision(raw, candidates_for(build_estimate_context("CleanSpace Facilities", "2026-09")))
    assert any("journal" in item.lower() for item in errors)


def test_negative_accrual_is_rejected(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    try:
        create_accrual(
            vendor="Aether Compute",
            period="2026-09",
            amount=-100,
            method="usage_run_rate",
            confidence=0.9,
            evidence=[],
            reasoning_summary="negative",
            expense_account="Cloud Infrastructure Expense",
        )
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("negative accrual must be rejected")


def test_duplicate_accrual_is_prevented(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    first = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11849.90,
        method="usage_run_rate",
        confidence=0.9,
        evidence=[],
        reasoning_summary="first",
        expense_account="Cloud Infrastructure Expense",
        trace_id="2026-09/t/aether_compute",
    )
    second = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=1,
        method="last_invoice",
        confidence=0.1,
        evidence=[],
        reasoning_summary="dup",
        expense_account="Cloud Infrastructure Expense",
    )
    assert first.accrual_id == second.accrual_id
    assert first.estimated_amount == 11849.90
    assert len(get_open_accruals(period="2026-09")) == 1


def test_reconciliation_cannot_happen_twice_and_keeps_trace_id(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    record = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11849.90,
        method="usage_run_rate",
        confidence=0.91,
        evidence=[],
        reasoning_summary="usage",
        expense_account="Cloud Infrastructure Expense",
        trace_id="2026-09/run1/aether_compute",
    )
    first = reconcile_accrual(record.accrual_id, "INV-AE-2026-09", 12100)
    assert first.trace_id == "2026-09/run1/aether_compute"
    assert first.estimation_error == 250.10
    assert first.absolute_error == 250.10
    assert first.percentage_error == 2.11
    try:
        reconcile_accrual(record.accrual_id, "INV-AE-2026-09", 12100)
    except ValueError as exc:
        assert "not open" in str(exc)
    else:
        raise AssertionError("second reconcile must fail")


def test_malformed_agent_output_fails_safely(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(estimated_amount=99999, estimation_method="usage_run_rate")
    decision, trace = finalize_vendor_close("Aether Compute", "2026-09", raw, run_id="bad")
    assert decision.status == "insufficient_evidence"
    assert decision.journal_entry is None
    assert decision.estimated_amount is None
    assert trace.validation_errors
    assert get_open_accruals(vendor="Aether Compute") == []


def test_cli_trace_shows_competing_aether_estimates_without_hardcoding_winner(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    posted, trace = finalize_vendor_close("Aether Compute", "2026-09", _decision(), run_id="cli")
    text = format_vendor_trace(trace)
    assert "Last invoice" in text
    assert "Recent average" in text
    assert "Trend projection" in text
    assert "Usage x contract rate" in text
    assert "$12,250.00" in text
    assert "$12,766.67" in text
    assert "$11,849.90" in text
    assert trace.agent_selection.method == "usage_run_rate"


def test_cli_uses_the_actual_selected_method(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        estimated_amount=12250,
        estimation_method="last_invoice",
        reasoning_summary="Copied last month.",
    )
    posted, trace = finalize_vendor_close("Aether Compute", "2026-09", raw, run_id="cli2")
    text = format_vendor_trace(trace)
    assert posted.estimation_method == "last_invoice"
    assert "Method: Last invoice" in text
    assert "Usage x contract rate" in text


def test_harbor_cli_shows_seasonal_versus_recent_average(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = _decision(
        vendor="Harbor Electric",
        estimated_amount=4650,
        estimation_method="seasonal_prior_year",
        reasoning_summary="Same month last year, not the summer peak.",
    )
    posted, trace = finalize_vendor_close("Harbor Electric", "2026-09", raw, run_id="cli3")
    text = format_vendor_trace(trace)
    assert "$7,733.33" in text
    assert "$4,650.00" in text
    assert "Prior-year same month" in text
    assert posted.estimation_method == "seasonal_prior_year"


def test_traces_use_stable_vendor_filenames(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    _decision_out, trace = finalize_vendor_close(
        "Aether Compute", "2026-09", _decision(), run_id="files"
    )
    path = save_trace(trace, tmp_path / "2026-09" / "files")
    assert path.name == "aether_compute.json"
    assert vendor_slug("Harbor Electric") == "harbor_electric"
    assert vendor_slug("Helios Hardware") == "helios_hardware"
    assert _decision_out.accrual_id
    record = get_open_accruals(vendor="Aether Compute")[0]
    result = reconcile_accrual(record.accrual_id, "INV-AE-2026-09", 12100)
    recon_path = save_reconciliation(result, tmp_path / "2026-09" / "files" / "reconcile")
    assert recon_path.name == "aether_compute.json"
    assert result.trace_id == trace.trace_id
