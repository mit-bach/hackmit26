"""Deterministic month-end close evaluation. Agents do not score these metrics."""

from __future__ import annotations

from close.checklist import unresolved_blockers
from close.ledger import load_entries, replay_hit_count
from close.models import CloseEvalMetrics, MonthEndState
from close.month_end import load_state, run_month_end
from close.period_lock import load_events
from close.snapshot import list_snapshots
from bs_recon.store import load_reconciliations


def evaluate_close(period: str, *, state: MonthEndState | None = None) -> CloseEvalMetrics:
    current = state or load_state(period) or run_month_end(period, live=False, reset=False)
    recs = load_reconciliations(period)
    approved = [item for item in recs if item.status in {"SIGNED_OFF", "MATCHED", "EXPLAINED_DIFFERENCE"}]
    failed = [item for item in recs if item.status in {"HUMAN_REVIEW", "BLOCKED"}]
    entries = [item for item in load_entries() if item.get("period") == period]
    duplicate_prevented = replay_hit_count()
    tied = 0
    for item in recs:
        if abs(item.difference) < 0.005 or item.status in {"SIGNED_OFF", "MATCHED", "EXPLAINED_DIFFERENCE"}:
            tied += 1
        elif item.reconciling_items:
            tied += 1
    accuracy = round(100.0 * tied / len(recs), 1) if recs else 100.0
    snapshots = list_snapshots(period)
    expected_blocked = bool(current.human_review_items) or bool(unresolved_blockers(current.tasks))
    if current.period.status == "CLOSED":
        status_ok = not expected_blocked
    elif current.period.status == "BLOCKED":
        status_ok = expected_blocked
    else:
        status_ok = True
    return CloseEvalMetrics(
        period=period,
        required_tasks=len(current.tasks),
        completed_tasks=sum(1 for item in current.tasks if item.status == "COMPLETE"),
        blocked_tasks=len(unresolved_blockers(current.tasks)),
        approved_reconciliations=len(approved),
        failed_reconciliations=len(failed),
        human_review_items=len(current.human_review_items),
        journal_proposals=len(entries),
        duplicate_journal_attempts_prevented=max(0, duplicate_prevented - len(entries)),
        account_tie_out_accuracy=accuracy,
        close_status=current.period.status,
        close_status_correct=status_ok,
        audit_trace_complete=bool(current.trace_path),
        snapshot_persisted=bool(snapshots) if current.period.status == "CLOSED" else True,
    )


def format_eval(metrics: CloseEvalMetrics) -> str:
    lines = [
        f"CLOSE EVALUATION — {metrics.period}",
        "",
        f"Required close tasks: {metrics.required_tasks}",
        f"Completed tasks: {metrics.completed_tasks}",
        f"Blocked tasks: {metrics.blocked_tasks}",
        f"Approved account reconciliations: {metrics.approved_reconciliations}",
        f"Failed reconciliations: {metrics.failed_reconciliations}",
        f"HUMAN_REVIEW items: {metrics.human_review_items}",
        f"Journal proposals generated: {metrics.journal_proposals}",
        f"Duplicate journal attempts prevented: {metrics.duplicate_journal_attempts_prevented}",
        f"Account tie-out accuracy: {metrics.account_tie_out_accuracy:.1f}%",
        f"Close status: {metrics.close_status}",
        f"Close-status correctness: {'PASS' if metrics.close_status_correct else 'FAIL'}",
        f"Audit-trace completeness: {'PASS' if metrics.audit_trace_complete else 'FAIL'}",
        f"Snapshot persisted: {'yes' if metrics.snapshot_persisted else 'no'}",
    ]
    return "\n".join(lines)
