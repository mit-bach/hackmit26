"""Forecast-versus-actual attribution. Timing, amount, new, removed, unexplained."""

from __future__ import annotations

import json
from datetime import date, timedelta

from accrual.estimation import money
from reporting.forecast import monday_on_or_before
from reporting import ledger as reporting_ledger
from reporting.models import (
    CashActualMovement,
    CashForecastSnapshot,
    ForecastLine,
    ForecastVarianceContributor,
    ForecastVarianceExplanation,
    ForecastWeekActual,
)
from reporting.statements import ratio
from tools import DataFileError


def load_actuals() -> list[CashActualMovement]:
    path = reporting_ledger.DATA_REPORTING / "actuals.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DataFileError(f"Invalid JSON in actuals.json: {exc.msg}") from exc
    return [CashActualMovement.model_validate(item) for item in raw]


def realize_actuals(
    snapshot: CashForecastSnapshot,
    plants: list[CashActualMovement] | None = None,
    *,
    window_end: str | None = None,
) -> list[CashActualMovement]:
    """Most forecast lines occur as planned; plants override or add misses."""
    from reporting.sources import load_assumptions

    plants = list(plants if plants is not None else load_actuals())
    planted_ids = {item.source_id for item in plants}
    window_start = snapshot.weeks[0].week_start if snapshot.weeks else snapshot.as_of_date
    if window_end is None:
        window_end = load_assumptions().forecast_actuals_as_of or snapshot.as_of_date
        window_end = (monday_on_or_before(date.fromisoformat(window_end[:10])) + timedelta(days=6)).isoformat()
    realized: list[CashActualMovement] = list(plants)
    for line in snapshot.lines:
        if not line.committed or line.source_id in planted_ids:
            continue
        week = line.week_start or _week_key(line.expected_date)
        if week < window_start or week > _week_key(window_end):
            continue
        realized.append(
            CashActualMovement(
                movement_id=f"ACT-{line.source_id}",
                source_type=line.source_type,
                source_id=line.source_id,
                date=line.expected_date if _in_window(line.expected_date, window_start, window_end) else week,
                amount=line.amount,
                kind="inflow" if line.amount > 0 else "outflow",
                description=line.rationale,
                evidence_refs=list(line.evidence_refs),
            )
        )
    return realized


def _week_key(value: str) -> str:
    return monday_on_or_before(date.fromisoformat(value[:10])).isoformat()


def _in_window(value: str, start: str, end: str) -> bool:
    day = date.fromisoformat(value[:10])
    return date.fromisoformat(start) <= day <= date.fromisoformat(end)


