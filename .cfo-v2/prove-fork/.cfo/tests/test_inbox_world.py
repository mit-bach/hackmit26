"""World mailbox tools: personas, outbound+reply roundtrip, Grant boundaries."""

from __future__ import annotations

from inbox.agents import counterparty_message_agent, finance_inbox_agent, run_counterparty_agent
from inbox.fixtures import spec_clean_attachment
from inbox.tools import (
    COUNTERPARTY_TOOL_NAMES,
    FORBIDDEN_COUNTERPARTY_TOOLS,
    FORBIDDEN_INBOX_TOOLS,
    INBOX_TOOL_NAMES,
    _get_inbox_thread,
    _list_inbox_messages,
    _list_inbox_threads,
    _list_world_personas,
    _reply_in_thread,
    _send_inbox_message,
    _send_office_outbound,
)
from inbox.transport import get_message


def _tool_names(agent) -> set[str]:
    names: set[str] = set()
    for tool in agent.tools:
        names.add(getattr(tool, "name", None) or getattr(tool, "__name__", str(tool)))
    return names


def test_world_agent_cannot_dispatch_or_send_as_finance() -> None:
    cp_tools = _tool_names(counterparty_message_agent)
    ib_tools = _tool_names(finance_inbox_agent)
    assert COUNTERPARTY_TOOL_NAMES <= cp_tools
    assert INBOX_TOOL_NAMES <= ib_tools
    assert not (FORBIDDEN_COUNTERPARTY_TOOLS & cp_tools)
    assert "dispatch_inbox_action" not in cp_tools
    assert "send_office_outbound" not in cp_tools
    assert "send_inbox_message" not in ib_tools
    assert not (FORBIDDEN_INBOX_TOOLS & ib_tools)
    assert "send_office_outbound" in ib_tools


def test_list_world_personas_includes_vendors_and_customers() -> None:
    result = _list_world_personas()
    assert result["found"] is True
    assert result["wrote_ap"] is False
    personas = result["personas"]
    roles = {row["role"] for row in personas}
    names = {row["name"] for row in personas}
    assert "vendor" in roles
    assert "customer" in roles
    assert "bank" in roles
    assert "Acme Supplies" in names
    assert "Northwind Labs" in names


def test_send_office_outbound_and_reply_in_thread_roundtrip() -> None:
    outbound = _send_office_outbound(
        thread_id="THR-world-roundtrip",
        message_id="MSG-OUT-001",
        to_name="Acme Supplies",
        to_address="billing@acmesupplies.example",
        subject="Missing invoice number",
        body_text="Please send the invoice number for September.",
        from_address="ap@hackmit-cfo.example",
    )
    assert outbound["found"] is True
    assert outbound["office_outbound"] is True
    assert outbound["wrote_ap"] is False
    stored = get_message("MSG-OUT-001")
    assert stored is not None
    assert stored.metadata.get("office_outbound") is True
    assert stored.sender_address == "ap@hackmit-cfo.example"

    reply = _reply_in_thread(
        "THR-world-roundtrip",
        "MSG-OUT-001",
        "MSG-OUT-001R",
        "Invoice Number: ACM-INBOX-1001\nAmount Due: 12450.00",
    )
    assert reply["found"] is True
    answer = get_message("MSG-OUT-001R")
    assert answer is not None
    assert answer.sender_address == "billing@acmesupplies.example"
    assert answer.sender_name == "Acme Supplies"
    assert "ap@hackmit-cfo.example" in answer.recipient_addresses
    assert answer.metadata.get("office_outbound") is not True
    thread = _get_inbox_thread("THR-world-roundtrip")
    assert thread["found"] is True
    assert {item["message_id"] for item in thread["messages"]} == {"MSG-OUT-001", "MSG-OUT-001R"}
    listed = _list_inbox_threads()
    assert any(row["thread_id"] == "THR-world-roundtrip" for row in listed["threads"])
    msgs = _list_inbox_messages("THR-world-roundtrip")
    assert len(msgs["messages"]) == 2


def test_world_cannot_send_inbox_message_as_finance() -> None:
    envelope = {
        "message_id": "MSG-FAKE-AP",
        "thread_id": "THR-fake",
        "sender_name": "HackMIT AP",
        "sender_address": "ap@hackmit-cfo.example",
        "recipient_addresses": ["billing@acmesupplies.example"],
        "subject": "Not allowed",
        "body_text": "impersonation",
        "sent_at": "2026-09-18T10:00:00Z",
        "received_at": "2026-09-18T10:00:02Z",
        "correlation_id": "MSG-FAKE-AP",
    }
    import json

    result = _send_inbox_message(json.dumps(envelope))
    assert result["found"] is False
    assert get_message("MSG-FAKE-AP") is None


def test_office_outbound_rejects_vendor_from_address() -> None:
    result = _send_office_outbound(
        thread_id="THR-bad-from",
        message_id="MSG-BAD-FROM",
        to_name="Acme Supplies",
        to_address="billing@acmesupplies.example",
        subject="nope",
        body_text="nope",
        from_address="billing@acmesupplies.example",
    )
    assert result["found"] is False
    assert get_message("MSG-BAD-FROM") is None


def test_world_fixture_send_lands_for_email() -> None:
    sent = run_counterparty_agent(spec_clean_attachment())
    assert sent.sent is True
    stored = get_message("MSG-INBOX-001")
    assert stored is not None
    assert stored.sender_address == "billing@acmesupplies.example"
