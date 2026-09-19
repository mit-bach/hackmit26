"""NetSuite SuiteTalk REST vendorBill incremental sync. No inbound webhook."""

from __future__ import annotations

from typing import Any

from invoice_ingestion.interpret import from_structured_record
from invoice_ingestion.workflow import ingest_candidates
from integrations.models import IntegrationResult, WebhookEvent
from integrations.providers.base import fixture_dir, load_json
from integrations.store import payload_hash, remember_event, set_sync_cursor, sync_cursor, update_event

REST_RECORD = "vendorBill"
REST_PATH = "/services/rest/record/v1/vendorBill"


def load_bills() -> list[dict]:
    return load_json(fixture_dir("netsuite") / "vendor_bills.json")


def event_id(row: dict) -> str:
    return f"netsuite:{row.get('id')}:{row.get('lastModifiedDate') or 'na'}"


def to_candidate(row: dict):
    entity = row.get("entity") or {}
    po = row.get("purchaseOrder") or row.get("po_id")
    if isinstance(po, dict):
        po = po.get("refName") or po.get("id")
    return from_structured_record(
        {
            "vendor": entity.get("refName") or row.get("vendor"),
            "vendor_id": entity.get("id"),
            "invoice_number": row.get("tranId") or row.get("vendorInvoiceNumber"),
            "invoice_date": (row.get("tranDate") or "")[:10],
            "due_date": (row.get("dueDate") or "")[:10] or None,
            "currency": (row.get("currency") or {}).get("refName") if isinstance(row.get("currency"), dict) else row.get("currency") or "USD",
            "total": row.get("total") or row.get("userTotal"),
            "po_number": po,
        },
        source_type="erp",
        source_id=f"netsuite:{row.get('id')}",
        source_uri=f"netsuite://record/v1/vendorBill/{row.get('id')}",
        reason="NetSuite SuiteTalk REST vendorBill",
        extra_context={
            "provider": "netsuite",
            "internal_id": row.get("id"),
            "status": (row.get("status") or {}).get("refName") if isinstance(row.get("status"), dict) else row.get("status"),
            "rest_record": REST_RECORD,
        },
    )


def sync(*, cursor: str | None = None) -> IntegrationResult:
    rows = load_bills()
    last_seen = cursor or sync_cursor("netsuite")
    processed = 0
    numbers: list[str] = []
    for row in rows:
        eid = event_id(row)
        if last_seen and eid <= last_seen:
            continue
        envelope = WebhookEvent(
            provider="netsuite",
            provider_event_id=eid,
            event_type="netsuite.vendorbill.sync",
            verified=True,
            raw_payload_hash=payload_hash(eid),
            source_ref=f"netsuite:{row.get('id')}",
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
        stored.result = "vendor_bill_synced"
        update_event(stored)
        processed += 1
        set_sync_cursor("netsuite", eid)
    return IntegrationResult(
        provider="netsuite",
        action="sync",
        status="processed",
        invoice_candidates=processed,
        invoice_numbers=numbers,
        message=f"NetSuite REST {REST_PATH} synced {processed} vendor bill(s)",
        details={"record": REST_RECORD, "internal_ids": [row.get("id") for row in rows]},
    )


def demo_payloads() -> list[dict[str, Any]]:
    return [{"action": "sync"}]
