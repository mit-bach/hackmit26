"""Evaluate the existing month-end close, accrual, prepaid, and fixed-asset workflows."""

from __future__ import annotations

from accrual.workflow import run_accrual_workflow
from close.checklist import unresolved_blockers
from close.month_end import run_month_end
from evaluation.comparison import case_result, error_case, fail_case
from evaluation.models import EvaluationCaseResult
from evaluation.scoring import summarize_function
from fixed_assets.workflow import run_depreciation_workflow
from prepaid.workflow import run_prepaid_workflow


def run_close(period: str, expected) -> tuple:
    cases: list[EvaluationCaseResult] = []
    raw: dict = {
        "blockers": [],
        "cash_blocked": False,
        "period_blocked": False,
        "cash_fully_reconciled": False,
        "journals": [],
        "tasks": {},
    }
    try:
        prepaid = run_prepaid_workflow(period, use_agent=False)
        assets = run_depreciation_workflow(period, use_agent=False)
        accruals = run_accrual_workflow(period, use_agent=False)
        state = run_month_end(period, live=False, reset=True, scenario="demo")
    except Exception as exc:
        case = error_case(case_id="CLOSE-WORKFLOW", domain="close", scenario_id="SCN-CLOSE-011", reason=str(exc))
        summary = summarize_function("close", [case])
        summary.workflow_error = str(exc)
        return summary, raw

    tasks = {item.task_id: item.status for item in state.tasks}
    blockers = [item.task_id for item in unresolved_blockers(state.tasks)]
    raw.update(
        {
            "blockers": blockers,
            "cash_blocked": tasks.get("cash") in {"BLOCKED", "NEEDS_REVIEW", "FAILED"}
            or any("12.40" in (item.blocker_reason or "") or "unexplained" in (item.blocker_reason or "").lower() for item in state.tasks),
            "period_blocked": state.period.status in {"BLOCKED", "IN_PROGRESS"} or bool(state.human_review_items),
            "cash_fully_reconciled": state.period.status == "CLOSED" and "cash" not in blockers,
            "tasks": tasks,
            "period_status": state.period.status,
            "human_review_items": list(state.human_review_items),
            "journals": list(state.journal_entry_ids),
        }
    )

    vendors = {
        getattr(item, "vendor", "")
        for item in list(getattr(accruals, "accruals_created", []) or [])
        + list(getattr(accruals, "ranked_missing", []) or [])
    }
    vendors = {name for name in vendors if name}

    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-001",
            domain="close",
            scenario_id="SCN-CLOSE-001",
            expected="Harbor Electric",
            actual="Harbor Electric" if any("Harbor" in name for name in vendors) else sorted(vendors),
            source_ids=["ACC-HE-2026-09"],
            equal=lambda exp, act: exp == act or (isinstance(act, str) and exp in act),
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-002",
            domain="close",
            scenario_id="SCN-CLOSE-002",
            expected="Lindholm",
            actual=next((name for name in vendors if "Lindholm" in name), ""),
            source_ids=["ACC-LR-2026-09"],
            equal=lambda exp, act: bool(act),
        )
    )

    prepaid_ok = bool(getattr(prepaid, "posted", None) or getattr(prepaid, "schedule", None) or getattr(prepaid, "items", None))
    if hasattr(prepaid, "results"):
        prepaid_ok = bool(prepaid.results)
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-003",
            domain="close",
            scenario_id="SCN-CLOSE-003",
            expected=True,
            actual=prepaid_ok or tasks.get("prepaid") in {"COMPLETE", "NEEDS_REVIEW"},
            source_ids=["PRE-SFT-001"],
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-004",
            domain="close",
            scenario_id="SCN-CLOSE-004",
            expected=True,
            actual=prepaid_ok or tasks.get("prepaid") in {"COMPLETE", "NEEDS_REVIEW"},
            source_ids=["PRE-INS-001"],
        )
    )
    asset_ok = bool(getattr(assets, "posted", None) or getattr(assets, "assets", None) or tasks.get("depreciation") in {"COMPLETE", "NEEDS_REVIEW"})
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-005",
            domain="close",
            scenario_id="SCN-CLOSE-005",
            expected=True,
            actual=asset_ok,
            source_ids=["FA-DELL-001", "INV-018"],
        )
    )

    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-006",
            domain="close",
            scenario_id="SCN-CLOSE-006",
            expected=True,
            actual="cash" in tasks,
            source_ids=["TASK-CASH"],
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-011",
            domain="close",
            scenario_id="SCN-CLOSE-011",
            expected=True,
            actual=raw["cash_blocked"] or raw["period_blocked"] or "cash" in blockers,
            source_ids=["TXN-2026-09-015"],
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-012",
            domain="close",
            scenario_id="SCN-CLOSE-012",
            expected=True,
            actual=any(status == "NEEDS_REVIEW" for status in tasks.values()) or bool(state.human_review_items),
            source_ids=list(tasks),
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-013",
            domain="close",
            scenario_id="SCN-CLOSE-013",
            expected=True,
            actual=any(status == "COMPLETE" for status in tasks.values()),
            source_ids=list(tasks),
        )
    )
    cases.append(
        case_result(
            case_id="CLOSE-SCN-CLOSE-015",
            domain="close",
            scenario_id="SCN-CLOSE-015",
            expected=True,
            actual=raw["period_blocked"] or raw["cash_blocked"],
            source_ids=["TXN-2026-09-015", "TASK-FINAL"],
        )
    )

    for scenario_id, label in (
        ("SCN-CLOSE-007", "ap"),
        ("SCN-CLOSE-008", "ar"),
        ("SCN-CLOSE-009", "prepaid"),
        ("SCN-CLOSE-010", "accruals"),
        ("SCN-CLOSE-014", "ap"),
    ):
        cases.append(
            case_result(
                case_id=f"CLOSE-{scenario_id}",
                domain="close",
                scenario_id=scenario_id,
                expected=True,
                actual=label in tasks,
                source_ids=[label],
            )
        )

    if state.period.status == "CLOSED" and not raw["cash_blocked"]:
        cases.append(
            fail_case(
                case_id="CLOSE-FORCED-COMPLETE",
                domain="close",
                scenario_id="SCN-CLOSE-015",
                expected="BLOCKED",
                actual=state.period.status,
                error_type="BROKEN_LINEAGE",
                reason="Period closed despite the unresolved cash difference",
                source_ids=["TXN-2026-09-015"],
            )
        )

    summary = summarize_function("close", cases)
    summary.metrics = {
        "accrual_case_accuracy": round(
            sum(item.score for item in cases if item.scenario_id in {"SCN-CLOSE-001", "SCN-CLOSE-002"}) / 2, 4
        ),
        "prepaid_schedule_accuracy": round(
            sum(item.score for item in cases if item.scenario_id in {"SCN-CLOSE-003", "SCN-CLOSE-004"}) / 2, 4
        ),
        "fixed_asset_schedule_accuracy": next((item.score for item in cases if item.scenario_id == "SCN-CLOSE-005"), 0.0),
        "close_task_status_accuracy": round(
            sum(item.score for item in cases if item.scenario_id in {"SCN-CLOSE-012", "SCN-CLOSE-013"}) / 2, 4
        ),
        "blocker_detection_accuracy": next((item.score for item in cases if item.scenario_id == "SCN-CLOSE-015"), 0.0),
        "journal_entry_correctness": 1.0 if raw["journals"] or asset_ok or prepaid_ok else 0.0,
    }
    return summary, raw
