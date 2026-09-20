from __future__ import annotations

import json

from ar.store import all_payments, applications, journals, load_empty_state
from evaluation.isolation import operational_phase_guard
from integrations.providers import stripe
from integrations.router import (
    WORKFLOW_DISPUTE,
    WORKFLOW_DUPLICATE,
    WORKFLOW_PAYMENT,
    WORKFLOW_PAYMENT_FAILED,
    WORKFLOW_PAYOUT,
    WORKFLOW_REFUND,
    classify_stripe_event,
)
from integrations.store import all_payouts, all_reconciliations, reset_integration_state
from simulations.stripe.eval import evaluate_runs, hidden_ground_truth
from simulations.stripe.pack import build_company_pack, scenario_by_id
from simulations.stripe.persist import persist_pack
from simulations.stripe.runtime import run_all_scenarios, run_scenario


def _run(scenario_id: str) -> dict:
    pack = build_company_pack()
    return run_scenario(scenario_by_id(scenario_id, pack), pack=pack)


def test_router_classifies_stripe_event_types():
    assert classify_stripe_event("payment_intent.succeeded") == WORKFLOW_PAYMENT
    assert classify_stripe_event("charge.succeeded") == WORKFLOW_PAYMENT
    assert classify_stripe_event("refund.created") == WORKFLOW_REFUND
    assert classify_stripe_event("charge.dispute.created") == WORKFLOW_DISPUTE
    assert classify_stripe_event("payout.reconciliation_completed") == WORKFLOW_PAYOUT
    assert classify_stripe_event("payment_intent.payment_failed") == WORKFLOW_PAYMENT_FAILED
    assert classify_stripe_event("payment_intent.created") == "ignored"


def test_simple_payment_goes_through_adapter_and_ar():
    run = _run("stripe_simple_payment")
    graded = evaluate_runs([run])
    assert graded["cases"][0]["passed"], graded["cases"][0]
    assert run["entities"]["payments"]
    assert run["reconciliation"]["status"] == "MATCH"
    assert run["reconciliation"]["expected_payout_minor"] == 97070


def test_customer_paid_gross_not_net_settlement():
    run = _run("stripe_simple_payment")
    payment = run["entities"]["payments"][0]
    invoice = next(item for item in run["entities"]["invoices"] if item["invoice_id"] == "INV-STR-001")
    receipt = next(item for item in run["journals"] if item["entry_type"] == "cash_receipt")
    fee = next(item for item in run["journals"] if item["entry_type"] == "processor_fee")
    assert payment["amount"] == 1000.00
    assert invoice["outstanding_amount"] == 0
    assert invoice["original_amount"] == 1000.00
    assert receipt["debit"]["amount"] == 1000.00
    assert receipt["credit"]["account"] == "Accounts Receivable"
    assert fee["debit"]["amount"] == 29.30
    assert run["reconciliation"]["expected_payout_minor"] == 97070
    assert run["reconciliation"]["bank_deposit_amount"] == 970.70
    assert payment["amount"] != run["reconciliation"]["expected_payout"]


def test_combined_payout_is_not_one_invoice():
    run = _run("stripe_payout_multiple_payments")
    assert evaluate_runs([run])["cases"][0]["passed"]
    payout = run["entities"]["payouts"][0]
    assert len(payout["lines"]) == 3
    assert payout["amount"] == 97070 + 145595 + 48520


def test_refund_before_payout_keeps_history():
    run = _run("stripe_refund_before_payout")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert any(item["entry_type"] == "refund" for item in run["journals"])
    assert run["entities"]["payments"][0]["application_status"] in {"APPLIED", "PARTIALLY_APPLIED"}


def test_refund_after_payout_uses_later_payout():
    run = _run("stripe_refund_after_payout")
    assert evaluate_runs([run])["cases"][0]["passed"]
    payout_ids = {item["payout_id"] for item in run["entities"]["payouts"]}
    assert "po_str_005a" in payout_ids
    assert "po_str_005b" in payout_ids


