"""Human-readable audit report generated from structured stats. Counts come from Python."""

from __future__ import annotations

from audit.models import AuditFinding, AuditRun, ReportStats, ReperformanceRecord


def compute_stats(run: AuditRun) -> ReportStats:
    passed = sum(1 for item in run.controls if item.result == "PASS")
    failed = sum(1 for item in run.controls if item.result == "FAIL")
    exceptions = sum(1 for item in run.controls if item.result == "EXCEPTION")
    human_review = sum(1 for item in run.controls if item.result == "HUMAN_REVIEW")
    not_tested = sum(1 for item in run.controls if item.result == "NOT_TESTED")
    populations = {sample.population_name: sample.population_size for sample in run.samples}
    return ReportStats(
        period=run.period,
        audit_run_id=run.audit_run_id,
        scope=list(run.scope),
        populations=populations,
        sampling=[
            {
                "sample_id": sample.sample_id,
                "population": sample.population_name,
                "method": sample.sampling_method,
                "seed": sample.seed,
                "sample_size": sample.sample_size,
                "population_size": sample.population_size,
                "sampled_ids": list(sample.sampled_ids),
            }
            for sample in run.samples
        ],
        controls_tested=len(run.controls),
        passed=passed,
        failed=failed,
        exceptions=exceptions,
        human_review=human_review,
        not_tested=not_tested,
        finding_count=len(run.findings),
        unresolved_count=len(run.unresolved),
        reperformance_count=len(run.reperformance),
        reperformance_agreed=sum(1 for item in run.reperformance if item.agreed),
        reperformance_disagreed=sum(1 for item in run.reperformance if not item.agreed),
        finding_ids=[item.finding_id for item in run.findings],
        control_results={item.control_id: item.result for item in run.controls},
    )


def _money(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def format_findings(findings: list[AuditFinding]) -> list[str]:
    if not findings:
        return ["(none)"]
    lines = []
    for item in findings:
        lines.extend(
            [
                f"- {item.finding_id}  {item.severity}  {item.result}  {item.control_id}",
                f"  {item.title}",
                f"  objects: {', '.join(item.affected_object_ids) or '(none)'}",
                f"  evidence: {', '.join(item.evidence_ids) or '(none)'}",
                f"  exposure: {_money(item.monetary_exposure)}",
                f"  follow-up: {item.recommended_follow_up}",
                f"  issue: {item.issue_key or '(none)'}{'  RECURRING' if item.recurring else ''}",
                f"  severity rationale: {item.severity_rationale}",
            ]
        )
    return lines


def format_reperformance(rows: list[ReperformanceRecord]) -> list[str]:
    if not rows:
        return ["(none)"]
    lines = []
    for item in rows:
        agreement = "AGREE" if item.agreed else "DISAGREE"
        lines.append(
            f"- {item.reconciliation_id}  {item.recon_type}  {agreement}  {item.result}  "
            f"tolerance={item.tolerance}  used_original_as_input={str(item.used_original_as_input).lower()}"
        )
        if item.differences:
            lines.append(f"  differences: {'; '.join(item.differences)}")
        lines.append(f"  evidence: {', '.join(item.evidence_trace) or '(none)'}")
    return lines


def format_audit_report(run: AuditRun) -> str:
    stats = run.stats
    sample_lines = []
    for row in stats.sampling:
        sample_lines.append(
            f"- {row['population']}: {row['method']} seed={row['seed']} "
            f"{row['sample_size']}/{row['population_size']} → {', '.join(row['sampled_ids']) or '(none)'}"
        )
    control_lines = [
        f"- {item.control_id}  {item.control_name}  {item.result}  tested={len(item.tested_ids)}"
        for item in run.controls
    ]
    unresolved_lines = [
        f"- {item.object_id}  {item.result}  {item.detail}" for item in run.unresolved
    ] or ["(none)"]
    populations = [f"- {name}: {count}" for name, count in stats.populations.items()] or ["(none)"]
    return "\n".join(
        [
            f"INDEPENDENT AUDIT REPORT — {stats.period}",
            f"Audit run: {stats.audit_run_id}",
            "",
            "SCOPE",
            *([f"- {item}" for item in stats.scope] or ["- (none)"]),
            "",
            "POPULATIONS EXAMINED",
            *populations,
            "",
            "SAMPLING METHODOLOGY",
            *(sample_lines or ["(none)"]),
            "",
            "CONTROLS TESTED",
            *(control_lines or ["(none)"]),
            "",
            "RESULTS",
            f"Passed: {stats.passed}",
            f"Failed: {stats.failed}",
            f"Exceptions: {stats.exceptions}",
            f"Human review: {stats.human_review}",
            f"Not tested: {stats.not_tested}",
            f"Findings: {stats.finding_count}",
            f"Unresolved items: {stats.unresolved_count}",
            "",
            "RECONCILIATION RE-PERFORMANCE",
            f"Agreed: {stats.reperformance_agreed}",
            f"Disagreed: {stats.reperformance_disagreed}",
            *format_reperformance(run.reperformance),
            "",
            "FINDINGS",
            *format_findings(run.findings),
            "",
            "UNRESOLVED ITEMS",
            *unresolved_lines,
            "",
            "EVIDENCE REFERENCES",
            f"Finding IDs: {', '.join(stats.finding_ids) or '(none)'}",
            f"Trace: {run.trace_path or '(in-memory)'}",
            f"Source records mutated: {str(run.source_records_mutated).lower()}",
        ]
    )
