"""Deterministic evaluation of planted audit cases and runtime mutations."""

from __future__ import annotations

from audit.dataset import FALSE_POSITIVE_GUARD_IDS
from audit.evidence import evidence_completeness
from audit.models import AuditRun, EvaluationMetrics, RunComparison
from audit.store import load_ground_truth


def _finding_object_ids(run: AuditRun) -> set[str]:
    found: set[str] = set()
    for item in run.findings:
        found.update(item.affected_object_ids)
        found.update(item.payment_ids)
        found.update(item.invoice_ids)
        found.update(item.vendor_ids)
        found.update(item.approval_ids)
        found.update(item.journal_entry_ids)
        found.update(item.reconciliation_ids)
    return found


def evaluate_mutations(run: AuditRun, mutations) -> tuple[int, int, list[str], list[str]]:
    by_control: dict[str, set[str]] = {}
    for finding in run.findings:
        ids = set(
            finding.affected_object_ids
            + finding.payment_ids
            + finding.invoice_ids
            + finding.vendor_ids
            + finding.approval_ids
            + finding.journal_entry_ids
            + finding.reconciliation_ids
        )
        by_control.setdefault(finding.control_id, set()).update(ids)
    expected = [item for item in mutations if getattr(item, "expected_detect", True)]
    detected = [
        item.mutation_id
        for item in expected
        if item.object_id in by_control.get(item.control_id, set())
    ]
    missed = [
        item.mutation_id
        for item in expected
        if item.object_id not in by_control.get(item.control_id, set())
    ]
    return len(expected), len(detected), detected, missed


