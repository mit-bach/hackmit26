import inspect

from accrual.diagnostics import method_diagnostics
from accrual.models import AccrualDecision, ComparisonRecord, ComparisonReport
from accrual.policy import METHOD_PREFERENCE, copy_context, preferred_candidate
from accrual.report import format_compare
from accrual.store import build_estimate_context
from accrual.workflow import finalize_vendor_close
from tools import collect_case_evidence, load_invoice


def _patch_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)


def test_policy_source_has_no_demo_vendor_names():
    from pathlib import Path

    source = Path(inspect.getfile(preferred_candidate)).read_text()
    for name in ("Aether", "Harbor", "Helios", "NewForge", "Lindholm", "Pulse"):
        assert name not in source
    assert "usage_run_rate" in METHOD_PREFERENCE


def test_renamed_metered_vendor_still_prefers_usage():
    original = build_estimate_context("Aether Compute", "2026-09")
    renamed = copy_context(original, "Nebula Cloud")
    chosen = preferred_candidate(renamed)
    assert chosen is not None
    assert chosen.method == "usage_run_rate"
    assert chosen.amount == preferred_candidate(original).amount


def test_renamed_seasonal_vendor_still_prefers_prior_year():
    original = build_estimate_context("Harbor Electric", "2026-09")
    renamed = copy_context(original, "Coastal Power")
    chosen = preferred_candidate(renamed)
    assert chosen is not None
    assert chosen.method == "seasonal_prior_year"
    assert chosen.amount == 4650


def test_contract_outranks_recent_average():
    context = build_estimate_context("Lindholm & Ruiz LLP", "2026-09")
    chosen = preferred_candidate(copy_context(context, "North Counsel LLP"))
    assert chosen is not None
    assert chosen.method == "contract_commitment"
    assert chosen.amount == 8500


def test_disagreement_is_preserved_and_does_not_mutate(tmp_path, monkeypatch):
    _patch_ledger(tmp_path, monkeypatch)
    raw = AccrualDecision(
        vendor="Harbor Electric",
        period="2026-09",
        status="accrual_required",
        estimated_amount=7733.33,
        confidence=0.7,
        estimation_method="recent_average",
        evidence=["recent months"],
        reasoning_summary="I chose the recent average.",
    )
    decision, trace = finalize_vendor_close("Harbor Electric", "2026-09", raw, run_id="diag")
    assert decision.estimation_method == "recent_average"
    assert decision.estimated_amount == 7733.33
    assert trace.policy_method == "seasonal_prior_year"
    assert trace.policy_agreement is False
    assert any("REVIEW_FLAG" in item or "DISAGREE" in item for item in trace.diagnostic_warnings)
    assert method_diagnostics(
        agent_method="recent_average",
        agent_status="accrual_required",
        context=build_estimate_context("Harbor Electric", "2026-09"),
    )


def test_format_compare_preserves_disagreement():
    report = ComparisonReport(
        period="2026-09",
        agreements=1,
        disagreements=1,
        comparisons=[
            ComparisonRecord(
                vendor="Aether Compute",
                period="2026-09",
                policy_method="usage_run_rate",
                policy_amount=11849.90,
                agent_method="usage_run_rate",
                agent_amount=11849.90,
                agent_status="accrual_required",
                agree=True,
            ),
            ComparisonRecord(
                vendor="Harbor Electric",
                period="2026-09",
                policy_method="seasonal_prior_year",
                policy_amount=4650,
                agent_method="recent_average",
                agent_amount=7733.33,
                agent_status="accrual_required",
                agree=False,
                diagnostic_warnings=["DISAGREE: agent selected recent_average"],
            ),
        ],
    )
    text = format_compare(report)
    assert "usage_run_rate" in text
    assert "recent_average" in text
    assert "Yes" in text
    assert "No" in text
    assert "DISAGREE" in text


def test_compare_cli_is_wired():
    from accrue import main

    help_text = __import__("accrue").__doc__
    assert "compare" in help_text
    # Missing key path is a CLI contract; do not call the live agent here.
    import os

    if os.environ.get("OPENAI_API_KEY"):
        assert main.__name__ == "main"


def test_duplicate_current_invoices_are_not_missing():
    from accrual.discovery import discover_vendor

    result = discover_vendor("Amazon Web Services", "2026-09")
    assert result.invoice_received is True
    assert result.missing_bill_candidate is False
    assert set(result.current_invoice_ids) >= {"INV-002", "INV-016"}
    assert any(signal.type == "multiple_current_invoices" for signal in result.signals)


def test_ap_workflow_is_unchanged():
    invoice = load_invoice("INV-016")
    assert invoice is not None
    assert invoice.vendor == "Amazon Web Services"
    assert invoice.po_id is None
    evidence = collect_case_evidence("INV-016")
    assert evidence.exception_types == ["missing_po"]
    assert load_invoice("INV-002").po_id == "PO-102"
