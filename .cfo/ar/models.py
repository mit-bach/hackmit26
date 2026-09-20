from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from skills.models import AgentSkillTrace


InvoiceStatus = Literal["OPEN", "PARTIALLY_PAID", "PAID", "PAST_DUE", "DISPUTED"]
CollectionStatus = Literal["NONE", "REMINDED", "ESCALATED", "PROMISE_TO_PAY", "ON_HOLD"]
DisputeStatus = Literal["NONE", "OPEN", "RESOLVED"]
AgingBucket = Literal["CURRENT", "1-30", "31-60", "61-90", "90+"]
CollectionAction = Literal[
    "NO_ACTION",
    "SEND_GENTLE_REMINDER",
    "SEND_OVERDUE_REMINDER",
    "SEND_FINAL_NOTICE",
    "REQUEST_INTERNAL_REVIEW",
    "ESCALATE_DISPUTE",
    "HOLD_CONTACT",
]
PaymentApplicationStatus = Literal[
    "UNMATCHED",
    "PROPOSED",
    "APPLIED",
    "PARTIALLY_APPLIED",
    "HUMAN_REVIEW",
]
CashDecision = Literal["AUTO_APPLY", "HUMAN_REVIEW", "UNAPPLIED"]
ARJournalType = Literal[
    "ar_invoice",
    "cash_receipt",
    "unapplied_cash",
    "refund",
    "processor_fee",
    "dispute",
]


class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customer_id: str
    customer_name: str
    payment_behavior: str = "mixed"
    on_time_rate: float = Field(ge=0, le=1, default=0.8)
    average_days_late: int = 0
    strategic: bool = False
    risk_flag: str = ""
    typical_remittance: str = "invoice_number"
    currency: str = "USD"
    notes: str = ""
    aliases: list[str] = Field(default_factory=list)


class CustomerInvoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    customer_id: str
    customer_name: str
    invoice_date: str
    due_date: str
    original_amount: float
    outstanding_amount: float
    currency: str = "USD"
    status: InvoiceStatus = "OPEN"
    payment_terms: str = "net 30"
    purchase_order: Optional[str] = None
    reference: Optional[str] = None
    description: str = ""
    created_at: str = ""
    last_payment_date: Optional[str] = None
    last_collection_contact: Optional[str] = None
    reminder_count: int = 0
    collection_status: CollectionStatus = "NONE"
    dispute_status: DisputeStatus = "NONE"
    dispute_reason: str = ""
    promised_pay_date: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class CustomerPayment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    payment_id: str
    payment_date: str
    amount: float
    currency: str = "USD"
    payer_name: str
    customer_id: Optional[str] = None
    bank_reference: str = ""
    remittance_text: str = ""
    invoice_reference: Optional[str] = None
    source: str = "bank"
    unapplied_amount: float = 0
    application_status: PaymentApplicationStatus = "UNMATCHED"
    metadata: dict = Field(default_factory=dict)


class AgingLine(BaseModel):
    invoice_id: str
    customer_id: str
    customer_name: str
    original_amount: float
    outstanding_amount: float
    due_date: str
    days_past_due: int
    aging_bucket: AgingBucket
    dispute_status: DisputeStatus
    collection_status: CollectionStatus
    invoice_status: InvoiceStatus


class AgingTotals(BaseModel):
    total_ar: float = 0
    current_ar: float = 0
    past_due_ar: float = 0
    bucket_amounts: dict[str, float] = Field(default_factory=dict)
    bucket_percents: dict[str, float] = Field(default_factory=dict)
    disputed_ar: float = 0
    partially_paid_ar: float = 0
    open_invoice_count: int = 0


class CustomerAging(BaseModel):
    customer_id: str
    customer_name: str
    total_outstanding: float
    oldest_unpaid_invoice: Optional[str] = None
    oldest_due_date: Optional[str] = None
    max_days_past_due: int = 0
    open_invoices: int = 0
    amount_past_due: float = 0
    dispute_amount: float = 0
    payment_behavior: str = ""


