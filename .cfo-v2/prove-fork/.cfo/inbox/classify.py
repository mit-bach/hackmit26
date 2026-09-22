"""Deterministic inbox classifier. Structured output only."""

from __future__ import annotations

from invoice_ingestion.interpret import classify_text, looks_like_invoice_text, parse_invoice_text_clean
from inbox.models import InboxAction, InboxClassification, InboxClass, MessageEnvelope
from inbox.normalize import (
    dollars_to_cents,
    normalize_currency,
    normalize_invoice_number,
    normalize_iso_date,
    normalize_po,
    resolve_vendor,
)
from inbox.security import (
    attachment_is_unsupported,
    has_prompt_injection,
    has_unsafe_mutation_request,
    message_blob,
    security_reason_codes,
)

SOURCE_CLASS_MAP = {
    "invoice": "VENDOR_INVOICE",
    "quote": "CONTRACT_OR_QUOTE",
    "statement": "VENDOR_STATEMENT",
    "purchase_order": "PURCHASE_ORDER",
    "payment_confirmation": "PAYMENT_CONFIRMATION",
    "marketing": "NON_FINANCE",
    "receipt": "NON_FINANCE",
    "reimbursement": "INTERNAL_REQUEST",
    "not_invoice": "UNSUPPORTED_OR_UNRESOLVED",
    "unreadable": "UNSUPPORTED_OR_UNRESOLVED",
    "invoice_missing": "UNSUPPORTED_OR_UNRESOLVED",
    "needs_follow_up": "UNSUPPORTED_OR_UNRESOLVED",
}

DEFAULT_ACTIONS: dict[str, InboxAction] = {
    "VENDOR_INVOICE": "CREATE_AP_INVOICE",
    "PURCHASE_ORDER": "ROUTE_TO_EXISTING_WORKFLOW",
    "GOODS_RECEIPT": "RECORD_GOODS_RECEIPT",
    "VENDOR_STATEMENT": "IGNORE",
    "PAYMENT_CONFIRMATION": "RECORD_PAYMENT_NOTICE",
    "CREDIT_MEMO": "ROUTE_TO_EXISTING_WORKFLOW",
    "CUSTOMER_REMITTANCE": "RECORD_CUSTOMER_REMITTANCE",
    "BANK_NOTICE": "RECORD_PAYMENT_NOTICE",
    "CONTRACT_OR_QUOTE": "IGNORE",
    "INTERNAL_REQUEST": "ROUTE_TO_EXISTING_WORKFLOW",
    "NON_FINANCE": "IGNORE",
    "UNSUPPORTED_OR_UNRESOLVED": "REQUEST_MISSING_INFORMATION",
}

DISPATCH_TARGETS: dict[str, str] = {
    "CREATE_AP_INVOICE": "invoice_ingestion.workflow.ingest_candidates",
    "UPDATE_EXISTING_AP_INVOICE": "invoice_ingestion.workflow.ingest_candidates",
    "ATTACH_SUPPORTING_EVIDENCE": "invoice_ingestion.registry.merge_provenance",
    "RECORD_GOODS_RECEIPT": "inbox.notices.goods_receipt",
    "RECORD_PAYMENT_NOTICE": "inbox.notices.payment",
    "RECORD_CUSTOMER_REMITTANCE": "inbox.notices.remittance",
    "ROUTE_TO_EXISTING_WORKFLOW": "inbox.notices.route",
    "REQUEST_MISSING_INFORMATION": "inbox.clarification",
    "IGNORE": "none",
    "REJECT_UNSAFE_REQUEST": "none",
}

CREDIT_MARKERS = ("credit memo", "credit note", "credit memorandum")
REMIT_MARKERS = ("remittance advice", "please apply this payment", "lockbox remittance")
BANK_MARKERS = ("bank notice", "ach return", "wire notice", "returned ach")
GR_MARKERS = ("goods received", "goods receipt", "packing list", "receiving report", "received in full")
PO_MARKERS = ("purchase order", "po number")
INTERNAL_MARKERS = ("please accrue", "expense report", "internal request")
CONTRACT_MARKERS = ("quotation", "quote number", "quoted amount", "estimate valid", "this is a quote")


def _blob(message: MessageEnvelope) -> str:
    return message_blob(message)


def _specific_class(blob: str, source_class: str) -> InboxClass:
    lower = blob.lower()
    if any(token in lower for token in CREDIT_MARKERS):
        return "CREDIT_MEMO"
    if any(token in lower for token in REMIT_MARKERS):
        return "CUSTOMER_REMITTANCE"
    if any(token in lower for token in BANK_MARKERS):
        return "BANK_NOTICE"
    if any(token in lower for token in CONTRACT_MARKERS) and not looks_like_invoice_text(blob):
        return "CONTRACT_OR_QUOTE"
    if any(token in lower for token in GR_MARKERS) and not looks_like_invoice_text(blob):
        return "GOODS_RECEIPT"
    if source_class == "purchase_order" or (
        any(token in lower for token in PO_MARKERS)
        and "invoice number" not in lower
        and "amount due" not in lower
        and not looks_like_invoice_text(blob)
    ):
        return "PURCHASE_ORDER"
    if any(token in lower for token in INTERNAL_MARKERS) and not looks_like_invoice_text(blob):
        return "INTERNAL_REQUEST"
    mapped = SOURCE_CLASS_MAP.get(source_class)
    if mapped in {
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
    }:
        return mapped  # type: ignore[return-value]
    return "UNSUPPORTED_OR_UNRESOLVED"


