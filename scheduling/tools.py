from __future__ import annotations

from agents import function_tool

from scheduling.cash import (
    load_cash_position,
    payment_candidate,
    spendable_cash,
)
from scheduling.pool import load_pool
from tools import load_policies


def _dump(model) -> dict:
    return model.model_dump()


@function_tool
def get_cash_position() -> dict:
    """Return the company cash position. Do not invent balances or reserves."""
    cash = load_cash_position()
    return {
        "found": True,
        "cash": _dump(cash),
        "spendable_cash": spendable_cash(cash),
        "spendable_cash_note": (
            "bank_balance + expected receipts - payroll - other committed outflows - minimum reserve"
        ),
    }


@function_tool
def get_approved_pool() -> dict:
    """Return invoices that already passed AP validation and may be scheduled."""
    rows = load_pool()
    return {"found": True, "count": len(rows), "invoices": rows}


@function_tool
def get_payment_candidates() -> dict:
    """Python-computed payment facts for the approved pool. Do not recalculate discounts or due dates."""
    rows = load_pool()
    candidates = []
    for row in rows:
        item = payment_candidate(row["invoice_id"], approval_source=row.get("approval_source", "ap_workflow"))
        if item is not None:
            candidates.append(_dump(item))
    return {"found": True, "count": len(candidates), "candidates": candidates}


@function_tool
def get_treasury_policies() -> dict:
    """Return payment-scheduling policies P-012 through P-016."""
    policies = [item for item in load_policies() if "payment_scheduling" in item.exception_types]
    return {"found": True, "policies": [_dump(item) for item in policies]}
