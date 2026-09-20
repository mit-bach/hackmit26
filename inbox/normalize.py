"""Deterministic field normalization. No model arithmetic."""

from __future__ import annotations

import re

from invoice_ingestion.interpret import normalize_date, parse_money
from invoice_ingestion.store import is_known_vendor, known_vendor_names
from tools import normalize_vendor

CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
PO_RE = re.compile(r"PO-?(\d+)", re.I)


def dollars_to_cents(amount: float | int | None) -> int | None:
    parsed = parse_money(amount)
    if parsed is None:
        return None
    return int(round(parsed * 100))


def cents_to_dollars(cents: int | None) -> float | None:
    if cents is None:
        return None
    return round(cents / 100.0, 2)


def normalize_currency(value: str | None, *, text: str = "") -> str | None:
    raw = (value or "").strip().upper()
    if raw and CURRENCY_RE.match(raw):
        return raw
    blob = f"{value or ''} {text}".upper()
    if "USD" in blob or "$" in (value or "") or "$" in text:
        return "USD"
    return raw or None


def normalize_po(value: str | None) -> str | None:
    if not value:
        return None
    match = PO_RE.search(value)
    if match:
        return f"PO-{match.group(1)}"
    cleaned = value.strip().upper()
    return cleaned or None


def normalize_invoice_number(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().upper().rstrip(".,")
    return cleaned or None


def resolve_vendor(name: str | None) -> tuple[str | None, bool]:
    """Return (canonical vendor name if known else original, is_known)."""
    if not name or not name.strip():
        return None, False
    wanted = normalize_vendor(name)
    for known in known_vendor_names():
        if normalize_vendor(known) == wanted:
            return known, True
    return name.strip(), is_known_vendor(name)


def normalize_iso_date(value: str | None) -> str | None:
    return normalize_date(value)
