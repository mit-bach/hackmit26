"""Discover which expenses are expected in a period before the Accrual Agent estimates them."""

from __future__ import annotations

from accrual.estimation import infer_cadence, months_between, parse_period, period_from_date, prior_year_period
from accrual.models import (
    DiscoveryReport,
    DiscoveryResult,
    DiscoverySignal,
    ExpectedVendor,
)
from accrual.policy import preferred_candidate
from accrual.store import (
    all_accrual_invoices,
    build_estimate_context,
    contract_for,
    current_invoices_for,
    expense_account_for,
    goods_receipts_for,
    historical_invoices_for,
    purchase_orders_for,
    usage_for,
)
from accrual.trace import new_run_id, vendor_slug
from tools import all_goods_receipts, all_purchase_orders, normalize_vendor

from accrual.store import _contract_active, _contracts, _usage_rows


def _prior_period(period: str) -> str:
    year, month = parse_period(period)
    month -= 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year:04d}-{month:02d}"


def _consecutive_months(history_periods: list[str], ending_at: str) -> int:
    period_set = set(history_periods)
    streak = 0
    cursor = ending_at
    while cursor in period_set:
        streak += 1
        cursor = _prior_period(cursor)
    return streak


def _cadence_due(cadence: str, period: str) -> bool:
    month = int(period[5:7])
    if cadence == "monthly":
        return True
    if cadence == "quarterly":
        return month in {3, 6, 9, 12}
    if cadence == "annual":
        return False
    return False


def _candidate_universe(period: str) -> list[str]:
    names: dict[str, str] = {}

    def add(name: str) -> None:
        names.setdefault(normalize_vendor(name), name)

    for invoice in all_accrual_invoices():
        if invoice.service_period < period:
            add(invoice.vendor)
    for contract in _contracts():
        if _contract_active(contract, period):
            add(contract.vendor)
    for usage in _usage_rows():
        if usage.period == period:
            add(usage.vendor)
    billed_po_ids = {
        item.po_id
        for item in all_accrual_invoices()
        if item.service_period == period and item.po_id
    }
    for purchase_order in all_purchase_orders():
        if period_from_date(purchase_order.created_date) != period:
            continue
        if purchase_order.po_id in billed_po_ids:
            continue
        add(purchase_order.vendor)
    for receipt in all_goods_receipts():
        if not receipt.received_date or period_from_date(receipt.received_date) != period:
            continue
        if receipt.po_id in billed_po_ids:
            continue
        purchase_order = next(
            (item for item in all_purchase_orders() if item.po_id == receipt.po_id),
            None,
        )
        if purchase_order:
            add(purchase_order.vendor)
    return sorted(names.values(), key=str.lower)


