"""Normalized integration models. Provider payloads stay provider-specific."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ProcessingStatus = Literal[
    "received",
    "verified",
    "duplicate",
    "ignored",
    "processed",
    "error",
    "rejected",
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WebhookEvent(BaseModel):
    provider: str
    provider_event_id: str
    event_type: str
    received_at: datetime = Field(default_factory=utcnow)
    provider_created_at: Optional[datetime] = None
    verified: bool = False
    raw_payload_hash: str
    processing_status: ProcessingStatus = "received"
    source_ref: Optional[str] = None
    receipt_count: int = 1
    normalized_id: Optional[str] = None
    downstream: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None


class PayoutLine(BaseModel):
    """One funds movement inside a processor payout.

    `amount` is major units for display. Prefer `amount_minor` (integer cents) for math.
    """

    line_type: str
    amount: float
    currency: str = "USD"
    reference: Optional[str] = None
    description: str = ""
    provider_object_id: Optional[str] = None
    amount_minor: Optional[int] = None
    fee_minor: Optional[int] = None
    net_minor: Optional[int] = None
    source_object_id: Optional[str] = None
    created: Optional[str] = None
    category: Optional[str] = None


class ProviderPayout(BaseModel):
    provider: str
    event_id: str
    payout_id: str
    status: str
    amount: int
    currency: str
    arrival_date: Optional[str] = None
    provider_created_at: Optional[str] = None
    source_event_type: str
    raw_source_ref: str
    reference: Optional[str] = None
    lines: list[PayoutLine] = Field(default_factory=list)
    bank_deposit_id: Optional[str] = None
    bank_deposit_amount: Optional[float] = None
    bank_deposit_currency: Optional[str] = None


class ReconciliationBreakdown(BaseModel):
    payout_id: str
    provider: str
    currency: str = "USD"
    gross_payments: float = 0.0
    refunds: float = 0.0
    chargebacks: float = 0.0
    fees: float = 0.0
    adjustments: float = 0.0
    other: float = 0.0
    expected_payout: float = 0.0
    actual_payout: float = 0.0
    difference: float = 0.0
    bank_deposit_amount: Optional[float] = None
    bank_deposit_id: Optional[str] = None
    bank_matched: bool = False
    matched: bool = False
    status: str = "MATCH"
    exceptions: list[str] = Field(default_factory=list)
    expected_payout_minor: int = 0
    actual_payout_minor: int = 0
    lines: list[PayoutLine] = Field(default_factory=list)


class EmailSourceRecord(BaseModel):
    """Mailbox-agnostic email record. Gmail and Outlook both produce this."""

    provider: str
    message_id: str
    mailbox: str = ""
    sender: str = ""
    subject: str = ""
    sent_at: Optional[str] = None
    body: str = ""
    thread_uri: Optional[str] = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class IntegrationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: str
    action: str
    status: str
    provider_event_id: Optional[str] = None
    duplicate: bool = False
    invoice_candidates: int = 0
    invoice_numbers: list[str] = Field(default_factory=list)
    classification: Optional[str] = None
    payout_id: Optional[str] = None
    payout_amount: Optional[float] = None
    payment_id: Optional[str] = None
    workflow: Optional[str] = None
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
