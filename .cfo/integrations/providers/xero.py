"""Xero invoice webhooks. Only ACCPAY bills enter AP ingestion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from invoice_ingestion.interpret import from_structured_record
from invoice_ingestion.workflow import ingest_candidates
from integrations.models import IntegrationResult, WebhookEvent
from integrations.providers.base import env, fixture_dir, hmac_sha256_b64, load_json
from integrations.store import payload_hash, remember_event, update_event


def webhook_key() -> str:
    return env("XERO_WEBHOOK_KEY", "xero-webhook-key-hackmit")


def verify_signature(raw: bytes, signature: str | None, key: str | None = None) -> bool:
    if not signature:
        return False
    expected = hmac_sha256_b64(raw, key or webhook_key())
    import hmac

    return hmac.compare_digest(expected, signature)


def sign(raw: bytes, key: str | None = None) -> str:
    return hmac_sha256_b64(raw, key or webhook_key())


def event_id(item: dict) -> str:
    return "|".join(
        [
            str(item.get("tenantId") or ""),
            str(item.get("resourceId") or ""),
            str(item.get("eventType") or ""),
            str(item.get("eventDateUtc") or ""),
        ]
    )


def load_bills() -> dict[str, dict]:
    rows = load_json(fixture_dir("xero") / "invoices.json")
    return {str(item["InvoiceID"]): item for item in rows}


def fetch_invoice(invoice_id: str) -> dict | None:
    return load_bills().get(invoice_id)


def _created_at(item: dict) -> datetime | None:
    raw = item.get("eventDateUtc")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def process_item(item: dict, *, verified: bool, raw: bytes) -> IntegrationResult:
    eid = event_id(item)
    envelope = WebhookEvent(
        provider="xero",
        provider_event_id=eid,
        event_type=f"{item.get('eventCategory')}.{item.get('eventType')}",
        provider_created_at=_created_at(item),
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"xero:{item.get('resourceId')}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="xero",
            action="webhook",
            status="duplicate",
            provider_event_id=eid,
            duplicate=True,
            message="duplicate Xero event; bill not re-ingested",
        )
    if str(item.get("eventCategory") or "").upper() != "INVOICE":
        stored.processing_status = "ignored"
        stored.result = "not_invoice_category"
        update_event(stored)
        return IntegrationResult(
            provider="xero",
            action="webhook",
            status="ignored",
            provider_event_id=eid,
            message="non-invoice Xero event stored only",
        )
    invoice = fetch_invoice(str(item.get("resourceId") or ""))
    if invoice is None:
        stored.processing_status = "error"
        stored.error = "invoice_not_found"
        update_event(stored)
        return IntegrationResult(provider="xero", action="webhook", status="error", message="Xero invoice fetch missed")
    invoice_type = str(invoice.get("Type") or "")
    if invoice_type != "ACCPAY":
        stored.processing_status = "ignored"
        stored.result = f"skipped_{invoice_type or 'unknown_type'}"
        update_event(stored)
        return IntegrationResult(
            provider="xero",
            action="webhook",
            status="ignored",
            provider_event_id=eid,
            classification=invoice_type,
            message=f"Xero {invoice_type} is not an AP bill",
            details={"invoice_id": invoice.get("InvoiceID"), "type": invoice_type},
        )
    contact = invoice.get("Contact") or {}
    candidate = from_structured_record(
        {
            "vendor": contact.get("Name"),
            "vendor_id": contact.get("ContactID"),
            "invoice_number": invoice.get("InvoiceNumber"),
            "invoice_date": invoice.get("Date"),
            "due_date": invoice.get("DueDate"),
            "currency": invoice.get("CurrencyCode") or "USD",
            "subtotal": invoice.get("SubTotal"),
            "tax": invoice.get("TotalTax"),
            "total": invoice.get("Total"),
            "po_number": invoice.get("Reference"),
        },
        source_type="erp",
        source_id=f"xero:{invoice['InvoiceID']}",
        source_uri=item.get("resourceUrl"),
        reason="Xero Accounting API bill fetched after INVOICE webhook",
        extra_context={"provider": "xero", "type": "ACCPAY", "tenant_id": item.get("tenantId")},
    )
    report = ingest_candidates([candidate], forward_to_ap=True, reset_overlay=False, save_trace=False)
    numbers = [row.vendor_invoice_number for row in report.canonical_invoices]
    stored.processing_status = "processed"
    stored.downstream = "invoice_ingestion"
    stored.normalized_id = numbers[0] if numbers else None
    stored.result = "bill_ingested"
    update_event(stored)
    return IntegrationResult(
        provider="xero",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        invoice_candidates=len(report.candidates),
        invoice_numbers=numbers,
        message=f"Xero bill {invoice.get('InvoiceNumber')}",
        details={"invoice_id": invoice.get("InvoiceID")},
    )


def process_raw(raw: bytes, headers: dict[str, str], *, require_signature: bool = True) -> IntegrationResult:
    signature = headers.get("x-xero-signature") or headers.get("X-Xero-Signature")
    if require_signature and not verify_signature(raw, signature):
        return IntegrationResult(provider="xero", action="webhook", status="rejected", message="invalid x-xero-signature")
    payload = json.loads(raw.decode("utf-8"))
    last = IntegrationResult(provider="xero", action="webhook", status="ignored", message="no events")
    for item in payload.get("events") or []:
        last = process_item(item, verified=True, raw=raw)
        if last.status == "rejected":
            return last
    return last


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("xero") / "webhooks.json")
