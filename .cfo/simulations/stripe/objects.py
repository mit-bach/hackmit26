"""Deterministic Stripe-API-shaped object builders. No network."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def unix(year: int, month: int, day: int, hour: int = 16) -> int:
    return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp())


def iso_date(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def standard_fee_cents(gross_cents: int) -> int:
    return int(round(gross_cents * 0.029)) + 30


def event(event_id: str, event_type: str, obj: dict[str, Any], created: int) -> dict[str, Any]:
    return {
        "id": event_id,
        "object": "event",
        "api_version": "2025-08-27.basil",
        "created": created,
        "type": event_type,
        "livemode": False,
        "data": {"object": obj},
    }


def customer(customer_id: str, name: str, email: str, created: int) -> dict[str, Any]:
    return {
        "id": customer_id,
        "object": "customer",
        "name": name,
        "email": email,
        "created": created,
        "metadata": {},
    }


def payment_intent(
    *,
    pi_id: str,
    amount: int,
    customer_id: str,
    created: int,
    status: str = "succeeded",
    charge_id: str = "",
    metadata: dict[str, str] | None = None,
    description: str = "",
    currency: str = "usd",
) -> dict[str, Any]:
    return {
        "id": pi_id,
        "object": "payment_intent",
        "amount": amount,
        "amount_received": amount if status == "succeeded" else 0,
        "currency": currency,
        "status": status,
        "customer": customer_id,
        "latest_charge": charge_id or None,
        "description": description,
        "metadata": dict(metadata or {}),
        "created": created,
    }


def charge(
    *,
    charge_id: str,
    amount: int,
    customer_id: str,
    customer_name: str,
    created: int,
    pi_id: str = "",
    metadata: dict[str, str] | None = None,
    description: str = "",
    status: str = "succeeded",
    refunded: bool = False,
    disputed: bool = False,
    currency: str = "usd",
    balance_transaction: str = "",
) -> dict[str, Any]:
    return {
        "id": charge_id,
        "object": "charge",
        "amount": amount,
        "amount_captured": amount if status == "succeeded" else 0,
        "amount_refunded": 0,
        "currency": currency,
        "paid": status == "succeeded",
        "status": status,
        "customer": customer_id,
        "payment_intent": pi_id,
        "balance_transaction": balance_transaction or None,
        "description": description,
        "refunded": refunded,
        "disputed": disputed,
        "billing_details": {"name": customer_name},
        "metadata": dict(metadata or {}),
        "created": created,
    }


def balance_transaction(
    *,
    txn_id: str,
    amount: int,
    fee: int,
    txn_type: str,
    payout_id: str | None,
    created: int,
    source: dict[str, Any] | str,
    description: str = "",
    currency: str = "usd",
) -> dict[str, Any]:
    signed_amount = amount
    if txn_type in {"refund", "payment_refund", "dispute", "chargeback", "stripe_fee"} and amount > 0:
        signed_amount = -abs(amount)
    if txn_type in {"charge", "payment"}:
        net = signed_amount - abs(fee)
        fee_value = abs(fee)
    else:
        net = signed_amount - abs(fee) if txn_type in {"dispute", "chargeback"} and fee else signed_amount
        fee_value = abs(fee)
    return {
        "id": txn_id,
        "object": "balance_transaction",
        "amount": signed_amount,
        "fee": fee_value,
        "net": net,
        "currency": currency,
        "type": txn_type,
        "description": description or txn_type,
        "payout": payout_id,
        "source": source,
        "created": created,
        "fee_details": [{"type": "stripe_fee", "amount": fee_value, "currency": currency}] if fee_value else [],
    }


def refund(
    *,
    refund_id: str,
    amount: int,
    charge_id: str,
    created: int,
    metadata: dict[str, str] | None = None,
    currency: str = "usd",
    payment_intent: str = "",
    balance_transaction: str = "",
) -> dict[str, Any]:
    return {
        "id": refund_id,
        "object": "refund",
        "amount": amount,
        "currency": currency,
        "charge": charge_id,
        "payment_intent": payment_intent or None,
        "balance_transaction": balance_transaction or None,
        "status": "succeeded",
        "reason": "requested_by_customer",
        "metadata": dict(metadata or {}),
        "created": created,
    }


def dispute(
    *,
    dispute_id: str,
    amount: int,
    charge_id: str,
    created: int,
    fee: int = 1500,
    reason: str = "fraudulent",
    currency: str = "usd",
    payment_intent: str = "",
    balance_transactions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": dispute_id,
        "object": "dispute",
        "amount": amount,
        "currency": currency,
        "charge": charge_id,
        "payment_intent": payment_intent or None,
        "reason": reason,
        "status": "lost",
        "fee": fee,
        "created": created,
        "balance_transactions": list(balance_transactions or []),
    }


def payout(
    *,
    payout_id: str,
    amount: int,
    created: int,
    arrival: int,
    status: str = "paid",
    currency: str = "usd",
) -> dict[str, Any]:
    return {
        "id": payout_id,
        "object": "payout",
        "amount": amount,
        "currency": currency,
        "arrival_date": arrival,
        "status": status,
        "created": created,
        "method": "standard",
        "type": "bank_account",
        "statement_descriptor": "STRIPE PAYOUT",
    }


def bank_deposit(
    *,
    deposit_id: str,
    payout_id: str,
    amount_cents: int,
    date: str,
    currency: str = "USD",
) -> dict[str, Any]:
    return {
        "deposit_id": deposit_id,
        "payout_id": payout_id,
        "amount": round(amount_cents / 100.0, 2),
        "amount_minor": amount_cents,
        "currency": currency,
        "date": date,
        "description": f"STRIPE PAYOUT {payout_id}",
    }
