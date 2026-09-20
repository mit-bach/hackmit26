from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from memory.models import MemoryLookup
from skills.models import AgentSkillTrace


EstimationMethod = Literal[
    "last_invoice",
    "simple_average",
    "recent_average",
    "weighted_recent_average",
    "linear_trend",
    "seasonal_prior_year",
    "contract_commitment",
    "usage_run_rate",
    "goods_receipt",
    "purchase_order",
    "conservative_minimum",
]

AccrualStatus = Literal["accrual_required", "no_accrual_needed", "insufficient_evidence"]
AccrualRecordStatus = Literal["open", "reversed", "reconciled"]


class AccrualInvoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    vendor: str
    amount: float
    invoice_date: str
    service_period: str
    currency: str = "USD"
    expense_account: str = ""
    vendor_invoice_number: str = ""
    description: str = ""
    po_id: Optional[str] = None
    source: str = "historical"


class VendorContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contract_id: str
    vendor: str
    start_date: str
    end_date: str
    billing_cadence: Literal["monthly", "quarterly", "annual", "as_needed"]
    amount: Optional[float] = None
    currency: str = "USD"
    expense_account: str = ""
    billed_in_arrears: bool = True
    monthly_minimum: float = 0
    description: str = ""


class VendorUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor: str
    period: str
    metric: str
    quantity: float
    unit_price: float
    currency: str = "USD"
    partial_period: bool = False
    as_of: str = ""
    description: str = ""


class EstimateCandidate(BaseModel):
    method: EstimationMethod
    applicable: bool
    amount: Optional[float] = None
    rationale: str
    inputs: dict = Field(default_factory=dict)


class JournalLine(BaseModel):
    account: str
    amount: float


class JournalEntry(BaseModel):
    entry_id: str
    period: str
    vendor: str
    memo: str
    debit: JournalLine
    credit: JournalLine
    entry_type: Literal["accrual", "reversal", "invoice"] = "accrual"
    related_accrual_id: Optional[str] = None
    created_at: str = ""


class AccrualDecision(BaseModel):
    vendor: str
    period: str
    status: AccrualStatus
    estimated_amount: Optional[float] = None
    currency: str = "USD"
    confidence: float = Field(ge=0, le=1)
    estimation_method: Optional[EstimationMethod] = None
    evidence: list[str] = Field(default_factory=list)
    reasoning_summary: str
    expense_account: str = ""
    journal_entry: Optional[JournalEntry] = None
    accrual_id: Optional[str] = None
    trace_id: Optional[str] = None
    discovery_trace_id: Optional[str] = None


class ExpectedVendor(BaseModel):
    vendor: str
    period: str
    signals: list[str] = Field(default_factory=list)
    invoice_already_received: bool = False
    current_invoice_ids: list[str] = Field(default_factory=list)
    expense_account: str = ""


class DiscoverySignal(BaseModel):
    type: str
    detail: str
    confidence: float = Field(ge=0, le=1)


class DiscoveryResult(BaseModel):
    vendor: str
    period: str
    expense_expected: bool
    invoice_received: bool
    missing_bill_candidate: bool
    expectation_confidence: float = Field(ge=0, le=1)
    signals: list[DiscoverySignal] = Field(default_factory=list)
    reason: str
    discovery_trace_id: str = ""
    current_invoice_ids: list[str] = Field(default_factory=list)
    indicative_amount: Optional[float] = None
    indicative_method: Optional[str] = None


class DiscoveryReport(BaseModel):
    period: str
    results: list[DiscoveryResult] = Field(default_factory=list)
    expected_count: int = 0
    invoices_received_count: int = 0
    missing_count: int = 0
    discovery_run_id: str = ""


class BacktestRecord(BaseModel):
    vendor: str
    period: str
    selected_method: Optional[str] = None
    estimated_amount: Optional[float] = None
    actual_invoice_id: str
    actual_amount: float
    error: Optional[float] = None
    absolute_error: Optional[float] = None
    percentage_error: Optional[float] = None
    expense_expected: bool = False
    expectation_confidence: float = 0
    estimate_confidence: float = 0
    discovery_trace_id: str = ""
    accrual_trace_id: str = ""
    hidden_invoice_id: str = ""
    future_leak_detected: bool = False
    estimate_committed_before_reveal: bool = False


class MethodMetrics(BaseModel):
    method: str
    observations: int
    mean_absolute_error: float = 0
    mean_absolute_percentage_error: Optional[float] = None


class BacktestMetrics(BaseModel):
    invoices_tested: int
    mean_absolute_error: float = 0
    median_absolute_error: float = 0
    mean_absolute_percentage_error: Optional[float] = None
    mean_signed_error: float = 0
    within_5_percent: Optional[float] = None
    within_10_percent: Optional[float] = None
    by_method: list[MethodMetrics] = Field(default_factory=list)


class BacktestReport(BaseModel):
    records: list[BacktestRecord] = Field(default_factory=list)
    metrics: BacktestMetrics
    periods: list[str] = Field(default_factory=list)
    trace_path: Optional[str] = None
    recent_average_analysis: Optional[dict] = None


