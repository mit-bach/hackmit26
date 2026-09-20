"""Collections candidate generation and hard policy. Agents choose tone, not eligibility."""

from __future__ import annotations

from accrual.estimation import money
from ar.aging import aging_bucket, days_past_due, derive_status, parse_date
from ar.drain import customer_has_unapplied_cash
from ar.models import (
    CollectionAction,
    CollectionDecision,
    CollectionFacts,
    Customer,
    CustomerInvoice,
)
from ar.store import all_customers, get_customer, open_invoices, precedents

WRITEOFF_ACTIONS = {"REQUEST_INTERNAL_REVIEW"}

DEFAULT_COOLDOWN_DAYS = 7
SEND_ACTIONS = {
    "SEND_GENTLE_REMINDER",
    "SEND_OVERDUE_REMINDER",
    "SEND_FINAL_NOTICE",
}


def _days_since(value: str | None, as_of: str) -> int | None:
    if not value:
        return None
    return (parse_date(as_of) - parse_date(value[:10])).days


def build_collection_facts(
    invoice: CustomerInvoice,
    as_of: str,
    *,
    customer: Customer | None = None,
    cooldown_days: int = DEFAULT_COOLDOWN_DAYS,
) -> CollectionFacts:
    customer = customer or get_customer(invoice.customer_id)
    dpd = days_past_due(invoice.due_date, as_of)
    days_since = _days_since(invoice.last_collection_contact, as_of)
    cooldown = days_since is not None and days_since < cooldown_days
    promise_open = bool(
        invoice.promised_pay_date and parse_date(invoice.promised_pay_date) >= parse_date(as_of)
    )
    blocked: list[str] = []
    facts: list[str] = [
        f"Outstanding {money(invoice.outstanding_amount)} of original {money(invoice.original_amount)}",
        f"{dpd} days past due as of {as_of}",
        f"Reminders already sent: {invoice.reminder_count}",
    ]
    if invoice.dispute_status == "OPEN":
        blocked.append("automated_demand")
        facts.append(f"Open dispute: {invoice.dispute_reason or 'unspecified'}")
    if money(invoice.outstanding_amount) <= 0 or derive_status(invoice, as_of) == "PAID":
        blocked.append("any_collection")
        facts.append("Invoice is paid")
    if cooldown:
        blocked.append("duplicate_reminder")
        facts.append(f"Last contact {invoice.last_collection_contact} ({days_since} days ago)")
    if promise_open:
        blocked.append("premature_chase")
        facts.append(f"Customer promised to pay on {invoice.promised_pay_date}")
    if money(invoice.outstanding_amount) < money(invoice.original_amount):
        facts.append("Partial payment already received; remaining balance is the collectible amount")
    if customer:
        facts.append(
            f"Payment history: {customer.payment_behavior}, "
            f"on-time {customer.on_time_rate:.0%}, avg late {customer.average_days_late} days"
        )
        if customer.risk_flag:
            facts.append(f"Risk flag: {customer.risk_flag}")
        if customer.strategic:
            facts.append("Strategic customer")

    if invoice.dispute_status == "OPEN":
        priority = "review"
    elif dpd >= 90 or invoice.reminder_count >= 3:
        priority = "critical"
    elif dpd >= 61 or invoice.reminder_count >= 2:
        priority = "high"
    elif dpd >= 31:
        priority = "medium"
    elif dpd > 0:
        priority = "low"
    else:
        priority = "none"

    return CollectionFacts(
        invoice_id=invoice.invoice_id,
        customer_id=invoice.customer_id,
        customer_name=invoice.customer_name,
        outstanding_amount=money(invoice.outstanding_amount),
        original_amount=money(invoice.original_amount),
        due_date=invoice.due_date,
        days_past_due=dpd,
        aging_bucket=aging_bucket(dpd),
        invoice_status=derive_status(invoice, as_of),
        dispute_status=invoice.dispute_status,
        dispute_reason=invoice.dispute_reason,
        collection_status=invoice.collection_status,
        reminder_count=invoice.reminder_count,
        last_collection_contact=invoice.last_collection_contact,
        days_since_contact=days_since,
        promised_pay_date=invoice.promised_pay_date,
        promise_still_open=promise_open,
        on_time_rate=customer.on_time_rate if customer else 0,
        average_days_late=customer.average_days_late if customer else 0,
        payment_behavior=customer.payment_behavior if customer else "",
        strategic=bool(customer and customer.strategic),
        risk_flag=customer.risk_flag if customer else "",
        cooldown_active=cooldown,
        suggested_priority=priority,
        blocked_actions=blocked,
        facts=facts,
    )


