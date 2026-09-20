"""Demo website API: reads Maximor state and invokes existing workflows."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from demo.reset import reset_demo_runtime
from demo_web.app import create_app
from demo_web.workspace import shutdown_workspace

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


def test_health_and_status(client):
    health = client.get("/api/health").json()
    assert health["ok"] is True
    assert health["bots"] == 15
    assert health["stripe"]["mode"] in {"simulated", "live"}
    status = client.get("/api/demo/status").json()
    assert status["company_id"] == "CO-MAXIMOR"
    assert status["autonomy"]["human_in_completion_path"] is False


def test_overview_uses_real_books(client):
    payload = client.get("/api/demo/overview").json()
    assert payload["header"] == "Autonomous Office of the CFO"
    assert payload["metrics"]["cash"] > 0
    assert payload["metrics"]["ar_outstanding"] > 0
    assert payload["metrics"]["unreconciled_items"] == 12.4
    assert payload["metrics"]["close_status"] == "BLOCKED"
    assert payload["metrics"]["active_bots"] == 15


def test_invoice_register_and_detail(client):
    rows = client.get("/api/invoices").json()["invoices"]
    ids = {item["invoice_id"] for item in rows}
    assert "INV-001" in ids
    assert "INV-006" in ids
    detail = client.get("/api/invoices/INV-001").json()
    assert detail["amount"] == 12450.0
    assert detail["vendor"] == "Acme Supplies"
    assert detail["three_way"]["invoice"]["id"] == "INV-001"
    missing = client.get("/api/invoices/INV-DOES-NOT-EXIST")
    assert missing.status_code == 404


def test_ar_aging_buckets(client):
    payload = client.get("/api/ar").json()
    assert set(payload["buckets"]) == {"CURRENT", "1-30", "31-60", "61-90", "90+"}
    assert payload["outstanding"] > 0


def test_stripe_waterfall_from_kernel(client):
    payload = client.get("/api/stripe").json()
    assert payload["mode"]["mode"] == "simulated"
    assert payload["payouts"]
    first = payload["payouts"][0]["breakdown"]
    assert "gross_payments" in first
    assert "fees" in first
    assert "expected_payout" in first


def test_agents_are_fifteen_grain_bots(client):
    payload = client.get("/api/agents").json()
    slugs = [item["slug"] for item in payload["bots"]]
    assert slugs == [
        "email",
        "stripe",
        "bank",
        "books",
        "ap",
        "pay",
        "apply",
        "collect",
        "cash",
        "close",
        "story",
        "ctl-pay",
        "ctl-cash",
        "ctl-books",
        "audit",
    ]
    assert "Finance Inbox Agent" not in slugs


def test_scenarios_hide_planted_answers(client):
    cards = client.get("/api/scenarios").json()["scenarios"]
    assert len(cards) == 14
    assert all(item.get("planted_issue") in (None, "") for item in cards)
    titles = {item["id"] for item in cards}
    assert "cfo-cycle" in titles
    assert "messy-invoice" in titles
    assert "document-trap" in titles
    assert "self-correction" in titles
    assert "stripe-to-books" in titles


def test_evaluations_hide_expected_before_run(client):
    payload = client.get("/api/evaluations").json()
    assert payload["scored"] in {False, True}
    if not payload["scored"]:
        assert all("expected" not in item for item in payload["catalog"])


def test_reset_preserves_canonical(client):
    before = (CANONICAL / "invoices.json").read_text()
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["canonical_preserved"] is True
    assert (CANONICAL / "invoices.json").read_text() == before


def test_ingest_messy_invoice(client):
    payload = client.post("/api/workflows/invoice-ingestion", json={"sample_id": "MSG-E-MESSY"}).json()
    assert payload["ok"] is True
    assert payload["result"]["classification"] in {"invoice", "quote", "statement", "receipt", "other", "not_an_invoice"}
    assert payload["result"]["sample_id"] == "MSG-E-MESSY"


def test_ingest_quote_is_not_invoice(client):
    payload = client.post("/api/workflows/invoice-ingestion", json={"sample_id": "MSG-E-QUOTE"}).json()
    assert payload["ok"] is True
    assert payload["result"]["classification"] != "invoice"


def test_ap_duplicate_is_held(client):
    payload = client.post("/api/workflows/ap/INV-006").json()
    assert payload["ok"] is True
    assert payload["result"]["decision"]["decision"] == "HOLD"
    assert "duplicate" in payload["result"]["evidence"]["exception_types"]


def test_ap_clean_match_approves(client):
    payload = client.post("/api/workflows/ap", json={"invoice_id": "INV-001"}).json()
    assert payload["ok"] is True
    assert payload["result"]["decision"]["decision"] == "APPROVE"
    assert payload["result"]["evidence"]["exception_types"] == []


def test_ap_idempotent(client):
    first = client.post("/api/workflows/ap/INV-001").json()
    second = client.post("/api/workflows/ap/INV-001").json()
    assert first["ok"] and second["ok"]
    assert first["result"]["decision"]["decision"] == second["result"]["decision"]["decision"]


def test_trace_roundtrip(client):
    payload = client.post("/api/workflows/ap/INV-001").json()
    trace_id = payload["trace_id"]
    loaded = client.get(f"/api/traces/{trace_id}").json()
    assert loaded["trace_id"] == trace_id
    missing = client.get("/api/traces/missing")
    assert missing.status_code == 404


def test_unknown_scenario(client):
    assert client.post("/api/workflows/scenario/not-real").status_code == 404


def test_read_pages_load_persisted_state(client):
    assert client.get("/api/close").json()["status"] == "BLOCKED"
    assert client.get("/api/forecast").json()["weeks"]
    assert client.get("/api/architecture").json()["grain"] == 15
    assert client.get("/api/memory").json()["events"]
    inbox = client.get("/api/inbox").json()
    assert any(item["sample_id"] == "MSG-E-QUOTE" for item in inbox["samples"])


def test_runtime_survives_rebind(tmp_path):
    from demo_web.app import create_app
    from demo_web.workspace import shutdown_workspace
    from demo.reset import reset_demo_runtime

    runtime = tmp_path / "persist"
    reset_demo_runtime(runtime, source=CANONICAL)
    app = create_app(CANONICAL, runtime)
    with TestClient(app) as first:
        created = first.post("/api/workflows/ap/INV-001").json()
        trace_id = created["trace_id"]
        assert first.get(f"/api/traces/{trace_id}").status_code == 200
    shutdown_workspace()
    app2 = create_app(CANONICAL, runtime)
    with TestClient(app2) as second:
        assert second.get(f"/api/traces/{trace_id}").status_code == 200
        assert second.get("/api/invoices/INV-001").json()["amount"] == 12450.0
    shutdown_workspace()


def test_gauntlet_and_lineage_are_judge_readable(client):
    payload = client.get("/api/gauntlet").json()
    assert payload["scored"] is False
    assert payload["catalog"]
    assert all("expected" not in item for item in payload["cases"])
    trap = client.get("/api/stories/trap").json()
    assert "naive" in trap
    assert trap["payable"] is False
    lineage = client.get("/api/lineage/INV-001").json()
    assert "Acme Supplies" in lineage["title"]
    assert lineage["steps"]
    assert lineage["received"]
    scored = client.post("/api/workflows/gauntlet").json()
    assert scored["ok"] is True
    card = scored["result"]["scorecard"]
    assert card["total_scenarios"] >= 20
    after = client.get("/api/gauntlet").json()
    assert after["scored"] is True


def test_duplicate_ap_explains_downstream_prevention(client):
    payload = client.post("/api/workflows/ap/INV-006").json()
    narrative = payload["result"]["explanation"]["narrative"]
    assert "duplicate" in narrative.lower() or "already" in narrative.lower()
    assert payload["result"]["naive"]
    assert payload["result"]["lineage"]["steps"]
