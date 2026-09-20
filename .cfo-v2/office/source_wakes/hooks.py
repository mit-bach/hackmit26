"""Webhook/poll → Source Bot land → Handle intents. Client, not Harness core."""

from __future__ import annotations

from pathlib import Path

from integrations.providers import gmail, outlook, xero
from invoice_ingestion.store import list_bank_transactions

from source_wakes.wakes import SourceWakeResult, land_bank_transaction, land_books_record, land_email_message, land_stripe_payout


def wake_stripe(computer: Path, raw: bytes, headers: dict[str, str]) -> list[SourceWakeResult]:
    return [land_stripe_payout(computer, raw, headers, provider="stripe")]


def wake_adyen(computer: Path, raw: bytes, headers: dict[str, str]) -> list[SourceWakeResult]:
    return [land_stripe_payout(computer, raw, headers, provider="adyen")]


def wake_gmail(computer: Path, raw: bytes, headers: dict[str, str]) -> list[SourceWakeResult]:
    result = gmail.process_raw(raw, headers, require_signature=False)
    message_ids = list((result.details or {}).get("message_ids") or [])
    return [land_email_message(computer, str(mid), profile="invoice") for mid in message_ids]


def wake_outlook(computer: Path, raw: bytes, headers: dict[str, str]) -> list[SourceWakeResult]:
    result = outlook.process_raw(raw, headers)
    resource = str((result.details or {}).get("message_id") or result.provider_event_id or "")
    if not resource:
        return []
    return [land_email_message(computer, resource, profile="invoice")]


def wake_xero(computer: Path, raw: bytes, headers: dict[str, str]) -> list[SourceWakeResult]:
    result = xero.process_raw(raw, headers)
    record_kind = "xero-accpay" if result.status == "processed" else "xero-accrec"
    classification = "invoice" if result.status == "processed" else str(result.classification or "ignored")
    source_id = str(result.invoice_numbers[0] if result.invoice_numbers else result.provider_event_id or "xero")
    return [
        land_books_record(
            computer,
            profile="erp-invoice",
            source_id=source_id,
            record_kind=record_kind,
            candidate=None,
            classification=classification if result.status == "processed" else "open-invoice" if classification == "ACCREC" else "not_invoice",
            reason=result.message,
        )
    ]


def poll_bank(computer: Path, period: str = "2026-09") -> list[SourceWakeResult]:
    rows = list_bank_transactions(period)
    return [
        land_bank_transaction(computer, str(row.get("transaction_id")), period=period)
        for row in rows
        if row.get("transaction_id")
    ]
