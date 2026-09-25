"""Gmail Pub/Sub push → history.list → messages.get → shared email classifier."""

from __future__ import annotations

import base64
import json
from typing import Any

from integrations.ingest import ingest_email_record
from integrations.models import EmailSourceRecord, IntegrationResult, WebhookEvent
from integrations.providers.base import env, fixture_dir, live_mode, load_json
from integrations.store import (
    gmail_history_id,
    payload_hash,
    remember_event,
    set_gmail_history_id,
    update_event,
)


def verify_pubsub(headers: dict[str, str], *, require_auth: bool = False) -> bool:
    """Official Pub/Sub push auth is an OIDC Bearer JWT.

    Mock/demo mode does not require Google credentials. Live mode checks for a
    Bearer token and, when google-auth is installed, verifies iss/aud/email.
    """
    if not require_auth and not live_mode():
        return True
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return False
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return False
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        audience = env("GMAIL_PUSH_AUDIENCE") or env("GMAIL_PUBSUB_AUDIENCE") or None
        claims = id_token.verify_oauth2_token(token, google_requests.Request(), audience)
        if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
            return False
        expected_email = env("GMAIL_PUSH_SERVICE_ACCOUNT")
        if expected_email and claims.get("email") != expected_email:
            return False
        return True
    except ImportError:
        return True
    except Exception:
        return False


def decode_pubsub(payload: dict) -> dict:
    message = payload.get("message") or payload
    data = message.get("data") or ""
    if isinstance(data, str) and data:
        padded = data + "=" * (-len(data) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        return json.loads(decoded.decode("utf-8"))
    return {}


def event_id(payload: dict) -> str:
    message = payload.get("message") or {}
    return str(message.get("messageId") or message.get("message_id") or payload_hash(json.dumps(payload)))


def load_mailbox_state() -> dict:
    return load_json(fixture_dir("gmail") / "mailbox.json")


def _messages_since(mailbox: str, start_history_id: str | None, new_history_id: str) -> list[dict]:
    state = load_mailbox_state()
    history = state.get("history") or []
    start = int(start_history_id or "0")
    end = int(new_history_id)
    message_ids: list[str] = []
    for row in history:
        hid = int(row.get("id") or 0)
        if start < hid <= end:
            for added in row.get("messagesAdded") or []:
                mid = (added.get("message") or {}).get("id") or added.get("id")
                if mid:
                    message_ids.append(str(mid))
    catalog = {item["id"]: item for item in state.get("messages") or []}
    return [catalog[mid] for mid in message_ids if mid in catalog]


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
        provider="gmail",
        message_id=str(row.get("id")),
        mailbox=str(row.get("mailbox") or env("GMAIL_ACCOUNT") or "ap@hackmit-cfo.example"),
        sender=str(row.get("from") or ""),
        subject=str(row.get("subject") or ""),
        sent_at=row.get("sent_at"),
        body=str(row.get("body") or ""),
        thread_uri=row.get("thread_uri") or f"gmail://{row.get('id')}",
        attachments=attachments,
    )


def process_event(payload: dict, *, verified: bool, raw: bytes) -> IntegrationResult:
    eid = event_id(payload)
    notice = decode_pubsub(payload)
    mailbox = str(notice.get("emailAddress") or env("GMAIL_ACCOUNT") or "ap@hackmit-cfo.example")
    history_id = str(notice.get("historyId") or "")
    envelope = WebhookEvent(
        provider="gmail",
        provider_event_id=eid,
        event_type="gmail.history",
        verified=verified,
        raw_payload_hash=payload_hash(raw),
        source_ref=f"gmail:{mailbox}:{history_id}",
    )
    stored = remember_event(envelope)
    if stored.receipt_count > 1:
        return IntegrationResult(
            provider="gmail",
            action="webhook",
            status="duplicate",
            provider_event_id=eid,
            duplicate=True,
            message="duplicate Pub/Sub delivery; mailbox not re-ingested",
        )
    previous = gmail_history_id(mailbox)
    messages = _messages_since(mailbox, previous, history_id or "0")
    if history_id:
        set_gmail_history_id(mailbox, history_id)
    numbers: list[str] = []
    classifications: list[str] = []
    candidate_count = 0
    for row in messages:
        record = _to_email_record(row)
        classification, reason, report = ingest_email_record(record, forward_to_ap=True)
        classifications.append(classification)
        if report:
            candidate_count += len(report.candidates)
            numbers.extend(
                item.vendor_invoice_number for item in report.canonical_invoices if item.vendor_invoice_number
            )
    stored.processing_status = "processed"
    stored.downstream = "invoice_ingestion"
    stored.result = ",".join(classifications) or "no_new_messages"
    stored.normalized_id = numbers[0] if numbers else None
    update_event(stored)
    return IntegrationResult(
        provider="gmail",
        action="webhook",
        status="processed",
        provider_event_id=eid,
        invoice_candidates=candidate_count,
        invoice_numbers=numbers,
        classification=classifications[0] if classifications else None,
        message=f"historyId={history_id} messages={len(messages)}",
        details={"mailbox": mailbox, "history_id": history_id, "message_ids": [m["id"] for m in messages]},
    )


def process_raw(raw: bytes, headers: dict[str, str], *, require_signature: bool = True) -> IntegrationResult:
    if require_signature and not verify_pubsub(headers, require_auth=require_signature and live_mode()):
        return IntegrationResult(provider="gmail", action="webhook", status="rejected", message="invalid Pub/Sub auth")
    payload = json.loads(raw.decode("utf-8"))
    return process_event(payload, verified=True, raw=raw)


def renew_gmail_watch() -> dict[str, Any]:
    """Call users.watch. Official watches expire; Google requires renewal within 7 days."""
    if not live_mode():
        state = load_mailbox_state()
        return {
            "historyId": state.get("watch", {}).get("historyId", "1000"),
            "expiration": state.get("watch", {}).get("expiration", "1760000000000"),
            "mode": "mock",
        }
    # Live hook: callers supply google-api-python-client credentials.
    return {"mode": "live", "error": "live Gmail watch requires GOOGLE_APPLICATION_CREDENTIALS"}


def demo_payloads() -> list[dict[str, Any]]:
    return load_json(fixture_dir("gmail") / "pubsub.json")
