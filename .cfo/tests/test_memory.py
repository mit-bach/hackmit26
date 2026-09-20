from __future__ import annotations

from memory.format import format_lookup_trace, format_precedents
from memory.hooks import lookup_for_cash
from memory.models import DecisionMemory, MemoryEvidence, MemoryQuery
from memory.policy import memory_mode
from memory.retrieve import lookup_memories, search_memories
from memory.scenarios import (
    AUGUST_STRIPE,
    CLOUDCO_CONTRADICT,
    CLOUDCO_SEPTEMBER,
    NORDIC_SEPTEMBER,
    SEPTEMBER_STRIPE,
    run_harbor_cross_period,
    run_harbor_period,
    run_prepaid_cross_period,
    run_stripe_contradiction,
    run_stripe_cross_period,
    run_stripe_period,
)
from memory.store import find_by_idempotency_key, load_memories, put_memory
from memory.write import write_decision
from skills.assignments import skills_for
from skills.loader import load_skill


def _manual_record(**overrides) -> DecisionMemory:
    payload = dict(
        period="2026-08",
        workflow="cash_reconciliation",
        entity_type="payment_provider",
        entity_id="stripe",
        situation_type="payout_difference",
        situation_summary="Stripe payout lower than gross receipts",
        evidence=[MemoryEvidence(kind="fee", label="processing_fees", amount=300.0, amount_minor=30000)],
        decision="reconcile payout net of fees and chargebacks",
        reasoning_summary="Difference matched fees plus chargebacks.",
        accounting_treatment="net_payout_fees_and_chargebacks",
        outcome="EXPLAINED_EXCEPTION",
        reusable_precedent="Stripe payouts may arrive net of fees and chargebacks",
        source_trace_ids=["REC-001"],
        tags=["stripe", "payout_difference"],
        fingerprint="manual-aug",
    )
    payload.update(overrides)
    record, created = write_decision(**payload)
    return record, created


def test_memory_record_persists():
    record, created = _manual_record()
    assert created is True
    assert record.decision_id.startswith("DEC-2026-08-")
    stored = load_memories()
    assert any(item.decision_id == record.decision_id for item in stored)
    assert stored[0].reasoning_summary
    assert "chain of thought" not in stored[0].reasoning_summary.lower()


def test_memory_survives_separate_workflow_runs():
    first, _ = _manual_record()
    run_stripe_period(SEPTEMBER_STRIPE, memory_enabled=True, reset=True)
    ids = {item.decision_id for item in load_memories()}
    assert first.decision_id in ids
    assert any(item.period == "2026-09" for item in load_memories())


def test_later_period_retrieves_earlier_period_memory():
    _manual_record()
    lookup = lookup_memories(
        MemoryQuery(
            workflow="cash_reconciliation",
            entity_id="stripe",
            situation_type="payout_difference",
            prior_to_period="2026-09",
            exclude_period="2026-09",
        )
    )
    assert lookup.queried is True
    assert lookup.retrieved
    assert lookup.precedents[0].period == "2026-08"


def test_unrelated_memory_is_not_retrieved():
    _manual_record()
    write_decision(
        period="2026-08",
        workflow="prepaid",
        entity_type="vendor",
        entity_id="cloudco",
        situation_type="prepaid_treatment",
        situation_summary="CloudCo annual license prepaid",
        evidence=[],
        decision="straight_line_monthly",
        reasoning_summary="Twelve-month coverage.",
        accounting_treatment="straight_line_monthly",
        outcome="amortized",
        reusable_precedent="CloudCo annual licenses are prepaid",
        source_trace_ids=["PRE-1"],
        tags=["prepaid", "cloudco"],
        fingerprint="cloud-aug",
    )
    hits = search_memories(
        MemoryQuery(workflow="cash_reconciliation", entity_id="stripe", situation_type="payout_difference")
    )
    assert all(item.entity_id == "stripe" for item in hits)
    assert all(item.workflow == "cash_reconciliation" for item in hits)


def test_entity_specific_precedent_ranks_above_unrelated():
    write_decision(
        period="2026-08",
        workflow="cash_reconciliation",
        entity_type="payment_provider",
        entity_id="adyen",
        situation_type="payout_difference",
        situation_summary="Adyen fee pattern",
        evidence=[],
        decision="net payout",
        reasoning_summary="Adyen fees explained the difference.",
        accounting_treatment="net_payout_fees_and_chargebacks",
        outcome="EXPLAINED_EXCEPTION",
        reusable_precedent="Adyen payouts may arrive net of fees",
        source_trace_ids=["REC-ADY"],
        tags=["adyen", "payout_difference"],
        fingerprint="adyen-aug",
    )
    stripe, _ = _manual_record()
    hits = search_memories(
        MemoryQuery(
            workflow="cash_reconciliation",
            entity_type="payment_provider",
            entity_id="stripe",
            situation_type="payout_difference",
        )
    )
    assert hits
    assert hits[0].decision_id == stripe.decision_id
    assert hits[0].entity_id == "stripe"


