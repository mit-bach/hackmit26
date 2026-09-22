"""Disk-backed canonical invoice registry.

HackMIT constraint: not a production database. The file lives under
runs/ingestion/registry.json so a second Sidecar/Bot process sees the same
identity. Cleared with the AP overlay when reset_overlay=True.
"""

from __future__ import annotations

import os
from pathlib import Path

from atomic_json import read_json_object, with_file_lock, write_json_atomic
from invoice_ingestion.identity import canonical_invoice_key, identity_keys
from invoice_ingestion.models import CanonicalInvoice

REGISTRY_DIR_ENV = "CFO_INGEST_STATE_DIR"
_DEFAULT_STATE_DIR = Path(__file__).resolve().parent.parent / "runs" / "ingestion"


def _default_state_dir() -> Path:
    override = os.environ.get(REGISTRY_DIR_ENV)
    if override:
        return Path(override)
    return _DEFAULT_STATE_DIR


STATE_DIR = _default_state_dir()
REGISTRY_PATH = STATE_DIR / "registry.json"
LOCK_PATH = STATE_DIR / "registry.lock"

_canonicals: dict[str, CanonicalInvoice] = {}
_index: dict[str, str] = {}
_handed_off: set[str] = set()
_loaded = False


def configure_paths(directory: Path | None = None) -> Path:
    """Point the registry at a Computer/runs tree. Tests isolate this."""
    global STATE_DIR, REGISTRY_PATH, LOCK_PATH, _loaded
    STATE_DIR = Path(directory) if directory is not None else _default_state_dir()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH = STATE_DIR / "registry.json"
    LOCK_PATH = STATE_DIR / "registry.lock"
    _clear_memory()
    _loaded = False
    return STATE_DIR


def next_canonical_id() -> str:
    _ensure_loaded()
    used: list[int] = []

    def _take(canonical_id: str) -> None:
        if not canonical_id.startswith("ING-"):
            return
        suffix = canonical_id.split("-", 1)[-1]
        if suffix.isdigit():
            used.append(int(suffix))

    for canonical_id in _canonicals:
        _take(canonical_id)
    from tools import all_invoices

    for invoice in all_invoices():
        _take(invoice.invoice_id)
    return f"ING-{max(used, default=0) + 1:03d}"


def reset_registry() -> None:
    def _reset() -> None:
        _clear_memory()
        _save_unlocked()

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with_file_lock(LOCK_PATH, _reset)
    global _loaded
    _loaded = True


def all_canonicals() -> list[CanonicalInvoice]:
    _ensure_loaded()
    return list(_canonicals.values())


def lookup(obj) -> CanonicalInvoice | None:
    _ensure_loaded()
    for key in identity_keys(obj):
        canonical_id = _index.get(key)
        if canonical_id and canonical_id in _canonicals:
            return _canonicals[canonical_id]
    return None


def remember(record: CanonicalInvoice) -> CanonicalInvoice:
    def _remember() -> CanonicalInvoice:
        _load_unlocked()
        _store_record(record)
        _save_unlocked()
        return record

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    return with_file_lock(LOCK_PATH, _remember)


def merge_provenance(existing: CanonicalInvoice, incoming: CanonicalInvoice) -> bool:
    """Attach new source refs onto an existing canonical invoice. Returns True if added."""
    seen = {(ref.source_type, ref.source_id) for ref in existing.sources}
    added = False
    for ref in incoming.sources:
        pair = (ref.source_type, ref.source_id)
        if pair in seen:
            continue
        existing.sources.append(ref)
        seen.add(pair)
        added = True
    if not existing.document_hash and incoming.document_hash:
        existing.document_hash = incoming.document_hash
    if not existing.po_id and incoming.po_id:
        existing.po_id = incoming.po_id
    if incoming.evidence:
        existing.evidence = list(existing.evidence) + list(incoming.evidence)
    if incoming.vendor_id and not existing.vendor_id:
        existing.vendor_id = incoming.vendor_id
    remember(existing)
    return added


def already_handed_off(canonical_id: str) -> bool:
    _ensure_loaded()
    return canonical_id in _handed_off


def mark_handed_off(canonical_id: str) -> None:
    def _mark() -> None:
        _load_unlocked()
        _handed_off.add(canonical_id)
        _save_unlocked()

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with_file_lock(LOCK_PATH, _mark)


def source_already_known(record: CanonicalInvoice, source_type: str, source_id: str) -> bool:
    return any(ref.source_type == source_type and ref.source_id == source_id for ref in record.sources)


def known_source_pairs(record: CanonicalInvoice) -> set[tuple[str, str]]:
    return {(ref.source_type, ref.source_id) for ref in record.sources}


def _clear_memory() -> None:
    _canonicals.clear()
    _index.clear()
    _handed_off.clear()


def _store_record(record: CanonicalInvoice) -> None:
    if not record.canonical_key:
        record.canonical_key = canonical_invoice_key(record)
    _canonicals[record.canonical_id] = record
    for key in identity_keys(record):
        _index[key] = record.canonical_id
    global _loaded
    _loaded = True


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with_file_lock(LOCK_PATH, _load_unlocked)


def _load_unlocked() -> None:
    global _loaded
    _clear_memory()
    payload = read_json_object(REGISTRY_PATH)
    for row in payload.get("canonicals") or []:
        record = CanonicalInvoice.model_validate(row)
        _store_record(record)
    for canonical_id in payload.get("handed_off") or []:
        _handed_off.add(str(canonical_id))
    _loaded = True


def _save_unlocked() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        REGISTRY_PATH,
        {
            "canonicals": [item.model_dump(mode="json") for item in _canonicals.values()],
            "index": dict(_index),
            "handed_off": sorted(_handed_off),
        },
    )
