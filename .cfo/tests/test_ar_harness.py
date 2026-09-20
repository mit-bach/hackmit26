"""Session 06 proofs: apply vs collect, Verifier Handles, Grant isolation."""

from __future__ import annotations

import json
from pathlib import Path

from ar.agents import CASH_TOOLS, COLLECTION_TOOLS, cash_application_agent, collections_agent
from ar.collections import enforce_collection_decision, policy_collection_decision, build_collection_facts
from ar.drain import new_deposits
from ar.grants import profile_allows, tool_export_names
from ar.models import CollectionDecision, CustomerInvoice
from ar.store import (
    get_invoice,
    get_payment,
    get_review,
    open_human_reviews,
    open_reviews,
    reset_state,
)
from ar.workflow import drain_new_deposits, run_cash_apply, run_collections

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


def test_ambiguous_remittance_is_verifier_handle_not_human_queue():
    reset_state()
    before = get_invoice("INV-AR-103").outstanding_amount
    trace = run_cash_apply("PAY-AMBIGUOUS", as_of=AS_OF, live=False)
    assert trace.final.decision == "HUMAN_REVIEW"
    assert trace.posted is False
    assert get_invoice("INV-AR-103").outstanding_amount == before
    assert get_payment("PAY-005").application_status == "HUMAN_REVIEW"
    item = get_review("PAY-005")
    assert item is not None
    assert item.human_queue is False
    assert item.queue_owner == "ctl-cash"
    assert item.queue_profile == "review-apply"
    assert item.handle_path
    assert item.packet_path
    from ar.store import HANDLES_DIR, PACKETS_DIR

    assert Path(item.handle_path).parent == HANDLES_DIR
    assert Path(item.packet_path).parent == PACKETS_DIR
    handle = json.loads(Path(item.handle_path).read_text())
    assert handle["toSlug"] == "ctl-cash"
    assert handle["profile"] == "review-apply"
    assert handle["humanQueue"] is False
    assert handle["kernelStatus"] == "HUMAN_REVIEW"
    packet = json.loads(Path(item.packet_path).read_text())
    assert packet["human_queue"] is False
    assert packet["queue_owner"] == "ctl-cash"
    assert open_human_reviews() == []
    assert any(row.review_id == item.review_id for row in open_reviews())


def test_collections_blocked_until_apply_drains():
    reset_state()
    assert new_deposits(AS_OF)
    blocked = run_collections(AS_OF, live=False)
    assert blocked.blocked is True
    assert blocked.decisions == []
    assert blocked.apply_handle_path
    handle = json.loads(Path(blocked.apply_handle_path).read_text())
    assert handle["toSlug"] == "apply"
    assert handle["humanQueue"] is False
    drain_new_deposits(AS_OF, live=False)
    assert new_deposits(AS_OF) == []
    run = run_collections(AS_OF, live=False)
    assert run.blocked is False
    ids = {item.invoice_id for item in run.decisions}
    assert "INV-AR-045" not in ids
    assert "INV-AR-020" in ids


def test_collections_cannot_chase_paid_disputed_cooldown():
    paid = _invoice(outstanding_amount=0, status="PAID")
    paid_facts = build_collection_facts(paid, AS_OF)
    raw = CollectionDecision(
        invoice_id=paid_facts.invoice_id,
        customer_id=paid_facts.customer_id,
        customer_name=paid_facts.customer_name,
        action="SEND_FINAL_NOTICE",
        outstanding_amount=paid_facts.outstanding_amount,
        days_past_due=paid_facts.days_past_due,
        reason="chase anyway",
        confidence=0.9,
        draft_message="Pay now",
    )
    assert enforce_collection_decision(paid_facts, raw).action == "NO_ACTION"

    disputed = _invoice(due_date="2026-07-20", dispute_status="OPEN", status="DISPUTED")
    disputed_facts = build_collection_facts(disputed, AS_OF)
    disputed_raw = CollectionDecision(
        invoice_id=disputed_facts.invoice_id,
        customer_id=disputed_facts.customer_id,
        customer_name=disputed_facts.customer_name,
        action="SEND_OVERDUE_REMINDER",
        outstanding_amount=disputed_facts.outstanding_amount,
        days_past_due=disputed_facts.days_past_due,
        reason="chase anyway",
        confidence=0.9,
        draft_message="Pay $1,000.00 now",
    )
    enforced = enforce_collection_decision(disputed_facts, disputed_raw)
    assert enforced.action == "ESCALATE_DISPUTE"
    assert enforced.draft_message is None

    cooled = _invoice(due_date="2026-08-01", last_collection_contact="2026-09-28", reminder_count=1)
    cooled_facts = build_collection_facts(cooled, AS_OF)
    cooled_raw = policy_collection_decision(cooled_facts)
    assert cooled_raw.action == "HOLD_CONTACT"
    send = CollectionDecision(
        invoice_id=cooled_facts.invoice_id,
        customer_id=cooled_facts.customer_id,
        customer_name=cooled_facts.customer_name,
        action="SEND_GENTLE_REMINDER",
        outstanding_amount=cooled_facts.outstanding_amount,
        days_past_due=cooled_facts.days_past_due,
        reason="again",
        confidence=0.9,
        draft_message=f"Pay ${cooled_facts.outstanding_amount:,.2f}",
    )
    assert enforce_collection_decision(cooled_facts, send).action == "HOLD_CONTACT"


def test_apply_cannot_call_create_accrual_or_pay_run():
    assert profile_allows("apply", "apply", "ar.tools.get_cash_application_facts")
    assert not profile_allows("apply", "apply", "accrual.tools.create_accrual")
    assert not profile_allows("apply", "apply", "scheduling.tools.get_approved_pool")
    assert not profile_allows("apply", "apply", "scheduling.tools.get_payment_candidates")
    assert not profile_allows("apply", "apply", "ar.tools.get_collection_candidates")
    assert not profile_allows("collect", "chase", "ar.tools.get_cash_application_facts")
    assert not profile_allows("collect", "chase", "accrual.tools.create_accrual")
    apply_names = tool_export_names(CASH_TOOLS)
    collect_names = tool_export_names(COLLECTION_TOOLS)
    assert "get_cash_application_facts" in apply_names
    assert "get_collection_candidates" not in apply_names
    assert "create_accrual" not in apply_names
    assert "get_approved_pool" not in apply_names
    assert "get_cash_application_facts" not in collect_names
    assert "create_accrual" not in collect_names
    assert cash_application_agent.output_type.__name__ == "CashApplicationProposal"
    assert collections_agent.output_type.__name__ == "CollectionDecision"


def test_state_json_is_disk_source_of_truth():
    from ar.store import STATE_PATH

    reset_state()
    assert STATE_PATH.exists()
    run_cash_apply("PAY-001", live=False)
    raw = json.loads(STATE_PATH.read_text())
    assert raw["payments"]["PAY-001"]["application_status"] == "APPLIED"
    assert raw["invoices"]["INV-AR-001"]["outstanding_amount"] == 0
