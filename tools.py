from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from agents import function_tool

from models import GoodsReceipt, Invoice, PurchaseOrder

DATA_DIR = Path(__file__).resolve().parent / "data"

# Used only to describe the size of an amount gap. The agent still decides.
SMALL_AMOUNT_ABS = 300.0
SMALL_AMOUNT_PCT = 0.05


class DataFileError(Exception):
    """Raised when a data file is missing or not valid JSON."""


def _read_json(path: Path) -> list:
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise DataFileError(f"Data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataFileError(
            f"Invalid JSON in {path.name}: {exc.msg} (line {exc.lineno})"
        ) from exc
    if not isinstance(raw, list):
        raise DataFileError(f"{path.name} must contain a JSON array")
    return raw


@lru_cache(maxsize=1)
def _invoices() -> list[Invoice]:
    return [Invoice.model_validate(item) for item in _read_json(DATA_DIR / "invoices.json")]


@lru_cache(maxsize=1)
def _purchase_orders() -> list[PurchaseOrder]:
    return [
        PurchaseOrder.model_validate(item)
        for item in _read_json(DATA_DIR / "purchase_orders.json")
    ]


@lru_cache(maxsize=1)
def _goods_receipts() -> list[GoodsReceipt]:
    return [
        GoodsReceipt.model_validate(item)
        for item in _read_json(DATA_DIR / "goods_receipts.json")
    ]


def load_invoice(invoice_id: str) -> Invoice | None:
    for invoice in _invoices():
        if invoice.invoice_id == invoice_id:
            return invoice
    return None


def load_purchase_order(po_id: str | None) -> PurchaseOrder | None:
    if not po_id:
        return None
    for purchase_order in _purchase_orders():
        if purchase_order.po_id == po_id:
            return purchase_order
    return None


def load_goods_receipt(po_id: str | None) -> GoodsReceipt | None:
    if not po_id:
        return None
    for receipt in _goods_receipts():
        if receipt.po_id == po_id:
            return receipt
    return None


def load_duplicate_invoices(invoice_id: str) -> list[Invoice]:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return []
    return [
        other
        for other in _invoices()
        if other.vendor_invoice_number == invoice.vendor_invoice_number
        and other.invoice_id != invoice.invoice_id
    ]


def po_exists(po_id: str | None) -> bool:
    return load_purchase_order(po_id) is not None


def po_is_approved(po_id: str | None) -> bool:
    purchase_order = load_purchase_order(po_id)
    return bool(purchase_order and purchase_order.status.lower() == "approved")


def invoice_po_amount_difference(invoice_id: str) -> float | None:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return None
    purchase_order = load_purchase_order(invoice.po_id)
    if purchase_order is None:
        return None
    return round(invoice.amount - purchase_order.authorized_amount, 2)


def invoice_amount_matches_po(invoice_id: str) -> bool:
    difference = invoice_po_amount_difference(invoice_id)
    return difference is not None and difference == 0


def vendors_match(invoice_id: str) -> bool:
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    if invoice is None or purchase_order is None:
        return False
    return invoice.vendor == purchase_order.vendor


