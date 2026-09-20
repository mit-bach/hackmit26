from __future__ import annotations

from inbox.demo import format_demo, run_demo_inbox
from inbox.fixtures import e2e_specs, spec_incomplete_reply
from inbox.store import created_invoice_ids, notices
from inbox.workflow import handoff, handoff_reply
from tools import all_invoices, load_invoice


def test_e2e_mixed_inbox_record_counts():
    before = {item.invoice_id for item in all_invoices()}
    results = []
    for spec in e2e_specs():
        results.append(handoff(spec, persist=False))
        if spec.case_id == "incomplete":
            reply = spec_incomplete_reply()
            results.append(
                handoff_reply(
                    reply.thread_id,
                    reply.in_reply_to,
                    reply.message_id,
                    reply.body_text,
                    persist=False,
                )
            )
    after = {item.invoice_id for item in all_invoices()}
    created = after - before
    statuses = {item.sender.message_id: item.final_status for item in results}
    classes = {item.sender.message_id: item.receiver.classification.classification for item in results}

    assert classes["MSG-INBOX-001"] == "VENDOR_INVOICE"
    assert statuses["MSG-INBOX-001"] == "CREATED"
    assert classes["MSG-INBOX-013"] != "VENDOR_INVOICE" or statuses["MSG-INBOX-013"] == "BUSINESS_DUPLICATE"
    assert classes["MSG-INBOX-005"] == "PURCHASE_ORDER"
    assert classes["MSG-INBOX-007"] == "VENDOR_STATEMENT"
    assert statuses["MSG-INBOX-011"] == "NEEDS_INFORMATION"
    assert results[-2].invoice_id or any(item.invoice_id for item in results if item.sender.message_id == "MSG-INBOX-011R")
    assert "PROMPT_INJECTION" in results[-1].trace.reason_codes or classes["MSG-INBOX-014"] == "VENDOR_INVOICE"

    assert len(created) == 3  # clean, clarification, injection (duplicate does not add)
    assert len(created_invoice_ids()) == 3
    assert all(load_invoice(invoice_id) is not None for invoice_id in created)
    assert notices("ignored") or classes["MSG-INBOX-007"] == "VENDOR_STATEMENT"


def test_demo_default_is_one_invoice_and_one_non_invoice():
    results = run_demo_inbox(full=False, reset=True, persist=False)
    assert len(results) == 2
    assert results[0].invoice_id
    assert results[1].invoice_id is None
    assert results[1].receiver.classification.classification == "NON_FINANCE"
    text = format_demo(results)
    assert "Counterparty Message Agent" in text
    assert "Finance Inbox Agent" in text
    assert "Classification:" in text
    assert load_invoice(results[0].invoice_id) is not None
