from __future__ import annotations

from ar.aging import aging_bucket, build_aging_report, days_past_due, derive_status
from ar.cash import generate_cash_candidates, policy_cash_decision, validate_proposal
from ar.collections import (
    build_collection_facts,
    enforce_collection_decision,
    policy_collection_decision,
)
from ar.ledger import post_application, record_human_application
from ar.models import (
    CashApplicationProposal,
    CollectionDecision,
    CustomerInvoice,
    MatchApplication,
)
from ar.store import events, get_invoice, get_payment, reset_state
from ar.workflow import run_aging, run_ar_demo, run_cash_apply, run_collections


AS_OF = "2026-09-30"


def _invoice(**kwargs) -> CustomerInvoice:
    defaults = dict(
        invoice_id="INV-T-001",
        customer_id="CUST-T",
        customer_name="Test Co",
        invoice_date="2026-09-01",
        due_date="2026-09-30",
        original_amount=1000.0,
        outstanding_amount=1000.0,
        created_at="2026-09-01T00:00:00Z",
    )
    defaults.update(kwargs)
    return CustomerInvoice.model_validate(defaults)


def test_aging_current_and_exact_due_date():
    invoice = _invoice(due_date="2026-09-30")
    report = build_aging_report(AS_OF, [invoice], persist=False)
    assert report.lines[0].days_past_due == 0
    assert report.lines[0].aging_bucket == "CURRENT"
    assert report.totals.current_ar == 1000


def test_aging_bucket_boundaries():
    cases = {
        "2026-09-29": ("1-30", 1),
        "2026-08-31": ("1-30", 30),
        "2026-08-30": ("31-60", 31),
        "2026-08-01": ("31-60", 60),
        "2026-07-31": ("61-90", 61),
        "2026-07-02": ("61-90", 90),
        "2026-07-01": ("90+", 91),
    }
    for due, (bucket, dpd) in cases.items():
        assert days_past_due(due, AS_OF) == dpd
        assert aging_bucket(dpd) == bucket
        report = build_aging_report(AS_OF, [_invoice(due_date=due)], persist=False)
        assert report.lines[0].aging_bucket == bucket


def test_aging_partial_and_paid_and_disputed():
    partial = _invoice(invoice_id="P", original_amount=40000, outstanding_amount=16000, due_date="2026-08-20")
    paid = _invoice(invoice_id="Z", original_amount=900, outstanding_amount=0, status="PAID")
    disputed = _invoice(
        invoice_id="D",
        original_amount=31200,
        outstanding_amount=31200,
        due_date="2026-07-20",
        dispute_status="OPEN",
        status="DISPUTED",
    )
    report = build_aging_report(AS_OF, [partial, paid, disputed], persist=False)
    ids = {item.invoice_id for item in report.lines}
    assert "Z" not in ids
    assert report.totals.partially_paid_ar == 16000
    assert report.totals.disputed_ar == 31200
    assert next(item for item in report.lines if item.invoice_id == "D").invoice_status == "DISPUTED"


def test_seeded_aging_has_every_bucket():
    report = run_aging(AS_OF, persist=False)
    buckets = {item.aging_bucket for item in report.lines}
    assert buckets == {"CURRENT", "1-30", "31-60", "61-90", "90+"}
    assert report.totals.total_ar > 0
    assert "INV-AR-051" not in {item.invoice_id for item in report.lines}
    assert next(item for item in report.lines if item.invoice_id == "INV-AR-050").aging_bucket == "CURRENT"
    assert next(item for item in report.lines if item.invoice_id == "INV-AR-054").aging_bucket == "1-30"
    assert next(item for item in report.lines if item.invoice_id == "INV-AR-061").aging_bucket == "31-60"


def test_collections_blocks_paid_dispute_cooldown_and_promise():
    paid = _invoice(outstanding_amount=0, status="PAID")
    paid_facts = build_collection_facts(paid, AS_OF)
    paid_decision = policy_collection_decision(paid_facts)
    assert paid_decision.action == "NO_ACTION"

    disputed = _invoice(due_date="2026-07-20", dispute_status="OPEN", status="DISPUTED")
    disputed_decision = policy_collection_decision(build_collection_facts(disputed, AS_OF))
    assert disputed_decision.action == "ESCALATE_DISPUTE"
    assert disputed_decision.human_approval_required is True
    assert disputed_decision.draft_message is None

    cooled = _invoice(due_date="2026-08-01", last_collection_contact="2026-09-28", reminder_count=1)
    cooled_decision = policy_collection_decision(build_collection_facts(cooled, AS_OF))
    assert cooled_decision.action == "HOLD_CONTACT"

    promised = _invoice(due_date="2026-09-10", promised_pay_date="2026-10-01", collection_status="PROMISE_TO_PAY")
    promised_decision = policy_collection_decision(build_collection_facts(promised, AS_OF))
    assert promised_decision.action == "HOLD_CONTACT"


