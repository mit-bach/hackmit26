from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from integrations.cash import reconcile_payout
from integrations.models import PayoutLine, ProviderPayout
from integrations.providers import stripe
from integrations.server import app
from integrations.store import all_events, all_payouts, all_reconciliations, get_payout, set_bank_deposit
from tools import all_invoices


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _headers(raw: bytes) -> dict[str, str]:
    return {"stripe-signature": stripe.sign(raw)}


def _line(line_type: str, amount_minor: int, **kwargs) -> PayoutLine:
    currency = kwargs.pop("currency", "USD")
    return PayoutLine(
        line_type=line_type,
        amount=amount_minor / 100.0,
        currency=currency,
        amount_minor=amount_minor,
        description=kwargs.pop("description", line_type),
        provider_object_id=kwargs.pop("provider_object_id", f"txn_{line_type}"),
        **kwargs,
    )


def _payout(lines: list[PayoutLine], *, amount: int = 9742000, bank: float | None = 97420.0, currency: str = "USD") -> ProviderPayout:
    return ProviderPayout(
        provider="stripe",
        event_id="evt_math",
        payout_id="po_math",
        status="paid",
        amount=amount,
        currency=currency,
        source_event_type="payout.reconciliation_completed",
        raw_source_ref="stripe:evt_math",
        lines=lines,
        bank_deposit_id="BANK-1" if bank is not None else None,
        bank_deposit_amount=bank,
        bank_deposit_currency=currency if bank is not None else None,
    )


def _live_payout_obj(payout_id: str = "po_live_1", amount: int = 4950) -> dict:
    return {
        "id": payout_id,
        "object": "payout",
        "amount": amount,
        "currency": "usd",
        "status": "paid",
        "created": 1758153600,
        "arrival_date": 1758240000,
        "statement_descriptor": "STRIPE PAYOUT",
    }


def _live_txn(txn_id: str, amount: int, txn_type: str, **extra) -> dict:
    row = {
        "id": txn_id,
        "object": "balance_transaction",
        "amount": amount,
        "currency": "usd",
        "type": txn_type,
        "fee": extra.get("fee", 0),
        "net": extra.get("net", amount),
        "created": 1758153600,
        "description": extra.get("description", txn_type),
        "source": extra.get("source", txn_id.replace("txn", "ch")),
        "payout": extra.get("payout", "po_live_1"),
    }
    return row


class FakeList:
    def __init__(self, data, has_more=False):
        self.data = data
        self.has_more = has_more


def test_missing_signature_rejected():
    raw = _raw(stripe.demo_payloads()[1])
    result = stripe.process_raw(raw, {})
    assert result.status == "rejected"
    assert "missing" in result.message.lower()
    assert all_payouts() == []
    assert all_reconciliations() == []


def test_signature_uses_raw_body_not_reserialized_json():
    payload = stripe.demo_payloads()[1]
    raw = _raw(payload)
    pretty = json.dumps(payload, indent=2).encode("utf-8")
    result = stripe.process_raw(pretty, {"stripe-signature": stripe.sign(raw)})
    assert result.status == "rejected"
    assert all_payouts() == []

    captured = {}
    import stripe as stripe_sdk

    real_construct = stripe_sdk.Webhook.construct_event

    def spy(payload, sig_header, secret, **kwargs):
        captured["payload"] = payload
        captured["type"] = type(payload)
        return real_construct(payload=payload, sig_header=sig_header, secret=secret, **kwargs)

    with patch("stripe.Webhook.construct_event", side_effect=spy):
        ok = stripe.process_raw(raw, _headers(raw))
    assert ok.status == "processed"
    assert isinstance(captured["payload"], (bytes, bytearray))
    assert captured["payload"] == raw


def test_http_missing_and_invalid_signature_leave_no_payout():
    client = TestClient(app)
    raw = _raw(stripe.demo_payloads()[1])
    missing = client.post("/webhooks/stripe", content=raw)
    assert missing.status_code == 400
    bad = client.post("/webhooks/stripe", content=raw, headers={"stripe-signature": "t=1,v1=nope"})
    assert bad.status_code == 400
    assert all_payouts() == []
    assert all_events() == []


