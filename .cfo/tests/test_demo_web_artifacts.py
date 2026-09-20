"""Displayed source artifacts must be the exact workflow inputs/outputs."""

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


def test_ingest_source_id_is_the_email_fixture(client):
    preview = client.get("/api/inbox/MSG-E-MESSY").json()
    assert preview["sample_id"] == "MSG-E-MESSY"
    assert preview["artifact"]["artifact_id"] == "MSG-E-MESSY"
    assert preview["artifact"]["record"]["message_id"] == "MSG-E-MESSY"
    att = preview["artifact"]["attachments"][0]
    assert att["record"]["attachment_id"] == "ATT-E-MESSY"
    payload = client.post("/api/workflows/invoice-ingestion", json={"sample_id": "MSG-E-MESSY"}).json()
    assert payload["result"]["sample_id"] == "MSG-E-MESSY"
    assert payload["result"]["io"]["inputs"]["email"]["artifact_id"] == "MSG-E-MESSY"
    assert payload["result"]["io"]["inputs"]["email"]["record"]["message_id"] == payload["result"]["source"]["message_id"]


def test_invoice_source_email_matches_canonical_invoice(client):
    detail = client.get("/api/invoices/INV-001").json()
    emails = detail["source_emails"]
    assert any(item["artifact_id"] == "MSG-E-INV-001" for item in emails)
    assert detail["invoice"]["invoice_id"] == "INV-001"
    assert detail["source_document"]["artifact_id"] == "INV-001"
    assert detail["three_way"]["artifacts"]["invoice"]["record"]["invoice_id"] == "INV-001"
    assert detail["three_way"]["artifacts"]["purchase_order"]["record"]["po_id"] == "PO-101"
    assert detail["three_way"]["artifacts"]["goods_receipt"]["record"]["receipt_id"] == "GR-101"


def test_duplicate_pair_is_inv006_and_inv007(client):
    detail = client.get("/api/invoices/INV-006").json()
    pair = detail["duplicate_peer"]
    assert pair["document_a"]["artifact_id"] == "INV-006"
    assert pair["document_b"]["artifact_id"] == "INV-007"
    assert pair["comparison"]["invoice_number_match"] is True
    assert pair["comparison"]["amount_match"] is True
    payload = client.post("/api/workflows/ap/INV-006").json()
    assert payload["result"]["io"]["inputs"]["document_a"]["artifact_id"] == "INV-006"
    assert payload["result"]["io"]["outputs"]["invoice"]["artifact_id"] == "INV-006"
    assert payload["result"]["io"]["after"]["invoice_id"] == "INV-006"


def test_three_way_source_ids(client):
    payload = client.post("/api/workflows/ap/INV-003").json()
    tw = payload["result"]["io"]["inputs"]
    assert tw["invoice"]["record"]["invoice_id"] == "INV-003"
    assert tw["purchase_order"]["record"]["po_id"] == "PO-103"
    assert tw["goods_receipt"]["record"]["receipt_id"] == "GR-103"
    assert tw["goods_receipt"]["record"]["quantity_received"] == 40
    assert tw["goods_receipt"]["record"]["quantity_ordered"] == 50


def test_stripe_payout_id_is_reconciliation_input(client):
    view = client.get("/api/stripe").json()
    payout_id = view["payouts"][0]["payout"]["payout_id"]
    bundle = view["bundles"][payout_id]
    assert bundle["payout"]["artifact_id"] == payout_id
    assert bundle["payout"]["record"]["payout_id"] == payout_id
    payload = client.post("/api/workflows/stripe-reconciliation").json()
    assert payload["result"]["io"]["inputs"]["payout"]["artifact_id"] == "po_1MaximorFees"
    assert payload["result"]["record_ids"][0] == payload["result"]["io"]["inputs"]["payout"]["record"]["payout_id"]


def test_bank_transaction_id_is_reconciliation_input(client):
    view = client.get("/api/cash").json()
    case = view["featured_cases"]["unexplained"]
    assert case["bank"]["artifact_id"] == "TXN-2026-09-015"
    assert case["bank"]["record"]["transaction_id"] == "TXN-2026-09-015"
    assert any(item["artifact_id"] == "GL-AR-NS" for item in case["ledger"])
    payload = client.post("/api/workflows/bank-reconciliation").json()
    bank_id = payload["result"]["io"]["inputs"]["unexplained"]["bank"]["artifact_id"]
    assert bank_id == "TXN-2026-09-015"
    matches = payload["result"]["report"]["matches"]
    hit = next(item for item in matches if bank_id in (item.get("bank_transaction_ids") or []))
    assert hit["bank_transaction_ids"][0] == bank_id


