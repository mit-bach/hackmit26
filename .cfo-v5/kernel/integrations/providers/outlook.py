"""Microsoft Graph Outlook change notifications → shared email classifier."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import unquote_plus
import json

from integrations.ingest import ingest_email_record
from integrations.models import EmailSourceRecord, IntegrationResult, WebhookEvent
from integrations.providers.base import env, fixture_dir, load_json
from integrations.store import (
    payload_hash,
    remember_event,
    remember_outlook_subscription,
    update_event,
)

MAX_MESSAGE_SUB_MINUTES = 10080  # official max without resource data
RICH_MESSAGE_SUB_MINUTES = 1440


def client_state() -> str:
    return env("OUTLOOK_CLIENT_STATE", "outlook-client-state-hackmit")


def validation_response(token: str) -> str:
    """Return the URL-decoded validation token as plain text (Graph handshake)."""
    return unquote_plus(token)


def verify_notification(item: dict) -> bool:
    expected = client_state()
    got = str(item.get("clientState") or "")
    return got == expected


def event_id(item: dict) -> str:
    sub = str(item.get("subscriptionId") or "")
    resource_id = str((item.get("resourceData") or {}).get("id") or item.get("resource") or "")
    change = str(item.get("changeType") or "")
    return f"{sub}:{resource_id}:{change}"


def load_mailbox() -> dict:
    return load_json(fixture_dir("outlook") / "mailbox.json")


def fetch_outlook_message(message_id: str) -> dict | None:
    catalog = {item["id"]: item for item in load_mailbox().get("messages") or []}
    return catalog.get(message_id)


def _to_email_record(row: dict) -> EmailSourceRecord:
    attachments = []
    for item in row.get("attachments") or []:
        attachments.append(
            {
                "attachment_id": item.get("attachment_id") or item.get("id"),
                "filename": item.get("filename"),
                "content_type": item.get("content_type") or "application/pdf",
                "path": item.get("path"),
            }
        )
    return EmailSourceRecord(
        provider="outlook",
        message_id=str(row.get("id")),
        mailbox=str(row.get("mailbox") or env("OUTLOOK_MAILBOX") or "ap@hackmit-cfo.example"),
        sender=str(row.get("from") or ""),
        subject=str(row.get("subject") or ""),
        sent_at=row.get("sent_at"),
        body=str(row.get("body") or ""),
        thread_uri=row.get("thread_uri") or f"outlook://{row.get('id')}",
        attachments=attachments,
    )


def create_outlook_subscription(*, mailbox_oid: str | None = None, with_resource_data: bool = False) -> dict:
    minutes = RICH_MESSAGE_SUB_MINUTES if with_resource_data else MAX_MESSAGE_SUB_MINUTES
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    mailbox_oid = mailbox_oid or env("OUTLOOK_MAILBOX_OID") or "ap-mailbox-oid"
    payload = {
        "id": "outlook-sub-hackmit",
        "changeType": "created",
        "notificationUrl": env("OUTLOOK_NOTIFICATION_URL") or "https://example.invalid/webhooks/outlook",
        "lifecycleNotificationUrl": env("OUTLOOK_LIFECYCLE_URL") or None,
        "resource": f"users/{mailbox_oid}/messages",
        "expirationDateTime": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "clientState": client_state(),
        "maxExpirationMinutes": minutes,
    }
    remember_outlook_subscription(payload)
    return payload


def renew_outlook_subscription(subscription: dict | None = None) -> dict:
    current = subscription or create_outlook_subscription()
    return create_outlook_subscription(
        mailbox_oid=str(current.get("resource") or "").split("/")[1] if "/" in str(current.get("resource") or "") else None
    )


def handle_lifecycle(item: dict) -> IntegrationResult:
    lifecycle = str(item.get("lifecycleEvent") or item.get("changeType") or "")
    return IntegrationResult(
        provider="outlook",
        action="lifecycle",
        status="processed",
        provider_event_id=str(item.get("subscriptionId") or ""),
        message=f"lifecycle {lifecycle}",
        details={"lifecycle": lifecycle},
    )


def process_notification(item: dict, *, verified: bool, raw: bytes) -> IntegrationResult:
    if item.get("lifecycleEvent"):
        return handle_lifecycle(item)
    eid = event_id(item)
    envelope = WebhookEvent(
        provider="outlook",
        provider_event_id=eid,
        event_type=str(item.get("changeType") or "created"),
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"outlook:{eid}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="outlook",
            action="webhook",
            status="duplicate",
            provider_event_id=eid,
            duplicate=True,
            message="duplicate Graph notification; message not re-ingested",
        )
    resource_id = str((item.get("resourceData") or {}).get("id") or "")
    row = fetch_outlook_message(resource_id)
    if row is None:
        stored.processing_status = "processed"
        stored.result = "message_missing"
        update_event(stored)
        return IntegrationResult(
            provider="outlook",
            action="webhook",
            status="processed",
            provider_event_id=eid,
            message="notification resource not in mailbox snapshot",
        )
    record = _to_email_record(row)
    classification, reason, report = ingest_email_record(record, forward_to_ap=True)
    numbers = []
    candidates = 0
    if report:
        candidates = len(report.candidates)
        numbers = [item.vendor_invoice_number for item in report.canonical_invoices if item.vendor_invoice_number]
    stored.processing_status = "processed"
    stored.downstream = "invoice_ingestion"
    stored.result = classification
    stored.normalized_id = numbers[0] if numbers else None
    update_event(stored)
    return IntegrationResult(
        provider="outlook",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        invoice_candidates=candidates,
        invoice_numbers=numbers,
        classification=classification,
        message=reason,
        details={"message_id": resource_id, "subject": row.get("subject")},
    )


def process_raw(raw: bytes, headers: dict[str, str], *, require_signature: bool = True) -> IntegrationResult:
    payload = json.loads(raw.decode("utf-8") or "{}")
    items = payload.get("value") or ([payload] if payload else [])
    last = IntegrationResult(provider="outlook", action="webhook", status="ignored", message="empty notification")
    for item in items:
        if require_signature and not verify_notification(item):
            return IntegrationResult(
                provider="outlook",
                action="webhook",
                status="rejected",
                message="clientState mismatch",
            )
        last = process_notification(item, verified=True, raw=raw)
        if last.duplicate or last.status == "rejected":
            return last
    return last


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("outlook") / "notifications.json")