def test_http_valid_signature_accepted():
    client = TestClient(app)
    raw = _raw(stripe.demo_payloads()[1])
    response = client.post("/webhooks/stripe", content=raw, headers=_headers(raw))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["payout_id"] == "po_1HackMIT97420"


def test_unrelated_event_ignored():
    payload = {
        "id": "evt_pi_created",
        "object": "event",
        "type": "payment_intent.created",
        "created": 1758153600,
        "data": {"object": {"id": "pi_123", "object": "payment_intent"}},
    }
    raw = _raw(payload)
    result = stripe.process_raw(raw, _headers(raw))
    assert result.status == "ignored"
    assert result.payout_id is None
    assert all_payouts() == []
    assert all_reconciliations() == []
    assert all(item.invoice_id != "pi_123" for item in all_invoices())


def test_malformed_event_rejected_safely():
    result = stripe.process_raw(b"not-json", {}, require_signature=False)
    assert result.status == "rejected"
    assert all_payouts() == []

    raw = b'{"id":"evt_x","type":"payout.paid"}'
    signed = stripe.process_raw(raw, _headers(raw), require_signature=False)
    assert signed.status == "error"
    assert "missing" in signed.message.lower()
    assert all_payouts() == []


def test_relevant_payout_event_processed():
    raw = _raw(stripe.demo_payloads()[1])
    result = stripe.process_raw(raw, _headers(raw))
    assert result.status == "processed"
    assert result.details["status"] == "MATCH"
    assert get_payout("po_1HackMIT97420") is not None


def test_same_payout_different_events_one_canonical_record():
    for payload in stripe.demo_payloads():
        raw = _raw(payload)
        stripe.process_raw(raw, _headers(raw))
    assert len([item for item in all_payouts() if item.provider == "stripe"]) == 1
    assert len(all_reconciliations()) == 1
    assert len(all_events()) == 2
    assert {item.event_type for item in all_events()} == {"payout.created", "payout.reconciliation_completed"}


def test_manual_sync_after_webhook_does_not_duplicate():
    for payload in stripe.demo_payloads():
        raw = _raw(payload)
        stripe.process_raw(raw, _headers(raw))
    result = stripe.sync(provider=stripe.MockStripeProvider())
    assert result.status == "processed"
    assert result.details["new_payouts"] == 0
    assert result.details["new_reconciliations"] == 0
    assert len([item for item in all_payouts() if item.provider == "stripe"]) == 1
    assert len(all_reconciliations()) == 1


def test_webhook_after_manual_sync_does_not_duplicate():
    stripe.sync(provider=stripe.MockStripeProvider())
    assert len(all_payouts()) == 1
    for payload in stripe.demo_payloads():
        raw = _raw(payload)
        result = stripe.process_raw(raw, _headers(raw), provider=stripe.MockStripeProvider())
        assert result.duplicate or result.details.get("new_reconciliation") is False
    assert len([item for item in all_payouts() if item.provider == "stripe"]) == 1
    assert len(all_reconciliations()) == 1


def test_live_mode_without_credentials_fails_cleanly(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "live")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    result = stripe.sync()
    assert result.status == "error"
    assert "STRIPE_SECRET_KEY" in result.message
    assert all_payouts() == []
    text = stripe.connection_status()
    assert "mode: live" in text
    assert "secret key: missing" in text
    assert "sk_" not in text


def test_mock_mode_status_needs_no_credentials():
    text = stripe.connection_status()
    assert text == "Stripe\n  mode: mock"


def test_status_never_prints_secrets(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "live")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_DO_NOT_PRINT")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_DO_NOT_PRINT")
    with patch("stripe.Balance.retrieve", return_value={"object": "balance"}):
        text = stripe.connection_status()
    assert "sk_test_DO_NOT_PRINT" not in text
    assert "whsec_DO_NOT_PRINT" not in text
    assert "secret key: configured" in text
    assert "webhook secret: configured" in text
    assert "API connection: OK" in text


