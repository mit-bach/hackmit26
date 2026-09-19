"""Historical close backtests with an as-of cutoff. No future invoices leak in."""

from __future__ import annotations

from statistics import mean, median

from accrual.cutoff import data_cutoff
from accrual.discovery import discover_vendor
from accrual.estimation import money
from accrual.models import BacktestMetrics, BacktestRecord, BacktestReport, MethodMetrics
from accrual.policy import preferred_candidate
from accrual.store import all_accrual_invoices, build_estimate_context, current_invoices_for, later_invoices_for
from accrual.trace import TRACES_ROOT, new_run_id, vendor_slug

LATEST_CLOSE = "2026-09"


def _percentage_error(estimated: float, actual: float) -> float | None:
    if actual == 0:
        return None
    return round(abs(estimated - actual) / abs(actual) * 100, 2)


def compute_backtest_metrics(records: list[BacktestRecord]) -> BacktestMetrics:
    scored = [item for item in records if item.absolute_error is not None and item.estimated_amount is not None]
    if not scored:
        return BacktestMetrics(invoices_tested=0)
    abs_errors = [item.absolute_error for item in scored if item.absolute_error is not None]
    signed = [item.error for item in scored if item.error is not None]
    pcts = [item.percentage_error for item in scored if item.percentage_error is not None]
    within_5 = [item for item in scored if item.percentage_error is not None and item.percentage_error <= 5]
    within_10 = [item for item in scored if item.percentage_error is not None and item.percentage_error <= 10]
    by_method: dict[str, list[BacktestRecord]] = {}
    for item in scored:
        if item.selected_method:
            by_method.setdefault(item.selected_method, []).append(item)
    method_rows = []
    for method, rows in sorted(by_method.items()):
        method_pcts = [row.percentage_error for row in rows if row.percentage_error is not None]
        method_rows.append(
            MethodMetrics(
                method=method,
                observations=len(rows),
                mean_absolute_error=money(mean(row.absolute_error or 0 for row in rows)),
                mean_absolute_percentage_error=round(mean(method_pcts), 2) if method_pcts else None,
            )
        )
    return BacktestMetrics(
        invoices_tested=len(scored),
        mean_absolute_error=money(mean(abs_errors)),
        median_absolute_error=money(median(abs_errors)),
        mean_absolute_percentage_error=round(mean(pcts), 2) if pcts else None,
        mean_signed_error=money(mean(signed)) if signed else 0,
        within_5_percent=round(100 * len(within_5) / len(pcts), 1) if pcts else None,
        within_10_percent=round(100 * len(within_10) / len(pcts), 1) if pcts else None,
        by_method=method_rows,
    )


def _hidden_invoice_visible(invoice_id: str, vendor: str, period: str) -> bool:
    current_ids = {item.invoice_id for item in current_invoices_for(vendor, period)}
    later_ids = {item.invoice_id for item in later_invoices_for(vendor, period)}
    return invoice_id in current_ids or invoice_id in later_ids


def run_backtest_case(invoice) -> BacktestRecord:
    period = invoice.service_period
    hidden_id = invoice.invoice_id
    estimated = None
    method = None
    discovery_id = ""
    expected = False
    expectation_confidence = 0.0
    leaked = False
    with data_cutoff(period, hide_period_invoices=True, allow_later_invoices=False):
        leaked = _hidden_invoice_visible(hidden_id, invoice.vendor, period)
        discovery = discover_vendor(invoice.vendor, period, run_id=f"backtest-{period}")
        discovery_id = discovery.discovery_trace_id
        expected = discovery.expense_expected or discovery.missing_bill_candidate
        expectation_confidence = discovery.expectation_confidence
        context = build_estimate_context(invoice.vendor, period)
        if any(item.invoice_id == hidden_id for item in context.current_invoices + context.historical_invoices):
            leaked = True
        if any(item.service_period > period for item in context.historical_invoices + context.current_invoices):
            leaked = True
        candidate = preferred_candidate(context) if expected else None
        if candidate:
            estimated = candidate.amount
            method = candidate.method
    # Actual is revealed only after the estimate is committed.
    actual = invoice.amount
    error = None
    abs_error = None
    pct = None
    if estimated is not None:
        error = money(estimated - actual)
        abs_error = money(abs(error))
        pct = _percentage_error(estimated, actual)
    return BacktestRecord(
        vendor=invoice.vendor,
        period=period,
        selected_method=method,
        estimated_amount=estimated,
        actual_invoice_id=hidden_id,
        actual_amount=actual,
        error=error,
        absolute_error=abs_error,
        percentage_error=pct,
        expense_expected=expected,
        expectation_confidence=expectation_confidence,
        estimate_confidence=0.85 if estimated is not None else 0,
        discovery_trace_id=discovery_id,
        accrual_trace_id=f"{period}/backtest/{vendor_slug(invoice.vendor)}",
        hidden_invoice_id=hidden_id,
        future_leak_detected=leaked,
        estimate_committed_before_reveal=True,
    )


def select_backtest_invoices(latest_period: str = LATEST_CLOSE):
    invoices = [
        item
        for item in all_accrual_invoices()
        if item.service_period < latest_period
    ]
    selected = []
    for invoice in invoices:
        with data_cutoff(invoice.service_period, hide_period_invoices=True, allow_later_invoices=False):
            discovery = discover_vendor(invoice.vendor, invoice.service_period, run_id="select")
        if discovery.expense_expected or discovery.missing_bill_candidate:
            selected.append(invoice)
    return selected


def run_backtest(latest_period: str = LATEST_CLOSE) -> BacktestReport:
    invoices = select_backtest_invoices(latest_period)
    records = [run_backtest_case(item) for item in invoices]
    metrics = compute_backtest_metrics(records)
    periods = sorted({item.period for item in records})
    report = BacktestReport(records=records, metrics=metrics, periods=periods)
    run_id = new_run_id()
    directory = TRACES_ROOT / "backtest" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "results.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    report.trace_path = str(path)
    return report