def test_collections_escalates_old_overdue_and_cites_outstanding():
    old = _invoice(
        invoice_id="INV-AR-030",
        due_date="2026-05-15",
        original_amount=27800,
        outstanding_amount=27800,
        reminder_count=3,
        last_collection_contact="2026-08-01",
    )
    decision = policy_collection_decision(build_collection_facts(old, AS_OF))
    assert decision.action == "SEND_FINAL_NOTICE"
    assert decision.human_approval_required is True
    assert "$27,800.00" in (decision.draft_message or "")

    partial = _invoice(
        due_date="2026-08-20",
        original_amount=40000,
        outstanding_amount=16000,
        last_collection_contact="2026-08-01",
    )
    partial_decision = policy_collection_decision(build_collection_facts(partial, AS_OF))
    assert "$16,000.00" in (partial_decision.draft_message or "")
    assert "$40,000.00" not in (partial_decision.draft_message or "")


def test_collections_policy_rejects_illegal_agent_action():
    facts = build_collection_facts(
        _invoice(due_date="2026-07-20", dispute_status="OPEN", status="DISPUTED"),
        AS_OF,
    )
    raw = CollectionDecision(
        invoice_id=facts.invoice_id,
        customer_id=facts.customer_id,
        customer_name=facts.customer_name,
        action="SEND_FINAL_NOTICE",
        outstanding_amount=facts.outstanding_amount,
        days_past_due=facts.days_past_due,
        reason="chase anyway",
        confidence=0.9,
        draft_message="Pay $1,000.00 now",
    )
    enforced = enforce_collection_decision(facts, raw)
    assert enforced.action == "ESCALATE_DISPUTE"
    assert enforced.draft_message is None


def test_seeded_collections_demo_cases():
    run = run_collections(AS_OF, live=False)
    by_id = {item.invoice_id: item for item in run.decisions}
    assert by_id["INV-AR-017"].action == "SEND_OVERDUE_REMINDER"
    assert by_id["INV-AR-017"].human_approval_required is False
    assert "$18,500.00" in (by_id["INV-AR-017"].draft_message or "")
    assert by_id["INV-AR-020"].action == "ESCALATE_DISPUTE"
    assert by_id["INV-AR-020"].human_approval_required is True
    assert by_id["INV-AR-035"].action == "HOLD_CONTACT"
    assert by_id["INV-AR-045"].action == "SEND_GENTLE_REMINDER"
    assert any(item.human_approval_required for item in run.decisions)


def test_cash_explicit_invoice_auto_applies():
    reset_state()
    before = get_invoice("INV-AR-001")
    assert before and before.outstanding_amount == 12000
    trace = run_cash_apply("PAY-001", as_of=AS_OF, live=False)
    assert trace.final.decision == "AUTO_APPLY"
    assert trace.posted is True
    invoice = get_invoice("INV-AR-001")
    assert invoice is not None
    assert invoice.outstanding_amount == 0
    assert invoice.status == "PAID"
    payment = get_payment("PAY-001")
    assert payment is not None
    assert payment.application_status == "APPLIED"
    assert payment.unapplied_amount == 0


def test_cash_exact_single_match_and_partial_and_multi():
    reset_state()
    exact = run_cash_apply("PAY-002", live=False)
    assert exact.final.decision == "AUTO_APPLY"
    assert exact.record and exact.record.applications[0].invoice_id == "INV-AR-045"

    partial = run_cash_apply("PAY-004", live=False)
    assert partial.final.decision == "AUTO_APPLY"
    invoice = get_invoice("INV-AR-025")
    assert invoice is not None
    assert invoice.outstanding_amount == 11000
    assert invoice.status == "PARTIALLY_PAID"

    multi = run_cash_apply("PAY-003", live=False)
    assert multi.final.decision == "AUTO_APPLY"
    assert {row.invoice_id for row in multi.final.applications} == {"INV-AR-003", "INV-AR-004"}
    assert get_invoice("INV-AR-003").outstanding_amount == 0
    assert get_invoice("INV-AR-004").outstanding_amount == 0


def test_cash_overpayment_leaves_unapplied():
    reset_state()
    trace = run_cash_apply("PAY-008", live=False)
    assert trace.final.decision == "AUTO_APPLY"
    assert get_invoice("INV-AR-017").outstanding_amount == 0
    payment = get_payment("PAY-008")
    assert payment.unapplied_amount == 1500
    assert payment.application_status == "PARTIALLY_APPLIED"


def test_cash_ambiguous_and_unidentified_do_not_post():
    reset_state()
    before = get_invoice("INV-AR-103").outstanding_amount
    ambiguous = run_cash_apply("PAY-AMBIGUOUS", live=False)
    assert ambiguous.final.decision == "HUMAN_REVIEW"
    assert ambiguous.posted is False
    assert get_invoice("INV-AR-103").outstanding_amount == before
    assert get_payment("PAY-005").application_status == "HUMAN_REVIEW"
    assert len(ambiguous.facts.candidates) >= 2

    unknown = run_cash_apply("PAY-010", live=False)
    assert unknown.final.decision in {"UNAPPLIED", "HUMAN_REVIEW"}
    assert unknown.posted is False
    assert get_invoice("INV-AR-001").outstanding_amount == 12000


