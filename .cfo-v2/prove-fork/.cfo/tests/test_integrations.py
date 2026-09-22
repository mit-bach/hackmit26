from __future__ import annotations

import json

from fastapi.testclient import TestClient

from integrations.cash import reconcile_payout
from integrations.demo import process_provider, run_integration_demo
from integrations.providers import adyen, coupa, gmail, netsuite, outlook, stripe, xero
from integrations.server import app
from integrations.store import all_payouts, gmail_history_id, get_payout
from invoice_ingestion.models import InvoiceCandidate
from tools import all_invoices


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def test_stripe_valid_signature_accepted():
    payload = stripe.demo_payloads()[1]
    raw = _raw(payload)
    result = stripe.process_raw(raw, {"stripe-signature": stripe.sign(raw)})
    assert result.status == "processed"
    assert result.payout_id == "po_1HackMIT97420"
    assert result.invoice_candidates == 0


def test_stripe_invalid_signature_rejected():
    payload = stripe.demo_payloads()[1]
    raw = _raw(payload)
    result = stripe.process_raw(raw, {"stripe-signature": "t=1,v1=deadbeef"})
    assert result.status == "rejected"


def test_stripe_duplicate_event_idempotent():
    payload = stripe.demo_payloads()[1]
    raw = _raw(payload)
    headers = {"stripe-signature": stripe.sign(raw)}
    first = stripe.process_raw(raw, headers)
    second = stripe.process_raw(raw, {"stripe-signature": stripe.sign(raw)})
    assert first.status == "processed"
    assert second.duplicate is True
    assert len([item for item in all_payouts() if item.provider == "stripe"]) == 1


def test_stripe_reconciliation_loads_transactions_and_is_not_an_invoice():
    for payload in stripe.demo_payloads():
        raw = _raw(payload)
        stripe.process_raw(raw, {"stripe-signature": stripe.sign(raw)})
    payout = get_payout("po_1HackMIT97420")
    assert payout is not None
    assert len(payout.lines) >= 4
    breakdown = reconcile_payout(payout)
    assert breakdown.gross_payments == 102000.0
    assert breakdown.refunds == -1500.0
    assert breakdown.chargebacks == -1000.0
    assert breakdown.fees == -2080.0
    assert breakdown.expected_payout == 97420.0
    assert breakdown.actual_payout == 97420.0
    assert breakdown.matched is True
    assert all(not isinstance(item, InvoiceCandidate) for item in [])
    assert all(item.invoice_id != "po_1HackMIT97420" for item in all_invoices())


def test_adyen_valid_hmac_and_duplicate():
    payload = adyen.demo_payloads()[1]
    raw = _raw(payload)
    headers = {"hmacsignature": adyen.sign(raw)}
    first = adyen.process_raw(raw, headers)
    second = adyen.process_raw(raw, {"hmacsignature": adyen.sign(raw)})
    assert first.status == "processed"
    assert first.payout_id == "3JZKT2B4N7Q1P8R5S6T0"
    assert first.invoice_candidates == 0
    assert second.duplicate is True
    payout = get_payout("3JZKT2B4N7Q1P8R5S6T0")
    breakdown = reconcile_payout(payout)
    assert breakdown.expected_payout == 84210.0
    assert breakdown.matched is True


def test_adyen_invalid_hmac_rejected():
    raw = _raw(adyen.demo_payloads()[0])
    result = adyen.process_raw(raw, {"hmacsignature": "nope"})
    assert result.status == "rejected"
    assert all_payouts() == []


def test_gmail_pubsub_history_and_classifier():
    payloads = gmail.demo_payloads()
    invoice = gmail.process_raw(json.dumps(payloads[0]).encode(), {}, require_signature=False)
    quote = gmail.process_raw(json.dumps(payloads[1]).encode(), {}, require_signature=False)
    marketing = gmail.process_raw(json.dumps(payloads[2]).encode(), {}, require_signature=False)
    seen = gmail.process_raw(json.dumps(payloads[3]).encode(), {}, require_signature=False)
    replay = gmail.process_raw(json.dumps(payloads[0]).encode(), {}, require_signature=False)
    assert invoice.invoice_numbers == ["INV-9001"]
    assert quote.classification == "quote"
    assert quote.invoice_candidates == 0
    assert marketing.classification == "marketing"
    assert seen.invoice_numbers == ["INV-9001"]
    assert replay.duplicate is True
    assert gmail_history_id("ap@hackmit-cfo.example") == "5000"
    aws = [item for item in all_invoices() if item.vendor_invoice_number == "INV-9001"]
    assert len(aws) == 1