def discover_vendor(vendor: str, period: str, run_id: str = "") -> DiscoveryResult:
    history = historical_invoices_for(vendor, period)
    current = current_invoices_for(vendor, period)
    contract = contract_for(vendor)
    usage = usage_for(vendor, period)
    receipts = goods_receipts_for(vendor, period)
    purchase_orders = purchase_orders_for(vendor, period)
    billed_pos = {item.po_id for item in current if item.po_id}
    unbilled_receipts = [(po, gr) for po, gr in receipts if po.po_id not in billed_pos and gr.received]
    unbilled_pos = [item for item in purchase_orders if item.po_id not in billed_pos]
    signals: list[DiscoverySignal] = []

    periods = [item.service_period for item in history]
    cadence = infer_cadence(history)
    last_history = max(periods, default="")
    streak = _consecutive_months(periods, _prior_period(period)) if periods else 0

    if len(current) > 1:
        signals.append(
            DiscoverySignal(
                type="multiple_current_invoices",
                detail=(
                    f"{len(current)} distinct current-period invoices received "
                    f"({', '.join(item.invoice_id for item in current)}). "
                    "The expected period obligation is treated as satisfied."
                ),
                confidence=0.99,
            )
        )

    if cadence == "monthly" and last_history and months_between(last_history, period) <= 2 and streak >= 3:
        signals.append(
            DiscoverySignal(
                type="monthly_cadence",
                detail=f"Invoices received in each of the previous {streak} months",
                confidence=0.99 if streak >= 6 else 0.95,
            )
        )
    elif cadence == "monthly" and last_history and months_between(last_history, period) <= 2:
        signals.append(
            DiscoverySignal(
                type="monthly_cadence",
                detail=f"Recent monthly billing; last invoice {last_history}",
                confidence=0.9,
            )
        )

    if cadence == "quarterly" and _cadence_due("quarterly", period):
        signals.append(
            DiscoverySignal(
                type="quarterly_cadence",
                detail=f"Quarterly billing pattern; {period[5:]} is a quarter-end month",
                confidence=0.93,
            )
        )

    if any(item.service_period == prior_year_period(period) for item in history):
        signals.append(
            DiscoverySignal(
                type="seasonal_prior_year",
                detail=f"Same month last year ({prior_year_period(period)}) was invoiced",
                confidence=0.8,
            )
        )

    if contract and _contract_active(contract, period) and contract.billing_cadence != "as_needed":
        if _cadence_due(contract.billing_cadence, period) and contract.amount:
            cadence_label = contract.billing_cadence.title()
            signals.append(
                DiscoverySignal(
                    type="recurring_contract",
                    detail=f"{cadence_label} contract {contract.contract_id} for ${contract.amount:,.2f}",
                    confidence=0.99 if contract.billing_cadence == "monthly" else 0.97,
                )
            )
    if contract and contract.billing_cadence == "as_needed":
        signals.append(
            DiscoverySignal(
                type="as_needed_contract",
                detail="Time-and-materials contract with no monthly commitment",
                confidence=0.2,
            )
        )

    if usage:
        signals.append(
            DiscoverySignal(
                type="usage",
                detail=f"Usage recorded for {period}",
                confidence=0.9,
            )
        )

    if unbilled_receipts:
        receipt_ids = ", ".join(receipt.receipt_id for _, receipt in unbilled_receipts)
        po_ids = ", ".join(po.po_id for po, _ in unbilled_receipts)
        signals.append(
            DiscoverySignal(
                type="goods_receipt",
                detail=f"Goods received under {po_ids} ({receipt_ids})",
                confidence=1.0,
            )
        )

    draft_only = False
    approved_unreceived = False
    for item in unbilled_pos:
        if item.po_id in {po.po_id for po, _ in unbilled_receipts}:
            continue
        if item.status.lower() != "approved":
            draft_only = True
            signals.append(
                DiscoverySignal(
                    type="draft_purchase_order",
                    detail=f"{item.po_id} is {item.status}; no goods receipt",
                    confidence=0.25,
                )
            )
        else:
            approved_unreceived = True
            signals.append(
                DiscoverySignal(
                    type="approved_purchase_order",
                    detail=f"Approved {item.po_id} has no invoice or receipt",
                    confidence=0.55,
                )
            )

    if len(history) == 1 and streak < 2 and not contract and not unbilled_receipts and not usage:
        signals.append(
            DiscoverySignal(
                type="isolated_invoice",
                detail=f"Single historical invoice in {history[0].service_period} does not imply recurrence",
                confidence=0.1,
            )
        )

    confidence = max((item.confidence for item in signals), default=0.0)
    invoice_received = bool(current)
    strong = confidence >= 0.5
    weak_review = 0.2 <= confidence < 0.5 and (draft_only or approved_unreceived or (contract and contract.billing_cadence == "as_needed"))
    expense_expected = strong or (invoice_received and confidence >= 0.5) or weak_review
    if invoice_received and not signals:
        expense_expected = False
    missing = expense_expected and not invoice_received

    if invoice_received:
        reason = f"Expense may be expected, but {', '.join(item.invoice_id for item in current)} already arrived."
        expense_expected = True if strong or cadence in {"monthly", "quarterly"} else expense_expected
        missing = False
        if strong or cadence in {"monthly", "quarterly"}:
            expense_expected = True
            confidence = max(confidence, 0.9)
            invoice_ids = ", ".join(item.invoice_id for item in current)
            if len(current) > 1:
                reason = (
                    f"Expected {cadence or 'period'} expense already invoiced via "
                    f"{len(current)} distinct bills ({invoice_ids})."
                )
            else:
                reason = f"Expected {cadence or 'period'} expense already invoiced ({invoice_ids})."
    elif missing and unbilled_receipts:
        reason = "Goods received this period and no matching invoice."
    elif missing and contract and contract.billing_cadence != "as_needed":
        reason = f"{contract.billing_cadence.title()} recurring vendor with no {period} invoice."
    elif missing and cadence == "monthly":
        reason = f"Monthly recurring vendor with no {period} invoice."
    elif missing and cadence == "quarterly":
        reason = f"Quarterly vendor due in {period} with no invoice."
    elif missing and weak_review:
        reason = "Weak evidence only; do not assume the expense was incurred."
    elif not expense_expected:
        reason = "No recurring pattern, contract commitment, or received goods for this period."
    else:
        reason = "Possible period expense; invoice not received."

    indicative_amount = None
    indicative_method = None
    if missing:
        candidate = preferred_candidate(build_estimate_context(vendor, period))
        if candidate:
            indicative_amount = candidate.amount
            indicative_method = candidate.method

    return DiscoveryResult(
        vendor=vendor,
        period=period,
        expense_expected=expense_expected,
        invoice_received=invoice_received,
        missing_bill_candidate=missing,
        expectation_confidence=round(confidence, 2),
        signals=signals,
        reason=reason,
        discovery_trace_id=f"{period}/{run_id or 'discovery'}/discovery/{vendor_slug(vendor)}",
        current_invoice_ids=[item.invoice_id for item in current],
        indicative_amount=indicative_amount,
        indicative_method=indicative_method,
    )


