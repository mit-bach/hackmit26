from __future__ import annotations

import pytest
from pydantic import ValidationError

from inbox.classify import classify_message, lookup_default_action, lookup_dispatch_target
from inbox.dispatch import action_for_classification, lookup_handler
from inbox.extract import hash_attachment
from inbox.fixtures import (
    CLEAN_INVOICE,
    spec_clean_attachment,
    spec_credit_memo,
    spec_injection,
    spec_malformed,
    spec_non_finance,
    spec_purchase_order,
    spec_quote,
)
from inbox.models import (
    INBOX_ACTIONS,
    INBOX_CLASSES,
    InboxClassification,
    MessageAttachment,
    MessageEnvelope,
)
from inbox.normalize import cents_to_dollars, dollars_to_cents, normalize_currency, normalize_po
from inbox.security import has_prompt_injection, has_unsafe_mutation_request
from inbox.store import created_invoice_ids
from inbox.transport import deliver, prior_outcome
from inbox.workflow import handoff
from tools import load_invoice


def _envelope(spec) -> MessageEnvelope:
    return MessageEnvelope.model_validate(spec.model_dump())


def test_message_schema_requires_core_fields():
    with pytest.raises(ValidationError):
        MessageEnvelope(
            message_id="x",
            thread_id="t",
            sender_name="A",
            sender_address="a@b.c",
            subject="s",
            body_text="b",
            sent_at="2026-09-18T10:00:00Z",
            received_at="2026-09-18T10:00:00Z",
        )


def test_classification_schema_rejects_unknown_class():
    with pytest.raises(ValidationError):
        InboxClassification(
            classification="RANDOM_TYPE",
            selected_action="IGNORE",
            confidence=0.9,
        )


def test_classification_schema_accepts_registered_values():
    for name in INBOX_CLASSES:
        item = InboxClassification(
            classification=name,
            selected_action=lookup_default_action(name) or "IGNORE",
            confidence=0.5,
        )
        assert item.classification == name
    assert "CREATE_AP_INVOICE" in INBOX_ACTIONS


def test_attachment_hash_is_stable():
    attachment = MessageAttachment(filename="a.pdf", mime_type="application/pdf", content=CLEAN_INVOICE)
    assert hash_attachment(attachment) == hash_attachment(attachment)
    other = MessageAttachment(filename="a.pdf", mime_type="application/pdf", content=CLEAN_INVOICE + "\nextra")
    assert hash_attachment(attachment) != hash_attachment(other)


def test_action_registry_lookup():
    assert lookup_handler("CREATE_AP_INVOICE") is not None
    assert lookup_handler("NOT_A_REAL_ACTION") is None
    assert action_for_classification("VENDOR_INVOICE") == "CREATE_AP_INVOICE"
    assert action_for_classification("NON_FINANCE") == "IGNORE"
    assert action_for_classification("UNKNOWN") is None
    assert lookup_dispatch_target("CREATE_AP_INVOICE") == "invoice_ingestion.workflow.ingest_candidates"


def test_field_normalization():
    assert dollars_to_cents(12450.0) == 1_245_000
    assert cents_to_dollars(1_245_000) == 12450.0
    assert normalize_po("PO101") == "PO-101"
    assert normalize_currency(None, text="Amount Due $12.00") == "USD"


def test_prompt_injection_is_detected_and_ignored():
    import inbox.classify as classify_mod

    assert "prove-fork" in classify_mod.__file__, classify_mod.__file__
    message = _envelope(spec_injection())
    assert has_prompt_injection(message)
    assert has_unsafe_mutation_request(message)
    before = created_invoice_ids()
    result = handoff(spec_injection(), persist=False)
    assert result.invoice_id in (None, "")
    assert "PROMPT_INJECTION" in result.trace.reason_codes
    assert result.receiver.dispatch.mutation is False
    assert result.receiver.dispatch.ready_for_payment is False
    assert result.final_status == "REJECTED"
    assert created_invoice_ids() == before


def test_unsupported_action_fails_closed():
    from inbox.dispatch import dispatch
    from inbox.models import InboxClassification

    message = _envelope(spec_non_finance())
    bogus = InboxClassification(
        classification="NON_FINANCE",
        selected_action="REJECT_UNSAFE_REQUEST",
        confidence=0.1,
        reason_codes=["FORCED"],
    )
    # Unknown action string cannot be constructed on the model; registry lookup fails closed.
    assert lookup_handler("invent_a_payable") is None
    result, _ = dispatch(message, bogus)
    assert result.mutation is False
    assert created_invoice_ids() == []


def test_persisted_state_replays_transport_outcome(tmp_path):
    from inbox.store import configure_runs_dir, load_state, persist_state, reset_inbox_state
    from invoice_ingestion.adapter import reset_ingested_invoices

    configure_runs_dir(tmp_path)
    first = handoff(spec_clean_attachment(), persist=True)
    persist_state()
    reset_inbox_state()
    reset_ingested_invoices()
    load_state()
    second = handoff(spec_clean_attachment(), persist=False)
    assert second.replayed is True
    assert second.final_status == "DUPLICATE_DELIVERY"
    assert first.invoice_id == second.invoice_id
    assert created_invoice_ids() == [first.invoice_id]


def test_transport_idempotency_same_message_id():
    first = handoff(spec_clean_attachment(), persist=False)
    second = handoff(spec_clean_attachment(), persist=False)
    assert second.replayed is True
    assert second.final_status == "DUPLICATE_DELIVERY"
    assert first.invoice_id == second.invoice_id
    assert created_invoice_ids().count(first.invoice_id) == 1
    assert load_invoice(first.invoice_id) is not None


def test_quote_and_po_never_become_invoices():
    quote = handoff(spec_quote(), persist=False)
    po = handoff(spec_purchase_order(), persist=False)
    assert quote.receiver.classification.classification == "CONTRACT_OR_QUOTE"
    assert po.receiver.classification.classification == "PURCHASE_ORDER"
    assert quote.invoice_id is None
    assert po.invoice_id is None
    assert created_invoice_ids() == []


def test_credit_memo_is_unsupported_not_an_invoice():
    result = handoff(spec_credit_memo(), persist=False)
    assert result.receiver.classification.classification == "CREDIT_MEMO"
    assert "CREDIT_MEMO_PATH_UNAVAILABLE" in result.trace.reason_codes
    assert result.invoice_id is None
    assert created_invoice_ids() == []


def test_malformed_attachment_has_stable_reason_code():
    result = handoff(spec_malformed(), persist=False)
    assert result.invoice_id is None
    assert "PARSE_FAILURE" in result.trace.reason_codes or "UNSUPPORTED_ATTACHMENT" in result.trace.reason_codes
    assert created_invoice_ids() == []
