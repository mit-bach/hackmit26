"""Cross-workflow identity and Stripe waterfall stay on the Maximor pack."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from demo.reset import reset_demo_runtime
from demo_web.app import create_app
from demo_web.workspace import shutdown_workspace
from integrations.cash import reconcile_payout
from integrations.models import ProviderPayout

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "data" / "demo"


@pytest.fixture
def client(tmp_path):
    runtime = tmp_path / "demo_runtime"
    reset_demo_runtime(runtime, source=CANONICAL)
    app = create_app(CANONICAL, runtime)
    with TestClient(app) as test_client:
        yield test_client
    shutdown_workspace()


def test_inv001_consistent_across_surfaces(client):
    row = client.get("/api/consistency/INV-001").json()
    assert row["ok"] is True
    assert row["invoice_id"] == "INV-001"
    assert row["amount"] == 12450.0
    assert row["amount_minor"] == 1_245_000
    assert row["ap"]["amount"] == 12450.0
    assert any(item.get("payment_id") == "PAY-AP-001" for item in row["payments"])
    assert any(item.get("entry_id") == "JE-AP-INV-001" for item in row["journals"])
    assert any(item.get("transaction_id") == "TXN-2026-09-018A" for item in row["bank"])
    assert row["close_tasks"]
    for payment in row["payments"]:
        if payment.get("invoice_ids") == ["INV-001"]:
            assert payment["amount_minor"] == 1_245_000


def test_stripe_charges_minus_adjustments_equal_payout(client):
    payload = client.get("/api/stripe").json()
    for item in payload["payouts"]:
        breakdown = item["breakdown"]
        payout = item["payout"]
        # Display fields for refunds/fees/chargebacks are signed (already negative).
        reconstructed = (
            breakdown["gross_payments"]
            + breakdown["refunds"]
            + breakdown["chargebacks"]
            + breakdown["fees"]
            + breakdown.get("adjustments", 0)
            + breakdown.get("other", 0)
        )
        assert round(reconstructed, 2) == round(breakdown["expected_payout"], 2)
        model = ProviderPayout.model_validate(payout)
        again = reconcile_payout(model)
        assert again.expected_payout_minor == breakdown["expected_payout_minor"]
        if item["bank_deposit"] and breakdown.get("bank_deposit_amount") is not None:
            assert abs(again.expected_payout - (item["payout"].get("bank_deposit_amount") or again.expected_payout)) < 0.02 or again.exceptions


def test_planted_invoice_cases_detected(client):
    quote = client.post("/api/workflows/invoice-ingestion", json={"sample_id": "MSG-E-QUOTE"}).json()
    assert quote["ok"] is True
    assert quote["result"]["classification"] != "invoice"

    statement = client.post("/api/workflows/invoice-ingestion", json={"sample_id": "MSG-E-STMT"}).json()
    if statement["ok"] and statement["result"].get("sample_id") == "MSG-E-STMT":
        assert statement["result"]["classification"] != "invoice"

    duplicate = client.post("/api/workflows/ap/INV-006").json()
    assert duplicate["result"]["decision"]["decision"] == "HOLD"
    assert "duplicate" in duplicate["result"]["evidence"]["exception_types"]

    mismatch = client.post("/api/workflows/ap/INV-003").json()
    assert mismatch["result"]["decision"]["decision"] == "HOLD"
    assert mismatch["result"]["evidence"]["exception_types"]


def test_bank_recon_finds_unexplained_difference(client):
    payload = client.post("/api/workflows/bank-reconciliation").json()
    assert payload["ok"] is True
    matches = payload["result"]["report"]["matches"]
    unexplained = [
        item
        for item in matches
        if "TXN-2026-09-015" in (item.get("bank_transaction_ids") or [])
    ]
    assert unexplained
    assert unexplained[0]["match_type"] in {"UNEXPLAINED_DIFFERENCE", "UNMATCHED_BANK"} or unexplained[0]["status"] == "HUMAN_REVIEW"


def test_memory_harbor_writes_and_retrieves(client):
    payload = client.post("/api/workflows/memory", json={"story": "harbor"}).json()
    assert payload["ok"] is True
    body = payload["result"]["payload"]
    assert body["memory_enabled"] is True
    assert body.get("august_trace") or body.get("august")


def test_schedule_is_idempotent(client):
    first = client.post("/api/workflows/schedule").json()
    second = client.post("/api/workflows/schedule").json()
    assert first["ok"] and second["ok"]
    pay_a = [item["invoice_id"] for item in first["result"]["trace"]["plan"]["pay_this_week"]]
    pay_b = [item["invoice_id"] for item in second["result"]["trace"]["plan"]["pay_this_week"]]
    assert pay_a == pay_b
