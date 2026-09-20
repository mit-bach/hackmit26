"""Agent tools. Counterparty tools cannot write AP. Inbox tools dispatch only."""

from __future__ import annotations

from agents import function_tool

from inbox.classify import classify_message as classify_message_impl
from inbox.dispatch import dispatch as dispatch_impl
from inbox.extract import attachment_text, extract_invoice_candidates, hash_attachment
from inbox.models import MessageEnvelope, MessageSpec
from inbox.personas import list_personas
from inbox.transport import all_messages, deliver, get_message, list_thread

OFFICE_FROM_ADDRESSES = frozenset(
    {
        "ap@hackmit-cfo.example",
        "collections@hackmit-cfo.example",
    }
)
DEFAULT_AP_FROM = "ap@hackmit-cfo.example"
DEFAULT_COLLECTIONS_FROM = "collections@hackmit-cfo.example"


def _office_from_name(from_address: str) -> str:
    if from_address.lower() == DEFAULT_COLLECTIONS_FROM:
        return "HackMIT Collections"
    return "HackMIT AP"


def _compose_counterparty_message(
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


def _send_inbox_message(envelope_json: str) -> dict:
    message = MessageEnvelope.model_validate_json(envelope_json)
    if message.sender_address.lower() in OFFICE_FROM_ADDRESSES:
        return {
            "found": False,
            "error": (
                "send_inbox_message is the outside world speaking. "
                "Finance outbound uses send_office_outbound."
            ),
            "wrote_ap": False,
        }
    stored = deliver(message)
    return {
        "found": True,
        "message_id": stored.message_id,
        "thread_id": stored.thread_id,
        "delivered": True,
        "attachment_hashes": [item.sha256 for item in stored.attachments if item.sha256],
        "wrote_ap": False,
    }


def _reply_in_thread(
    thread_id: str,
    in_reply_to: str,
    message_id: str,
    body_text: str,
    subject: str = "",
) -> dict:
    original = get_message(in_reply_to)
    if original is None:
        thread = list_thread(thread_id)
        original = thread[0] if thread else None
    if original is None:
        return {"found": False, "error": "Original thread message was not found. Do not invent it."}
    metadata = dict(original.metadata)
    office_outbound = bool(metadata.get("office_outbound"))
    if office_outbound:
        if metadata.get("to_name"):
            sender_name = str(metadata["to_name"])
        elif original.recipient_addresses:
            sender_name = original.recipient_addresses[0]
        else:
            sender_name = original.sender_name
        if metadata.get("to_address"):
            sender_address = str(metadata["to_address"])
        elif original.recipient_addresses:
            sender_address = original.recipient_addresses[0]
        else:
            sender_address = original.sender_address
        recipients = [original.sender_address]
        reply_metadata = {"reply": True, "in_reply_to_office_outbound": True}
    else:
        sender_name = original.sender_name
        sender_address = original.sender_address
        recipients = list(original.recipient_addresses)
        reply_metadata = {"reply": True}
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
            "metadata": reply_metadata,
        }
    )
    stored = deliver(reply)
    return {"found": True, "message_id": stored.message_id, "thread_id": stored.thread_id, "wrote_ap": False}


