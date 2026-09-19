"""As-of cutoff so discovery, tools, and backtests cannot see future close data."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class DataCutoff:
    period: str
    hide_period_invoices: bool = False
    allow_later_invoices: bool = False


_CUTOFF: ContextVar[DataCutoff | None] = ContextVar("accrual_cutoff", default=None)


def current_cutoff() -> DataCutoff | None:
    return _CUTOFF.get()


@contextmanager
def data_cutoff(
    period: str,
    hide_period_invoices: bool = False,
    allow_later_invoices: bool = False,
):
    token = _CUTOFF.set(
        DataCutoff(
            period=period,
            hide_period_invoices=hide_period_invoices,
            allow_later_invoices=allow_later_invoices,
        )
    )
    try:
        yield
    finally:
        _CUTOFF.reset(token)


def invoice_visible(service_period: str) -> bool:
    cutoff = current_cutoff()
    if cutoff is None:
        return True
    if service_period > cutoff.period:
        return False
    if service_period == cutoff.period and cutoff.hide_period_invoices:
        return False
    return True


def dated_visible(value: str | None) -> bool:
    cutoff = current_cutoff()
    if cutoff is None:
        return True
    if not value:
        return False
    return value[:7] <= cutoff.period


def later_invoices_allowed() -> bool:
    cutoff = current_cutoff()
    return cutoff is None or cutoff.allow_later_invoices
