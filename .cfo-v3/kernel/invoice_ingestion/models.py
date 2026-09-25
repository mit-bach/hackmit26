from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_SOURCES = (
    "email",
    "erp",
    "procurement",
    "vendor_portal",
    "employee_submission",
    "document",
    "edi",
    "bank_card",
)

# Structured records are mapped in Python. Messy documents may use an agent.
STRUCTURED_SOURCES = ("erp", "procurement", "edi")
UNSTRUCTURED_SOURCES = (
    "email",
    "vendor_portal",
    "employee_submission",
    "document",
    "bank_card",
)

SOURCE_AGENTS = {
    "email": "Email Invoice Agent",
    "erp": "ERP Invoice Agent",
    "procurement": "Procurement Invoice Agent",
    "vendor_portal": "Vendor Portal Agent",
    "employee_submission": "Employee Submission Agent",
    "document": "Physical Mail / Document Agent",
    "edi": "EDI / Electronic Invoicing Agent",
    "bank_card": "Bank/Card Discovery Agent",
}

Classification = Literal[
    "invoice",
    "receipt",
    "statement",
    "quote",
    "purchase_order",
    "marketing",
    "payment_confirmation",
    "reimbursement",
    "not_invoice",
    "unreadable",
    "invoice_missing",
    "needs_follow_up",
]

ValidationStatus = Literal["valid", "rejected", "ambiguous"]
DiscoveryStatus = Literal["invoice_found", "invoice_missing", "needs_follow_up"]


class InvoiceEvidence(BaseModel):
    field: str
    source: str
    text: Optional[str] = None
    value: str | float | None = None


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str = ""
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class InvoiceCandidate(BaseModel):
    """Normalized extraction from one source record. Not an approval."""

    model_config = ConfigDict(extra="ignore")

    source_type: str
    source_id: str
    source_uri: Optional[str] = None

    vendor: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    amount: Optional[float] = None
    po_id: Optional[str] = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    document_path: Optional[str] = None
    document_hash: Optional[str] = None
    page_refs: list[str] = Field(default_factory=list)
    extraction_confidence: Optional[float] = None
    evidence: list[InvoiceEvidence] = Field(default_factory=list)
    source_context: dict[str, Any] = Field(default_factory=dict)
    classification: str = "invoice"
    classification_reason: str = ""


class SourceRef(BaseModel):
    source_type: str
    source_id: str
    source_uri: Optional[str] = None
    agent: str
    document_hash: Optional[str] = None


class ValidationResult(BaseModel):
    source_type: str
    source_id: str
    status: ValidationStatus
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CanonicalInvoice(BaseModel):
    canonical_id: str
    vendor: str
    vendor_id: Optional[str] = None
    vendor_invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    currency: str = "USD"
    amount: float
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    po_id: Optional[str] = None
    description: str = ""
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    document_hash: Optional[str] = None
    evidence: list[InvoiceEvidence] = Field(default_factory=list)
    validation_status: ValidationStatus = "valid"
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    already_in_ap_inbox: bool = False
    existing_ap_invoice_id: Optional[str] = None
    forwarded_to_ap: bool = False
    ap_invoice_id: Optional[str] = None
    ap_result: Optional[str] = None
    canonical_key: Optional[str] = None
    ingestion_status: str = "new_invoice"
    provenance_added: bool = False
    new_this_run: bool = True


class RecordTrace(BaseModel):
    source_type: str
    source_id: str
    agent: str
    classification: Optional[str] = None
    reason: Optional[str] = None
    candidate_produced: bool = False
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    evidence: list[InvoiceEvidence] = Field(default_factory=list)
    validation_status: Optional[str] = None
    validation_errors: list[str] = Field(default_factory=list)
    duplicate_of: Optional[str] = None
    canonical_id: Optional[str] = None
    forwarded_to_ap: bool = False
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    source_ref: Optional[str] = None
    canonical_key: Optional[str] = None
    status: Optional[str] = None
    provenance_added: bool = False
    ap_handoff: bool = False
    extraction_method: Optional[str] = None


class SourceRunResult(BaseModel):
    source_type: str
    agent: str
    records_checked: int = 0
    invoices_found: int = 0
    non_invoices: int = 0
    missing_documentation: int = 0
    candidates: list[InvoiceCandidate] = Field(default_factory=list)
    discovery: list["BankDiscoveryResult"] = Field(default_factory=list)
    traces: list[RecordTrace] = Field(default_factory=list)
    extraction_method: str = "deterministic"
    error: Optional[str] = None


class BankDiscoveryResult(BaseModel):
    transaction_id: str
    status: DiscoveryStatus
    reason: str
    vendor_descriptor: str = ""
    amount: Optional[float] = None
    candidate: Optional[InvoiceCandidate] = None
    matched_source_ids: list[str] = Field(default_factory=list)


class SourceAgentOutput(BaseModel):
    source_id: str
    classification: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    candidate: Optional[InvoiceCandidate] = None
    warnings: list[str] = Field(default_factory=list)


class BankAgentOutput(BaseModel):
    transaction_id: str
    status: DiscoveryStatus
    reason: str
    candidate: Optional[InvoiceCandidate] = None
    matched_source_ids: list[str] = Field(default_factory=list)


class IngestionReport(BaseModel):
    period: str
    started_at: str
    source_runs: list[SourceRunResult] = Field(default_factory=list)
    candidates: list[InvoiceCandidate] = Field(default_factory=list)
    rejected: list[InvoiceCandidate] = Field(default_factory=list)
    canonical_invoices: list[CanonicalInvoice] = Field(default_factory=list)
    discovery: list[BankDiscoveryResult] = Field(default_factory=list)
    traces: list[RecordTrace] = Field(default_factory=list)
    duplicates_removed: int = 0
    forwarded_invoice_ids: list[str] = Field(default_factory=list)
    new_canonical_count: int = 0
    replayed_canonical_count: int = 0
    provenance_updates: int = 0
    new_ap_handoffs: int = 0
    errors: list[str] = Field(default_factory=list)
    trace_path: Optional[str] = None
