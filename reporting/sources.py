"""AP, AR, and payroll adapters that emit canonical forecast lines."""

from __future__ import annotations

import json
from datetime import date, timedelta

from accrual.estimation import money
from reporting import ledger as reporting_ledger
from reporting.models import (
    APForecastDecision,
    CollectionExpectation,
    ForecastLine,
    PayrollSchedule,
    Receivable,
    ReceivableStatus,
    ReportingAssumptions,
)
from tools import DataFileError, load_invoice

STATUS_MAP: dict[str, ReceivableStatus] = {
    "OPEN": "open",
    "PARTIALLY_PAID": "partially_paid",
    "PAID": "paid",
    "PAST_DUE": "overdue",
    "DISPUTED": "open",
}


def load_assumptions() -> ReportingAssumptions:
    path = reporting_ledger.DATA_REPORTING / "assumptions.json"
    if not path.exists():
        return ReportingAssumptions()
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DataFileError(f"Invalid JSON in assumptions.json: {exc.msg}") from exc
    return ReportingAssumptions.model_validate(raw)


def load_payroll() -> list[PayrollSchedule]:
    path = reporting_ledger.DATA_REPORTING / "payroll.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [PayrollSchedule.model_validate(item) for item in raw]


def load_other_cash() -> list[ForecastLine]:
    path = reporting_ledger.DATA_REPORTING / "other_cash.json"
    if not path.exists():
        return []
    rows = []
    for item in json.loads(path.read_text()):
        rows.append(
            ForecastLine(
                line_id=item.get("line_id") or f"FL-OTH-{item.get('source_id')}",
                source_type="other",
                source_id=item["source_id"],
                expected_date=item["expected_date"],
                amount=money(item["amount"]),
                confidence=float(item.get("confidence", 0.9)),
                rationale=item.get("rationale") or item.get("description") or "Known other cash item",
                source_workflow="reporting",
                evidence_refs=[f"other:{item['source_id']}"],
            )
        )
    return rows


def load_ap_decisions() -> dict[str, APForecastDecision]:
    path = reporting_ledger.DATA_REPORTING / "ap_forecast_state.json"
    rows: dict[str, APForecastDecision] = {}
    if path.exists():
        for item in json.loads(path.read_text()):
            parsed = APForecastDecision.model_validate(item)
            rows[parsed.invoice_id] = parsed
    return rows


_ap_overrides: dict[str, APForecastDecision] = {}


def reset_ap_overrides() -> None:
    _ap_overrides.clear()


def set_ap_decision(
    invoice_id: str,
    *,
    hold: bool = False,
    scheduled_pay_date: str | None = None,
    approval_state: str = "approved",
    reason: str = "",
) -> APForecastDecision:
    decision = APForecastDecision(
        invoice_id=invoice_id,
        hold=hold,
        scheduled_pay_date=scheduled_pay_date,
        approval_state=approval_state,
        reason=reason,
        source="runtime",
    )
    _ap_overrides[invoice_id] = decision
    return decision


def ap_decision_for(invoice_id: str) -> APForecastDecision | None:
    if invoice_id in _ap_overrides:
        return _ap_overrides[invoice_id]
    return load_ap_decisions().get(invoice_id)


def receivable_from_invoice(invoice, customer=None) -> Receivable:
    status = STATUS_MAP.get(getattr(invoice, "status", "OPEN"), "open")
    if invoice.outstanding_amount <= 0:
        status = "paid"
    elif invoice.outstanding_amount < invoice.original_amount and status != "overdue":
        status = "partially_paid"
    return Receivable(
        invoice_id=invoice.invoice_id,
        customer_id=invoice.customer_id,
        customer_name=getattr(invoice, "customer_name", "") or (customer.customer_name if customer else ""),
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        amount=money(invoice.original_amount),
        outstanding_amount=money(invoice.outstanding_amount),
        status=status,
        promised_pay_date=invoice.promised_pay_date,
        payment_behavior=getattr(customer, "payment_behavior", "") if customer else "",
        on_time_rate=getattr(customer, "on_time_rate", 0.8) if customer else 0.8,
        average_days_late=getattr(customer, "average_days_late", 0) if customer else 0,
        currency=getattr(invoice, "currency", "USD"),
        disputed=getattr(invoice, "dispute_status", "NONE") == "OPEN",
    )


