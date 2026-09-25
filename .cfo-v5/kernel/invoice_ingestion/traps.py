"""Deterministic document-trap analysis for messy AP intake.

Python owns classification flags. Agents may narrate them; they do not invent
totals, invoice numbers, or a payable from a void, quote, statement, or payout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from invoice_ingestion.validate import amounts_consistent
from tools import normalize_invoice_number, normalize_vendor

VOID_MARKERS = (
    "voided invoice",
    "this invoice is void",
    "void — do not pay",
    "void - do not pay",
    "void: do not pay",
    "do not pay this invoice",
    "cancelled invoice",
    "canceled invoice",
)
REVISION_MARKERS = (
    "this invoice replaces",
    "revised invoice",
    "revision of invoice",
    "supersedes invoice",
    "replaces invoice",
    "correcting invoice",
)
CREDIT_MARKERS = ("credit memo", "credit note", "credit memorandum")
STRIPE_PAYOUT_MARKERS = (
    "stripe payout",
    "stripe settlement",
    "stripe transfer to bank",
    "automatic payout",
)
CARD_AS_INVOICE_MARKERS = (
    "card charge presented as invoice",
    "this is a bank transaction",
    "corporate card charge, not a vendor invoice",
)
BANKING_LABELS = (
    r"(?:routing|aba)\s*(?:number|#)?\s*[:#]?\s*(\d{8,12})",
    r"(?:account)\s*(?:number|#)?\s*[:#]?\s*(\d{6,17})",
)
SUPERSEDES_RE = re.compile(
    r"(?:replaces|supersedes|revision of|correcting)\s+invoice\s*[:#]?\s*([A-Z0-9][A-Z0-9\-_/]+)",
    re.I,
)


@dataclass(frozen=True)
class DocumentAnalysis:
    classification: str
    reason: str
    payable: bool
    flags: tuple[str, ...] = ()
    supersedes: str | None = None
    tax_consistent: bool | None = None
    banking: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "classification": self.classification,
            "reason": self.reason,
            "payable": self.payable,
            "flags": list(self.flags),
            "supersedes": self.supersedes,
            "tax_consistent": self.tax_consistent,
            "banking": dict(self.banking),
        }


def _blob(*parts: str) -> str:
    return "\n".join(part or "" for part in parts).lower()


def extract_supersedes(text: str) -> str | None:
    match = SUPERSEDES_RE.search(text or "")
    if not match:
        return None
    return match.group(1).rstrip(".,")


def extract_banking(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    blob = text or ""
    routing = re.search(BANKING_LABELS[0], blob, re.I)
    account = re.search(BANKING_LABELS[1], blob, re.I)
    if routing:
        found["routing"] = routing.group(1)
    if account:
        found["account"] = account.group(1)
    return found


def tax_arithmetic_ok(text: str) -> bool | None:
    from invoice_ingestion.interpret import labeled_money

    subtotal = labeled_money(text, "subtotal", "sub-total", "net")
    tax = labeled_money(text, "tax", "vat", "sales tax")
    total = labeled_money(text, "amount due", "total due", "total", "balance due")
    if subtotal is None or total is None:
        return None
    return amounts_consistent(subtotal, tax, total)


def banking_mismatch(document_banking: dict[str, str], expected: dict[str, str] | None) -> bool:
    if not expected or not document_banking:
        return False
    for key in ("routing", "account"):
        left = (document_banking.get(key) or "").replace(" ", "")
        right = (expected.get(key) or "").replace(" ", "")
        if left and right and left != right:
            return True
    return False


def same_number_different_vendors(left_vendor: str, right_vendor: str, number: str) -> bool:
    if not number:
        return False
    return normalize_vendor(left_vendor) != normalize_vendor(right_vendor) and bool(
        normalize_invoice_number(number)
    )


def analyze_document(
    text: str,
    *,
    subject: str = "",
    filename: str = "",
    expected_banking: dict[str, str] | None = None,
) -> DocumentAnalysis:
    """Flags planted document traps without loading any answer key."""
    from invoice_ingestion.interpret import classify_text, looks_like_invoice_text

    classification, reason = classify_text(text, subject=subject, filename=filename)
    blob = _blob(subject, filename, text)
    flags: list[str] = []
    payable = classification == "invoice"
    supersedes = extract_supersedes(text)
    if supersedes:
        flags.append("revised_invoice")
    if any(marker in blob for marker in VOID_MARKERS):
        flags.append("voided")
        classification = "not_invoice"
        reason = "Voided invoice, not a payable"
        payable = False
    if any(marker in blob for marker in CREDIT_MARKERS):
        flags.append("credit_memo")
        payable = False
    if any(marker in blob for marker in STRIPE_PAYOUT_MARKERS) and not looks_like_invoice_text(text):
        flags.append("stripe_payout_as_invoice")
        classification = "not_invoice"
        reason = "Stripe payout is a cash settlement, not a vendor invoice or revenue"
        payable = False
    if any(marker in blob for marker in CARD_AS_INVOICE_MARKERS) and not looks_like_invoice_text(text):
        flags.append("card_charge_as_invoice")
        payable = False
    tax_ok = tax_arithmetic_ok(text)
    if tax_ok is False:
        flags.append("tax_arithmetic_error")
        payable = False
    banking = extract_banking(text)
    if banking_mismatch(banking, expected_banking):
        flags.append("incorrect_banking")
        payable = False
    if classification in {"quote", "statement", "purchase_order", "receipt", "marketing", "payment_confirmation"}:
        payable = False
    return DocumentAnalysis(
        classification=classification,
        reason=reason,
        payable=payable,
        flags=tuple(dict.fromkeys(flags)),
        supersedes=supersedes,
        tax_consistent=tax_ok,
        banking=banking,
    )


def should_create_payable(analysis: DocumentAnalysis) -> bool:
    return bool(analysis.payable and analysis.classification == "invoice")
