"""Deterministic evidence-completeness checks. The report agent cannot fill gaps."""

from __future__ import annotations

from audit.models import AuditFinding, AuditRun, ControlException

REVIEW_RESULTS = {"FAIL", "EXCEPTION", "HUMAN_REVIEW"}


def _missing_finding_fields(finding: AuditFinding) -> list[str]:
    missing: list[str] = []
    if not finding.finding_id:
        missing.append("finding_id")
    if not finding.audit_run_id:
        missing.append("audit_run_id")
    if not finding.control_id:
        missing.append("control_id")
    if not finding.affected_object_ids:
        missing.append("affected_object_ids")
    if not finding.evidence_ids:
        missing.append("evidence_ids")
    if not finding.expected_policy:
        missing.append("expected_policy")
    if finding.control_id == "AUD-SOD-001":
        actors = [
            finding.facts.get("requester_id"),
            finding.facts.get("preparer_id"),
            finding.facts.get("approver_id"),
            finding.facts.get("initiator_id"),
            finding.facts.get("reviewer_id"),
        ]
        if not any(actors):
            missing.append("sod_actor_ids")
        if not finding.facts.get("policy_reference") and not finding.expected_policy:
            missing.append("policy_reference")
    if finding.control_id == "AUD-PCE-001":
        if not finding.facts.get("close_timestamp") and not finding.facts.get("close_status"):
            missing.append("close_timestamp")
        if not finding.facts.get("posting_timestamp") and not finding.facts.get("effective_date"):
            missing.append("posting_timestamp")
    if finding.control_id == "AUD-REPERF-001":
        if not finding.facts.get("original_result") or not finding.facts.get("independent_result"):
            missing.append("reperformance_source_arithmetic")
    if finding.control_id == "AUD-RND-001":
        if finding.facts.get("amount") is None and finding.monetary_exposure is None:
            missing.append("payment_amount")
    return missing


def _missing_unresolved_fields(item: ControlException, audit_run_id: str, control_id: str) -> list[str]:
    missing: list[str] = []
    if not item.object_id:
        missing.append("object_id")
    if not item.evidence_ids and not item.facts:
        missing.append("evidence")
    if control_id == "AUD-SOD-001" and not any(
        item.facts.get(key) for key in ("requester_id", "approver_id", "initiator_id", "preparer_id")
    ):
        missing.append("sod_actor_ids")
    if control_id == "AUD-PCE-001" and not item.facts.get("close_timestamp") and not item.facts.get("close_status"):
        missing.append("close_timestamp")
    if not audit_run_id:
        missing.append("audit_run_id")
    if not control_id:
        missing.append("control_id")
    return missing


def validate_run_evidence(run: AuditRun) -> list[str]:
    """Return human-readable errors. Empty means every exception is defensible."""
    errors: list[str] = []
    by_object: dict[str, str] = {}
    for control in run.controls:
        for exception in control.exceptions:
            by_object[exception.object_id] = control.control_id
    for finding in run.findings:
        if finding.result not in REVIEW_RESULTS:
            continue
        missing = _missing_finding_fields(finding)
        if missing:
            errors.append(f"{finding.finding_id} missing {', '.join(missing)}")
    for item in run.unresolved:
        control_id = by_object.get(item.object_id, "")
        missing = _missing_unresolved_fields(item, run.audit_run_id, control_id)
        if missing:
            errors.append(f"unresolved {item.object_id} missing {', '.join(missing)}")
    return errors


def evidence_completeness(run: AuditRun) -> tuple[int, int]:
    reviewable = [item for item in run.findings if item.result in REVIEW_RESULTS]
    complete = sum(1 for item in reviewable if not _missing_finding_fields(item))
    return complete, len(reviewable)
