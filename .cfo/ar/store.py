"""Persisted AR subledger. Seed files are the baseline; runs/ar is the live book."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ar.models import (
    AREvent,
    ARJournalEntry,
    ARPrecedent,
    ARState,
    CashApplicationRecord,
    CashReviewItem,
    CollectionMessage,
    Customer,
    CustomerInvoice,
    CustomerPayment,
    HumanCorrection,
)
from atomic_json import write_json_atomic
from tools import DataFileError

STATE_DIR = Path(__file__).resolve().parent.parent / "runs" / "ar"
STATE_PATH = STATE_DIR / "state.json"
TRACES_DIR = STATE_DIR / "traces"
HANDLES_DIR = STATE_DIR / "handles"
PACKETS_DIR = STATE_DIR / "packets"
DRAIN_PATH = STATE_DIR / "drain.json"

PAYMENT_ALIASES = {"PAY-AMBIGUOUS": "PAY-005"}

_state: ARState | None = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DataFileError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(raw, list):
        raise DataFileError(f"{path.name} must contain a JSON array")
    return raw


def _data_dir() -> Path:
    from tools import DATA_DIR

    return DATA_DIR


def seed_customers() -> list[Customer]:
    return [Customer.model_validate(item) for item in _read_json(_data_dir() / "ar_customers.json")]


def seed_invoices() -> list[CustomerInvoice]:
    return [CustomerInvoice.model_validate(item) for item in _read_json(_data_dir() / "ar_invoices.json")]


def seed_payments() -> list[CustomerPayment]:
    return [CustomerPayment.model_validate(item) for item in _read_json(_data_dir() / "ar_payments.json")]


def seed_precedents() -> list[ARPrecedent]:
    return [ARPrecedent.model_validate(item) for item in _read_json(_data_dir() / "ar_precedents.json")]


def _seed_state() -> ARState:
    customers = {item.customer_id: item for item in seed_customers()}
    invoices = {item.invoice_id: item for item in seed_invoices()}
    payments = {item.payment_id: item for item in seed_payments()}
    aliases = dict(PAYMENT_ALIASES)
    for payment in payments.values():
        alias = str(payment.metadata.get("alias") or "")
        if alias:
            aliases[alias] = payment.payment_id
    return ARState(
        invoices=invoices,
        payments=payments,
        precedents=seed_precedents(),
        customers=customers,
        aliases=aliases,
    )


def load_state(*, reset: bool = False) -> ARState:
    global _state
    if reset or _state is None:
        if not reset and STATE_PATH.exists():
            raw = json.loads(STATE_PATH.read_text())
            _state = ARState.model_validate(raw)
        else:
            _state = _seed_state()
            save_state()
    return _state


def atomic_write_text(path: Path, text: str) -> None:
    """Write `text` to `path` with a same-directory replace so readers never see a torn file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text)
    os.replace(tmp, path)


def save_state() -> None:
    if _state is None:
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json_atomic(STATE_PATH, json.loads(_state.model_dump_json()))


def reset_state() -> ARState:
    return load_state(reset=True)


def clear_state_cache() -> None:
    global _state
    _state = None


def configure_paths(directory: Path) -> None:
    global STATE_DIR, STATE_PATH, TRACES_DIR, HANDLES_DIR, PACKETS_DIR, DRAIN_PATH, _state
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    STATE_PATH = directory / "state.json"
    TRACES_DIR = directory / "traces"
    HANDLES_DIR = directory / "handles"
    PACKETS_DIR = directory / "packets"
    DRAIN_PATH = directory / "drain.json"
    _state = None


@contextmanager
def isolated_ar_state(directory: Path):
    global STATE_DIR, STATE_PATH, TRACES_DIR, HANDLES_DIR, PACKETS_DIR, DRAIN_PATH, _state
    previous = (STATE_DIR, STATE_PATH, TRACES_DIR, HANDLES_DIR, PACKETS_DIR, DRAIN_PATH, _state)
    configure_paths(directory)
    try:
        yield
    finally:
        STATE_DIR, STATE_PATH, TRACES_DIR, HANDLES_DIR, PACKETS_DIR, DRAIN_PATH, _state = previous


def all_customers() -> list[Customer]:
    return list(load_state().customers.values())


def get_customer(customer_id: str) -> Customer | None:
    return load_state().customers.get(customer_id)


def all_invoices() -> list[CustomerInvoice]:
    return list(load_state().invoices.values())


def open_invoices(customer_id: str = "") -> list[CustomerInvoice]:
    rows = [item for item in all_invoices() if item.outstanding_amount > 0]
    if customer_id:
        rows = [item for item in rows if item.customer_id == customer_id]
    return rows


def get_invoice(invoice_id: str) -> CustomerInvoice | None:
    return load_state().invoices.get(invoice_id)


