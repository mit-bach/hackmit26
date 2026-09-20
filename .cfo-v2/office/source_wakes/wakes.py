"""Source Bot wake host: Kernel lands the object, Client emits Handle intents.

Pi completion is not required. The send payload is the proof that a Bot would
call bot_send_prompt. This module does not match, pay, apply, accrue, or lock.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from integrations.models import EmailSourceRecord
from integrations.providers import adyen, stripe
from integrations.store import get_payout, get_reconciliation
from invoice_ingestion.interpret import interpret_email
from invoice_ingestion.models import InvoiceCandidate
from invoice_ingestion.sources import run_bank_card_source
from invoice_ingestion.store import get_bank_transaction, get_email
from invoice_ingestion.workflow import ingest_candidates

from source_wakes.destinations import (
    BANK_LINE,
    STRIPE_CHARGES,
    STRIPE_DEPOSIT,
    books_destination,
    email_destination,
)
from source_wakes.packets import write_packet


def bot_id_for_slug(slug: str) -> str:
    return f"bot_{slug.replace('-', '_')}"


@dataclass(frozen=True)
class HandleIntent:
    from_slug: str
    to_slug: str
    profile: str
    paths: list[str]
    prompt: str
    kind: str = "a2a_handoff"
    mode: str = "async"
    on_busy: str = "queue"
    idempotency_key: str = ""

    def to_send_payload(self) -> dict[str, Any]:
        return {
            "from": bot_id_for_slug(self.from_slug),
            "to": bot_id_for_slug(self.to_slug),
            "toSlug": self.to_slug,
            "profile": self.profile,
            "prompt": self.prompt,
            "paths": list(self.paths),
            "kind": self.kind,
            "mode": self.mode,
            "onBusy": self.on_busy,
            "idempotencyKey": self.idempotency_key,
        }


@dataclass
class SourceWakeResult:
    slug: str
    profile: str
    source_id: str
    classification: str
    reason: str
    packet_path: str | None
    intents: list[HandleIntent] = field(default_factory=list)
    invoice_candidates: int = 0
    kernel_status: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def _wake_prompt(profile: str, path: str, sentence: str) -> str:
    return f"profile: {profile}\npath: {path}\n{sentence}"


def _intent(
    *,
    from_slug: str,
    to_slug: str,
    profile: str,
    path: str,
    source_id: str,
    sentence: str,
) -> HandleIntent:
    key = f"{from_slug}:{source_id}:{to_slug}:{profile}"
    return HandleIntent(
        from_slug=from_slug,
        to_slug=to_slug,
        profile=profile,
        paths=[path],
        prompt=_wake_prompt(profile, path, sentence),
        idempotency_key=key,
    )


def land_email_message(
    computer: Path,
    message_id: str,
    *,
    profile: str = "invoice",
    email: dict | None = None,
    period: str = "2026-09",
) -> SourceWakeResult:
    """Classify one message. Invoice → ap. Remittance → apply. Not a bill approval."""
    row = email if email is not None else get_email(message_id)
    if row is None:
        return SourceWakeResult(
            slug="email",
            profile=profile,
            source_id=message_id,
            classification="unreadable",
            reason=f"Email {message_id} was not found. Do not invent message data.",
            packet_path=None,
        )
    classification, reason, candidates = interpret_email(row)
    candidate_dump = None
    canonical_id = None
    if classification == "invoice" and candidates:
        report = ingest_candidates(
            candidates,
            period=period,
            forward_to_ap=True,
            reset_overlay=False,
            save_trace=False,
        )
        if report.canonical_invoices:
            canonical_id = report.canonical_invoices[0].canonical_id
        candidate_dump = candidates[0].model_dump(mode="json")
        # Packet names ids. It does not paste attachment text.
        if isinstance(candidate_dump, dict):
            candidate_dump.pop("evidence", None)
            context = dict(candidate_dump.get("source_context") or {})
            context.pop("text", None)
            candidate_dump["source_context"] = context
    dest = email_destination(classification)
    payload = {
        "bot": "email",
        "profile": profile,
        "source_id": message_id,
        "classification": classification,
        "reason": reason,
        "canonical_id": canonical_id,
        "candidate": candidate_dump if classification == "invoice" else None,
        "destination": {"slug": dest[0], "profile": dest[1]} if dest else None,
    }
    path = write_packet(computer, "email", message_id, payload)
    intents: list[HandleIntent] = []
    if dest is not None:
        to_slug, to_profile = dest
        sentence = (
            "Landed a vendor bill. Kernel already extracted fields. Do not invent amounts."
            if to_slug == "ap"
            else "Landed a customer remittance. Do not apply cash in this Bot."
        )
        intents.append(
            _intent(
                from_slug="email",
                to_slug=to_slug,
                profile=to_profile,
                path=path,
                source_id=message_id,
                sentence=sentence,
            )
        )
    return SourceWakeResult(
        slug="email",
        profile=profile,
        source_id=message_id,
        classification=classification,
        reason=reason,
        packet_path=path,
        intents=intents,
        invoice_candidates=1 if classification == "invoice" and candidates else 0,
        details={"canonical_id": canonical_id},
    )


def land_email_record(computer: Path, record: EmailSourceRecord, *, profile: str = "invoice") -> SourceWakeResult:
    return land_email_message(
        computer,
        record.message_id,
        profile=profile,
        email={
            "message_id": record.message_id,
            "from": record.sender,
            "subject": record.subject,
            "body": record.body,
            "thread_uri": record.thread_uri,
            "attachments": record.attachments,
        },
    )


def land_stripe_payout(
    computer: Path,
    raw: bytes,
    headers: dict[str, str],
    *,
    provider: str = "stripe",
    require_signature: bool = True,
) -> SourceWakeResult:
    """Unpack the Kernel waterfall. Never produce InvoiceCandidate."""
    module = stripe if provider == "stripe" else adyen
    result = module.process_raw(raw, headers, require_signature=require_signature)
    payout_id = result.payout_id or "missing"
    payout = get_payout(payout_id) if result.payout_id else None
    breakdown = get_reconciliation(payout_id) if result.payout_id else None
    charges = []
    if payout is not None:
        for line in payout.lines:
            if (line.category or line.line_type) in {"gross", "refund", "chargeback"} or line.line_type in {
                "charge",
                "payment",
                "refund",
                "dispute",
                "chargeback",
            }:
                charges.append(
                    {
                        "line_type": line.line_type,
                        "category": line.category,
                        "amount": line.amount,
                        "reference": line.reference,
                        "provider_object_id": line.provider_object_id,
                    }
                )
    payload = {
        "bot": "stripe",
        "profile": "payout",
        "provider": provider,
        "payout_id": result.payout_id,
        "status": result.status,
        "invoice_candidates": result.invoice_candidates,
        "deposit": {
            "bank_deposit_id": payout.bank_deposit_id if payout else None,
            "bank_deposit_amount": payout.bank_deposit_amount if payout else None,
            "expected_payout": breakdown.expected_payout if breakdown else None,
            "actual_payout": breakdown.actual_payout if breakdown else None,
            "reconciliation_status": breakdown.status if breakdown else None,
        },
        "charges": charges,
    }
    path = write_packet(computer, "stripe", payout_id, payload)
    intents: list[HandleIntent] = []
    if result.status == "processed" and result.payout_id:
        intents.append(
            _intent(
                from_slug="stripe",
                to_slug=STRIPE_DEPOSIT[0],
                profile=STRIPE_DEPOSIT[1],
                path=path,
                source_id=result.payout_id,
                sentence="Landed a processor deposit. Kernel already unpacked the waterfall. Do not invent totals.",
            )
        )
        intents.append(
            _intent(
                from_slug="stripe",
                to_slug=STRIPE_CHARGES[0],
                profile=STRIPE_CHARGES[1],
                path=path,
                source_id=f"{result.payout_id}:charges",
                sentence="Landed charge-level payout facts. Do not apply cash in this Bot.",
            )
        )
    return SourceWakeResult(
        slug="stripe",
        profile="payout",
        source_id=payout_id,
        classification="payout",
        reason=result.message,
        packet_path=path,
        intents=intents,
        invoice_candidates=result.invoice_candidates,
        kernel_status=result.status,
        details={"duplicate": result.duplicate, "payout_id": result.payout_id},
    )


def land_bank_transaction(computer: Path, transaction_id: str, *, period: str = "2026-09") -> SourceWakeResult:
    """A charge is not a bill. invoice_missing stays on bank."""
    row = get_bank_transaction(transaction_id)
    if row is None:
        return SourceWakeResult(
            slug="bank",
            profile="card",
            source_id=transaction_id,
            classification="unreadable",
            reason=f"Transaction {transaction_id} was not found. Do not invent bank data.",
            packet_path=None,
        )
    run = run_bank_card_source(period, use_llm=False)
    discovery = next((item for item in run.discovery if item.transaction_id == transaction_id), None)
    status = discovery.status if discovery else "invoice_missing"
    reason = (
        discovery.reason
        if discovery
        else "No supporting invoice documentation found for this charge"
    )
    candidate = discovery.candidate if discovery else None
    if status == "invoice_found" and candidate is not None:
        ingest_candidates(
            [candidate],
            period=period,
            forward_to_ap=True,
            reset_overlay=False,
            save_trace=False,
        )
    payload = {
        "bot": "bank",
        "profile": "card",
        "transaction_id": transaction_id,
        "status": status,
        "reason": reason,
        "vendor_descriptor": row.get("vendor_descriptor"),
        "amount": row.get("amount"),
        "candidate": None if candidate is None else {
            "vendor": candidate.vendor,
            "vendor_invoice_number": candidate.vendor_invoice_number,
            "amount": candidate.amount,
            "source_id": candidate.source_id,
        },
    }
    path = write_packet(computer, "bank", transaction_id, payload)
    intents: list[HandleIntent] = []
    if status != "invoice_missing":
        intents.append(
            _intent(
                from_slug="bank",
                to_slug=BANK_LINE[0],
                profile=BANK_LINE[1],
                path=path,
                source_id=transaction_id,
                sentence="Landed a bank line. A charge is not a bill. Do not invent invoices.",
            )
        )
    return SourceWakeResult(
        slug="bank",
        profile="card",
        source_id=transaction_id,
        classification=status,
        reason=reason,
        packet_path=path,
        intents=intents,
        invoice_candidates=1 if candidate is not None else 0,
        kernel_status=status,
    )


def land_books_record(
    computer: Path,
    *,
    profile: str,
    source_id: str,
    record_kind: str,
    candidate: InvoiceCandidate | None,
    classification: str,
    reason: str,
    period: str = "2026-09",
) -> SourceWakeResult:
    """Structured ERP/EDI/Coupa: Python parse wins. Bot does not remap filled fields."""
    canonical_id = None
    if candidate is not None and classification == "invoice":
        report = ingest_candidates(
            [candidate],
            period=period,
            forward_to_ap=True,
            reset_overlay=False,
            save_trace=False,
        )
        if report.canonical_invoices:
            canonical_id = report.canonical_invoices[0].canonical_id
    dest = books_destination(record_kind=record_kind)
    payload = {
        "bot": "books",
        "profile": profile,
        "source_id": source_id,
        "record_kind": record_kind,
        "classification": classification,
        "reason": reason,
        "canonical_id": canonical_id,
        "python_parse_wins": True,
        "destination": {"slug": dest[0], "profile": dest[1]} if dest else None,
    }
    path = write_packet(computer, "books", source_id, payload)
    intents: list[HandleIntent] = []
    if dest is not None and classification in {"invoice", "open-invoice", "period-lock-state"}:
        to_slug, to_profile = dest
        intents.append(
            _intent(
                from_slug="books",
                to_slug=to_slug,
                profile=to_profile,
                path=path,
                source_id=source_id,
                sentence="Landed a books record. Python parse wins. Do not remap filled fields. Do not lock the period.",
            )
        )
    return SourceWakeResult(
        slug="books",
        profile=profile,
        source_id=source_id,
        classification=classification,
        reason=reason,
        packet_path=path,
        intents=intents,
        invoice_candidates=1 if candidate is not None else 0,
        details={"canonical_id": canonical_id, "record_kind": record_kind},
    )


def write_send_payloads(computer: Path, result: SourceWakeResult) -> Path:
    path = Path(computer) / "workspace" / "sources" / result.slug / f"{result.source_id}.send.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([item.to_send_payload() for item in result.intents], indent=2) + "\n")
    return path
