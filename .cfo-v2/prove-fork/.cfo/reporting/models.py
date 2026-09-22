from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from skills.models import AgentSkillTrace


AccountClass = Literal["revenue", "cogs", "opex", "cash", "ar", "ap", "other"]
ComparisonKind = Literal["prior_period", "budget", "forecast"]
ContributorConfidence = Literal["high", "medium", "low"]
ContributorKind = Literal["verified", "likely", "unexplained"]
ReceivableStatus = Literal["open", "partially_paid", "paid", "overdue"]
ForecastSourceType = Literal["invoice", "receivable", "payroll", "other"]
ForecastVarianceKind = Literal[
    "timing",
    "amount",
    "new_unforecast",
    "removed_cancelled",
    "unexplained",
]
ReviewDecision = Literal["APPROVE", "REJECT", "REQUEST_EVIDENCE", "ESCALATE"]
EscalationStatus = Literal["none", "reviewer", "human"]


class ChartAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")

    account_id: str
    name: str
    account_class: AccountClass
    aliases: list[str] = Field(default_factory=list)


class ReportingLine(BaseModel):
    """One account movement. Totals are summed in Python, never by an agent."""

    model_config = ConfigDict(extra="ignore")

    line_id: str
    entry_id: str
    transaction_id: str
    period: str
    posting_date: str
    account: str
    account_class: AccountClass
    side: Literal["debit", "credit"]
    amount: float
    memo: str = ""
    vendor: str = ""
    customer: str = ""
    product: str = ""
    category: str = ""
    quantity: Optional[float] = None
    rate: Optional[float] = None
    source_workflow: str = "reporting"
    source_document_id: str = ""
    ledger_entry_id: str = ""
    trace_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    idempotency_key: str = ""


class PeriodBalances(BaseModel):
    period: str
    as_of_date: str
    cash: float = 0
    ap: float = 0
    ar: float = 0
    currency: str = "USD"


class BudgetPeriod(BaseModel):
    period: str
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    cash: Optional[float] = None
    ap: Optional[float] = None
    ar: Optional[float] = None


class ReportingAssumptions(BaseModel):
    ar_fallback_days_after_due: int = 0
    ar_default_confidence: float = 0.7
    low_confidence_threshold: float = 0.5
    variance_tolerance: float = 0.02
    materiality_abs: float = 1000.0
    materiality_pct: float = 0.01
    week_start: str = "monday"
    forecast_actuals_as_of: str = "2026-10-04"


class FinancialMetric(BaseModel):
    metric: str
    period: str
    current_value: float
    comparison_value: Optional[float] = None
    comparison_kind: Optional[ComparisonKind] = None
    comparison_period: Optional[str] = None
    absolute_variance: Optional[float] = None
    relative_variance: Optional[float] = None
    dollar_variance: Optional[float] = None
    unit: Literal["usd", "ratio"] = "usd"
    source: str = "ledger"
    metric_id: str = ""
    evidence_refs: list[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        if not self.metric_id:
            self.metric_id = f"metric:{self.metric}:{self.period}"


class IncomeStatement(BaseModel):
    period: str
    revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    operating_expenses: float
    operating_income: float
    cash: float = 0
    ap: float = 0
    ar: float = 0
    metrics: list[FinancialMetric] = Field(default_factory=list)
    line_ids: list[str] = Field(default_factory=list)


class AttributedTransaction(BaseModel):
    transaction_id: str
    line_id: str
    entry_id: str
    source_document_id: str = ""
    vendor: str = ""
    customer: str = ""
    account: str
    category: str = ""
    amount: float
    posting_date: str
    period: str
    source_workflow: str = ""
    ledger_entry_id: str = ""
    trace_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    quantity: Optional[float] = None
    rate: Optional[float] = None


class QuantityRateMix(BaseModel):
    quantity_effect: Optional[float] = None
    rate_effect: Optional[float] = None
    mix_effect: Optional[float] = None
    residual: Optional[float] = None


class VarianceContributor(BaseModel):
    label: str
    amount: float
    share_of_variance: float = 0
    source_transaction_ids: list[str] = Field(default_factory=list)
    ledger_entry_ids: list[str] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)
    vendor: str = ""
    customer: str = ""
    account: str = ""
    category: str = ""
    confidence: ContributorConfidence = "high"
    kind: ContributorKind = "verified"
    quantity_rate_mix: Optional[QuantityRateMix] = None
    transactions: list[AttributedTransaction] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class DrilldownNode(BaseModel):
    level: Literal["metric", "account", "category", "entity", "transaction", "evidence"]
    key: str
    label: str
    amount: float
    children: list["DrilldownNode"] = Field(default_factory=list)
    transaction_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class VarianceExplanation(BaseModel):
    variance_id: str
    metric: str
    period: str
    comparison_period: str = ""
    comparison_kind: ComparisonKind = "prior_period"
    current_value: float
    comparison_value: float
    variance: float
    dollar_variance: float
    contributors: list[VarianceContributor] = Field(default_factory=list)
    unexplained_amount: float = 0
    reconciled: bool = True
    residual_tolerance: float = 0.02
    narrative: str = ""
    material: bool = False
    unsupported_claims: list[str] = Field(default_factory=list)
    drilldown: list[DrilldownNode] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    trace_id: str = ""


