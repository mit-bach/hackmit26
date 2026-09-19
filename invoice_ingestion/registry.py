"""In-memory canonical invoice registry for one process/session.

HackMIT constraint: no production database. Cleared with the AP overlay.
Repeated ingest_invoices() calls in the same session reuse these records
instead of minting a second payable.
"""

from __future__ import annotations

from invoice_ingestion.identity import canonical_invoice_key, identity_keys
from invoice_ingestion.models import CanonicalInvoice

_canonicals: dict[str, CanonicalInvoice] = {}
_index: dict[str, str] = {}
_handed_off: set[str] = set()


def next_canonical_id() -> str:
    used: list[int] = []
    for canonical_id in _canonicals:
        if not canonical_id.startswith("ING-"):
            continue
        suffix = canonical_id.split("-", 1)[-1]
        if suffix.isdigit():
            used.append(int(suffix))
    return f"ING-{max(used, default=0) + 1:03d}"


def reset_registry() -> None:
    _canonicals.clear()
    _index.clear()
    _handed_off.clear()


def all_canonicals() -> list[CanonicalInvoice]:
    return list(_canonicals.values())


def lookup(obj) -> CanonicalInvoice | None:
    for key in identity_keys(obj):
        canonical_id = _index.get(key)
        if canonical_id and canonical_id in _canonicals:
            return _canonicals[canonical_id]
    return None


def _index_record(record: CanonicalInvoice) -> None:
    for key in identity_keys(record):
        _index[key] = record.canonical_id


def remember(record: CanonicalInvoice) -> CanonicalInvoice:
    """Store or replace the canonical record and refresh identity indexes."""
    if not record.canonical_key:
        record.canonical_key = canonical_invoice_key(record)
    _canonicals[record.canonical_id] = record
    _index_record(record)
    return record


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
    return canonical_id in _handed_off


def mark_handed_off(canonical_id: str) -> None:
    _handed_off.add(canonical_id)


def source_already_known(record: CanonicalInvoice, source_type: str, source_id: str) -> bool:
    return any(ref.source_type == source_type and ref.source_id == source_id for ref in record.sources)


def known_source_pairs(record: CanonicalInvoice) -> set[tuple[str, str]]:
    return {(ref.source_type, ref.source_id) for ref in record.sources}
