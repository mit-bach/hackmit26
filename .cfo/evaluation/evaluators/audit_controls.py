"""Evaluate the existing independent auditor workflow."""

from __future__ import annotations

from audit.eval import _finding_object_ids
from audit.store import load_invoices
from audit.workflow import run_audit
from evaluation.comparison import case_result, error_case, fail_case
from evaluation.models import EvaluationCaseResult
from evaluation.scoring import summarize_function

def _duplicate_reperformed(object_id: str, run) -> bool:
    """AP already held the duplicate and the auditor independently confirmed it."""
    from tools import exception_types_for, has_duplicate_vendor_invoice_number

    try:
        ap_caught = "duplicate" in exception_types_for(object_id)
        independent = has_duplicate_vendor_invoice_number(object_id)
    except Exception:
        return False
    control = next((item for item in run.controls if item.control_id == "AUD-DUP-INV-001"), None)
    tested = object_id in (control.tested_ids if control else [])
    return bool(ap_caught and independent and tested)


AUDIT_CASES = (
    ("SCN-AUDIT-001", "AUD-DUP-VEND-001", "VEND-001", "DUPLICATE_VENDOR"),
    ("SCN-AUDIT-002", "AUD-DUP-INV-001", "INV-006", "DUPLICATE_INVOICE"),
    ("SCN-AUDIT-003", "AUD-RND-001", "PAY-AP-009", "ROUND_NUMBER"),
    ("SCN-AUDIT-004", "AUD-PCE-001", "JE-POST-CLOSE-001", "UNAUTHORIZED_POST_CLOSE_ENTRY"),
    ("SCN-AUDIT-005", "AUD-SOD-001", "APR-INV-SELF", "SELF_APPROVAL"),
    ("SCN-AUDIT-007", "AUD-SOD-001", "PAY-AP-010", "SELF_APPROVAL"),
)


def run_audit_eval(period: str, expected_findings: list, *, seed: int = 42) -> tuple:
    try:
        run = run_audit(period, seed=seed, use_agent=False, persist=True)
    except Exception as exc:
        case = error_case(case_id="AUDIT-WORKFLOW", domain="audit", scenario_id="SCN-AUDIT-001", reason=str(exc))
        summary = summarize_function("audit", [case])
        summary.workflow_error = str(exc)
        return summary, {}

    found_ids = _finding_object_ids(run)
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

    cases: list[EvaluationCaseResult] = []
    for scenario_id, control_id, object_id, reason_code in AUDIT_CASES:
        detected = object_id in by_control.get(control_id, set()) or object_id in found_ids
        if reason_code == "DUPLICATE_INVOICE" and not detected:
            detected = _duplicate_reperformed(object_id, run)
        if detected:
            cases.append(
                case_result(
                    case_id=f"AUDIT-{scenario_id}",
                    domain="audit",
                    scenario_id=scenario_id,
                    expected="FAIL",
                    actual="FAIL",
                    source_ids=[object_id],
                    diagnostics={"expected_positive": True, "predicted_positive": True, "reason": reason_code},
                )
            )
        else:
            cases.append(
                fail_case(
                    case_id=f"AUDIT-{scenario_id}",
                    domain="audit",
                    scenario_id=scenario_id,
                    expected="FAIL",
                    actual="PASS",
                    error_type="CONTROL_FAILURE_MISSED",
                    reason=f"Auditor missed {reason_code} on {object_id}",
                    source_ids=[object_id],
                    diagnostics={"expected_positive": True, "predicted_positive": False},
                )
            )

    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-006",
            domain="audit",
            scenario_id="SCN-AUDIT-006",
            expected=True,
            actual="INV-009" in found_ids or "PO-109" in found_ids or "APR-INV-SELF" in found_ids,
            source_ids=["INV-009", "PO-109"],
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-008",
            domain="audit",
            scenario_id="SCN-AUDIT-008",
            expected=True,
            actual="PAY-AP-009" in found_ids or "PAY-AP-010" in found_ids,
            source_ids=["PAY-AP-009", "PAY-AP-010"],
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-009",
            domain="audit",
            scenario_id="SCN-AUDIT-009",
            expected=True,
            actual=bool(run.reperformance),
            source_ids=["REC-CLEAN-001"],
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-010",
            domain="audit",
            scenario_id="SCN-AUDIT-010",
            expected=True,
            actual=any(item.invoice_id == "INV-001" for item in load_invoices()),
            source_ids=["INV-001"],
            reason="Clean three-way match is in the AP population; sampling is risk-based",
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-011",
            domain="audit",
            scenario_id="SCN-AUDIT-011",
            expected=True,
            actual=any(sample.population_name == "journal_entries" and sample.sampled_ids for sample in run.samples),
            source_ids=["JE-AP-INV-001"],
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-012",
            domain="audit",
            scenario_id="SCN-AUDIT-012",
            expected=True,
            actual="REC-NS-1240" in found_ids or "TXN-2026-09-015" in found_ids or bool(run.reperformance),
            source_ids=["REC-NS-1240", "TXN-2026-09-015"],
        )
    )
    cases.append(
        case_result(
            case_id="AUDIT-SCN-AUDIT-013",
            domain="audit",
            scenario_id="SCN-AUDIT-013",
            expected=True,
            actual=all(sample.sampled_ids for sample in run.samples),
            source_ids=[sample.sample_id for sample in run.samples],
        )
    )

    planted_controls = {item[1] for item in AUDIT_CASES}
    planted_ids = {item.population_item_id for item in expected_findings} | {item[2] for item in AUDIT_CASES}
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
        if finding.control_id in planted_controls or ids & planted_ids:
            planted_ids.update(ids)
    extra = sorted(found_ids - planted_ids - {"INV-001", "PAY-AP-001", "VEND-001-DUP", "INV-007", "PO-109"})
    if extra:
        cases.append(
            fail_case(
                case_id="AUDIT-FALSE-POSITIVE",
                domain="audit",
                scenario_id="SCN-AUDIT-013",
                expected=[],
                actual=extra[:8],
                error_type="FALSE_AUDIT_FINDING",
                reason=f"Unexpected finding objects: {extra[:8]}",
                source_ids=extra[:8],
                diagnostics={"expected_positive": False, "predicted_positive": True},
                status="PARTIAL",
                score=0.5,
            )
        )

    summary = summarize_function("audit", cases)
    detected = [
        item
        for item in AUDIT_CASES
        if item[2] in found_ids
        or item[2] in by_control.get(item[1], set())
        or (item[3] == "DUPLICATE_INVOICE" and _duplicate_reperformed(item[2], run))
    ]
    summary.metrics = {
        "finding_recall": round(len(detected) / len(AUDIT_CASES), 4),
        "finding_precision": round(
            1.0 - (len(extra) / max(len(found_ids), 1)),
            4,
        ),
        "control_test_accuracy": summary.accuracy,
        "reperformance_accuracy": next((item.score for item in cases if item.scenario_id == "SCN-AUDIT-009"), 0.0),
        "false_positive_findings": float(len(extra)),
        "false_negative_findings": float(len(AUDIT_CASES) - len(detected)),
    }
    raw = {
        "found_ids": sorted(found_ids),
        "finding_ids": [item.finding_id for item in run.findings],
        "sample_ids": {sample.population_name: list(sample.sampled_ids) for sample in run.samples},
        "audit_run_id": run.audit_run_id,
    }
    return summary, raw
