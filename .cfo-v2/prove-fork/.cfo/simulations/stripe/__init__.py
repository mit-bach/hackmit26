"""Stripe simulation pack, runtime, and hidden-ground-truth evaluation."""

from simulations.stripe.pack import build_company_pack, scenario_by_id
from simulations.stripe.runtime import run_scenario, run_all_scenarios
from simulations.stripe.eval import evaluate_runs, write_eval_report

__all__ = [
    "build_company_pack",
    "scenario_by_id",
    "run_scenario",
    "run_all_scenarios",
    "evaluate_runs",
    "write_eval_report",
]
