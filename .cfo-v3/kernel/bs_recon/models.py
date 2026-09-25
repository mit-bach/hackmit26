from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


ReconStatus = Literal[
    "NOT_STARTED",
    "IN_PROGRESS",
    "MATCHED",
    "EXPLAINED_DIFFERENCE",
    "HUMAN_REVIEW",
    "BLOCKED",
    "SIGNED_OFF",
]
ItemClassification = Literal[
    "exact_match",
    "timing_difference",
    "unexplained_difference",
    "missing_evidence",
    "stale_evidence",
    "duplicate_support",
    "arithmetic_inconsistency",
]
ItemStatus = Literal["open", "explained", "unexplained", "cleared"]
Finding = Literal[
    "exact_match",
    "explained_timing_difference",
    "unexplained_difference",
    "missing_evidence",
    "stale_evidence",
    "duplicate_support",
    "arithmetic_inconsistency",
]


class ReconcilingItem(BaseModel):
    item_id: str
    description: str
    amount: float
    source: str
    expected_resolution_date: Optional[str] = None
    classification: ItemClassification
    status: ItemStatus = "open"
    evidence_refs: list[str] = Field(default_factory=list)


class BalanceSheetReconciliation(BaseModel):
    reconciliation_id: str
    period: str
    account_id: str
    account_name: str
    ledger_balance: float
    evidence_balance: float
    difference: float
    status: ReconStatus = "NOT_STARTED"
    preparer: str = "Balance Sheet Reconciliation Preparer"
    reviewer: str = "Balance Sheet Reconciliation Reviewer"
    evidence_refs: list[str] = Field(default_factory=list)
    reconciling_items: list[ReconcilingItem] = Field(default_factory=list)
    supporting_source: str = ""
    explanation: str = ""
    finding: Finding = "exact_match"
    created_at: str = ""
    reviewed_at: Optional[str] = None
    ledger_source: str = ""
    calculations: dict = Field(default_factory=dict)
    review_decision: Optional[str] = None
    supporting_balance: float = 0
    review_status: str = ""
    blocking_items: list[str] = Field(default_factory=list)
    proposed_adjustments: list[str] = Field(default_factory=list)
    preparer_name: str = "Balance Sheet Reconciliation Preparer"
    reviewer_name: str = "Balance Sheet Reconciliation Reviewer"


class ReconPacket(BaseModel):
    account_id: str
    account_name: str
    period: str
    ledger_balance: float
    evidence_balance: float
    ledger_source: str
    evidence_source: str
    evidence_refs: list[str] = Field(default_factory=list)
    reconciling_items: list[ReconcilingItem] = Field(default_factory=list)
    stale_evidence: bool = False
    duplicate_support: bool = False
    missing_evidence: bool = False
    calculations: dict = Field(default_factory=dict)


class ReconDecision(BaseModel):
    account_id: str
    finding: Finding
    status: ReconStatus
    explanation: str
    confidence: float = Field(ge=0, le=1, default=0)
    escalate: bool = False
    evidence_used: list[str] = Field(default_factory=list)


class ReconReview(BaseModel):
    account_id: str
    decision: Literal["APPROVE", "REJECT", "REQUEST_EVIDENCE", "ESCALATE"]
    sign_off: bool = False
    agree_with_preparer: bool = True
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)


class ReconTrace(BaseModel):
    reconciliation_id: str
    period: str
    account_id: str
    packet: ReconPacket
    preparer: Optional[ReconDecision] = None
    reviewer: Optional[ReconReview] = None
    final: BalanceSheetReconciliation
    used_agent: bool = False


class ReconRun(BaseModel):
    period: str
    reconciliations: list[BalanceSheetReconciliation] = Field(default_factory=list)
    traces: list[ReconTrace] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    signed_off: int = 0
    used_agent: bool = False