def test_agent_receives_prior_precedent():
    story = run_stripe_cross_period(memory_enabled=True)
    lookup = story["september_trace"].memory_lookup
    assert lookup is not None
    assert lookup.queried is True
    assert lookup.retrieved
    text = format_precedents(lookup)
    assert "Prior precedent" in text
    assert "2026-08" in text
    assert "not as authoritative truth" in text.lower() or "precedent, not as authoritative" in text


def test_precedent_does_not_override_contradictory_current_evidence():
    story = run_stripe_contradiction(memory_enabled=True)
    trace = story["september_trace"]
    lookup = trace.memory_lookup
    assert lookup is not None
    assert lookup.retrieved
    assert lookup.precedent_used is False
    assert lookup.current_evidence_checked is True
    assert lookup.evidence_supports_precedent is False
    assert lookup.deviation
    assert trace.final.status == "HUMAN_REVIEW"


def test_later_period_decision_becomes_new_memory():
    story = run_stripe_cross_period(memory_enabled=True)
    periods = {item.period for item in load_memories()}
    assert "2026-08" in periods
    assert "2026-09" in periods
    sep_ids = [item.decision_id for item in load_memories() if item.period == "2026-09"]
    assert sep_ids
    assert story["september_trace"].written_memory_id in sep_ids
    assert story["september_trace"].written_memory_id != story["august_trace"].written_memory_id


def test_memory_disabled_skips_retrieval():
    story = run_stripe_cross_period(memory_enabled=False)
    lookup = story["september_trace"].memory_lookup
    assert lookup is not None
    assert lookup.memory_enabled is False
    assert lookup.queried is False
    assert lookup.retrieved == []
    assert lookup.precedent_used is False
    assert story["september_trace"].final.status in {"MATCHED", "EXPLAINED_EXCEPTION"}


def test_august_september_stripe_scenario():
    story = run_stripe_cross_period(memory_enabled=True)
    aug = story["august_trace"]
    sep = story["september_trace"]
    assert aug.final.bank_amount == AUGUST_STRIPE.bank
    assert aug.final.ledger_amount == AUGUST_STRIPE.gross
    assert abs(aug.final.difference) == 380
    assert aug.final.status == "EXPLAINED_EXCEPTION"
    assert sep.final.bank_amount == SEPTEMBER_STRIPE.bank
    assert sep.final.ledger_amount == SEPTEMBER_STRIPE.gross
    assert abs(sep.final.difference) == 540
    assert sep.final.status == "EXPLAINED_EXCEPTION"
    lookup = sep.memory_lookup
    assert lookup.precedent_used is True
    assert lookup.current_evidence_checked is True
    blob = format_lookup_trace(lookup)
    assert "memory_lookup" in blob
    assert "workflow=cash_reconciliation" in blob
    assert "entity=stripe" in blob
    assert lookup.retrieved[0] in blob
    assert "precedent_used:" in blob
    assert "yes" in blob


def test_deterministic_reruns_do_not_create_duplicate_memory():
    first = run_stripe_period(AUGUST_STRIPE, memory_enabled=True, reset=True)
    count_after_first = len(load_memories())
    second = run_stripe_period(AUGUST_STRIPE, memory_enabled=True, reset=True)
    assert len(load_memories()) == count_after_first
    keys = [item.idempotency_key for item in load_memories()]
    assert len(keys) == len(set(keys))
    first_id = first.traces[0].written_memory_id
    second_id = second.traces[0].written_memory_id
    if first_id and second_id:
        assert first_id == second_id
        assert find_by_idempotency_key(load_memories()[0].idempotency_key) is not None


def test_prepaid_cross_period_uses_vendor_precedent():
    story = run_prepaid_cross_period(memory_enabled=True, september_item=CLOUDCO_SEPTEMBER)
    sep = story["september_trace"]
    assert sep.selected_method == "straight_line_monthly"
    assert sep.memory_lookup is not None
    assert sep.memory_lookup.precedent_used is True
    assert sep.memory_lookup.retrieved
    assert any(item.period == "2026-08" for item in load_memories() if item.entity_id == "cloudco")
    assert sep.written_memory_id


def test_prepaid_unrelated_vendor_does_not_use_cloudco_precedent():
    story = run_prepaid_cross_period(memory_enabled=True, september_item=NORDIC_SEPTEMBER)
    lookup = story["september_trace"].memory_lookup
    assert lookup is not None
    assert lookup.precedent_used is False
    assert story["september_trace"].selected_method == "straight_line_monthly"


def test_prepaid_contradictory_coverage_does_not_reuse_annual_treatment():
    story = run_prepaid_cross_period(memory_enabled=True, september_item=CLOUDCO_CONTRADICT)
    lookup = story["september_trace"].memory_lookup
    assert story["september_trace"].selected_method == "immediate_expense"
    assert lookup.precedent_used is False
    assert lookup.current_evidence_checked is True
    assert lookup.deviation


