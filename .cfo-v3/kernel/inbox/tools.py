"""Agent tools. Counterparty tools cannot write AP. Inbox tools dispatch only."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from agents import function_tool

from inbox.classify import classify_message as classify_message_impl
from inbox.dispatch import dispatch as dispatch_impl
from inbox.extract import attachment_text, extract_invoice_candidates, hash_attachment
from inbox.models import MessageEnvelope, MessageSpec
from inbox.personas import EMPLOYEE_SENDERS, list_personas
from inbox.transport import all_messages, all_thread_ids, deliver, get_message, list_thread

FINANCE_SENDERS = frozenset(
    {
        "ap@hackmit-cfo.example",
        "collections@hackmit-cfo.example",
        "ar@hackmit-cfo.example",
        "inbox@hackmit-cfo.example",
        "finance@hackmit-cfo.example",
    }
)
FINANCE_DOMAIN = "@hackmit-cfo.example"


def is_finance_sender(address: str) -> bool:
    """True when the address is a finance mailbox. Employee senders are not finance."""
    addr = (address or "").strip().lower()
    if not addr:
        return False
    if addr in EMPLOYEE_SENDERS:
        return False
    if addr in FINANCE_SENDERS:
        return True
    return addr.endswith(FINANCE_DOMAIN)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _received_iso(sent_at: str) -> str:
    try:
        stamp = datetime.strptime(sent_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (stamp + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return _now_iso()


def _persist_mailbox() -> None:
    try:
        from inbox.store import persist_state

        persist_state()
    except Exception:
        return


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
    if is_finance_sender(message.sender_address):
        return {
            "found": False,
            "error": (
                "send_inbox_message refuses finance senders. "
                "Finance speaks with send_office_outbound."
            ),
            "wrote_ap": False,
        }
    stored = deliver(message)
    _persist_mailbox()
    return {
        "found": True,
        "message_id": stored.message_id,
        "thread_id": stored.thread_id,
        "delivered": True,
        "attachment_hashes": [item.sha256 for item in stored.attachments if item.sha256],
        "wrote_ap": False,
    }


def send_office_outbound(
    thread_id: str,
    message_id: str,
    to_name: str,
    to_address: str,
    subject: str,
    body_text: str,
    from_address: str = "ap@hackmit-cfo.example",
    from_name: str = "HackMIT Finance",
    in_reply_to: str = "",
    sent_at: str = "2026-09-18T10:00:00Z",
) -> dict:
    """Finance speaks in the simulated mailbox. Counterparties cannot use this."""
    if not is_finance_sender(from_address):
        return {
            "found": False,
            "error": "send_office_outbound requires a finance from_address.",
            "wrote_ap": False,
        }
    if is_finance_sender(to_address):
        return {
            "found": False,
            "error": "send_office_outbound cannot address another finance mailbox.",
            "wrote_ap": False,
        }
    sender_name = from_name or (
        "Maximor Collections" if from_address.lower().startswith("collections@") else "HackMIT Finance"
    )
    envelope = MessageEnvelope(
        message_id=message_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to or None,
        sender_name=sender_name,
        sender_address=from_address,
        recipient_addresses=[to_address],
        subject=subject,
        body_text=body_text,
        sent_at=sent_at,
        received_at=_received_iso(sent_at),
        correlation_id=message_id,
        metadata={
            "office_outbound": True,
            "to_name": to_name,
        },
    )
    stored = deliver(envelope)
    _persist_mailbox()
    return {
        "found": True,
        "message_id": stored.message_id,
        "thread_id": stored.thread_id,
        "delivered": True,
        "office_outbound": True,
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
    if original.metadata.get("office_outbound") or is_finance_sender(original.sender_address):
        sender_address = original.recipient_addresses[0] if original.recipient_addresses else ""
        sender_name = str(original.metadata.get("to_name") or sender_address)
        recipients = [original.sender_address]
        metadata = {"reply": True}
    else:
        sender_address = original.sender_address
        sender_name = original.sender_name
        recipients = list(original.recipient_addresses)
        metadata = {"reply": True}
    reply = original.model_copy(
        update={
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "thread_id": thread_id,
            "sender_name": sender_name,
            "sender_address": sender_address,
            "recipient_addresses": recipients,
            "subject": subject or f"Re: {original.subject}",
            "body_text": body_text,
            "attachments": [],
            "correlation_id": original.correlation_id,
            "metadata": metadata,
        }
    )
    stored = deliver(reply)
    _persist_mailbox()
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


def list_world_personas() -> dict:
    """Read-only personas World may speak as. Does not write AP."""
    return {"found": True, "personas": list_personas(), "wrote_ap": False}


def list_inbox_threads() -> dict:
    threads = []
    for thread_id in all_thread_ids():
        messages = list_thread(thread_id)
        threads.append(
            {
                "thread_id": thread_id,
                "message_ids": [item.message_id for item in messages],
                "count": len(messages),
            }
        )
    if not threads:
        seen: dict[str, list[str]] = {}
        for item in all_messages():
            seen.setdefault(item.thread_id, []).append(item.message_id)
        threads = [
            {"thread_id": thread_id, "message_ids": ids, "count": len(ids)}
            for thread_id, ids in seen.items()
        ]
    return {"found": True, "threads": threads, "wrote_ap": False}


def list_inbox_messages(thread_id: str) -> dict:
    messages = list_thread(thread_id)
    return {
        "found": True,
        "thread_id": thread_id,
        "messages": [item.model_dump() for item in messages],
        "wrote_ap": False,
    }


def get_inbox_thread(thread_id: str) -> dict:
    messages = list_thread(thread_id)
    if not messages:
        return {"found": False, "error": f"Inbox thread {thread_id} was not found.", "wrote_ap": False}
    return {
        "found": True,
        "thread_id": thread_id,
        "messages": [item.model_dump() for item in messages],
        "wrote_ap": False,
    }


_compose_counterparty_message = compose_counterparty_message
_send_inbox_message = send_inbox_message
_send_office_outbound = send_office_outbound
_reply_in_thread = reply_in_thread
_get_inbox_message = get_inbox_message
_get_inbox_attachment = get_inbox_attachment
_classify_inbox_message = classify_inbox_message
_extract_inbox_invoice = extract_inbox_invoice
_dispatch_inbox_action = dispatch_inbox_action
_list_world_personas = list_world_personas
_list_inbox_threads = list_inbox_threads
_list_inbox_messages = list_inbox_messages
_get_inbox_thread = get_inbox_thread

compose_counterparty_message_tool = function_tool(compose_counterparty_message)
send_inbox_message_tool = function_tool(send_inbox_message)
send_office_outbound_tool = function_tool(send_office_outbound)
reply_in_thread_tool = function_tool(reply_in_thread)
get_inbox_message_tool = function_tool(get_inbox_message)
get_inbox_attachment_tool = function_tool(get_inbox_attachment)
classify_inbox_message_tool = function_tool(classify_inbox_message)
extract_inbox_invoice_tool = function_tool(extract_inbox_invoice)
dispatch_inbox_action_tool = function_tool(dispatch_inbox_action)
list_world_personas_tool = function_tool(list_world_personas)
list_inbox_threads_tool = function_tool(list_inbox_threads)
list_inbox_messages_tool = function_tool(list_inbox_messages)
get_inbox_thread_tool = function_tool(get_inbox_thread)

COUNTERPARTY_TOOLS = (
    compose_counterparty_message_tool,
    send_inbox_message_tool,
    reply_in_thread_tool,
    list_inbox_threads_tool,
    list_inbox_messages_tool,
    get_inbox_thread_tool,
    list_world_personas_tool,
)
INBOX_TOOLS = (
    get_inbox_message_tool,
    get_inbox_attachment_tool,
    classify_inbox_message_tool,
    extract_inbox_invoice_tool,
    dispatch_inbox_action_tool,
    list_inbox_threads_tool,
    list_inbox_messages_tool,
    get_inbox_thread_tool,
    send_office_outbound_tool,
)

COUNTERPARTY_TOOL_NAMES = {
    "compose_counterparty_message",
    "send_inbox_message",
    "reply_in_thread",
    "list_inbox_threads",
    "list_inbox_messages",
    "get_inbox_thread",
    "list_world_personas",
}
INBOX_TOOL_NAMES = {
    "get_inbox_message",
    "get_inbox_attachment",
    "classify_inbox_message",
    "extract_inbox_invoice",
    "dispatch_inbox_action",
    "send_office_outbound",
}
FORBIDDEN_COUNTERPARTY_TOOLS = {
    "dispatch_inbox_action",
    "send_office_outbound",
    "classify_inbox_message",
    "extract_inbox_invoice",
    "register_runtime_invoice",
    "ingest_candidates",
    "register_canonical",
}
FORBIDDEN_INBOX_TOOLS = {
    "send_inbox_message",
    "compose_counterparty_message",
    "reply_in_thread",
}