def load_receivables() -> list[Receivable]:
    from ar.store import all_invoices, get_customer

    rows = []
    for invoice in all_invoices():
        rows.append(receivable_from_invoice(invoice, get_customer(invoice.customer_id)))
    return rows


def expected_collection(receivable: Receivable, assumptions: ReportingAssumptions | None = None) -> CollectionExpectation | None:
    if receivable.outstanding_amount <= 0 or receivable.status == "paid":
        return None
    assumptions = assumptions or load_assumptions()
    due = date.fromisoformat(receivable.due_date[:10])
    disputed = bool(getattr(receivable, "disputed", False))
    if disputed:
        expected = due + timedelta(days=assumptions.ar_fallback_days_after_due)
        confidence = 0.15
        rule = "disputed"
        rationale = "Open dispute excluded from base-case cash"
    elif receivable.promised_pay_date:
        expected = date.fromisoformat(receivable.promised_pay_date[:10])
        confidence = min(0.95, max(0.55, receivable.on_time_rate + 0.1))
        rule = "promised_pay_date"
        rationale = f"Customer promised payment on {expected.isoformat()}"
    elif receivable.average_days_late:
        expected = due + timedelta(days=receivable.average_days_late)
        confidence = max(0.2, min(0.85, receivable.on_time_rate))
        rule = "historical_days_late"
        rationale = (
            f"Customer historically pays {receivable.average_days_late} days after due date"
        )
    else:
        expected = due + timedelta(days=assumptions.ar_fallback_days_after_due)
        confidence = assumptions.ar_default_confidence
        rule = "due_date"
        rationale = f"Due date {due.isoformat()}; no contrary payment history"
    if receivable.on_time_rate < assumptions.low_confidence_threshold and not disputed:
        confidence = min(confidence, assumptions.low_confidence_threshold - 0.01)
    return CollectionExpectation(
        invoice_id=receivable.invoice_id,
        customer_id=receivable.customer_id,
        expected_date=expected.isoformat(),
        amount=money(receivable.outstanding_amount),
        confidence=round(confidence, 4),
        rationale=rationale,
        rule=rule,
        low_confidence=confidence < assumptions.low_confidence_threshold or disputed,
        source_document_id=receivable.invoice_id,
    )


def ar_forecast_lines(as_of: str | None = None) -> list[ForecastLine]:
    """Live AR lines. Paid invoices drop out; disputed items are visible but uncommitted."""
    assumptions = load_assumptions()
    from ar.schedule import unapplied_received_by_customer
    from scheduling.cash import load_cash_position

    cash = load_cash_position()
    as_of_date = as_of or cash.as_of_date
    remaining = dict(unapplied_received_by_customer(as_of_date, cash.as_of_date))
    receivables = sorted(load_receivables(), key=lambda item: (item.due_date, item.invoice_id))
    lines: list[ForecastLine] = []
    for receivable in receivables:
        expectation = expected_collection(receivable, assumptions)
        if expectation is None:
            continue
        amount = money(expectation.amount)
        disputed = bool(getattr(receivable, "disputed", False))
        take = remaining.get(receivable.customer_id, 0)
        haircut_note = ""
        if take > 0 and not disputed:
            reduced = money(min(amount, take))
            amount = money(amount - reduced)
            remaining[receivable.customer_id] = money(take - reduced)
            if reduced:
                haircut_note = (
                    f"Unapplied received cash of ${reduced:,.2f} already in the bank "
                    "for this customer"
                )
        if amount <= 0:
            continue
        rationale = expectation.rationale
        if haircut_note:
            rationale = f"{rationale}; {haircut_note}"
        evidence = [
            f"receivable:{receivable.invoice_id}",
            f"customer:{receivable.customer_id}",
            f"rule:{expectation.rule}",
            f"due:{receivable.due_date}",
        ]
        if receivable.promised_pay_date:
            evidence.append(f"promise:{receivable.promised_pay_date}")
        if disputed:
            evidence.append("disputed:true")
        if haircut_note:
            evidence.append("haircut:unapplied_received")
        lines.append(
            ForecastLine(
                line_id=f"FL-AR-{receivable.invoice_id}",
                source_type="receivable",
                source_id=receivable.invoice_id,
                expected_date=expectation.expected_date,
                amount=amount,
                confidence=expectation.confidence,
                rationale=rationale,
                customer=receivable.customer_name or receivable.customer_id,
                committed=not disputed,
                source_workflow="ar",
                evidence_refs=evidence,
            )
        )
    return lines


