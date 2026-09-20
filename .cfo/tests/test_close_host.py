"""Bot close host: Profile isolation, Grant SoD, default September stays BLOCKED."""

from __future__ import annotations

import json
from pathlib import Path

from close.gating import journal_safeguards
from close.host import run_close_host
from close.ledger import load_entries
from close.profile_grants import (
    CREATE_ACCRUAL,
    DISPLAY_NAMES,
    PROFILE_OPS,
    mutating_ops,
    profile_allows,
)

REPO = Path(__file__).resolve().parents[2]
FRAGMENT = REPO / ".cfo-v2" / "office" / "bots" / "close" / "grants.fragment.json"
COMPILED = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.json"


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def test_prepaid_cannot_call_create_accrual():
    assert CREATE_ACCRUAL not in PROFILE_OPS["prepaid"]
    assert not profile_allows("prepaid", CREATE_ACCRUAL)
    fragment = json.loads(FRAGMENT.read_text())
    assert CREATE_ACCRUAL not in fragment["byProfile"]["prepaid"]["ops"]
    assert CREATE_ACCRUAL not in fragment["byDisplayName"]["Prepaid Preparer"]["ops"]
    compiled = json.loads(COMPILED.read_text())
    assert CREATE_ACCRUAL not in compiled["byDisplayName"]["Prepaid Preparer"]["ops"]


def test_coordinate_has_no_mutating_catalog_ops():
    assert PROFILE_OPS["coordinate"] == ()
    assert mutating_ops("coordinate") == ()
    fragment = json.loads(FRAGMENT.read_text())
    assert fragment["byProfile"]["coordinate"]["ops"] == []
    compiled = json.loads(COMPILED.read_text())
    assert compiled["byDisplayName"]["Close Manager"]["ops"] == []


def test_accrue_is_the_only_create_accrual_profile():
    holders = [name for name, ops in PROFILE_OPS.items() if CREATE_ACCRUAL in ops]
    assert holders == ["accrue"]
    assert profile_allows("accrue", CREATE_ACCRUAL)


def test_fragment_display_names_are_not_unioned():
    fragment = json.loads(FRAGMENT.read_text())
    accrue = set(fragment["byDisplayName"]["Accrual Agent"]["ops"])
    prepaid = set(fragment["byDisplayName"]["Prepaid Preparer"]["ops"])
    coordinate = set(fragment["byDisplayName"]["Close Manager"]["ops"])
    assert accrue & prepaid == set()
    assert CREATE_ACCRUAL not in prepaid
    assert not coordinate
    for profile, display in DISPLAY_NAMES.items():
        assert fragment["byProfile"][profile]["ops"] == fragment["byDisplayName"][display]["ops"]


def test_host_demo_september_blocked_on_1240(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    computer = tmp_path / "computer"
    state_dir = tmp_path / "month_end"
    result = run_close_host(
        "2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=computer,
        state_dir=state_dir,
    )
    assert result.status == "BLOCKED"
    assert result.gate_passed is False
    assert result.marked_closed is False
    details = " ".join(result.blocked_on)
    assert "12.40" in details or "12.4" in details
    pack = json.loads((computer / result.pack_path).read_text())
    assert pack["status"] == "BLOCKED"
    assert pack["marked_closed"] is False
    assert pack["lock_door"] == "close.month_end"
    assert pack["queue_owner"] == "ctl-books"
    assert pack["human_queue"] is False


def test_host_sequences_separate_profile_wakes(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    computer = tmp_path / "computer"
    result = run_close_host(
        "2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=computer,
        state_dir=tmp_path / "month_end",
    )
    assert "coordinate" in result.profiles_worn
    assert "accrue" in result.profiles_worn
    assert "prepaid" in result.profiles_worn
    wakes_dir = computer / "workspace" / "close" / "2026-09" / "wakes"
    rows = [json.loads(path.read_text()) for path in sorted(wakes_dir.glob("*.json"))]
    for row in rows:
        assert row["profile"]
        assert isinstance(row["ops"], list)
        if row["profile"] != "accrue":
            assert CREATE_ACCRUAL not in row["ops"]
        if row["profile"] == "coordinate":
            assert row["ops"] == []
            assert row["mutatingOps"] == []
            assert row["mark_closed"] is False
        assert "+" not in row["profile"]
    profiles = [row["profile"] for row in rows]
    assert profiles.count("coordinate") >= 1
    lock_handle = computer / "workspace" / "close" / "2026-09" / "handles" / "ctl-books-lock.json"
    assert lock_handle.exists()
    lock = json.loads(lock_handle.read_text())
    assert lock["toSlug"] == "ctl-books"
    assert lock["profile"] == "lock"
    assert lock["humanQueue"] is False
    assert lock["can_mark_closed"] is False
    assert result.live_handles is False
    harness_handles = list((computer / "harness" / "bots" / "bot_ctl_books" / "handles").glob("*.json"))
    assert harness_handles


def test_host_does_not_mark_closed(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    result = run_close_host(
        "2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=tmp_path / "computer",
        state_dir=tmp_path / "month_end",
    )
    assert result.marked_closed is False
    from close.period_lock import is_period_closed

    assert is_period_closed("2026-09") is False


def test_journals_stay_balanced_after_host_demo(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_close_host(
        "2026-09",
        scenario="demo",
        live=False,
        reset=True,
        computer_root=tmp_path / "computer",
        state_dir=tmp_path / "month_end",
    )
    ok, findings = journal_safeguards("2026-09")
    rows = [item for item in load_entries() if item.get("period") == "2026-09"]
    for item in rows:
        assert float(item.get("debit") or 0) == float(item.get("credit") or 0)
    assert "unbalanced" not in " ".join(findings)
    assert ok or all(not f.startswith("unbalanced") for f in findings)
