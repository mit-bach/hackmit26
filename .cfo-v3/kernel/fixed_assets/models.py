from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


DepreciationMethod = Literal["straight_line"]
AssetStatus = Literal["active", "fully_depreciated", "review", "duplicate"]
AssetClass = Literal["tangible", "intangible"]
ScheduleLineStatus = Literal["scheduled", "posted", "skipped"]
CapitalDecision = Literal["capitalize", "expense", "duplicate_review", "insufficient_evidence"]


class FixedAsset(BaseModel):
    model_config = ConfigDict(extra="ignore")

    asset_id: str
    description: str
    vendor: str
    acquisition_date: str
    placed_in_service_date: str
    cost: float
    salvage_value: float = 0
    useful_life_months: int
    depreciation_method: DepreciationMethod = "straight_line"
    asset_account: str
    accumulated_depreciation_account: str
    depreciation_expense_account: str
    evidence_refs: list[str] = Field(default_factory=list)
    status: AssetStatus = "active"
    asset_class: AssetClass = "tangible"
    source_document_id: str = ""
    transaction_id: str = ""
    created_at: str = ""


class DepreciationScheduleLine(BaseModel):
    asset_id: str
    period: str
    beginning_book_value: float
    depreciation_amount: float
    ending_book_value: float
    status: ScheduleLineStatus = "scheduled"
    journal_entry_id: Optional[str] = None
    posted_in_period: Optional[str] = None


class CapitalCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    vendor: str
    description: str
    amount: float
    invoice_date: str
    source_document_id: str = ""
    transaction_id: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    useful_life_months: int = 36
    salvage_value: float = 0
    asset_class: AssetClass = "tangible"
    asset_account: str = "Computer Equipment"
    accumulated_depreciation_account: str = "Accumulated Depreciation - Equipment"
    depreciation_expense_account: str = "Depreciation Expense"


class AssetDecision(BaseModel):
    asset_id: str
    decision: CapitalDecision
    confidence: float = Field(ge=0, le=1, default=0)
    reasoning_summary: str = ""
    evidence_used: list[str] = Field(default_factory=list)
    duplicate_of: Optional[str] = None


class AssetReview(BaseModel):
    asset_id: str
    decision: Literal["APPROVE", "REJECT", "REQUEST_EVIDENCE", "ESCALATE"]
    agree_with_preparer: bool = True
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)


class AssetTrace(BaseModel):
    asset_id: str
    period: str
    preparer: Optional[AssetDecision] = None
    reviewer: Optional[AssetReview] = None
    lines_posted: list[DepreciationScheduleLine] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    explanation: str = ""
    duplicate_of: Optional[str] = None
    used_agent: bool = False


class AssetRun(BaseModel):
    period: str
    assets: list[FixedAsset] = Field(default_factory=list)
    lines_posted: list[DepreciationScheduleLine] = Field(default_factory=list)
    duplicates: list[dict] = Field(default_factory=list)
    traces: list[AssetTrace] = Field(default_factory=list)
    journal_entry_ids: list[str] = Field(default_factory=list)
    register_cost: float = 0
    register_accum: float = 0
    register_nbv: float = 0
    exceptions: list[str] = Field(default_factory=list)
    used_agent: bool = False