def compare_forecast_to_actuals(
    snapshot: CashForecastSnapshot,
    actuals: list[CashActualMovement] | None = None,
    *,
    analysis_id: str = "",
    as_of_actuals: str | None = None,
) -> ForecastVarianceExplanation:
    from reporting.sources import load_assumptions

    actuals = list(actuals if actuals is not None else realize_actuals(snapshot))
    window_start = snapshot.weeks[0].week_start if snapshot.weeks else snapshot.as_of_date
    known = as_of_actuals or load_assumptions().forecast_actuals_as_of
    if known:
        window_end = (monday_on_or_before(date.fromisoformat(known[:10])) + timedelta(days=6)).isoformat()
    elif actuals:
        last = max(item.date for item in actuals)
        window_end = (monday_on_or_before(date.fromisoformat(last[:10])) + timedelta(days=6)).isoformat()
    else:
        window_end = snapshot.weeks[-1].week_end if snapshot.weeks else snapshot.as_of_date

    window_actuals = [item for item in actuals if _in_window(item.date, window_start, window_end)]
    committed = [item for item in snapshot.lines if item.committed]

    week_rows: list[ForecastWeekActual] = []
    running_actual = snapshot.beginning_cash
    for week in snapshot.weeks:
        week_actuals = [item for item in window_actuals if _week_key(item.date) == week.week_start]
        actual_in = money(sum(item.amount for item in week_actuals if item.amount > 0))
        actual_out = money(sum(abs(item.amount) for item in week_actuals if item.amount < 0))
        forecast_in = money(week.ar_collections + week.other_inflows)
        forecast_out = money(week.ap_payments + week.payroll + week.other_outflows)
        if week.week_start <= _week_key(window_end):
            running_actual = money(running_actual + actual_in - actual_out)
            actual_ending = running_actual
        else:
            actual_ending = week.ending_cash
            actual_in = 0.0
            actual_out = 0.0
        week_rows.append(
            ForecastWeekActual(
                week_start=week.week_start,
                forecast_inflows=forecast_in,
                actual_inflows=actual_in if week.week_start <= _week_key(window_end) else 0.0,
                inflow_variance=money((actual_in if week.week_start <= _week_key(window_end) else 0.0) - forecast_in)
                if week.week_start <= _week_key(window_end)
                else 0.0,
                forecast_outflows=forecast_out,
                actual_outflows=actual_out if week.week_start <= _week_key(window_end) else 0.0,
                outflow_variance=money((actual_out if week.week_start <= _week_key(window_end) else 0.0) - forecast_out)
                if week.week_start <= _week_key(window_end)
                else 0.0,
                forecast_ending_cash=week.ending_cash,
                actual_ending_cash=actual_ending if week.week_start <= _week_key(window_end) else week.ending_cash,
                ending_cash_variance=money(actual_ending - week.ending_cash)
                if week.week_start <= _week_key(window_end)
                else 0.0,
            )
        )

    focal = next((row for row in reversed(week_rows) if row.week_start <= _week_key(window_end)), None)
    total_miss = focal.ending_cash_variance if focal else 0.0

    actual_by_source = {item.source_id: item for item in window_actuals}
    planted_by_source = {item.source_id: item for item in actuals}
    def _line_in_window(line: ForecastLine) -> bool:
        week = line.week_start or _week_key(line.expected_date)
        return window_start <= week <= _week_key(window_end)

    forecast_in_window = {item.source_id: item for item in committed if _line_in_window(item)}
    contributors: list[ForecastVarianceContributor] = []

    def add(label: str, amount: float, kind, source_id: str = "", source_type: str = "") -> None:
        if abs(amount) <= 0.005:
            return
        contributors.append(
            ForecastVarianceContributor(
                label=label,
                amount=money(amount),
                kind=kind,
                source_id=source_id,
                source_type=source_type,
                evidence_refs=[f"{source_type}:{source_id}"] if source_id else ["forecast:residual"],
            )
        )

    seen_actual: set[str] = set()
    for source_id, forecast in {item.source_id: item for item in committed}.items():
        actual = actual_by_source.get(source_id)
        forecast_in = source_id in forecast_in_window
        if actual is None and forecast_in:
            late = planted_by_source.get(source_id)
            if late is not None and _week_key(late.date) != (forecast.week_start or _week_key(forecast.expected_date)):
                add(
                    f"{forecast.source_type} {source_id} timing moved to {late.date}",
                    money(-forecast.amount),
                    "timing",
                    source_id,
                    forecast.source_type,
                )
            else:
                add(
                    f"{forecast.source_type} {source_id} did not arrive in the actuals window",
                    money(-forecast.amount),
                    "removed_cancelled",
                    source_id,
                    forecast.source_type,
                )
            continue
        if actual is None:
            continue
        seen_actual.add(source_id)
        amount_gap = money(actual.amount - forecast.amount)
        same_week = _week_key(actual.date) == (forecast.week_start or _week_key(forecast.expected_date))
        if not same_week:
            add(
                f"{forecast.source_type} {source_id} timing moved to {actual.date}",
                amount_gap if forecast_in else actual.amount,
                "timing",
                source_id,
                forecast.source_type,
            )
            # When the forecast date is outside the window and the actual is inside,
            # the cash impact is the actual movement (early payment / late receipt).
            if not forecast_in:
                contributors[-1].amount = money(actual.amount)
            elif not _in_window(actual.date, window_start, window_end):
                contributors[-1].amount = money(-forecast.amount)
        elif abs(amount_gap) > 0.02:
            add(
                f"{forecast.source_type} {source_id} amount miss",
                amount_gap,
                "amount",
                source_id,
                forecast.source_type,
            )

    for source_id, actual in actual_by_source.items():
        if source_id in seen_actual or source_id in {item.source_id for item in committed}:
            continue
        add(
            f"Unforecast {actual.source_type} {source_id}",
            actual.amount,
            "new_unforecast",
            source_id,
            actual.source_type,
        )

    named_total = money(sum(item.amount for item in contributors))
    unexplained = money(total_miss - named_total)
    if abs(unexplained) > 0.02:
        add("Other/unexplained", unexplained, "unexplained")
    else:
        unexplained = 0.0

    for item in contributors:
        item.share_of_variance = ratio(item.amount / total_miss) if total_miss else 0.0
    reconciled = abs(money(sum(item.amount for item in contributors) - total_miss)) <= 0.02
    return ForecastVarianceExplanation(
        analysis_id=analysis_id or f"FVA-{snapshot.forecast_id}",
        forecast_id=snapshot.forecast_id,
        as_of_date=snapshot.as_of_date,
        weeks=week_rows,
        contributors=contributors,
        unexplained_amount=unexplained,
        total_ending_cash_variance=total_miss,
        reconciled=reconciled,
        narrative=_narrative(snapshot, week_rows, contributors, total_miss),
        evidence_refs=[
            f"forecast:{snapshot.forecast_id}",
            *[ref for item in contributors for ref in item.evidence_refs],
        ],
        trace_id=f"TRACE-FVA-{snapshot.forecast_id}",
    )


def _narrative(
    snapshot: CashForecastSnapshot,
    weeks: list[ForecastWeekActual],
    contributors: list[ForecastVarianceContributor],
    total_miss: float,
) -> str:
    last = next((row for row in reversed(weeks) if row.ending_cash_variance or row.actual_inflows or row.actual_outflows), None)
    parts = [
        f"Forecast {snapshot.forecast_id} as of {snapshot.as_of_date} "
        "is compared with actual cash that became known later."
    ]
    if last:
        parts.append(
            f"Ending cash forecast {last.forecast_ending_cash:,.2f} vs actual "
            f"{last.actual_ending_cash:,.2f} (miss {total_miss:+,.2f})."
        )
    for item in contributors:
        parts.append(f"{item.kind}: {item.label} {item.amount:+,.2f}.")
    return " ".join(parts)


def forecast_line_in_week(line: ForecastLine, week_start: str) -> bool:
    return (line.week_start or _week_key(line.expected_date)) == week_start
