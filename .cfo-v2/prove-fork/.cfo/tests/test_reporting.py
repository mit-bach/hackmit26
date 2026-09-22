from __future__ import annotations

import json
from pathlib import Path

import pytest

from reporting.actuals import compare_forecast_to_actuals, realize_actuals
from reporting.board import build_board_pack, render_markdown
from reporting.forecast import HORIZON_WEEKS, build_forecast, validate_forecast
from reporting.ledger import lines_for, post_balanced_entry
from reporting.models import CashActualMovement, VarianceContributor, VarianceExplanation
from reporting.posting import post_ap_payment
from reporting.seed import seed_demo_ledger, seed_demo_receivable
from reporting.sources import (
    ap_forecast_lines,
    ar_forecast_lines,
    expected_collection,
    load_receivables,
    payroll_forecast_lines,
    set_ap_decision,
)
from reporting.statements import build_income_statement, compare_metrics, period_report
from reporting.store import latest_snapshot, list_snapshots, load_snapshot, save_snapshot
from reporting.variance import (
    analyze_variance,
    flag_unsupported_claims,
    reconcile_contributors,
    trace_variance,
)
from reporting.workflow import run_reporting_workflow
from scheduling.pool import add_approved


def _seed_pool() -> None:
    for invoice_id in ("INV-001", "INV-002", "INV-006", "INV-009", "INV-016"):
        add_approved(invoice_id, source="test")
    set_ap_decision("INV-016", hold=True, approval_state="hold", reason="Missing PO")
    set_ap_decision("INV-009", scheduled_pay_date="2026-10-09", reason="Deferred")
    set_ap_decision("INV-002", scheduled_pay_date="2026-09-22", reason="Due this week")
    set_ap_decision("INV-006", scheduled_pay_date="2026-09-21", reason="Late")
    set_ap_decision("INV-001", scheduled_pay_date="2026-09-30", reason="Due")


def test_ledger_aggregates_and_gross_margin():
    seed_demo_ledger()
    august = build_income_statement("2026-08")
    september = build_income_statement("2026-09")
    assert august.revenue == 1_000_000
    assert august.cogs == 360_000
    assert august.gross_profit == 640_000
    assert august.gross_margin_pct == pytest.approx(0.64)
    assert september.revenue == 1_000_000
    assert september.cogs == 390_000
    assert september.gross_profit == 610_000
    assert september.gross_margin_pct == pytest.approx(0.61)
    assert september.operating_income == 410_000


def test_period_over_period_and_account_contribution():
    seed_demo_ledger()
    current, prior, metrics = period_report("2026-09", comparison_period="2026-08")
    assert prior is not None
    gm = next(item for item in metrics if item.metric == "gross_margin_pct" and item.comparison_kind == "prior_period")
    assert gm.current_value == pytest.approx(0.61)
    assert gm.comparison_value == pytest.approx(0.64)
    assert gm.absolute_variance == pytest.approx(-0.03)
    assert gm.relative_variance == pytest.approx(-0.046875)
    assert gm.dollar_variance == -30_000
    cogs = next(item for item in metrics if item.metric == "cogs" and item.comparison_kind == "prior_period")
    assert cogs.absolute_variance == 30_000
    hosting = [item for item in lines_for(period="2026-09", account_class="cogs") if item.category == "hosting"]
    assert sum(item.amount for item in hosting if item.side == "debit") == 95_000


def test_variance_traces_to_transactions_and_reconciles():
    seed_demo_ledger()
    explanation = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
    by_label = {item.label: item for item in explanation.contributors}
    assert "Cloud hosting" in by_label
    assert by_label["Cloud hosting"].amount == -15_000
    assert "TXN-HOST-SEP-OVERAGE" in by_label["Cloud hosting"].source_transaction_ids
    assert by_label["Supplier price / materials"].amount == -10_000
    assert "TXN-SUP-SEP-001" in by_label["Supplier price / materials"].source_transaction_ids
    assert by_label["Supplier price / materials"].quantity_rate_mix is not None
    assert by_label["Supplier price / materials"].quantity_rate_mix.rate_effect == 10_000
    assert by_label["Freight"].amount == -4_000
    assert "TXN-FRT-SEP-EXPEDITE" in by_label["Freight"].source_transaction_ids
    assert explanation.unexplained_amount == -1_000
    assert explanation.dollar_variance == -30_000
    assert reconcile_contributors(
        explanation.contributors,
        explanation.unexplained_amount,
        explanation.dollar_variance,
        explanation.residual_tolerance,
    )
    assert explanation.reconciled
    trace = trace_variance("gross_margin", "2026-09", "2026-08")
    assert trace.transactions
    assert trace.drilldown[0].level == "metric"
    assert any(node.level == "transaction" for account in trace.drilldown[0].children for category in account.children for entity in category.children for node in entity.children)