def test_duplicate_ap_exception_writes_vendor_invoice_pattern_memory():
    from models import FinalAPDecision
    from memory.hooks import lookup_for_ap, write_ap_memory
    from tools import collect_case_evidence

    evidence = collect_case_evidence("INV-018")
    assert "duplicate" in evidence.exception_types
    final = FinalAPDecision(
        invoice_id="INV-018",
        decision="HOLD",
        confidence=0.9,
        reasons=["duplicate vendor invoice number"],
        duplicate_detected=True,
        receipt_status=evidence.receipt_status,
        evidence_used=["INV-018"],
        investigation_performed=True,
        audit_status="passed",
    )
    written = write_ap_memory(evidence, final, period="2026-09", trace_id="INV-018")
    assert written is not None
    record, created = written
    assert created is True
    assert record.situation_type == "vendor_invoice_pattern"
    assert "duplicate" in record.tags
    lookup = lookup_for_ap(evidence, "2026-10")
    assert lookup.queried is True
    assert any(item.decision_id == record.decision_id for item in lookup.precedents)


def test_prior_period_precedent_skill_is_assigned():
    skill = load_skill("prior-period-precedent")
    assert "precedent, not as authoritative" in skill["body"].lower() or "not as authoritative truth" in skill["body"]
    assert "prior-period-precedent" in skills_for("Cash Exception Investigator")
    assert "prior-period-precedent" in skills_for("Prepaid Preparer")
    assert "prior-period-precedent" in skills_for("Exception Investigator")
    assert "prior-period-precedent" in skills_for("Accrual Agent")
    assert "prior-period-precedent" in skills_for("Month-End Close Reviewer")
    assert "prior-period-precedent" not in skills_for("AP Preparer")


def test_put_memory_is_idempotent():
    record, created = _manual_record()
    again, created_again = put_memory(record)
    assert created is True
    assert created_again is False
    assert again.decision_id == record.decision_id
    assert len(load_memories()) == 1


def test_harbor_electric_september_reuses_august_methodology():
    story = run_harbor_cross_period(memory_enabled=True)
    aug = story["august_trace"]
    sep = story["september_trace"]
    assert aug.final_method == "seasonal_prior_year"
    assert aug.final_amount == 7800
    assert aug.written_memory_id
    assert sep.final_method == "seasonal_prior_year"
    assert sep.final_amount == 4650
    lookup = sep.memory_lookup
    assert lookup is not None
    assert lookup.queried is True
    assert lookup.precedent_used is True
    assert lookup.current_evidence_checked is True
    assert lookup.evidence_supports_precedent is True
    assert lookup.retrieved
    assert lookup.retrieved[0] == aug.written_memory_id
    assert sep.written_memory_id
    assert sep.written_memory_id != aug.written_memory_id
    packet = story["september_packet"]
    assert lookup.retrieved[0] in packet
    assert "prior decision" in packet.lower() or "PRIOR-PERIOD ACCRUAL" in packet
    assert "Harbor Electric" in packet


def test_harbor_method_shift_is_visible_and_still_correct():
    story = run_harbor_cross_period(memory_enabled=True, august_method="recent_average")
    lookup = story["september_trace"].memory_lookup
    assert story["september_trace"].final_method == "seasonal_prior_year"
    assert lookup is not None
    assert lookup.retrieved
    assert lookup.precedent_used is False
    assert lookup.current_evidence_checked is True
    assert lookup.deviation
    assert "recent_average" in lookup.deviation
    assert lookup.retrieved[0] in story["september_packet"]


def test_harbor_memory_off_still_books_seasonal():
    story = run_harbor_cross_period(memory_enabled=False)
    lookup = story["september_trace"].memory_lookup
    assert story["september_trace"].final_method == "seasonal_prior_year"
    assert story["september_trace"].final_amount == 4650
    assert lookup is not None
    assert lookup.memory_enabled is False
    assert lookup.queried is False
    assert lookup.precedent_used is False
    assert story["september_trace"].written_memory_id


def test_harbor_accrual_write_is_idempotent():
    first_decision, first_trace = run_harbor_period(
        "2026-08",
        memory_enabled=True,
        hide_period_invoices=True,
        method="seasonal_prior_year",
        reset=True,
        run_id="mem-aug-idemp-1",
    )
    count = len(load_memories())
    second_decision, second_trace = run_harbor_period(
        "2026-08",
        memory_enabled=True,
        hide_period_invoices=True,
        method="seasonal_prior_year",
        reset=True,
        run_id="mem-aug-idemp-2",
    )
    assert first_decision.estimation_method == second_decision.estimation_method
    assert len(load_memories()) == count
    assert first_trace.written_memory_id == second_trace.written_memory_id


def test_cash_query_with_memory_off_is_empty():
    _manual_record()
    with memory_mode(False):
        from cash_recon.models import MatchCandidate

        candidate = MatchCandidate(
            candidate_id="FEE_NETTED:x:y",
            match_type="FEE_NETTED",
            bank_transaction_ids=["BNK"],
            ledger_entry_ids=["GL"],
            bank_amount=9620,
            ledger_amount=10000,
            difference=-380,
            provider="stripe",
        )
        lookup = lookup_for_cash(candidate, "2026-09")
    assert lookup.memory_enabled is False
    assert lookup.queried is False
    assert lookup.retrieved == []
