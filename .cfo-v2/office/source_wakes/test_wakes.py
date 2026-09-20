from __future__ import annotations

import json
from pathlib import Path

from integrations.providers import stripe
from invoice_ingestion.interpret import classify_text, interpret_email
from invoice_ingestion.models import InvoiceCandidate
from invoice_ingestion.sources import run_bank_card_source
from invoice_ingestion.workflow import ingest_invoices
from source_wakes.packets import read_packet
from source_wakes.wakes import land_bank_transaction, land_email_message, land_stripe_payout, write_send_payloads


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def test_email_invoice_writes_file_and_addresses_ap(tmp_path):
    computer = tmp_path / "computer"
    result = land_email_message(computer, "MSG-E01", profile="invoice")
    assert result.classification == "invoice"
    assert result.packet_path is not None
    assert (computer / result.packet_path).is_file()
    packet = read_packet(computer, result.packet_path)
    assert packet["candidate"] is not None
    assert packet["destination"] == {"slug": "ap", "profile": "prepare"}
    assert len(result.intents) == 1
    payload = result.intents[0].to_send_payload()
    assert payload["toSlug"] == "ap"
    assert payload["to"] == "bot_ap"
    assert payload["from"] == "bot_email"
    assert payload["profile"] == "prepare"
    assert payload["kind"] == "a2a_handoff"
    assert result.packet_path in payload["paths"]
    send_path = write_send_payloads(computer, result)
    dumped = json.loads(send_path.read_text())
    assert dumped[0]["toSlug"] == "ap"


def test_email_remittance_addresses_apply(tmp_path):
    remittance = {
        "message_id": "MSG-R01",
        "from": "ap@northstar.example",
        "subject": "Remittance advice for INV-AR-007",
        "body": "Please find our remittance advice. Payment received for INV-AR-007. Thank you for your payment.",
        "thread_uri": "email://ar-inbox/MSG-R01",
        "attachments": [],
    }
    classification, reason, candidates = interpret_email(remittance)
    assert classification == "payment_confirmation"
    assert candidates == []
    computer = tmp_path / "computer"
    result = land_email_message(computer, "MSG-R01", profile="invoice", email=remittance)
    assert result.classification == "payment_confirmation"
    assert result.invoice_candidates == 0
    assert len(result.intents) == 1
    payload = result.intents[0].to_send_payload()
    assert payload["toSlug"] == "apply"
    assert payload["to"] == "bot_apply"
    assert payload["profile"] == "apply"


def test_email_two_pipes_do_not_split_bots():
    invoice = classify_text("Invoice Number: INV-1\nInvoice date: 2026-09-01\nAmount due: $10.00")
    remittance = classify_text("Remittance advice. Payment received for INV-AR-007.")
    assert invoice[0] == "invoice"
    assert remittance[0] == "payment_confirmation"


def test_stripe_fixture_payout_is_not_an_invoice_candidate(tmp_path):
    payload = stripe.demo_payloads()[1]
    raw = _raw(payload)
    computer = tmp_path / "computer"
    result = land_stripe_payout(computer, raw, {"stripe-signature": "test"}, require_signature=False)
    assert result.kernel_status == "processed"
    assert result.invoice_candidates == 0
    assert result.packet_path is not None
    packet = read_packet(computer, result.packet_path)
    assert packet["invoice_candidates"] == 0
    assert "InvoiceCandidate" not in json.dumps(packet)
    slugs = {item.to_slug for item in result.intents}
    assert slugs == {"cash", "apply"}
    assert all(item.from_slug == "stripe" for item in result.intents)
    assert all(not isinstance(item, InvoiceCandidate) for item in result.intents)


def test_bank_charge_without_docs_stays_invoice_missing(tmp_path):
    run = run_bank_card_source("2026-09")
    missing = next(item for item in run.discovery if item.transaction_id == "CC-4412")
    assert missing.status == "invoice_missing"
    assert missing.candidate is None
    computer = tmp_path / "computer"
    result = land_bank_transaction(computer, "CC-4412")
    assert result.classification == "invoice_missing"
    assert result.intents == []
    assert result.invoice_candidates == 0
    packet = read_packet(computer, result.packet_path)
    assert packet["status"] == "invoice_missing"
    assert packet["candidate"] is None


def test_inbox_kernel_lands_bill_to_ap(tmp_path):
    from inbox.fixtures import spec_clean_attachment
    from source_wakes.wakes import land_inbox_spec

    computer = tmp_path / "computer"
    result = land_inbox_spec(computer, spec_clean_attachment(), profile="invoice")
    assert result.kernel_status in {"CREATED", "LINKED", "BUSINESS_DUPLICATE", "DUPLICATE_DELIVERY"}
    assert result.packet_path is not None
    packet = read_packet(computer, result.packet_path)
    assert packet["destination"] == {"slug": "ap", "profile": "prepare"}
    assert result.intents[0].to_send_payload()["toSlug"] == "ap"
    assert result.details.get("canonical_id")


def test_aws_bill_from_two_sources_is_one_invoice():
    report = ingest_invoices("2026-09", forward_to_ap=True, reset_overlay=True)
    aws = [item for item in report.canonical_invoices if item.vendor_invoice_number == "INV-9001"]
    assert len(aws) == 1
    assert {ref.source_type for ref in aws[0].sources} == {"email", "vendor_portal", "bank_card"}
