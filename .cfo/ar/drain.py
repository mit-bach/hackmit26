"""Apply-before-collect gate. New deposits must be seen by apply for the as-of date."""

from __future__ import annotations

from accrual.estimation import money
from ar.models import CustomerPayment
from ar.store import all_payments, save_payment

APPLY_DRAINED_KEY = "apply_drained_as_of"


def is_apply_drained(payment: CustomerPayment) -> bool:
    if payment.application_status != "UNMATCHED":
        return True
    return bool((payment.metadata or {}).get(APPLY_DRAINED_KEY))


def new_deposits(as_of: str) -> list[CustomerPayment]:
    """Payments dated on or before as-of that apply has not processed."""
    rows = []
    for payment in all_payments():
        if payment.payment_date > as_of:
            continue
        if is_apply_drained(payment):
            continue
        rows.append(payment)
    return rows


def mark_apply_drained(payment: CustomerPayment, as_of: str) -> CustomerPayment:
    metadata = dict(payment.metadata or {})
    metadata[APPLY_DRAINED_KEY] = as_of
    updated = payment.model_copy(update={"metadata": metadata})
    return save_payment(updated)


def customer_has_unapplied_cash(customer_id: str) -> bool:
    if not customer_id:
        return False
    for payment in all_payments():
        if payment.customer_id != customer_id:
            continue
        if money(payment.unapplied_amount) <= 0:
            continue
        if payment.application_status in {"UNMATCHED", "HUMAN_REVIEW", "PARTIALLY_APPLIED"}:
            return True
    return False
