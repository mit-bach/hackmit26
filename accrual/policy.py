"""Evidence-type method preference. Never keys off vendor names."""

from __future__ import annotations

from accrual.estimation import (
    EstimateContext,
    candidates_for,
    naive_recent_average_is_misleading,
)
from accrual.models import EstimateCandidate

# Stronger evidence types rank above proxies. Seasonal is only used when
# a naive recent average is misleading. Vendor names must never appear here.
METHOD_PREFERENCE: tuple[str, ...] = (
    "usage_run_rate",
    "goods_receipt",
    "contract_commitment",
    "seasonal_prior_year",
    "recent_average",
    "weighted_recent_average",
    "last_invoice",
    "simple_average",
    "linear_trend",
    "purchase_order",
    "conservative_minimum",
)


def preferred_candidate(context: EstimateContext) -> EstimateCandidate | None:
    """Choose one applicable Python candidate from evidence type, not vendor identity."""
    applicable = [item for item in candidates_for(context) if item.applicable and item.amount is not None]
    by_method = {item.method: item for item in applicable}
    if not applicable:
        return None
    seasonal_ok = "seasonal_prior_year" in by_method and naive_recent_average_is_misleading(context)
    for method in METHOD_PREFERENCE:
        if method == "seasonal_prior_year" and not seasonal_ok:
            continue
        if method in by_method:
            return by_method[method]
    return applicable[0]


def copy_context(context: EstimateContext, vendor: str) -> EstimateContext:
    """Reuse evidence under a different vendor name for generalization tests."""
    return EstimateContext(
        vendor=vendor,
        period=context.period,
        historical_invoices=list(context.historical_invoices),
        current_invoices=list(context.current_invoices),
        contract=context.contract,
        usage=context.usage,
        purchase_orders=list(context.purchase_orders),
        goods_receipts=list(context.goods_receipts),
        expense_account=context.expense_account,
    )