def test_dispute_is_not_unexplained_bank_break():
    run = _run("stripe_chargeback")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["reconciliation"]["status"] == "MATCH"
    assert any(item["event_type"] == "stripe_dispute" for item in run["ar_events"])
    invoice = next(item for item in run["entities"]["invoices"] if item["invoice_id"] == "INV-STR-006")
    payment = run["entities"]["payments"][0]
    assert payment["amount"] == 800.00
    assert invoice["outstanding_amount"] == 0
    assert invoice["status"] == "DISPUTED"
    assert run["relationships"]["disputes"][0]["payment_id"] == payment["payment_id"]
    assert run["reconciliation"]["expected_payout_minor"] == -81500


def test_fee_uses_source_facts_not_universal_rate():
    run = _run("stripe_fee_variation")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert abs(run["reconciliation"]["fees"]) == 72.0
    standard = round(2000 * 0.029, 2) + 0.30
    assert abs(run["reconciliation"]["fees"]) != standard


def test_duplicate_event_is_idempotent():
    run = _run("stripe_duplicate_event")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["replay"]["duplicate"] is True
    assert len(all_payouts()) == 1
    assert len(all_reconciliations()) == 1
    receipts = [item for item in run["journals"] if item["entry_type"] == "cash_receipt"]
    assert len(receipts) == 1


def test_out_of_order_events_converge():
    run = _run("stripe_out_of_order")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["reconciliation"]["status"] == "MATCH"
    assert run["reconciliation"]["expected_payout_minor"] == 97070


def test_missing_metadata_matches_by_evidence():
    run = _run("stripe_missing_metadata")
    assert evaluate_runs([run])["cases"][0]["passed"]
    payment = run["entities"]["payments"][0]
    assert not payment["invoice_reference"]
    assert run["applications"][0]["applications"][0]["invoice_id"] == "INV-STR-010"


def test_ambiguous_invoices_use_context_not_arbitrary_pick():
    run = _run("stripe_ambiguous_invoice")
    assert evaluate_runs([run])["cases"][0]["passed"]
    applied = run["applications"][0]["applications"][0]["invoice_id"]
    assert applied == "INV-STR-011A"


def test_bank_discrepancy_is_exact_and_blocks_close():
    run = _run("stripe_bank_discrepancy_1240")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["reconciliation"]["status"] == "MISMATCH"
    assert "bank_amount_differs_from_stripe_payout" in run["reconciliation"]["exceptions"]
    assert run["close"]["effect"] == "BLOCK_CLOSE"
    bank_gap = abs(
        round(run["reconciliation"]["actual_payout"] - run["reconciliation"]["bank_deposit_amount"], 2)
    )
    assert bank_gap == 12.40


def test_cross_period_cash_settles_in_october():
    run = _run("stripe_cross_period_timing")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["forecast"]["settlement_period"] == "2026-10"
    payment = run["entities"]["payments"][0]
    assert payment["payment_date"].startswith("2026-09")


def test_cross_period_memory_selects_platform_fee_invoice():
    run = _run("stripe_cross_period_memory")
    assert evaluate_runs([run])["cases"][0]["passed"]
    applied = run["applications"][0]["applications"][0]["invoice_id"]
    assert applied == "INV-STR-018B"
    blob = json.dumps(run)
    assert "AR-PREC-STR-ATLAS-AUG" in blob or "precedent" in blob.lower()


def test_failed_payment_does_not_post_cash():
    run = _run("stripe_failed_then_retry")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert any(row["classified_workflow"] == WORKFLOW_PAYMENT_FAILED for row in run["agent_routing"])
    assert len(run["applications"]) == 1


def test_unmatched_stripe_charge_stays_unapplied():
    run = _run("stripe_unmatched_order")
    assert evaluate_runs([run])["cases"][0]["passed"]
    payment = run["entities"]["payments"][0]
    assert payment["application_status"] in {"UNMATCHED", "UNAPPLIED"}
    assert run["applications"] == []


def test_overpayment_is_not_silently_applied():
    run = _run("stripe_overpayment")
    assert evaluate_runs([run])["cases"][0]["passed"]
    payment = run["entities"]["payments"][0]
    assert payment["application_status"] == "HUMAN_REVIEW"
    assert not any(item["entry_type"] == "cash_receipt" for item in run["journals"])


