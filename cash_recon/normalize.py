"""Deterministic bank-description normalization. Agents do not invent references."""

from __future__ import annotations

import re

from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, LedgerEntry

STOPWORDS = {
    "ach",
    "out",
    "in",
    "wire",
    "transfer",
    "intl",
    "ref",
    "payment",
    "customer",
    "debit",
    "credit",
    "misc",
    "card",
    "inc",
    "llc",
    "co",
    "the",
    "and",
    "payout",
    "settlement",
}

INVOICE_RE = re.compile(r"\b(?:inv|invoice)[- ]?(\d{3,})\b", re.I)
REF_RE = re.compile(r"\b(?:ref|reference)[- ]?([a-z0-9-]{3,})\b", re.I)
TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
STRIPE_RE = re.compile(r"\bstripe\b|\bstrp[- ]?\w+", re.I)
ADYEN_RE = re.compile(r"\badyen\b|\bady[- ]?\w+", re.I)
REFUND_RE = re.compile(r"\brefund\b|\breversal\b", re.I)
WIRE_RE = re.compile(r"\bwire\b", re.I)


def tokens(text: str) -> set[str]:
    found = {item.lower() for item in TOKEN_RE.findall(text or "")}
    return {item for item in found if item not in STOPWORDS and len(item) > 1}


def overlap_score(left: str, right: str) -> float:
    a = tokens(left)
    b = tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def combined_text(item: BankTransaction | LedgerEntry) -> str:
    parts = [item.description, item.reference, item.counterparty]
    return " ".join(part for part in parts if part)


def extract_invoice_ids(text: str) -> list[str]:
    return [f"INV-{match}" if not match.upper().startswith("INV") else match.upper() for match in INVOICE_RE.findall(text or "")]


def detect_provider(text: str, explicit: str | None = None) -> str | None:
    if explicit:
        name = explicit.lower()
        if name in {"stripe", "adyen"}:
            return name
    blob = text or ""
    if STRIPE_RE.search(blob):
        return "stripe"
    if ADYEN_RE.search(blob):
        return "adyen"
    return None


def looks_like_refund(item: BankTransaction | LedgerEntry) -> bool:
    if getattr(item, "entry_type", "") == "refund":
        return True
    if getattr(item, "transaction_type", "") in {"card_refund", "refund"}:
        return True
    return bool(REFUND_RE.search(combined_text(item)))


def looks_like_wire(item: BankTransaction | LedgerEntry) -> bool:
    if getattr(item, "transaction_type", "") in {"wire_debit", "wire_credit"}:
        return True
    return bool(WIRE_RE.search(combined_text(item)))


def counterparties_compatible(left: str, right: str) -> bool:
    if not left or not right:
        return True
    score = overlap_score(left, right)
    if score >= 0.34:
        return True
    a = tokens(left)
    b = tokens(right)
    return bool(a and b and (a <= b or b <= a))


def prepare_bank(rows: list[BankTransaction]) -> list[BankTransaction]:
    prepared: list[BankTransaction] = []
    for row in rows:
        item = row.model_copy(deep=True)
        if not item.period:
            item.period = period_of(item.date)
        if not item.amount_minor:
            item.amount_minor = cents(item.amount)
        if not item.provider:
            item.provider = detect_provider(combined_text(item), item.provider)
        prepared.append(item)
    return prepared


def prepare_ledger(rows: list[LedgerEntry]) -> list[LedgerEntry]:
    prepared: list[LedgerEntry] = []
    for row in rows:
        item = row.model_copy(deep=True)
        if not item.period:
            item.period = period_of(item.date)
        if not item.amount_minor:
            item.amount_minor = cents(item.amount)
        prepared.append(item)
    return prepared