def test_live_fetch_payout_and_paginated_transactions(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "live")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_hackmit")
    payout_obj = _live_payout_obj(amount=4950)
    pages = {
        None: FakeList(
            [_live_txn("txn_a", 3000, "charge"), _live_txn("txn_b", 2000, "charge")],
            has_more=True,
        ),
        "txn_b": FakeList(
            [_live_txn("txn_fee", -50, "stripe_fee")],
            has_more=False,
        ),
    }

    def fake_list(**kwargs):
        return pages[kwargs.get("starting_after")]

    with patch("stripe.Payout.retrieve", return_value=payout_obj), patch(
        "stripe.BalanceTransaction.list", side_effect=fake_list
    ):
        payload = {
            "id": "evt_live_recon",
            "type": "payout.reconciliation_completed",
            "created": 1758240000,
            "data": {"object": {"id": "po_live_1"}},
        }
        raw = _raw(payload)
        result = stripe.process_raw(raw, _headers(raw), provider=stripe.LiveStripeProvider())
    assert result.status == "processed"
    payout = get_payout("po_live_1")
    assert payout is not None
    assert [line.provider_object_id for line in payout.lines] == ["txn_a", "txn_b", "txn_fee"]
    assert payout.bank_deposit_amount is None
    breakdown = reconcile_payout(payout)
    assert breakdown.status == "AWAITING_BANK"
    assert breakdown.gross_payments == 50.0
    assert breakdown.fees == -0.50
    assert breakdown.expected_payout == 49.50
    assert breakdown.actual_payout == 49.50
    assert all(item.invoice_id != "po_live_1" for item in all_invoices())


def test_live_api_failure_is_traced(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "live")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_hackmit")
    with patch("stripe.Payout.retrieve", side_effect=RuntimeError("boom")):
        payload = {
            "id": "evt_live_fail",
            "type": "payout.reconciliation_completed",
            "created": 1,
            "data": {"object": {"id": "po_missing"}},
        }
        raw = _raw(payload)
        result = stripe.process_raw(raw, _headers(raw), provider=stripe.LiveStripeProvider())
    assert result.status == "error"
    assert "stripe_api_failure" in result.details["exceptions"]
    assert get_payout("po_missing") is None
    events = [item for item in all_events() if item.provider_event_id == "evt_live_fail"]
    assert events and events[0].processing_status == "error"


def test_live_bank_mismatch_exception(monkeypatch):
    monkeypatch.setenv("STRIPE_MODE", "live")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_hackmit")
    payout_obj = _live_payout_obj(amount=9742000)
    txns = FakeList(
        [
            _live_txn("txn_1", 10200000, "charge", payout="po_live_1"),
            _live_txn("txn_2", -150000, "refund", payout="po_live_1"),
            _live_txn("txn_3", -100000, "adjustment", description="Chargeback ORD", payout="po_live_1"),
            _live_txn("txn_4", -208000, "stripe_fee", payout="po_live_1"),
        ]
    )

    def fake_list(**kwargs):
        if hasattr(txns, "auto_paging_iter"):
            return txns
        return txns

    with patch("stripe.Payout.retrieve", return_value=payout_obj), patch(
        "stripe.BalanceTransaction.list", side_effect=fake_list
    ):
        set_bank_deposit("po_live_1", amount=97407.60, deposit_id="BANK-DIFF", currency="USD")
        payload = {
            "id": "evt_mismatch",
            "type": "payout.reconciliation_completed",
            "created": 1,
            "data": {"object": {"id": "po_live_1"}},
        }
        raw = _raw(payload)
        result = stripe.process_raw(raw, _headers(raw), provider=stripe.LiveStripeProvider())
    assert result.status == "processed"
    breakdown = all_reconciliations()[0]
    assert breakdown.status == "MISMATCH"
    assert "bank_amount_differs_from_stripe_payout" in breakdown.exceptions
    assert breakdown.bank_deposit_amount == 97407.60
    assert breakdown.actual_payout == 97420.0
    assert breakdown.expected_payout == 97420.0


