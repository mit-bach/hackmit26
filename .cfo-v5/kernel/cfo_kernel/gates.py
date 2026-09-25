"""Kernel gates that sit next to a mutating op. The RPC path calls these before the op."""

from __future__ import annotations

from cfo_kernel.validators import GateFailed


def assert_kernel_gate(op: str, args: dict) -> None:
    if op == "accrual.tools.create_accrual":
        from accrual.estimation import compute_estimate, invoice_already_received
        from accrual.store import build_estimate_context

        vendor = str(args.get("vendor") or "")
        period = str(args.get("period") or "")
        context = build_estimate_context(vendor, period)
        if invoice_already_received(context):
            raise GateFailed("Invoice already received for this period. Do not accrue.")
        method = args.get("method")
        if method:
            candidate = compute_estimate(context, method)
            if not candidate.applicable or candidate.amount is None:
                raise GateFailed(candidate.rationale or "accrual estimate is not applicable")
        return
    if op == "accrual.tools.reconcile_accrual_with_invoice":
        from accrual.ledger import find_accrual

        accrual_id = str(args.get("accrual_id") or "")
        if not accrual_id or find_accrual(accrual_id) is None:
            raise GateFailed(f"No open accrual {accrual_id} to reconcile.")
        return
    if op == "close.month_end.run_month_end":
        # evaluate_close_gates runs in after_mutate on the op result.
        return