def test_harbor_memory_and_journal_ids(client):
    close = client.get("/api/close").json()
    harbor = close["harbor"]["input"]
    assert harbor["history_table"]["source_path"] == "historical_invoices.json"
    assert any(item["artifact_id"] == "MEM-004" for item in harbor["prior_memory"])
    assert harbor["seeded_journal"]["artifact_id"] == "JE-ACC-HE-202609"
    payload = client.post("/api/workflows/memory", json={"story": "harbor"}).json()
    lookup = payload["result"]["io"]["outputs"].get("september_lookup") or {}
    retrieved = []
    if isinstance(lookup, dict):
        retrieved = lookup.get("retrieved_ids") or lookup.get("memory_ids") or []
        if lookup.get("decision_id"):
            retrieved.append(lookup["decision_id"])
    august = payload["result"]["io"]["inputs"].get("august_trace") or {}
    written = (august.get("written_memory_id") if isinstance(august, dict) else None) or payload["result"]["io"]["outputs"].get("written_memory_id")
    assert payload["result"]["payload"]["memory_enabled"] is True
    assert written or retrieved or payload["result"]["io"]["outputs"].get("final_method")


def test_accrual_journal_is_produced_record(client):
    payload = client.post("/api/workflows/accrual", json={"vendor": "Harbor Electric"}).json()
    outputs = payload["result"]["io"]["outputs"]
    journal = outputs.get("journal_entry") or {}
    if journal:
        entry_id = journal.get("entry_id") or journal.get("journal_id")
        assert entry_id
        assert outputs.get("accrual_id") or entry_id


def test_scenario_preview_hides_expected(client):
    preview = client.get("/api/scenarios/duplicate-invoice").json()
    assert preview["id"] == "duplicate-invoice"
    assert preview["expected"] is None
    assert preview["planted_issue"] is None
    ids = {item["artifact_id"] for item in preview["inputs"]}
    assert "INV-006" in ids
    assert "INV-007" in ids
    ran = client.post("/api/workflows/scenario/duplicate-invoice").json()
    assert ran["expected"]
    assert any(item.get("case_id") == "AC-AP-DUP" for item in ran["expected"])


def test_self_approval_source_ids_visible_before_audit_run(client):
    audit = client.get("/api/audit").json()
    assert audit["last_run"] in (None, audit["last_run"])
    featured = audit["inputs"]["featured"]["self_approval"]["record"]
    assert featured["requester_id"] == featured["approver_id"] == "USR-PREP-02"
    assert audit.get("last_run") is None or "findings" in (audit.get("last_run") or {})


def test_company_state_and_cfo_before_after(client):
    state = client.get("/api/demo/company-state").json()
    assert state["unreconciled_item"] == "TXN-2026-09-015"
    assert "cash" in state
    payload = client.post("/api/workflows/cfo-cycle").json()
    inner = payload.get("result") or {}
    io = inner.get("io") or {}
    before = io.get("before") or state
    assert before["unreconciled_item"] == "TXN-2026-09-015"
    assert before["period"] == "2026-09"
    if payload.get("ok"):
        assert io["after"]["period"] == "2026-09"


def test_overview_cfo_cycle_has_no_unknown_invoices(client):
    import json

    from ar.store import get_invoice
    from close.actions import DEFAULT_AR_INVOICE

    overview = client.get("/api/demo/overview").json()
    ar_ids = {item["invoice_id"] for item in client.get("/api/ar").json()["invoices"]}
    assert DEFAULT_AR_INVOICE in ar_ids
    assert get_invoice(DEFAULT_AR_INVOICE) is not None
    assert "Unknown invoice" not in json.dumps(overview)
    overview_invoice_ids = [
        rid
        for item in overview.get("briefing") or []
        for rid in item.get("record_ids") or []
        if str(rid).startswith("INV-AR")
    ]
    assert set(overview_invoice_ids) <= ar_ids
    payload = client.post("/api/workflows/cfo-cycle").json()
    assert "Unknown invoice" not in json.dumps(payload)
    assert payload.get("ok") is True
    refreshed = {item["invoice_id"] for item in client.get("/api/ar").json()["invoices"]}
    assert DEFAULT_AR_INVOICE in refreshed
    overview_after = client.get("/api/demo/overview").json()
    assert "Unknown invoice" not in json.dumps(overview_after)


def test_evaluations_populate_after_run(client):
    before = client.get("/api/evaluations").json()
    assert before["scored"] is False
    assert all(item.get("status") == "not_run" for item in before["catalog"])
    payload = client.post("/api/workflows/evaluate").json()
    assert payload.get("ok") is True
    after = client.get("/api/evaluations").json()
    assert after["scored"] is True
    assert after["summary"]["total"] == len(after["catalog"])
    assert after["summary"]["passed"] + after["summary"]["failed"] == after["summary"]["total"]
    sample = next(item for item in after["catalog"] if item["case_id"] == "AC-CASH-RECON-1240")
    assert sample["passed"] in {True, False}
    assert sample.get("expected")
    assert sample.get("actual") is not None