def test_unsupported_explanations_are_flagged():
    seed_demo_ledger()
    explanation = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
    flags = flag_unsupported_claims(explanation, "Gross margin fell because of a recession and competitor pricing.")
    assert flags
    from reporting.reviewer import review_variance

    explanation.narrative = "The decline is caused by a recession."
    verdict = review_variance(explanation)
    assert verdict.decision in {"ESCALATE", "REQUEST_EVIDENCE"}
    assert any(item.code == "unsupported_claim" for item in verdict.findings)


def test_cash_forecast_is_thirteen_weeks_and_rolls():
    seed_demo_receivable()
    _seed_pool()
    snapshot = build_forecast("2026-09-19", beginning_cash=500_000)
    assert len(snapshot.weeks) == HORIZON_WEEKS == 13
    assert snapshot.weeks[0].beginning_cash == 500_000
    for index, week in enumerate(snapshot.weeks[:-1]):
        assert snapshot.weeks[index + 1].beginning_cash == week.ending_cash
    assert validate_forecast(snapshot) == []
    recomputed = week.beginning_cash + week.ar_collections + week.other_inflows - week.ap_payments - week.payroll - week.other_outflows
    assert abs(recomputed - week.ending_cash) <= 0.02


def test_ap_ar_payroll_populate_forecast_and_holds():
    seed_demo_receivable()
    _seed_pool()
    snapshot = build_forecast("2026-09-19", beginning_cash=500_000)
    ap_ids = {item.source_id for item in snapshot.lines if item.source_type == "invoice"}
    ar_ids = {item.source_id for item in snapshot.lines if item.source_type == "receivable"}
    pr_ids = {item.source_id for item in snapshot.lines if item.source_type == "payroll"}
    assert "INV-002" in ap_ids
    assert "INV-016" in ap_ids
    assert "INV-AR-FC-001" in ar_ids
    assert "PR-2026-10-02" in pr_ids
    held = next(item for item in snapshot.lines if item.source_id == "INV-016")
    assert held.hold is True
    assert held.committed is False
    aws = next(item for item in snapshot.lines if item.source_id == "INV-002")
    assert aws.expected_date == "2026-09-22"
    assert aws.amount == -8320
    assert aws.evidence_refs
    assert "INV-016" not in {item.source_id for week in snapshot.weeks for item in snapshot.lines if item.line_id in week.line_ids and item.committed}


def test_changed_payment_date_shifts_forecast_week():
    seed_demo_receivable()
    _seed_pool()
    first = build_forecast("2026-09-19", beginning_cash=500_000)
    set_ap_decision("INV-002", scheduled_pay_date="2026-10-06", reason="Moved to the next week")
    second = build_forecast("2026-09-19", beginning_cash=500_000, prior=first)
    first_line = next(item for item in first.lines if item.source_id == "INV-002")
    second_line = next(item for item in second.lines if item.source_id == "INV-002")
    assert first_line.week_start != second_line.week_start
    assert second_line.expected_date == "2026-10-06"
    assert any(item.source_id == "INV-002" and item.field == "expected_date" for item in second.changes_from_prior)


def test_forecast_snapshots_are_immutable_versions():
    seed_demo_receivable()
    _seed_pool()
    first = build_forecast("2026-09-19", beginning_cash=500_000, version=1)
    saved = save_snapshot(first)
    with pytest.raises(ValueError, match="immutable"):
        save_snapshot(first)
    set_ap_decision("INV-002", scheduled_pay_date="2026-10-06", reason="Moved")
    second = build_forecast("2026-09-19", beginning_cash=500_000, prior=saved, version=2)
    save_snapshot(second)
    assert load_snapshot(saved.forecast_id).weeks[0].beginning_cash == 500_000
    assert len(list_snapshots()) == 2
    assert latest_snapshot("2026-09-19").forecast_id == second.forecast_id
    assert saved.forecast_id != second.forecast_id


def test_forecast_vs_actual_classifies_and_reconciles():
    seed_demo_receivable()
    _seed_pool()
    snapshot = build_forecast("2026-09-19", beginning_cash=500_000)
    actuals = realize_actuals(snapshot)
    explanation = compare_forecast_to_actuals(snapshot, actuals)
    kinds = {item.kind for item in explanation.contributors}
    assert "timing" in kinds
    assert "amount" in kinds
    assert "new_unforecast" in kinds
    labels = " ".join(item.label for item in explanation.contributors)
    assert "INV-AR-FC-001" in labels
    assert "INV-009" in labels
    assert "PR-2026-10-02" in labels
    assert "BNK-UNX-001" in labels
    late_ar = next(item for item in explanation.contributors if item.source_id == "INV-AR-FC-001")
    assert late_ar.kind == "timing"
    early_ap = next(item for item in explanation.contributors if item.source_id == "INV-009")
    assert early_ap.kind == "timing"
    payroll = next(item for item in explanation.contributors if item.source_id == "PR-2026-10-02")
    assert payroll.kind == "amount"
    assert payroll.amount == -3200
    unexpected = next(item for item in explanation.contributors if item.source_id == "BNK-UNX-001")
    assert unexpected.kind == "new_unforecast"
    assert unexpected.amount == -800
    assert explanation.reconciled
    assert abs(
        sum(item.amount for item in explanation.contributors) - explanation.total_ending_cash_variance
    ) <= 0.02


