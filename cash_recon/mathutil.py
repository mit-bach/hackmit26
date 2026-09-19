"""Integer-cent arithmetic. Reuses integrations.cash; the LLM does not add these."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta

from integrations.cash import major_units, to_minor


def cents(amount: float | int | None) -> int:
    if amount is None:
        return 0
    return to_minor(float(amount))


def dollars(amount_minor: int, currency: str = "USD") -> float:
    return major_units(int(amount_minor), currency)


def money_text(amount: float | int | None) -> str:
    if amount is None:
        return "n/a"
    value = float(amount)
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def period_of(value: str) -> str:
    text = (value or "")[:10]
    if len(text) >= 7:
        return text[:7]
    return ""


def parse_date(value: str) -> date | None:
    text = (value or "")[:10]
    if len(text) < 10:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def date_diff_days(left: str, right: str) -> int | None:
    start = parse_date(left)
    end = parse_date(right)
    if start is None or end is None:
        return None
    return abs((start - end).days)


def date_gap(left: str, right: str, missing: int = 99) -> int:
    delta = date_diff_days(left, right)
    return missing if delta is None else delta


def period_end(period: str) -> date:
    year, month = int(period[:4]), int(period[5:7])
    return date(year, month, monthrange(year, month)[1])


def period_start(period: str) -> date:
    year, month = int(period[:4]), int(period[5:7])
    return date(year, month, 1)


def shift_period(period: str, months: int) -> str:
    year, month = int(period[:4]), int(period[5:7])
    month += months
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return f"{year:04d}-{month:02d}"


def adjacent_period(left: str, right: str) -> bool:
    if not left or not right or left == right:
        return False
    return shift_period(left, 1) == right or shift_period(right, 1) == left


def in_period(value: str, period: str) -> bool:
    return period_of(value) == period


def add_days(value: str, days: int) -> str:
    parsed = parse_date(value)
    if parsed is None:
        return value
    return (parsed + timedelta(days=days)).isoformat()
