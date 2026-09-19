from __future__ import annotations

from datetime import date, timedelta

from reporting.forecast import (
    HORIZON_WEEKS,
    build_forecast,
    lines_for_week,
    persist_forecast_export,
    validate_forecast,
    week_starts,
)
from reporting.sources import expected_collection, load_receivables
from reporting.store import next_version
from scheduling.cash import canonical_expected_receipts, receipts_source_of_truth, spendable_cash
from scheduling.pool import add_approved, seed_demo_pool

from ar.context import expected_collections, unapplied_cash_total
from ar.review import reject_review
from ar.store import get_invoice, reset_state
from ar.workflow import run_cash_apply


AS_OF = "2026-09-30"


def _seed_ap() -> None:
    seed_demo_pool()
    for invoice_id in ("INV-001", "INV-002", "INV-006"):
        add_approved(invoice_id, source="test")


def test_thirteen_weeks_roll_forward_and_deterministic_arithmetic():
    reset_state()
    _seed_ap()
    snapshot = build_forecast(AS_OF)
    assert len(snapshot.weeks) == HORIZON_WEEKS == 13
    assert snapshot.weeks[0].week_start == week_starts(AS_OF)[0].isoformat()
    assert snapshot.weeks[0].beginning_cash == snapshot.beginning_cash
    for index, week in enumerate(snapshot.weeks[:-1]):
        assert snapshot.weeks[index + 1].beginning_cash == week.ending_cash
        recomputed = (
            week.beginning_cash
            + week.ar_collections
            + week.other_inflows
            - week.ap_payments
            - week.payroll
            - week.other_outflows
        )
        assert abs(recomputed - week.ending_cash) <= 0.02
    assert validate_forecast(snapshot) == []


def test_ar_collections_derive_from_open_invoices_and_trace_to_lines():
    reset_state()
    snapshot = build_forecast(AS_OF)
    ar_ids = {item.source_id for item in snapshot.lines if item.source_type == "receivable"}
    assert "INV-AR-001" in ar_ids
    assert "INV-AR-045" in ar_ids
    week = snapshot.weeks[0]
    detail = lines_for_week(snapshot, week.week_start, source_type="receivable")
    assert abs(sum(item.amount for item in detail) - week.ar_collections) <= 0.02


def test_paid_invoice_disappears_and_opening_absorbs_receipt():
    reset_state()
    before = build_forecast(AS_OF)
    assert any(item.source_id == "INV-AR-001" for item in before.lines)
    run_cash_apply("PAY-001", as_of=AS_OF, live=False)
    after = build_forecast(AS_OF)
    assert get_invoice("INV-AR-001").outstanding_amount == 0
    assert not any(item.source_id == "INV-AR-001" for item in after.lines)
    assert after.beginning_cash == before.beginning_cash + 12000
    assert after.assumptions["posted_ar_cash"] == before.assumptions["posted_ar_cash"] + 12000


def test_promise_to_pay_and_disputed_and_partial_rules():
    reset_state()
    run_cash_apply("PAY-004", as_of=AS_OF, live=False)
    receivables = {item.invoice_id: item for item in load_receivables()}
    promise = expected_collection(receivables["INV-AR-035"])
    assert promise is not None
    assert promise.expected_date == "2026-10-01"
    assert promise.rule == "promised_pay_date"
    disputed = expected_collection(receivables["INV-AR-020"])
    assert disputed is not None
    assert disputed.low_confidence
    assert disputed.rule == "disputed"
    snapshot = build_forecast(AS_OF)
    orbit = next(item for item in snapshot.lines if item.source_id == "INV-AR-020")
    assert orbit.committed is False
    assert "disputed:true" in orbit.evidence_refs
    assert not any(
        item.source_id == "INV-AR-020" and item.committed and item.week_start == week.week_start
        for week in snapshot.weeks
        for item in snapshot.lines
        if item.line_id in week.line_ids
    )
    pinnacle = next(item for item in snapshot.lines if item.source_id == "INV-AR-025")
    assert pinnacle.amount == 11000


def test_scheduled_ap_and_payroll_feed_outflows():
    reset_state()
    _seed_ap()
    snapshot = build_forecast(AS_OF)
    ap_ids = {item.source_id for item in snapshot.lines if item.source_type == "invoice"}
    pr_ids = {item.source_id for item in snapshot.lines if item.source_type == "payroll"}
    assert "INV-002" in ap_ids
    assert "PR-2026-10-02" in pr_ids
    assert any(week.payroll > 0 for week in snapshot.weeks)
    assert any(week.ap_payments > 0 for week in snapshot.weeks)


def test_human_review_cash_is_not_double_counted():
    reset_state()
    before = build_forecast(AS_OF)
    ar_before = sum(week.ar_collections for week in before.weeks)
    run_cash_apply("PAY-005", as_of=AS_OF, live=False)
    after = build_forecast(AS_OF)
    assert get_invoice("INV-AR-101").outstanding_amount == 10000
    assert get_invoice("INV-AR-103").outstanding_amount == 25000
    assert after.beginning_cash == before.beginning_cash + 25000
    ar_after = sum(week.ar_collections for week in after.weeks)
    assert abs((after.beginning_cash + ar_after) - (before.beginning_cash + ar_before)) <= 0.02
    assert after.assumptions["unapplied_customer_cash"] >= 25000


def test_unapplied_rejected_cash_stays_out_of_future_collections():
    reset_state()
    run_cash_apply("PAY-005", as_of=AS_OF, live=False)
    reject_review("PAY-005", "Unable to identify intended invoices")
    snapshot = build_forecast(AS_OF)
    assert snapshot.assumptions["posted_ar_cash"] >= 25000
    assert unapplied_cash_total() >= 25000
    assert get_invoice("INV-AR-103").outstanding_amount == 25000


def test_canonical_expected_receipts_is_live_ar_and_ap_spendable_stays():
    reset_state()
    live = expected_collections(AS_OF, 7)
    assert canonical_expected_receipts(AS_OF) == live
    truth = receipts_source_of_truth(AS_OF)
    assert truth["source_of_truth"] == "live_ar"
    assert truth["legacy_is_fallback_only"] is True
    assert spendable_cash() == 115000


def test_forecast_reruns_reflect_persisted_ar_and_export_trace():
    reset_state()
    first = build_forecast(AS_OF, version=next_version(AS_OF))
    run_cash_apply("PAY-001", as_of=AS_OF, live=False)
    second = build_forecast(AS_OF, prior=first, version=next_version(AS_OF))
    assert any(item.source_id == "INV-AR-001" and item.field == "removed" for item in second.changes_from_prior)
    export = persist_forecast_export(second)
    assert (export / "forecast.json").exists()
    assert (export / "trace.json").exists()


def test_week_grid_is_monday_aligned():
    starts = week_starts("2026-09-30", 13)
    assert starts[0] == date(2026, 9, 28)
    assert starts[1] == starts[0] + timedelta(weeks=1)
    assert starts[0].weekday() == 0
    assert len(starts) == 13
