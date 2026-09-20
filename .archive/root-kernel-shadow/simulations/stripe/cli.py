"""CLI for Stripe simulation and hidden-ground-truth evaluation."""

from __future__ import annotations

import json
from pathlib import Path

from simulations.stripe.eval import evaluate_runs, format_eval_table, write_eval_report
from simulations.stripe.persist import persist_pack
from simulations.stripe.runtime import isolated_simulation, run_all_scenarios

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUNS = ROOT / "runs" / "evals"


def _write_outputs(dest: Path, runs: list[dict], payload: dict) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    viz = dest / "visualization"
    viz.mkdir(parents=True, exist_ok=True)
    for run in runs:
        (viz / f"{run['scenario_id']}.json").write_text(json.dumps(run, indent=2, default=str) + "\n")
    (viz / "index.json").write_text(
        json.dumps(
            {
                "scenarios": [item["scenario_id"] for item in runs],
                "results": [item["result"] for item in runs],
                "metrics": payload.get("metrics") or {},
            },
            indent=2,
        )
        + "\n"
    )
    write_eval_report(payload, dest / "stripe_simulation.json")
    write_eval_report(payload, DEFAULT_RUNS / "stripe_simulation.json")


def run_simulate(argv: list[str] | None = None) -> int:
    dest = DEFAULT_RUNS / "stripe_simulation"
    persist_pack()
    dest.mkdir(parents=True, exist_ok=True)
    with isolated_simulation(dest / "state"):
        runs = run_all_scenarios(persist_root=dest)
    payload = evaluate_runs(runs)
    _write_outputs(dest, runs, payload)
    print(f"Simulated {len(runs)} Stripe scenarios.")
    print("Wrote pack to data/simulations/stripe/")
    print(f"Wrote visualization to {dest / 'visualization'}")
    print(f"Wrote {DEFAULT_RUNS / 'stripe_simulation.json'}")
    return 0 if payload["passed"] else 1


def run_eval(argv: list[str] | None = None) -> int:
    dest = DEFAULT_RUNS / "stripe_simulation"
    dest.mkdir(parents=True, exist_ok=True)
    with isolated_simulation(dest / "state"):
        runs = run_all_scenarios(persist_root=dest)
    payload = evaluate_runs(runs)
    _write_outputs(dest, runs, payload)
    print(format_eval_table(payload))
    print(f"\nWrote {dest / 'stripe_simulation.json'}")
    print(f"Wrote {DEFAULT_RUNS / 'stripe_simulation.json'}")
    return 0 if payload["passed"] else 1