class ComparisonRecord(BaseModel):
    vendor: str
    period: str
    policy_method: Optional[str] = None
    policy_amount: Optional[float] = None
    agent_method: Optional[str] = None
    agent_amount: Optional[float] = None
    agent_status: str = ""
    agree: Optional[bool] = None
    diagnostic_warnings: list[str] = Field(default_factory=list)
    candidate_methods: list[str] = Field(default_factory=list)
    agent_mape: Optional[float] = None
    policy_mape: Optional[float] = None
    discovery_trace_id: str = ""
    accrual_trace_id: str = ""


class ComparisonReport(BaseModel):
    period: str
    comparisons: list[ComparisonRecord] = Field(default_factory=list)
    agreements: int = 0
    disagreements: int = 0
    trace_path: Optional[str] = None


class LiveEvalTrial(BaseModel):
    vendor: str
    run: int
    status: str
    method: Optional[str] = None
    amount: Optional[float] = None


class LiveEvalVendorSummary(BaseModel):
    vendor: str
    trials: int
    method_counts: dict[str, int] = Field(default_factory=dict)
    status_counts: dict[str, int] = Field(default_factory=dict)


class LiveEvalReport(BaseModel):
    period: str
    runs: int
    vendors: list[str] = Field(default_factory=list)
    trials: list[LiveEvalTrial] = Field(default_factory=list)
    summaries: list[LiveEvalVendorSummary] = Field(default_factory=list)
    trace_path: Optional[str] = None


class OpenAccrual(BaseModel):
    accrual_id: str
    vendor: str
    period: str
    estimated_amount: float
    currency: str = "USD"
    expense_account: str
    liability_account: str = "Accrued Expenses"
    status: AccrualRecordStatus = "open"
    estimation_method: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    journal_entry_id: str
    created_at: str
    trace_id: Optional[str] = None
    discovery_trace_id: Optional[str] = None
    reversal_entry_id: Optional[str] = None
    invoice_entry_id: Optional[str] = None
    actual_invoice_id: Optional[str] = None
    actual_amount: Optional[float] = None
    estimation_error: Optional[float] = None
    reconciled_at: Optional[str] = None


class TraceJournal(BaseModel):
    entry_id: Optional[str] = None
    debit_account: str
    credit_account: str
    amount: float


class ReconciliationResult(BaseModel):
    accrual_id: str
    vendor: str
    period: str
    estimated_amount: float
    actual_invoice_id: str
    actual_amount: float
    estimation_error: float
    absolute_error: float = 0
    percentage_error: Optional[float] = None
    reversal_entry_id: str
    invoice_entry_id: str
    trace_id: Optional[str] = None
    discovery_trace_id: Optional[str] = None
    accrual_trace_id: Optional[str] = None
    reconciliation_trace_id: Optional[str] = None
    expense_account: str = ""
    reversal: Optional[TraceJournal] = None
    invoice_entry: Optional[TraceJournal] = None


class CandidateEstimateView(BaseModel):
    method: str
    label: str
    amount: Optional[float] = None
    applicable: bool = False


class AgentSelection(BaseModel):
    decision: str
    method: Optional[str] = None
    amount: Optional[float] = None
    confidence: float = Field(ge=0, le=1)
    reason: str


class TraceEvidence(BaseModel):
    historical_invoices: list[dict] = Field(default_factory=list)
    current_invoices: list[dict] = Field(default_factory=list)
    contract: Optional[dict] = None
    usage: Optional[dict] = None
    purchase_orders: list[dict] = Field(default_factory=list)
    goods_receipts: list[dict] = Field(default_factory=list)


class VendorDecisionTrace(BaseModel):
    trace_id: str
    vendor: str
    period: str
    invoice_received: bool
    evidence: TraceEvidence
    candidate_estimates: list[CandidateEstimateView] = Field(default_factory=list)
    agent_selection: AgentSelection
    validation_errors: list[str] = Field(default_factory=list)
    safety_rules_triggered: list[str] = Field(default_factory=list)
    final_decision: str
    final_method: Optional[str] = None
    final_amount: Optional[float] = None
    confidence: float = Field(ge=0, le=1)
    rationale: str
    journal_entry: Optional[TraceJournal] = None
    accrual_id: Optional[str] = None
    tools_called: list[str] = Field(default_factory=list)
    discovery_trace_id: Optional[str] = None
    expectation_confidence: Optional[float] = None
    estimate_confidence: Optional[float] = None
    agent: Optional[AgentSkillTrace] = None
    policy_method: Optional[str] = None
    policy_amount: Optional[float] = None
    policy_agreement: Optional[bool] = None
    diagnostic_warnings: list[str] = Field(default_factory=list)
    memory_lookup: Optional[MemoryLookup] = None
    written_memory_id: Optional[str] = None


class AccrualPeriodReport(BaseModel):
    period: str
    vendors_reviewed: int
    accruals_created: list[AccrualDecision] = Field(default_factory=list)
    no_accrual_needed: list[AccrualDecision] = Field(default_factory=list)
    uncertain_items: list[AccrualDecision] = Field(default_factory=list)
    total_accrued_expense: float = 0
    traces: list[VendorDecisionTrace] = Field(default_factory=list)
    discovery: Optional[DiscoveryReport] = None
    ranked_missing: list[AccrualDecision] = Field(default_factory=list)
    trace_dir: Optional[str] = None
    trace_path: Optional[str] = None
