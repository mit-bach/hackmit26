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
    source: str = "human",
) -> ARPrecedent:
    ids = [item.invoice_id for item in applications]
    kind = "batch_payment" if len(applications) > 1 else "human_correction"
    actor = "Verifier" if source == "verifier" else "Human"
    summary = (
        f"{payment.payer_name} settled {len(applications)} invoices in one remittance "
        f"({', '.join(ids)}) totaling ${money(sum(item.amount for item in applications)):,.2f}."
        if len(applications) > 1
        else f"{actor} applied {payment.payment_id} to {ids[0] if ids else 'invoices'}: {reason}"
    )
    facts = {
        "payment_id": payment.payment_id,
        "payer_name": payment.payer_name,
        "amount": money(payment.amount),
        "applications": [item.model_dump() for item in applications],
        "invoice_ids": ids,
        "pattern": "combination" if len(applications) > 1 else "single",
        "reason": reason,
        "queue_owner": "ctl-cash" if source == "verifier" else "emergency-cli",
    }
    for existing in precedents(payment.customer_id or ""):
        if (
            existing.customer_id == payment.customer_id
            and existing.kind == kind
            and existing.source == source
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
    prefix = "AR-PREC-V" if source == "verifier" else "AR-PREC-H"
    precedent = ARPrecedent(
        precedent_id=f"{prefix}-{correction_id}",
        customer_id=payment.customer_id,
        kind=kind,
        summary=summary,
        facts=facts,
        source=source,
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


def record_verifier_application(
    payment_id: str,
    applications: list[MatchApplication],
    reason: str,
    reviewer: str = "ctl-cash",
    review_id: str = "",
) -> ARPrecedent | None:
    """Office path: ctl-cash concurrence writes remittance habit. Not the CLI."""
    payment = get_payment(payment_id)
    if payment is None or not payment.customer_id:
        return None
    return _learn_precedent(
        payment,
        applications,
        reason,
        correction_id=review_id or payment.payment_id,
        review_id=review_id,
        source="verifier",
    )


def record_collection_contact(
    customer_id: str,
    invoice_id: str,
    action: str,
    as_of: str,
) -> ARPrecedent | None:
    """Collect Memory: this customer was contacted. Color, not an eligibility override."""
    if not customer_id:
        return None
    for existing in precedents(customer_id):
        if existing.kind == "collection_contact" and existing.source == "collect":
            updated = existing.model_copy(
                update={
                    "support_count": existing.support_count + 1,
                    "summary": (
                        f"Last Kernel-allowed contact was {action} on {invoice_id} as of {as_of}."
                    ),
                    "facts": {
                        **existing.facts,
                        "last_invoice_id": invoice_id,
                        "last_action": action,
                        "last_as_of": as_of,
                    },
                    "source_payment_id": existing.source_payment_id,
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
        precedent_id=f"AR-PREC-C-{invoice_id}",
        customer_id=customer_id,
        kind="collection_contact",
        summary=f"Kernel-allowed {action} reached the mailbox for {invoice_id} as of {as_of}.",
        facts={"invoice_id": invoice_id, "action": action, "as_of": as_of},
        source="collect",
        support_count=1,
    )
    return add_precedent(precedent)


FEE_ACCOUNT = "Stripe Processing Fees"
DISPUTE_ACCOUNT = "Chargeback Losses"


def learn_stripe_precedent(payment: CustomerPayment, invoice_ids: list[str]) -> ARPrecedent | None:
    """Record that this customer remits invoice identity through Stripe facts."""
    if not payment.customer_id or not invoice_ids:
        return None
    for existing in precedents(payment.customer_id):
        if existing.kind == "stripe_metadata" and existing.source_payment_id == payment.payment_id:
            return existing
    description = " ".join(
        part
        for part in [payment.remittance_text, payment.invoice_reference, payment.bank_reference]
        if part
    )
    precedent = ARPrecedent(
        precedent_id=f"AR-PREC-STR-{payment.payment_id}",
        customer_id=payment.customer_id,
        kind="stripe_metadata",
        summary=(
            f"{payment.payer_name} typically remits Stripe invoice references "
            f"({', '.join(invoice_ids)}) with description {description!r}."
        ),
        facts={
            "invoice_ids": invoice_ids,
            "description": description,
            "source": "stripe",
            "amount": money(payment.amount),
            "invoice_reference": payment.invoice_reference,
        },
        source="stripe",
        source_payment_id=payment.payment_id,
    )
    return add_precedent(precedent)


def post_refund(
    *,
    refund_id: str,
    amount: float,
    payment: CustomerPayment | None,
    invoice_ids: list[str],
    refund_date: str,
    memo: str,
    stripe_refund_id: str,
) -> dict:
    """Reverse previously applied cash without erasing the original payment."""
    from ar.store import events as load_events

    for event in load_events():
        if (event.details or {}).get("stripe_refund_id") == stripe_refund_id:
            return {"status": "duplicate", "event_id": event.event_id, "journal_entry_ids": []}

    amount = money(amount)
    period = _period(refund_date)
    restored: list[InvoiceBalanceChange] = []
    remaining = amount
    targets = invoice_ids or (
        [item.invoice_id for item in applications_for_payment(payment.payment_id)[-1].applications]
        if payment and applications_for_payment(payment.payment_id)
        else []
    )
    for invoice_id in targets:
        invoice = get_invoice(invoice_id)
        if invoice is None or remaining <= 0:
            continue
        applied_cap = money(invoice.original_amount - invoice.outstanding_amount)
        take = money(min(remaining, applied_cap if applied_cap > 0 else remaining))
        if take <= 0:
            continue
        previous_outstanding = money(invoice.outstanding_amount)
        previous_status = invoice.status
        updated = invoice.model_copy(
            update={
                "outstanding_amount": money(previous_outstanding + take),
                "status": derive_status(
                    invoice.model_copy(update={"outstanding_amount": money(previous_outstanding + take)}),
                    refund_date,
                ),
            }
        )
        save_invoice(updated)
        restored.append(
            InvoiceBalanceChange(
                invoice_id=invoice_id,
                previous_outstanding=previous_outstanding,
                applied_amount=money(-take),
                new_outstanding=updated.outstanding_amount,
                previous_status=previous_status,
                new_status=updated.status,
            )
        )
        remaining = money(remaining - take)

    journal = _write_journal(
        counterparty=(payment.payer_name if payment else "Stripe customer"),
        amount=amount,
        debit=AR_ACCOUNT,
        credit=CASH_ACCOUNT,
        entry_type="refund",
        memo=memo,
        payment_id=payment.payment_id if payment else refund_id,
        invoice_ids=targets,
        period=period,
    )
    event = add_event(
        "stripe_refund",
        memo,
        payment_id=payment.payment_id if payment else None,
        invoice_ids=targets,
        details={
            "stripe_refund_id": stripe_refund_id,
            "amount": amount,
            "journal_entry_ids": [journal.entry_id],
            "invoice_changes": [item.model_dump() for item in restored],
        },
    )
    return {
        "status": "processed",
        "event_id": event.event_id,
        "journal_entry_ids": [journal.entry_id],
        "invoice_changes": restored,
    }


def open_dispute(
    *,
    dispute_id: str,
    amount: float,
    fee_amount: float,
    invoice_ids: list[str],
    payment: CustomerPayment | None,
    dispute_date: str,
    reason: str,
    stripe_dispute_id: str,
) -> dict:
    from ar.store import events as load_events

    for event in load_events():
        if (event.details or {}).get("stripe_dispute_id") == stripe_dispute_id:
            return {"status": "duplicate", "event_id": event.event_id, "journal_entry_ids": []}

    amount = money(amount)
    fee_amount = money(fee_amount)
    journal_ids: list[str] = []
    period = _period(dispute_date)
    for invoice_id in invoice_ids:
        invoice = get_invoice(invoice_id)
        if invoice is None:
            continue
        save_invoice(
            invoice.model_copy(
                update={
                    "dispute_status": "OPEN",
                    "dispute_reason": reason or invoice.dispute_reason or "stripe_dispute",
                    "status": "DISPUTED",
                }
            )
        )
    if amount > 0:
        journal = _write_journal(
            counterparty=(payment.payer_name if payment else "Stripe customer"),
            amount=amount,
            debit=DISPUTE_ACCOUNT,
            credit=CASH_ACCOUNT,
            entry_type="dispute",
            memo=f"Stripe dispute {stripe_dispute_id}: {reason}",
            payment_id=payment.payment_id if payment else dispute_id,
            invoice_ids=invoice_ids,
            period=period,
        )
        journal_ids.append(journal.entry_id)
    if fee_amount > 0:
        journal = _write_journal(
            counterparty="Stripe",
            amount=fee_amount,
            debit=DISPUTE_ACCOUNT,
            credit=CASH_ACCOUNT,
            entry_type="dispute",
            memo=f"Stripe dispute fee {stripe_dispute_id}",
            payment_id=payment.payment_id if payment else dispute_id,
            invoice_ids=invoice_ids,
            period=period,
        )
        journal_ids.append(journal.entry_id)
    event = add_event(
        "stripe_dispute",
        f"Dispute {stripe_dispute_id} for ${amount:,.2f}",
        payment_id=payment.payment_id if payment else None,
        invoice_ids=invoice_ids,
        details={
            "stripe_dispute_id": stripe_dispute_id,
            "amount": amount,
            "fee_amount": fee_amount,
            "reason": reason,
            "journal_entry_ids": journal_ids,
        },
    )
    return {"status": "processed", "event_id": event.event_id, "journal_entry_ids": journal_ids}


def post_processor_fee(
    *,
    payout_id: str,
    fee_amount: float,
    fee_date: str,
    memo: str = "",
) -> dict:
    from ar.store import journals as load_journals

    fee_amount = money(abs(fee_amount))
    if fee_amount <= 0:
        return {"status": "skipped", "journal_entry_ids": []}
    for entry in load_journals():
        if entry.entry_type == "processor_fee" and payout_id in (entry.memo or ""):
            return {"status": "duplicate", "journal_entry_ids": [entry.entry_id]}
    journal = _write_journal(
        counterparty="Stripe",
        amount=fee_amount,
        debit=FEE_ACCOUNT,
        credit=CASH_ACCOUNT,
        entry_type="processor_fee",
        memo=memo or f"Stripe processor fee for payout {payout_id}",
        payment_id=payout_id,
        invoice_ids=[],
        period=_period(fee_date),
    )
    add_event(
        "stripe_fee",
        journal.memo,
        details={"payout_id": payout_id, "fee_amount": fee_amount, "journal_entry_ids": [journal.entry_id]},
    )
    return {"status": "processed", "journal_entry_ids": [journal.entry_id]}
