"""Rolling 13-week cash forecast. Weekly totals are recalculated from lines."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from accrual.estimation import money

from reporting.ledger import opening_cash
from reporting.models import (
    CashForecastSnapshot,
    CashForecastWeek,
    ForecastChange,
    ForecastLine,
)
from reporting.sources import (
    ap_forecast_lines,
    ar_forecast_lines,
    load_assumptions,
    load_other_cash,
    payroll_forecast_lines,
)

HORIZON_WEEKS = 13
ROOT = Path(__file__).resolve().parent.parent
FORECAST_EXPORT_DIR = ROOT / "runs" / "forecast"


def monday_on_or_before(value: date) -> date:
    return value - timedelta(days=value.weekday())


def week_starts(as_of: str, weeks: int = HORIZON_WEEKS) -> list[date]:
    start = monday_on_or_before(date.fromisoformat(as_of[:10]))
    return [start + timedelta(weeks=index) for index in range(weeks)]


def week_of(value: str, starts: list[date]) -> date | None:
    day = date.fromisoformat(value[:10])
    monday = monday_on_or_before(day)
    for start in starts:
        if start == monday:
            return start
    return None


def collect_lines(as_of: str) -> list[ForecastLine]:
    return [
        *ap_forecast_lines(),
        *ar_forecast_lines(as_of),
        *payroll_forecast_lines(),
        *load_other_cash(),
    ]


def posted_ar_receipts(as_of: str) -> float:
    """Customer cash received after the last bank snapshot. Inbox UNMATCHED items are excluded."""
    from ar.schedule import received_customer_cash
    from scheduling.cash import load_cash_position

    cash = load_cash_position()
    return money(sum(item.amount for item in received_customer_cash(as_of, cash.as_of_date)))


def lines_for_week(
    snapshot: CashForecastSnapshot,
    week_start: str,
    *,
    source_type: str | None = None,
    committed_only: bool = True,
) -> list[ForecastLine]:
    rows = [item for item in snapshot.lines if item.week_start == week_start]
    if committed_only:
        rows = [item for item in rows if item.committed]
    if source_type:
        rows = [item for item in rows if item.source_type == source_type]
    return rows


def persist_forecast_export(snapshot: CashForecastSnapshot, directory: Path | None = None) -> Path:
    """Write the existing reporting snapshot plus a judge-facing runs/forecast copy."""
    from reporting.store import load_snapshot, save_snapshot

    saved = load_snapshot(snapshot.forecast_id)
    if saved is None:
        saved = save_snapshot(snapshot)
    export_root = Path(directory) if directory is not None else FORECAST_EXPORT_DIR
    run_dir = export_root / saved.forecast_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = saved.model_dump_json(indent=2) + "\n"
    (run_dir / "forecast.json").write_text(payload)
    (run_dir / "trace.json").write_text(payload)
    return run_dir


def _assign_weeks(lines: list[ForecastLine], starts: list[date], as_of: str) -> list[ForecastLine]:
    first = starts[0]
    last = starts[-1] + timedelta(days=6)
    assigned = []
    for line in lines:
        expected = date.fromisoformat(line.expected_date[:10])
        if expected < first:
            monday = first
        elif expected > last:
            continue
        else:
            monday = monday_on_or_before(expected)
        assigned.append(line.model_copy(update={"week_start": monday.isoformat()}))
    return assigned


def _week_totals(week_start: date, beginning: float, lines: list[ForecastLine]) -> CashForecastWeek:
    week_end = week_start + timedelta(days=6)
    rows = [item for item in lines if item.committed and item.week_start == week_start.isoformat()]
    ar_collections = money(sum(item.amount for item in rows if item.source_type == "receivable" and item.amount > 0))
    other_inflows = money(sum(item.amount for item in rows if item.source_type == "other" and item.amount > 0))
    ap_payments = money(sum(abs(item.amount) for item in rows if item.source_type == "invoice" and item.amount < 0))
    payroll = money(sum(abs(item.amount) for item in rows if item.source_type == "payroll" and item.amount < 0))
    other_outflows = money(sum(abs(item.amount) for item in rows if item.source_type == "other" and item.amount < 0))
    ending = money(beginning + ar_collections + other_inflows - ap_payments - payroll - other_outflows)
    recomputed = money(beginning + sum(item.amount for item in rows))
    if abs(recomputed - ending) > 0.02:
        ending = recomputed
    return CashForecastWeek(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        beginning_cash=money(beginning),
        ar_collections=ar_collections,
        other_inflows=other_inflows,
        ap_payments=ap_payments,
        payroll=payroll,
        other_outflows=other_outflows,
        ending_cash=ending,
        line_ids=[item.line_id for item in rows],
    )


def diff_forecasts(prior: CashForecastSnapshot | None, current_lines: list[ForecastLine]) -> list[ForecastChange]:
    if prior is None:
        return []
    previous = {item.source_id: item for item in prior.lines}
    now = {item.source_id: item for item in current_lines}
    changes: list[ForecastChange] = []
    for source_id, line in now.items():
        old = previous.get(source_id)
        if old is None:
            changes.append(
                ForecastChange(
                    source_id=source_id,
                    source_type=line.source_type,
                    field="added",
                    current=f"{line.expected_date}:{line.amount}",
                    reason=line.rationale,
                )
            )
            continue
        if old.expected_date != line.expected_date:
            changes.append(
                ForecastChange(
                    source_id=source_id,
                    source_type=line.source_type,
                    field="expected_date",
                    previous=old.expected_date,
                    current=line.expected_date,
                    reason=line.rationale or "Payment date moved",
                )
            )
        if money(old.amount) != money(line.amount):
            changes.append(
                ForecastChange(
                    source_id=source_id,
                    source_type=line.source_type,
                    field="amount",
                    previous=str(old.amount),
                    current=str(line.amount),
                    reason=line.rationale or "Amount changed",
                )
            )
        if old.hold != line.hold:
            changes.append(
                ForecastChange(
                    source_id=source_id,
                    source_type=line.source_type,
                    field="hold",
                    previous=str(old.hold),
                    current=str(line.hold),
                    reason=line.rationale,
                )
            )
    for source_id, old in previous.items():
        if source_id not in now:
            changes.append(
                ForecastChange(
                    source_id=source_id,
                    source_type=old.source_type,
                    field="removed",
                    previous=f"{old.expected_date}:{old.amount}",
                    reason="Source no longer in forecast",
                )
            )
    return changes


def build_forecast(
    as_of: str,
    *,
    beginning_cash: float | None = None,
    prior: CashForecastSnapshot | None = None,
    forecast_id: str = "",
    version: int = 1,
    agent_judgments: list[str] | None = None,
    weeks: int = HORIZON_WEEKS,
) -> CashForecastSnapshot:
    starts = week_starts(as_of, weeks)
    raw_lines = collect_lines(as_of)
    lines = _assign_weeks(raw_lines, starts, as_of)
    posted = posted_ar_receipts(as_of)
    if beginning_cash is not None:
        cash = money(beginning_cash)
    else:
        cash = money(opening_cash(as_of) + posted)
    weeks_out: list[CashForecastWeek] = []
    cursor = cash
    for start in starts:
        week = _week_totals(start, cursor, lines)
        weeks_out.append(week)
        cursor = week.ending_cash
    assumptions = load_assumptions()
    held = [item.source_id for item in lines if item.hold]
    low = [item.line_id for item in lines if item.confidence < assumptions.low_confidence_threshold]
    stamp = as_of.replace("-", "")
    from ar.context import unapplied_cash_total
    from scheduling.cash import load_cash_position, receipts_source_of_truth

    extra = receipts_source_of_truth(as_of)
    extra.update(
        {
            "posted_ar_cash": posted,
            "unapplied_customer_cash": unapplied_cash_total(),
            "minimum_cash_reserve": load_cash_position().minimum_cash_reserve,
        }
    )
    return CashForecastSnapshot(
        forecast_id=forecast_id or f"CF-{as_of}-v{version}",
        as_of_date=as_of,
        horizon_weeks=weeks,
        beginning_cash=cash,
        weeks=weeks_out,
        lines=lines,
        assumptions={**assumptions.model_dump(), **extra},
        agent_judgments=list(agent_judgments or []),
        changes_from_prior=diff_forecasts(prior, lines),
        source_trace_ids=sorted({tid for item in lines for tid in item.trace_ids}),
        low_confidence_lines=low,
        held_ap_ids=held,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        version=version,
        immutable=True,
        trace_id=f"TRACE-CF-{stamp}-v{version}",
    )


def validate_forecast(snapshot: CashForecastSnapshot) -> list[str]:
    errors: list[str] = []
    if len(snapshot.weeks) != snapshot.horizon_weeks:
        errors.append(f"Forecast must have {snapshot.horizon_weeks} weeks, found {len(snapshot.weeks)}")
    if snapshot.weeks and money(snapshot.weeks[0].beginning_cash) != money(snapshot.beginning_cash):
        errors.append("First-week beginning cash does not match snapshot beginning cash")
    for index, week in enumerate(snapshot.weeks):
        rows = [
            item
            for item in snapshot.lines
            if item.committed and item.week_start == week.week_start
        ]
        expected_end = money(week.beginning_cash + sum(item.amount for item in rows))
        if abs(expected_end - week.ending_cash) > 0.02:
            errors.append(f"Week {week.week_start} does not roll from its forecast lines")
        if index + 1 < len(snapshot.weeks):
            nxt = snapshot.weeks[index + 1]
            if money(nxt.beginning_cash) != money(week.ending_cash):
                errors.append(f"Week {nxt.week_start} beginning cash does not follow prior ending cash")
        if item_hold_in_committed(rows):
            errors.append(f"Held AP invoice included as committed in {week.week_start}")
    return errors


def item_hold_in_committed(rows: list[ForecastLine]) -> bool:
    return any(item.hold and item.committed for item in rows)
