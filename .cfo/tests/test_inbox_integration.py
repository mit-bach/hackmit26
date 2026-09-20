from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from inbox.agents import counterparty_message_agent, finance_inbox_agent
from inbox.tools import COUNTERPARTY_TOOL_NAMES, FORBIDDEN_COUNTERPARTY_TOOLS, INBOX_TOOL_NAMES
from inbox.fixtures import (
    spec_body_invoice,
    spec_business_duplicate,
    spec_clean_attachment,
    spec_concurrent,
    spec_goods_receipt,
    spec_incomplete,
    spec_incomplete_reply,
    spec_no_po,
    spec_payment,
    spec_price_mismatch,
    spec_unknown_vendor,
)
from inbox.store import created_invoice_ids, notices
from inbox.transport import get_message, list_thread
from inbox.workflow import handoff, handoff_reply
from invoice_ingestion.store import is_known_vendor
from tools import all_invoices, collect_case_evidence, load_invoice


def test_two_distinct_agents_and_tool_boundaries():
    assert counterparty_message_agent.name == "Counterparty Message Agent"
    assert finance_inbox_agent.name == "Finance Inbox Agent"
    assert counterparty_message_agent.name != finance_inbox_agent.name
    def _names(agent):
        names = set()
        for tool in agent.tools:
            names.add(getattr(tool, "name", None) or getattr(tool, "__name__", str(tool)))
        return names

    cp_tools = _names(counterparty_message_agent)
    ib_tools = _names(finance_inbox_agent)
    assert COUNTERPARTY_TOOL_NAMES <= cp_tools or "send_inbox_message" in " ".join(cp_tools)
    assert not (FORBIDDEN_COUNTERPARTY_TOOLS & cp_tools)
    assert "dispatch_inbox_action" in ib_tools or INBOX_TOOL_NAMES & ib_tools
    assert "send_inbox_message" not in ib_tools
    assert finance_inbox_agent.tools
    assert counterparty_message_agent.instructions != finance_inbox_agent.instructions


def test_sender_to_transport_to_inbox():
    result = handoff(spec_clean_attachment(), persist=False)
    stored = get_message("MSG-INBOX-001")
    assert stored is not None
    assert stored.sender_address == "billing@acmesupplies.example"
    assert result.sender.agent == "Counterparty Message Agent"
    assert result.receiver.agent == "Finance Inbox Agent"
    assert result.sender.run_id.startswith("RUN-CP-")
    assert result.receiver.run_id.startswith("RUN-IB-")
    assert result.sender.run_id != result.receiver.run_id


def test_clean_attachment_creates_one_canonical_invoice_and_matches():
    before = {item.invoice_id for item in all_invoices()}
    result = handoff(spec_clean_attachment(), persist=False)
    after = {item.invoice_id for item in all_invoices()}
    created = after - before
    assert result.invoice_id in created
    assert len(created_invoice_ids()) == 1
    invoice = load_invoice(result.invoice_id)
    assert invoice.vendor == "Acme Supplies"
    assert invoice.vendor_invoice_number == "ACM-INBOX-1001"
    assert invoice.po_id == "PO-101"
    assert invoice.amount == 12450
    evidence = collect_case_evidence(result.invoice_id)
    assert evidence.po_exists is True
    assert evidence.amount_matches is True
    assert evidence.receipt_status == "full"
    assert evidence.exception_types == []
    assert result.receiver.dispatch.match_status == "MATCHED"
    assert result.receiver.dispatch.ready_for_payment is False
    assert result.trace.invoice_id == result.invoice_id
    assert result.trace.attachment_hashes
    assert invoice.source_message_id == "MSG-INBOX-001"
    assert invoice.source_thread_id == result.trace.thread_id
    assert invoice.source_trace_id == result.trace.trace_id
    assert invoice.source_attachment_hashes == result.trace.attachment_hashes


def test_body_only_invoice_creates_one_payable():
    result = handoff(spec_body_invoice(), persist=False)
    assert result.invoice_id
    invoice = load_invoice(result.invoice_id)
    assert invoice.vendor_invoice_number == "FIG-INBOX-2002"
    assert invoice.amount == 2448
    assert len(created_invoice_ids()) == 1


def test_price_mismatch_is_recorded_and_blocked():
    result = handoff(spec_price_mismatch(), persist=False)
    assert result.invoice_id
    evidence = collect_case_evidence(result.invoice_id)
    assert "material_amount_mismatch" in evidence.exception_types
    assert result.receiver.dispatch.match_status == "BLOCKED"
    assert result.receiver.dispatch.ready_for_payment is False
    invoice = load_invoice(result.invoice_id)
    assert invoice.amount == 5000


