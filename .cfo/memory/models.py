"""Canonical organizational decision memory.

Stores concise, auditor-facing rationale — not unconstrained chain-of-thought.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

WorkflowName = Literal[
    "cash_reconciliation",
    "accounts_payable",
    "prepaid",
    "month_end_close",
]

EntityType = Literal["payment_provider", "vendor", "customer", "account"]


class MemoryEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: str
    label: str
    amount: Optional[float] = None
    amount_minor: Optional[int] = None
    reference: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class DecisionMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    decision_id: str
    period: str
    workflow: str
    entity_type: str
    entity_id: str
    situation_type: str
    situation_summary: str
    evidence: list[MemoryEvidence] = Field(default_factory=list)
    decision: str
    reasoning_summary: str
    accounting_treatment: str
    outcome: str
    reusable_precedent: str
    source_trace_ids: list[str] = Field(default_factory=list)
    created_at: str
    tags: list[str] = Field(default_factory=list)
    idempotency_key: str
    entity_name: Optional[str] = None
    accounting_category: Optional[str] = None
    support_count: int = 1


class MemoryQuery(BaseModel):
    workflow: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    situation_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    accounting_category: Optional[str] = None
    prior_to_period: Optional[str] = None
    exclude_period: Optional[str] = None
    limit: int = 5


class RetrievedPrecedent(BaseModel):
    decision_id: str
    period: str
    workflow: str
    entity_id: str
    situation_type: str
    situation_summary: str
    decision: str
    reasoning_summary: str
    accounting_treatment: str
    reusable_precedent: str
    outcome: str
    score: float = 0
    tags: list[str] = Field(default_factory=list)


class MemoryLookup(BaseModel):
    queried: bool = False
    memory_enabled: bool = True
    query: dict[str, Any] = Field(default_factory=dict)
    retrieved: list[str] = Field(default_factory=list)
    precedents: list[RetrievedPrecedent] = Field(default_factory=list)
    precedent_used: bool = False
    precedent_relevance: Optional[str] = None
    current_evidence_checked: bool = False
    evidence_supports_precedent: Optional[bool] = None
    deviation: Optional[str] = None
    decision: Optional[str] = None
    investigation_steps: int = 0
    skipped_hypotheses: list[str] = Field(default_factory=list)
