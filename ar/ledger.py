"""Post accepted cash applications to the AR subledger and shared journal."""

from __future__ import annotations

from datetime import datetime, timezone

from accrual.estimation import money
from ar.aging import derive_status
from ar.models import (
    ARJournalEntry,
    ARJournalLine,
    ARPrecedent,
    CashApplicationProposal,
    CashApplicationRecord,
    CustomerPayment,
    HumanCorrection,
    InvoiceBalanceChange,
    InvoiceStatus,
    MatchApplication,
)
from ar.store import (
    add_application,
    add_event,
    add_human_correction,
    add_journal,
    add_precedent,
    applications_for_payment,
    get_invoice,
    get_payment,
    journals,
    next_id,
    precedents,
    save_human_correction,
    save_invoice,
    save_payment,
)

AR_ACCOUNT = "Accounts Receivable"
CASH_ACCOUNT = "Cash"
UNAPPLIED_ACCOUNT = "Unapplied Cash"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _period(day: str) -> str:
    return day[:7]


def _write_journal(
    *,
    counterparty: str,
    amount: float,
    debit: str,
    credit: str,
    entry_type,
    memo: str,
    payment_id: str,
    invoice_ids: list[str],
    period: str,
) -> ARJournalEntry:
    amount = money(amount)
    if amount <= 0:
        raise ValueError("Journal amount must be positive.")
    entry = ARJournalEntry(
        entry_id=next_id("AR-JE", [item.entry_id for item in journals()]),
        period=period,
        counterparty=counterparty,
        memo=memo,
        debit=ARJournalLine(account=debit, amount=amount),
        credit=ARJournalLine(account=credit, amount=amount),
        entry_type=entry_type,
        related_payment_id=payment_id,
        related_invoice_ids=invoice_ids,
        created_at=_now(),
    )
    return add_journal(entry)


def apply_to_invoice(invoice_id: str, amount: float, payment_date: str) -> InvoiceBalanceChange:
    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Unknown invoice {invoice_id}")
    amount = money(amount)
    previous_outstanding = money(invoice.outstanding_amount)
    previous_status: InvoiceStatus = invoice.status
    new_outstanding = money(previous_outstanding - amount)
    if new_outstanding < 0:
        raise ValueError(f"Application would overpay {invoice_id}")
    updated = invoice.model_copy(
        update={
            "outstanding_amount": new_outstanding,
            "last_payment_date": payment_date,
            "status": derive_status(
                invoice.model_copy(update={"outstanding_amount": new_outstanding}),
                payment_date,
            ),
        }
    )
    save_invoice(updated)
    return InvoiceBalanceChange(
        invoice_id=invoice_id,
        previous_outstanding=previous_outstanding,
        applied_amount=amount,
        new_outstanding=new_outstanding,
        previous_status=previous_status,
        new_status=updated.status,
    )


def post_application(
    payment: CustomerPayment,
    proposal: CashApplicationProposal,
) -> CashApplicationRecord:
    existing = applications_for_payment(payment.payment_id)
    if existing:
        return existing[-1]

    applied = money(sum(item.amount for item in proposal.applications))
    unapplied = money(payment.amount - applied)
    changes = [
        apply_to_invoice(item.invoice_id, item.amount, payment.payment_date)
        for item in proposal.applications
    ]
    journal_ids: list[str] = []
    counterparty = payment.payer_name
    period = _period(payment.payment_date)
    if applied > 0:
        journal = _write_journal(
            counterparty=counterparty,
            amount=applied,
            debit=CASH_ACCOUNT,
            credit=AR_ACCOUNT,
            entry_type="cash_receipt",
            memo=f"Apply {payment.payment_id} to " + ", ".join(item.invoice_id for item in proposal.applications),
            payment_id=payment.payment_id,
            invoice_ids=[item.invoice_id for item in proposal.applications],
            period=period,
        )
        journal_ids.append(journal.entry_id)
    if unapplied > 0:
        journal = _write_journal(
            counterparty=counterparty,
            amount=unapplied,
            debit=CASH_ACCOUNT,
            credit=UNAPPLIED_ACCOUNT,
            entry_type="unapplied_cash",
            memo=f"Unapplied remainder of {payment.payment_id}",
            payment_id=payment.payment_id,
            invoice_ids=[],
            period=period,
        )
        journal_ids.append(journal.entry_id)

    status = "APPLIED" if unapplied <= 0 else "PARTIALLY_APPLIED"
    updated_payment = payment.model_copy(
        update={"unapplied_amount": unapplied, "application_status": status}
    )
    save_payment(updated_payment)
    record = CashApplicationRecord(
        application_id="AR-APP-000",
        payment_id=payment.payment_id,
        applications=list(proposal.applications),
        total_applied=applied,
        unapplied_amount=unapplied,
        decision="AUTO_APPLY",
        status=status,
        posted=True,
        invoice_changes=changes,
        journal_entry_ids=journal_ids,
        created_at=_now(),
        reason=proposal.reason,
    )
    # Use live application list for the next id.
    from ar.store import applications

    record = record.model_copy(
        update={"application_id": next_id("AR-APP", [item.application_id for item in applications()])}
    )
    add_application(record)
    add_event(
        "cash_applied",
        (
            f"Applied {payment.payment_id} ${applied:,.2f} to "
            + ", ".join(item.invoice_id for item in proposal.applications)
            + (f" (${unapplied:,.2f} unapplied)" if unapplied else "")
        ),
        payment_id=payment.payment_id,
        invoice_ids=[item.invoice_id for item in proposal.applications],
        details={
            "applications": [item.model_dump() for item in proposal.applications],
            "unapplied_amount": unapplied,
            "journal_entry_ids": journal_ids,
            "reason": proposal.reason,
            "evidence_used": proposal.evidence_used,
            "precedent_used": proposal.precedent_used,
            "precedent_affected": proposal.precedent_affected,
        },
    )
    return record


