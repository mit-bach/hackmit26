"""Complete independent-audit demo pathway."""

from __future__ import annotations

from audit.compare import compare_runs, format_comparison
from audit.dataset import FALSE_POSITIVE_GUARD_IDS, clean_dataset
from audit.eval import evaluate_run, format_metrics
from audit.evidence import validate_run_evidence
from audit.history import record_correction
from audit.independence import run_independence_suite
from audit.mutations import apply_mutations, restore_mutation
from audit.report import format_audit_report
from audit.store import load_ground_truth
from audit.trace import evidence_chain, format_chain
from audit.workflow import run_audit


def run_audit_demo(period: str = "2026-09", *, seed: int = 26) -> dict:
    """Run finance-style work first is represented by operational fixtures, then audit independently."""
    run = run_audit(period, seed=seed, use_agent=False, persist=True)
    metrics = evaluate_run(run, load_ground_truth())
    run.metrics = metrics
    if run.trace_path:
        from audit.store import save_run

        save_run(run)
    return {
        "run": run,
        "metrics": metrics,
        "report": format_audit_report(run),
        "narrative": (
            "We ran the finance workflow first. Operational AP, payment, close, "
            "and reconciliation decisions were recorded against the existing "
            "transaction IDs. Then an independent auditor sampled the resulting "
            "work, recomputed selected reconciliations without using the original "
            "conclusions as inputs, caught the planted control failures, and "
            "produced findings tied to source evidence."
        ),
    }


def run_adversarial_demo(period: str = "2026-09", *, seed: int = 26) -> dict:
    """Clean baseline → runtime mutations → independent audit → correction → second run."""
    clean = clean_dataset(period)
    baseline = run_audit(period, seed=seed, use_agent=False, persist=True, dataset=clean)
    independence = run_independence_suite(clean)

    mutated, mutations = apply_mutations(clean)
    first = run_audit(period, seed=seed, use_agent=False, persist=True, dataset=mutated)

    sod = next((item for item in first.findings if item.control_id == "AUD-SOD-001"), None)
    rnd = next((item for item in first.findings if item.control_id == "AUD-RND-001"), None)
    corrections = []
    if sod:
        corrections.append(
            record_correction(
                issue_key=sod.issue_key,
                object_id=sod.affected_object_ids[0],
                control_id=sod.control_id,
                finding_id=sod.finding_id,
                action="corrective_action",
                notes="Approver identity restored so requester and approver differ.",
            )
        )
    if rnd:
        corrections.append(
            record_correction(
                issue_key=rnd.issue_key,
                object_id=rnd.affected_object_ids[0],
                control_id=rnd.control_id,
                finding_id=rnd.finding_id,
                action="corrective_action",
                notes="Accounting recorded a corrective action but left the $50,000 wire in place.",
            )
        )

    corrected = restore_mutation(mutated.copy(), "self_approve")
    corrected.corrections = list(corrections)
    second = run_audit(period, seed=seed, use_agent=False, persist=True, dataset=corrected)

    comparison = compare_runs(first, second)
    chain = evidence_chain(clean, first)
    metrics = evaluate_run(
        first,
        {"planted_exceptions": [], "expected_pass": [{"object_id": item} for item in FALSE_POSITIVE_GUARD_IDS]},
        mutations=mutations,
        independence=independence,
        trace=chain,
        comparison=comparison,
    )
    first.metrics = metrics
    evidence_errors = validate_run_evidence(first) + validate_run_evidence(second)
    return {
        "baseline": baseline,
        "first": first,
        "second": second,
        "mutations": mutations,
        "metrics": metrics,
        "comparison": comparison,
        "chain": chain,
        "independence": independence,
        "evidence_errors": evidence_errors,
        "corrections": corrections,
    }


def format_demo(payload: dict) -> str:
    run = payload["run"]
    metrics = payload["metrics"]
    finding_lines = [
        f"- {item.finding_id}: {item.severity} {item.control_id} → {', '.join(item.affected_object_ids)}"
        for item in run.findings
    ] or ["- (none)"]
    return "\n".join(
        [
            "INDEPENDENT AUDITOR DEMO",
            "",
            payload["narrative"],
            "",
            payload["report"],
            "",
            format_metrics(metrics),
            "",
            "PLANTED FAILURES CAUGHT",
            *finding_lines,
            "",
            f"Trace IDs: {run.audit_run_id}",
            f"Saved: {run.trace_path or '(in-memory)'}",
        ]
    )


def format_adversarial_demo(payload: dict) -> str:
    baseline = payload["baseline"]
    first = payload["first"]
    second = payload["second"]
    mutations = payload["mutations"]
    metrics = payload["metrics"]
    comparison = payload["comparison"]
    independence = payload["independence"]

    def _findings(run) -> list[str]:
        rows = [
            f"- {item.issue_key}  {item.result}  {item.severity}"
            f"{'  RECURRING' if item.recurring else ''}"
            for item in run.findings
        ]
        return rows or ["- (none)"]

    sample_lines = []
    for sample in first.samples:
        sample_lines.append(
            f"- {sample.population_name}: {sample.sample_size}/{sample.population_size} via {sample.sampling_method}"
        )
    control_lines = [
        f"- {item.control_id}: {item.result}  tested={len(item.tested_ids)}  exceptions={len(item.exceptions)}"
        for item in first.controls
    ]
    reperf_lines = [
        f"- {item.reconciliation_id}: {'AGREE' if item.agreed else 'DISAGREE'}  "
        f"used_original_as_input={item.used_original_as_input}"
        for item in first.reperformance
        if not item.agreed
    ] or ["- (none)"]
    mutation_lines = [f"- {item.mutation_id}: {item.description} → {item.object_id}" for item in mutations]
    independence_lines = [
        f"- {item['name']}: {'PASS' if item['passed'] else 'FAIL'}  "
        f"independent_unchanged={item['independent_unchanged']}  "
        f"disagreement_detected={item['disagreement_detected']}"
        for item in independence
    ]
    return "\n".join(
        [
            "ADVERSARIAL INDEPENDENT AUDITOR DEMO",
            "",
            "BASELINE",
            f"Clean September records. Findings: {len(baseline.findings)}. "
            f"Controls passed: {baseline.stats.passed}/{baseline.stats.controls_tested}.",
            "",
            "RUNTIME MUTATIONS",
            *mutation_lines,
            "",
            "AUDIT SAMPLE",
            *sample_lines,
            "",
            "CONTROL RESULTS",
            *control_lines,
            "",
            "RE-PERFORMANCE DISAGREEMENTS",
            *reperf_lines,
            "",
            "FINDINGS",
            *_findings(first),
            "",
            "EVIDENCE TRACE",
            format_chain(payload["chain"]),
            "",
            "AFTER CORRECTION",
            "SOD self-approval was corrected. The $50,000 manual wire was left in place.",
            *_findings(second),
            "",
            format_comparison(comparison),
            "",
            "EVALUATION",
            format_metrics(metrics),
            "",
            "INDEPENDENCE",
            *independence_lines,
            "",
            f"Baseline run: {baseline.audit_run_id}",
            f"Audit run A: {first.audit_run_id}",
            f"Audit run B: {second.audit_run_id}",
        ]
    )
