"""Persist inbox traces, notices, and transport outcomes.

AP invoices are not stored here. They go through tools.register_runtime_invoice.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from invoice_ingestion.models import CanonicalInvoice
from invoice_ingestion.registry import mark_handed_off, remember
from models import Invoice
from tools import all_invoices, load_invoice, register_runtime_invoice

from inbox.models import InboxHandoffResult, InboxTrace, MessageEnvelope
from inbox.transport import all_messages, all_outcomes, restore_mailbox

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR_ENV = "CFO_INBOX_RUNS_DIR"
_DEFAULT_DIR = ROOT / "runs" / "inbox"


def _default_runs_dir() -> Path:
    override = os.environ.get(RUNS_DIR_ENV)
    if override:
        return Path(override)
    return _DEFAULT_DIR


RUNS_DIR = _default_runs_dir()

_notices: list[dict] = []
_created_invoices: dict[str, Invoice] = {}
_canonicals: dict[str, CanonicalInvoice] = {}
_traces: dict[str, InboxTrace] = {}


def configure_runs_dir(directory: Path | None = None) -> Path:
    global RUNS_DIR
    RUNS_DIR = Path(directory) if directory is not None else _default_runs_dir()
    return RUNS_DIR


def reset_store() -> None:
    _notices.clear()
    _created_invoices.clear()
    _canonicals.clear()
    _traces.clear()


def record_notice(kind: str, payload: dict) -> dict:
    row = {"kind": kind, **payload}
    _notices.append(row)
    return row


def notices(kind: str | None = None) -> list[dict]:
    if kind is None:
        return list(_notices)
    return [item for item in _notices if item.get("kind") == kind]


def apply_inbox_provenance(
    invoice: Invoice,
    *,
    message_id: str,
    thread_id: str,
    trace_id: str,
    attachment_hashes: list[str] | None = None,
) -> Invoice:
    hashes = [item for item in (attachment_hashes or []) if item]
    if not hashes:
        hashes = list(invoice.source_attachment_hashes)
    return invoice.model_copy(
        update={
            "source_message_id": invoice.source_message_id or message_id,
            "source_thread_id": invoice.source_thread_id or thread_id,
            "source_trace_id": invoice.source_trace_id or trace_id,
            "source_attachment_hashes": list(invoice.source_attachment_hashes) or hashes,
        }
    )


def remember_invoice(invoice: Invoice, canonical: CanonicalInvoice | None = None) -> Invoice:
    persisted = register_runtime_invoice(invoice)
    _created_invoices[persisted.invoice_id] = persisted
    if canonical is not None:
        _canonicals[canonical.canonical_id] = canonical
    return persisted


def created_invoices() -> list[Invoice]:
    found: list[Invoice] = []
    seen: set[str] = set()
    for item in _created_invoices.values():
        if item.invoice_id in seen:
            continue
        seen.add(item.invoice_id)
        found.append(item)
    for item in all_invoices():
        if item.invoice_id in seen:
            continue
        if item.source_message_id or item.source_trace_id:
            seen.add(item.invoice_id)
            found.append(item)
    return found


def created_invoice_ids() -> list[str]:
    return [item.invoice_id for item in created_invoices()]


def remember_trace(trace: InboxTrace) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / "traces" / f"{trace.trace_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    trace.trace_path = str(path)
    path.write_text(trace.model_dump_json(indent=2) + "\n")
    _traces[trace.trace_id] = trace
    return path


def all_traces() -> list[InboxTrace]:
    return list(_traces.values())


def get_trace(trace_id: str) -> InboxTrace | None:
    return _traces.get(trace_id)


def persist_state() -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "messages": [item.model_dump() for item in all_messages()],
        "outcomes": {key: item.model_dump() for key, item in all_outcomes().items()},
        "invoice_ids": created_invoice_ids(),
        "canonicals": [item.model_dump() for item in _canonicals.values()],
        "notices": list(_notices),
        "traces": [item.model_dump() for item in _traces.values()],
    }
    path = RUNS_DIR / "state.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def load_state(path: Path | None = None) -> dict:
    target = path or (RUNS_DIR / "state.json")
    if not target.exists():
        return {}
    raw = json.loads(target.read_text())
    messages = [MessageEnvelope.model_validate(item) for item in raw.get("messages") or []]
    outcomes = {
        key: InboxHandoffResult.model_validate(value)
        for key, value in (raw.get("outcomes") or {}).items()
    }
    restore_mailbox(messages, outcomes)
    for row in raw.get("invoices") or []:
        invoice = Invoice.model_validate(row)
        if load_invoice(invoice.invoice_id) is None:
            register_runtime_invoice(invoice)
        loaded = load_invoice(invoice.invoice_id) or invoice
        _created_invoices[loaded.invoice_id] = loaded
    for invoice_id in raw.get("invoice_ids") or []:
        invoice = load_invoice(str(invoice_id))
        if invoice is not None:
            _created_invoices[invoice.invoice_id] = invoice
    for row in raw.get("canonicals") or []:
        canonical = CanonicalInvoice.model_validate(row)
        _canonicals[canonical.canonical_id] = canonical
        remember(canonical)
        if canonical.forwarded_to_ap or canonical.ap_invoice_id:
            mark_handed_off(canonical.canonical_id)
    _notices.clear()
    _notices.extend(raw.get("notices") or [])
    _traces.clear()
    for row in raw.get("traces") or []:
        trace = InboxTrace.model_validate(row)
        _traces[trace.trace_id] = trace
    return raw


def reset_inbox_state(*, load_disk: bool = False) -> None:
    from inbox.transport import reset_transport

    reset_transport()
    reset_store()
    if load_disk:
        load_state()
