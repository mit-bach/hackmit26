"""Compare gauntlet modes without fabricating results."""

from __future__ import annotations

from typing import Any

from evals.maximor_finance_gauntlet.runner import run_gauntlet, write_gauntlet


def run_modes(*, include_existing: bool = False) -> dict[str, Any]:
    """A = current/full, B = memory off, C = shared state off, D = full upgraded."""
    specs = [
        {"mode_id": "B", "title": "Memory disabled", "memory_enabled": False, "shared_state": True},
        {"mode_id": "C", "title": "Shared canonical state reduced", "memory_enabled": True, "shared_state": False},
        {"mode_id": "A", "title": "Current Maximor (memory on, shared state on)", "memory_enabled": True, "shared_state": True},
        {"mode_id": "D", "title": "Full upgraded Maximor", "memory_enabled": True, "shared_state": True},
    ]
    modes = []
    for spec in specs:
        payload = run_gauntlet(
            memory_enabled=spec["memory_enabled"],
            shared_state=spec["shared_state"],
            include_existing=include_existing,
        )
        modes.append(
            {
                "mode_id": spec["mode_id"],
                "title": spec["title"],
                "memory_enabled": spec["memory_enabled"],
                "shared_state": spec["shared_state"],
                "scorecard": payload["scorecard"],
                "run_id": payload["run_id"],
            }
        )
    by_id = {item["mode_id"]: item for item in modes}
    comparison = {
        "memory_on_vs_off": {
            "on": (by_id["A"]["scorecard"] or {}).get("memory_correctness"),
            "off": (by_id["B"]["scorecard"] or {}).get("memory_correctness"),
            "long_horizon_on": (by_id["A"]["scorecard"] or {}).get("long_horizon_accuracy"),
            "long_horizon_off": (by_id["B"]["scorecard"] or {}).get("long_horizon_accuracy"),
        },
        "shared_state_on_vs_off": {
            "on": (by_id["A"]["scorecard"] or {}).get("cross_workflow_consistency"),
            "off": (by_id["C"]["scorecard"] or {}).get("cross_workflow_consistency"),
        },
    }
    result = {"modes": modes, "comparison": comparison}
    write_gauntlet(
        {"modes": True, **result},
        dest=__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "runs" / "evals" / "maximor_finance_gauntlet_modes.json",
    )
    return result