class VarianceTrace(BaseModel):
    metric: str
    period: str
    comparison_period: str
    dollar_variance: float
    contributors: list[VarianceContributor] = Field(default_factory=list)
    transactions: list[AttributedTransaction] = Field(default_factory=list)
    drilldown: list[DrilldownNode] = Field(default_factory=list)
    unexplained_amount: float = 0
    reconciled: bool = True


class Receivable(BaseModel):
    """Canonical customer receivable. Adapter over AR CustomerInvoice."""

    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    customer_id: str
    customer_name: str = ""
    invoice_date: str
    due_date: str
    amount: float
    outstanding_amount: float
    status: ReceivableStatus = "open"
    promised_pay_date: Optional[str] = None
    payment_behavior: str = ""
    on_time_rate: float = 0.8
    average_days_late: int = 0
    currency: str = "USD"
    disputed: bool = False


class CollectionExpectation(BaseModel):
    invoice_id: str
    customer_id: str
    expected_date: str
    amount: float
    confidence: float = Field(ge=0, le=1)
    rationale: str
    rule: str
    low_confidence: bool = False
    source_document_id: str = ""


class PayrollSchedule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schedule_id: str
    pay_date: str
    expected_amount: float
    description: str = "Payroll"
    confidence: float = 0.99


class APForecastDecision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    hold: bool = False
    scheduled_pay_date: Optional[str] = None
    approval_state: str = "approved"
    reason: str = ""
    source: str = "overlay"


class ForecastLine(BaseModel):
    line_id: str
    source_type: ForecastSourceType
    source_id: str
    expected_date: str
    amount: float
    confidence: float = Field(ge=0, le=1)
    rationale: str
    week_start: str = ""
    vendor: str = ""
    customer: str = ""
    hold: bool = False
    committed: bool = True
    source_workflow: str = ""
    trace_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class CashForecastWeek(BaseModel):
    week_start: str
    week_end: str = ""
    beginning_cash: float
    ar_collections: float = 0
    other_inflows: float = 0
    ap_payments: float = 0
    payroll: float = 0
    other_outflows: float = 0
    ending_cash: float
    line_ids: list[str] = Field(default_factory=list)


class ForecastChange(BaseModel):
    source_id: str
    source_type: str
    field: str
    previous: str = ""
    current: str = ""
    reason: str = ""


class CashForecastSnapshot(BaseModel):
    forecast_id: str
    as_of_date: str
    horizon_weeks: int = 13
    beginning_cash: float
    weeks: list[CashForecastWeek] = Field(default_factory=list)
    lines: list[ForecastLine] = Field(default_factory=list)
    assumptions: dict = Field(default_factory=dict)
    agent_judgments: list[str] = Field(default_factory=list)
    changes_from_prior: list[ForecastChange] = Field(default_factory=list)
    source_trace_ids: list[str] = Field(default_factory=list)
    low_confidence_lines: list[str] = Field(default_factory=list)
    held_ap_ids: list[str] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    created_at: str = ""
    version: int = 1
    immutable: bool = True
    trace_id: str = ""
    trace_path: Optional[str] = None


class CashActualMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    movement_id: str
    source_type: str
    source_id: str
    date: str
    amount: float
    kind: Literal["inflow", "outflow"]
    description: str = ""
    bank_transaction_id: str = ""
    ledger_entry_id: str = ""
    reconciliation_id: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class ForecastWeekActual(BaseModel):
    week_start: str
    forecast_inflows: float = 0
    actual_inflows: float = 0
    inflow_variance: float = 0
    forecast_outflows: float = 0
    actual_outflows: float = 0
    outflow_variance: float = 0
    forecast_ending_cash: float = 0
    actual_ending_cash: float = 0
    ending_cash_variance: float = 0


class ForecastVarianceContributor(BaseModel):
    label: str
    amount: float
    kind: ForecastVarianceKind
    source_id: str = ""
    source_type: str = ""
    share_of_variance: float = 0
    evidence_refs: list[str] = Field(default_factory=list)


class ForecastVarianceExplanation(BaseModel):
    analysis_id: str
    forecast_id: str
    as_of_date: str
    weeks: list[ForecastWeekActual] = Field(default_factory=list)
    contributors: list[ForecastVarianceContributor] = Field(default_factory=list)
    unexplained_amount: float = 0
    total_ending_cash_variance: float = 0
    reconciled: bool = True
    narrative: str = ""
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    trace_id: str = ""
    trace_path: Optional[str] = None


class BoardPackSection(BaseModel):
    title: str
    metrics: list[FinancialMetric] = Field(default_factory=list)
    narrative: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    items: list[str] = Field(default_factory=list)


class BoardPack(BaseModel):
    pack_id: str
    period: str
    as_of_date: str
    sections: list[BoardPackSection] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    markdown: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    forecast_id: str = ""
    variance_ids: list[str] = Field(default_factory=list)
    trace_id: str = ""
    trace_path: Optional[str] = None


class ReviewFinding(BaseModel):
    code: str
    detail: str
    severity: Literal["info", "warning", "material"] = "warning"
    evidence_refs: list[str] = Field(default_factory=list)


class ReviewVerdict(BaseModel):
    review_id: str
    subject_id: str
    role: str
    decision: ReviewDecision
    agree_with_preparer: bool = True
    reasons: list[str] = Field(default_factory=list)
    findings: list[ReviewFinding] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    escalation: EscalationStatus = "none"
    confidence: float = Field(ge=0, le=1, default=0.9)
    agents: list[AgentSkillTrace] = Field(default_factory=list)


class ProvenanceLink(BaseModel):
    """Visible cross-workflow chain for one canonical document."""

    source_document_id: str
    ap_decision: str = ""
    scheduled_payment: str = ""
    forecast_line_id: str = ""
    forecast_id: str = ""
    bank_transaction_id: str = ""
    reconciliation_id: str = ""
    ledger_entry_id: str = ""
    variance_id: str = ""
    board_pack_id: str = ""
    close_link_id: str = ""
    trace_ids: list[str] = Field(default_factory=list)


class ReportingRun(BaseModel):
    run_id: str
    period: str
    comparison_period: str
    as_of_date: str
    statement: Optional[IncomeStatement] = None
    comparison_statement: Optional[IncomeStatement] = None
    metrics: list[FinancialMetric] = Field(default_factory=list)
    variances: list[VarianceExplanation] = Field(default_factory=list)
    forecast: Optional[CashForecastSnapshot] = None
    forecast_variance: Optional[ForecastVarianceExplanation] = None
    board_pack: Optional[BoardPack] = None
    reviews: list[ReviewVerdict] = Field(default_factory=list)
    provenance: list[ProvenanceLink] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    escalations: list[str] = Field(default_factory=list)
    trace_path: Optional[str] = None
