"""Registry-based action dispatcher. Unknown actions fail closed."""

from __future__ import annotations

from collections.abc import Callable

from inbox.classify import lookup_default_action
from inbox.handlers import (
    handle_create_ap_invoice,
    handle_ignore,
    handle_needs_information,
    handle_parse_failure,
    handle_record_notice,
    handle_reject,
    handle_unsupported,
    extract_primary_candidate,
)
from inbox.models import (
    ClarificationRequest,
    DispatchResult,
    InboxAction,
    InboxClassification,
    MessageEnvelope,
)
from inbox.security import has_unsafe_mutation_request

Handler = Callable[..., DispatchResult | tuple[DispatchResult, ClarificationRequest]]


def _route_goods(message, classification):
    return handle_record_notice("RECORD_GOODS_RECEIPT", "goods_receipt", message, classification)


def _route_payment(message, classification):
    return handle_record_notice("RECORD_PAYMENT_NOTICE", "payment_notice", message, classification)


def _route_remittance(message, classification):
    return handle_record_notice("RECORD_CUSTOMER_REMITTANCE", "remittance", message, classification)


def _route_po(message, classification):
    return handle_record_notice(
        "ROUTE_TO_EXISTING_WORKFLOW",
        "purchase_order",
        message,
        classification,
        extra_reasons=["PURCHASE_ORDER_NOT_INVOICE"],
    )


def _route_internal(message, classification):
    return handle_record_notice(
        "ROUTE_TO_EXISTING_WORKFLOW",
        "internal_request",
        message,
        classification,
        extra_reasons=["INTERNAL_REQUEST"],
    )


def _route_credit(message, classification):
    return handle_unsupported(message, classification)


HANDLERS: dict[InboxAction, Handler] = {
    "CREATE_AP_INVOICE": handle_create_ap_invoice,
    "UPDATE_EXISTING_AP_INVOICE": handle_create_ap_invoice,
    "ATTACH_SUPPORTING_EVIDENCE": handle_create_ap_invoice,
    "RECORD_GOODS_RECEIPT": _route_goods,
    "RECORD_PAYMENT_NOTICE": _route_payment,
    "RECORD_CUSTOMER_REMITTANCE": _route_remittance,
    "ROUTE_TO_EXISTING_WORKFLOW": handle_unsupported,
    "REQUEST_MISSING_INFORMATION": handle_needs_information,
    "IGNORE": handle_ignore,
    "REJECT_UNSAFE_REQUEST": handle_reject,
}

CLASS_HANDLERS: dict[str, InboxAction] = {
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


def lookup_handler(action: str) -> Handler | None:
    if action not in HANDLERS:
        return None
    return HANDLERS[action]  # type: ignore[index]


def dispatch(
    message: MessageEnvelope,
    classification: InboxClassification,
) -> tuple[DispatchResult, ClarificationRequest | None]:
    action = classification.selected_action
    if action not in HANDLERS:
        result = DispatchResult(
            action="REJECT_UNSAFE_REQUEST",
            status="REJECTED",
            reason_codes=["UNKNOWN_ACTION", f"unknown_action:{action}"],
            mutation=False,
        )
        return result, None

    if "PROMPT_INJECTION" in classification.reason_codes:
        return handle_reject(message, classification), None

    if action == "CREATE_AP_INVOICE":
        candidate, errors = extract_primary_candidate(message)
        if errors and candidate is None:
            return handle_parse_failure(message, classification, errors), None
        if candidate is None:
            return handle_needs_information(message, classification)
        result = handle_create_ap_invoice(message, classification, candidate)
        if result.status == "NEEDS_INFORMATION":
            clarification, = (handle_needs_information(message, classification)[1],)
            return result, clarification
        return result, None

    if action == "REQUEST_MISSING_INFORMATION":
        if "PARSE_FAILURE" in classification.reason_codes or "UNSUPPORTED_ATTACHMENT" in classification.reason_codes:
            return handle_parse_failure(message, classification, classification.reason_codes), None
        return handle_needs_information(message, classification)

    if action == "ROUTE_TO_EXISTING_WORKFLOW":
        if classification.classification == "PURCHASE_ORDER":
            return _route_po(message, classification), None
        if classification.classification == "INTERNAL_REQUEST":
            return _route_internal(message, classification), None
        if classification.classification == "CREDIT_MEMO":
            return _route_credit(message, classification), None
        return handle_unsupported(message, classification), None

    if action == "RECORD_GOODS_RECEIPT":
        return _route_goods(message, classification), None
    if action == "RECORD_PAYMENT_NOTICE":
        return _route_payment(message, classification), None
    if action == "RECORD_CUSTOMER_REMITTANCE":
        return _route_remittance(message, classification), None
    if action == "IGNORE":
        return handle_ignore(message, classification), None
    if action == "REJECT_UNSAFE_REQUEST":
        if has_unsafe_mutation_request(message):
            return handle_reject(message, classification), None
        return handle_reject(message, classification), None

    if action in {"UPDATE_EXISTING_AP_INVOICE", "ATTACH_SUPPORTING_EVIDENCE"}:
        candidate, errors = extract_primary_candidate(message)
        if candidate is None:
            return handle_parse_failure(message, classification, errors or ["MISSING_CANDIDATE"]), None
        return handle_create_ap_invoice(message, classification, candidate), None

    result = DispatchResult(
        action="REJECT_UNSAFE_REQUEST",
        status="REJECTED",
        reason_codes=["UNKNOWN_ACTION"],
        mutation=False,
    )
    return result, None


def action_for_classification(classification: str) -> InboxAction | None:
    mapped = CLASS_HANDLERS.get(classification)
    if mapped is None:
        return lookup_default_action(classification)
    return mapped
