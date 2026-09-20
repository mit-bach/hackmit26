"""Agent tools. Counterparty tools cannot write AP. Inbox tools dispatch only."""

from __future__ import annotations

from agents import function_tool

from inbox.classify import classify_message as classify_message_impl
from inbox.dispatch import dispatch as dispatch_impl
from inbox.extract import attachment_text, extract_invoice_candidates, hash_attachment
from inbox.models import MessageEnvelope, MessageSpec
from inbox.transport import deliver, get_message, list_thread


def compose_counterparty_message(
    case_id: str,
    message_id: str,
    thread_id: str,
    sender_name: str,
    sender_address: str,
    subject: str,
    body_text: str,
    sent_at: str = "2026-09-18T10:00:00Z",
    received_at: str = "2026-09-18T10:00:02Z",
    in_reply_to: str = "",
    correlation_id: str = "",
    recipient: str = "ap@hackmit-cfo.example",
) -> dict:
    """Build a typed message envelope. Does not write financial records."""
    spec = MessageSpec(
        case_id=case_id,
        message_id=message_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to or None,
        sender_name=sender_name,
        sender_address=sender_address,
        recipient_addresses=[recipient],
        subject=subject,
        body_text=body_text,
        sent_at=sent_at,
        received_at=received_at,
        correlation_id=correlation_id or message_id,
    )
    return {"found": True, "envelope": spec.model_dump(), "wrote_ap": False}


def send_inbox_message(envelope_json: str) -> dict:
    """Deliver a JSON message envelope to the finance inbox. Not an AP write."""
    message = MessageEnvelope.model_validate_json(envelope_json)
    stored = deliver(message)
    return {
        "found": True,
        "message_id": stored.message_id,
        "thread_id": stored.thread_id,
        "delivered": True,
        "attachment_hashes": [item.sha256 for item in stored.attachments if item.sha256],
        "wrote_ap": False,
    }


def reply_in_thread(thread_id: str, in_reply_to: str, message_id: str, body_text: str, subject: str = "") -> dict:
    """Send a clarification reply in the same thread. Cannot write AP records."""
    original = get_message(in_reply_to)
    if original is None:
        thread = list_thread(thread_id)
        original = thread[0] if thread else None
    if original is None:
        return {"found": False, "error": "Original thread message was not found. Do not invent it."}
    reply = original.model_copy(
        update={
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "thread_id": thread_id,
            "subject": subject or f"Re: {original.subject}",
            "body_text": body_text,
            "attachments": [],
            "correlation_id": original.correlation_id,
            "metadata": {"reply": True},
        }
    )
    stored = deliver(reply)
    return {"found": True, "message_id": stored.message_id, "thread_id": stored.thread_id, "wrote_ap": False}


def get_inbox_message(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found. Do not invent it."}
    return {"found": True, "message": row.model_dump()}


def get_inbox_attachment(message_id: str, filename: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    for attachment in row.attachments:
        if attachment.filename == filename:
            try:
                text = attachment_text(attachment)
            except Exception as exc:
                return {"found": False, "error": str(exc), "reason_code": getattr(exc, "reason_code", "PARSE_FAILURE")}
            return {
                "found": True,
                "filename": filename,
                "mime_type": attachment.mime_type,
                "text": text,
                "sha256": hash_attachment(attachment),
            }
    return {"found": False, "error": f"Attachment {filename} was not found."}


def classify_inbox_message(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    return {"found": True, "classification": classify_message_impl(row).model_dump()}


def extract_inbox_invoice(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    candidates, errors = extract_invoice_candidates(row)
    return {
        "found": True,
        "candidates": [item.model_dump() for item in candidates],
        "errors": errors,
    }


def dispatch_inbox_action(message_id: str) -> dict:
    """Select the registered handler. The only inbox path that may mutate AP."""
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    classification = classify_message_impl(row)
    result, clarification = dispatch_impl(row, classification)
    return {
        "found": True,
        "classification": classification.model_dump(),
        "dispatch": result.model_dump(),
        "clarification": clarification.model_dump() if clarification else None,
    }


compose_counterparty_message_tool = function_tool(compose_counterparty_message)
send_inbox_message_tool = function_tool(send_inbox_message)
reply_in_thread_tool = function_tool(reply_in_thread)
get_inbox_message_tool = function_tool(get_inbox_message)
get_inbox_attachment_tool = function_tool(get_inbox_attachment)
classify_inbox_message_tool = function_tool(classify_inbox_message)
extract_inbox_invoice_tool = function_tool(extract_inbox_invoice)
dispatch_inbox_action_tool = function_tool(dispatch_inbox_action)

COUNTERPARTY_TOOLS = (
    compose_counterparty_message_tool,
    send_inbox_message_tool,
    reply_in_thread_tool,
)
INBOX_TOOLS = (
    get_inbox_message_tool,
    get_inbox_attachment_tool,
    classify_inbox_message_tool,
    extract_inbox_invoice_tool,
    dispatch_inbox_action_tool,
)

COUNTERPARTY_TOOL_NAMES = {
    "compose_counterparty_message",
    "send_inbox_message",
    "reply_in_thread",
}
INBOX_TOOL_NAMES = {
    "get_inbox_message",
    "get_inbox_attachment",
    "classify_inbox_message",
    "extract_inbox_invoice",
    "dispatch_inbox_action",
}
FORBIDDEN_COUNTERPARTY_TOOLS = {
    "dispatch_inbox_action",
    "register_runtime_invoice",
    "ingest_candidates",
    "register_canonical",
}
