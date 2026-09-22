"""Deterministic month-end close gates. Agents cannot override these checks."""

from __future__ import annotations

from close.checklist import TASK_SPECS
from close.ledger import load_entries
from close.models import CloseGateResult, MonthEndState
from close.reviews import blocking_reviews, load_reviews

REQUIRED_TASKS = [spec["task_id"] for spec in TASK_SPECS if spec["task_id"] not in {"final_review", "mark_closed"}]
REQUIRED_ACCOUNTS = (
    "Cash",
    "Accounts Receivable",
    "Accounts Payable",
    "Accrued Expenses",
    "Prepaid Expenses",
    "Fixed Assets",
    "Accumulated Depreciation",
)


def journal_safeguards(period: str) -> tuple[bool, list[str]]:
    findings: list[str] = []
    rows = [item for item in load_entries() if item.get("period") == period]
    keys: dict[str, str] = {}
    for item in rows:
        debit = float(item.get("debit") or 0)
        credit = float(item.get("credit") or 0)
        if abs(debit - credit) > 0.001:
            findings.append(f"unbalanced:{item.get('entry_id')}")
        if debit <= 0:
            findings.append(f"non_positive:{item.get('entry_id')}")
        if not item.get("evidence_refs"):
            findings.append(f"missing_evidence:{item.get('entry_id')}")
        key = str(item.get("idempotency_key") or "")
        if key:
            if key in keys:
                findings.append(f"duplicate_key:{key}")
            keys[key] = str(item.get("entry_id"))
    return not findings, findings


def evidence_gaps(period: str) -> list[str]:
    gaps: list[str] = []
    from prepaid.store import get_item, load_items

    missing = get_item("PRE-INS-MISSING")
    if missing is not None and (not missing.evidence_refs or not missing.source_document_id):
        gaps.append("PRE-INS-MISSING missing Northshore policy evidence")
    for item in load_items():
        if item.status == "review" and (not item.evidence_refs or not item.source_document_id):
            if item.prepaid_id not in " ".join(gaps):
                gaps.append(f"{item.prepaid_id} missing source document")
    return gaps


def evaluate_close_gates(state: MonthEndState) -> CloseGateResult:
    period = state.period.period
    by_id = {item.task_id: item for item in state.tasks}
    task_status = {item.task_id: item.status for item in state.tasks}
    tasks_complete = all(by_id[task_id].status == "COMPLETE" for task_id in REQUIRED_TASKS if task_id in by_id)
    blockers: list[str] = []
    if not tasks_complete:
        unfinished = [task_id for task_id in REQUIRED_TASKS if by_id.get(task_id) and by_id[task_id].status != "COMPLETE"]
        blockers.append("Required tasks incomplete: " + ", ".join(unfinished))

    recon_status: dict[str, str] = {}
    from bs_recon.store import load_reconciliations

    recs = {item.account_id: item for item in load_reconciliations(period)}
    signed = True
    for account in REQUIRED_ACCOUNTS:
        rec = recs.get(account)
        status = rec.status if rec else "MISSING"
        recon_status[account] = status
        if status != "SIGNED_OFF":
            signed = False
            blockers.append(f"{account} reconciliation is {status}, not SIGNED_OFF")

    reviews = blocking_reviews(period)
    no_blocking = not reviews
    if reviews:
        blockers.append("Blocking review items: " + ", ".join(item.review_id for item in reviews))

    gaps = evidence_gaps(period)
    evidence_ok = not gaps
    if gaps:
        blockers.extend(gaps)

    journals_ok, journal_findings = journal_safeguards(period)
    if not journals_ok:
        blockers.extend(journal_findings)

    passed = tasks_complete and signed and no_blocking and evidence_ok and journals_ok
    return CloseGateResult(
        period=period,
        all_required_tasks_complete=tasks_complete,
        all_required_bs_recs_signed_off=signed,
        no_blocking_reviews=no_blocking,
        evidence_complete=evidence_ok,
        journal_safeguards_pass=journals_ok,
        blockers=blockers,
        task_status=task_status,
        recon_status=recon_status,
        journal_findings=journal_findings,
        evidence_gaps=gaps,
        passed=passed,
    )


def reviewer_facts(state: MonthEndState, gate: CloseGateResult) -> dict:
    return {
        "period": state.period.period,
        "close_status": state.period.status,
        "task_completion_state": gate.task_status,
        "unresolved_review_items": [
            {
                "review_id": item.review_id,
                "status": item.status,
                "description": item.description,
                "amount": item.amount,
            }
            for item in load_reviews(state.period.period)
            if item.status != "RESOLVED"
        ],
        "bs_reconciliation_statuses": gate.recon_status,
        "journal_validation_results": {
            "pass": gate.journal_safeguards_pass,
            "findings": gate.journal_findings,
        },
        "evidence_completeness": {
            "pass": gate.evidence_complete,
            "gaps": gate.evidence_gaps,
        },
        "material_exceptions": [item.detail for item in state.exceptions],
        "gate_passed": gate.passed,
        "allowed_decisions": ["APPROVE_CLOSE", "REJECT_CLOSE", "REQUEST_REVIEW"],
        "instruction": (
            "Return only APPROVE_CLOSE, REJECT_CLOSE, or REQUEST_REVIEW. "
            "Python will reject APPROVE_CLOSE when gate_passed is false."
        ),
    }
