from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from models import (
    CashPosition,
    DeferredPayment,
    PaymentCandidate,
    PaymentMetrics,
    PaymentPlan,
    ScheduledPayment,
)
from tools import DATA_DIR, collect_case_evidence, load_invoice, vendor_alias_established


def cash_position_path() -> Path:
    return DATA_DIR / "cash_position.json"
PRIORITY_RANK = {"critical": 0, "high": 1, "normal": 2, "low": 3}
BLOCKING_EXCEPTIONS = {
    "duplicate",
    "missing_po",
    "po_not_approved",
    "goods_not_received",
    "partial_receipt",
    "material_amount_mismatch",
    "unknown_invoice",
    "approval_limit_exceeded",
}


def load_cash_position() -> CashPosition:
    return CashPosition.model_validate(json.loads(cash_position_path().read_text()))


def as_of(cash: CashPosition | None = None) -> date:
    cash = cash or load_cash_position()
    return date.fromisoformat(cash.as_of_date)


def spendable_cash(cash: CashPosition | None = None) -> float:
    """Cash available for AP this week after payroll, other commitments, and the reserve.

    Uses the CashPosition field as passed in (AP scheduling / tests). Forecast and
    close use canonical_expected_receipts() — live AR — as the source of truth.
    """
    cash = cash or load_cash_position()
    return (
        cash.bank_balance
        + cash.expected_receipts_next_7_days
        - cash.payroll_next_7_days
        - cash.other_committed_outflows
        - cash.minimum_cash_reserve
    )


def canonical_expected_receipts(as_of: str | None = None, horizon_days: int | None = None) -> float:
    """Live AR expected collections. This is the forecast-facing receipts number."""
    from ar.context import expected_collections

    cash = load_cash_position()
    return expected_collections(
        as_of or cash.as_of_date,
        horizon_days if horizon_days is not None else cash.payment_horizon_days,
        bank_as_of=cash.as_of_date,
    )


def receipts_source_of_truth(as_of: str | None = None) -> dict:
    cash = load_cash_position()
    live = canonical_expected_receipts(as_of or cash.as_of_date, cash.payment_horizon_days)
    legacy = cash.expected_receipts_next_7_days
    return {
        "legacy_expected_receipts_next_7_days": legacy,
        "live_ar_expected_collections": live,
        "source_of_truth": "live_ar",
        "mismatch": abs(live - legacy) > 0.01,
        "legacy_is_fallback_only": True,
    }


def policy_eligible_for_pool(invoice_id: str) -> bool:
    """Invoices the AP policy layer would allow into an approved pool."""
    evidence = collect_case_evidence(invoice_id)
    if set(evidence.exception_types) & BLOCKING_EXCEPTIONS:
        return False
    if "vendor_mismatch" in evidence.exception_types and not vendor_alias_established(evidence):
        return False
    return True


def payment_candidate(
    invoice_id: str,
    approval_source: str = "ap_workflow",
    cash: CashPosition | None = None,
) -> PaymentCandidate | None:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return None
    cash = cash or load_cash_position()
    today = as_of(cash)
    due = date.fromisoformat(invoice.due_date)
    days = (due - today).days
    deadline = (
        date.fromisoformat(invoice.early_payment_discount_deadline)
        if invoice.early_payment_discount_deadline
        else None
    )
    discount_open = bool(
        invoice.early_payment_discount_percent > 0 and deadline is not None and deadline >= today
    )
    discount_amount = (
        round(invoice.amount * (invoice.early_payment_discount_percent / 100), 2) if discount_open else 0.0
    )
    pay_amount = round(invoice.amount - discount_amount, 2)
    horizon = cash.payment_horizon_days
    return PaymentCandidate(
        invoice_id=invoice.invoice_id,
        vendor=invoice.vendor,
        amount=invoice.amount,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        vendor_priority=invoice.vendor_priority,
        days_until_due=days,
        discount_open=discount_open,
        discount_percent=invoice.early_payment_discount_percent if discount_open else 0,
        discount_deadline=invoice.early_payment_discount_deadline,
        discount_amount=discount_amount,
        pay_amount_if_this_week=pay_amount,
        late=days < 0,
        due_within_horizon=0 <= days <= horizon,
        unnecessary_if_paid_early=(not discount_open) and days > horizon,
        late_fee_percent=invoice.late_fee_percent,
        approval_source=approval_source,
    )


def sort_candidates(candidates: list[PaymentCandidate]) -> list[PaymentCandidate]:
    return sorted(
        candidates,
        key=lambda item: (
            0 if item.late or item.due_within_horizon else 1,
            0 if item.discount_open else 1,
            PRIORITY_RANK.get(item.vendor_priority, 9),
            item.days_until_due,
            -item.discount_amount,
        ),
    )