def evaluate_run(
    run: AuditRun,
    ground_truth: dict | None = None,
    *,
    mutations=None,
    independence: list[dict] | None = None,
    trace: dict | None = None,
    comparison: RunComparison | None = None,
) -> EvaluationMetrics:
    truth = ground_truth if ground_truth is not None else load_ground_truth()
    planted = list(truth.get("planted_exceptions") or [])
    planted_ids = [item["object_id"] for item in planted]
    expected_pass = [item["object_id"] for item in truth.get("expected_pass") or []]
    found_ids = _finding_object_ids(run)
    detected = [item for item in planted_ids if item in found_ids]
    missed = [item for item in planted_ids if item not in found_ids]
    extra = [
        item
        for item in sorted(found_ids)
        if item not in planted_ids and item not in expected_pass
    ]
    # Extra IDs that are related peers of a planted case are not false positives.
    planted_set = set(planted_ids)
    related_ok = set()
    for finding in run.findings:
        if planted_set & set(finding.affected_object_ids + finding.invoice_ids + finding.vendor_ids + finding.reconciliation_ids + finding.approval_ids + finding.payment_ids + finding.journal_entry_ids):
            related_ok.update(finding.affected_object_ids)
            related_ok.update(finding.invoice_ids)
            related_ok.update(finding.vendor_ids)
    extra = [item for item in extra if item not in related_ok and item not in expected_pass]
    true_positives = len(detected)
    false_negatives = len(missed)
    false_positives = len(extra)
    detection_rate = true_positives / len(planted_ids) if planted_ids else 1.0
    expected_agree = {
        item["object_id"]
        for item in planted
        if item.get("kind") == "recon_agreement"
    }
    expected_disagree = {
        item["object_id"]
        for item in planted
        if item.get("kind") == "recon_disagreement"
    }
    recon_correct = 0
    recon_total = 0
    for record in run.reperformance:
        if record.reconciliation_id in expected_agree:
            recon_total += 1
            recon_correct += int(record.agreed)
        elif record.reconciliation_id in expected_disagree:
            recon_total += 1
            recon_correct += int(not record.agreed)
        else:
            recon_total += 1
            recon_correct += int(record.agreed == (not any(
                record.reconciliation_id == item["object_id"] and item.get("kind") == "recon_disagreement"
                for item in planted
            )))
    # Also count expected-pass recon IDs from truth.
    for item in truth.get("expected_pass") or []:
        if item.get("control_id") == "AUD-REPERF-001":
            record = next((row for row in run.reperformance if row.reconciliation_id == item["object_id"]), None)
            if record is not None:
                pass
    evidence_complete, evidence_total = evidence_completeness(run)
    completeness = evidence_complete / evidence_total if evidence_total else 1.0
    injected = detected_mutations = 0
    mutation_rate = 0.0
    if mutations:
        injected, detected_mutations, _detected_names, _missed_names = evaluate_mutations(run, mutations)
        mutation_rate = detected_mutations / injected if injected else 1.0
        mutation_objects = {item.object_id for item in mutations if getattr(item, "expected_detect", True)}
        if not planted_ids:
            planted_ids = [item.object_id for item in mutations if getattr(item, "expected_detect", True)]
            detected = [item for item in planted_ids if item in found_ids]
            missed = [item for item in planted_ids if item not in found_ids]
            true_positives = len(detected)
            false_negatives = len(missed)
            detection_rate = true_positives / len(planted_ids) if planted_ids else 1.0
            related_ok = set()
            expected_set = set(planted_ids)
            for finding in run.findings:
                ids = set(
                    finding.affected_object_ids
                    + finding.invoice_ids
                    + finding.vendor_ids
                    + finding.reconciliation_ids
                    + finding.approval_ids
                    + finding.payment_ids
                    + finding.journal_entry_ids
                )
                if expected_set & ids:
                    related_ok.update(ids)
            extra = [
                item
                for item in sorted(found_ids)
                if item not in expected_set
                and item not in related_ok
                and item not in expected_pass
            ]
            false_positives = len(extra)
            disagree_ids = {
                item.object_id for item in mutations if item.control_id == "AUD-REPERF-001" and item.expected_detect
            }
            recon_correct = 0
            recon_total = 0
            for record in run.reperformance:
                recon_total += 1
                recon_correct += int(record.agreed == (record.reconciliation_id not in disagree_ids))
        primary = {oid for finding in run.findings for oid in finding.affected_object_ids}
        guard_hits = sorted(primary & (FALSE_POSITIVE_GUARD_IDS - mutation_objects))
        extra = sorted(set(extra) | set(guard_hits))
        false_positives = len(extra)
    independence_rows = independence or []
    independence_passed = sum(1 for item in independence_rows if item.get("passed"))
    return EvaluationMetrics(
        period=run.period,
        planted_exceptions=len(planted_ids),
        detected_exceptions=len(detected),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        control_detection_rate=round(detection_rate, 4),
        reperformance_agreement_accuracy=round(recon_correct / recon_total, 4) if recon_total else 1.0,
        human_review_count=run.stats.human_review + run.stats.unresolved_count,
        evidence_link_completeness=round(completeness, 4),
        planted_ids=planted_ids,
        detected_ids=detected,
        missed_ids=list(missed),
        extra_ids=extra,
        runtime_mutations_injected=injected,
        mutations_detected=detected_mutations,
        mutation_detection_rate=round(mutation_rate, 4),
        reperformance_independence_passed=independence_passed,
        reperformance_independence_total=len(independence_rows),
        evidence_complete_findings=evidence_complete,
        evidence_total_findings=evidence_total,
        cross_workflow_trace_complete=bool(trace and trace.get("complete")),
        recurring_findings=len(comparison.recurring) if comparison else sum(1 for item in run.findings if item.recurring),
        resolved_findings=len(comparison.findings_resolved) if comparison else 0,
    )


def format_metrics(metrics: EvaluationMetrics) -> str:
    return "\n".join(
        [
            f"Audit evaluation — {metrics.period}",
            f"Planted exceptions: {metrics.planted_exceptions}",
            f"Detected exceptions: {metrics.detected_exceptions}",
            f"True positives: {metrics.true_positives}",
            f"False positives: {metrics.false_positives}",
            f"False negatives: {metrics.false_negatives}",
            f"Control detection rate: {metrics.control_detection_rate:.2%}",
            f"Re-performance agreement accuracy: {metrics.reperformance_agreement_accuracy:.2%}",
            f"Human-review items: {metrics.human_review_count}",
            f"Evidence-link completeness: {metrics.evidence_link_completeness:.2%}",
            f"Runtime mutations injected: {metrics.runtime_mutations_injected}",
            f"Mutations detected: {metrics.mutations_detected}",
            f"Mutation detection rate: {metrics.mutation_detection_rate:.2%}",
            f"Re-performance independence: {metrics.reperformance_independence_passed}/{metrics.reperformance_independence_total}",
            f"Evidence-complete findings: {metrics.evidence_complete_findings}/{metrics.evidence_total_findings}",
            f"Cross-workflow trace complete: {str(metrics.cross_workflow_trace_complete).lower()}",
            f"Recurring findings: {metrics.recurring_findings}",
            f"Resolved findings: {metrics.resolved_findings}",
            f"Missed: {', '.join(metrics.missed_ids) or '(none)'}",
        ]
    )