def test_hidden_ground_truth_is_not_on_operational_objects():
    pack = build_company_pack()
    for event in pack.events:
        blob = json.dumps(event)
        assert "expected_net_cents" not in blob
        assert "expected_gl_entries" not in blob
    with operational_phase_guard():
        run = run_scenario(scenario_by_id("stripe_simple_payment", pack), pack=pack)
    assert "expected_net_cents" not in json.dumps(run.get("agent_actions"))


def test_full_suite_and_eval_metrics(tmp_path):
    pack = build_company_pack()
    runs = [run_scenario(item, pack=pack) for item in pack.scenarios]
    report = evaluate_runs(runs)
    assert report["metrics"]["cases_total"] == len(pack.scenarios)
    assert report["passed"], json.dumps(report["cases"], indent=2)
    assert report["metrics"]["end_to_end_scenario_pass_rate"] == 1.0
    persist_pack(tmp_path / "pack")
    assert (tmp_path / "pack" / "events.json").exists()
    assert (tmp_path / "pack" / "evaluation" / "ground_truth.json").exists()


def test_suite_is_isolated_across_consecutive_runs():
    first = evaluate_runs(run_all_scenarios())
    second = evaluate_runs(run_all_scenarios())
    assert first["passed"] and second["passed"]
    assert first["metrics"] == second["metrics"]


def test_multiple_payments_close_one_invoice():
    run = _run("stripe_multiple_payments_one_invoice")
    assert evaluate_runs([run])["cases"][0]["passed"]
    invoice = next(item for item in run["entities"]["invoices"] if item["invoice_id"] == "INV-STR-021")
    assert invoice["outstanding_amount"] == 0
    assert invoice["original_amount"] == 1000.00
    amounts = sorted(item["amount"] for item in run["entities"]["payments"])
    assert amounts == [400.00, 600.00]
    assert run["reconciliation"]["expected_payout_minor"] == (40000 - 1190) + (60000 - 1770)
    assert run["relationships"]["invoice_to_payments"]["INV-STR-021"]


def test_payout_before_bank_matches():
    run = _run("stripe_payout_before_bank")
    assert evaluate_runs([run])["cases"][0]["passed"]
    assert run["reconciliation"]["status"] == "MATCH"
    assert run["reconciliation"]["expected_payout_minor"] == 97070
    assert run["relationships"]["payout_to_bank"][0]["bank_deposit_id"] == "BANK-STR-001"


def test_stripe_object_links_are_traceable():
    pack = build_company_pack()
    charge = next(item for item in pack.charges if item["id"] == "ch_str_001")
    assert charge["balance_transaction"] == "txn_str_001"
    assert charge["payment_intent"] == "pi_str_001"
    refund = next(item for item in pack.refunds if item["id"] == "re_str_005")
    assert refund["charge"] == "ch_str_005"
    assert refund["balance_transaction"] == "txn_str_005_re"
    assert refund["payment_intent"] == "pi_str_005"
    dispute = next(item for item in pack.disputes if item["id"] == "dp_str_006")
    assert dispute["charge"] == "ch_str_006"
    assert [item["id"] for item in dispute["balance_transactions"]] == ["txn_str_006_dp", "txn_str_006_dp_fee"]
    payout = next(item for item in pack.payouts if item["id"] == "po_str_002")
    assert payout["amount"] == 97070 + 145595 + 48520
    deposit = next(item for item in pack.bank_deposits if item["payout_id"] == "po_str_002")
    assert deposit["amount_minor"] == payout["amount"]


def test_journals_balance_and_fee_is_separate():
    run = _run("stripe_simple_payment")
    for row in run["journals"]:
        assert row["debit"]["amount"] == row["credit"]["amount"]
    types = {row["entry_type"] for row in run["journals"]}
    assert "cash_receipt" in types
    assert "processor_fee" in types


def test_payment_intent_created_still_ignored():
    reset_integration_state()
    load_empty_state()
    payload = {
        "id": "evt_pi_created_sim",
        "object": "event",
        "type": "payment_intent.created",
        "created": 1,
        "data": {"object": {"id": "pi_open", "object": "payment_intent"}},
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    result = stripe.process_raw(raw, {"stripe-signature": stripe.sign(raw)})
    assert result.status == "ignored"
    assert all_payouts() == []
    assert all_payments() == []
