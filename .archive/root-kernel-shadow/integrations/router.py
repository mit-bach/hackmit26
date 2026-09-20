"""Infer the destination workflow from an incoming provider event.

Callers do not name the agent. Classification is deterministic from the
event type; agents still decide what to do after the event is routed.
"""

from __future__ import annotations

from integrations.cash import classify_line
from integrations.models import PayoutLine

WORKFLOW_PAYOUT = "stripe_payout_reconciliation"
WORKFLOW_PAYMENT = "ar_cash_application"
WORKFLOW_REFUND = "ar_refund"
WORKFLOW_DISPUTE = "ar_dispute"
WORKFLOW_PAYMENT_FAILED = "payment_failed"
WORKFLOW_DUPLICATE = "idempotency"
WORKFLOW_IGNORED = "ignored"
WORKFLOW_BANK_EXCEPTION = "cash_reconciliation_exception"

STRIPE_PAYOUT_EVENTS = {
    "payout.created",
    "payout.updated",
    "payout.paid",
    "payout.failed",
    "payout.canceled",
    "payout.reconciliation_completed",
}
STRIPE_PAYMENT_EVENTS = {
    "payment_intent.succeeded",
    "charge.succeeded",
    "charge.captured",
}
STRIPE_PAYMENT_FAILED_EVENTS = {
    "payment_intent.payment_failed",
    "charge.failed",
}
STRIPE_REFUND_EVENTS = {
    "charge.refunded",
    "refund.created",
    "refund.updated",
}
STRIPE_DISPUTE_EVENTS = {
    "charge.dispute.created",
    "charge.dispute.closed",
    "charge.dispute.funds_withdrawn",
    "radar.early_fraud_warning.created",
}


def classify_stripe_event(event_type: str) -> str:
    kind = str(event_type or "").strip()
    if kind in STRIPE_PAYOUT_EVENTS:
        return WORKFLOW_PAYOUT
    if kind in STRIPE_PAYMENT_EVENTS:
        return WORKFLOW_PAYMENT
    if kind in STRIPE_REFUND_EVENTS:
        return WORKFLOW_REFUND
    if kind in STRIPE_DISPUTE_EVENTS:
        return WORKFLOW_DISPUTE
    if kind in STRIPE_PAYMENT_FAILED_EVENTS:
        return WORKFLOW_PAYMENT_FAILED
    return WORKFLOW_IGNORED


def classify_balance_transaction_type(line_type: str, description: str = "") -> str:
    line = PayoutLine(line_type=line_type, amount=0, description=description)
    return classify_line(line)


def classify_reconciliation_exception(exceptions: list[str]) -> str:
    if any("bank_amount_differs" in item for item in exceptions):
        return WORKFLOW_BANK_EXCEPTION
    if any("payout_amount_does_not_equal" in item for item in exceptions):
        return WORKFLOW_BANK_EXCEPTION
    return WORKFLOW_PAYOUT
