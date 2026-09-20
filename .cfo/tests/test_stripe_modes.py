from __future__ import annotations

import json

from simulations.stripe.classify import SCENARIO_CLASSES, classify_scenario
from simulations.stripe.eval import evaluate_runs, hidden_ground_truth
from simulations.stripe.modes import run_mode, run_three_modes
from simulations.stripe.pack import build_company_pack
from simulations.stripe.runtime import run_scenario


def test_every_scenario_has_a_decision_class():
    pack = build_company_pack()
    ids = {item.scenario_id for item in pack.scenarios}
    assert ids <= set(SCENARIO_CLASSES)
    for scenario_id in ids:
        row = classify_scenario(scenario_id)
        assert row["decision_class"] in {"deterministic", "agentic", "hybrid"}


def test_strict_baseline_fails_missing_metadata_and_ambiguous():
    pack = build_company_pack()
    missing = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_missing_metadata"),
        pack=pack,
        decision_mode="strict",
        memory_enabled=False,
        use_llm=False,
    )
    ambiguous = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_ambiguous_invoice"),
        pack=pack,
        decision_mode="strict",
        memory_enabled=False,
        use_llm=False,
    )
    assert evaluate_runs([missing])["cases"][0]["passed"] is False
    assert evaluate_runs([ambiguous])["cases"][0]["passed"] is False


def test_agentic_memory_off_recovers_context_matches():
    pack = build_company_pack()
    missing = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_missing_metadata"),
        pack=pack,
        decision_mode="agentic",
        memory_enabled=False,
        use_llm=False,
    )
    ambiguous = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_ambiguous_invoice"),
        pack=pack,
        decision_mode="agentic",
        memory_enabled=False,
        use_llm=False,
    )
    assert evaluate_runs([missing])["cases"][0]["passed"] is True
    assert evaluate_runs([ambiguous])["cases"][0]["passed"] is True
    cash = [row for row in missing["agent_invocations"] if row.get("kind") == "cash_apply"]
    assert cash
    assert cash[0]["agent_invoked"] is True
    assert cash[0]["llm_called"] is False
    assert "cash-application" in cash[0]["skills"]
    assert "get_cash_application_facts" in cash[0]["tools_called"]


def test_hidden_ground_truth_is_not_in_agent_evidence():
    pack = build_company_pack()
    run = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_ambiguous_invoice"),
        pack=pack,
        decision_mode="agentic",
        memory_enabled=False,
        use_llm=False,
    )
    blob = json.dumps(run.get("agent_invocations") or [])
    hidden_ground_truth("stripe_ambiguous_invoice")
    assert "expected_net_cents" not in blob
    assert "expected_gl_entries" not in blob
    assert "expected_behavior" not in blob
    assert "expected_ar_effect_cents" not in blob


def test_three_modes_share_hidden_ground_truth():
    payload = run_three_modes()
    comparison = payload["comparison"]
    accuracy = comparison["accuracy_by_scenario"]
    assert "stripe_missing_metadata" in comparison["agents_improve"]
    assert "stripe_ambiguous_invoice" in comparison["agents_improve"]
    assert accuracy["stripe_simple_payment"]["A"] is True
    assert accuracy["stripe_simple_payment"]["C"] is True
    assert accuracy["stripe_bank_discrepancy_1240"]["A"] is True
    assert accuracy["stripe_overpayment"]["A"] is True
    assert "stripe_simple_payment" in comparison["remain_deterministic_by_design"]
    for mode in payload["modes"]:
        assert mode["metrics"]["cases_total"] == len(build_company_pack().scenarios)


def test_default_policy_eval_is_unchanged():
    pack = build_company_pack()
    run = run_scenario(
        next(item for item in pack.scenarios if item.scenario_id == "stripe_simple_payment"),
        pack=pack,
    )
    assert evaluate_runs([run])["cases"][0]["passed"] is True
    assert run["run_mode"]["decision_mode"] == "policy"
