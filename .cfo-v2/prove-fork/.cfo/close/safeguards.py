"""Cross-workflow boundaries. Does not replace AP, accrual, or scheduler internals."""

from __future__ import annotations

from accrual.ledger import get_open_accruals
from close.models import CloseRun
from scheduling.pool import load_pool, save_pool
from tools import normalize_vendor


def apply_close_safeguards(state: CloseRun) -> list[str]:
    """Enforce close boundaries and return the rules that fired."""
    fired: list[str] = []
    held = set(state.held_ids)
    approved = set(state.approved_ids)
    received_vendors = set()
    if state.discovery:
        received_vendors = {
            normalize_vendor(item.vendor)
            for item in state.discovery.results
            if item.invoice_received
        }

    pool = load_pool()
    seen: set[str] = set()
    cleaned: list[dict] = []
    for row in pool:
        invoice_id = row.get("invoice_id")
        if not invoice_id:
            continue
        if invoice_id in held:
            fired.append(f"hold_excluded_from_pool:{invoice_id}")
            continue
        if invoice_id in seen:
            fired.append(f"duplicate_pool_row_removed:{invoice_id}")
            continue
        if invoice_id not in approved and invoice_id not in held:
            # Accrual-only vendors must not appear as payables.
            if invoice_id.startswith("ACC-"):
                fired.append(f"accrual_not_payable:{invoice_id}")
                continue
        seen.add(invoice_id)
        cleaned.append(row)
    if len(cleaned) != len(pool):
        save_pool(cleaned)
        fired.append("pool_cleaned")

    if state.accrual:
        for decision in state.accrual.accruals_created:
            if normalize_vendor(decision.vendor) in received_vendors:
                fired.append(f"received_invoice_must_not_accrue:{decision.vendor}")

    for accrual in get_open_accruals(period=state.period):
        if accrual.actual_invoice_id:
            fired.append(f"reconciled_accrual_still_open:{accrual.accrual_id}")

    payout_ids = {item.payout_id for item in state.integrations if item.payout_id}
    for payout_id in payout_ids:
        if payout_id in seen:
            fired.append(f"payout_must_not_enter_payable_pool:{payout_id}")

    return list(dict.fromkeys(fired))


def assert_close_invariants(state: CloseRun) -> None:
    """Raise if close totals or boundaries are inconsistent."""
    if state.invoices_received != len(state.invoice_ids):
        raise ValueError("Invoice count does not match unique invoice IDs.")
    if len(state.approved_ids) + len(state.held_ids) != state.invoices_received:
        raise ValueError("Approved + held invoices must equal invoices received.")
    if set(state.approved_ids) & set(state.held_ids):
        raise ValueError("An invoice cannot be both approved and held.")
    if len(state.approved_ids) != len(set(state.approved_ids)):
        raise ValueError("Approved invoice IDs are duplicated.")
    if state.accrual and state.discovery:
        accrued_vendors = {normalize_vendor(item.vendor) for item in state.accrual.accruals_created}
        received = {
            normalize_vendor(item.vendor)
            for item in state.discovery.results
            if item.invoice_received
        }
        overlap = accrued_vendors & received
        if overlap:
            raise ValueError(f"Received vendors were accrued: {sorted(overlap)}")
    pool_ids = {row.get("invoice_id") for row in load_pool()}
    if pool_ids & set(state.held_ids):
        raise ValueError("HOLD invoices remain in the payment pool.")
    if any(str(item).startswith("ACC-") for item in pool_ids):
        raise ValueError("An accrual identifier entered the payable pool.")
