"""Action handlers. Mutations go through existing domain services only."""

from __future__ import annotations

from invoice_ingestion.identity import canonical_invoice_key
from invoice_ingestion.models import InvoiceCandidate
from invoice_ingestion.validate import existing_ap_match, validate_candidate
from invoice_ingestion.workflow import ingest_candidates
from tools import collect_case_evidence, load_invoice

from inbox.classify import DISPATCH_TARGETS
from inbox.extract import extract_invoice_candidates
from inbox.models import (
    ClarificationRequest,
    DispatchResult,
    InboxAction,
    InboxClassification,
    MatchStatus,
    MessageEnvelope,
)
from inbox.normalize import cents_to_dollars
from inbox.store import apply_inbox_provenance, record_notice, remember_invoice
from inbox.transport import invoice_lock


def match_status_for(invoice_id: str | None) -> tuple[MatchStatus, list[str], bool]:
    if not invoice_id or load_invoice(invoice_id) is None:
        return "NOT_APPLICABLE", [], False
    evidence = collect_case_evidence(invoice_id)
    exceptions = list(evidence.exception_types)
    if evidence.duplicate_detected:
        return "DUPLICATE", exceptions, False
    if "material_amount_mismatch" in exceptions:
        return "BLOCKED", exceptions, False
    if "missing_po" in exceptions and len(exceptions) == 1:
        return "NON_PO", exceptions, False
    if exceptions:
        return "EXCEPTION", exceptions, False
    if evidence.po_exists and evidence.amount_matches and evidence.receipt_status == "full":
        return "MATCHED", exceptions, False
    if not evidence.po_exists:
        return "NON_PO", exceptions, False
    return "UNMATCHED", exceptions, False


def _clarification(message: MessageEnvelope, classification: InboxClassification) -> ClarificationRequest:
    questions = []
    labels = {
        "vendor": "What is the vendor legal name?",
        "invoice_number": "What is the vendor invoice number?",
        "amount": "What is the amount due, including currency?",
        "invoice_date": "What is the invoice date (YYYY-MM-DD)?",
        "currency": "What is the currency code?",
    }
    for field in classification.missing_fields:
        questions.append(labels.get(field, f"Please provide {field}."))
    return ClarificationRequest(
        thread_id=message.thread_id,
        message_id=message.message_id,
        missing_fields=list(classification.missing_fields),
        questions=questions,
        reason_codes=["NEEDS_INFORMATION", *classification.reason_codes],
    )


def handle_create_ap_invoice(
    message: MessageEnvelope,
    classification: InboxClassification,
    candidate: InvoiceCandidate | None,
) -> DispatchResult:
    if candidate is None:
        return DispatchResult(
            action="CREATE_AP_INVOICE",
            status="UNRESOLVED",
            reason_codes=["MISSING_CANDIDATE"],
            dispatch_target=DISPATCH_TARGETS["CREATE_AP_INVOICE"],
        )
    validation = validate_candidate(candidate)
    if validation.status == "rejected":
        return DispatchResult(
            action="REQUEST_MISSING_INFORMATION",
            status="NEEDS_INFORMATION",
            validation_errors=validation.errors,
            validation_warnings=validation.warnings,
            reason_codes=["VALIDATION_REJECTED", *validation.errors],
            dispatch_target=DISPATCH_TARGETS["REQUEST_MISSING_INFORMATION"],
            called_workflow="invoice_ingestion.validate.validate_candidate",
        )

    key = canonical_invoice_key(candidate) or f"source:{message.message_id}"
    with invoice_lock(key):
        existing_id = None
        if candidate.vendor and candidate.vendor_invoice_number:
            existing_id = existing_ap_match(candidate.vendor, candidate.vendor_invoice_number)
        report = ingest_candidates(
            [candidate],
            period="2026-09",
            forward_to_ap=True,
            run_ap=False,
            reset_overlay=False,
            save_trace=False,
        )
        if not report.canonical_invoices:
            return DispatchResult(
                action="CREATE_AP_INVOICE",
                status="UNRESOLVED",
                validation_errors=validation.errors,
                reason_codes=["INGEST_PRODUCED_NO_CANONICAL"],
                called_workflow="invoice_ingestion.workflow.ingest_candidates",
            )
        item = report.canonical_invoices[0]
        invoice_id = item.ap_invoice_id or item.canonical_id
        invoice = load_invoice(invoice_id) if invoice_id else None
        if invoice is not None:
            hashes = [attachment.sha256 for attachment in message.attachments if attachment.sha256]
            if not hashes and item.document_hash:
                hashes = [item.document_hash]
            invoice = apply_inbox_provenance(
                invoice,
                message_id=message.message_id,
                thread_id=message.thread_id,
                trace_id=f"INBOX-{message.message_id}",
                attachment_hashes=hashes,
            )
            remember_invoice(invoice, item)
        match, exceptions, ready = match_status_for(invoice_id)
        duplicate = bool(item.already_in_ap_inbox or existing_id or not item.new_this_run)
        status = "CREATED"
        reason = ["AP_INVOICE_CREATED"]
        action: InboxAction = "CREATE_AP_INVOICE"
        if duplicate:
            status = "BUSINESS_DUPLICATE"
            action = "ATTACH_SUPPORTING_EVIDENCE"
            reason = ["BUSINESS_DUPLICATE", "EVIDENCE_LINKED"]
            if existing_id:
                invoice_id = existing_id
                match, exceptions, ready = match_status_for(invoice_id)
        if "unknown_vendor" in (item.warnings or []) or "UNKNOWN_VENDOR" in classification.reason_codes:
            reason.append("UNKNOWN_VENDOR")
        return DispatchResult(
            action=action,
            status=status,
            dispatch_target=DISPATCH_TARGETS[action],
            record_ids=[invoice_id] if invoice_id else [],
            invoice_id=invoice_id,
            canonical_id=item.canonical_id,
            match_status=match,
            match_exceptions=exceptions,
            ready_for_payment=ready,
            duplicate_of=existing_id or (item.existing_ap_invoice_id if duplicate else None),
            validation_errors=item.validation_errors,
            validation_warnings=item.warnings,
            reason_codes=list(dict.fromkeys(reason + classification.reason_codes)),
            called_workflow="invoice_ingestion.workflow.ingest_candidates+tools.collect_case_evidence",
            mutation=status == "CREATED",
            details={
                "ingestion_status": item.ingestion_status,
                "forwarded_to_ap": item.forwarded_to_ap,
                "amount": item.amount,
            },
        )


