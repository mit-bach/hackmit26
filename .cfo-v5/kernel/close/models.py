"""Shared close-run state. References existing workflow outputs; does not replace them."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from ar.models import ARCloseSnapshot
from accrual.models import AccrualPeriodReport, DiscoveryReport, ReconciliationResult
from models import ScheduleTrace


class APCloseResult(BaseModel):
    invoice_id: str
    vendor: str
    amount: float
    decision: Literal["APPROVE", "HOLD"]
    exceptions: list[str] = Field(default_factory=list)
    source: Literal["ap_workflow", "ap_policy"]
    trace_path: Optional[str] = None
    ap_decision_id: Optional[str] = None


class IntegrationSummary(BaseModel):
    provider: str
    action: str
    status: str
    invoice_numbers: list[str] = Field(default_factory=list)
    payout_id: Optional[str] = None
    duplicate: bool = False
    message: str = ""


class CloseException(BaseModel):
    kind: str
    ref: str
    detail: str


class AuditRefs(BaseModel):
    close_id: str
    ingestion_trace: Optional[str] = None
    integration_trace: Optional[str] = None
    ap_traces: list[str] = Field(default_factory=list)
    accrual_trace_dir: Optional[str] = None
    payment_plan_trace: Optional[str] = None
    reconciliation_traces: list[str] = Field(default_factory=list)


class CloseRun(BaseModel):
    period: str
    close_id: str
    started_at: str
    invoices_received: int = 0
    invoice_ids: list[str] = Field(default_factory=list)
    ingestion_canonical: int = 0
    ingestion_duplicates: int = 0
    integrations: list[IntegrationSummary] = Field(default_factory=list)
    ap_results: list[APCloseResult] = Field(default_factory=list)
    approved_ids: list[str] = Field(default_factory=list)
    held_ids: list[str] = Field(default_factory=list)
    discovery: Optional[DiscoveryReport] = None
    accrual: Optional[AccrualPeriodReport] = None
    payment: Optional[ScheduleTrace] = None
    reconciliations: list[ReconciliationResult] = Field(default_factory=list)
    exceptions: list[CloseException] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)
    audit: AuditRefs
    spendable_cash: float = 0
    ar: Optional[ARCloseSnapshot] = None
    trace_path: Optional[str] = None


ClosePeriodStatus = Literal[
    "OPEN",
    "IN_PROGRESS",
    "READY_FOR_REVIEW",
    "READY_TO_CLOSE",
    "BLOCKED",
    "CLOSED",
    "REOPENED",
]
CloseTaskStatus = Literal[
    "NOT_STARTED",
    "READY",
    "RUNNING",
    "COMPLETE",
    "NEEDS_REVIEW",
    "BLOCKED",
    "FAILED",
]
ReviewDecision = Literal["APPROVE", "REJECT", "REQUEST_EVIDENCE", "ESCALATE", "NEEDS_ADJUSTMENT", "HUMAN_REVIEW"]
ReviewItemStatus = Literal["OPEN", "IN_REVIEW", "RESOLVED", "REJECTED", "NEEDS_MORE_EVIDENCE"]
FinalCloseDecision = Literal["APPROVE_CLOSE", "REJECT_CLOSE", "REQUEST_REVIEW"]
ControlDecision = Literal["REJECTED", "APPROVED", "PENDING"]
BLOCKING_REVIEW_STATUSES = ("OPEN", "IN_REVIEW", "REJECTED", "NEEDS_MORE_EVIDENCE")


class IdentityLink(BaseModel):
    """One canonical chain: source document → transaction → JE → account → recon → task."""

    link_id: str
    source_document_id: str = ""
    transaction_id: str = ""
    journal_entry_id: str = ""
    account_id: str = ""
    reconciliation_id: str = ""
    close_task_id: str = ""
    review_id: str = ""
    extra: dict = Field(default_factory=dict)
    created_at: str = ""


class ClosePeriod(BaseModel):
    period: str
    status: ClosePeriodStatus = "OPEN"
    opened_at: str
    target_close_date: str = ""
    closed_at: Optional[str] = None
    reopened_at: Optional[str] = None
    reopen_reason: str = ""
    scenario: str = "demo"
    snapshot_ids: list[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approval_decision: Optional[str] = None
    approval_reason: str = ""
    approval_at: Optional[str] = None


class CloseTask(BaseModel):
    task_id: str
    period: str
    category: str
    description: str
    owner_agent: str = ""
    owner_role: str = ""
    task_type: str = ""
    dependencies: list[str] = Field(default_factory=list)
    status: CloseTaskStatus = "NOT_STARTED"
    blocker_reason: str = ""
    blocking_items: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    requires_review: bool = False
    reviewer: str = ""
    review_status: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    stale: bool = False


class ReviewVerdict(BaseModel):
    review_id: str
    subject_id: str
    role: str = "reviewer"
    decision: ReviewDecision
    agree_with_preparer: bool = True
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    created_at: str = ""


class ReviewItem(BaseModel):
    review_id: str
    period: str
    source_workflow: str
    source_case_id: str
    issue_type: str
    description: str
    amount: Optional[float] = None
    evidence_refs: list[str] = Field(default_factory=list)
    proposed_resolution: str = ""
    status: ReviewItemStatus = "OPEN"
    assigned_role: str = ""
    decision: str = ""
    decision_reason: str = ""
    decided_at: Optional[str] = None
    downstream_tasks_affected: list[str] = Field(default_factory=list)
    reviewer: str = ""
    resolution_action: str = ""
    source_object_ref: str = ""
    source_object_before: dict = Field(default_factory=dict)
    source_object_after: dict = Field(default_factory=dict)
    journal_entry_ids: list[str] = Field(default_factory=list)
    queue_owner: str = ""
    queue_profile: str = ""
    handle_path: str = ""
    packet_path: str = ""


class CloseGateResult(BaseModel):
    period: str
    all_required_tasks_complete: bool = False
    all_required_bs_recs_signed_off: bool = False
    no_blocking_reviews: bool = False
    evidence_complete: bool = False
    journal_safeguards_pass: bool = False
    blockers: list[str] = Field(default_factory=list)
    task_status: dict[str, str] = Field(default_factory=dict)
    recon_status: dict[str, str] = Field(default_factory=dict)
    journal_findings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    passed: bool = False


class FinalCloseVerdict(BaseModel):
    period: str
    decision: FinalCloseDecision
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    reviewer: str = "Month-End Close Reviewer"
    created_at: str = ""
    gate_passed: bool = False
    overridden_by_python: bool = False


class MaterialityPolicy(BaseModel):
    close_materiality_dollars: float = 1000.0
    auto_review_threshold: float = 50.0
    source: str = "data/close/materiality.json"
    note: str = "Materiality never auto-explains an unexplained difference."


class AccountRollForward(BaseModel):
    account: str
    period: str
    beginning: float = 0
    additions: float = 0
    reductions: float = 0
    ending: float = 0
    formula: str = ""
    tied: bool = True
    evidence_refs: list[str] = Field(default_factory=list)


class ReviewResolution(BaseModel):
    resolution_id: str
    item_id: str
    period: str
    resolution: str
    reviewer: str = "human"
    created_at: str = ""
    original_status: str = ""
    original_detail: str = ""


class CloseControlEvent(BaseModel):
    event_id: str
    event_type: str
    period: str
    created_at: str
    actor: str = ""
    reason: str = ""
    decision: ControlDecision = "REJECTED"
    attempted_entry: dict = Field(default_factory=dict)
    audit_trace: str = ""


class CloseManagerDecision(BaseModel):
    period: str
    next_tasks: list[str] = Field(default_factory=list)
    blocked_tasks: list[str] = Field(default_factory=list)
    waiting_on_humans: list[str] = Field(default_factory=list)
    narrative: str = ""
    can_close: bool = False


class CloseSnapshot(BaseModel):
    snapshot_id: str
    period: str
    close_timestamp: str
    close_status: ClosePeriodStatus
    ledger_balances: dict[str, float] = Field(default_factory=dict)
    ap_balance: float = 0
    ar_balance: float = 0
    cash_reconciliation: dict = Field(default_factory=dict)
    accrual_balances: dict[str, float] = Field(default_factory=dict)
    prepaid_rollforward: Optional[AccountRollForward] = None
    fixed_asset_rollforward: Optional[AccountRollForward] = None
    accumulated_depreciation_rollforward: Optional[AccountRollForward] = None
    account_reconciliations: list[dict] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    reviewer_approvals: list[dict] = Field(default_factory=list)
    audit_trace_refs: list[str] = Field(default_factory=list)
    resolutions: list[ReviewResolution] = Field(default_factory=list)
    tasks: list[CloseTask] = Field(default_factory=list)
    reopen_of: Optional[str] = None
    review_items: list[ReviewItem] = Field(default_factory=list)
    final_verdict: Optional[FinalCloseVerdict] = None
    close_gate: Optional[CloseGateResult] = None
    approved_by: Optional[str] = None


class CloseEvalMetrics(BaseModel):
    period: str
    required_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    approved_reconciliations: int = 0
    failed_reconciliations: int = 0
    human_review_items: int = 0
    journal_proposals: int = 0
    duplicate_journal_attempts_prevented: int = 0
    account_tie_out_accuracy: float = 0
    close_status: str = ""
    close_status_correct: bool = False
    audit_trace_complete: bool = False
    snapshot_persisted: bool = False


class MonthEndState(BaseModel):
    period: ClosePeriod
    close_id: str
    tasks: list[CloseTask] = Field(default_factory=list)
    exceptions: list[CloseException] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    reconciliation_ids: list[str] = Field(default_factory=list)
    human_review_items: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    completion_pct: float = 0
    identity_links: list[IdentityLink] = Field(default_factory=list)
    ap_results: list[APCloseResult] = Field(default_factory=list)
    ar: Optional[ARCloseSnapshot] = None
    accrual: Optional[AccrualPeriodReport] = None
    cash_status: str = ""
    prepaid_exceptions: list[str] = Field(default_factory=list)
    asset_exceptions: list[str] = Field(default_factory=list)
    recon_exceptions: list[str] = Field(default_factory=list)
    trace_path: Optional[str] = None
    snapshot_path: Optional[str] = None
    snapshot_ids: list[str] = Field(default_factory=list)
    roll_forwards: list[AccountRollForward] = Field(default_factory=list)
    manager: Optional[CloseManagerDecision] = None
    materiality: Optional[MaterialityPolicy] = None
    control_events: list[CloseControlEvent] = Field(default_factory=list)
    resolutions: list[ReviewResolution] = Field(default_factory=list)
    review_ids: list[str] = Field(default_factory=list)
    invalidated_tasks: list[str] = Field(default_factory=list)
    rerun_tasks: list[str] = Field(default_factory=list)
    force_cash_reset: bool = False
    gate: Optional[CloseGateResult] = None
    final_verdict: Optional[FinalCloseVerdict] = None