def mark_payment_decision(payment: CustomerPayment, proposal: CashApplicationProposal) -> CustomerPayment:
    """Record HUMAN_REVIEW / UNAPPLIED without changing invoice balances."""
    status = "HUMAN_REVIEW" if proposal.decision == "HUMAN_REVIEW" else "UNMATCHED"
    updated = payment.model_copy(
        update={
            "application_status": status,
            "unapplied_amount": money(payment.amount),
        }
    )
    save_payment(updated)
    add_event(
        "cash_held" if proposal.decision == "HUMAN_REVIEW" else "cash_unapplied",
        f"{proposal.decision} for {payment.payment_id}: {proposal.reason}",
        payment_id=payment.payment_id,
        details={
            "decision": proposal.decision,
            "ambiguities": proposal.ambiguities,
            "review_question": proposal.review_question,
            "evidence_used": proposal.evidence_used,
            "candidates_mentioned": proposal.ambiguities,
        },
    )
    return updated


def _learn_precedent(
    payment: CustomerPayment,
    applications: list[MatchApplication],
    reason: str,
    *,
    correction_id: str,
    review_id: str = "",
) -> ARPrecedent:
    ids = [item.invoice_id for item in applications]
    kind = "batch_payment" if len(applications) > 1 else "human_correction"
    summary = (
        f"{payment.payer_name} settled {len(applications)} invoices in one remittance "
        f"({', '.join(ids)}) totaling ${money(sum(item.amount for item in applications)):,.2f}."
        if len(applications) > 1
        else f"Human applied {payment.payment_id} to {ids[0] if ids else 'invoices'}: {reason}"
    )
    facts = {
        "payment_id": payment.payment_id,
        "payer_name": payment.payer_name,
        "amount": money(payment.amount),
        "applications": [item.model_dump() for item in applications],
        "invoice_ids": ids,
        "pattern": "combination" if len(applications) > 1 else "single",
        "reason": reason,
    }
    for existing in precedents(payment.customer_id or ""):
        if (
            existing.customer_id == payment.customer_id
            and existing.kind == kind
            and existing.source == "human"
        ):
            updated = existing.model_copy(
                update={
                    "support_count": existing.support_count + 1,
                    "summary": summary,
                    "facts": {**existing.facts, **facts, "prior_precedent": existing.precedent_id},
                    "source_payment_id": payment.payment_id,
                    "source_review_id": review_id or existing.source_review_id,
                }
            )
            from ar.store import load_state, save_state

            state = load_state()
            state.precedents = [
                updated if item.precedent_id == existing.precedent_id else item for item in state.precedents
            ]
            save_state()
            return updated
    precedent = ARPrecedent(
        precedent_id=f"AR-PREC-H-{correction_id}",
        customer_id=payment.customer_id,
        kind=kind,
        summary=summary,
        facts=facts,
        source="human",
        support_count=1,
        source_payment_id=payment.payment_id,
        source_review_id=review_id or None,
    )
    add_precedent(precedent)
    return precedent


def record_human_application(
    payment_id: str,
    applications: list[MatchApplication],
    reason: str,
    reviewer: str = "human",
    review_id: str = "",
) -> CashApplicationRecord:
    payment = get_payment(payment_id)
    if payment is None:
        raise ValueError(f"Unknown payment {payment_id}")
    proposal = CashApplicationProposal(
        payment_id=payment.payment_id,
        decision="AUTO_APPLY",
        applications=applications,
        confidence=1.0,
        reason=reason,
        evidence_used=["human_correction"],
        precedent_affected=True,
    )
    from ar.cash import validate_proposal

    validation = validate_proposal(payment, proposal)
    if not validation.passed:
        raise ValueError("Human application failed validation: " + "; ".join(validation.errors))
    from ar.store import human_corrections

    correction = HumanCorrection(
        correction_id=next_id("AR-HC", [item.correction_id for item in human_corrections()]),
        payment_id=payment.payment_id,
        applications=applications,
        reason=reason,
        reviewer=reviewer,
        created_at=_now(),
        posted=False,
    )
    add_human_correction(correction)
    precedent = _learn_precedent(
        payment,
        applications,
        reason,
        correction_id=correction.correction_id,
        review_id=review_id,
    )
    proposal = proposal.model_copy(update={"precedent_used": [precedent.precedent_id]})
    record = post_application(payment, proposal)
    save_human_correction(correction.model_copy(update={"posted": True}))
    return record