def _required_invoice_fields(invoice_number: str | None, amount_cents: int | None, vendor: str | None, invoice_date: str | None, currency: str | None) -> list[str]:
    missing: list[str] = []
    if not vendor:
        missing.append("vendor")
    if not invoice_number:
        missing.append("invoice_number")
    if amount_cents is None:
        missing.append("amount")
    if not invoice_date:
        missing.append("invoice_date")
    if not currency:
        missing.append("currency")
    return missing


def classify_message(message: MessageEnvelope) -> InboxClassification:
    blob = _blob(message)
    filenames = " ".join(item.filename for item in message.attachments)
    source_class, source_reason = classify_text(blob, subject=message.subject, filename=filenames)
    classification = _specific_class(blob, source_class)
    parsed = parse_invoice_text_clean(
        text=blob,
        source_type="email",
        source_id=message.message_id,
        vendor_hint=message.sender_name,
    )
    vendor, known = resolve_vendor(parsed.vendor or message.sender_name)
    invoice_number = normalize_invoice_number(parsed.vendor_invoice_number)
    po_number = normalize_po(parsed.po_id)
    currency = normalize_currency(parsed.currency, text=blob)
    invoice_date = normalize_iso_date(parsed.invoice_date)
    due_date = normalize_iso_date(parsed.due_date)
    amount_cents = dollars_to_cents(parsed.amount)
    if classification == "VENDOR_INVOICE" and not looks_like_invoice_text(blob) and source_class != "invoice":
        classification = "UNSUPPORTED_OR_UNRESOLVED"

    missing = []
    if classification == "VENDOR_INVOICE" or (
        "invoice" in blob.lower()
        and classification == "UNSUPPORTED_OR_UNRESOLVED"
        and source_class in {"invoice", "not_invoice", "needs_follow_up"}
    ):
        missing = _required_invoice_fields(invoice_number, amount_cents, vendor, invoice_date, currency)

    reason_codes = security_reason_codes(message)
    if not known and vendor and classification == "VENDOR_INVOICE":
        reason_codes.append("UNKNOWN_VENDOR")
    if missing:
        reason_codes.append("MISSING_FIELDS")
    if any(attachment_is_unsupported(item.filename, item.mime_type) for item in message.attachments):
        if not looks_like_invoice_text(message.body_text):
            classification = "UNSUPPORTED_OR_UNRESOLVED"
            reason_codes.append("PARSE_FAILURE")

    action: InboxAction = DEFAULT_ACTIONS[classification]
    if classification == "VENDOR_INVOICE" and missing:
        action = "REQUEST_MISSING_INFORMATION"
        classification = "UNSUPPORTED_OR_UNRESOLVED"
        reason_codes.append("NEEDS_INFORMATION")
    if classification == "CREDIT_MEMO":
        reason_codes.append("CREDIT_MEMO_PATH_UNAVAILABLE")
    if has_unsafe_mutation_request(message) and classification != "VENDOR_INVOICE":
        action = "REJECT_UNSAFE_REQUEST"
        if classification not in {"VENDOR_INVOICE"}:
            classification = "UNSUPPORTED_OR_UNRESOLVED" if classification == "UNSUPPORTED_OR_UNRESOLVED" else classification
    if has_prompt_injection(message):
        # Injection that looks like a bill must not mint AP. Flags are not enough.
        action = "REJECT_UNSAFE_REQUEST"
        if classification == "VENDOR_INVOICE":
            classification = "UNSUPPORTED_OR_UNRESOLVED"

    confidence = 0.9
    if classification == "UNSUPPORTED_OR_UNRESOLVED":
        confidence = 0.35
    if missing:
        confidence = 0.3
    if "PROMPT_INJECTION" in reason_codes:
        confidence = min(confidence, 0.7)
    if not known and classification == "VENDOR_INVOICE":
        confidence = min(confidence, 0.75)

    document_ids = [item for item in (invoice_number, po_number) if item]
    evidence = [f"message:{message.message_id}"]
    evidence.extend(f"attachment:{item.filename}" for item in message.attachments)

    rationale = source_reason
    if classification == "CREDIT_MEMO":
        rationale = "Document is a credit memo, not a vendor invoice"
    elif classification == "CUSTOMER_REMITTANCE":
        rationale = "Remittance advice rather than a vendor invoice"
    elif classification == "BANK_NOTICE":
        rationale = "Bank notice rather than a vendor invoice"
    elif classification == "GOODS_RECEIPT":
        rationale = "Goods receipt / packing list, not a request for payment"
    elif missing:
        rationale = "Invoice language is present but required fields are missing"

    return InboxClassification(
        classification=classification,
        selected_action=action,
        confidence=confidence,
        document_ids=document_ids,
        counterparty_name=vendor,
        vendor_id=vendor if known else None,
        invoice_number=invoice_number,
        po_number=po_number,
        amount_cents=amount_cents,
        currency=currency,
        invoice_date=invoice_date,
        due_date=due_date,
        evidence_refs=evidence,
        missing_fields=missing,
        reason_codes=list(dict.fromkeys(reason_codes)),
        rationale=rationale,
        dispatch_target=DISPATCH_TARGETS[action],
    )


def lookup_default_action(classification: str) -> InboxAction | None:
    return DEFAULT_ACTIONS.get(classification)


def lookup_dispatch_target(action: str) -> str | None:
    return DISPATCH_TARGETS.get(action)
