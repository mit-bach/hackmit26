"""Shared date/period helpers. Accounting arithmetic still uses money()."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone

from accrual.estimation import money

__all__ = [
    "add_months",
    "money",
    "month_name",
    "now_iso",
    "overlap_days",
    "parse_iso_date",
    "parse_period",
    "period_end",
    "period_from_date",
    "period_start",
    "periods_inclusive",
]


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def parse_period(period: str) -> tuple[int, int]:
    year_str, month_str = period.split("-", 1)
    return int(year_str), int(month_str)


def period_from_date(value: str | date) -> str:
    if isinstance(value, date):
        return f"{value.year}-{value.month:02d}"
    return value[:7]


def period_start(period: str) -> date:
    year, month = parse_period(period)
    return date(year, month, 1)


def period_end(period: str) -> date:
    year, month = parse_period(period)
    return date(year, month, monthrange(year, month)[1])


def add_months(period: str, count: int) -> str:
    year, month = parse_period(period[:7])
    index = year * 12 + (month - 1) + count
    return f"{index // 12}-{index % 12 + 1:02d}"


def periods_inclusive(start: str, end: str) -> list[str]:
    first = period_from_date(start)
    last = period_from_date(end)
    if first > last:
        raise ValueError(f"Invalid period range {start} to {end}")
    rows = []
    current = first
    while current <= last:
        rows.append(current)
        current = add_months(current, 1)
    return rows


def overlap_days(start: date, end: date, period: str) -> int:
    window_start = max(start, period_start(period))
    window_end = min(end, period_end(period))
    if window_end < window_start:
        return 0
    return (window_end - window_start).days + 1


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def month_name(period: str) -> str:
    names = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    return names.get(period[5:7], period)
