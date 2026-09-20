from __future__ import annotations

import re
from datetime import datetime

from invoice_ingestion.interpret import parse_money, unknown_vendor_warning
from invoice_ingestion.models import (
    InvoiceCandidate,
    SUPPORTED_SOURCES,
    ValidationResult,
)
from tools import all_invoices, normalize_vendor

AMOUNT_TOLERANCE = 0.01
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def valid_date(value: str | None) -> bool:
    if not value:
        return False
    if not ISO_DATE.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def amounts_consistent(subtotal: float | None, tax: float | None, total: float | None) -> bool:
    if subtotal is None or total is None:
        return True
    expected = round(subtotal + (0.0 if tax is None else tax), 2)
    return abs(expected - total) <= AMOUNT_TOLERANCE


def validate_candidate(candidate: InvoiceCandidate, seen_source_ids: set[tuple[str, str]] | None = None) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if candidate.source_type not in SUPPORTED_SOURCES:
        errors.append(f"unsupported_source_type:{candidate.source_type}")
    if not candidate.source_id:
        errors.append("missing_source_id")
    if seen_source_ids is not None and (candidate.source_type, candidate.source_id) in seen_source_ids:
        errors.append("duplicate_source_id")

    if not (candidate.vendor or "").strip():
        errors.append("missing_vendor")
    if not (candidate.vendor_invoice_number or "").strip():
        errors.append("missing_invoice_number")

    amount = parse_money(candidate.amount)
    if amount is None:
        errors.append("missing_amount")
    elif amount < 0:
        errors.append("negative_amount")

    currency = (candidate.currency or "").strip().upper()
    if not currency:
        errors.append("missing_currency")
    elif not CURRENCY_RE.match(currency):
        errors.append(f"invalid_currency:{candidate.currency}")

    if candidate.invoice_date and not valid_date(candidate.invoice_date):
        errors.append(f"malformed_invoice_date:{candidate.invoice_date}")
    elif not candidate.invoice_date:
        errors.append("missing_invoice_date")
    if candidate.due_date and not valid_date(candidate.due_date):
        errors.append(f"malformed_due_date:{candidate.due_date}")

    subtotal = parse_money(candidate.subtotal)
    tax = parse_money(candidate.tax)
    if not amounts_consistent(subtotal, tax, amount):
        errors.append("inconsistent_totals")

    unknown = unknown_vendor_warning(candidate.vendor)
    if unknown:
        warnings.append(unknown)
    if not candidate.po_id:
        warnings.append("missing_po")

    status = "valid" if not errors else "rejected"
    if status == "valid" and candidate.extraction_confidence is not None and candidate.extraction_confidence < 0.5:
        status = "ambiguous"
        warnings.append("low_extraction_confidence")

    return ValidationResult(
        source_type=candidate.source_type,
        source_id=candidate.source_id,
        status=status,
        errors=errors,
        warnings=warnings,
    )


def existing_ap_match(vendor: str, invoice_number: str) -> str | None:
    wanted_vendor = normalize_vendor(vendor)
    wanted_number = invoice_number.strip().upper()
    for invoice in all_invoices():
        if (
            normalize_vendor(invoice.vendor) == wanted_vendor
            and invoice.vendor_invoice_number.strip().upper() == wanted_number
        ):
            return invoice.invoice_id
    return None
