from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from memory.models import MemoryLookup
from skills.models import AgentSkillTrace


class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    vendor: str
    po_id: Optional[str] = None
    amount: float
    invoice_date: str
    due_date: str
    vendor_invoice_number: str
    description: str = ""
    payment_terms: str = "net 30"
    early_payment_discount_percent: float = 0
    early_payment_discount_deadline: Optional[str] = None
    late_fee_percent: float = 0
    vendor_priority: str = "normal"
    source_message_id: Optional[str] = None
    source_thread_id: Optional[str] = None
    source_trace_id: Optional[str] = None
    source_attachment_hashes: list[str] = Field(default_factory=list)


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_id: str
    vendor: str
    authorized_amount: float
    description: str = ""
    status: str
    created_date: str = ""
    currency: str = "USD"
    approval_limit: Optional[float] = None
    approver: str = ""


class GoodsReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    receipt_id: str
    po_id: str
    received: bool
    received_date: Optional[str] = None
    amount_received: float
    quantity_ordered: int
    quantity_received: int


class CompanyPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore")

    policy_id: str
    title: str
    description: str
    action: str
    conditions: dict = Field(default_factory=dict)
    exception_types: list[str] = Field(default_factory=list)


class PriorCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    case_id: str
    invoice_id: str
    exception_types: list[str] = Field(default_factory=list)
    facts: dict = Field(default_factory=dict)
    final_decision: Literal["APPROVE", "HOLD"]
    reason: str
    policies_applied: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    audit_result: str = "PASS"


class APCaseEvidence(BaseModel):
    invoice_id: str
    invoice: Invoice | None = None
    purchase_order: PurchaseOrder | None = None
    goods_receipt: GoodsReceipt | None = None
    amount_difference: float | None = None
    percent_difference: float | None = None
    amount_matches: bool = False
    within_amount_tolerance: bool = False
    vendor_exact_match: bool = False
    vendors_are_similar: bool = False
    po_exists: bool = False
    po_approved: bool = False
    receipt_status: str = "not_applicable"
    duplicate_detected: bool = False
    duplicate_invoice_ids: list[str] = Field(default_factory=list)
    exception_types: list[str] = Field(default_factory=list)
    days_until_due: int | None = None
    invoice_dated_before_po: bool = False


class PreparerRecommendation(BaseModel):
    invoice_id: str
    recommendation: Literal["APPROVE", "HOLD", "INVESTIGATE"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    evidence_used: list[str]
    exception_types: list[str] = Field(default_factory=list)


class InvestigationReport(BaseModel):
    invoice_id: str
    issues_investigated: list[str]
    findings: list[str]
    relevant_precedents: list[str] = Field(default_factory=list)
    relevant_policies: list[str] = Field(default_factory=list)
    unresolved_risks: list[str] = Field(default_factory=list)
    recommendation: Literal["APPROVE", "HOLD"]
    confidence: float = Field(ge=0, le=1)


class ReviewerDecision(BaseModel):
    invoice_id: str
    recommendation: Literal["APPROVE", "HOLD"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    objections: list[str] = Field(default_factory=list)
    evidence_used: list[str]


class ApproverDecision(BaseModel):
    invoice_id: str
    decision: Literal["APPROVE", "HOLD"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    evidence_used: list[str]
    policies_used: list[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    invoice_id: str
    passed: bool
    findings: list[str]
    unsupported_assumptions: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    requires_reconsideration: bool = False


class FinalAPDecision(BaseModel):
    invoice_id: str
    decision: Literal["APPROVE", "HOLD"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    amount_difference: float | None = None
    duplicate_detected: bool
    receipt_status: str
    evidence_used: list[str]
    investigation_performed: bool
    audit_status: str
    reconsideration_performed: bool = False


class DecisionTrace(BaseModel):
    invoice_id: str
    started_at: str
    deterministic_evidence: APCaseEvidence
    preparer: PreparerRecommendation
    investigation: InvestigationReport | None = None
    reviewer: ReviewerDecision | None = None
    approver: ApproverDecision | None = None
    audit: AuditResult | None = None
    reconsideration: dict | None = None
    final: FinalAPDecision
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    memory_lookup: MemoryLookup | None = None
    written_memory_id: str | None = None
    trace_path: str | None = None
    packet_path: str | None = None
    verifier_handle: dict | None = None
    kernel_holds: list[str] = Field(default_factory=list)
    posted_to_pool: bool = False
    wakes: list[dict] = Field(default_factory=list)


class CashPosition(BaseModel):
    as_of_date: str
    bank_balance: float
    minimum_cash_reserve: float
    expected_receipts_next_7_days: float = 0
    payroll_next_7_days: float = 0
    other_committed_outflows: float = 0
    payment_horizon_days: int = 7


class PaymentCandidate(BaseModel):
    invoice_id: str
    vendor: str
    amount: float
    due_date: str
    payment_terms: str
    vendor_priority: str
    days_until_due: int
    discount_open: bool
    discount_percent: float
    discount_deadline: str | None = None
    discount_amount: float = 0
    pay_amount_if_this_week: float
    late: bool
    due_within_horizon: bool
    unnecessary_if_paid_early: bool
    late_fee_percent: float = 0
    approval_source: str = "ap_workflow"


class ScheduledPayment(BaseModel):
    invoice_id: str
    amount: float
    reason: str
    capture_discount: bool = False


class DeferredPayment(BaseModel):
    invoice_id: str
    reason: str
    proposed_pay_date: str | None = None


class PaymentPlan(BaseModel):
    as_of_date: str
    pay_this_week: list[ScheduledPayment]
    defer: list[DeferredPayment]
    total_payout: float
    cash_after_payments: float
    reserve_ok: bool
    reasons: list[str]
    confidence: float = Field(ge=0, le=1)


class PaymentMetrics(BaseModel):
    invoices_due_this_horizon: int
    due_invoices_paid_on_time: int
    on_time_percent: float
    discounts_available: float
    discounts_captured: float
    discounts_missed: float
    late_fees_avoided: float
    unnecessary_early_payments: int
    reserve_violation: bool
    total_cash_retained: float


class PaymentAuditResult(BaseModel):
    passed: bool
    findings: list[str]
    policy_violations: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)


class ScheduleTrace(BaseModel):
    as_of_date: str
    started_at: str
    cash: CashPosition
    spendable_cash: float
    candidates: list[PaymentCandidate]
    plan: PaymentPlan
    metrics: PaymentMetrics
    audit: PaymentAuditResult
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    trace_path: str | None = None
    plan_packet_path: str | None = None
    verifier_wake_path: str | None = None
    outflow_packet_path: str | None = None
