"""Deterministic receivable cash-flow schedule. The LLM does not pick dates or amounts."""

from __future__ import annotations

from datetime import timedelta

from accrual.estimation import money
from ar.aging import days_past_due, parse_date
from ar.models import CustomerInvoice
from ar.store import all_invoices, all_payments, get_customer, precedents

BASE_CASE_MIN_CONFIDENCE = 0.5
RECEIVED_STATUSES = {"APPLIED", "PARTIALLY_APPLIED", "HUMAN_REVIEW"}


class CollectionCandidate:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def is_received_cash(payment) -> bool:
    """Cash that has hit the bank. Seed UNMATCHED inbox items are not treasury cash yet."""
    if payment.application_status in RECEIVED_STATUSES:
        return True
    metadata = getattr(payment, "metadata", None) or {}
    return bool(metadata.get("unapplied_after_review"))


def received_customer_cash(as_of: str, bank_as_of: str) -> list:
    """Payments already in the door after the last bank snapshot."""
    rows = []
    start = parse_date(bank_as_of)
    end = parse_date(as_of)
    for payment in all_payments():
        day = parse_date(payment.payment_date)
        if day <= start or day > end:
            continue
        if not is_received_cash(payment):
            continue
        rows.append(payment)
    return rows


def unapplied_received_by_customer(as_of: str, bank_as_of: str) -> dict[str, float]:
    """Haircut future AR so received-but-unallocated cash is not also forecast as a collection."""
    haircut: dict[str, float] = {}
    for payment in received_customer_cash(as_of, bank_as_of):
        if payment.application_status == "APPLIED":
            continue
        amount = money(payment.unapplied_amount or payment.amount)
        if amount <= 0:
            continue
        if payment.application_status == "PARTIALLY_APPLIED" or payment.application_status in {
            "HUMAN_REVIEW",
            "UNMATCHED",
        }:
            key = payment.customer_id or ""
            haircut[key] = money(haircut.get(key, 0) + amount)
    return haircut


def _expected_date(invoice: CustomerInvoice, as_of: str) -> tuple[str, str, float, list[str]]:
    customer = get_customer(invoice.customer_id)
    assumptions: list[str] = []
    on_time = customer.on_time_rate if customer else 0.7
    avg_late = customer.average_days_late if customer else 0
    behavior = customer.payment_behavior if customer else ""
    as_of_d = parse_date(as_of)

    if invoice.promised_pay_date and parse_date(invoice.promised_pay_date) >= as_of_d:
        assumptions.append(f"Promise to pay on {invoice.promised_pay_date} outranks the original due date")
        return invoice.promised_pay_date[:10], "promise_to_pay", 0.86, assumptions

    due = parse_date(invoice.due_date)
    dpd = days_past_due(invoice.due_date, as_of)
    if due >= as_of_d:
        if behavior == "chronic_late" and avg_late > 0:
            shifted = due + timedelta(days=avg_late)
            assumptions.append(f"Late-payer history shifts expected cash by {avg_late} days")
            return shifted.isoformat(), "due_date_shifted", 0.55, assumptions
        confidence = 0.82 if on_time >= 0.9 else 0.68 if on_time >= 0.6 else 0.52
        assumptions.append("Undisputed invoice scheduled on its due date")
        return invoice.due_date, "due_date", confidence, assumptions

    if dpd >= 91:
        later = as_of_d + timedelta(days=56)
        assumptions.append("90+ days overdue: excluded from certain near-term cash")
        return later.isoformat(), "severely_overdue", 0.28, assumptions
    shift = max(avg_late, 14 if behavior == "chronic_late" else 7)
    expected = as_of_d + timedelta(days=shift)
    assumptions.append(f"Already {dpd} days overdue; expected {shift} days from as-of")
    confidence = 0.48 if behavior == "chronic_late" else 0.58
    return expected.isoformat(), "overdue_shifted", confidence, assumptions


def receivable_schedule(as_of: str, *, bank_as_of: str | None = None) -> list[dict]:
    bank_as_of = bank_as_of or as_of
    haircut = unapplied_received_by_customer(as_of, bank_as_of)
    remaining_haircut = dict(haircut)
    rows: list[dict] = []
    invoices = [item for item in all_invoices() if money(item.outstanding_amount) > 0]
    invoices.sort(key=lambda item: (item.due_date, item.invoice_id))
    used_precedent = {item.customer_id: [p.precedent_id for p in precedents(item.customer_id)] for item in invoices}

    for invoice in invoices:
        expected_date, basis, confidence, assumptions = _expected_date(invoice, as_of)
        amount = money(invoice.outstanding_amount)
        disputed = invoice.dispute_status == "OPEN"
        if disputed:
            confidence = 0.15
            basis = "disputed"
            assumptions.append("Open dispute excluded from base-case cash")
        take = remaining_haircut.get(invoice.customer_id, 0)
        if take > 0 and not disputed:
            reduced = money(min(amount, take))
            amount = money(amount - reduced)
            remaining_haircut[invoice.customer_id] = money(take - reduced)
            assumptions.append(
                f"Unapplied received cash of ${reduced:,.2f} already in the bank for this customer"
            )
        in_base = (not disputed) and confidence >= BASE_CASE_MIN_CONFIDENCE and amount > 0
        rows.append(
            {
                "invoice_id": invoice.invoice_id,
                "customer_id": invoice.customer_id,
                "customer_name": invoice.customer_name,
                "outstanding_amount": money(invoice.outstanding_amount),
                "expected_collection_amount": amount if in_base else (0.0 if disputed or amount <= 0 else amount),
                "expected_collection_date": expected_date,
                "source_due_date": invoice.due_date,
                "basis": basis,
                "confidence": confidence,
                "dispute_flag": disputed,
                "promise_to_pay_flag": bool(invoice.promised_pay_date),
                "assumptions": assumptions,
                "in_base_case": in_base,
                "precedent_ids": used_precedent.get(invoice.customer_id, []),
            }
        )
        if not in_base and not disputed and amount > 0:
            rows[-1]["expected_collection_amount"] = amount
    return rows


def expected_collections(as_of: str, horizon_days: int = 7, *, bank_as_of: str | None = None) -> float:
    """Canonical forecast-facing expected receipts for a horizon. Disputed and low-confidence items excluded."""
    end = parse_date(as_of) + timedelta(days=horizon_days)
    total = 0.0
    for item in receivable_schedule(as_of, bank_as_of=bank_as_of):
        if not item["in_base_case"]:
            continue
        day = parse_date(item["expected_collection_date"])
        if parse_date(as_of) <= day <= end:
            total = money(total + item["expected_collection_amount"])
    return money(total)
