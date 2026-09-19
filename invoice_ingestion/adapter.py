from __future__ import annotations

from models import Invoice
from invoice_ingestion.models import CanonicalInvoice
from invoice_ingestion.registry import reset_registry
from tools import clear_runtime_invoices, register_runtime_invoice


def to_ap_invoice(canonical: CanonicalInvoice) -> Invoice:
    due = canonical.due_date or canonical.invoice_date
    return Invoice(
        invoice_id=canonical.canonical_id,
        vendor=canonical.vendor,
        po_id=canonical.po_id,
        amount=canonical.amount,
        invoice_date=canonical.invoice_date,
        due_date=due,
        vendor_invoice_number=canonical.vendor_invoice_number,
        description=canonical.description,
    )


def register_canonical(canonical: CanonicalInvoice) -> Invoice:
    invoice = to_ap_invoice(canonical)
    register_runtime_invoice(invoice)
    return invoice


def reset_ingested_invoices() -> None:
    clear_runtime_invoices()
    reset_registry()