def _get_inbox_message(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found. Do not invent it."}
    return {"found": True, "message": row.model_dump()}


def _get_inbox_attachment(message_id: str, filename: str) -> dict:
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


def _classify_inbox_message(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    return {"found": True, "classification": classify_message_impl(row).model_dump()}


def _extract_inbox_invoice(message_id: str) -> dict:
    row = get_message(message_id)
    if row is None:
        return {"found": False, "error": f"Inbox message {message_id} was not found."}
    candidates, errors = extract_invoice_candidates(row)
    return {
        "found": True,
        "candidates": [item.model_dump() for item in candidates],
        "errors": errors,
    }


def _dispatch_inbox_action(message_id: str) -> dict:
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


def _list_inbox_threads() -> dict:
    by_thread: dict[str, list[MessageEnvelope]] = {}
    for message in all_messages():
        by_thread.setdefault(message.thread_id, []).append(message)
    threads = []
    for thread_id, rows in by_thread.items():
        last = rows[-1]
        threads.append(
            {
                "thread_id": thread_id,
                "message_count": len(rows),
                "subject": last.subject,
                "last_sender_address": last.sender_address,
                "office_outbound": any(bool(item.metadata.get("office_outbound")) for item in rows),
            }
        )
    return {"found": True, "threads": threads}


def _list_inbox_messages(thread_id: str = "") -> dict:
    rows = list_thread(thread_id) if thread_id else all_messages()
    messages = [
        {
            "message_id": item.message_id,
            "thread_id": item.thread_id,
            "sender_name": item.sender_name,
            "sender_address": item.sender_address,
            "subject": item.subject,
            "sent_at": item.sent_at,
            "in_reply_to": item.in_reply_to,
            "office_outbound": bool(item.metadata.get("office_outbound")),
        }
        for item in rows
    ]
    return {"found": True, "messages": messages}


def _get_inbox_thread(thread_id: str) -> dict:
    rows = list_thread(thread_id)
    if not rows:
        return {"found": False, "error": f"Inbox thread {thread_id} was not found. Do not invent it."}
    return {
        "found": True,
        "thread_id": thread_id,
        "messages": [item.model_dump() for item in rows],
    }


def _list_world_personas() -> dict:
    return {"found": True, "personas": list_personas(), "wrote_ap": False}


def _send_office_outbound(
    thread_id: str,
    message_id: str,
    to_name: str,
    to_address: str,
    subject: str,
    body_text: str,
    from_address: str = DEFAULT_AP_FROM,
    from_name: str = "",
    in_reply_to: str = "",
    sent_at: str = "2026-09-18T12:00:00Z",
) -> dict:
    sender = from_address.strip().lower()
    if sender not in OFFICE_FROM_ADDRESSES:
        return {
            "found": False,
            "error": (
                "send_office_outbound must send from ap@hackmit-cfo.example or "
                "collections@hackmit-cfo.example. Do not impersonate a vendor."
            ),
            "wrote_ap": False,
        }
    display_name = from_name.strip() or _office_from_name(sender)
    received_at = sent_at.replace("T12:", "T12:") if "T12:" in sent_at else sent_at
    message = MessageEnvelope(
        message_id=message_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to or None,
        sender_name=display_name,
        sender_address=sender,
        recipient_addresses=[to_address],
        subject=subject,
        body_text=body_text,
        sent_at=sent_at,
        received_at=received_at,
        correlation_id=message_id,
        metadata={
            "office_outbound": True,
            "to_name": to_name,
            "to_address": to_address,
            "from_address": sender,
            "from_name": display_name,
        },
    )
    stored = deliver(message)
    return {
        "found": True,
        "message_id": stored.message_id,
        "thread_id": stored.thread_id,
        "delivered": True,
        "office_outbound": True,
        "wrote_ap": False,
    }


@function_tool
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
    return _compose_counterparty_message(
        case_id,
        message_id,
        thread_id,
        sender_name,
        sender_address,
        subject,
        body_text,
        sent_at,
        received_at,
        in_reply_to,
        correlation_id,
        recipient,
    )


@function_tool
def send_inbox_message(envelope_json: str) -> dict:
    """Deliver a JSON message envelope to the finance inbox. Not an AP write."""
    return _send_inbox_message(envelope_json)


@function_tool
def reply_in_thread(thread_id: str, in_reply_to: str, message_id: str, body_text: str, subject: str = "") -> dict:
    """Send a clarification reply in the same thread. Cannot write AP records."""
    return _reply_in_thread(thread_id, in_reply_to, message_id, body_text, subject)


@function_tool
def get_inbox_message(message_id: str) -> dict:
    """Load one finance-inbox message. Returns found=false if it does not exist."""
    return _get_inbox_message(message_id)


@function_tool
def get_inbox_attachment(message_id: str, filename: str) -> dict:
    """Extract text from one inbox attachment. Do not invent missing files."""
    return _get_inbox_attachment(message_id, filename)


@function_tool
def classify_inbox_message(message_id: str) -> dict:
    """Classify one inbound finance-inbox message. Does not write AP records."""
    return _classify_inbox_message(message_id)


@function_tool
def extract_inbox_invoice(message_id: str) -> dict:
    """Extract invoice candidates from one inbox message. Python owns amounts."""
    return _extract_inbox_invoice(message_id)


@function_tool
def dispatch_inbox_action(message_id: str) -> dict:
    """Select the registered handler. The only inbox path that may mutate AP."""
    return _dispatch_inbox_action(message_id)


@function_tool
def list_inbox_threads() -> dict:
    """List finance-inbox threads. Browse only. Does not write AP records."""
    return _list_inbox_threads()


@function_tool
def list_inbox_messages(thread_id: str = "") -> dict:
    """List finance-inbox messages. Pass thread_id to limit the list to one thread."""
    return _list_inbox_messages(thread_id)


@function_tool
def get_inbox_thread(thread_id: str) -> dict:
    """Load every message in one finance-inbox thread. Do not invent missing threads."""
    return _get_inbox_thread(thread_id)


@function_tool
def list_world_personas() -> dict:
    """List simulated vendors, customers, banks, and employees. Read-only. Does not write AP."""
    return _list_world_personas()


@function_tool
def send_office_outbound(
    thread_id: str,
    message_id: str,
    to_name: str,
    to_address: str,
    subject: str,
    body_text: str,
    from_address: str = DEFAULT_AP_FROM,
    from_name: str = "",
    in_reply_to: str = "",
    sent_at: str = "2026-09-18T12:00:00Z",
) -> dict:
    """Send finance mail from ap@ or collections@ to a persona. Marks office_outbound. Not an AP write."""
    return _send_office_outbound(
        thread_id,
        message_id,
        to_name,
        to_address,
        subject,
        body_text,
        from_address,
        from_name,
        in_reply_to,
        sent_at,
    )


COUNTERPARTY_TOOLS = (
    compose_counterparty_message,
    send_inbox_message,
    reply_in_thread,
    list_inbox_threads,
    list_inbox_messages,
    get_inbox_thread,
    list_world_personas,
)
INBOX_TOOLS = (
    get_inbox_message,
    get_inbox_attachment,
    classify_inbox_message,
    extract_inbox_invoice,
    dispatch_inbox_action,
    list_inbox_threads,
    list_inbox_messages,
    get_inbox_thread,
    send_office_outbound,
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
    "list_inbox_threads",
    "list_inbox_messages",
    "get_inbox_thread",
    "send_office_outbound",
}
FORBIDDEN_COUNTERPARTY_TOOLS = {
    "dispatch_inbox_action",
    "send_office_outbound",
    "register_runtime_invoice",
    "ingest_candidates",
    "register_canonical",
    "get_invoice",
    "create_accrual",
    "get_payment_candidates",
    "get_approved_pool",
    "get_cash_application_facts",
}
FORBIDDEN_INBOX_TOOLS = {
    "send_inbox_message",
    "compose_counterparty_message",
    "reply_in_thread",
}
