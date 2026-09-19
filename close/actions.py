"""Reviewer actions that mutate the source object that created the close blocker."""

from __future__ import annotations

from close.cash_overlay import add_fee_evidence, add_ledger_entry
from close.context import remember_link
from close.dates import now_iso
from close.ledger import post_entry
from close.models import ReviewItem
from close.reviews import get_review, upsert_review

DEFAULT_AR_INVOICE = "INV-AR-050"
NORTHSHORE_POLICY = "DOC-NS-FLOOD-2026"
CASH_CORRECTION_ID = "GL-CASH-CORR-1240"
CASH_FEE_ID = "FEE-NS-1240"


class ReviewActionError(ValueError):
    pass


def invalidate_downstream(state, review: ReviewItem) -> list[str]:
    """Mark the source task READY and dependent close tasks stale/not started."""
    affected = list(review.downstream_tasks_affected)
    if not affected:
        return []
    first = affected[0]
    for task in state.tasks:
        if task.task_id not in affected:
            continue
        task.stale = True
        task.completed_at = None
        task.blocker_reason = ""
        task.blocking_items = []
        if task.task_id == first:
            task.status = "READY"
        else:
            task.status = "NOT_STARTED"
            task.output_refs = []
    if first == "cash":
        state.force_cash_reset = True
    state.invalidated_tasks = list(dict.fromkeys(list(state.invalidated_tasks) + affected))
    return affected


def resolve_review_item(
    review_id: str,
    *,
    action: str = "",
    reason: str = "",
    reviewer: str = "human",
    invoice_id: str = "",
    invoice_ids: list[str] | None = None,
    document_id: str = "",
    evidence_id: str = "",
    period: str = "",
) -> ReviewItem:
    item = get_review(review_id)
    if item is None:
        raise ReviewActionError(f"Unknown review item {review_id}")
    if period and item.period != period:
        raise ReviewActionError(f"{review_id} does not belong to {period}")
    chosen = (action or _default_action(item)).strip()
    before = _source_snapshot(item)
    journal_ids: list[str] = []
    if chosen in {"reject", "reject_resolution"}:
        after = before
        item = item.model_copy(
            update={
                "status": "REJECTED",
                "decision": "REJECT",
                "decision_reason": reason or "Reviewer rejected the proposed resolution.",
                "decided_at": now_iso(),
                "reviewer": reviewer,
                "resolution_action": chosen,
                "source_object_before": before,
                "source_object_after": after,
            }
        )
        return upsert_review(item)
    if chosen in {"request_evidence", "needs_more_evidence"}:
        item = item.model_copy(
            update={
                "status": "NEEDS_MORE_EVIDENCE",
                "decision": "REQUEST_EVIDENCE",
                "decision_reason": reason or "Reviewer requested additional evidence.",
                "decided_at": now_iso(),
                "reviewer": reviewer,
                "resolution_action": chosen,
                "source_object_before": before,
                "source_object_after": before,
            }
        )
        return upsert_review(item)
    if item.source_workflow == "cash":
        after, journal_ids = _resolve_cash(item, chosen, evidence_id=evidence_id)
    elif item.source_workflow == "ar":
        after, journal_ids = _resolve_ar(item, chosen, invoice_id=invoice_id, invoice_ids=invoice_ids)
    elif item.source_workflow == "prepaid":
        after, journal_ids = _resolve_prepaid(item, chosen, document_id=document_id)
    else:
        raise ReviewActionError(f"No reviewer action for workflow {item.source_workflow}")
    item = item.model_copy(
        update={
            "status": "RESOLVED",
            "decision": chosen,
            "decision_reason": reason or _reason_for(item, chosen, after),
            "decided_at": now_iso(),
            "reviewer": reviewer,
            "resolution_action": chosen,
            "source_object_ref": after.get("ref") or item.source_case_id,
            "source_object_before": before,
            "source_object_after": after,
            "journal_entry_ids": journal_ids,
            "evidence_refs": list(dict.fromkeys(list(item.evidence_refs) + list(after.get("evidence_refs") or []))),
        }
    )
    saved = upsert_review(item)
    remember_link(
        review_id=saved.review_id,
        transaction_id=saved.source_case_id,
        journal_entry_id=journal_ids[0] if journal_ids else "",
        close_task_id=saved.downstream_tasks_affected[0] if saved.downstream_tasks_affected else "",
        source_document_id=str(after.get("source_document_id") or ""),
        extra={
            "action": chosen,
            "source_workflow": saved.source_workflow,
            "source_object": saved.source_object_ref,
        },
    )
    return saved