def collection_candidates(
    as_of: str,
    invoices: list[CustomerInvoice] | None = None,
    *,
    cooldown_days: int = DEFAULT_COOLDOWN_DAYS,
) -> list[CollectionFacts]:
    rows = invoices if invoices is not None else open_invoices()
    customers = {item.customer_id: item for item in all_customers()}
    facts = [
        build_collection_facts(
            invoice,
            as_of,
            customer=customers.get(invoice.customer_id),
            cooldown_days=cooldown_days,
        )
        for invoice in rows
    ]
    return [item for item in facts if item.days_past_due > 0 or item.dispute_status == "OPEN"]


def _draft_message(facts: CollectionFacts, action: CollectionAction) -> str | None:
    if action not in SEND_ACTIONS:
        return None
    tone = {
        "SEND_GENTLE_REMINDER": (
            "This is a friendly reminder that the balance below recently came due."
        ),
        "SEND_OVERDUE_REMINDER": (
            "This invoice is now overdue. Please arrange payment of the outstanding balance."
        ),
        "SEND_FINAL_NOTICE": (
            "This is a final notice before the account is escalated internally for collection review."
        ),
    }[action]
    return (
        f"Dear {facts.customer_name},\n\n"
        f"{tone}\n\n"
        f"Invoice: {facts.invoice_id}\n"
        f"Due date: {facts.due_date}\n"
        f"Outstanding balance: ${facts.outstanding_amount:,.2f}\n"
        f"Days past due: {facts.days_past_due}\n\n"
        "Please remit the current outstanding balance, not any prior original amount.\n\n"
        "Office of the CFO\nAccounts Receivable"
    )


def policy_collection_decision(facts: CollectionFacts) -> CollectionDecision:
    """Deterministic fallback used by demos and tests. Agents may choose a different valid action."""
    policy_checks: list[str] = []
    used = list(facts.facts)
    if "any_collection" in facts.blocked_actions or facts.invoice_status == "PAID":
        policy_checks.append("Paid invoices cannot be collected")
        return CollectionDecision(
            invoice_id=facts.invoice_id,
            customer_id=facts.customer_id,
            customer_name=facts.customer_name,
            action="NO_ACTION",
            outstanding_amount=facts.outstanding_amount,
            days_past_due=facts.days_past_due,
            reminder_count=facts.reminder_count,
            reason="Invoice is paid; collection contact is blocked.",
            evidence_used=used,
            confidence=1.0,
            human_approval_required=False,
            policy_checks=policy_checks,
        )
    if facts.dispute_status == "OPEN":
        policy_checks.append("Disputed invoices cannot receive automated payment demands")
        return CollectionDecision(
            invoice_id=facts.invoice_id,
            customer_id=facts.customer_id,
            customer_name=facts.customer_name,
            action="ESCALATE_DISPUTE",
            outstanding_amount=facts.outstanding_amount,
            days_past_due=facts.days_past_due,
            reminder_count=facts.reminder_count,
            reason="Open billing dispute; do not send an automated collection demand.",
            evidence_used=used,
            confidence=0.93,
            human_approval_required=True,
            policy_checks=policy_checks,
        )
    if facts.promise_still_open:
        policy_checks.append("Open payment promise blocks a new chase")
        return CollectionDecision(
            invoice_id=facts.invoice_id,
            customer_id=facts.customer_id,
            customer_name=facts.customer_name,
            action="HOLD_CONTACT",
            outstanding_amount=facts.outstanding_amount,
            days_past_due=facts.days_past_due,
            reminder_count=facts.reminder_count,
            reason=f"Customer promised to pay on {facts.promised_pay_date}; do not send another message today.",
            evidence_used=used,
            confidence=0.9,
            policy_checks=policy_checks,
        )
    if facts.cooldown_active:
        policy_checks.append("Cooldown prevents duplicate reminders")
        return CollectionDecision(
            invoice_id=facts.invoice_id,
            customer_id=facts.customer_id,
            customer_name=facts.customer_name,
            action="HOLD_CONTACT",
            outstanding_amount=facts.outstanding_amount,
            days_past_due=facts.days_past_due,
            reminder_count=facts.reminder_count,
            reason="A reminder was sent inside the cooldown window.",
            evidence_used=used,
            confidence=0.91,
            policy_checks=policy_checks,
        )
    if facts.days_past_due <= 0:
        return CollectionDecision(
            invoice_id=facts.invoice_id,
            customer_id=facts.customer_id,
            customer_name=facts.customer_name,
            action="NO_ACTION",
            outstanding_amount=facts.outstanding_amount,
            days_past_due=facts.days_past_due,
            reminder_count=facts.reminder_count,
            reason="Invoice is not past due.",
            evidence_used=used,
            confidence=1.0,
            policy_checks=policy_checks,
        )

    if facts.days_past_due >= 90 and facts.reminder_count >= 2:
        action: CollectionAction = "SEND_FINAL_NOTICE"
        reason = "Invoice is 90+ days overdue after multiple unanswered reminders."
        human = True
        confidence = 0.88
    elif facts.days_past_due >= 61:
        action = "SEND_FINAL_NOTICE" if facts.reminder_count >= 2 else "SEND_OVERDUE_REMINDER"
        reason = "Invoice is 61–90 days overdue."
        human = action == "SEND_FINAL_NOTICE"
        confidence = 0.84
    elif facts.days_past_due >= 31:
        action = "SEND_OVERDUE_REMINDER"
        reason = "Invoice is materially overdue, no dispute, no recent payment promise."
        human = False
        confidence = 0.86
    elif facts.on_time_rate >= 0.9 and facts.reminder_count == 0:
        action = "SEND_GENTLE_REMINDER"
        reason = "Invoice is only a few days late and the customer normally pays on time."
        human = False
        confidence = 0.82
    else:
        action = "SEND_OVERDUE_REMINDER" if facts.days_past_due > 10 else "SEND_GENTLE_REMINDER"
        reason = "Invoice is past due with no dispute or open promise."
        human = False
        confidence = 0.8

    if facts.invoice_status == "PARTIALLY_PAID":
        policy_checks.append("Message must use outstanding balance, not original amount")
        reason += f" Remaining balance is ${facts.outstanding_amount:,.2f}."

    return CollectionDecision(
        invoice_id=facts.invoice_id,
        customer_id=facts.customer_id,
        customer_name=facts.customer_name,
        action=action,
        outstanding_amount=facts.outstanding_amount,
        days_past_due=facts.days_past_due,
        reminder_count=facts.reminder_count,
        reason=reason,
        evidence_used=used,
        confidence=confidence,
        human_approval_required=human,
        draft_message=_draft_message(facts, action),
        policy_checks=policy_checks,
        precedent_used=[item.precedent_id for item in precedents(facts.customer_id)],
        precedent_affected=False,
    )


