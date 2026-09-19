from __future__ import annotations

import json
from calendar import monthrange
from datetime import date
from functools import lru_cache
from pathlib import Path

from accrual.cutoff import dated_visible, invoice_visible, later_invoices_allowed
from accrual.estimation import EstimateContext, period_from_date
from accrual.models import (
    AccrualInvoice,
    ExpectedVendor,
    VendorContract,
    VendorUsage,
)
from models import GoodsReceipt, Invoice, PurchaseOrder
from tools import (
    DATA_DIR,
    all_goods_receipts,
    all_invoices,
    all_purchase_orders,
    normalize_vendor,
)

LIABILITY_ACCOUNT = "Accrued Expenses"

VENDOR_EXPENSE_ACCOUNTS = {
    "aethercompute": "Cloud Infrastructure Expense",
    "amazonwebservic": "Cloud Infrastructure Expense",
    "cleanspacefacility": "Facilities Expense",
    "harborelectric": "Utilities Expense",
    "lindholmruizllp": "Legal Expense",
    "heliohardware": "IT Hardware Expense",
    "pulserecruiting": "Recruiting Expense",
    "orbitanalytic": "Software Subscription Expense",
    "newforgeconsulting": "Professional Services Expense",
}


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return raw


@lru_cache(maxsize=1)
def _historical_invoices() -> list[AccrualInvoice]:
    return [
        AccrualInvoice.model_validate(item)
        for item in _read_json(DATA_DIR / "historical_invoices.json")
    ]


@lru_cache(maxsize=1)
def _contracts() -> list[VendorContract]:
    return [
        VendorContract.model_validate(item)
        for item in _read_json(DATA_DIR / "vendor_contracts.json")
    ]


@lru_cache(maxsize=1)
def _usage_rows() -> list[VendorUsage]:
    return [VendorUsage.model_validate(item) for item in _read_json(DATA_DIR / "vendor_usage.json")]


@lru_cache(maxsize=1)
def _later_invoices() -> list[AccrualInvoice]:
    return [
        AccrualInvoice.model_validate(item)
        for item in _read_json(DATA_DIR / "later_invoices.json")
    ]


def clear_store_cache() -> None:
    _historical_invoices.cache_clear()
    _contracts.cache_clear()
    _usage_rows.cache_clear()
    _later_invoices.cache_clear()


def same_vendor(left: str, right: str) -> bool:
    return normalize_vendor(left) == normalize_vendor(right)


def _from_ap_invoice(invoice: Invoice) -> AccrualInvoice:
    return AccrualInvoice(
        invoice_id=invoice.invoice_id,
        vendor=invoice.vendor,
        amount=invoice.amount,
        invoice_date=invoice.invoice_date,
        service_period=period_from_date(invoice.invoice_date),
        vendor_invoice_number=invoice.vendor_invoice_number,
        description=invoice.description,
        po_id=invoice.po_id,
        source="ap",
    )


def all_accrual_invoices() -> list[AccrualInvoice]:
    merged = list(_historical_invoices())
    seen = {item.invoice_id for item in merged}
    for invoice in all_invoices():
        if invoice.invoice_id in seen:
            continue
        merged.append(_from_ap_invoice(invoice))
        seen.add(invoice.invoice_id)
    return [item for item in merged if invoice_visible(item.service_period)]


def invoices_for_vendor(vendor: str) -> list[AccrualInvoice]:
    return [item for item in all_accrual_invoices() if same_vendor(item.vendor, vendor)]


def invoices_for_period(vendor: str, period: str) -> list[AccrualInvoice]:
    return [item for item in invoices_for_vendor(vendor) if item.service_period == period]


def historical_invoices_for(vendor: str, period: str) -> list[AccrualInvoice]:
    return [item for item in invoices_for_vendor(vendor) if item.service_period < period]


def current_invoices_for(vendor: str, period: str) -> list[AccrualInvoice]:
    return invoices_for_period(vendor, period)


def later_invoices_for(vendor: str = "", period: str = "") -> list[AccrualInvoice]:
    if not later_invoices_allowed():
        return []
    rows = list(_later_invoices())
    if vendor:
        rows = [item for item in rows if same_vendor(item.vendor, vendor)]
    if period:
        rows = [item for item in rows if item.service_period == period]
    return rows