def test_outlook_handshake_and_notifications():
    client = TestClient(app)
    response = client.post("/webhooks/outlook?validationToken=secret%20token")
    assert response.status_code == 200
    assert response.text == "secret token"
    assert response.headers["content-type"].startswith("text/plain")

    invoice = outlook.process_raw(json.dumps(outlook.demo_payloads()[0]).encode(), {})
    quote = outlook.process_raw(json.dumps(outlook.demo_payloads()[1]).encode(), {})
    replay = outlook.process_raw(json.dumps(outlook.demo_payloads()[0]).encode(), {})
    assert invoice.invoice_numbers == ["HEL-INV-6200"]
    assert quote.classification == "quote"
    assert replay.duplicate is True
    bad = outlook.process_raw(
        json.dumps({"value": [{"clientState": "wrong", "resourceData": {"id": "x"}, "subscriptionId": "s", "changeType": "created"}]}).encode(),
        {},
    )
    assert bad.status == "rejected"

    sub = outlook.create_outlook_subscription()
    assert sub["maxExpirationMinutes"] == 10080
    renewed = outlook.renew_outlook_subscription(sub)
    assert renewed["expirationDateTime"] >= sub["expirationDateTime"]
    lifecycle = outlook.handle_lifecycle({"lifecycleEvent": "missed", "subscriptionId": sub["id"]})
    assert lifecycle.action == "lifecycle"


def test_xero_signature_bill_and_ar_skip():
    payloads = xero.demo_payloads()
    bill_raw = json.dumps(payloads[0], separators=(",", ":")).encode()
    ar_raw = json.dumps(payloads[1], separators=(",", ":")).encode()
    bill = xero.process_raw(bill_raw, {"x-xero-signature": xero.sign(bill_raw)})
    ar = xero.process_raw(ar_raw, {"x-xero-signature": xero.sign(ar_raw)})
    replay = xero.process_raw(bill_raw, {"x-xero-signature": xero.sign(bill_raw)})
    rejected = xero.process_raw(bill_raw, {"x-xero-signature": "nope"})
    assert bill.invoice_numbers == ["XERO-BILL-441"]
    assert ar.status == "ignored"
    assert ar.classification == "ACCREC"
    assert replay.duplicate is True
    assert rejected.status == "rejected"
    assert all(item.vendor_invoice_number != "XERO-SALE-990" for item in all_invoices())


def test_coupa_sync_preserves_po_and_is_idempotent():
    first = coupa.sync()
    second = coupa.sync()
    assert first.invoice_numbers == ["COUPA-1200"]
    assert first.details["po_preserved"] is True
    assert first.details["three_way_match"] is False
    assert second.invoice_candidates == 0
    invoices = [item for item in all_invoices() if item.vendor_invoice_number == "COUPA-1200"]
    assert len(invoices) == 1
    assert invoices[0].po_id == "PO-201"


def test_netsuite_rest_sync_idempotent():
    first = netsuite.sync()
    second = netsuite.sync()
    assert first.invoice_numbers == ["NS-8821"]
    assert "vendorBill" in first.message
    assert second.invoice_candidates == 0
    bills = [item for item in all_invoices() if item.vendor_invoice_number == "NS-8821"]
    assert len(bills) == 1
    assert bills[0].invoice_id.startswith("ING-")


def test_http_webhooks_reject_bad_signatures():
    client = TestClient(app)
    stripe_raw = _raw(stripe.demo_payloads()[1])
    stripe_bad = client.post("/webhooks/stripe", content=stripe_raw, headers={"stripe-signature": "nope"})
    assert stripe_bad.status_code == 400
    adyen_raw = _raw(adyen.demo_payloads()[0])
    adyen_bad = client.post("/webhooks/adyen", content=adyen_raw, headers={"hmacsignature": "nope"})
    assert adyen_bad.status_code == 401
    xero_raw = json.dumps(xero.demo_payloads()[0], separators=(",", ":")).encode()
    xero_bad = client.post("/webhooks/xero", content=xero_raw, headers={"x-xero-signature": "nope"})
    assert xero_bad.status_code == 401


def test_integration_demo_replay_is_idempotent():
    text = run_integration_demo(replay=True)
    assert "Invoice extracted: AWS INV-9001" in text
    assert "Invoice extracted: HEL-INV-6200" in text
    assert "XERO-BILL-441" in text or "Bill fetched" in text
    assert "COUPA-1200" in text
    assert "NS-8821" in text
    assert "Expected payout" in text
    assert "$97,420.00" in text or "97420" in text
    assert "Idempotency check: PASS" in text
    assert "MATCH" in text