class AgingReport(BaseModel):
    as_of_date: str
    lines: list[AgingLine] = Field(default_factory=list)
    totals: AgingTotals = Field(default_factory=AgingTotals)
    customers: list[CustomerAging] = Field(default_factory=list)
    calculated_at: str = ""
    trace_path: Optional[str] = None


class CollectionFacts(BaseModel):
    invoice_id: str
    customer_id: str
    customer_name: str
    outstanding_amount: float
    original_amount: float
    due_date: str
    days_past_due: int
    aging_bucket: AgingBucket
    invoice_status: InvoiceStatus
    dispute_status: DisputeStatus
    dispute_reason: str = ""
    collection_status: CollectionStatus
    reminder_count: int = 0
    last_collection_contact: Optional[str] = None
    days_since_contact: Optional[int] = None
    promised_pay_date: Optional[str] = None
    promise_still_open: bool = False
    on_time_rate: float = 0
    average_days_late: int = 0
    payment_behavior: str = ""
    strategic: bool = False
    risk_flag: str = ""
    cooldown_active: bool = False
    suggested_priority: str = "low"
    blocked_actions: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


class CollectionDecision(BaseModel):
    invoice_id: str
    customer_id: str
    customer_name: str
    action: CollectionAction
    outstanding_amount: float
    days_past_due: int
    reminder_count: int = 0
    reason: str
    evidence_used: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    human_approval_required: bool = False
    draft_message: Optional[str] = None
    policy_checks: list[str] = Field(default_factory=list)
    precedent_used: list[str] = Field(default_factory=list)
    precedent_affected: bool = False


class CollectionMessage(BaseModel):
    message_id: str
    invoice_id: str
    customer_id: str
    customer_name: str
    action: CollectionAction
    outstanding_amount: float
    draft_message: str
    reason: str
    evidence_used: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    human_approval_required: bool = False
    created_at: str
    as_of_date: str
    sent: bool = False


class CollectionRun(BaseModel):
    as_of_date: str
    started_at: str
    candidates: list[CollectionFacts] = Field(default_factory=list)
    decisions: list[CollectionDecision] = Field(default_factory=list)
    outbox: list[CollectionMessage] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    trace_path: Optional[str] = None


class MatchApplication(BaseModel):
    invoice_id: str
    amount: float


class CashMatchCandidate(BaseModel):
    candidate_id: str
    applications: list[MatchApplication]
    total_applied: float
    unapplied_amount: float
    match_type: str
    score: float = 0
    evidence: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class CashApplicationFacts(BaseModel):
    payment: CustomerPayment
    identified_customer_id: Optional[str] = None
    identified_customer_name: Optional[str] = None
    customer_confidence: float = 0
    open_invoices: list[CustomerInvoice] = Field(default_factory=list)
    candidates: list[CashMatchCandidate] = Field(default_factory=list)
    remittance_invoice_ids: list[str] = Field(default_factory=list)
    stale_invoice_ids: list[str] = Field(default_factory=list)
    missing_invoice_ids: list[str] = Field(default_factory=list)
    identity_conflicts: list[str] = Field(default_factory=list)
    precedents: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


class CashApplicationProposal(BaseModel):
    payment_id: str
    decision: CashDecision
    applications: list[MatchApplication] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reason: str
    evidence_used: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    review_question: Optional[str] = None
    precedent_used: list[str] = Field(default_factory=list)
    precedent_affected: bool = False


class CashReviewDecision(BaseModel):
    payment_id: str
    recommendation: CashDecision
    agree_with_preparer: bool
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    equally_plausible: bool = False
    material: bool = False


class ValidationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)


class InvoiceBalanceChange(BaseModel):
    invoice_id: str
    previous_outstanding: float
    applied_amount: float
    new_outstanding: float
    previous_status: InvoiceStatus
    new_status: InvoiceStatus


class ARJournalLine(BaseModel):
    account: str
    amount: float


class ARJournalEntry(BaseModel):
    entry_id: str
    period: str
    counterparty: str
    memo: str
    debit: ARJournalLine
    credit: ARJournalLine
    entry_type: ARJournalType
    related_payment_id: Optional[str] = None
    related_invoice_ids: list[str] = Field(default_factory=list)
    created_at: str = ""


