"""Write the reusable Stripe simulation pack for demos and the frontend."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.isolation import evaluation_phase
from simulations.stripe.pack import build_company_pack

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DIR = ROOT / "data" / "simulations" / "stripe"


def persist_pack(dest: Path | None = None) -> Path:
    dest = Path(dest or DEFAULT_DIR)
    dest.mkdir(parents=True, exist_ok=True)
    pack = build_company_pack()
    operational = {
        "manifest": {
            "company": pack.company,
            "period": pack.period,
            "scenario_ids": [item.scenario_id for item in pack.scenarios],
        },
        "customers": pack.customers,
        "invoices": pack.invoices,
        "precedents": pack.precedents,
        "stripe_customers": pack.stripe_customers,
        "payment_intents": pack.payment_intents,
        "charges": pack.charges,
        "refunds": pack.refunds,
        "disputes": pack.disputes,
        "balance_transactions": pack.balance_transactions,
        "payouts": pack.payouts,
        "bank_deposits": pack.bank_deposits,
        "events": pack.events,
        "scenarios": [
            {
                "scenario_id": item.scenario_id,
                "title": item.title,
                "difficulty": item.difficulty,
                "event_ids": [event.get("id") for event in item.events],
                "input_condition": item.ground_truth.input_condition if item.ground_truth else "",
            }
            for item in pack.scenarios
        ],
    }
    for name, payload in operational.items():
        path = dest / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n")
    eval_dir = dest / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    with evaluation_phase():
        (eval_dir / "ground_truth.json").write_text(json.dumps(pack.ground_truth_rows(), indent=2) + "\n")
    return dest
