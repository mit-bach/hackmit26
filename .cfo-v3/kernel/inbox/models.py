"""Typed inbox envelopes, classifications, actions, and traces."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


COUNTERPARTY_AGENT = "Counterparty Message Agent"
FINANCE_INBOX_AGENT = "Finance Inbox Agent"

InboxClass = Literal[
    "VENDOR_INVOICE",
    "PURCHASE_ORDER",
    "GOODS_RECEIPT",
    "VENDOR_STATEMENT",
    "PAYMENT_CONFIRMATION",
    "CREDIT_MEMO",
    "CUSTOMER_REMITTANCE",
    "BANK_NOTICE",
    "CONTRACT_OR_QUOTE",
    "INTERNAL_REQUEST",
    "NON_FINANCE",
    "UNSUPPORTED_OR_UNRESOLVED",
]

InboxAction = Literal[
    "CREATE_AP_INVOICE",
    "UPDATE_EXISTING_AP_INVOICE",
    "ATTACH_SUPPORTING_EVIDENCE",
    "RECORD_GOODS_RECEIPT",
    "RECORD_PAYMENT_NOTICE",
    "RECORD_CUSTOMER_REMITTANCE",
    "ROUTE_TO_EXISTING_WORKFLOW",
    "REQUEST_MISSING_INFORMATION",
    "IGNORE",
    "REJECT_UNSAFE_REQUEST",
]

InboxStatus = Literal[
    "CREATED",
    "LINKED",
    "DUPLICATE_DELIVERY",
    "BUSINESS_DUPLICATE",
    "NEEDS_INFORMATION",
    "UNRESOLVED",
    "IGNORED",
    "REJECTED",
    "ROUTED",
    "PARSE_FAILURE",
    "UNSUPPORTED",
]

MatchStatus = Literal[
    "MATCHED",
    "UNMATCHED",
    "NON_PO",
    "EXCEPTION",
    "BLOCKED",
    "DUPLICATE",
    "NOT_APPLICABLE",
]


INBOX_CLASSES: tuple[str, ...] = (
    "VENDOR_INVOICE",
    "PURCHASE_ORDER",
    "GOODS_RECEIPT",
    "VENDOR_STATEMENT",
    "PAYMENT_CONFIRMATION",
    "CREDIT_MEMO",
    "CUSTOMER_REMITTANCE",
    "BANK_NOTICE",
    "CONTRACT_OR_QUOTE",
    "INTERNAL_REQUEST",
    "NON_FINANCE",
    "UNSUPPORTED_OR_UNRESOLVED",
)

INBOX_ACTIONS: tuple[str, ...] = (
    "CREATE_AP_INVOICE",
    "UPDATE_EXISTING_AP_INVOICE",
    "ATTACH_SUPPORTING_EVIDENCE",
    "RECORD_GOODS_RECEIPT",
    "RECORD_PAYMENT_NOTICE",
    "RECORD_CUSTOMER_REMITTANCE",
    "ROUTE_TO_EXISTING_WORKFLOW",
    "REQUEST_MISSING_INFORMATION",
    "IGNORE",
    "REJECT_UNSAFE_REQUEST",
)


class MessageAttachment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    mime_type: str = "text/plain"
    content: Optional[str] = None
    path: Optional[str] = None
    sha256: Optional[str] = None


class MessageEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: str
    thread_id: str
    in_reply_to: Optional[str] = None
    sender_name: str
    sender_address: str
    recipient_addresses: list[str] = Field(default_factory=list)
    subject: str
    body_text: str
    body_html: Optional[str] = None
    sent_at: str
    received_at: str
    attachments: list[MessageAttachment] = Field(default_factory=list)
    source: str = "inbox"
    correlation_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedIdentifiers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_ids: list[str] = Field(default_factory=list)
    counterparty_name: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None


class InboxClassification(BaseModel):
    """Typed classifier output. Free-form rationale never mutates records."""

    model_config = ConfigDict(extra="ignore")

    classification: InboxClass
    selected_action: InboxAction
    confidence: float = Field(ge=0, le=1)
    document_ids: list[str] = Field(default_factory=list)
    counterparty_name: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    evidence_refs: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    rationale: str = ""
    dispatch_target: str = ""


class ClarificationRequest(BaseModel):
    thread_id: str
    message_id: str
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class DispatchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: InboxAction
    status: InboxStatus
    dispatch_target: str = ""
    record_ids: list[str] = Field(default_factory=list)
    invoice_id: Optional[str] = None
    canonical_id: Optional[str] = None
    match_status: Optional[MatchStatus] = None
    match_exceptions: list[str] = Field(default_factory=list)
    ready_for_payment: bool = False
    duplicate_of: Optional[str] = None
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    called_workflow: Optional[str] = None
    mutation: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ToolCallTrace(BaseModel):
    agent: str
    tool: str
    input_summary: str = ""
    output_summary: str = ""
    timestamp: str = ""


class InboxAttempt(BaseModel):
    attempt: int
    message_id: str
    classification: Optional[InboxClassification] = None
    dispatch: Optional[DispatchResult] = None
    status: InboxStatus
    reason_codes: list[str] = Field(default_factory=list)
    timestamp: str = ""


class InboxTrace(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trace_id: str
    sender_agent: str = COUNTERPARTY_AGENT
    receiver_agent: str = FINANCE_INBOX_AGENT
    sender_run_id: Optional[str] = None
    receiver_run_id: Optional[str] = None
    message_id: str
    thread_id: str
    attachment_hashes: list[str] = Field(default_factory=list)
    classification: Optional[InboxClassification] = None
    selected_action: Optional[str] = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    duplicate_check: Optional[str] = None
    called_workflow: Optional[str] = None
    record_ids: list[str] = Field(default_factory=list)
    invoice_id: Optional[str] = None
    match_status: Optional[str] = None
    final_status: InboxStatus
    reason_codes: list[str] = Field(default_factory=list)
    decision_summary: str = ""
    attempts: list[InboxAttempt] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    timestamps: dict[str, str] = Field(default_factory=dict)
    trace_path: Optional[str] = None


class CounterpartyAgentOutput(BaseModel):
    agent: str = COUNTERPARTY_AGENT
    run_id: str
    message_id: str
    thread_id: str
    sent: bool
    status: str
    reason_codes: list[str] = Field(default_factory=list)
    attachment_hashes: list[str] = Field(default_factory=list)


class InboxAgentOutput(BaseModel):
    agent: str = FINANCE_INBOX_AGENT
    run_id: str
    message_id: str
    thread_id: str
    classification: InboxClassification
    dispatch: DispatchResult
    clarification: Optional[ClarificationRequest] = None
    replayed: bool = False


class InboxHandoffResult(BaseModel):
    sender: CounterpartyAgentOutput
    receiver: InboxAgentOutput
    trace: InboxTrace
    invoice_id: Optional[str] = None
    final_status: InboxStatus
    replayed: bool = False


class MessageSpec(BaseModel):
    """Fixture used by the Counterparty Message Agent. Not an AP record."""

    model_config = ConfigDict(extra="ignore")

    case_id: str
    message_id: str
    thread_id: str
    in_reply_to: Optional[str] = None
    sender_name: str
    sender_address: str
    recipient_addresses: list[str] = Field(default_factory=lambda: ["ap@hackmit-cfo.example"])
    subject: str
    body_text: str
    body_html: Optional[str] = None
    sent_at: str = "2026-09-18T10:00:00Z"
    received_at: str = "2026-09-18T10:00:02Z"
    attachments: list[MessageAttachment] = Field(default_factory=list)
    source: str = "inbox"
    correlation_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
