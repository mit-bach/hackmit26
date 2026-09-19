"""Deterministic arithmetic for accrual estimates. The LLM chooses a method; Python does the math."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Iterable

from accrual.models import (
    AccrualInvoice,
    EstimateCandidate,
    EstimationMethod,
    VendorContract,
    VendorUsage,
)
from models import GoodsReceipt, PurchaseOrder

RECENT_WINDOW = 6
RECENT_AVERAGE_WINDOW = 3
QUARTER_END_MONTHS = {3, 6, 9, 12}


@dataclass
class EstimateContext:
    vendor: str
    period: str
    historical_invoices: list[AccrualInvoice] = field(default_factory=list)
    current_invoices: list[AccrualInvoice] = field(default_factory=list)
    contract: VendorContract | None = None
    usage: VendorUsage | None = None
    purchase_orders: list[PurchaseOrder] = field(default_factory=list)
    goods_receipts: list[tuple[PurchaseOrder, GoodsReceipt]] = field(default_factory=list)
    expense_account: str = ""


def money(value: float) -> float:
    return round(float(value), 2)


def parse_period(period: str) -> tuple[int, int]:
    year_str, month_str = period.split("-", 1)
    return int(year_str), int(month_str)


def months_between(start: str, end: str) -> int:
    start_year, start_month = parse_period(start)
    end_year, end_month = parse_period(end)
    return (end_year - start_year) * 12 + (end_month - start_month)


def prior_year_period(period: str) -> str:
    year, month = parse_period(period)
    return f"{year - 1}-{month:02d}"


def period_from_date(value: str) -> str:
    return value[:7]


def invoice_already_received(context: EstimateContext) -> bool:
    return len(context.current_invoices) > 0


def sorted_history(invoices: Iterable[AccrualInvoice]) -> list[AccrualInvoice]:
    return sorted(invoices, key=lambda item: (item.service_period, item.invoice_date))


def recent_amounts(invoices: list[AccrualInvoice], window: int = RECENT_WINDOW) -> list[float]:
    return [item.amount for item in sorted_history(invoices)[-window:]]


def simple_average(amounts: list[float]) -> float:
    if not amounts:
        raise ValueError("simple_average requires at least one amount")
    return money(mean(amounts))


def weighted_recent_average(amounts: list[float]) -> float:
    """Linear weights 1..n so the newest invoice counts most."""
    if not amounts:
        raise ValueError("weighted_recent_average requires at least one amount")
    weights = range(1, len(amounts) + 1)
    return money(sum(amount * weight for amount, weight in zip(amounts, weights)) / sum(weights))


def last_invoice_amount(amounts: list[float]) -> float:
    if not amounts:
        raise ValueError("last_invoice_amount requires at least one amount")
    return money(amounts[-1])


def recent_average(amounts: list[float], window: int = RECENT_AVERAGE_WINDOW) -> float:
    """Mean of the newest `window` invoices. Used as the 'recent average' demo candidate."""
    if not amounts:
        raise ValueError("recent_average requires at least one amount")
    return simple_average(amounts[-window:])


def linear_trend_projection(amounts: list[float]) -> float:
    """Ordinary least squares; project one period beyond the sample."""
    count = len(amounts)
    if count < 2:
        raise ValueError("linear_trend_projection requires at least two amounts")
    xs = list(range(count))
    x_mean = (count - 1) / 2
    y_mean = mean(amounts)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, amounts))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    slope = numerator / denominator if denominator else 0.0
    intercept = y_mean - slope * x_mean
    return money(intercept + slope * count)


def coefficient_of_variation(amounts: list[float]) -> float | None:
    if len(amounts) < 2:
        return None
    average = mean(amounts)
    if average == 0:
        return None
    return round(pstdev(amounts) / abs(average), 4)


def usage_run_rate(quantity: float, unit_price: float) -> float:
    return money(quantity * unit_price)


def history_stats(invoices: list[AccrualInvoice]) -> dict:
    ordered = sorted_history(invoices)
    amounts = [item.amount for item in ordered]
    if not amounts:
        return {"count": 0}
    return {
        "count": len(amounts),
        "mean": simple_average(amounts),
        "median": money(median(amounts)),
        "min": money(min(amounts)),
        "max": money(max(amounts)),
        "last_amount": money(amounts[-1]),
        "last_period": ordered[-1].service_period,
        "coefficient_of_variation": coefficient_of_variation(amounts),
        "recent_simple_average": simple_average(recent_amounts(ordered)),
        "recent_weighted_average": weighted_recent_average(recent_amounts(ordered)),
    }


def infer_cadence(invoices: list[AccrualInvoice]) -> str:
    ordered = sorted_history(invoices)
    if len(ordered) < 2:
        return "irregular"
    gaps = [
        months_between(left.service_period, right.service_period)
        for left, right in zip(ordered, ordered[1:])
    ]
    if not gaps:
        return "irregular"
    typical = median(gaps)
    if typical <= 1.5:
        return "monthly"
    if 2.5 <= typical <= 3.5:
        return "quarterly"
    if 11 <= typical <= 13:
        return "annual"
    return "irregular"


def _history_is_fresh(invoices: list[AccrualInvoice], period: str) -> bool:
    if not invoices:
        return False
    last_period = sorted_history(invoices)[-1].service_period
    gap = months_between(last_period, period)
    cadence = infer_cadence(invoices)
    if cadence == "monthly":
        return gap <= 2
    if cadence == "quarterly":
        return gap <= 4
    if cadence == "annual":
        return gap <= 13
    return gap <= 2


def _contract_covers(contract: VendorContract, period: str) -> bool:
    return contract.start_date[:7] <= period <= contract.end_date[:7]


def _cadence_due_this_period(cadence: str, period: str) -> bool:
    _, month = parse_period(period)
    if cadence == "monthly":
        return True
    if cadence == "quarterly":
        return month in QUARTER_END_MONTHS
    if cadence == "annual":
        return False
    return False


def _unbilled_receipts(context: EstimateContext) -> list[tuple[PurchaseOrder, GoodsReceipt]]:
    billed_po_ids = {invoice.po_id for invoice in context.current_invoices if invoice.po_id}
    received: list[tuple[PurchaseOrder, GoodsReceipt]] = []
    for purchase_order, receipt in context.goods_receipts:
        if not receipt.received:
            continue
        if receipt.quantity_received <= 0 and receipt.amount_received <= 0:
            continue
        if purchase_order.po_id in billed_po_ids:
            continue
        received.append((purchase_order, receipt))
    return received


def _approved_unbilled_pos(context: EstimateContext) -> list[PurchaseOrder]:
    billed_po_ids = {invoice.po_id for invoice in context.current_invoices if invoice.po_id}
    received_po_ids = {purchase_order.po_id for purchase_order, _ in _unbilled_receipts(context)}
    approved: list[PurchaseOrder] = []
    for purchase_order in context.purchase_orders:
        if purchase_order.po_id in billed_po_ids or purchase_order.po_id in received_po_ids:
            continue
        if purchase_order.status.lower() != "approved":
            continue
        if period_from_date(purchase_order.created_date) != context.period:
            continue
        approved.append(purchase_order)
    return approved


def candidates_for(context: EstimateContext) -> list[EstimateCandidate]:
    """Return every estimation method with an applicability flag and a Python-computed amount."""
    if invoice_already_received(context):
        invoice_ids = ", ".join(item.invoice_id for item in context.current_invoices)
        return [
            EstimateCandidate(
                method="last_invoice",
                applicable=False,
                amount=None,
                rationale=f"No accrual: invoice already received ({invoice_ids}).",
                inputs={"current_invoice_ids": [item.invoice_id for item in context.current_invoices]},
            )
        ]

    history = sorted_history(context.historical_invoices)
    amounts = recent_amounts(history)
    fresh = _history_is_fresh(history, context.period)
    candidates: list[EstimateCandidate] = []

    last_period = history[-1].service_period if history else None
    last_gap = months_between(last_period, context.period) if last_period else None
    candidates.append(
        EstimateCandidate(
            method="last_invoice",
            applicable=bool(amounts) and fresh,
            amount=last_invoice_amount(amounts) if amounts and fresh else None,
            rationale=(
                f"Most recent invoice {last_period} was {amounts[-1]:,.2f}."
                if amounts and fresh
                else "Last invoice is missing or too old to use as a run-rate."
            ),
            inputs={"last_period": last_period, "months_since_last": last_gap},
        )
    )

    candidates.append(
        EstimateCandidate(
            method="simple_average",
            applicable=len(amounts) >= 2 and fresh,
            amount=simple_average(amounts) if len(amounts) >= 2 and fresh else None,
            rationale=(
                f"Mean of the last {len(amounts)} invoices is {simple_average(amounts):,.2f}."
                if len(amounts) >= 2 and fresh
                else "Need at least two recent invoices for a simple average."
            ),
            inputs={"amounts": amounts, "coefficient_of_variation": coefficient_of_variation(amounts)},
        )
    )

    last_three = [item.amount for item in history[-RECENT_AVERAGE_WINDOW:]]
    recent_ok = len(last_three) >= 2 and fresh
    candidates.append(
        EstimateCandidate(
            method="recent_average",
            applicable=recent_ok,
            amount=recent_average(last_three) if recent_ok else None,
            rationale=(
                f"Mean of the last {len(last_three)} invoices is {recent_average(last_three):,.2f}."
                if recent_ok
                else "Need at least two recent invoices for a recent average."
            ),
            inputs={"amounts": last_three, "window": RECENT_AVERAGE_WINDOW},
        )
    )

    candidates.append(
        EstimateCandidate(
            method="weighted_recent_average",
            applicable=len(amounts) >= 2 and fresh,
            amount=weighted_recent_average(amounts) if len(amounts) >= 2 and fresh else None,
            rationale=(
                f"Linear weights 1..{len(amounts)} on recent invoices give {weighted_recent_average(amounts):,.2f}."
                if len(amounts) >= 2 and fresh
                else "Need at least two recent invoices for a weighted average."
            ),
            inputs={"amounts": amounts},
        )
    )

    trend_ok = len(amounts) >= 3 and fresh
    candidates.append(
        EstimateCandidate(
            method="linear_trend",
            applicable=trend_ok,
            amount=linear_trend_projection(amounts) if trend_ok else None,
            rationale=(
                f"Least-squares projection of the last {len(amounts)} invoices is {linear_trend_projection(amounts):,.2f}."
                if trend_ok
                else "Need at least three recent invoices to project a trend."
            ),
            inputs={"amounts": amounts},
        )
    )

    prior = prior_year_period(context.period)
    seasonal = next((item for item in history if item.service_period == prior), None)
    candidates.append(
        EstimateCandidate(
            method="seasonal_prior_year",
            applicable=seasonal is not None,
            amount=money(seasonal.amount) if seasonal else None,
            rationale=(
                f"Same month last year ({prior}) billed {seasonal.amount:,.2f}."
                if seasonal
                else f"No invoice found for {prior}."
            ),
            inputs={"prior_year_period": prior, "prior_year_invoice_id": seasonal.invoice_id if seasonal else None},
        )
    )

    contract = context.contract
    contract_due = bool(
        contract
        and contract.amount
        and _contract_covers(contract, context.period)
        and _cadence_due_this_period(contract.billing_cadence, context.period)
    )
    candidates.append(
        EstimateCandidate(
            method="contract_commitment",
            applicable=contract_due,
            amount=money(contract.amount) if contract_due and contract and contract.amount is not None else None,
            rationale=(
                f"Contract {contract.contract_id} commits {contract.amount:,.2f} on a {contract.billing_cadence} cadence."
                if contract_due and contract and contract.amount is not None
                else "No fixed contract amount is due this period."
            ),
            inputs={
                "contract_id": contract.contract_id if contract else None,
                "billing_cadence": contract.billing_cadence if contract else None,
            },
        )
    )

    usage = context.usage
    usage_ok = usage is not None
    usage_amount = usage_run_rate(usage.quantity, usage.unit_price) if usage_ok else None
    candidates.append(
        EstimateCandidate(
            method="usage_run_rate",
            applicable=usage_ok,
            amount=usage_amount,
            rationale=(
                f"{usage.quantity:,.0f} {usage.metric} × {usage.unit_price} = {usage_amount:,.2f}."
                if usage_ok and usage is not None and usage_amount is not None
                else "No usage record for this period."
            ),
            inputs=(
                {
                    "quantity": usage.quantity,
                    "unit_price": usage.unit_price,
                    "metric": usage.metric,
                    "partial_period": usage.partial_period,
                }
                if usage_ok and usage is not None
                else {}
            ),
        )
    )

    receipts = _unbilled_receipts(context)
    receipt_amount = money(sum(receipt.amount_received for _, receipt in receipts)) if receipts else None
    candidates.append(
        EstimateCandidate(
            method="goods_receipt",
            applicable=bool(receipts),
            amount=receipt_amount,
            rationale=(
                f"Goods received and not invoiced total {receipt_amount:,.2f}."
                if receipts and receipt_amount is not None
                else "No unmatched goods receipt in this period."
            ),
            inputs={
                "receipt_ids": [receipt.receipt_id for _, receipt in receipts],
                "po_ids": [purchase_order.po_id for purchase_order, _ in receipts],
            },
        )
    )

    approved_pos = _approved_unbilled_pos(context)
    po_amount = money(sum(item.authorized_amount for item in approved_pos)) if approved_pos else None
    candidates.append(
        EstimateCandidate(
            method="purchase_order",
            applicable=bool(approved_pos),
            amount=po_amount,
            rationale=(
                f"Approved unreceived PO total {po_amount:,.2f}. Weaker than a goods receipt."
                if approved_pos and po_amount is not None
                else "No approved, unbilled, unrecepted PO in this period."
            ),
            inputs={"po_ids": [item.po_id for item in approved_pos]},
        )
    )

    applicable_amounts = [item.amount for item in candidates if item.applicable and item.amount is not None]
    candidates.append(
        EstimateCandidate(
            method="conservative_minimum",
            applicable=len(applicable_amounts) >= 2,
            amount=money(min(applicable_amounts)) if len(applicable_amounts) >= 2 else None,
            rationale=(
                f"Lowest applicable candidate is {min(applicable_amounts):,.2f}."
                if len(applicable_amounts) >= 2
                else "Need two applicable estimates to take a conservative minimum."
            ),
            inputs={"applicable_amounts": applicable_amounts},
        )
    )
    return candidates


def compute_estimate(context: EstimateContext, method: EstimationMethod) -> EstimateCandidate:
    for candidate in candidates_for(context):
        if candidate.method == method:
            return candidate
    return EstimateCandidate(
        method=method,
        applicable=False,
        amount=None,
        rationale=f"Unknown method {method}.",
    )


def naive_recent_average_is_misleading(context: EstimateContext) -> bool:
    """True when last-year same month diverges sharply from the last-three-month average."""
    amounts = recent_amounts(context.historical_invoices, window=3)
    seasonal = next(
        (
            item
            for item in context.historical_invoices
            if item.service_period == prior_year_period(context.period)
        ),
        None,
    )
    if seasonal is None or len(amounts) < 3:
        return False
    recent = simple_average(amounts)
    if recent == 0:
        return False
    return abs(recent - seasonal.amount) / recent >= 0.25


def is_finite_amount(value: float | None) -> bool:
    return value is not None and math.isfinite(value)
