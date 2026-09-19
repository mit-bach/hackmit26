"""Adyen transfer webhooks. Never produces InvoiceCandidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from integrations.cash import major_units, reconcile_payout
from integrations.models import IntegrationResult, PayoutLine, ProviderPayout, WebhookEvent
from integrations.providers.base import env, fixture_dir, hmac_sha256_hex_key_b64, load_json
from integrations.store import payload_hash, remember_event, remember_payout, update_event

TRANSFER_TYPES = {
    "balancePlatform.transfer.created",
    "balancePlatform.transfer.updated",
}


def _hmac_key() -> str:
    # Official Adyen HMAC keys are hex. Mock key is 32 bytes as hex.
    return env("ADYEN_HMAC_KEY", "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")


def verify_hmac(raw: bytes, signature: str | None, hex_key: str | None = None) -> bool:
    if not signature:
        return False
    expected = hmac_sha256_hex_key_b64(raw, hex_key or _hmac_key())
    import hmac as hmac_mod

    return hmac_mod.compare_digest(expected, signature)


def sign(raw: bytes, hex_key: str | None = None) -> str:
    return hmac_sha256_hex_key_b64(raw, hex_key or _hmac_key())


def event_id(payload: dict) -> str:
    data = payload.get("data") or {}
    transfer_id = str(data.get("id") or "")
    status = str(data.get("status") or "")
    event_type = str(payload.get("type") or "")
    return f"{event_type}:{transfer_id}:{status}"


def _created_at(payload: dict) -> datetime | None:
    data = payload.get("data") or {}
    for key in ("creationDate", "valueDate", "updateDate"):
        value = data.get(key)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    return None


def load_related_transactions(transfer_id: str) -> list[dict]:
    path = fixture_dir("adyen") / "transactions.json"
    rows = load_json(path)
    return [row for row in rows if row.get("transfer_id") == transfer_id]


def load_bank_deposit(transfer_id: str) -> dict | None:
    path = fixture_dir("adyen") / "bank_deposit.json"
    row = load_json(path)
    if row.get("transfer_id") == transfer_id:
        return row
    return None


def _lines(transfer_id: str) -> list[PayoutLine]:
    lines = []
    for row in load_related_transactions(transfer_id):
        amount_minor = int(row.get("amount") or 0)
        currency = str(row.get("currency") or "USD").upper()
        lines.append(
            PayoutLine(
                line_type=str(row.get("type") or "other"),
                amount=major_units(amount_minor, currency),
                currency=currency,
                reference=row.get("reference") or row.get("pspReference"),
                description=str(row.get("description") or ""),
                provider_object_id=row.get("id"),
            )
        )
    return lines


def normalize_payout(payload: dict) -> ProviderPayout:
    data = payload.get("data") or {}
    amount = data.get("amount") or {}
    transfer_id = str(data.get("id") or "")
    deposit = load_bank_deposit(transfer_id)
    value = int(amount.get("value") or 0)
    currency = str(amount.get("currency") or "USD").upper()
    return ProviderPayout(
        provider="adyen",
        event_id=event_id(payload),
        payout_id=transfer_id,
        status=str(data.get("status") or ""),
        amount=value,
        currency=currency,
        arrival_date=str(data.get("valueDate") or "")[:10] or None,
        provider_created_at=str(data.get("creationDate") or ""),
        source_event_type=str(payload.get("type") or ""),
        raw_source_ref=f"adyen:{transfer_id}",
        reference=data.get("reference"),
        lines=_lines(transfer_id),
        bank_deposit_id=(deposit or {}).get("deposit_id"),
        bank_deposit_amount=(deposit or {}).get("amount"),
    )


def process_event(payload: dict, *, verified: bool, raw: bytes) -> IntegrationResult:
    eid = event_id(payload)
    event_type = str(payload.get("type") or "")
    envelope = WebhookEvent(
        provider="adyen",
        provider_event_id=eid or payload_hash(raw),
        event_type=event_type,
        provider_created_at=_created_at(payload),
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"adyen:{eid}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="adyen",
            action="webhook",
            status="duplicate",
            provider_event_id=stored.provider_event_id,
            duplicate=True,
            payout_id=stored.normalized_id,
            message="duplicate Adyen notification; no second payout",
        )
    if event_type not in TRANSFER_TYPES:
        stored.processing_status = "ignored"
        stored.result = "not_a_transfer_event"
        update_event(stored)
        return IntegrationResult(
            provider="adyen",
            action="webhook",
            status="ignored",
            provider_event_id=eid,
            message=f"ignored event type {event_type}",
        )
    payout = remember_payout(normalize_payout(payload))
    stored.processing_status = "processed"
    stored.normalized_id = payout.payout_id
    stored.downstream = "cash_reconciliation"
    stored.result = "transfer_recorded"
    update_event(stored)
    breakdown = reconcile_payout(payout)
    return IntegrationResult(
        provider="adyen",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        payout_id=payout.payout_id,
        payout_amount=major_units(payout.amount, payout.currency),
        invoice_candidates=0,
        message=f"{event_type} transfer {payout.payout_id}",
        details={
            "status": payout.status,
            "matched": breakdown.matched,
            "expected": breakdown.expected_payout,
            "actual": breakdown.actual_payout,
        },
    )


def process_raw(raw: bytes, headers: dict[str, str], *, require_signature: bool = True) -> IntegrationResult:
    signature = headers.get("hmacsignature") or headers.get("HmacSignature")
    if require_signature and not verify_hmac(raw, signature):
        return IntegrationResult(
            provider="adyen",
            action="webhook",
            status="rejected",
            message="invalid Adyen HMAC signature",
        )
    payload = json.loads(raw.decode("utf-8"))
    return process_event(payload, verified=True, raw=raw)


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("adyen") / "events.json")
