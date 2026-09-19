"""Stripe payout webhooks. Never produces InvoiceCandidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from integrations.cash import major_units, reconcile_payout
from integrations.models import IntegrationResult, PayoutLine, ProviderPayout, WebhookEvent
from integrations.providers.base import env, fixture_dir, live_mode, load_json
from integrations.store import (
    get_event,
    get_payout,
    payload_hash,
    remember_event,
    remember_payout,
    update_event,
)

PAYOUT_EVENTS = {
    "payout.created",
    "payout.updated",
    "payout.paid",
    "payout.failed",
    "payout.canceled",
    "payout.reconciliation_completed",
}


def _secret() -> str:
    return env("STRIPE_WEBHOOK_SECRET", "whsec_test_hackmit")


def verify_signature(raw: bytes, signature: str | None, secret: str | None = None) -> bool:
    secret = secret or _secret()
    if not signature:
        return False
    try:
        import stripe

        stripe.Webhook.construct_event(raw, signature, secret)
        return True
    except Exception:
        return False


def sign(raw: bytes, secret: str | None = None) -> str:
    import time

    import stripe

    secret = secret or _secret()
    return stripe.WebhookSignature.generate_header(int(time.time()), raw.decode("utf-8"), secret)


def event_id(payload: dict) -> str:
    return str(payload.get("id") or "")


def _created_at(payload: dict) -> datetime | None:
    created = payload.get("created")
    if isinstance(created, int):
        return datetime.fromtimestamp(created, tz=timezone.utc)
    return None


def _lines_from_balance_txns(rows: list[dict]) -> list[PayoutLine]:
    lines = []
    for row in rows:
        amount_minor = int(row.get("amount") or 0)
        currency = str(row.get("currency") or "usd").upper()
        source = row.get("source") if isinstance(row.get("source"), dict) else {}
        metadata = source.get("metadata") or {}
        reference = metadata.get("order_id") or source.get("id") or row.get("id")
        lines.append(
            PayoutLine(
                line_type=str(row.get("type") or "other"),
                amount=major_units(amount_minor, currency),
                currency=currency,
                reference=str(reference) if reference else None,
                description=str(row.get("description") or row.get("type") or ""),
                provider_object_id=str(row.get("id") or "") or None,
            )
        )
    return lines


def load_balance_transactions(payout_id: str) -> list[dict]:
    path = fixture_dir("stripe") / "balance_transactions.json"
    rows = load_json(path)
    return [row for row in rows if row.get("payout") == payout_id]


def load_bank_deposit(payout_id: str) -> dict | None:
    path = fixture_dir("stripe") / "bank_deposit.json"
    row = load_json(path)
    if row.get("payout_id") == payout_id:
        return row
    return None


def normalize_payout(payload: dict, lines: list[PayoutLine] | None = None) -> ProviderPayout:
    obj = payload.get("data", {}).get("object") or payload
    payout_id = str(obj.get("id") or "")
    amount = int(obj.get("amount") or 0)
    currency = str(obj.get("currency") or "usd").upper()
    arrival = obj.get("arrival_date")
    arrival_date = None
    if isinstance(arrival, int):
        arrival_date = datetime.fromtimestamp(arrival, tz=timezone.utc).date().isoformat()
    elif isinstance(arrival, str):
        arrival_date = arrival
    deposit = load_bank_deposit(payout_id)
    return ProviderPayout(
        provider="stripe",
        event_id=str(payload.get("id") or payout_id),
        payout_id=payout_id,
        status=str(obj.get("status") or ""),
        amount=amount,
        currency=currency,
        arrival_date=arrival_date,
        provider_created_at=str(obj.get("created") or payload.get("created") or ""),
        source_event_type=str(payload.get("type") or "payout"),
        raw_source_ref=f"stripe:{payload.get('id') or payout_id}",
        reference=obj.get("statement_descriptor") or obj.get("id"),
        lines=lines or [],
        bank_deposit_id=(deposit or {}).get("deposit_id"),
        bank_deposit_amount=(deposit or {}).get("amount"),
    )


def process_event(payload: dict, *, verified: bool, raw: bytes) -> IntegrationResult:
    event_type = str(payload.get("type") or "")
    eid = event_id(payload)
    envelope = WebhookEvent(
        provider="stripe",
        provider_event_id=eid or payload_hash(raw),
        event_type=event_type,
        provider_created_at=_created_at(payload),
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"stripe:{eid}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="duplicate",
            provider_event_id=stored.provider_event_id,
            duplicate=True,
            payout_id=stored.normalized_id,
            message="duplicate Stripe event; no second payout",
        )
    if event_type not in PAYOUT_EVENTS:
        stored.processing_status = "ignored"
        stored.result = "not_a_payout_event"
        update_event(stored)
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="ignored",
            provider_event_id=eid,
            message=f"ignored event type {event_type}",
        )
    lines: list[PayoutLine] = []
    obj = payload.get("data", {}).get("object") or {}
    payout_id = str(obj.get("id") or "")
    if event_type == "payout.reconciliation_completed" or not get_payout(payout_id):
        lines = _lines_from_balance_txns(load_balance_transactions(payout_id))
    payout = remember_payout(normalize_payout(payload, lines))
    stored.processing_status = "processed"
    stored.normalized_id = payout.payout_id
    stored.downstream = "cash_reconciliation"
    stored.result = "payout_recorded"
    update_event(stored)
    breakdown = reconcile_payout(payout)
    return IntegrationResult(
        provider="stripe",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        payout_id=payout.payout_id,
        payout_amount=major_units(payout.amount, payout.currency),
        invoice_candidates=0,
        message=f"{event_type} payout {payout.payout_id}",
        details={
            "matched": breakdown.matched,
            "expected": breakdown.expected_payout,
            "actual": breakdown.actual_payout,
            "source_count": len(payout.lines),
        },
    )


def process_raw(raw: bytes, headers: dict[str, str], *, require_signature: bool = True) -> IntegrationResult:
    signature = headers.get("stripe-signature") or headers.get("Stripe-Signature")
    if require_signature and not verify_signature(raw, signature):
        return IntegrationResult(
            provider="stripe",
            action="webhook",
            status="rejected",
            message="invalid Stripe-Signature",
        )
    payload = json.loads(raw.decode("utf-8"))
    return process_event(payload, verified=True, raw=raw)


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("stripe") / "events.json")
