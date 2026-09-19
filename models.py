from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    vendor: str
    po_id: Optional[str] = None
    amount: float
    invoice_date: str
    due_date: str
    vendor_invoice_number: str
    description: str = ""


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_id: str
    vendor: str
    authorized_amount: float
    description: str = ""
    status: str
    created_date: str = ""
    currency: str = "USD"
    approval_limit: Optional[float] = None
    approver: str = ""


class GoodsReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    receipt_id: str
    po_id: str
    received: bool
    received_date: Optional[str] = None
    amount_received: float
    quantity_ordered: int
    quantity_received: int


class Precedent(BaseModel):
    id: str
    invoice_id: str
    corrected_decision: Literal["APPROVE", "HOLD", "HUMAN_REVIEW"]
    note: str
    created_at: str
    situation: dict


class APDecision(BaseModel):
    invoice_id: str
    decision: Literal["APPROVE", "HOLD", "HUMAN_REVIEW"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    amount_difference: float | None = Field(
        default=None,
        description="Invoice amount minus PO authorized amount. Null when no PO exists.",
    )
    duplicate_detected: bool
    receipt_status: str = Field(
        description="full, partial, not_received, missing, or not_applicable"
    )
    evidence_used: list[str] = Field(
        description="Record IDs actually inspected, such as INV-001, PO-101, GR-101."
    )
