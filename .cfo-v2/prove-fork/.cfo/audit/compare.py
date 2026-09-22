"""Deterministic comparison of two audit runs using stable issue keys."""

from __future__ import annotations

from audit.models import AuditRun, RunComparison


def _pass_rate(run: AuditRun) -> float:
    total = run.stats.controls_tested
    if not total:
        return 0.0
    return round(run.stats.passed / total, 4)


def _keys(run: AuditRun) -> dict[str, str]:
    return {item.issue_key or f"{item.control_id}:{item.affected_object_ids[0]}": item.finding_id for item in run.findings}


def _unresolved_keys(run: AuditRun) -> set[str]:
    return {item.object_id for item in run.unresolved}


def compare_runs(before: AuditRun, after: AuditRun) -> RunComparison:
    before_keys = _keys(before)
    after_keys = _keys(after)
    before_set = set(before_keys)
    after_set = set(after_keys)
    still_open = sorted(before_set & after_set)
    resolved = sorted(before_set - after_set)
    opened = sorted(after_set - before_set)
    recurring = sorted(
        key
        for key in still_open
        if any(item.issue_key == key and item.recurring for item in after.findings)
    )
    before_hr = _unresolved_keys(before)
    after_hr = _unresolved_keys(after)
    before_rate = _pass_rate(before)
    after_rate = _pass_rate(after)
    return RunComparison(
        before_run_id=before.audit_run_id,
        after_run_id=after.audit_run_id,
        findings_opened=opened,
        findings_resolved=resolved,
        findings_still_open=still_open,
        findings_new=opened,
        recurring=recurring,
        human_review_resolved=sorted(before_hr - after_hr),
        before_pass_rate=before_rate,
        after_pass_rate=after_rate,
        pass_rate_change=round(after_rate - before_rate, 4),
    )


def format_comparison(comparison: RunComparison) -> str:
    def _lines(label: str, rows: list[str]) -> list[str]:
        return [f"{label}: {len(rows)}"] + [f"  - {item}" for item in rows] or [f"{label}: 0"]

    return "\n".join(
        [
            f"AUDIT RUN COMPARISON  {comparison.before_run_id} → {comparison.after_run_id}",
            *_lines("Findings opened / new", comparison.findings_new),
            *_lines("Findings resolved", comparison.findings_resolved),
            *_lines("Findings still open", comparison.findings_still_open),
            *_lines("Recurring findings", comparison.recurring),
            *_lines("Human-review items resolved", comparison.human_review_resolved),
            f"Control pass rate: {comparison.before_pass_rate:.2%} → {comparison.after_pass_rate:.2%} "
            f"({comparison.pass_rate_change:+.2%})",
        ]
    )
