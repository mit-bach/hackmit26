"""Shared AR snapshots for forecast, bank rec, close, audit, and reporting."""

from __future__ import annotations

from accrual.estimation import money
from ar.aging import build_aging_report
from ar.models import ARCloseSnapshot
from ar.schedule import expected_collections as live_expected_collections
from ar.schedule import receivable_schedule
from ar.store import all_payments, events, journals, outbox


def expected_collections(as_of: str, horizon_days: int = 7, *, bank_as_of: str | None = None) -> float:
    """Canonical forecast-facing expected receipts. Sourced from the AR receivable schedule."""
    return live_expected_collections(as_of, horizon_days, bank_as_of=bank_as_of)


def incoming_customer_payments() -> list[dict]:
    rows = []
    for payment in all_payments():
        rows.append(
            {
                "payment_id": payment.payment_id,
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "currency": payment.currency,
                "payer_name": payment.payer_name,
                "bank_reference": payment.bank_reference,
                "application_status": payment.application_status,
                "unapplied_amount": payment.unapplied_amount,
                "source": payment.source,
            }
        )
    return rows


def unapplied_cash_total() -> float:
    return money(
        sum(
            payment.unapplied_amount
            for payment in all_payments()
            if payment.application_status in {"UNMATCHED", "HUMAN_REVIEW", "PARTIALLY_APPLIED"}
        )
    )


def ar_close_snapshot(as_of: str) -> ARCloseSnapshot:
    report = build_aging_report(as_of, persist=False)
    payments = all_payments()
    return ARCloseSnapshot(
        as_of_date=as_of,
        total_ar=report.totals.total_ar,
        current_ar=report.totals.current_ar,
        past_due_ar=report.totals.past_due_ar,
        disputed_ar=report.totals.disputed_ar,
        partially_paid_ar=report.totals.partially_paid_ar,
        unapplied_cash=unapplied_cash_total(),
        aging_buckets=dict(report.totals.bucket_amounts),
        open_invoice_count=report.totals.open_invoice_count,
        expected_collections_7d=expected_collections(as_of, 7),
        past_due_customer_count=sum(1 for item in report.customers if item.amount_past_due > 0),
        payments_applied=sum(1 for item in payments if item.application_status in {"APPLIED", "PARTIALLY_APPLIED"}),
        payments_unapplied=sum(1 for item in payments if item.application_status == "UNMATCHED"),
        payments_human_review=sum(1 for item in payments if item.application_status == "HUMAN_REVIEW"),
        collection_outbox=len(outbox()),
    )


def audit_trail(payment_id: str = "") -> list[dict]:
    rows = [item.model_dump(mode="json") for item in events()]
    if payment_id:
        rows = [item for item in rows if item.get("payment_id") == payment_id]
    return rows


def shared_journal() -> list[dict]:
    """AR journals in the same shape close/audit can consume next to accrual journals."""
    return [item.model_dump(mode="json") for item in journals()]
