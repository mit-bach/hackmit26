"""Deterministic canonical identity. Python-only — never an LLM concern.

Primary key is normalized vendor + invoice number. That is enough to collapse
the same bill arriving from email, a vendor portal, and a card charge.

Document hashes and source IDs are secondary indexes for replay detection when
vendor/number are missing, and for attaching new provenance to an existing bill.

Amount and date are intentionally NOT part of the primary key: two different
invoices can share a round number and a date, and the same invoice can extract
with slight numeric noise across sources.
"""

from __future__ import annotations

from tools import normalize_invoice_number, normalize_vendor


def canonical_invoice_key(
    candidate=None,
    *,
    vendor: str | None = None,
    vendor_invoice_number: str | None = None,
) -> str | None:
    """Stable identity for one vendor invoice, independent of source."""
    if candidate is not None:
        vendor = vendor or getattr(candidate, "vendor", None)
        vendor_invoice_number = vendor_invoice_number or getattr(
            candidate, "vendor_invoice_number", None
        )
    vendor_key = normalize_vendor(vendor or "")
    number_key = normalize_invoice_number(vendor_invoice_number)
    if not vendor_key or not number_key:
        return None
    return f"{vendor_key}:{number_key}"


def source_key(source_type: str | None, source_id: str | None) -> str | None:
    if not source_type or not source_id:
        return None
    return f"source:{source_type}:{source_id}"


def hash_key(document_hash: str | None) -> str | None:
    if not document_hash:
        return None
    return f"hash:{document_hash}"


def identity_keys(obj) -> list[str]:
    """All deterministic lookup keys for a candidate, canonical invoice, or source ref."""
    keys: list[str] = []
    primary = canonical_invoice_key(obj)
    if primary:
        keys.append(f"invoice:{primary}")

    digest = getattr(obj, "document_hash", None)
    hashed = hash_key(digest)
    if hashed:
        keys.append(hashed)

    source = source_key(getattr(obj, "source_type", None), getattr(obj, "source_id", None))
    if source:
        keys.append(source)

    for ref in getattr(obj, "sources", None) or []:
        ref_source = source_key(getattr(ref, "source_type", None), getattr(ref, "source_id", None))
        if ref_source:
            keys.append(ref_source)
        ref_hash = hash_key(getattr(ref, "document_hash", None))
        if ref_hash:
            keys.append(ref_hash)

    # Unique, preserve order.
    return list(dict.fromkeys(keys))