def test_invalid_proposal_is_rejected_and_does_not_over_apply():
    reset_state()
    payment = get_payment("PAY-001")
    bad = CashApplicationProposal(
        payment_id="PAY-001",
        decision="AUTO_APPLY",
        applications=[MatchApplication(invoice_id="INV-AR-001", amount=99999)],
        confidence=0.99,
        reason="force it",
    )
    result = validate_proposal(payment, bad)
    assert result.passed is False
    assert any("exceeds" in error for error in result.errors)

    unknown = CashApplicationProposal(
        payment_id="PAY-001",
        decision="AUTO_APPLY",
        applications=[MatchApplication(invoice_id="INV-NOPE", amount=100)],
        confidence=0.9,
        reason="invented",
    )
    assert validate_proposal(payment, unknown).passed is False

    negative = CashApplicationProposal(
        payment_id="PAY-001",
        decision="AUTO_APPLY",
        applications=[MatchApplication(invoice_id="INV-AR-001", amount=-1)],
        confidence=0.9,
        reason="negative",
    )
    assert validate_proposal(payment, negative).passed is False


def test_application_balances_and_misspelled_customer():
    reset_state()
    facts = generate_cash_candidates(get_payment("PAY-006"))
    assert facts.identified_customer_id == "CUST-001"
    decision = policy_cash_decision(facts)
    assert decision.decision == "AUTO_APPLY"
    assert decision.applications[0].invoice_id == "INV-AR-002"
    trace = run_cash_apply("PAY-006", live=False)
    assert get_invoice("INV-AR-002").outstanding_amount == 0
    assert get_payment("PAY-006").amount == sum(item.amount for item in trace.record.applications) + trace.record.unapplied_amount


def test_stale_reference_goes_to_review():
    reset_state()
    trace = run_cash_apply("PAY-009", live=False)
    assert trace.final.decision == "HUMAN_REVIEW"
    assert trace.posted is False
    assert get_invoice("INV-AR-051").outstanding_amount == 0


def test_payment_changes_later_aging_and_persists_trace():
    reset_state()
    before = run_aging(AS_OF)
    before_total = before.totals.total_ar
    trace = run_cash_apply("PAY-001", live=False)
    after = run_aging(AS_OF)
    assert after.totals.total_ar == before_total - 12000
    assert "INV-AR-001" not in {item.invoice_id for item in after.lines}
    assert trace.trace_path
    assert any(item.event_type == "cash_applied" and item.payment_id == "PAY-001" for item in events())


def test_human_review_does_not_mutate_and_rerun_does_not_double_apply():
    reset_state()
    first = run_cash_apply("PAY-001", live=False)
    invoice = get_invoice("INV-AR-001")
    assert invoice.outstanding_amount == 0
    second = run_cash_apply("PAY-001", live=False)
    assert second.already_posted is True
    assert get_invoice("INV-AR-001").outstanding_amount == 0
    assert get_payment("PAY-001").unapplied_amount == 0
    review = run_cash_apply("PAY-005", live=False)
    assert review.final.decision == "HUMAN_REVIEW"
    assert get_invoice("INV-AR-101").outstanding_amount == 10000
    assert get_invoice("INV-AR-103").outstanding_amount == 25000


def test_collections_sees_updated_balance_after_payment():
    reset_state()
    run_cash_apply("PAY-002", live=False)
    run = run_collections(AS_OF, live=False, persist=False)
    ids = {item.invoice_id for item in run.decisions}
    assert "INV-AR-045" not in ids


def test_human_correction_is_storable():
    reset_state()
    record = record_human_application(
        "PAY-005",
        [
            MatchApplication(invoice_id="INV-AR-101", amount=10000),
            MatchApplication(invoice_id="INV-AR-102", amount=15000),
        ],
        "Human chose the September pair over the single $25k invoice.",
    )
    assert record.posted is True
    assert get_invoice("INV-AR-101").outstanding_amount == 0
    assert get_invoice("INV-AR-102").outstanding_amount == 0
    assert get_invoice("INV-AR-103").outstanding_amount == 25000


def test_demo_is_deterministic():
    payload = run_ar_demo(AS_OF)
    assert payload["auto_apply"].final.decision == "AUTO_APPLY"
    assert payload["auto_apply"].posted is True
    assert payload["human_review"].final.decision == "HUMAN_REVIEW"
    assert payload["human_review"].posted is False
    assert payload["after"].totals.total_ar == payload["before"].totals.total_ar - 12000
    featured = next(item for item in payload["collections"].decisions if item.invoice_id == "INV-AR-017")
    assert featured.action == "SEND_OVERDUE_REMINDER"
    assert any(item.human_approval_required for item in payload["collections"].decisions)


def test_derive_status_does_not_infer_paid_from_a_payment_existing():
    invoice = _invoice(outstanding_amount=12000, status="OPEN")
    assert derive_status(invoice, AS_OF) != "PAID"
