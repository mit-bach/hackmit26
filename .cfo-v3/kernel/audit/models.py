"""Structured audit records. Agents consume these; they do not invent counts or IDs."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


AuditResultCode = Literal["PASS", "FAIL", "EXCEPTION", "HUMAN_REVIEW", "NOT_TESTED"]
Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
FindingStatus = Literal["OPEN", "CONFIRMED", "CLEARED", "UNRESOLVED"]
SamplingMethod = Literal["random", "risk_based"]
ObjectType = Literal[
    "transaction",
    "invoice",
    "journal_entry",
    "payment",
    "reconciliation",
    "approval",
    "vendor",
]
PostCloseClass = Literal[
    "PASS",
    "AUTHORIZED_POST_CLOSE_ADJUSTMENT",
    "UNAUTHORIZED_POST_CLOSE_ENTRY",
    "HUMAN_REVIEW",
]


class AccountingPeriod(BaseModel):
    model_config = ConfigDict(extra="ignore")

    period: str
    status: Literal["OPEN", "CLOSED"] = "OPEN"
    close_timestamp: Optional[str] = None
    closed_by: Optional[str] = None
    close_id: Optional[str] = None


class AuditVendor(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor_id: str
    vendor_name: str
    first_seen: str
    status: str = "active"
    unusual: bool = False


class AuditInvoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    vendor_id: str = ""
    vendor: str
    vendor_invoice_number: str
    amount: float
    invoice_date: str
    period: str = ""
    source: str = "audit_fixture"
    operational_decision: Optional[str] = None
    operational_duplicate_detected: Optional[bool] = None


class AuditPayment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    payment_id: str
    amount: float
    currency: str = "USD"
    vendor_id: str
    vendor_name: str
    payment_date: str
    payment_method: str = "ach"
    source: str = "automated"
    invoice_ids: list[str] = Field(default_factory=list)
    approval_ids: list[str] = Field(default_factory=list)
    initiator_id: str = ""
    approver_id: str = ""
    period: str = ""
    recurring: bool = False
    description: str = ""
    missing_support: bool = False


class AuditJournalEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry_id: str
    period: str
    effective_date: str
    posting_date: str
    posting_timestamp: str
    amount: float
    vendor: str = ""
    memo: str = ""
    poster_id: str = ""
    poster_role: str = ""
    entry_source: str = "manual"
    authorization_id: Optional[str] = None
    authorized: bool = False
    authorization_policy: Optional[str] = None
    related_source_ids: list[str] = Field(default_factory=list)
    approval_ids: list[str] = Field(default_factory=list)
    debit_account: str = ""
    credit_account: str = ""
    preparer_id: str = ""
    approver_id: str = ""


class AuditApproval(BaseModel):
    model_config = ConfigDict(extra="ignore")

    approval_id: str
    object_type: str
    object_id: str
    requester_id: Optional[str] = None
    preparer_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    approver_id: Optional[str] = None
    initiator_id: Optional[str] = None
    amount: Optional[float] = None
    period: str = ""


class OperationalDecision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object_id: str
    object_type: str
    workflow: str
    decision: str
    duplicate_detected: Optional[bool] = None
    reconciliation_status: Optional[str] = None
    match_type: Optional[str] = None
    bank_transaction_ids: list[str] = Field(default_factory=list)
    ledger_entry_ids: list[str] = Field(default_factory=list)
    invoice_ids: list[str] = Field(default_factory=list)
    amount: Optional[float] = None
    estimated_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    estimation_error: Optional[float] = None
    trace_id: Optional[str] = None


class PlantedReconciliation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reconciliation_id: str
    period: str
    recon_type: str
    bank_transaction_ids: list[str] = Field(default_factory=list)
    ledger_entry_ids: list[str] = Field(default_factory=list)
    original_match_type: str
    original_status: str
    original_bank_amount: float = 0
    original_ledger_amount: float = 0
    original_difference: float = 0
    planted_error: bool = False
    payment_id: Optional[str] = None
    invoice_ids: list[str] = Field(default_factory=list)
    original_decision: Optional[str] = None
    estimated_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    original_error: Optional[float] = None
    vendor: str = ""


class PopulationItem(BaseModel):
    object_id: str
    object_type: ObjectType
    amount: float = 0
    period: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class SampleRecord(BaseModel):
    sample_id: str
    audit_run_id: str
    population_name: str
    population_size: int
    eligible_ids: list[str]
    sampling_method: SamplingMethod
    seed: Optional[int] = None
    risk_criteria: list[str] = Field(default_factory=list)
    sample_size: int
    sampled_ids: list[str]
    timestamp: str
    period: str
    risk_scores: dict[str, float] = Field(default_factory=dict)


class ControlException(BaseModel):
    object_id: str
    object_type: str
    result: AuditResultCode
    detail: str
    facts: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    related_ids: dict[str, list[str]] = Field(default_factory=dict)
    monetary_exposure: Optional[float] = None


class ControlResult(BaseModel):
    control_id: str
    control_name: str
    control_description: str
    control_type: str
    population: str
    test_method: str
    policy_reference: str = ""
    result: AuditResultCode
    evidence: list[str] = Field(default_factory=list)
    exceptions: list[ControlException] = Field(default_factory=list)
    tested_ids: list[str] = Field(default_factory=list)
    audit_run_id: str
    facts: dict[str, Any] = Field(default_factory=dict)


class ControlSpec(BaseModel):
    control_id: str
    control_name: str
    control_description: str
    control_type: str
    population: str
    test_method: str
    policy_reference: str = ""


class ReperformanceRecord(BaseModel):
    record_id: str
    audit_run_id: str
    reconciliation_id: str
    recon_type: str
    source_ids: list[str] = Field(default_factory=list)
    original_result: dict[str, Any] = Field(default_factory=dict)
    independent_result: dict[str, Any] = Field(default_factory=dict)
    differences: list[str] = Field(default_factory=list)
    tolerance: float = 0
    agreed: bool
    result: AuditResultCode
    evidence_trace: list[str] = Field(default_factory=list)
    used_original_as_input: bool = False


class AuditFinding(BaseModel):
    finding_id: str
    audit_run_id: str
    control_id: str
    title: str
    description: str
    affected_object_type: str
    affected_object_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    condition_observed: str
    expected_policy: str
    result: AuditResultCode
    severity: Severity
    severity_rationale: str
    monetary_exposure: Optional[float] = None
    recommended_follow_up: str = ""
    owner: Optional[str] = None
    status: FindingStatus = "OPEN"
    source_trace_ids: list[str] = Field(default_factory=list)
    sample_id: Optional[str] = None
    test_id: Optional[str] = None
    issue_key: str = ""
    facts: dict[str, Any] = Field(default_factory=dict)
    recurring: bool = False
    prior_correction_id: Optional[str] = None
    payment_ids: list[str] = Field(default_factory=list)
    invoice_ids: list[str] = Field(default_factory=list)
    vendor_ids: list[str] = Field(default_factory=list)
    approval_ids: list[str] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    reconciliation_ids: list[str] = Field(default_factory=list)


class AuditCorrection(BaseModel):
    correction_id: str
    issue_key: str
    finding_id: str = ""
    object_id: str
    control_id: str
    valid: bool = True
    action: str = "corrective_action"
    recorded_at: str = ""
    notes: str = ""


class RunComparison(BaseModel):
    before_run_id: str
    after_run_id: str
    findings_opened: list[str] = Field(default_factory=list)
    findings_resolved: list[str] = Field(default_factory=list)
    findings_still_open: list[str] = Field(default_factory=list)
    findings_new: list[str] = Field(default_factory=list)
    recurring: list[str] = Field(default_factory=list)
    human_review_resolved: list[str] = Field(default_factory=list)
    before_pass_rate: float = 0
    after_pass_rate: float = 0
    pass_rate_change: float = 0


class ReportStats(BaseModel):
    period: str
    audit_run_id: str
    scope: list[str] = Field(default_factory=list)
    populations: dict[str, int] = Field(default_factory=dict)
    sampling: list[dict[str, Any]] = Field(default_factory=list)
    controls_tested: int = 0
    passed: int = 0
    failed: int = 0
    exceptions: int = 0
    human_review: int = 0
    not_tested: int = 0
    finding_count: int = 0
    unresolved_count: int = 0
    reperformance_count: int = 0
    reperformance_agreed: int = 0
    reperformance_disagreed: int = 0
    finding_ids: list[str] = Field(default_factory=list)
    control_results: dict[str, str] = Field(default_factory=dict)


class EvaluationMetrics(BaseModel):
    period: str
    planted_exceptions: int = 0
    detected_exceptions: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    control_detection_rate: float = 0
    reperformance_agreement_accuracy: float = 0
    human_review_count: int = 0
    evidence_link_completeness: float = 0
    planted_ids: list[str] = Field(default_factory=list)
    detected_ids: list[str] = Field(default_factory=list)
    missed_ids: list[str] = Field(default_factory=list)
    extra_ids: list[str] = Field(default_factory=list)
    runtime_mutations_injected: int = 0
    mutations_detected: int = 0
    mutation_detection_rate: float = 0
    reperformance_independence_passed: int = 0
    reperformance_independence_total: int = 0
    evidence_complete_findings: int = 0
    evidence_total_findings: int = 0
    cross_workflow_trace_complete: bool = False
    recurring_findings: int = 0
    resolved_findings: int = 0


class FindingInterpretation(BaseModel):
    finding_id: str
    result: AuditResultCode
    severity: Severity
    severity_rationale: str
    human_follow_up: str = ""


class AuditorInterpretation(BaseModel):
    audit_run_id: str
    what_was_tested: list[str] = Field(default_factory=list)
    populations: dict[str, int] = Field(default_factory=dict)
    sampling_methods: list[str] = Field(default_factory=list)
    evidence_examined: list[str] = Field(default_factory=list)
    deterministic_tests: list[str] = Field(default_factory=list)
    reperformance_summary: list[str] = Field(default_factory=list)
    findings: list[FindingInterpretation] = Field(default_factory=list)
    human_follow_up: list[str] = Field(default_factory=list)


class AuditReportAgentOutput(BaseModel):
    audit_run_id: str
    narrative: str
    finding_ids_cited: list[str] = Field(default_factory=list)
    unused_invented_ids: list[str] = Field(default_factory=list)


class AuditRun(BaseModel):
    audit_run_id: str
    period: str
    started_at: str
    scope: list[str] = Field(default_factory=list)
    samples: list[SampleRecord] = Field(default_factory=list)
    controls: list[ControlResult] = Field(default_factory=list)
    reperformance: list[ReperformanceRecord] = Field(default_factory=list)
    findings: list[AuditFinding] = Field(default_factory=list)
    unresolved: list[ControlException] = Field(default_factory=list)
    stats: ReportStats
    interpretation: Optional[AuditorInterpretation] = None
    report_text: str = ""
    metrics: Optional[EvaluationMetrics] = None
    used_agent: bool = False
    trace_path: Optional[str] = None
    source_records_mutated: bool = False