def _singularize(token: str) -> str:
    if token.endswith("ies") and len(token) > 3:
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 3:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def _normalize_vendor(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[.,]", " ", cleaned)
    cleaned = re.sub(
        r"\b(co|company|inc|incorporated|llc|ltd|corp|corporation)\b",
        " ",
        cleaned,
    )
    tokens = [_singularize(token) for token in cleaned.split()]
    return "".join(ch for ch in "".join(tokens) if ch.isalnum())


def vendors_are_similar(invoice_id: str) -> bool:
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    if invoice is None or purchase_order is None:
        return False
    left = _normalize_vendor(invoice.vendor)
    right = _normalize_vendor(purchase_order.vendor)
    return left == right or left in right or right in left


def goods_fully_received(po_id: str | None) -> bool:
    receipt = load_goods_receipt(po_id)
    if receipt is None or not receipt.received:
        return False
    if receipt.quantity_received < receipt.quantity_ordered:
        return False
    purchase_order = load_purchase_order(po_id)
    if purchase_order is not None and receipt.amount_received < purchase_order.authorized_amount:
        return False
    return True


def has_duplicate_vendor_invoice_number(invoice_id: str) -> bool:
    return len(load_duplicate_invoices(invoice_id)) > 0


def receipt_status_for(po_id: str | None) -> str:
    if not po_id:
        return "not_applicable"
    receipt = load_goods_receipt(po_id)
    if receipt is None:
        return "missing"
    if not receipt.received or (
        receipt.quantity_received == 0 and receipt.amount_received == 0
    ):
        return "not_received"
    if goods_fully_received(po_id):
        return "full"
    return "partial"


def classify_amount_discrepancy(invoice_id: str) -> str:
    difference = invoice_po_amount_difference(invoice_id)
    if difference is None:
        return "no_po"
    if difference == 0:
        return "exact_match"
    invoice = load_invoice(invoice_id)
    purchase_order = load_purchase_order(invoice.po_id) if invoice else None
    abs_diff = abs(difference)
    percent = (
        abs_diff / purchase_order.authorized_amount
        if purchase_order and purchase_order.authorized_amount
        else None
    )
    if percent is not None and abs_diff <= SMALL_AMOUNT_ABS and percent <= SMALL_AMOUNT_PCT:
        return "small_discrepancy"
    return "material_mismatch"


def python_checks(invoice_id: str) -> dict:
    """Deterministic match facts. The agent uses these numbers; it does not recalculate them."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {"found": False, "error": f"Invoice {invoice_id} not found"}

    purchase_order = load_purchase_order(invoice.po_id)
    receipt = load_goods_receipt(invoice.po_id)
    duplicates = load_duplicate_invoices(invoice_id)
    difference = invoice_po_amount_difference(invoice_id)
    percent_difference = None
    if difference is not None and purchase_order and purchase_order.authorized_amount:
        percent_difference = round(difference / purchase_order.authorized_amount, 4)

    return {
        "found": True,
        "po_id_on_invoice": invoice.po_id,
        "po_exists": po_exists(invoice.po_id),
        "po_is_approved": po_is_approved(invoice.po_id),
        "po_status": purchase_order.status if purchase_order else None,
        "invoice_amount": invoice.amount,
        "po_authorized_amount": purchase_order.authorized_amount if purchase_order else None,
        "amount_difference": difference,
        "percent_difference": percent_difference,
        "amount_matches": invoice_amount_matches_po(invoice_id),
        "amount_discrepancy_class": classify_amount_discrepancy(invoice_id),
        "invoice_vendor": invoice.vendor,
        "po_vendor": purchase_order.vendor if purchase_order else None,
        "vendors_match_exactly": vendors_match(invoice_id),
        "vendors_are_similar": vendors_are_similar(invoice_id),
        "goods_fully_received": goods_fully_received(invoice.po_id),
        "receipt_status": receipt_status_for(invoice.po_id),
        "receipt_found": receipt is not None,
        "quantity_ordered": receipt.quantity_ordered if receipt else None,
        "quantity_received": receipt.quantity_received if receipt else None,
        "amount_received": receipt.amount_received if receipt else None,
        "duplicate_detected": has_duplicate_vendor_invoice_number(invoice_id),
        "duplicate_invoice_ids": [item.invoice_id for item in duplicates],
        "vendor_invoice_number": invoice.vendor_invoice_number,
        "invoice_dated_before_po": bool(
            purchase_order and invoice.invoice_date < purchase_order.created_date
        ),
        "authorized_amount_exceeds_approval_limit": bool(
            purchase_order
            and purchase_order.approval_limit is not None
            and purchase_order.authorized_amount > purchase_order.approval_limit
        ),
    }


def _missing_po_id(po_id: str) -> bool:
    return not po_id or po_id.strip().lower() in {"none", "null"}


@function_tool
def get_invoice(invoice_id: str) -> dict:
    """Look up one invoice by invoice_id. Returns found=false if it does not exist."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {
            "found": False,
            "error": f"Invoice {invoice_id} was not found. Do not invent invoice data.",
        }
    return {
        "found": True,
        "invoice": invoice.model_dump(),
        "python_checks": python_checks(invoice_id),
    }


@function_tool
def get_purchase_order(po_id: str) -> dict:
    """Look up a purchase order by po_id. Returns found=false if it is missing."""
    if _missing_po_id(po_id):
        return {
            "found": False,
            "error": "No purchase order id was provided. Do not invent a PO.",
        }
    purchase_order = load_purchase_order(po_id)
    if purchase_order is None:
        return {
            "found": False,
            "error": f"Purchase order {po_id} was not found. Do not invent PO data.",
        }
    return {
        "found": True,
        "purchase_order": purchase_order.model_dump(),
        "po_exists": True,
        "po_is_approved": purchase_order.status.lower() == "approved",
    }


@function_tool
def get_goods_receipt(po_id: str) -> dict:
    """Look up the goods receipt for a PO. Returns found=false if none exists."""
    if _missing_po_id(po_id):
        return {
            "found": False,
            "error": "No purchase order id was provided, so there is no goods receipt to load.",
        }
    receipt = load_goods_receipt(po_id)
    if receipt is None:
        return {
            "found": False,
            "error": f"No goods receipt was found for {po_id}. Do not invent a receipt.",
            "receipt_status": "missing",
        }
    return {
        "found": True,
        "goods_receipt": receipt.model_dump(),
        "receipt_status": receipt_status_for(po_id),
        "goods_fully_received": goods_fully_received(po_id),
    }


@function_tool
def find_duplicate_invoices(invoice_id: str) -> dict:
    """Find other invoices that share the same vendor_invoice_number."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {
            "found": False,
            "error": f"Invoice {invoice_id} was not found. Do not invent duplicates.",
        }
    duplicates = load_duplicate_invoices(invoice_id)
    return {
        "found": True,
        "vendor_invoice_number": invoice.vendor_invoice_number,
        "duplicate_detected": len(duplicates) > 0,
        "duplicates": [item.model_dump() for item in duplicates],
    }


@function_tool
def find_precedents(invoice_id: str) -> dict:
    """Look up similar human corrections stored in AP memory."""
    from memory import find_similar_precedents

    checks = python_checks(invoice_id)
    if not checks.get("found"):
        return {
            "found": False,
            "error": f"Invoice {invoice_id} was not found. Do not invent precedents.",
        }
    matches = find_similar_precedents(invoice_id, checks)
    return {
        "found": True,
        "match_count": len(matches),
        "precedents": matches,
    }