def test_reconciliation_math_normal_payout():
    lines = [
        _line("charge", 2500000),
        _line("charge", 3100000),
        _line("charge", 2800000),
        _line("charge", 1800000),
        _line("refund", -150000),
        _line("adjustment", -100000, description="Chargeback ORD-1003"),
        _line("stripe_fee", -208000),
    ]
    row = reconcile_payout(_payout(lines, amount=9742000, bank=97420.0))
    assert row.gross_payments == 102000.0
    assert row.refunds == -1500.0
    assert row.chargebacks == -1000.0
    assert row.fees == -2080.0
    assert row.expected_payout == 97420.0
    assert row.status == "MATCH"
    assert row.expected_payout_minor == 9742000


def test_reconciliation_math_components():
    refund = reconcile_payout(_payout([_line("charge", 10000), _line("refund", -2000)], amount=8000, bank=80.0))
    assert refund.refunds == -20.0
    assert refund.status == "MATCH"

    chargeback = reconcile_payout(_payout([_line("charge", 10000), _line("dispute", -3000)], amount=7000, bank=70.0))
    assert chargeback.chargebacks == -30.0
    assert chargeback.status == "MATCH"

    fee = reconcile_payout(_payout([_line("charge", 10000), _line("stripe_fee", -250)], amount=9750, bank=97.50))
    assert fee.fees == -2.50
    assert fee.status == "MATCH"

    adjustment = reconcile_payout(
        _payout([_line("charge", 10000), _line("adjustment", 500, description="volume bonus")], amount=10500, bank=105.0)
    )
    assert adjustment.adjustments == 5.0
    assert adjustment.status == "MATCH"

    unknown = reconcile_payout(
        _payout([_line("charge", 10000), _line("climate_order_purchase", -100)], amount=9900, bank=99.0)
    )
    assert unknown.other == -1.0
    assert unknown.status == "NEEDS_REVIEW"
    assert any(item.startswith("unknown_balance_transaction_type:") for item in unknown.exceptions)

    multi = reconcile_payout(
        _payout([_line("charge", 4000), _line("charge", 6000), _line("payment", 2000)], amount=12000, bank=120.0)
    )
    assert multi.gross_payments == 120.0
    assert multi.status == "MATCH"


def test_reconciliation_currency_and_bank_states():
    mismatch_ccy = reconcile_payout(
        _payout([_line("charge", 10000, currency="EUR")], amount=10000, bank=100.0, currency="USD")
    )
    assert mismatch_ccy.status == "NEEDS_REVIEW"
    assert any("currency_mismatch" in item for item in mismatch_ccy.exceptions)

    awaiting = reconcile_payout(_payout([_line("charge", 10000)], amount=10000, bank=None))
    assert awaiting.status == "AWAITING_BANK"
    assert awaiting.bank_deposit_amount is None

    matched = reconcile_payout(_payout([_line("charge", 10000)], amount=10000, bank=100.0))
    assert matched.status == "MATCH"

    bank_diff = reconcile_payout(_payout([_line("charge", 10000)], amount=10000, bank=99.87))
    assert bank_diff.status == "MISMATCH"
    assert "bank_amount_differs_from_stripe_payout" in bank_diff.exceptions

    net_diff = reconcile_payout(_payout([_line("charge", 10000)], amount=9000, bank=90.0))
    assert net_diff.status == "MISMATCH"
    assert "payout_amount_does_not_equal_normalized_transaction_net" in net_diff.exceptions


def test_stripe_demo_computes_fixture_values():
    text = stripe.run_stripe_demo()
    assert "Payout: po_1HackMIT97420" in text
    assert "$102,000.00" in text
    assert "$1,500.00" in text
    assert "$1,000.00" in text
    assert "$2,080.00" in text
    assert "$97,420.00" in text
    assert "Status: MATCH" in text
    assert "New payout records: 0" in text
    assert "New reconciliations: 0" in text
    assert "Idempotency: PASS" in text
    assert all(item.invoice_id != "po_1HackMIT97420" for item in all_invoices())


def test_mock_sync_specific_payout():
    result = stripe.sync(payout_id="po_1HackMIT97420", provider=stripe.MockStripeProvider())
    assert result.status == "processed"
    assert result.payout_id == "po_1HackMIT97420"
    replay = stripe.sync(payout_id="po_1HackMIT97420", provider=stripe.MockStripeProvider())
    assert replay.details["new_payouts"] == 0
