"""Feed InvoiceCandidates from named providers into existing ingestion."""

from __future__ import annotations

from invoice_ingestion.interpret import interpret_email
from invoice_ingestion.models import InvoiceCandidate, IngestionReport
from invoice_ingestion.workflow import ingest_candidates
from integrations.models import EmailSourceRecord


def email_dict(record: EmailSourceRecord) -> dict:
    return {
        "message_id": record.message_id,
        "from": record.sender,
        "subject": record.subject,
        "body": record.body,
        "sent_at": record.sent_at,
        "thread_uri": record.thread_uri or f"{record.provider}://{record.message_id}",
        "attachments": record.attachments,
        "provider": record.provider,
    }


def classify_email(record: EmailSourceRecord) -> tuple[str, str, list[InvoiceCandidate]]:
    return interpret_email(email_dict(record))


def ingest_email_record(
    record: EmailSourceRecord,
    *,
    period: str = "2026-09",
    forward_to_ap: bool = True,
) -> tuple[str, str, IngestionReport | None]:
    classification, reason, candidates = classify_email(record)
    if not candidates:
        return classification, reason, None
    for item in candidates:
        context = dict(item.source_context or {})
        context["provider"] = record.provider
        item.source_context = context
    report = ingest_candidates(
        candidates,
        period=period,
        forward_to_ap=forward_to_ap,
        reset_overlay=False,
        save_trace=False,
    )
    return classification, reason, report
