"""Three-mode Stripe evaluation against the same hidden ground truth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from evaluation.isolation import evaluation_phase
from simulations.stripe.classify import classify_scenario
from simulations.stripe.eval import evaluate_runs
from simulations.stripe.runtime import run_all_scenarios

MODE_SPECS = (
    {
        "mode_id": "A",
        "title": "deterministic-only baseline",
        "decision_mode": "strict",
        "memory_enabled": False,
        "use_llm": False,
    },
    {
        "mode_id": "B",
        "title": "agentic system with memory disabled",
        "decision_mode": "agentic",
        "memory_enabled": False,
        "use_llm": None,
    },
    {
        "mode_id": "C",
        "title": "full agentic system with memory enabled",
        "decision_mode": "agentic",
        "memory_enabled": True,
        "use_llm": None,
    },
)


def _llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def run_mode(spec: dict[str, Any]) -> dict[str, Any]:
    use_llm = spec["use_llm"]
    if use_llm is None:
        use_llm = _llm_available() and spec["decision_mode"] == "agentic"
    runs = run_all_scenarios(
        decision_mode=spec["decision_mode"],
        memory_enabled=spec["memory_enabled"],
        use_llm=use_llm,
    )
    with evaluation_phase():
        graded = evaluate_runs(runs)
    by_id = {row["scenario_id"]: row for row in graded["cases"]}
    return {
        "mode_id": spec["mode_id"],
        "title": spec["title"],
        "decision_mode": spec["decision_mode"],
        "memory_enabled": spec["memory_enabled"],
        "llm_available": _llm_available(),
        "llm_used": bool(use_llm),
        "passed": graded["passed"],
        "metrics": graded["metrics"],
        "cases": [
            {
                "scenario_id": row["scenario_id"],
                "passed": row["passed"],
                "decision_class": classify_scenario(row["scenario_id"])["decision_class"],
                "notes": row.get("notes") or [],
            }
            for row in graded["cases"]
        ],
        "runs": runs,
        "graded": by_id,
    }


def compare_modes(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_mode = {row["mode_id"]: row for row in results}
    scenario_ids = [item["scenario_id"] for item in by_mode["A"]["cases"]]
    accuracy = {}
    agents_improve = []
    memory_improves = []
    remain_deterministic = []
    for scenario_id in scenario_ids:
        a = next(item for item in by_mode["A"]["cases"] if item["scenario_id"] == scenario_id)
        b = next(item for item in by_mode["B"]["cases"] if item["scenario_id"] == scenario_id)
        c = next(item for item in by_mode["C"]["cases"] if item["scenario_id"] == scenario_id)
        klass = classify_scenario(scenario_id)["decision_class"]
        accuracy[scenario_id] = {
            "class": klass,
            "A": a["passed"],
            "B": b["passed"],
            "C": c["passed"],
        }
        if (not a["passed"]) and b["passed"]:
            agents_improve.append(scenario_id)
        if (not b["passed"]) and c["passed"]:
            memory_improves.append(scenario_id)
        if klass == "deterministic" and a["passed"] and b["passed"] and c["passed"]:
            remain_deterministic.append(scenario_id)
    return {
        "accuracy_by_scenario": accuracy,
        "agents_improve": agents_improve,
        "memory_improves": memory_improves,
        "remain_deterministic_by_design": remain_deterministic,
        "llm_available": _llm_available(),
    }


def run_three_modes() -> dict[str, Any]:
    results = [run_mode(spec) for spec in MODE_SPECS]
    comparison = compare_modes(results)
    return {
        "modes": [
            {key: row[key] for key in row if key not in {"runs", "graded"}}
            for row in results
        ],
        "comparison": comparison,
        "runs_by_mode": {row["mode_id"]: row["runs"] for row in results},
    }


def format_modes_table(payload: dict[str, Any]) -> str:
    lines = [
        "Stripe three-mode evaluation",
        "",
        f"{'scenario':<36} {'class':<14} {'A':<6} {'B':<6} {'C':<6}",
    ]
    for scenario_id, row in (payload.get("comparison") or {}).get("accuracy_by_scenario", {}).items():
        lines.append(
            f"{scenario_id:<36} {row['class']:<14} "
            f"{'PASS' if row['A'] else 'FAIL':<6} "
            f"{'PASS' if row['B'] else 'FAIL':<6} "
            f"{'PASS' if row['C'] else 'FAIL':<6}"
        )
    comparison = payload.get("comparison") or {}
    lines.append("")
    lines.append("Agents improve: " + ", ".join(comparison.get("agents_improve") or []) or "Agents improve: (none)")
    lines.append("Memory improves: " + ", ".join(comparison.get("memory_improves") or []) or "Memory improves: (none)")
    lines.append(
        "Deterministic by design: "
        + ", ".join(comparison.get("remain_deterministic_by_design") or [])
    )
    lines.append(f"LLM available: {comparison.get('llm_available')}")
    for mode in payload.get("modes") or []:
        metrics = mode.get("metrics") or {}
        lines.append(
            f"Mode {mode['mode_id']} {mode['title']}: "
            f"{metrics.get('cases_passed', 0)}/{metrics.get('cases_total', 0)} "
            f"llm_used={mode.get('llm_used')}"
        )
    return "\n".join(lines)


def write_modes_report(payload: dict[str, Any], dest: Path) -> Path:
    import json

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    slim = {key: value for key, value in payload.items() if key != "runs_by_mode"}
    dest.write_text(json.dumps(slim, indent=2, default=str) + "\n")
    return dest
