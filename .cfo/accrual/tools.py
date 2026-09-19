from __future__ import annotations

from agents import function_tool

from accrual.estimation import (
    candidates_for,
    compute_estimate,
    history_stats,
    infer_cadence,
    invoice_already_received,
    naive_recent_average_is_misleading,
    sorted_history,
)
from accrual.ledger import (
    create_accrual as persist_accrual,
    find_open_accrual,
    get_open_accruals as load_open_accruals,
    journal_for,
    reconcile_accrual,
)
from accrual.models import EstimationMethod
from accrual.store import (
    build_estimate_context,
    contract_for,
    current_invoices_for,
    expense_account_for,
    goods_receipts_for,
    invoices_for_vendor,
    later_invoices_for,
    list_expected_vendors,
    purchase_orders_for,
    usage_for,
)


def _dump(model) -> dict:
    return model.model_dump(mode="json")


@function_tool
def get_expected_invoices(period: str) -> dict:
    """Discover expected expenses and missing bills from financial evidence."""
    from accrual.discovery import discover_period

    report = discover_period(period)
    return {
        "found": True,
        "period": period,
        "expected_count": report.expected_count,
        "invoices_received_count": report.invoices_received_count,
        "missing_count": report.missing_count,
        "vendors": [_dump(item) for item in report.results],
    }


@function_tool
def get_current_period_invoices(period: str, vendor: str = "") -> dict:
    """Invoices already received for the accounting period."""
    if vendor:
        invoices = current_invoices_for(vendor, period)
    else:
        invoices = [
            item
            for expected in list_expected_vendors(period)
            for item in current_invoices_for(expected.vendor, period)
        ]
    return {
        "found": True,
        "period": period,
        "vendor": vendor or None,
        "invoice_count": len(invoices),
        "invoices": [_dump(item) for item in invoices],
    }


@function_tool
def get_vendor_invoice_history(vendor: str) -> dict:
    """Historical invoices and Python-computed stats for one vendor. Do not recalculate the stats."""
    invoices = sorted_history(invoices_for_vendor(vendor))
    if not invoices:
        return {
            "found": False,
            "vendor": vendor,
            "error": f"No invoices found for {vendor}. Do not invent invoice history.",
        }
    return {
        "found": True,
        "vendor": vendor,
        "inferred_cadence": infer_cadence(invoices),
        "stats": history_stats(invoices),
        "invoices": [_dump(item) for item in invoices],
    }


@function_tool
def get_purchase_orders(vendor: str, period: str = "") -> dict:
    """Purchase orders for a vendor, optionally limited to a period."""
    orders = purchase_orders_for(vendor, period)
    if not orders:
        return {
            "found": False,
            "vendor": vendor,
            "period": period or None,
            "error": f"No purchase orders found for {vendor}. Do not invent a PO.",
        }
    return {
        "found": True,
        "vendor": vendor,
        "period": period or None,
        "purchase_orders": [_dump(item) for item in orders],
    }


@function_tool
def get_goods_receipts(vendor: str, period: str = "") -> dict:
    """Goods receipts for a vendor, joined to the related PO."""
    pairs = goods_receipts_for(vendor, period)
    if not pairs:
        return {
            "found": False,
            "vendor": vendor,
            "period": period or None,
            "error": f"No goods receipts found for {vendor}. Do not invent a receipt.",
        }
    return {
        "found": True,
        "vendor": vendor,
        "period": period or None,
        "goods_receipts": [
            {
                "purchase_order": _dump(purchase_order),
                "goods_receipt": _dump(receipt),
            }
            for purchase_order, receipt in pairs
        ],
    }


@function_tool
def get_vendor_contract(vendor: str) -> dict:
    """Active contract terms used to infer a committed amount."""
    contract = contract_for(vendor)
    if contract is None:
        return {
            "found": False,
            "vendor": vendor,
            "error": f"No contract found for {vendor}. Do not invent contract terms.",
        }
    return {"found": True, "contract": _dump(contract)}


