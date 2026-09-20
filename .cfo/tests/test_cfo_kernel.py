"""Kernel sidecar proofs. Handle completion was not live-proven (no Pi)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cfo_kernel.paths import KERNEL_ROOT, REPO_ROOT, attach_computer, eval_phase
from cfo_kernel.rpc import handle_rpc
from cfo_kernel.seed import default_fixture_dir, default_slug_map, seed_computer

OVERLAY_INVOICE = {
    "invoice_id": "ING-SIDECAR-001",
    "vendor": "Sidecar Overlay Co",
    "po_id": None,
    "amount": 12.0,
    "invoice_date": "2026-09-01",
    "due_date": "2026-09-30",
    "vendor_invoice_number": "SC-001",
    "description": "overlay persist proof",
}

CASH_CASE = {
    "case_id": "CASE-SIDECAR-001",
    "bank": [
        {
            "transaction_id": "TXN-SIDECAR-001",
            "date": "2026-09-15",
            "amount": 100.0,
            "amount_minor": 10000,
            "description": "sidecar persist",
            "period": "2026-09",
        }
    ],
    "ledger": [],
    "fees": [],
    "candidates": [],
}


def _rpc(op: str, *, slug: str, profile: str, bot_id: str, args: dict | None = None, key=None):
    return handle_rpc(
        {
            "op": op,
            "args": args or {},
            "botId": bot_id,
            "slug": slug,
            "profile": profile,
            "handleId": "h_test",
            "idempotencyKey": key,
        }
    )


def _host(op: str, args: dict, key: str):
    return _rpc(
        op,
        slug="_host",
        profile="sidecar",
        bot_id="kernel-host",
        args=args,
        key=key,
    )


@pytest.fixture
def computer(tmp_path):
    dest = seed_computer(
        tmp_path / "computer",
        catalog=default_fixture_dir() / "catalog.json",
        grants=default_fixture_dir() / "grants.json",
        slug_map=default_slug_map(),
    )
    bound = attach_computer(dest)
    yield bound
    from bs_recon.tools import configure_packet_store
    from cash_recon.case_store import configure_case_dir
    from tools import configure_overlay_path

    configure_case_dir(None)
    configure_packet_store(None)
    configure_overlay_path()


def test_eval_phase_defaults_operational(monkeypatch):
    monkeypatch.delenv("CFO_EVAL_PHASE", raising=False)
    assert eval_phase() == "operational"


def test_rpc_read_invoice_against_seeded_data(computer):
    response = _rpc(
        "tools.get_invoice",
        slug="ap",
        profile="prepare",
        bot_id="bot_ap",
        args={"invoice_id": "INV-001"},
    )
    assert response["ok"] is True
    assert response["error"] is None
    assert response["result"]["found"] is True
    assert response["result"]["invoice"]["invoice_id"] == "INV-001"
    assert response["result"]["invoice"]["amount"] == 12450


def test_audit_interpret_cannot_create_accrual(computer):
    from accrual.ledger import ACCRUALS_PATH, load_accruals

    before = ACCRUALS_PATH.read_text() if ACCRUALS_PATH.exists() else ""
    before_ids = {item.accrual_id for item in load_accruals()}
    response = _rpc(
        "accrual.tools.create_accrual",
        slug="audit",
        profile="interpret",
        bot_id="bot_audit",
        args={
            "vendor": "Acme Supplies",
            "period": "2026-09",
            "method": "contract",
            "confidence": 0.9,
            "evidence": ["should-not-write"],
            "reasoning_summary": "forbidden proof",
        },
        key="should-not-matter",
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "forbidden"
    after = ACCRUALS_PATH.read_text() if ACCRUALS_PATH.exists() else ""
    assert after == before
    assert {item.accrual_id for item in load_accruals()} == before_ids


def test_mutating_op_requires_idempotency_key(computer):
    response = _host(
        "kernel.register_runtime_invoice",
        {"invoice": OVERLAY_INVOICE},
        key="",
    )
    assert response["error"]["code"] == "idempotency_required"


def test_same_idempotency_key_different_body_errors(computer):
    first = _host(
        "kernel.register_runtime_invoice",
        {"invoice": OVERLAY_INVOICE},
        key="overlay-key-1",
    )
    assert first["ok"] is True
    changed = dict(OVERLAY_INVOICE)
    changed["amount"] = 99.0
    second = _host(
        "kernel.register_runtime_invoice",
        {"invoice": changed},
        key="overlay-key-1",
    )
    assert second["ok"] is False
    assert second["error"]["code"] == "idempotency_mismatch"


def test_overlay_survives_in_process_reattach(computer):
    registered = _host(
        "kernel.register_runtime_invoice",
        {"invoice": OVERLAY_INVOICE},
        key="overlay-persist-1",
    )
    assert registered["ok"] is True
    overlay = computer.runs / "ingestion" / "overlay.json"
    assert overlay.exists()
    payload = json.loads(overlay.read_text())
    ids = [item["invoice_id"] for item in payload["invoices"]]
    assert "ING-SIDECAR-001" in ids

    attach_computer(computer.root)
    response = _rpc(
        "tools.get_invoice",
        slug="ap",
        profile="prepare",
        bot_id="bot_ap",
        args={"invoice_id": "ING-SIDECAR-001"},
    )
    assert response["ok"] is True
    assert response["result"]["found"] is True
    assert response["result"]["invoice"]["vendor"] == "Sidecar Overlay Co"


def test_cash_case_survives_reattach(computer):
    bound = _host("kernel.bind_cash_case", CASH_CASE, key="cash-case-1")
    assert bound["ok"] is True
    case_path = computer.runs / "cash_recon" / "cases" / "CASE-SIDECAR-001.json"
    assert case_path.exists()

    attach_computer(computer.root)
    response = _rpc(
        "cash_recon.tools.get_bank_transaction",
        slug="cash",
        profile="match",
        bot_id="bot_cash",
        args={"transaction_id": "TXN-SIDECAR-001", "case_id": "CASE-SIDECAR-001"},
    )
    assert response["ok"] is True
    assert response["result"]["transaction_id"] == "TXN-SIDECAR-001"


def test_operational_phase_blocks_answer_keys(computer):
    from audit.store import load_ground_truth
    from evaluation.isolation import AnswerKeyIsolationError, operational_phase_guard

    ground = computer.data / "audit" / "ground_truth.json"
    assert ground.exists()
    with operational_phase_guard():
        with pytest.raises(AnswerKeyIsolationError):
            load_ground_truth()

    response = _rpc(
        "audit.tools.get_audit_ground_truth",
        slug="audit",
        profile="interpret",
        bot_id="bot_audit",
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "forbidden"


def test_eval_only_op_forbidden_even_if_listed(computer, tmp_path):
    grants = json.loads((default_fixture_dir() / "grants.json").read_text())
    grants["byDisplayName"]["Auditor Agent"]["ops"].append(
        "audit.tools.get_audit_ground_truth"
    )
    patched = tmp_path / "grants-eval.json"
    patched.write_text(json.dumps(grants, indent=2) + "\n")
    dest = seed_computer(
        tmp_path / "eval-computer",
        catalog=default_fixture_dir() / "catalog.json",
        grants=patched,
        slug_map=default_slug_map(),
    )
    attach_computer(dest)
    response = _rpc(
        "audit.tools.get_audit_ground_truth",
        slug="audit",
        profile="interpret",
        bot_id="bot_audit",
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "forbidden"
    assert "get_audit_ground_truth" in response["error"]["message"]


def test_lock_op_name_is_month_end_not_test_packet():
    from cfo_kernel import LOCK_OP, TEST_PACKET_OP

    assert LOCK_OP == "close.month_end.run_month_end"
    assert TEST_PACKET_OP == "close.orchestrator.run_cfo_close"
    assert LOCK_OP != TEST_PACKET_OP


def test_sidecar_health_is_not_a_bot(computer):
    response = handle_rpc(
        {
            "op": "kernel.health",
            "args": {},
            "botId": "kernel-host",
            "slug": "_host",
            "profile": "sidecar",
            "handleId": "",
            "idempotencyKey": None,
        }
    )
    assert response["ok"] is True
    assert response["result"]["sidecar"] is True
    assert response["result"]["bot"] is False
    assert response["result"]["bindsHarnessBot"] is False
    assert response["result"]["drainsInboxes"] is False
    assert response["result"]["lockOp"] == "close.month_end.run_month_end"


def test_kill_and_restart_sidecar_keeps_overlay(computer):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(KERNEL_ROOT)
    env["CFO_EVAL_PHASE"] = "operational"
    env["HARNESS_COMPUTER"] = str(computer.root)
    env.pop("HARNESS_BOT", None)

    def _start() -> subprocess.Popen:
        return subprocess.Popen(
            [sys.executable, "-m", "cfo_kernel", "--computer", str(computer.root), "--port", "0"],
            cwd=str(KERNEL_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _wait_port(proc: subprocess.Popen) -> int:
        deadline = time.time() + 20
        while time.time() < deadline:
            if computer.port_path.exists():
                payload = json.loads(computer.port_path.read_text())
                return int(payload["port"])
            if proc.poll() is not None:
                err = proc.stderr.read().decode() if proc.stderr else ""
                raise RuntimeError(f"sidecar exited {proc.returncode}: {err}")
            time.sleep(0.05)
        raise TimeoutError("sidecar did not write cfo/kernel.port")

    import urllib.request

    first = _start()
    try:
        port = _wait_port(first)
        body = json.dumps(
            {
                "op": "kernel.register_runtime_invoice",
                "args": {"invoice": OVERLAY_INVOICE},
                "botId": "kernel-host",
                "slug": "_host",
                "profile": "sidecar",
                "handleId": "h_restart",
                "idempotencyKey": "overlay-restart-1",
            }
        ).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/rpc",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as reply:
            payload = json.loads(reply.read().decode())
        assert payload["ok"] is True
    finally:
        first.terminate()
        try:
            first.wait(timeout=5)
        except subprocess.TimeoutExpired:
            first.kill()
            first.wait(timeout=5)

    if computer.port_path.exists():
        computer.port_path.unlink()

    second = _start()
    try:
        port = _wait_port(second)
        body = json.dumps(
            {
                "op": "tools.get_invoice",
                "args": {"invoice_id": "ING-SIDECAR-001"},
                "botId": "bot_ap",
                "slug": "ap",
                "profile": "prepare",
                "handleId": "h_restart_read",
                "idempotencyKey": None,
            }
        ).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/rpc",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as reply:
            payload = json.loads(reply.read().decode())
        assert payload["ok"] is True
        assert payload["result"]["found"] is True
        assert payload["result"]["invoice"]["invoice_id"] == "ING-SIDECAR-001"
    finally:
        second.terminate()
        try:
            second.wait(timeout=5)
        except subprocess.TimeoutExpired:
            second.kill()
            second.wait(timeout=5)


def test_empty_catalog_fail_closed(tmp_path):
    empty_cfo = tmp_path / "empty"
    empty_cfo.mkdir()
    (empty_cfo / "catalog.json").write_text('{"version": "1", "ops": []}\n')
    (empty_cfo / "grants.json").write_text('{"version": "1", "byDisplayName": {}}\n')
    dest = seed_computer(
        tmp_path / "empty-computer",
        catalog=empty_cfo / "catalog.json",
        grants=empty_cfo / "grants.json",
        slug_map=default_slug_map(),
    )
    attach_computer(dest)
    response = _rpc(
        "tools.get_invoice",
        slug="ap",
        profile="prepare",
        bot_id="bot_ap",
        args={"invoice_id": "INV-001"},
    )
    assert response["ok"] is False
    assert response["error"]["code"] in {"forbidden", "unknown_op"}


def test_compiled_live_grants_allow_prepare_read(tmp_path):
    """Session 01 compiler output on the live Computer is the Grant SoT."""
    live = REPO_ROOT / ".cfo-v2" / "office" / "computer"
    grants = live / "cfo" / "grants.json"
    catalog = live / "cfo" / "catalog.json"
    if not grants.exists() or not catalog.exists():
        pytest.skip("live computer catalog/grants missing")
    payload = json.loads(grants.read_text())
    by_name = payload.get("byDisplayName") or payload.get("agents") or {}
    preparer = by_name.get("AP Preparer") or {}
    if "tools.get_invoice" not in (preparer.get("ops") or []):
        pytest.skip("session 01 has not granted tools.get_invoice to AP Preparer")
    dest = seed_computer(
        tmp_path / "live-shape",
        catalog=catalog,
        grants=grants,
        slug_map=live / "cfo" / "slug-map.json",
    )
    attach_computer(dest)
    response = _rpc(
        "tools.get_invoice",
        slug="ap",
        profile="prepare",
        bot_id="bot_ap",
        args={"invoice_id": "INV-001"},
    )
    assert response["ok"] is True
    assert response["result"]["found"] is True
    forbidden = _rpc(
        "accrual.tools.create_accrual",
        slug="audit",
        profile="interpret",
        bot_id="bot_audit",
        args={"vendor": "x", "period": "2026-09", "method": "contract", "confidence": 0.1, "evidence": [], "reasoning_summary": "no"},
        key="live-forbid",
    )
    assert forbidden["ok"] is False
    assert forbidden["error"]["code"] == "forbidden"