def enforce_collection_decision(facts: CollectionFacts, decision: CollectionDecision) -> CollectionDecision:
    """Reject or rewrite only when a hard rule is violated. Do not invent a stronger chase."""
    checks = list(decision.policy_checks)
    action = decision.action
    message = decision.draft_message
    human = decision.human_approval_required
    reason = decision.reason

    if facts.invoice_status == "PAID" or money(facts.outstanding_amount) <= 0:
        checks.append("Blocked collection on paid invoice")
        action = "NO_ACTION"
        message = None
        human = False
        reason = "Paid invoices cannot receive collection messages."
    elif customer_has_unapplied_cash(facts.customer_id) and action in SEND_ACTIONS:
        checks.append("Blocked chase while unapplied cash may belong to this customer")
        action = "HOLD_CONTACT"
        message = None
        human = False
        reason = (
            "Unapplied cash may belong to this customer. Handle apply first. "
            "Do not invent that the invoice is unpaid."
        )
    elif facts.dispute_status == "OPEN" and action in SEND_ACTIONS:
        checks.append("Blocked automated demand on disputed invoice")
        action = "ESCALATE_DISPUTE"
        message = None
        human = True
        reason = "Disputed invoices cannot receive automated collection demands."
    elif facts.cooldown_active and action in SEND_ACTIONS:
        checks.append("Blocked duplicate reminder inside cooldown")
        action = "HOLD_CONTACT"
        message = None
        human = False
        reason = "Cooldown prevents another customer-facing reminder."
    elif facts.promise_still_open and action in SEND_ACTIONS:
        checks.append("Blocked chase while promise to pay is still open")
        action = "HOLD_CONTACT"
        message = None
        human = False
        reason = "An open payment promise blocks another chase."

    if action in SEND_ACTIONS:
        expected = f"${facts.outstanding_amount:,.2f}"
        if not message or expected not in message:
            checks.append("Draft must cite the current outstanding balance")
            message = _draft_message(facts, action)
        if (
            facts.outstanding_amount != facts.original_amount
            and message
            and f"${facts.original_amount:,.2f}" in message
        ):
            checks.append("Draft replaced; it demanded the original amount after a partial payment")
            message = _draft_message(facts, action)
        if action == "SEND_FINAL_NOTICE":
            human = True
    elif action not in {"REQUEST_INTERNAL_REVIEW", "ESCALATE_DISPUTE"}:
        message = None

    return decision.model_copy(
        update={
            "action": action,
            "draft_message": message,
            "human_approval_required": human,
            "reason": reason,
            "outstanding_amount": facts.outstanding_amount,
            "policy_checks": checks,
            "invoice_id": facts.invoice_id,
            "customer_id": facts.customer_id,
            "customer_name": facts.customer_name,
        }
    )
