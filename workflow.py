from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agent import (
    approver_agent,
    audit_agent,
    investigator_agent,
    preparer_agent,
    reviewer_agent,
    run_agent,
)
from models import (
    APCaseEvidence,
    ApproverDecision,
    AuditResult,
    DecisionTrace,
    FinalAPDecision,
    InvestigationReport,
    PreparerRecommendation,
    ReviewerDecision,
)
from skills.loader import usage_from_agent
from tools import DataFileError, collect_case_evidence, load_invoice, vendor_alias_established

RUNS_DIR = Path(__file__).resolve().parent / "runs"
MAX_RECONSIDERATIONS = 1


def _dump(model) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2)


def _needs_investigation(evidence: APCaseEvidence, preparer: PreparerRecommendation) -> bool:
    if evidence.exception_types:
        return True
    return preparer.recommendation == "INVESTIGATE"


def _blocking_approve_violations(evidence: APCaseEvidence) -> list[str]:
    """Hard policy holds that an APPROVE cannot survive."""
    violations: list[str] = []
    if evidence.duplicate_detected:
        violations.append("P-002 duplicate vendor invoice number")
    if not evidence.po_exists:
        violations.append("P-008 missing purchase order")
    elif not evidence.po_approved:
        violations.append("P-003 unapproved purchase order")
    if evidence.receipt_status in {"missing", "not_received"}:
        violations.append("P-004 goods not received")
    if evidence.receipt_status == "partial":
        violations.append("P-005 partial receipt paid in full")
    if (
        evidence.po_exists
        and not evidence.vendor_exact_match
        and "vendor_mismatch" in evidence.exception_types
        and not vendor_alias_established(evidence)
    ):
        violations.append("P-006 unknown vendor identity with no supporting prior case")
    if (
        "material_amount_mismatch" in evidence.exception_types
        and not evidence.within_amount_tolerance
    ):
        violations.append("P-009 amount variance exceeds published tolerance")
    return violations


def _run_preparer(invoice_id: str, evidence: APCaseEvidence) -> PreparerRecommendation:
    return run_agent(
        preparer_agent,
        (
            f"Prepare AP case {invoice_id}.\n\n"
            "Python already computed these facts. Use them; do not recalculate:\n"
            f"{_dump(evidence)}"
        ),
    )


def _run_investigator(
    invoice_id: str,
    evidence: APCaseEvidence,
    preparer: PreparerRecommendation,
) -> InvestigationReport:
    return run_agent(
        investigator_agent,
        (
            f"Investigate exceptions on invoice {invoice_id}.\n\n"
            f"Exception types: {evidence.exception_types}\n\n"
            f"Python facts:\n{_dump(evidence)}\n\n"
            f"Preparer recommendation:\n{_dump(preparer)}\n\n"
            "Search policies and prior cases. If nothing supports payment, HOLD."
        ),
    )


def _run_reviewer(
    invoice_id: str,
    evidence: APCaseEvidence,
    preparer: PreparerRecommendation,
    investigation: InvestigationReport | None,
    audit: AuditResult | None = None,
) -> ReviewerDecision:
    extra = ""
    if audit is not None:
        extra = (
            "\n\nAudit found a material problem with the previous APPROVE. "
            "Reconsider independently.\n"
            f"{_dump(audit)}"
        )
    investigation_block = (
        f"\n\nInvestigator report:\n{_dump(investigation)}" if investigation else "\n\nNo investigator report. This was treated as a straightforward case."
    )
    return run_agent(
        reviewer_agent,
        (
            f"Independently review invoice {invoice_id}.\n\n"
            f"Python facts:\n{_dump(evidence)}\n\n"
            f"Preparer:\n{_dump(preparer)}"
            f"{investigation_block}"
            f"{extra}"
        ),
    )


def _run_approver(
    invoice_id: str,
    evidence: APCaseEvidence,
    preparer: PreparerRecommendation,
    investigation: InvestigationReport | None,
    reviewer: ReviewerDecision,
) -> ApproverDecision:
    investigation_block = (
        f"\n\nInvestigator:\n{_dump(investigation)}" if investigation else "\n\nNo investigator report."
    )
    return run_agent(
        approver_agent,
        (
            f"Make the final autonomous payment decision for {invoice_id}. "
            "Decide APPROVE or HOLD. There is no human approver.\n\n"
            f"Python facts:\n{_dump(evidence)}\n\n"
            f"Preparer:\n{_dump(preparer)}"
            f"{investigation_block}\n\n"
            f"Reviewer:\n{_dump(reviewer)}"
        ),
    )


def _run_audit(
    invoice_id: str,
    evidence: APCaseEvidence,
    approver: ApproverDecision,
    investigation: InvestigationReport | None,
) -> AuditResult:
    investigation_block = (
        f"\n\nInvestigator:\n{_dump(investigation)}" if investigation else ""
    )
    return run_agent(
        audit_agent,
        (
            f"Audit the autonomous decision for {invoice_id}.\n\n"
            f"Python facts:\n{_dump(evidence)}\n\n"
            f"Approver decision:\n{_dump(approver)}"
            f"{investigation_block}"
        ),
    )