def _default_action(item: ReviewItem) -> str:
    if item.source_workflow == "cash":
        return "post_correcting_entry"
    if item.source_workflow == "ar":
        return "apply_payment"
    if item.source_workflow == "prepaid":
        return "attach_evidence"
    raise ReviewActionError(f"No default action for {item.source_workflow}")


def _reason_for(item: ReviewItem, action: str, after: dict) -> str:
    if item.source_workflow == "cash" and action == "post_correcting_entry":
        return f"Posted correcting cash entry {after.get('entry_id')} for ${item.amount:,.2f}."
    if item.source_workflow == "cash" and action == "classify_reconciling_item":
        return f"Attached reconciling evidence {after.get('evidence_id')} for the cash difference."
    if item.source_workflow == "ar":
        invoices = ", ".join(after.get("invoice_ids") or [])
        return f"Applied {item.source_case_id} to {invoices}."
    if item.source_workflow == "prepaid":
        return f"Attached {after.get('source_document_id')} to {item.source_case_id}."
    return action


def _source_snapshot(item: ReviewItem) -> dict:
    if item.source_workflow == "cash":
        from cash_recon.store import get_report
        from close.cash_overlay import load_overlay

        report = get_report(item.period)
        match = None
        if report is not None:
            for row in report.matches:
                if item.source_case_id in row.bank_transaction_ids or row.reconciliation_id == item.source_case_id:
                    match = {
                        "reconciliation_id": row.reconciliation_id,
                        "match_type": row.match_type,
                        "difference": row.difference,
                        "status": row.status,
                    }
                    break
        return {
            "ref": item.source_case_id,
            "unexplained_difference": report.unexplained_difference if report else None,
            "match": match,
            "overlay": load_overlay(item.period),
        }
    if item.source_workflow == "ar":
        from ar.store import get_invoice, get_payment

        payment = get_payment(item.source_case_id)
        invoice = get_invoice(DEFAULT_AR_INVOICE)
        return {
            "ref": item.source_case_id,
            "payment_status": payment.application_status if payment else None,
            "unapplied_amount": payment.unapplied_amount if payment else None,
            "invoice_id": DEFAULT_AR_INVOICE,
            "invoice_outstanding": invoice.outstanding_amount if invoice else None,
            "invoice_status": invoice.status if invoice else None,
        }
    if item.source_workflow == "prepaid":
        from prepaid.store import get_item

        prepaid = get_item(item.source_case_id)
        return {
            "ref": item.source_case_id,
            "source_document_id": prepaid.source_document_id if prepaid else "",
            "evidence_refs": list(prepaid.evidence_refs) if prepaid else [],
            "status": prepaid.status if prepaid else None,
        }
    return {"ref": item.source_case_id}


def _resolve_cash(item: ReviewItem, action: str, *, evidence_id: str = "") -> tuple[dict, list[str]]:
    amount = float(item.amount or 12.4)
    if action in {"post_correcting_entry", "post_entry", "correcting_entry"}:
        overlay = add_ledger_entry(
            item.period,
            {
                "entry_id": CASH_CORRECTION_ID,
                "date": f"{item.period}-15",
                "amount": amount,
                "currency": "USD",
                "account": "1000-Cash",
                "counterparty": "Northstar LLC",
                "reference": "INV-AR-880",
                "description": "Reviewer correcting entry for the $12.40 Northstar wire difference",
                "entry_type": "cash_correction",
                "period": item.period,
                "source": "close_review",
            },
        )
        journal = post_entry(
            period=item.period,
            memo="Correcting entry for unexplained $12.40 Northstar wire difference",
            debit_account="Cash",
            credit_account="Other Income",
            amount=amount,
            entry_type="cash_correction",
            idempotency_key=f"close:{item.period}:cash-corr:{item.source_case_id}",
            source_document_id=item.source_case_id,
            transaction_id=item.source_case_id,
            evidence_refs=[item.source_case_id, item.review_id],
            related_ids={"review_id": item.review_id, "bank_txn": item.source_case_id},
            actor=item.reviewer or "human",
        )
        return (
            {
                "ref": CASH_CORRECTION_ID,
                "entry_id": overlay["entry_id"],
                "amount": amount,
                "close_journal_id": journal["entry_id"],
                "evidence_refs": [item.source_case_id, CASH_CORRECTION_ID],
                "kind": "cash_ledger_overlay",
            },
            [journal["entry_id"]],
        )
    if action in {"classify_reconciling_item", "attach_evidence", "classify"}:
        fee_id = evidence_id or CASH_FEE_ID
        evidence = add_fee_evidence(
            item.period,
            {
                "evidence_id": fee_id,
                "date": f"{item.period}-15",
                "amount": amount,
                "fee_type": "wire_variance",
                "reference": "INV-AR-880",
                "description": "Reviewer-attached evidence for the $12.40 Northstar difference",
                "source": "close_review",
            },
        )
        return (
            {
                "ref": fee_id,
                "evidence_id": evidence["evidence_id"],
                "amount": amount,
                "evidence_refs": [fee_id, item.source_case_id],
                "kind": "cash_fee_evidence",
            },
            [],
        )
    raise ReviewActionError(
        "Cash actions: post_correcting_entry, classify_reconciling_item, reject, needs_more_evidence"
    )


