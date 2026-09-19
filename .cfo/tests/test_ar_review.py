from __future__ import annotations

from ar.cash import generate_cash_candidates, policy_cash_decision, validate_proposal
from ar.ledger import mark_payment_decision
from ar.models import CashApplyTrace, MatchApplication
from ar.review import approve_review, correct_review, enqueue_review, reject_review
from ar.store import events, get_invoice, get_payment, get_review, journals, open_reviews, precedents, reset_state
from ar.workflow import run_ar_forecast_demo, run_cash_apply


AS_OF = "2026-09-30"


def _forced_review(payment_id: str, applications: list[MatchApplication] | None = None) -> CashApplyTrace:
    payment = get_payment(payment_id)
    facts = generate_cash_candidates(payment)
    preparer = policy_cash_decision(facts)
    if applications is not None:
        preparer = preparer.model_copy(
            update={"decision": "AUTO_APPLY", "applications": applications, "confidence": 0.7}
        )
    held = preparer.model_copy(
        update={"decision": "HUMAN_REVIEW", "review_question": "Forced into the review queue for tests."}
    )
    mark_payment_decision(payment, held)
    trace = CashApplyTrace(
        payment_id=payment.payment_id,
        started_at="2026-09-30T00:00:00Z",
        as_of_date=AS_OF,
        payment=get_payment(payment_id),
        facts=facts,
        preparer=preparer,
        validation=validate_proposal(payment, preparer),
        final=held,
    )
    enqueue_review(trace)
    return trace


def test_human_review_creates_persisted_review_item():
    reset_state()
    before = get_invoice("INV-AR-101").outstanding_amount
    trace = run_cash_apply("PAY-005", live=False)
    assert trace.final.decision == "HUMAN_REVIEW"
    item = get_review("PAY-005")
    assert item is not None
    assert item.status == "OPEN"
    assert item.payment_id == "PAY-005"
    assert item.payment_amount == 25000
    assert item.candidates
    assert item.trace_path
    assert get_invoice("INV-AR-101").outstanding_amount == before
    assert any(row.review_id == item.review_id for row in open_reviews())
    reset_state()
    assert get_review("PAY-005") is None
    run_cash_apply("PAY-005", live=False)
    assert get_review("PAY-005").status == "OPEN"


def test_approve_valid_proposal_posts_and_invalid_is_rejected():
    reset_state()
    _forced_review("PAY-001")
    item = approve_review("PAY-001", reviewer="controller", reason="Matches the remittance.")
    assert item.status == "APPROVED"
    assert item.resolved_by == "controller"
    assert get_invoice("INV-AR-001").outstanding_amount == 0
    assert get_payment("PAY-001").application_status == "APPLIED"
    journal = next(row for row in journals() if row.related_payment_id == "PAY-001")
    assert journal.debit.amount == journal.credit.amount == 12000
    assert journal.debit.account == "Cash"
    assert journal.credit.account == "Accounts Receivable"

    reset_state()
    _forced_review("PAY-001", [MatchApplication(invoice_id="INV-AR-001", amount=99999)])
    try:
        approve_review("PAY-001")
        raise AssertionError("invalid approval should fail")
    except ValueError as exc:
        assert "validation" in str(exc).lower()
    assert get_invoice("INV-AR-001").outstanding_amount == 12000
    assert get_review("PAY-001").status == "OPEN"


def test_correction_posts_specified_allocation_and_writes_precedent():
    reset_state()
    run_cash_apply("PAY-005", live=False)
    item = correct_review(
        "PAY-005",
        [
            MatchApplication(invoice_id="INV-AR-101", amount=10000),
            MatchApplication(invoice_id="INV-AR-102", amount=15000),
        ],
        "Customer confirmed both invoices in remittance email",
        reviewer="controller",
    )
    assert item.status == "CORRECTED"
    assert item.differed_from_agent is True
    assert get_invoice("INV-AR-101").outstanding_amount == 0
    assert get_invoice("INV-AR-102").outstanding_amount == 0
    assert get_invoice("INV-AR-103").outstanding_amount == 25000
    assert get_payment("PAY-005").application_status == "APPLIED"
    human = [row for row in precedents("CUST-003") if row.source == "human"]
    assert human
    assert human[-1].source_payment_id == "PAY-005"
    assert human[-1].source_review_id == item.review_id
    assert human[-1].facts["invoice_ids"] == ["INV-AR-101", "INV-AR-102"]
    types = {row.event_type for row in events() if row.payment_id == "PAY-005"}
    assert "cash_held" in types
    assert "cash_applied" in types
    assert "cash_review_resolved" in types
    resolved = next(row for row in events() if row.event_type == "cash_review_resolved")
    assert resolved.details["agent_decision"] == "HUMAN_REVIEW"
    assert resolved.details["differed_from_agent"] is True
    journal = next(row for row in journals() if row.related_payment_id == "PAY-005")
    assert journal.debit.amount == journal.credit.amount


def test_rejection_leaves_invoices_unchanged():
    reset_state()
    run_cash_apply("PAY-005", live=False)
    before_101 = get_invoice("INV-AR-101").outstanding_amount
    before_103 = get_invoice("INV-AR-103").outstanding_amount
    item = reject_review("PAY-005", "Unable to identify intended invoices", reviewer="controller")
    assert item.status == "REJECTED"
    assert get_invoice("INV-AR-101").outstanding_amount == before_101
    assert get_invoice("INV-AR-103").outstanding_amount == before_103
    payment = get_payment("PAY-005")
    assert payment.application_status == "UNMATCHED"
    assert payment.unapplied_amount == 25000
    assert payment.metadata.get("unapplied_after_review") is True
    assert not any(row.related_payment_id == "PAY-005" and row.entry_type == "cash_receipt" for row in journals())


def test_resolved_review_cannot_be_resolved_twice():
    reset_state()
    run_cash_apply("PAY-005", live=False)
    reject_review("PAY-005", "No match")
    try:
        reject_review("PAY-005", "again")
        raise AssertionError("second resolve should fail")
    except ValueError as exc:
        assert "already" in str(exc).lower()


def test_ar_forecast_demo_closes_the_loop():
    payload = run_ar_forecast_demo(AS_OF)
    assert payload["human_review"].final.decision == "HUMAN_REVIEW"
    assert payload["queue_before"]
    assert payload["resolved"].status == "CORRECTED"
    assert get_invoice("INV-AR-101").outstanding_amount == 0
    assert payload["forecast_before"].horizon_weeks == 13
    assert payload["forecast_after"].horizon_weeks == 13
    assert payload["precedents"]
    assert any(item["event_type"] == "cash_review_resolved" for item in payload["audit"])