def handle_record_notice(
    action: InboxAction,
    kind: str,
    message: MessageEnvelope,
    classification: InboxClassification,
    *,
    status: str = "ROUTED",
    extra_reasons: list[str] | None = None,
) -> DispatchResult:
    notice = record_notice(
        kind,
        {
            "message_id": message.message_id,
            "thread_id": message.thread_id,
            "classification": classification.classification,
            "counterparty": classification.counterparty_name,
            "invoice_number": classification.invoice_number,
            "po_number": classification.po_number,
            "amount_cents": classification.amount_cents,
            "amount": cents_to_dollars(classification.amount_cents),
        },
    )
    reasons = [f"ROUTED_{kind.upper()}", *(extra_reasons or []), *classification.reason_codes]
    return DispatchResult(
        action=action,
        status=status,  # type: ignore[arg-type]
        dispatch_target=DISPATCH_TARGETS[action],
        record_ids=[],
        reason_codes=list(dict.fromkeys(reasons)),
        called_workflow=DISPATCH_TARGETS[action],
        mutation=False,
        details={"notice": notice},
    )


def handle_ignore(message: MessageEnvelope, classification: InboxClassification) -> DispatchResult:
    record_notice(
        "ignored",
        {
            "message_id": message.message_id,
            "classification": classification.classification,
        },
    )
    return DispatchResult(
        action="IGNORE",
        status="IGNORED",
        dispatch_target="none",
        reason_codes=["IGNORED", *classification.reason_codes],
        called_workflow=None,
        mutation=False,
    )


def handle_reject(message: MessageEnvelope, classification: InboxClassification) -> DispatchResult:
    record_notice(
        "rejected",
        {"message_id": message.message_id, "classification": classification.classification},
    )
    return DispatchResult(
        action="REJECT_UNSAFE_REQUEST",
        status="REJECTED",
        dispatch_target="none",
        reason_codes=["REJECTED_UNSAFE", *classification.reason_codes],
        mutation=False,
    )


def handle_needs_information(
    message: MessageEnvelope,
    classification: InboxClassification,
) -> tuple[DispatchResult, ClarificationRequest]:
    request = _clarification(message, classification)
    record_notice(
        "clarification",
        {
            "message_id": message.message_id,
            "thread_id": message.thread_id,
            "missing_fields": request.missing_fields,
            "questions": request.questions,
        },
    )
    result = DispatchResult(
        action="REQUEST_MISSING_INFORMATION",
        status="NEEDS_INFORMATION",
        dispatch_target=DISPATCH_TARGETS["REQUEST_MISSING_INFORMATION"],
        reason_codes=["NEEDS_INFORMATION", *classification.missing_fields, *classification.reason_codes],
        mutation=False,
        details={"missing_fields": request.missing_fields, "questions": request.questions},
    )
    return result, request


def handle_unsupported(message: MessageEnvelope, classification: InboxClassification) -> DispatchResult:
    extra = []
    if classification.classification == "CREDIT_MEMO":
        extra.append("CREDIT_MEMO_PATH_UNAVAILABLE")
    record_notice(
        "unsupported",
        {
            "message_id": message.message_id,
            "classification": classification.classification,
        },
    )
    return DispatchResult(
        action="ROUTE_TO_EXISTING_WORKFLOW",
        status="UNSUPPORTED",
        dispatch_target="inbox.notices.unsupported",
        reason_codes=["UNSUPPORTED_ACTION", *extra, *classification.reason_codes],
        mutation=False,
    )


def handle_parse_failure(message: MessageEnvelope, classification: InboxClassification, codes: list[str]) -> DispatchResult:
    return DispatchResult(
        action="REQUEST_MISSING_INFORMATION",
        status="PARSE_FAILURE",
        dispatch_target="none",
        reason_codes=list(dict.fromkeys(["PARSE_FAILURE", *codes, *classification.reason_codes])),
        mutation=False,
    )


def extract_primary_candidate(message: MessageEnvelope) -> tuple[InvoiceCandidate | None, list[str]]:
    candidates, errors = extract_invoice_candidates(message)
    if not candidates:
        return None, errors
    return candidates[0], errors
