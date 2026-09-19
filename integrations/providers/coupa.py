"""Coupa Core Invoice API incremental sync. No webhook is documented for this use case."""

from __future__ import annotations

from typing import Any

from invoice_ingestion.interpret import from_structured_record
from invoice_ingestion.workflow import ingest_candidates
from integrations.models import IntegrationResult, WebhookEvent
from integrations.providers.base import fixture_dir, load_json
from integrations.store import payload_hash, remember_event, set_sync_cursor, sync_cursor, update_event


def load_invoices() -> list[dict]:
    return load_json(fixture_dir("coupa") / "invoices.json")


def event_id(row: dict) -> str:
    return f"coupa:{row.get('id')}:{row.get('updated-at') or row.get('updated_at') or 'na'}"


def to_candidate(row: dict):
    po = row.get("po-number") or row.get("po_number") or (row.get("order-header") or {}).get("po-number")
    supplier = row.get("supplier") or {}
    return from_structured_record(
        {
            "vendor": supplier.get("name") or row.get("supplier-name"),
            "vendor_id": supplier.get("id") or row.get("supplier-id"),
            "invoice_number": row.get("invoice-number") or row.get("invoice_number"),
            "invoice_date": (row.get("invoice-date") or row.get("invoice_date") or "")[:10],
            "due_date": (row.get("due-date") or "")[:10] or None,
            "currency": (row.get("currency") or {}).get("code") if isinstance(row.get("currency"), dict) else row.get("currency") or "USD",
            "subtotal": row.get("net-due") or row.get("subtotal"),
            "tax": row.get("tax-amount") or row.get("tax"),
            "total": row.get("gross-total") or row.get("total"),
            "po_number": po,
            "line_items": row.get("invoice-lines") or row.get("line_items") or [],
        },
        source_type="procurement",
        source_id=f"coupa:{row.get('id')}",
        source_uri=f"coupa://invoices/{row.get('id')}",
        reason="Coupa Invoice API record; three-way match left to AP workflow",
        extra_context={
            "provider": "coupa",
            "status": row.get("status"),
            "po_number": po,
            "receiving": row.get("receiving") or [],
        },
    )


def sync(*, cursor: str | None = None) -> IntegrationResult:
    rows = load_invoices()
    last_seen = cursor or sync_cursor("coupa")
    processed = 0
    numbers: list[str] = []
    for row in rows:
        eid = event_id(row)
        if last_seen and eid <= last_seen:
            continue
        envelope = WebhookEvent(
            provider="coupa",
            provider_event_id=eid,
            event_type="coupa.invoice.sync",
            verified=True,
            raw_payload_hash=payload_hash(eid),
            source_ref=f"coupa:{row.get('id')}",
        )
        stored = remember_event(envelope)
        if stored.receipt_count > 1:
            continue
        candidate = to_candidate(row)
        report = ingest_candidates([candidate], forward_to_ap=True, reset_overlay=False, save_trace=False)
        numbers.extend(item.vendor_invoice_number for item in report.canonical_invoices)
        stored.processing_status = "processed"
        stored.downstream = "invoice_ingestion"
        stored.normalized_id = candidate.vendor_invoice_number
        stored.result = "invoice_synced"
        update_event(stored)
        processed += 1
        set_sync_cursor("coupa", eid)
    return IntegrationResult(
        provider="coupa",
        action="sync",
        status="processed",
        invoice_candidates=processed,
        invoice_numbers=numbers,
        message=f"Coupa Invoice API synced {processed} record(s)",
        details={"cursor": sync_cursor("coupa"), "po_preserved": True, "three_way_match": False},
    )


def demo_payloads() -> list[dict[str, Any]]:
    return [{"action": "sync"}]
