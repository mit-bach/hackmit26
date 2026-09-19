"""Orchestrate AR aging, collections, and cash application."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from ar.aging import build_aging_report
from ar.cash import (
    generate_cash_candidates,
    needs_reviewer,
    policy_cash_decision,
    reviewer_policy,
    validate_proposal,
)
from ar.collections import (
    collection_candidates,
    enforce_collection_decision,
    policy_collection_decision,
)
from ar.context import ar_close_snapshot
from ar.ledger import mark_payment_decision, post_application
from ar.models import (
    AgingReport,
    CashApplicationProposal,
    CashApplyTrace,
    CollectionDecision,
    CollectionMessage,
    CollectionRun,
)
from ar.store import (
    add_event,
    add_outbox,
    applications_for_payment,
    get_invoice,
    get_payment,
    next_id,
    outbox,
    reset_state,
    save_invoice,
    save_trace,
)
from skills.loader import usage_from_agent

DEFAULT_AS_OF = "2026-09-30"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dump(model) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2)


def run_aging(as_of: str = DEFAULT_AS_OF, *, persist: bool = True) -> AgingReport:
    return build_aging_report(as_of, persist=persist)


def _live_collection_decision(facts, as_of: str) -> CollectionDecision:
    from agent import run_agent
    from ar.agents import collections_agent

    return run_agent(
        collections_agent,
        (
            f"Decide the next collections action as of {as_of}.\n\n"
            "Python already computed these facts. Use them; do not recalculate:\n"
            f"{_dump(facts)}"
        ),
    )


def run_collections(
    as_of: str = DEFAULT_AS_OF,
    *,
    live: bool | None = None,
    persist: bool = True,
) -> CollectionRun:
    live = bool(os.environ.get("OPENAI_API_KEY")) if live is None else live
    started = _now()
    candidates = collection_candidates(as_of)
    decisions: list[CollectionDecision] = []
    messages: list[CollectionMessage] = []
    used_agent = False
    for facts in candidates:
        if live:
            raw = _live_collection_decision(facts, as_of)
            used_agent = True
        else:
            raw = policy_collection_decision(facts)
        decision = enforce_collection_decision(facts, raw)
        decisions.append(decision)
        if decision.action in {"SEND_GENTLE_REMINDER", "SEND_OVERDUE_REMINDER", "SEND_FINAL_NOTICE"}:
            if persist and decision.draft_message:
                invoice = get_invoice(decision.invoice_id)
                if invoice:
                    save_invoice(
                        invoice.model_copy(
                            update={
                                "last_collection_contact": as_of,
                                "reminder_count": invoice.reminder_count + 1,
                                "collection_status": (
                                    "ESCALATED"
                                    if decision.action == "SEND_FINAL_NOTICE"
                                    else "REMINDED"
                                ),
                            }
                        )
                    )
                message = CollectionMessage(
                    message_id=next_id("AR-MSG", [item.message_id for item in outbox()]),
                    invoice_id=decision.invoice_id,
                    customer_id=decision.customer_id,
                    customer_name=decision.customer_name,
                    action=decision.action,
                    outstanding_amount=decision.outstanding_amount,
                    draft_message=decision.draft_message,
                    reason=decision.reason,
                    evidence_used=decision.evidence_used,
                    confidence=decision.confidence,
                    human_approval_required=decision.human_approval_required,
                    created_at=_now(),
                    as_of_date=as_of,
                    sent=False,
                )
                add_outbox(message)
                messages.append(message)
        elif persist and decision.action in {"ESCALATE_DISPUTE", "REQUEST_INTERNAL_REVIEW"}:
            add_event(
                "collections_review",
                f"{decision.action} for {decision.invoice_id}: {decision.reason}",
                invoice_ids=[decision.invoice_id],
                details=decision.model_dump(mode="json"),
            )

    agents = []
    if used_agent:
        from ar.agents import collections_agent

        agents = [usage_from_agent(collections_agent)]
    run = CollectionRun(
        as_of_date=as_of,
        started_at=started,
        candidates=candidates,
        decisions=decisions,
        outbox=messages,
        agents=agents,
        used_agent=used_agent,
    )
    if persist:
        path = save_trace("collections", run)
        run.trace_path = str(path)
        add_event(
            "collections_run",
            f"Collections run as of {as_of}: {len(decisions)} decisions, {len(messages)} drafts",
            invoice_ids=[item.invoice_id for item in decisions],
            details={"actions": [item.action for item in decisions]},
        )
    return run


def _live_cash_proposal(facts, payment_id: str) -> CashApplicationProposal:
    from agent import run_agent
    from ar.agents import cash_application_agent

    return run_agent(
        cash_application_agent,
        (
            f"Apply cash for {payment_id}.\n\n"
            "Python already computed these candidates. Choose among them; "
            "do not invent combinations:\n"
            f"{_dump(facts)}"
        ),
    )


def _live_review(proposal: CashApplicationProposal, facts) -> object:
    from agent import run_agent
    from ar.agents import cash_reviewer_agent

    return run_agent(
        cash_reviewer_agent,
        (
            "Review this cash-application proposal.\n\n"
            f"Proposal:\n{_dump(proposal)}\n\n"
            f"Facts:\n{_dump(facts)}"
        ),
    )


def run_cash_apply(
    payment_id: str,
    *,
    as_of: str = DEFAULT_AS_OF,
    live: bool | None = None,
    persist: bool = True,
) -> CashApplyTrace:
    live = bool(os.environ.get("OPENAI_API_KEY")) if live is None else live
    payment = get_payment(payment_id)
    if payment is None:
        raise ValueError(f"Unknown payment {payment_id}")
    posted_already = applications_for_payment(payment.payment_id)
    if posted_already or payment.application_status in {"APPLIED", "PARTIALLY_APPLIED"}:
        from ar.models import ValidationResult

        record = posted_already[-1] if posted_already else None
        apps = record.applications if record else []
        trace = CashApplyTrace(
            payment_id=payment.payment_id,
            started_at=_now(),
            as_of_date=as_of,
            payment=payment,
            facts=generate_cash_candidates(payment),
            preparer=CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="AUTO_APPLY",
                applications=apps,
                confidence=1.0,
                reason="Payment already posted; refusing to apply it again.",
            ),
            validation=ValidationResult(passed=True, errors=[]),
            final=CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="AUTO_APPLY",
                applications=apps,
                confidence=1.0,
                reason="Already posted.",
            ),
            posted=True,
            record=record,
            state_changes=record.invoice_changes if record else [],
            already_posted=True,
        )
        if persist:
            path = save_trace(f"cash-{payment.payment_id}", trace)
            trace.trace_path = str(path)
        return trace

    facts = generate_cash_candidates(payment)
    used_agent = False
    if live:
        preparer = _live_cash_proposal(facts, payment.payment_id)
        used_agent = True
    else:
        preparer = policy_cash_decision(facts)

    validation = validate_proposal(payment, preparer)
    reviewer = None
    final = preparer
    if not validation.passed:
        final = CashApplicationProposal(
            payment_id=payment.payment_id,
            decision="HUMAN_REVIEW",
            applications=[],
            confidence=0.0,
            reason="Rejected invalid agent proposal: " + "; ".join(validation.errors),
            evidence_used=preparer.evidence_used,
            ambiguities=list(preparer.ambiguities) + validation.errors,
            review_question="Proposal failed invariant checks and was not posted.",
        )
    elif needs_reviewer(preparer, facts):
        reviewer = _live_review(preparer, facts) if live else reviewer_policy(preparer, facts)
        if reviewer.recommendation != "AUTO_APPLY" or not reviewer.agree_with_preparer:
            final = CashApplicationProposal(
                payment_id=payment.payment_id,
                decision="HUMAN_REVIEW",
                applications=[],
                confidence=reviewer.confidence,
                reason="; ".join(reviewer.reasons) or "Reviewer sent this payment to human review.",
                evidence_used=preparer.evidence_used,
                ambiguities=preparer.ambiguities,
                review_question=preparer.review_question or "Reviewer found an equally plausible alternative.",
                precedent_used=preparer.precedent_used,
                precedent_affected=preparer.precedent_affected,
            )

    posted = False
    record = None
    journals = []
    if persist and final.decision == "AUTO_APPLY" and validation.passed and not (
        reviewer and (reviewer.recommendation != "AUTO_APPLY" or not reviewer.agree_with_preparer)
    ):
        final_validation = validate_proposal(payment, final)
        if final_validation.passed:
            record = post_application(payment, final)
            posted = True
            from ar.store import journals as load_journals

            journals = [item for item in load_journals() if item.entry_id in record.journal_entry_ids]
        else:
            validation = final_validation
            final = final.model_copy(
                update={
                    "decision": "HUMAN_REVIEW",
                    "applications": [],
                    "reason": "Rejected invalid application: " + "; ".join(final_validation.errors),
                }
            )
            mark_payment_decision(payment, final)
    elif persist:
        mark_payment_decision(payment, final)

    agents = []
    if used_agent:
        from ar.agents import cash_application_agent, cash_reviewer_agent

        agents = [usage_from_agent(cash_application_agent)]
        if reviewer is not None:
            agents.append(usage_from_agent(cash_reviewer_agent))

    payment_after = get_payment(payment.payment_id) or payment
    trace = CashApplyTrace(
        payment_id=payment.payment_id,
        started_at=_now(),
        as_of_date=as_of,
        payment=payment_after,
        facts=facts,
        preparer=preparer,
        validation=validation,
        reviewer=reviewer,
        final=final,
        posted=posted,
        record=record,
        state_changes=record.invoice_changes if record else [],
        journal_entries=journals,
        agents=agents,
        used_agent=used_agent,
        already_posted=False,
    )
    if persist:
        path = save_trace(f"cash-{payment.payment_id}", trace)
        trace.trace_path = str(path)
        if final.decision == "HUMAN_REVIEW" and not posted:
            from ar.review import enqueue_review

            enqueue_review(trace)
    return trace


def run_ar_demo(as_of: str = DEFAULT_AS_OF) -> dict:
    """Deterministic judge-facing story. Resets AR state so the demo is reproducible."""
    reset_state()
    before = run_aging(as_of)
    collections = run_collections(as_of, live=False)
    clear = run_cash_apply("PAY-001", as_of=as_of, live=False)
    ambiguous = run_cash_apply("PAY-AMBIGUOUS", as_of=as_of, live=False)
    after = run_aging(as_of)
    snapshot = ar_close_snapshot(as_of)
    return {
        "as_of": as_of,
        "before": before,
        "collections": collections,
        "auto_apply": clear,
        "human_review": ambiguous,
        "after": after,
        "snapshot": snapshot,
    }


def run_ar_forecast_demo(as_of: str = DEFAULT_AS_OF) -> dict:
    """Deterministic story: forecast → PAY-005 review → correction → updated forecast."""
    from ar.models import MatchApplication
    from ar.review import correct_review
    from ar.store import applications_for_payment, events, get_payment, journals, open_reviews, precedents
    from reporting.forecast import build_forecast, persist_forecast_export
    from reporting.seed import seed_demo_receivable
    from reporting.store import next_version
    from scheduling.pool import seed_demo_pool

    reset_state()
    seed_demo_pool()
    seed_demo_receivable()
    forecast_before = build_forecast(as_of, version=next_version(as_of))
    persist_forecast_export(forecast_before)
    aging_before = run_aging(as_of)
    human_review = run_cash_apply("PAY-005", as_of=as_of, live=False)
    queue_before = open_reviews()
    resolved = correct_review(
        "PAY-005",
        [
            MatchApplication(invoice_id="INV-AR-101", amount=10000),
            MatchApplication(invoice_id="INV-AR-102", amount=15000),
        ],
        "Customer confirmed both invoices in remittance email",
        reviewer="controller",
    )
    aging_after = run_aging(as_of)
    forecast_after = build_forecast(as_of, prior=forecast_before, version=next_version(as_of))
    persist_forecast_export(forecast_after)
    payment_after = get_payment("PAY-005")
    posted = applications_for_payment("PAY-005")
    posted_journals = [
        item for item in journals() if item.related_payment_id == "PAY-005"
    ]
    human_precedents = [
        item
        for item in precedents("CUST-003")
        if item.source == "human" and item.source_payment_id == "PAY-005"
    ]
    return {
        "as_of": as_of,
        "forecast_before": forecast_before,
        "aging_before": aging_before,
        "human_review": human_review,
        "queue_before": queue_before,
        "resolved": resolved,
        "invoice_changes": posted[-1].invoice_changes if posted else [],
        "payment_after": payment_after,
        "journals": posted_journals,
        "aging_after": aging_after,
        "forecast_after": forecast_after,
        "audit": [item.model_dump(mode="json") for item in events() if item.payment_id == "PAY-005"],
        "precedents": human_precedents,
    }