def _apply_safety_net(evidence: APCaseEvidence, approver: ApproverDecision, audit: AuditResult) -> AuditResult:
    """If the model approved through a must_hold control, force reconsideration."""
    if approver.decision != "APPROVE":
        return audit
    violations = _blocking_approve_violations(evidence)
    if not violations:
        return audit
    findings = list(audit.findings) + [
        f"Safety net: APPROVE conflicts with {item}" for item in violations
    ]
    return audit.model_copy(
        update={
            "passed": False,
            "requires_reconsideration": True,
            "policy_violations": list(dict.fromkeys(audit.policy_violations + violations)),
            "findings": findings,
        }
    )


def _build_final(
    evidence: APCaseEvidence,
    approver: ApproverDecision,
    audit: AuditResult,
    investigation_performed: bool,
    reconsideration_performed: bool,
) -> FinalAPDecision:
    decision = approver.decision
    reasons = list(approver.reasons)
    if decision == "APPROVE" and not audit.passed:
        decision = "HOLD"
        reasons.append("Audit could not support approval; autonomous system held payment.")
    evidence_used = list(approver.evidence_used)
    if investigation_performed:
        evidence_used = list(dict.fromkeys(evidence_used))
    return FinalAPDecision(
        invoice_id=evidence.invoice_id,
        decision=decision,
        confidence=approver.confidence if decision == approver.decision else min(approver.confidence, 0.7),
        reasons=reasons,
        amount_difference=evidence.amount_difference,
        duplicate_detected=evidence.duplicate_detected,
        receipt_status=evidence.receipt_status,
        evidence_used=evidence_used,
        investigation_performed=investigation_performed,
        audit_status="PASS" if audit.passed and decision == approver.decision else "FAIL",
        reconsideration_performed=reconsideration_performed,
    )


def _save_trace(trace: DecisionTrace) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"{trace.invoice_id}-{stamp}.json"
    trace.trace_path = str(path)
    path.write_text(trace.model_dump_json(indent=2) + "\n")
    return path


def run_ap_workflow(invoice_id: str) -> DecisionTrace:
    if load_invoice(invoice_id) is None:
        raise DataFileError(f"Invoice {invoice_id} was not found")

    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence = collect_case_evidence(invoice_id)

    print(f"Invoice: {invoice_id}", flush=True)
    print(f"Python facts: exceptions={evidence.exception_types or ['none']}", flush=True)
    print(flush=True)

    preparer = _run_preparer(invoice_id, evidence)

    investigation = None
    if _needs_investigation(evidence, preparer):
        investigation = _run_investigator(invoice_id, evidence, preparer)

    reviewer = _run_reviewer(invoice_id, evidence, preparer, investigation)
    approver = _run_approver(invoice_id, evidence, preparer, investigation, reviewer)
    audit = _apply_safety_net(evidence, approver, _run_audit(invoice_id, evidence, approver, investigation))

    reconsideration = None
    reconsideration_performed = False
    should_reconsider = (
        approver.decision == "APPROVE"
        and (audit.requires_reconsideration or not audit.passed)
        and MAX_RECONSIDERATIONS >= 1
    )
    if should_reconsider:
        reconsideration_performed = True
        print("Audit requested one reconsideration cycle.\n", flush=True)
        previous = {
            "reviewer": reviewer.model_dump(),
            "approver": approver.model_dump(),
            "audit": audit.model_dump(),
        }
        reviewer = _run_reviewer(invoice_id, evidence, preparer, investigation, audit)
        approver = _run_approver(invoice_id, evidence, preparer, investigation, reviewer)
        audit = _apply_safety_net(
            evidence, approver, _run_audit(invoice_id, evidence, approver, investigation)
        )
        if approver.decision == "APPROVE" and not audit.passed:
            approver = approver.model_copy(
                update={
                    "decision": "HOLD",
                    "reasons": approver.reasons
                    + ["Held after audit reconsideration because approval remained unsupported."],
                }
            )
            audit = audit.model_copy(update={"requires_reconsideration": False})
        reconsideration = {
            "previous": previous,
            "reviewer": reviewer.model_dump(),
            "approver": approver.model_dump(),
            "audit": audit.model_dump(),
        }

    final = _build_final(
        evidence,
        approver,
        audit,
        investigation_performed=investigation is not None,
        reconsideration_performed=reconsideration_performed,
    )

    ran = [preparer_agent]
    if investigation is not None:
        ran.append(investigator_agent)
    ran.extend([reviewer_agent, approver_agent, audit_agent])

    trace = DecisionTrace(
        invoice_id=invoice_id,
        started_at=started_at,
        deterministic_evidence=evidence,
        preparer=preparer,
        investigation=investigation,
        reviewer=reviewer,
        approver=approver,
        audit=audit,
        reconsideration=reconsideration,
        final=final,
        agents=[usage_from_agent(item) for item in ran],
    )
    _save_trace(trace)
    if final.decision == "APPROVE":
        from scheduling.pool import add_approved

        add_approved(invoice_id, source="ap_workflow", confidence=final.confidence)
    return trace