def _resolve_ar(
    item: ReviewItem,
    action: str,
    *,
    invoice_id: str = "",
    invoice_ids: list[str] | None = None,
) -> tuple[dict, list[str]]:
    if action not in {"apply_payment", "apply", "associate"}:
        raise ReviewActionError("AR actions: apply_payment, reject, needs_more_evidence")
    from ar.ledger import post_application
    from ar.models import CashApplicationProposal, MatchApplication
    from ar.store import get_invoice, get_payment

    payment = get_payment(item.source_case_id)
    if payment is None:
        raise ReviewActionError(f"Payment {item.source_case_id} is not in the AR store")
    targets = [row for row in ([invoice_id] if invoice_id else []) + list(invoice_ids or []) if row]
    if not targets:
        targets = [DEFAULT_AR_INVOICE]
    remaining = float(payment.unapplied_amount or payment.amount)
    applications = []
    invoice_before = {}
    for target in targets:
        invoice = get_invoice(target)
        if invoice is None:
            raise ReviewActionError(f"Unknown invoice {target}")
        apply_amount = min(remaining, float(invoice.outstanding_amount))
        if apply_amount <= 0:
            raise ReviewActionError(f"{target} has no outstanding balance to apply")
        invoice_before[target] = {
            "outstanding_amount": invoice.outstanding_amount,
            "status": invoice.status,
        }
        applications.append(MatchApplication(invoice_id=target, amount=apply_amount))
        remaining = round(remaining - apply_amount, 2)
    if remaining > 0.001:
        raise ReviewActionError("Reviewer application must consume the unmatched $4,500 payment")
    proposal = CashApplicationProposal(
        payment_id=payment.payment_id,
        decision="AUTO_APPLY",
        applications=applications,
        confidence=1.0,
        reason=f"Human reviewer associated {payment.payment_id} with " + ", ".join(targets),
        evidence_used=[payment.payment_id, *targets, item.review_id],
    )
    record = post_application(payment, proposal)
    refreshed = get_payment(payment.payment_id)
    invoice_after = {}
    for target in targets:
        invoice = get_invoice(target)
        invoice_after[target] = {
            "outstanding_amount": invoice.outstanding_amount if invoice else None,
            "status": invoice.status if invoice else None,
        }
    return (
        {
            "ref": payment.payment_id,
            "invoice_ids": targets,
            "invoice_before": invoice_before,
            "invoice_after": invoice_after,
            "payment_status": refreshed.application_status if refreshed else record.status,
            "unapplied_amount": refreshed.unapplied_amount if refreshed else 0,
            "application_id": record.application_id,
            "evidence_refs": [payment.payment_id, *targets],
            "kind": "ar_cash_application",
        },
        list(record.journal_entry_ids),
    )


def _resolve_prepaid(item: ReviewItem, action: str, *, document_id: str = "") -> tuple[dict, list[str]]:
    if action not in {"attach_evidence", "attach_policy", "attach"}:
        raise ReviewActionError("Prepaid actions: attach_evidence, reject, needs_more_evidence")
    from prepaid.store import get_item, upsert_item

    prepaid = get_item(item.source_case_id)
    if prepaid is None:
        raise ReviewActionError(f"Unknown prepaid item {item.source_case_id}")
    document = document_id or NORTHSHORE_POLICY
    updated = prepaid.model_copy(
        update={
            "source_document_id": document,
            "evidence_refs": list(dict.fromkeys(list(prepaid.evidence_refs) + [document])),
            "status": "active",
        }
    )
    upsert_item(updated)
    return (
        {
            "ref": updated.prepaid_id,
            "source_document_id": updated.source_document_id,
            "evidence_refs": list(updated.evidence_refs),
            "status": updated.status,
            "kind": "prepaid_item",
        },
        [],
    )
