"""Explicit month-end close dependency graph. Not a single sequential function."""

from __future__ import annotations

from close.models import CloseTask

TASK_SPECS: list[dict] = [
    {
        "task_id": "ingest",
        "category": "ingestion",
        "description": "Ingest documents",
        "owner_agent": "Email Invoice Agent",
        "dependencies": [],
    },
    {
        "task_id": "ap",
        "category": "ap",
        "description": "AP processing",
        "owner_agent": "AP Preparer",
        "dependencies": ["ingest"],
    },
    {
        "task_id": "ar",
        "category": "ar",
        "description": "AR processing",
        "owner_agent": "Collections Agent",
        "dependencies": ["ingest"],
    },
    {
        "task_id": "cash",
        "category": "cash",
        "description": "Cash reconciliation",
        "owner_agent": "Cash Reconciliation Preparer",
        "dependencies": ["ingest"],
        "requires_review": True,
        "reviewer": "Cash Reconciliation Reviewer",
    },
    {
        "task_id": "accruals",
        "category": "accruals",
        "description": "Accruals",
        "owner_agent": "Accrual Agent",
        "dependencies": ["ap"],
    },
    {
        "task_id": "prepaid",
        "category": "prepaid",
        "description": "Prepaid amortization",
        "owner_agent": "Prepaid Preparer",
        "dependencies": ["ap"],
        "requires_review": True,
        "reviewer": "Prepaid Reviewer",
    },
    {
        "task_id": "depreciation",
        "category": "fixed_assets",
        "description": "Depreciation",
        "owner_agent": "Fixed Asset Preparer",
        "dependencies": ["ap"],
        "requires_review": True,
        "reviewer": "Fixed Asset Reviewer",
    },
    {
        "task_id": "bs_recon",
        "category": "reconciliation",
        "description": "Balance-sheet reconciliations",
        "owner_agent": "Balance Sheet Reconciliation Preparer",
        "dependencies": ["cash", "accruals", "prepaid", "depreciation", "ar", "ap"],
        "requires_review": True,
        "reviewer": "Balance Sheet Reconciliation Reviewer",
    },
    {
        "task_id": "exceptions",
        "category": "review",
        "description": "Review unresolved exceptions",
        "owner_agent": "Month-End Close Reviewer",
        "dependencies": ["bs_recon"],
        "requires_review": True,
        "reviewer": "Month-End Close Reviewer",
    },
    {
        "task_id": "final_review",
        "category": "review",
        "description": "Final review",
        "owner_agent": "Month-End Close Reviewer",
        "dependencies": ["exceptions"],
        "requires_review": True,
        "reviewer": "Month-End Close Reviewer",
    },
    {
        "task_id": "mark_closed",
        "category": "close",
        "description": "Mark period closed",
        "owner_agent": "Month-End Close Reviewer",
        "dependencies": ["final_review"],
    },
]

BLOCKING_UPSTREAM = {"BLOCKED", "FAILED", "NEEDS_REVIEW"}


def build_tasks(period: str) -> list[CloseTask]:
    return [
        CloseTask(
            task_id=spec["task_id"],
            period=period,
            category=spec["category"],
            description=spec["description"],
            owner_agent=spec["owner_agent"],
            owner_role=spec.get("reviewer") or spec["owner_agent"],
            task_type=spec["category"],
            dependencies=list(spec["dependencies"]),
            requires_review=bool(spec.get("requires_review")),
            reviewer=spec.get("reviewer", ""),
        )
        for spec in TASK_SPECS
    ]


def task_map(tasks: list[CloseTask]) -> dict[str, CloseTask]:
    return {item.task_id: item for item in tasks}


def refresh_readiness(tasks: list[CloseTask]) -> list[CloseTask]:
    by_id = task_map(tasks)
    for task in tasks:
        if task.status in {"COMPLETE", "RUNNING", "NEEDS_REVIEW", "FAILED"}:
            continue
        deps = [by_id[dep] for dep in task.dependencies if dep in by_id]
        if any(dep.status in {"NEEDS_REVIEW", "FAILED"} for dep in deps) and all(
            dep.status in {"COMPLETE", "NEEDS_REVIEW", "FAILED"} for dep in deps
        ):
            blockers = [dep.task_id for dep in deps if dep.status in {"NEEDS_REVIEW", "FAILED"}]
            task.status = "BLOCKED"
            task.blocker_reason = "Upstream unresolved: " + ", ".join(blockers)
            continue
        if any(dep.status != "COMPLETE" for dep in deps):
            task.status = "NOT_STARTED"
            if any(dep.status == "BLOCKED" for dep in deps):
                task.blocker_reason = "Waiting on blocked upstream work"
            else:
                task.blocker_reason = ""
            continue
        task.blocker_reason = ""
        task.status = "READY"
    return tasks


def ready_tasks(tasks: list[CloseTask]) -> list[CloseTask]:
    order = [spec["task_id"] for spec in TASK_SPECS]
    ready = [item for item in tasks if item.status in {"READY", "FAILED"}]
    ready.sort(key=lambda item: order.index(item.task_id) if item.task_id in order else 99)
    return [item for item in ready if item.status == "READY"]


def completion_pct(tasks: list[CloseTask]) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for item in tasks if item.status == "COMPLETE")
    return round(100.0 * done / len(tasks), 1)


def unresolved_blockers(tasks: list[CloseTask]) -> list[CloseTask]:
    return [item for item in tasks if item.status in {"BLOCKED", "FAILED", "NEEDS_REVIEW"}]
