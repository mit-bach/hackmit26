from __future__ import annotations

from models import Invoice
from invoice_ingestion.models import CanonicalInvoice
from invoice_ingestion.registry import reset_registry
from tools import clear_runtime_invoices, register_runtime_invoice


def to_ap_invoice(canonical: CanonicalInvoice, **provenance) -> Invoice:
    due = canonical.due_date or canonical.invoice_date
    hashes = list(provenance.get("source_attachment_hashes") or [])
    if not hashes and canonical.document_hash:
        hashes = [canonical.document_hash]
    return Invoice(
        invoice_id=canonical.canonical_id,
        vendor=canonical.vendor,
        po_id=canonical.po_id,
        amount=canonical.amount,
        invoice_date=canonical.invoice_date,
        due_date=due,
        vendor_invoice_number=canonical.vendor_invoice_number,
        description=canonical.description,
        source_message_id=provenance.get("source_message_id"),
        source_thread_id=provenance.get("source_thread_id"),
        source_trace_id=provenance.get("source_trace_id"),
        source_attachment_hashes=hashes,
    )


def register_canonical(canonical: CanonicalInvoice, **provenance) -> Invoice:
    email_source = next((ref for ref in canonical.sources if getattr(ref, "source_type", None) == "email"), None)
    if email_source is not None and not provenance.get("source_message_id"):
        provenance["source_message_id"] = email_source.source_id
    existing = None
    from tools import load_invoice

    existing = load_invoice(canonical.canonical_id)
    if existing is not None:
        provenance.setdefault("source_message_id", existing.source_message_id)
        provenance.setdefault("source_thread_id", existing.source_thread_id)
        provenance.setdefault("source_trace_id", existing.source_trace_id)
        if not provenance.get("source_attachment_hashes") and existing.source_attachment_hashes:
            provenance["source_attachment_hashes"] = list(existing.source_attachment_hashes)
    invoice = to_ap_invoice(canonical, **provenance)
    register_runtime_invoice(invoice)
    return invoice


def reset_ingested_invoices() -> None:
    clear_runtime_invoices()
    reset_registry()
