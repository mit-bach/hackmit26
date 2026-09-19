"""Deterministic prepaid schedules. Agents may choose a method; they do not invent amounts."""

from __future__ import annotations

from close.dates import (
    money,
    overlap_days,
    parse_iso_date,
    period_end,
    period_from_date,
    periods_inclusive,
)
from prepaid.models import PrepaidItem, PrepaidScheduleLine, TreatmentCandidate


def validate_prepaid(item: PrepaidItem) -> None:
    if item.total_amount < 0:
        raise ValueError("Invalid negative prepaid amount.")
    if item.total_amount == 0:
        raise ValueError("Prepaid amount must be positive.")
    if not item.start_date or not item.end_date:
        raise ValueError("Missing service period: coverage dates are required.")
    start = parse_iso_date(item.start_date)
    end = parse_iso_date(item.end_date)
    if end < start:
        raise ValueError("Invalid service period: end date is before start date.")


def generate_schedule(item: PrepaidItem, method: str | None = None) -> list[PrepaidScheduleLine]:
    validate_prepaid(item)
    chosen = method or item.amortization_method
    if chosen == "immediate_expense":
        return _immediate(item)
    if chosen == "daily_prorate":
        return _daily(item)
    return _straight_line(item)


def _lines_from_amounts(
    item: PrepaidItem,
    amounts: list[tuple[str, float, int]],
    method: str,
) -> list[PrepaidScheduleLine]:
    if not amounts:
        raise ValueError("Service period does not overlap any accounting month.")
    rounded = [money(amount) for _, amount, _ in amounts]
    drift = money(item.total_amount - sum(rounded[:-1]))
    rounded[-1] = drift
    if money(sum(rounded)) != money(item.total_amount):
        raise ValueError("Schedule does not sum to the original prepaid amount.")
    lines = []
    for (period, _raw, days), amount in zip(amounts, rounded):
        if amount < 0:
            raise ValueError("Schedule produced a negative period amount.")
        lines.append(
            PrepaidScheduleLine(
                prepaid_id=item.prepaid_id,
                period=period,
                amount=amount,
                method=method,  # type: ignore[arg-type]
                days_in_period=days,
                evidence_refs=list(item.evidence_refs),
            )
        )
    return lines


def _straight_line(item: PrepaidItem) -> list[PrepaidScheduleLine]:
    periods = periods_inclusive(item.start_date, item.end_date)
    each = item.total_amount / len(periods)
    amounts = [(period, each, overlap_days(parse_iso_date(item.start_date), parse_iso_date(item.end_date), period)) for period in periods]
    return _lines_from_amounts(item, amounts, "straight_line_monthly")


def _daily(item: PrepaidItem) -> list[PrepaidScheduleLine]:
    start = parse_iso_date(item.start_date)
    end = parse_iso_date(item.end_date)
    total_days = (end - start).days + 1
    if total_days <= 0:
        raise ValueError("Invalid service period.")
    amounts = []
    for period in periods_inclusive(item.start_date, item.end_date):
        days = overlap_days(start, end, period)
        if days <= 0:
            continue
        amounts.append((period, item.total_amount * days / total_days, days))
    return _lines_from_amounts(item, amounts, "daily_prorate")


def _immediate(item: PrepaidItem) -> list[PrepaidScheduleLine]:
    start = period_from_date(item.start_date)
    end = period_from_date(item.end_date)
    if start != end:
        raise ValueError("Immediate expense is only valid when the service period is one month.")
    days = overlap_days(parse_iso_date(item.start_date), parse_iso_date(item.end_date), start)
    return _lines_from_amounts(item, [(start, item.total_amount, days)], "immediate_expense")


def remaining_balance(item: PrepaidItem, posted: list[PrepaidScheduleLine], method: str | None = None) -> float:
    schedule = generate_schedule(item, method)
    posted_periods = {line.period for line in posted if line.status == "posted"}
    return money(sum(line.amount for line in schedule if line.period not in posted_periods))


def treatment_candidates(item: PrepaidItem) -> list[TreatmentCandidate]:
    validate_prepaid(item)
    start = parse_iso_date(item.start_date)
    end = parse_iso_date(item.end_date)
    same_month = period_from_date(start) == period_from_date(end)
    partial = start.day != 1 or end != period_end(period_from_date(end))
    periods = periods_inclusive(item.start_date, item.end_date)
    rows = [
        TreatmentCandidate(
            method="straight_line_monthly",
            applicable=True,
            amount=money(item.total_amount / len(periods)),
            rationale=f"Equal monthly amortization across {len(periods)} months.",
            periods=len(periods),
        ),
        TreatmentCandidate(
            method="daily_prorate",
            applicable=True,
            amount=None,
            rationale="Allocate by days in each calendar month. Use when the first or last month is partial.",
            periods=len(periods),
        ),
        TreatmentCandidate(
            method="immediate_expense",
            applicable=same_month,
            amount=item.total_amount if same_month else None,
            rationale=(
                "Service begins and ends in the same month, so the payment can be expensed immediately."
                if same_month
                else "Service spans more than one month, so immediate expense is not applicable."
            ),
            periods=1 if same_month else len(periods),
        ),
    ]
    if partial:
        rows[1].rationale = "First or last month is a partial service period; daily proration is the stronger candidate."
    return rows


def select_treatment(item: PrepaidItem) -> str:
    """Deterministic policy. The agent may pick a different applicable candidate."""
    if not item.start_date or not item.end_date:
        return "insufficient_evidence"
    if not item.evidence_refs or not item.source_document_id:
        return "insufficient_evidence"
    start = parse_iso_date(item.start_date)
    end = parse_iso_date(item.end_date)
    if period_from_date(start) == period_from_date(end):
        return "immediate_expense"
    if start.day != 1 or end != period_end(period_from_date(end)):
        return "daily_prorate"
    return "straight_line_monthly"
