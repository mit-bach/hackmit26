"""Deterministic findings and severity. The agent may explain, not invent, these rules."""

from __future__ import annotations

from audit.models import (
    AuditFinding,
    ControlException,
    ControlResult,
    ReperformanceRecord,
)
from audit.policy import SeverityPolicy


def _money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def assign_severity(
    control_id: str,
    exception: ControlException,
    policy: SeverityPolicy,
) -> tuple[str, str]:
    exposure = exception.monetary_exposure or 0.0
    result = exception.result
    flags = exception.facts
    if result == "HUMAN_REVIEW":
        return "MEDIUM", "Identities or close evidence are incomplete, so the item is routed to human review."
    if control_id == "AUD-PCE-001" and result == "FAIL":
        if exposure >= policy.material_amount:
            return "CRITICAL", (
                f"Unauthorized post-close entry of {_money(exposure)} exceeds the "
                f"material threshold of {policy.material_amount:.2f}."
            )
        return "HIGH", "An entry was posted after period close without structured authorization."
    if control_id == "AUD-DUP-INV-001" and result == "FAIL":
        if exposure >= policy.material_amount:
            return "CRITICAL", "Operational AP missed a duplicate invoice above the material threshold."
        return "HIGH", "Operational AP missed a duplicate vendor invoice number that Python independently detected."
    if control_id == "AUD-REPERF-001" and result == "FAIL":
        if exposure >= policy.material_amount:
            return "HIGH", "Independent re-performance disagrees with the original reconciliation by a material amount."
        return "MEDIUM", "Independent re-performance disagrees with the original reconciliation."
    if control_id == "AUD-SOD-001" and result == "FAIL":
        if exposure >= policy.critical_amount:
            return "CRITICAL", "Self-approval on a payment or journal above the critical-amount threshold."
        if exposure >= policy.material_amount:
            return "HIGH", "Self-approval on a material payment or journal."
        return "MEDIUM", "Requester/preparer and approver IDs are the same in violation of SOD policy."
    if control_id == "AUD-RND-001" and result == "EXCEPTION":
        if flags.get("new_vendor") and flags.get("manual") and exposure >= policy.material_amount:
            return "HIGH", "Round-number manual payment to a new vendor above the material threshold."
        if exposure >= policy.critical_amount:
            return "HIGH", "Large round-number payment with additional risk context."
        return "MEDIUM", "Round-number payment flagged with contextual risk; not treated as automatic fraud."
    if control_id == "AUD-DUP-VEND-001" and result == "FAIL":
        return "MEDIUM", "Two vendor master records collapse to the same normalized legal-name key."
    if result == "FAIL" and exposure >= policy.critical_amount:
        return "CRITICAL", "Control failure with exposure at or above the critical-amount threshold."
    if result == "FAIL" and exposure >= policy.material_amount:
        return "HIGH", "Control failure with material monetary exposure."
    if result == "FAIL":
        return "MEDIUM", "Control failure with documented evidence; exposure is below the material threshold."
    return "LOW", "Exception recorded with limited monetary exposure."


def _related(exception: ControlException, key: str) -> list[str]:
    return list(exception.related_ids.get(key) or [])


def finding_from_exception(
    *,
    audit_run_id: str,
    control: ControlResult,
    exception: ControlException,
    policy: SeverityPolicy,
    index: int,
    sample_id: str | None = None,
) -> AuditFinding:
    severity, rationale = assign_severity(control.control_id, exception, policy)
    finding_id = f"FND-{audit_run_id}-{control.control_id}-{index:03d}"
    issue_key = f"{control.control_id}:{exception.object_id}"
    return AuditFinding(
        finding_id=finding_id,
        audit_run_id=audit_run_id,
        control_id=control.control_id,
        title=f"{control.control_name}: {exception.object_id}",
        description=exception.detail,
        affected_object_type=exception.object_type,
        affected_object_ids=[exception.object_id],
        evidence_ids=list(exception.evidence_ids),
        condition_observed=exception.detail,
        expected_policy=control.policy_reference or control.control_name,
        result=exception.result,
        severity=severity,  # type: ignore[arg-type]
        severity_rationale=rationale,
        monetary_exposure=_money(exception.monetary_exposure),
        recommended_follow_up=f"Investigate {exception.object_id} against {control.control_id}.",
        status="OPEN",
        source_trace_ids=list(exception.evidence_ids),
        sample_id=sample_id,
        test_id=f"{audit_run_id}:{control.control_id}",
        issue_key=issue_key,
        facts=dict(exception.facts),
        payment_ids=_related(exception, "payments") or ([exception.object_id] if exception.object_type == "payment" else []),
        invoice_ids=_related(exception, "invoices") or ([exception.object_id] if exception.object_type == "invoice" else []),
        vendor_ids=_related(exception, "vendors"),
        approval_ids=_related(exception, "approvals"),
        journal_entry_ids=_related(exception, "journals")
        or ([exception.object_id] if exception.object_type == "journal_entry" else []),
        reconciliation_ids=_related(exception, "reconciliations")
        or ([exception.object_id] if exception.object_type == "reconciliation" else []),
    )


def findings_from_controls(
    *,
    audit_run_id: str,
    controls: list[ControlResult],
    reperformance: list[ReperformanceRecord],
    policy: SeverityPolicy,
    sample_ids: dict[str, str] | None = None,
) -> tuple[list[AuditFinding], list[ControlException]]:
    findings: list[AuditFinding] = []
    unresolved: list[ControlException] = []
    index = 1
    samples = sample_ids or {}
    for control in controls:
        for exception in control.exceptions:
            if exception.result == "HUMAN_REVIEW":
                unresolved.append(exception)
                continue
            if exception.result in {"PASS", "NOT_TESTED"}:
                continue
            if exception.result == "EXCEPTION" and control.control_id == "AUD-RND-001":
                if exception.facts.get("ordinary"):
                    continue
            findings.append(
                finding_from_exception(
                    audit_run_id=audit_run_id,
                    control=control,
                    exception=exception,
                    policy=policy,
                    index=index,
                    sample_id=samples.get(exception.object_id),
                )
            )
            index += 1
    for record in reperformance:
        if record.result in {"FAIL", "EXCEPTION"} and not any(
            record.reconciliation_id in item.affected_object_ids for item in findings
        ):
            exception = ControlException(
                object_id=record.reconciliation_id,
                object_type="reconciliation",
                result=record.result,
                detail="; ".join(record.differences) or "Independent re-performance disagreed.",
                facts={
                    "original_result": record.original_result,
                    "independent_result": record.independent_result,
                    "used_original_as_input": record.used_original_as_input,
                    "tolerance": record.tolerance,
                },
                evidence_ids=list(record.evidence_trace),
                related_ids={"reconciliations": [record.reconciliation_id]},
                monetary_exposure=abs(
                    float((record.independent_result or {}).get("difference") or 0)
                    - float((record.original_result or {}).get("difference") or 0)
                ),
            )
            control = ControlResult(
                control_id="AUD-REPERF-001",
                control_name="Reconciliation re-performance",
                control_description="Independently re-run reconciliation arithmetic.",
                control_type="reperformance",
                population="reconciliations",
                test_method="independent_recompute",
                policy_reference="AUD-REPERF",
                result=record.result,
                audit_run_id=audit_run_id,
            )
            findings.append(
                finding_from_exception(
                    audit_run_id=audit_run_id,
                    control=control,
                    exception=exception,
                    policy=policy,
                    index=index,
                )
            )
            index += 1
    return findings, unresolved