def contract_for(vendor: str) -> VendorContract | None:
    for contract in _contracts():
        if not same_vendor(contract.vendor, vendor):
            continue
        if not dated_visible(contract.start_date) and current_cutoff_period():
            continue
        return contract
    return None


def current_cutoff_period() -> str | None:
    from accrual.cutoff import current_cutoff

    cutoff = current_cutoff()
    return cutoff.period if cutoff else None


def usage_for(vendor: str, period: str = "") -> list[VendorUsage]:
    rows = [item for item in _usage_rows() if same_vendor(item.vendor, vendor)]
    if period:
        rows = [item for item in rows if item.period == period]
    as_of = current_cutoff_period()
    if as_of:
        rows = [item for item in rows if item.period <= as_of]
    return sorted(rows, key=lambda item: item.period)


def purchase_orders_for(vendor: str, period: str = "") -> list[PurchaseOrder]:
    rows = [item for item in all_purchase_orders() if same_vendor(item.vendor, vendor)]
    rows = [item for item in rows if dated_visible(item.created_date) or not current_cutoff_period()]
    if not period:
        return rows
    receipt_po_ids = {
        receipt.po_id
        for receipt in all_goods_receipts()
        if receipt.received_date and period_from_date(receipt.received_date) == period
    }
    return [
        item
        for item in rows
        if period_from_date(item.created_date) == period or item.po_id in receipt_po_ids
    ]


def goods_receipts_for(vendor: str, period: str = "") -> list[tuple[PurchaseOrder, GoodsReceipt]]:
    purchase_orders = {item.po_id: item for item in purchase_orders_for(vendor)}
    pairs: list[tuple[PurchaseOrder, GoodsReceipt]] = []
    for receipt in all_goods_receipts():
        purchase_order = purchase_orders.get(receipt.po_id)
        if purchase_order is None:
            continue
        if period:
            receipt_period = period_from_date(receipt.received_date) if receipt.received_date else ""
            po_period = period_from_date(purchase_order.created_date)
            if receipt_period != period and po_period != period:
                continue
        if current_cutoff_period() and receipt.received_date and not dated_visible(receipt.received_date):
            continue
        pairs.append((purchase_order, receipt))
    return pairs


def expense_account_for(vendor: str, period: str = "") -> str:
    contract = contract_for(vendor)
    if contract and contract.expense_account:
        return contract.expense_account
    history = invoices_for_vendor(vendor)
    if period:
        history = [item for item in history if item.service_period <= period]
    for invoice in reversed(sorted(history, key=lambda item: item.service_period)):
        if invoice.expense_account:
            return invoice.expense_account
    return VENDOR_EXPENSE_ACCOUNTS.get(normalize_vendor(vendor), "Operating Expense")


def _period_end(period: str) -> date:
    year, month = (int(part) for part in period.split("-"))
    return date(year, month, monthrange(year, month)[1])


def _contract_active(contract: VendorContract, period: str) -> bool:
    start = date.fromisoformat(contract.start_date)
    end = date.fromisoformat(contract.end_date)
    period_start = date(int(period[:4]), int(period[5:7]), 1)
    return start <= _period_end(period) and end >= period_start


def _cadence_due(cadence: str, period: str) -> bool:
    month = int(period[5:7])
    if cadence == "monthly":
        return True
    if cadence == "quarterly":
        return month in {3, 6, 9, 12}
    return False


def list_expected_vendors(period: str) -> list[ExpectedVendor]:
    """Vendors discovery marked as expected, received, or missing-bill candidates."""
    from accrual.discovery import as_expected_vendors, discover_period

    return as_expected_vendors(discover_period(period))


def build_estimate_context(vendor: str, period: str) -> EstimateContext:
    current = current_invoices_for(vendor, period)
    usage_rows = usage_for(vendor, period)
    return EstimateContext(
        vendor=vendor,
        period=period,
        historical_invoices=historical_invoices_for(vendor, period),
        current_invoices=current,
        contract=contract_for(vendor),
        usage=usage_rows[-1] if usage_rows else None,
        purchase_orders=purchase_orders_for(vendor, period),
        goods_receipts=goods_receipts_for(vendor, period),
        expense_account=expense_account_for(vendor, period),
    )