def test_ar_collection_rules_and_low_confidence():
    seed_demo_receivable()
    receivables = {item.invoice_id: item for item in load_receivables()}
    quiet = receivables["INV-AR-FC-001"]
    expectation = expected_collection(quiet)
    assert expectation is not None
    assert expectation.expected_date == "2026-09-26"
    helios = next(item for item in receivables.values() if item.customer_id == "CUST-002" and item.outstanding_amount > 0)
    late = expected_collection(helios)
    assert late is not None
    assert late.low_confidence or late.confidence < 0.5
    assert "historically pays" in late.rationale or late.rule == "historical_days_late"
    lines = ar_forecast_lines()
    assert any(item.source_id == "INV-AR-FC-001" and item.amount == 25000 for item in lines)


def test_board_pack_ties_to_ledger_and_keeps_evidence():
    seed_demo_ledger()
    current, prior, metrics = period_report("2026-09")
    variance = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
    pack = build_board_pack(
        period="2026-09",
        as_of_date="2026-09-19",
        current=current,
        prior=prior,
        metrics=metrics,
        variances=[variance],
        forecast=None,
        forecast_variance=None,
    )
    gm_section = next(item for item in pack.sections if item.title == "Gross Margin")
    assert gm_section.metrics[0].current_value == current.gross_margin_pct
    assert any("metric:gross_margin_pct:2026-09" in ref for ref in gm_section.evidence_refs)
    assert pack.markdown
    assert "Gross Margin" in render_markdown(pack)
    from reporting.reviewer import review_board_pack

    verdict = review_board_pack(pack, {"2026-09": current, "2026-08": prior})
    assert verdict.decision == "APPROVE"
    assert not pack.unsupported_claims


def test_end_to_end_ap_forecast_payment_ledger_board_trace():
    seed_demo_ledger()
    seed_demo_receivable()
    add_approved("INV-002", source="ap_workflow")
    set_ap_decision("INV-002", scheduled_pay_date="2026-09-22", reason="Approved AP invoice due 2026-09-22")
    snapshot = build_forecast("2026-09-19", beginning_cash=500_000)
    forecast_line = next(item for item in snapshot.lines if item.source_id == "INV-002")
    assert forecast_line.amount == -8320
    posted = post_ap_payment(
        "INV-002",
        payment_date="2026-09-22",
        bank_transaction_id="BNK-INV-002",
        reconciliation_id="REC-INV-002",
        trace_id=snapshot.trace_id,
    )
    assert posted["journal"]["source_document_id"] == "INV-002"
    assert posted["journal"]["transaction_id"] == "INV-002"
    assert posted["reconciliation_id"] == "REC-INV-002"
    assert posted["movement"]["bank_transaction_id"] == "BNK-INV-002"
    variance = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
    current, prior, metrics = period_report("2026-09")
    pack = build_board_pack(
        period="2026-09",
        as_of_date="2026-09-19",
        current=current,
        prior=prior,
        metrics=metrics,
        variances=[variance],
        forecast=snapshot,
        forecast_variance=None,
    )
    run = run_reporting_workflow("2026-09", as_of="2026-09-19", live=False, seed=False, persist=True)
    assert run.statement.gross_margin_pct == pytest.approx(0.61)
    assert run.forecast is not None
    assert any(item.source_document_id == "INV-002" for item in run.provenance)
    chain = next(item for item in run.provenance if item.source_document_id == "INV-002")
    assert chain.forecast_id
    assert chain.variance_id
    assert chain.board_pack_id
    assert posted["journal"]["entry_id"]
    assert pack.forecast_id == snapshot.forecast_id
    assert "INV-002" in json.dumps(posted)


def test_demo_workflow_deterministic():
    run = run_reporting_workflow(live=False, seed=True, persist=True)
    assert run.statement is not None
    assert run.statement.gross_margin_pct == pytest.approx(0.61)
    assert run.variances[0].reconciled
    assert run.forecast is not None
    assert len(run.forecast.weeks) == 13
    assert run.forecast_variance is not None
    assert run.forecast_variance.reconciled
    assert run.board_pack is not None
    assert run.trace_path
    from reporting.report import format_reporting_run

    text = format_reporting_run(run)
    assert "1. Financial results" in text
    assert "7. Evidence / provenance trail" in text


def test_payroll_and_ap_source_modules_are_not_hardcoded_in_weeks():
    _seed_pool()
    payroll = payroll_forecast_lines()
    ap = ap_forecast_lines()
    assert payroll
    assert all(item.source_type == "payroll" for item in payroll)
    assert ap
    assert all(item.source_type == "invoice" for item in ap)