@function_tool
def get_vendor_usage(vendor: str, period: str = "") -> dict:
    """Metered usage and unit price. Python multiplies these; do not do that by hand."""
    rows = usage_for(vendor, period)
    if not rows:
        return {
            "found": False,
            "vendor": vendor,
            "period": period or None,
            "error": f"No usage data found for {vendor}. Do not invent consumption.",
        }
    return {
        "found": True,
        "vendor": vendor,
        "period": period or None,
        "usage": [_dump(item) for item in rows],
    }


@function_tool
def get_estimate_candidates(vendor: str, period: str) -> dict:
    """Python-computed estimate options. Choose a method; do not invent a new amount."""
    context = build_estimate_context(vendor, period)
    candidates = candidates_for(context)
    return {
        "found": True,
        "vendor": vendor,
        "period": period,
        "invoice_already_received": invoice_already_received(context),
        "current_invoice_ids": [item.invoice_id for item in context.current_invoices],
        "expense_account": context.expense_account,
        "naive_recent_average_is_misleading": naive_recent_average_is_misleading(context),
        "candidates": [_dump(item) for item in candidates],
    }


@function_tool
def compute_accrual_estimate(vendor: str, period: str, method: EstimationMethod) -> dict:
    """Return the Python amount for one named estimation method."""
    context = build_estimate_context(vendor, period)
    candidate = compute_estimate(context, method)
    return {
        "found": True,
        "vendor": vendor,
        "period": period,
        "candidate": _dump(candidate),
        "expense_account": context.expense_account,
    }


@function_tool
def create_accrual(
    vendor: str,
    period: str,
    method: EstimationMethod,
    confidence: float,
    evidence: list[str],
    reasoning_summary: str,
) -> dict:
    """Book an accrual using the Python amount for the chosen method. Idempotent per vendor+period."""
    context = build_estimate_context(vendor, period)
    if invoice_already_received(context):
        return {
            "booked": False,
            "error": "Invoice already received for this period. Do not accrue.",
            "current_invoice_ids": [item.invoice_id for item in context.current_invoices],
        }
    candidate = compute_estimate(context, method)
    if not candidate.applicable or candidate.amount is None:
        return {
            "booked": False,
            "error": candidate.rationale,
            "method": method,
        }
    existing = find_open_accrual(vendor, period)
    record = persist_accrual(
        vendor=vendor,
        period=period,
        amount=candidate.amount,
        method=method,
        confidence=confidence,
        evidence=evidence,
        reasoning_summary=reasoning_summary,
        expense_account=context.expense_account,
    )
    journal = journal_for(record.journal_entry_id)
    return {
        "booked": True,
        "already_existed": existing is not None,
        "accrual": _dump(record),
        "journal_entry": _dump(journal) if journal else None,
        "computed_amount": candidate.amount,
        "method": method,
    }


@function_tool
def get_open_accruals(period: str = "", vendor: str = "") -> dict:
    """Open (not yet reversed) accruals, optionally filtered by period or vendor."""
    rows = load_open_accruals(period=period, vendor=vendor)
    return {
        "found": True,
        "count": len(rows),
        "accruals": [_dump(item) for item in rows],
    }


@function_tool
def reconcile_accrual_with_invoice(
    accrual_id: str,
    invoice_id: str = "",
    actual_amount: float = 0,
) -> dict:
    """Reverse an open accrual and book the actual invoice. Computes estimation error in Python."""
    from accrual.ledger import find_accrual

    record = find_accrual(accrual_id)
    if record is None:
        return {"found": False, "error": f"Accrual {accrual_id} was not found."}

    invoice = None
    if invoice_id:
        matches = [
            item
            for item in later_invoices_for(record.vendor, record.period)
            if item.invoice_id == invoice_id
        ]
        invoice = matches[0] if matches else None
    if invoice is None:
        later = later_invoices_for(record.vendor, record.period)
        invoice = later[0] if later else None

    amount = actual_amount or (invoice.amount if invoice else 0)
    resolved_invoice_id = invoice_id or (invoice.invoice_id if invoice else "")
    if not resolved_invoice_id or not amount:
        return {
            "found": False,
            "error": "No matching later invoice and no actual_amount was provided.",
        }
    result = reconcile_accrual(accrual_id, resolved_invoice_id, amount)
    return {"found": True, "reconciliation": _dump(result)}