def save_invoice(invoice: CustomerInvoice) -> CustomerInvoice:
    state = load_state()
    state.invoices[invoice.invoice_id] = invoice
    save_state()
    return invoice


def all_payments() -> list[CustomerPayment]:
    return list(load_state().payments.values())


def resolve_payment_id(payment_id: str) -> str:
    key = payment_id.strip().upper()
    aliases = load_state().aliases
    return aliases.get(key, key)


def get_payment(payment_id: str) -> CustomerPayment | None:
    state = load_state()
    resolved = resolve_payment_id(payment_id)
    return state.payments.get(resolved)


def save_payment(payment: CustomerPayment) -> CustomerPayment:
    state = load_state()
    state.payments[payment.payment_id] = payment
    save_state()
    return payment


def applications() -> list[CashApplicationRecord]:
    return list(load_state().applications)


def applications_for_payment(payment_id: str) -> list[CashApplicationRecord]:
    payment_id = resolve_payment_id(payment_id)
    return [item for item in applications() if item.payment_id == payment_id and item.posted]


def add_application(record: CashApplicationRecord) -> CashApplicationRecord:
    state = load_state()
    state.applications.append(record)
    save_state()
    return record


def outbox() -> list[CollectionMessage]:
    return list(load_state().outbox)


def add_outbox(message: CollectionMessage) -> CollectionMessage:
    state = load_state()
    state.outbox.append(message)
    save_state()
    return message


def events() -> list[AREvent]:
    return list(load_state().events)


def add_event(
    event_type: str,
    summary: str,
    *,
    payment_id: str | None = None,
    invoice_ids: list[str] | None = None,
    details: dict | None = None,
) -> AREvent:
    state = load_state()
    event = AREvent(
        event_id=f"AR-EVT-{len(state.events) + 1:04d}",
        event_type=event_type,
        created_at=_now(),
        payment_id=payment_id,
        invoice_ids=invoice_ids or [],
        summary=summary,
        details=details or {},
    )
    state.events.append(event)
    save_state()
    return event


def precedents(customer_id: str = "") -> list[ARPrecedent]:
    rows = list(load_state().precedents)
    if customer_id:
        rows = [item for item in rows if item.customer_id in {None, customer_id}]
    return rows


def add_precedent(precedent: ARPrecedent) -> ARPrecedent:
    state = load_state()
    state.precedents.append(precedent)
    save_state()
    return precedent


def journals() -> list[ARJournalEntry]:
    return list(load_state().journals)


def add_journal(entry: ARJournalEntry) -> ARJournalEntry:
    state = load_state()
    state.journals.append(entry)
    save_state()
    return entry


def human_corrections() -> list[HumanCorrection]:
    return list(load_state().human_corrections)


def add_human_correction(correction: HumanCorrection) -> HumanCorrection:
    state = load_state()
    state.human_corrections.append(correction)
    save_state()
    return correction


def save_human_correction(correction: HumanCorrection) -> HumanCorrection:
    state = load_state()
    state.human_corrections = [
        correction if item.correction_id == correction.correction_id else item
        for item in state.human_corrections
    ]
    save_state()
    return correction


def reviews() -> list[CashReviewItem]:
    return list(load_state().reviews)


def open_reviews() -> list[CashReviewItem]:
    return [item for item in reviews() if item.status == "OPEN"]


def open_human_reviews() -> list[CashReviewItem]:
    """Human Operator queue. Operational apply never parks here."""
    return [item for item in open_reviews() if item.human_queue]


def get_review(payment_id: str) -> CashReviewItem | None:
    payment_id = resolve_payment_id(payment_id)
    matches = [item for item in reviews() if item.payment_id == payment_id]
    if not matches:
        return None
    open_item = next((item for item in reversed(matches) if item.status == "OPEN"), None)
    return open_item or matches[-1]


def add_review(item: CashReviewItem) -> CashReviewItem:
    state = load_state()
    state.reviews.append(item)
    save_state()
    return item


def save_review(item: CashReviewItem) -> CashReviewItem:
    state = load_state()
    state.reviews = [item if row.review_id == item.review_id else row for row in state.reviews]
    save_state()
    return item


def next_id(prefix: str, existing: list[str]) -> str:
    numbers = []
    for item in existing:
        if not item.startswith(prefix):
            continue
        suffix = item[len(prefix) :].lstrip("-")
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def save_trace(name: str, payload) -> Path:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = TRACES_DIR / f"{name}-{stamp}.json"
    if hasattr(payload, "model_dump_json"):
        atomic_write_text(path, payload.model_dump_json(indent=2) + "\n")
    else:
        atomic_write_text(path, json.dumps(payload, indent=2) + "\n")
    return path