def discover_period(period: str, run_id: str = "") -> DiscoveryReport:
    run_id = run_id or new_run_id()
    results = [discover_vendor(vendor, period, run_id=run_id) for vendor in _candidate_universe(period)]
    results = [
        item
        for item in results
        if item.expense_expected or item.invoice_received or item.missing_bill_candidate or item.signals
    ]
    # Drop pure isolated-invoice vendors that are not expected.
    results = [
        item
        for item in results
        if item.expense_expected
        or item.invoice_received
        or item.missing_bill_candidate
        or any(signal.type != "isolated_invoice" for signal in item.signals)
    ]
    return DiscoveryReport(
        period=period,
        results=sorted(results, key=lambda item: item.vendor.lower()),
        expected_count=sum(1 for item in results if item.expense_expected),
        invoices_received_count=sum(1 for item in results if item.invoice_received),
        missing_count=sum(1 for item in results if item.missing_bill_candidate),
        discovery_run_id=run_id,
    )


def as_expected_vendors(report: DiscoveryReport) -> list[ExpectedVendor]:
    rows: list[ExpectedVendor] = []
    for item in report.results:
        if not (item.expense_expected or item.missing_bill_candidate or item.invoice_received):
            continue
        rows.append(
            ExpectedVendor(
                vendor=item.vendor,
                period=item.period,
                signals=[signal.type for signal in item.signals],
                invoice_already_received=item.invoice_received,
                current_invoice_ids=item.current_invoice_ids,
                expense_account=expense_account_for(item.vendor, item.period),
            )
        )
    return rows


def missing_bill_candidates(report: DiscoveryReport) -> list[DiscoveryResult]:
    return [item for item in report.results if item.missing_bill_candidate]


def received_expenses(report: DiscoveryReport) -> list[DiscoveryResult]:
    return [item for item in report.results if item.invoice_received]
