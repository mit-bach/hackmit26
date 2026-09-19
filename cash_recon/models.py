"""Structured bank-reconciliation records. Amounts are major units for display.

Arithmetic uses `amount_minor` (integer cents). Agents do not compute these.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from skills.models import AgentSkillTrace

MatchType = Literal[
    "EXACT_MATCH",
    "GROUPED_MATCH",
    "FEE_NETTED",
    "PROVIDER_PAYOUT",
    "TIMING_DIFFERENCE",
    "POSSIBLE_DUPLICATE_BANK_TXN",
    "POSSIBLE_DUPLICATE_REFUND",
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
    "UNEXPLAINED_DIFFERENCE",
    "UNMATCHED_BANK",
    "UNMATCHED_LEDGER",
]

Disposition = Literal[
    "MATCHED",
    "EXPLAINED_EXCEPTION",
    "OUTSTANDING_TIMING_ITEM",
    "HUMAN_REVIEW",
]

PeriodStatus = Literal["RECONCILED", "OPEN", "FAILED_TIE"]
ReviewerStatus = Literal["CONFIRMED", "HUMAN_REVIEW", "REJECTED"]
CashDirection = Literal["inflow", "outflow"]

BANK_FEE_ACCOUNT = "6100-Bank-Fees"
CASH_ACCOUNT = "1000-Cash"


class BankTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    transaction_id: str
    date: str
    amount: float
    currency: str = "USD"
    description: str = ""
    reference: str = ""
    counterparty: str = ""
    transaction_type: str = "other"
    source: str = "bank"
    provider: Optional[str] = None
    period: str = ""
    amount_minor: int = 0
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry_id: str
    date: str
    amount: float
    currency: str = "USD"
    account: str = CASH_ACCOUNT
    counterparty: str = ""
    reference: str = ""
    description: str = ""
    entry_type: str = "other"
    period: str = ""
    source: str = "gl"
    amount_minor: int = 0
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class FeeEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evidence_id: str
    date: str
    amount: float
    fee_type: str = "bank_fee"
    reference: str = ""
    description: str = ""
    source: str = "bank_advice"
    amount_minor: int = 0
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class PeriodBalances(BaseModel):
    opening_bank: float
    opening_ledger: float
    as_of_date: str
    currency: str = "USD"
    opening_bank_minor: int = 0
    opening_ledger_minor: int = 0


class ProposedJournalLine(BaseModel):
    account: str
    amount: float
    amount_minor: int = 0
    side: Literal["debit", "credit"]


class ProposedJournalEntry(BaseModel):
    memo: str
    lines: list[ProposedJournalLine]
    related_bank_ids: list[str] = Field(default_factory=list)
    related_ledger_ids: list[str] = Field(default_factory=list)
    posted: bool = False
    support: str = ""


class MatchCandidate(BaseModel):
    candidate_id: str
    match_type: MatchType
    bank_transaction_ids: list[str]
    ledger_entry_ids: list[str]
    bank_amount: float
    ledger_amount: float
    difference: float
    bank_amount_minor: int = 0
    ledger_amount_minor: int = 0
    difference_minor: int = 0
    confidence: float = 0
    score: float = 0
    evidence: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    fee_evidence_ids: list[str] = Field(default_factory=list)
    provider: Optional[str] = None
    provider_payout_id: Optional[str] = None
    provider_status: Optional[str] = None
    proposed_adjusting_entries: list[ProposedJournalEntry] = Field(default_factory=list)


class ReconciliationMatch(BaseModel):
    reconciliation_id: str
    period: str
    match_key: str = ""
    bank_transaction_ids: list[str] = Field(default_factory=list)
    ledger_entry_ids: list[str] = Field(default_factory=list)
    match_type: MatchType
    bank_amount: float
    ledger_amount: float
    difference: float
    bank_amount_minor: int = 0
    ledger_amount_minor: int = 0
    difference_minor: int = 0
    confidence: float = 0
    status: Disposition
    explanation: str = ""
    evidence: list[str] = Field(default_factory=list)
    control_findings: list[str] = Field(default_factory=list)
    proposed_adjusting_entries: list[ProposedJournalEntry] = Field(default_factory=list)
    reviewer_status: ReviewerStatus = "CONFIRMED"
    human_review: bool = False
    candidate_id: Optional[str] = None
    provider: Optional[str] = None
    provider_payout_id: Optional[str] = None
    provider_status: Optional[str] = None
    calculations: dict[str, Any] = Field(default_factory=dict)


class PreparerSelection(BaseModel):
    case_id: str
    selected_candidate_id: Optional[str] = None
    disposition: Disposition
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    review_question: Optional[str] = None


class InvestigationNote(BaseModel):
    case_id: str
    issues_investigated: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    supported_explanations: list[str] = Field(default_factory=list)
    unsupported_hypotheses: list[str] = Field(default_factory=list)
    recommendation: Disposition
    confidence: float = Field(ge=0, le=1)
    human_review: bool = False
    evidence_used: list[str] = Field(default_factory=list)


class ReviewerVerdict(BaseModel):
    case_id: str
    reviewer_status: ReviewerStatus
    disposition: Disposition
    agree_with_preparer: bool = True
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    arithmetic_ok: bool = True
    human_review: bool = False


class ValidationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    reasons: list[str] = Field(default_factory=list)


class MatchTrace(BaseModel):
    reconciliation_id: str
    period: str
    match_type: MatchType
    status: Disposition
    bank_transactions: list[BankTransaction] = Field(default_factory=list)
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    candidates: list[MatchCandidate] = Field(default_factory=list)
    calculations: dict[str, Any] = Field(default_factory=dict)
    preparer: Optional[PreparerSelection] = None
    investigation: Optional[InvestigationNote] = None
    validation: Optional[ValidationResult] = None
    reviewer: Optional[ReviewerVerdict] = None
    final: ReconciliationMatch
    proposed_journal_entries: list[ProposedJournalEntry] = Field(default_factory=list)
    human_review: bool = False
    evidence: list[str] = Field(default_factory=list)
    control_findings: list[str] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    replay: bool = False
    trace_path: Optional[str] = None


class TieOut(BaseModel):
    bank_ending: float
    ledger_ending: float
    bank_ending_minor: int
    ledger_ending_minor: int
    break_amount: float
    break_minor: int
    reconciling_sum: float
    reconciling_sum_minor: int
    tied: bool
    items: list[dict[str, Any]] = Field(default_factory=list)
    formula: str = ""


class EvaluationMetrics(BaseModel):
    period: str
    total_bank_transactions: int = 0
    exact_matches: int = 0
    grouped_matches: int = 0
    provider_matches: int = 0
    true_exceptions: int = 0
    false_matches: int = 0
    false_exception_flags: int = 0
    unexplained_items: int = 0
    human_review_count: int = 0
    precision: float = 0
    recall: float = 0
    arithmetic_tied: bool = False
    ground_truth_used: bool = False


class CashReconciliationReport(BaseModel):
    period: str
    run_id: str
    started_at: str
    opening_bank: float
    opening_ledger: float
    bank_ending: float
    ledger_ending: float
    reconciled_amount: float
    outstanding_timing: float
    unexplained_difference: float
    human_review_count: int = 0
    period_status: PeriodStatus
    arithmetic_tied: bool
    tie_out: TieOut
    matches: list[ReconciliationMatch] = Field(default_factory=list)
    traces: list[MatchTrace] = Field(default_factory=list)
    control_findings: list[str] = Field(default_factory=list)
    agents: list[AgentSkillTrace] = Field(default_factory=list)
    used_agent: bool = False
    replay: bool = False
    metrics: Optional[EvaluationMetrics] = None
    trace_path: Optional[str] = None
    trace_dir: Optional[str] = None