def policy_backfill_order(candidates: list[PaymentCandidate]) -> list[PaymentCandidate]:
    """Due/late first (P-015), then open discounts (P-014). Never unnecessary early pays (P-016)."""
    must = [item for item in candidates if item.late or item.due_within_horizon]
    discounts = [
        item
        for item in candidates
        if item.discount_open and not item.late and not item.due_within_horizon
    ]
    return sort_candidates(must) + sort_candidates(discounts)


def apply_cash_and_policy_net(
    candidates: list[PaymentCandidate],
    proposed_pay_ids: list[str],
    cash: CashPosition | None = None,
) -> PaymentPlan:
    """Python enforces reserve, HOLD exclusion, discounts, dues, and no unnecessary early pays."""
    cash = cash or load_cash_position()
    today = as_of(cash)
    by_id = {item.invoice_id: item for item in candidates}
    remaining = spendable_cash(cash)
    paid: list[ScheduledPayment] = []
    paid_ids: set[str] = set()

    def try_pay(item: PaymentCandidate) -> None:
        nonlocal remaining
        if item.invoice_id in paid_ids or item.unnecessary_if_paid_early:
            return
        if item.pay_amount_if_this_week <= remaining + 1e-9:
            paid.append(
                ScheduledPayment(
                    invoice_id=item.invoice_id,
                    amount=item.pay_amount_if_this_week,
                    reason=_default_reason(item),
                    capture_discount=item.discount_open,
                )
            )
            paid_ids.add(item.invoice_id)
            remaining -= item.pay_amount_if_this_week

    proposed_items = [by_id[invoice_id] for invoice_id in proposed_pay_ids if invoice_id in by_id]
    for item in sort_candidates(proposed_items):
        try_pay(item)

    for item in policy_backfill_order(candidates):
        try_pay(item)

    defer: list[DeferredPayment] = []
    for item in candidates:
        if item.invoice_id in paid_ids:
            continue
        if item.unnecessary_if_paid_early:
            reason = "Discount closed and not due this horizon; defer to avoid an unnecessary early payment."
            proposed = item.due_date
        elif item.pay_amount_if_this_week > remaining + 1e-9:
            reason = "Insufficient spendable cash after reserve, payroll, and other commitments."
            proposed = (today + timedelta(days=cash.payment_horizon_days)).isoformat()
        else:
            reason = "Not selected for this week's plan."
            proposed = item.due_date
        defer.append(
            DeferredPayment(invoice_id=item.invoice_id, reason=reason, proposed_pay_date=proposed)
        )

    total = round(sum(row.amount for row in paid), 2)
    cash_after = round(
        cash.bank_balance
        + cash.expected_receipts_next_7_days
        - cash.payroll_next_7_days
        - cash.other_committed_outflows
        - total,
        2,
    )
    return PaymentPlan(
        as_of_date=cash.as_of_date,
        pay_this_week=paid,
        defer=defer,
        total_payout=total,
        cash_after_payments=cash_after,
        reserve_ok=cash_after + 1e-9 >= cash.minimum_cash_reserve,
        reasons=["Python applied P-012 through P-016 to the scheduler proposal."],
        confidence=0.99,
    )


def _default_reason(item: PaymentCandidate) -> str:
    if item.late:
        return "Invoice is already past due."
    if item.due_within_horizon:
        return f"Due {item.due_date}, within this week's payment horizon."
    if item.discount_open:
        return (
            f"Capture {item.discount_percent:g}% discount of ${item.discount_amount:,.2f} "
            f"before {item.discount_deadline}."
        )
    return "Selected for this week's payment run."


def compute_metrics(
    candidates: list[PaymentCandidate],
    plan: PaymentPlan,
    cash: CashPosition | None = None,
) -> PaymentMetrics:
    cash = cash or load_cash_position()
    pay_ids = {row.invoice_id for row in plan.pay_this_week}
    due = [item for item in candidates if item.late or item.due_within_horizon]
    due_paid = [item for item in due if item.invoice_id in pay_ids]
    discounts_available = round(sum(item.discount_amount for item in candidates if item.discount_open), 2)
    discounts_captured = round(
        sum(item.discount_amount for item in candidates if item.invoice_id in pay_ids and item.discount_open),
        2,
    )
    unnecessary = sum(1 for item in candidates if item.invoice_id in pay_ids and item.unnecessary_if_paid_early)
    late_fees_avoided = round(
        sum(item.amount * (item.late_fee_percent / 100) for item in due_paid if item.late_fee_percent),
        2,
    )
    on_time = (len(due_paid) / len(due) * 100) if due else 100.0
    return PaymentMetrics(
        invoices_due_this_horizon=len(due),
        due_invoices_paid_on_time=len(due_paid),
        on_time_percent=round(on_time, 1),
        discounts_available=discounts_available,
        discounts_captured=discounts_captured,
        discounts_missed=round(discounts_available - discounts_captured, 2),
        late_fees_avoided=late_fees_avoided,
        unnecessary_early_payments=unnecessary,
        reserve_violation=not plan.reserve_ok,
        total_cash_retained=plan.cash_after_payments,
    )