def test_no_po_invoice_is_recorded_unmatched():
    result = handoff(spec_no_po(), persist=False)
    assert result.invoice_id
    invoice = load_invoice(result.invoice_id)
    assert invoice.po_id is None
    evidence = collect_case_evidence(result.invoice_id)
    assert "missing_po" in evidence.exception_types
    assert result.receiver.dispatch.match_status in {"NON_PO", "UNMATCHED", "EXCEPTION"}
    assert result.receiver.dispatch.ready_for_payment is False


def test_goods_receipt_routes_without_creating_invoice():
    result = handoff(spec_goods_receipt(), persist=False)
    assert result.receiver.classification.classification == "GOODS_RECEIPT"
    assert result.receiver.classification.selected_action == "RECORD_GOODS_RECEIPT"
    assert result.invoice_id is None
    assert notices("goods_receipt")
    assert created_invoice_ids() == []


def test_payment_confirmation_routes_without_creating_invoice():
    result = handoff(spec_payment(), persist=False)
    assert result.receiver.classification.classification == "PAYMENT_CONFIRMATION"
    assert result.invoice_id is None
    assert notices("payment_notice")


def test_clarification_reply_in_same_thread_creates_one_invoice():
    first = handoff(spec_incomplete(), persist=False)
    assert first.invoice_id is None
    assert first.final_status == "NEEDS_INFORMATION"
    assert first.receiver.clarification is not None
    assert "invoice_number" in first.receiver.clarification.missing_fields or "amount" in first.receiver.clarification.missing_fields
    outbound = get_message("MSG-INBOX-011-OUT")
    assert outbound is not None
    assert outbound.metadata.get("office_outbound") is True
    assert outbound.sender_address == "ap@hackmit-cfo.example"
    handle_path = first.receiver.dispatch.details.get("world_handle_path")
    assert handle_path
    assert Path(handle_path).is_file()
    handle_path = first.receiver.dispatch.details.get("world_handle_path")
    assert handle_path
    assert Path(handle_path).is_file()
    reply_spec = spec_incomplete_reply()
    second = handoff_reply(
        reply_spec.thread_id,
        reply_spec.in_reply_to,
        reply_spec.message_id,
        reply_spec.body_text,
        persist=False,
    )
    assert list_thread("THR-incomplete")
    assert {item.message_id for item in list_thread("THR-incomplete")} >= {"MSG-INBOX-011", "MSG-INBOX-011R"}
    assert second.invoice_id
    assert load_invoice(second.invoice_id).vendor_invoice_number == "ACM-INBOX-5005"
    assert len(created_invoice_ids()) == 1
    assert len(second.trace.attempts) >= 1


def test_business_duplicate_links_and_does_not_create_second_payable():
    first = handoff(spec_clean_attachment(), persist=False)
    second = handoff(spec_business_duplicate(), persist=False)
    assert first.invoice_id
    assert second.final_status == "BUSINESS_DUPLICATE"
    assert len(created_invoice_ids()) == 1
    assert load_invoice(first.invoice_id) is not None
    assert second.receiver.dispatch.duplicate_of == first.invoice_id or second.invoice_id == first.invoice_id


def test_unknown_vendor_does_not_become_trusted():
    result = handoff(spec_unknown_vendor(), persist=False)
    assert result.invoice_id
    invoice = load_invoice(result.invoice_id)
    assert invoice.vendor == "Nimbus Analytics LLC"
    assert is_known_vendor("Nimbus Analytics LLC") is False
    assert "UNKNOWN_VENDOR" in result.trace.reason_codes


def test_concurrent_duplicate_creates_one_invoice():
    specs = [spec_concurrent("MSG-INBOX-017A"), spec_concurrent("MSG-INBOX-017B")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda spec: handoff(spec, persist=False), specs))
    invoice_ids = {item.invoice_id for item in results if item.invoice_id}
    assert len(created_invoice_ids()) == 1
    assert len(invoice_ids) == 1
    assert load_invoice(next(iter(invoice_ids))) is not None


def test_downstream_visibility_from_canonical_ap_record():
    result = handoff(spec_clean_attachment(), persist=False)
    invoice_id = result.invoice_id
    assert any(item.invoice_id == invoice_id for item in all_invoices())
    evidence = collect_case_evidence(invoice_id)
    assert evidence.invoice is not None
    assert evidence.invoice.invoice_id == invoice_id
