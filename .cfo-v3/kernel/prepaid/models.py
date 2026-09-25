from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from memory.models import MemoryLookup


AmortizationMethod = Literal["straight_line_monthly", "daily_prorate", "immediate_expense"]
PrepaidStatus = Literal["active", "fully_amortized", "blocked", "review"]
ScheduleLineStatus = Literal["scheduled", "posted", "skipped"]
TreatmentDecision = Literal[
    "straight_line_monthly",
    "daily_prorate",
    "immediate_expense",
    "insufficient_evidence",
]


class PrepaidItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prepaid_id: str
    vendor: str
    description: str
    source_document_id: str = ""
    total_amount: float
    start_date: str
    end_date: str
    initial_account: str
    expense_account: str
    amortization_method: AmortizationMethod = "straight_line_monthly"
    currency: str = "USD"
    status: PrepaidStatus = "active"
    created_at: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    transaction_id: str = ""
    late_discovery: bool = False


class PrepaidScheduleLine(BaseModel):
    prepaid_id: str
    period: str
    amount: float
    status: ScheduleLineStatus = "scheduled"
    journal_entry_id: Optional[str] = None
    evidence_refs: list[str] = Field(default_factory=list)
    method: AmortizationMethod = "straight_line_monthly"
    days_in_period: int = 0
    posted_in_period: Optional[str] = None


class TreatmentCandidate(BaseModel):
    method: AmortizationMethod
    applicable: bool
    amount: Optional[float] = None
    rationale: str
    periods: int = 0


class PrepaidDecision(BaseModel):
    prepaid_id: str
    selected_method: Optional[TreatmentDecision] = None
    confidence: float = Field(ge=0, le=1, default=0)
    reasoning_summary: str = ""
    evidence_used: list[str] = Field(default_factory=list)
    escalate: bool = False


class PrepaidReview(BaseModel):
    prepaid_id: str
    decision: Literal["APPROVE", "REJECT", "REQUEST_EVIDENCE", "ESCALATE"]
    agree_with_preparer: bool = True
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)


class PrepaidTrace(BaseModel):
    prepaid_id: str
    period: str
    candidates: list[TreatmentCandidate] = Field(default_factory=list)
    preparer: Optional[PrepaidDecision] = None
    reviewer: Optional[PrepaidReview] = None
    selected_method: Optional[str] = None
    lines_posted: list[PrepaidScheduleLine] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    explanation: str = ""
    used_agent: bool = False
    memory_lookup: Optional[MemoryLookup] = None
    written_memory_id: Optional[str] = None


class PrepaidRun(BaseModel):
    period: str
    items: list[PrepaidItem] = Field(default_factory=list)
    lines_posted: list[PrepaidScheduleLine] = Field(default_factory=list)
    skipped: list[dict] = Field(default_factory=list)
    traces: list[PrepaidTrace] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    remaining_by_account: dict[str, float] = Field(default_factory=dict)
    exceptions: list[str] = Field(default_factory=list)
    used_agent: bool = False
