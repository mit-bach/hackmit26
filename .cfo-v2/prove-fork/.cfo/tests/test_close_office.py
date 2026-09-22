"""Period-pass proofs: Computer runs path, $12.40 BLOCKED, lock door, Grants."""

from __future__ import annotations

import json
from pathlib import Path

from close.gating import evaluate_close_gates
from close.host import run_close_host
from close.month_end import load_state
from close.orchestrator import run_cfo_close
from close.period_lock import is_period_closed
from close.profile_grants import LOCK_DOOR, TEST_PACKET
from close.tools import _gate_payload, _packet_payload
from verifier.concurrence import apply_ctl_books_lock

REPO = Path(__file__).resolve().parents[2]
GRANTS = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.json"
GRANTS_EVAL = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.eval.json"


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def test_harness_computer_close_writes_computer_runs(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    computer = tmp_path / "computer"
    monkeypatch.setenv("HARNESS_COMPUTER", str(computer))
    runs = computer / "runs" / "month_end"
    result = run_close_host(
        period="2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=computer,
        state_dir=runs,
    )
    assert result["lock_door"] == LOCK_DOOR
    assert result["test_packet"] == TEST_PACKET
    assert result["marked_closed"] is False
    assert (computer / "runs" / "month_end").exists()
    assert (computer / result["pack_path"]).is_file()
    assert (computer / "workspace" / "close" / "2026-09" / "pack.json").is_file()
    assert (runs / "prepaids.json").is_file() or (runs / "2026-09.json").is_file()
    kernel_runs = REPO / ".cfo" / "runs" / "month_end"
    assert result["runs_dir"] == str(runs)
    assert Path(result["runs_dir"]) != kernel_runs
    assert is_period_closed("2026-09") is False
    assert not str(runs).startswith(str(kernel_runs))


def test_evaluate_close_gates_blocked_on_1240_and_lock_refuses(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    computer = tmp_path / "computer"
    result = run_close_host(
        period="2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=computer,
        state_dir=tmp_path / "month_end",
    )
    state = load_state("2026-09")
    assert state is not None
    gate = evaluate_close_gates(state)
    assert gate.passed is False
    details = " ".join(result.blocked_on)
    assert "12.40" in details or "12.4" in details
    locked = apply_ctl_books_lock("2026-09", bot_decision="CONCUR")
    assert locked["decision"] == "REFUSE"
    assert locked["gate_passed"] is False
    assert locked["closed"] is False
    assert load_state("2026-09").period.status != "CLOSED"
    facts = _gate_payload("2026-09")
    assert facts["passed"] is False
    assert facts["can_mark_closed"] is False
    assert facts["lock_door"] == LOCK_DOOR
    packet = _packet_payload("2026-09")
    assert packet["can_mark_closed"] is False
    assert packet["queue_owner"] == "ctl-books"


def test_run_cfo_close_test_packet_does_not_lock(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("close.orchestrator.CLOSE_DIR", tmp_path / "close")
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")
    run_cfo_close("2026-09", live=False, featured_ap=(), use_agent_accrual=False)
    assert is_period_closed("2026-09") is False


def test_operational_grants_omit_audit_ground_truth():
    text = GRANTS.read_text(encoding="utf-8")
    assert "get_audit_ground_truth" not in text
    grants = json.loads(text)
    lock = grants["byDisplayName"]["Month-End Close Reviewer"]["ops"]
    assert "accrual.tools.create_accrual" not in lock
    assert "close.tools.get_close_gates" in lock
    assert "close.tools.get_close_packet" in lock
    assert grants["byDisplayName"]["Close Manager"]["ops"] == []
    assert grants["byDisplayName"]["Audit Report Agent"]["ops"] == []
    eval_grants = json.loads(GRANTS_EVAL.read_text(encoding="utf-8"))
    assert "audit.tools.get_audit_ground_truth" in eval_grants["byDisplayName"]["Auditor Agent"]["ops"]
    assert "audit.tools.get_audit_ground_truth" not in grants["byDisplayName"]["Auditor Agent"]["ops"]
    roster = json.loads(
        (REPO / ".cfo-v2" / "office" / "computer" / "harness" / "roster.json").read_text(
            encoding="utf-8"
        )
    )
    close = next(bot for bot in roster["bots"] if bot["slug"] == "close")
    assert "accrual.tools.create_accrual" in close["connectors"]
    assert "close.tools.get_close_gates" not in close["connectors"]
    ctl_books = next(bot for bot in roster["bots"] if bot["slug"] == "ctl-books")
    assert "close.tools.get_close_gates" in ctl_books["connectors"]
    assert "accrual.tools.create_accrual" not in ctl_books["connectors"]