def _pool_invoice_ids() -> list[str]:
    from scheduling.pool import load_pool

    return [row["invoice_id"] for row in load_pool()]


def ap_forecast_lines(*, use_pool: bool = True) -> list[ForecastLine]:
    """Approved AP invoices become outflows. Held invoices are not committed."""
    from scheduling.pool import load_pool

    assumptions = load_assumptions()
    ids = _pool_invoice_ids() if use_pool else []
    decisions = load_ap_decisions()
    decisions.update(_ap_overrides)
    if not ids:
        ids = [item.invoice_id for item in decisions.values() if item.approval_state != "unapproved"]
        if not ids:
            ids = [row["invoice_id"] for row in load_pool()]
    seen: set[str] = set()
    lines: list[ForecastLine] = []
    for invoice_id in ids:
        if invoice_id in seen:
            continue
        seen.add(invoice_id)
        invoice = load_invoice(invoice_id)
        if invoice is None:
            continue
        decision = decisions.get(invoice_id)
        hold = bool(decision and decision.hold)
        pay_date = (decision.scheduled_pay_date if decision and decision.scheduled_pay_date else invoice.due_date)
        reason = (
            decision.reason
            if decision and decision.reason
            else (
                f"Approved AP invoice due {invoice.due_date}"
                if not hold
                else "Invoice is on hold and is not a committed payment"
            )
        )
        if hold:
            reason = decision.reason or "Invoice is on hold and is not a committed payment"
        lines.append(
            ForecastLine(
                line_id=f"FL-AP-{invoice_id}",
                source_type="invoice",
                source_id=invoice_id,
                expected_date=pay_date,
                amount=money(-abs(invoice.amount)),
                confidence=0.2 if hold else 0.95,
                rationale=reason,
                vendor=invoice.vendor,
                hold=hold,
                committed=not hold,
                source_workflow="ap",
                evidence_refs=[
                    f"invoice:{invoice_id}",
                    f"ap:{'hold' if hold else 'approved'}",
                    f"due:{invoice.due_date}",
                ],
            )
        )
    # Include overlay-only invoices that are approved but not yet in the pool.
    for invoice_id, decision in decisions.items():
        if invoice_id in seen:
            continue
        invoice = load_invoice(invoice_id)
        if invoice is None:
            continue
        hold = decision.hold
        lines.append(
            ForecastLine(
                line_id=f"FL-AP-{invoice_id}",
                source_type="invoice",
                source_id=invoice_id,
                expected_date=decision.scheduled_pay_date or invoice.due_date,
                amount=money(-abs(invoice.amount)),
                confidence=0.2 if hold else 0.95,
                rationale=decision.reason or "AP overlay",
                vendor=invoice.vendor,
                hold=hold,
                committed=not hold,
                source_workflow="ap",
                evidence_refs=[f"invoice:{invoice_id}", "ap:overlay"],
            )
        )
        seen.add(invoice_id)
    _ = assumptions
    return lines


def payroll_forecast_lines() -> list[ForecastLine]:
    lines = []
    for item in load_payroll():
        lines.append(
            ForecastLine(
                line_id=f"FL-PR-{item.schedule_id}",
                source_type="payroll",
                source_id=item.schedule_id,
                expected_date=item.pay_date,
                amount=money(-abs(item.expected_amount)),
                confidence=item.confidence,
                rationale=item.description or f"Payroll scheduled {item.pay_date}",
                committed=True,
                source_workflow="payroll",
                evidence_refs=[f"payroll:{item.schedule_id}", f"pay_date:{item.pay_date}"],
            )
        )
    return lines