class CashApplicationRecord(BaseModel):
    application_id: str
    payment_id: str
    applications: list[MatchApplication]
    total_applied: float
    unapplied_amount: float
    decision: CashDecision
    status: PaymentApplicationStatus
    posted: bool
    invoice_changes: list[InvoiceBalanceChange] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    created_at: str
    reason: str = ""


class HumanCorrection(BaseModel):
    correction_id: str
    payment_id: str
    applications: list[MatchApplication]
    reason: str
    reviewer: str = "human"
    created_at: str
    posted: bool = False


ReviewStatus = Literal["OPEN", "APPROVED", "CORRECTED", "REJECTED"]


class ARPrecedent(BaseModel):
    precedent_id: str
    customer_id: Optional[str] = None
    kind: str
    summary: str
    facts: dict = Field(default_factory=dict)
    source: str = "seed"
    support_count: int = 1
    source_payment_id: Optional[str] = None
    source_review_id: Optional[str] = None


class CashReviewItem(BaseModel):
    review_id: str
    payment_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    payment_amount: float
    payment_date: str
    remittance_text: str = ""
    invoice_reference: Optional[str] = None
    bank_reference: str = ""
    candidates: list[CashMatchCandidate] = Field(default_factory=list)
    proposed_applications: list[MatchApplication] = Field(default_factory=list)
    agent_recommendation: Optional[CashApplicationProposal] = None
    reviewer_recommendation: Optional[CashReviewDecision] = None
    ambiguities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0)
    trace_path: Optional[str] = None
    status: ReviewStatus = "OPEN"
    created_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None
    final_applications: list[MatchApplication] = Field(default_factory=list)
    differed_from_agent: bool = False


class AREvent(BaseModel):
    event_id: str
    event_type: str
    created_at: str
    payment_id: Optional[str] = None
    invoice_ids: list[str] = Field(default_factory=list)
    summary: str
    details: dict = Field(default_factory=dict)


class CashApplyTrace(BaseModel):
    payment_id: str
    started_at: str
    as_of_date: str
    payment: CustomerPayment
    facts: CashApplicationFacts
    preparer: CashApplicationProposal
    validation: ValidationResult
    reviewer: Optional[CashReviewDecision] = None
    final: CashApplicationProposal
    posted: bool = False
    record: Optional[CashApplicationRecord] = None
    state_changes: list[InvoiceBalanceChange] = Field(default_factory=list)
    journal_entries: list[ARJournalEntry] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    already_posted: bool = False
    trace_path: Optional[str] = None


class ARCloseSnapshot(BaseModel):
    as_of_date: str
    total_ar: float = 0
    current_ar: float = 0
    past_due_ar: float = 0
    disputed_ar: float = 0
    partially_paid_ar: float = 0
    unapplied_cash: float = 0
    aging_buckets: dict[str, float] = Field(default_factory=dict)
    open_invoice_count: int = 0
    expected_collections_7d: float = 0
    past_due_customer_count: int = 0
    payments_applied: int = 0
    payments_unapplied: int = 0
    payments_human_review: int = 0
    collection_outbox: int = 0


class ARState(BaseModel):
    invoices: dict[str, CustomerInvoice] = Field(default_factory=dict)
    payments: dict[str, CustomerPayment] = Field(default_factory=dict)
    applications: list[CashApplicationRecord] = Field(default_factory=list)
    outbox: list[CollectionMessage] = Field(default_factory=list)
    events: list[AREvent] = Field(default_factory=list)
    precedents: list[ARPrecedent] = Field(default_factory=list)
    journals: list[ARJournalEntry] = Field(default_factory=list)
    human_corrections: list[HumanCorrection] = Field(default_factory=list)
    reviews: list[CashReviewItem] = Field(default_factory=list)
    customers: dict[str, Customer] = Field(default_factory=dict)
    aliases: dict[str, str] = Field(default_factory=dict)
