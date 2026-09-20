"""Persisted cash-application packets. Queue owner is ctl-cash, not a human Operator."""

from __future__ import annotations

from datetime import datetime, timezone

from accrual.estimation import money
from ar.cash import generate_cash_candidates, validate_proposal
from ar.ledger import post_application, record_human_application, record_verifier_application
from ar.models import (
    CashApplicationProposal,
    CashApplyTrace,
    CashReviewItem,
    CustomerPayment,
    MatchApplication,
)
from ar.store import (
    add_event,
    add_review,
    get_payment,
    get_review,
    next_id,
    open_reviews,
    resolve_payment_id,
    reviews,
    save_payment,
    save_review,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def enqueue_review(trace: CashApplyTrace) -> CashReviewItem:
    """Create or return the open Verifier packet for a HUMAN_REVIEW payment."""
    from ar.handles import apply_verifier_handle

    existing = get_review(trace.payment_id)
    if existing and existing.status == "OPEN":
        updates: dict = {}
        if trace.trace_path and not existing.trace_path:
            updates["trace_path"] = trace.trace_path
        if not existing.handle_path:
            handle_path, packet_path = apply_verifier_handle(trace)
            updates["handle_path"] = str(handle_path)
            updates["packet_path"] = str(packet_path)
        if updates:
            existing = existing.model_copy(update=updates)
            save_review(existing)
        return existing
    proposed = list(trace.preparer.applications or trace.final.applications)
    handle_path, packet_path = apply_verifier_handle(trace)
    item = CashReviewItem(
        review_id=next_id("AR-REV", [row.review_id for row in reviews()]),
        payment_id=trace.payment_id,
        customer_id=trace.facts.identified_customer_id,
        customer_name=trace.facts.identified_customer_name,
        payment_amount=money(trace.payment.amount),
        payment_date=trace.payment.payment_date,
        remittance_text=trace.payment.remittance_text,
        invoice_reference=trace.payment.invoice_reference,
        bank_reference=trace.payment.bank_reference,
        candidates=list(trace.facts.candidates),
        proposed_applications=proposed,
        agent_recommendation=trace.preparer,
        reviewer_recommendation=trace.reviewer,
        ambiguities=list(trace.final.ambiguities or trace.preparer.ambiguities),
        confidence=trace.final.confidence,
        trace_path=trace.trace_path,
        status="OPEN",
        created_at=_now(),
        queue_owner="ctl-cash",
        queue_profile="review-apply",
        handle_path=str(handle_path),
        packet_path=str(packet_path),
        human_queue=False,
    )
    add_review(item)
    add_event(
        "cash_review_opened",
        f"Opened ctl-cash packet {item.review_id} for {item.payment_id}",
        payment_id=item.payment_id,
        details={
            "review_id": item.review_id,
            "ambiguities": item.ambiguities,
            "queue_owner": item.queue_owner,
            "handle_path": item.handle_path,
            "human_queue": False,
        },
    )
    return item


def require_open_review(payment_id: str) -> tuple[CashReviewItem, CustomerPayment]:
    payment = get_payment(payment_id)
    if payment is None:
        raise ValueError(f"Unknown payment {resolve_payment_id(payment_id)}")
    item = get_review(payment.payment_id)
    if item is None:
        raise ValueError(f"No review item exists for {payment.payment_id}")
    if item.status != "OPEN":
        raise ValueError(f"Review {item.review_id} is already {item.status}")
    return item, payment


def _resolve(
    item: CashReviewItem,
    *,
    status: str,
    reviewer: str,
    reason: str,
    applications: list[MatchApplication],
    differed: bool,
) -> CashReviewItem:
    updated = item.model_copy(
        update={
            "status": status,
            "resolved_at": _now(),
            "resolved_by": reviewer,
            "resolution_reason": reason,
            "final_applications": applications,
            "differed_from_agent": differed,
        }
    )
    save_review(updated)
    add_event(
        "cash_review_resolved",
        f"{status} {updated.review_id} for {updated.payment_id}: {reason}",
        payment_id=updated.payment_id,
        invoice_ids=[row.invoice_id for row in applications],
        details={
            "review_id": updated.review_id,
            "status": status,
            "resolved_by": reviewer,
            "reason": reason,
            "applications": [row.model_dump() for row in applications],
            "original_ambiguities": item.ambiguities,
            "agent_decision": item.agent_recommendation.decision if item.agent_recommendation else None,
            "agent_reason": item.agent_recommendation.reason if item.agent_recommendation else None,
            "differed_from_agent": differed,
            "trace_path": item.trace_path,
        },
    )
    return updated


def approve_review(
    payment_id: str,
    *,
    reviewer: str = "ctl-cash",
    reason: str = "Approved the proposed allocation.",
) -> CashReviewItem:
    item, payment = require_open_review(payment_id)
    if not item.proposed_applications:
        raise ValueError(
            f"{payment.payment_id} has no unique proposed allocation. "
            "Use the ctl-cash packet or emergency ar-review-correct --apply INV-…:amount"
        )
    proposal = CashApplicationProposal(
        payment_id=payment.payment_id,
        decision="AUTO_APPLY",
        applications=list(item.proposed_applications),
        confidence=1.0,
        reason=reason,
        evidence_used=["human_approval", *(item.agent_recommendation.evidence_used if item.agent_recommendation else [])],
        ambiguities=item.ambiguities,
        precedent_used=item.agent_recommendation.precedent_used if item.agent_recommendation else [],
        precedent_affected=False,
    )
    validation = validate_proposal(payment, proposal)
    if not validation.passed:
        raise ValueError("Approval failed validation: " + "; ".join(validation.errors))
    post_application(payment, proposal)
    record_verifier_application(
        payment.payment_id,
        list(item.proposed_applications),
        reason,
        reviewer=reviewer,
        review_id=item.review_id,
    )
    return _resolve(
        item,
        status="APPROVED",
        reviewer=reviewer,
        reason=reason,
        applications=list(item.proposed_applications),
        differed=False,
    )


def correct_review(
    payment_id: str,
    applications: list[MatchApplication],
    reason: str,
    reviewer: str = "ctl-cash",
) -> CashReviewItem:
    item, payment = require_open_review(payment_id)
    record = record_human_application(
        payment.payment_id,
        applications,
        reason,
        reviewer=reviewer,
        review_id=item.review_id,
    )
    proposed_key = tuple(sorted((row.invoice_id, row.amount) for row in item.proposed_applications))
    final_key = tuple(sorted((row.invoice_id, row.amount) for row in record.applications))
    return _resolve(
        item,
        status="CORRECTED",
        reviewer=reviewer,
        reason=reason,
        applications=list(record.applications),
        differed=proposed_key != final_key or (item.agent_recommendation and item.agent_recommendation.decision != "AUTO_APPLY"),
    )


def reject_review(
    payment_id: str,
    reason: str,
    reviewer: str = "ctl-cash",
) -> CashReviewItem:
    item, payment = require_open_review(payment_id)
    metadata = dict(payment.metadata or {})
    metadata["unapplied_after_review"] = True
    metadata["rejected_review_id"] = item.review_id
    save_payment(
        payment.model_copy(
            update={
                "application_status": "UNMATCHED",
                "unapplied_amount": money(payment.amount),
                "metadata": metadata,
            }
        )
    )
    add_event(
        "cash_unapplied",
        f"Rejected review for {payment.payment_id}: {reason}",
        payment_id=payment.payment_id,
        details={
            "review_id": item.review_id,
            "reason": reason,
            "resolved_by": reviewer,
            "candidates": [row.model_dump() for row in item.candidates],
            "trace_path": item.trace_path,
        },
    )
    return _resolve(
        item,
        status="REJECTED",
        reviewer=reviewer,
        reason=reason,
        applications=[],
        differed=True,
    )


def parse_apply_spec(raw: str) -> MatchApplication:
    if ":" not in raw:
        raise ValueError(f"Expected INV-AR-101:10000, got {raw!r}")
    invoice_id, _, amount = raw.partition(":")
    return MatchApplication(invoice_id=invoice_id.strip().upper(), amount=float(amount))
