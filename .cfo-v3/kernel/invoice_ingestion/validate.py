from __future__ import annotations

import re
from datetime import datetime

from invoice_ingestion.interpret import parse_money, unknown_vendor_warning
from invoice_ingestion.models import (
    InvoiceCandidate,
    SUPPORTED_SOURCES,
    ValidationResult,
)
from tools import all_invoices, normalize_invoice_number, normalize_vendor

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
    errors.extend(_line_item_errors(candidate))

    analysis = (candidate.source_context or {}).get("document_analysis") or {}
    flags = analysis.get("flags") or []
    if "voided" in flags:
        errors.append("voided_document")
    if "incorrect_banking" in flags:
        errors.append("incorrect_banking")
    if "tax_arithmetic_error" in flags and "inconsistent_totals" not in errors:
        errors.append("inconsistent_totals")
    if analysis.get("supersedes"):
        warnings.append(f"supersedes:{analysis['supersedes']}")
    if candidate.classification != "invoice":
        errors.append(f"not_a_payable:{candidate.classification}")

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


def _line_item_errors(candidate: InvoiceCandidate) -> list[str]:
    errors: list[str] = []
    items = candidate.line_items or []
    if not items:
        return errors
    amounts: list[float] = []
    extension_mismatch = False
    for item in items:
        qty = parse_money(item.quantity)
        unit = parse_money(item.unit_price)
        amt = parse_money(item.amount)
        if qty is not None and unit is not None and amt is not None:
            expected = round(qty * unit, 2)
            if abs(expected - amt) > AMOUNT_TOLERANCE:
                extension_mismatch = True
        if amt is not None:
            amounts.append(amt)
    if extension_mismatch:
        errors.append("line_item_extension_mismatch")
    if len(amounts) == len(items):
        line_sum = round(sum(amounts), 2)
        subtotal = parse_money(candidate.subtotal)
        if subtotal is not None and abs(line_sum - subtotal) > AMOUNT_TOLERANCE:
            errors.append("line_item_sum_mismatch")
    return errors


def existing_ap_match(vendor: str, invoice_number: str) -> str | None:
    wanted_vendor = normalize_vendor(vendor)
    wanted_number = normalize_invoice_number(invoice_number)
    if not wanted_vendor or not wanted_number:
        return None
    for invoice in all_invoices():
        if (
            normalize_vendor(invoice.vendor) == wanted_vendor
            and normalize_invoice_number(invoice.vendor_invoice_number) == wanted_number
        ):
            return invoice.invoice_id
    return None
