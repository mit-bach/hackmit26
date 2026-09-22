"""Story packets label UNLOCKED before lock. Forecast does not start from GL cash."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reporting.host import run_story_host
from reporting.store import save_snapshot
from reporting.trusted import forecast_starting_balance
from reporting.unlocked import UNLOCKED, labeled_number, lock_is_closed, stamp_amounts


def test_unlocked_labels_every_number_when_lock_missing():
    stamped = stamp_amounts({"revenue": 1000.0, "cash": 12.4}, lock_status="BLOCKED")
    assert stamped["revenue"]["label"] == UNLOCKED
    assert stamped["cash"]["label"] == UNLOCKED
    assert stamped["cash"]["value"] == 12.4
    closed = stamp_amounts({"revenue": 1000.0}, lock_status="CLOSED")
    assert closed["revenue"] == 1000.0
    assert lock_is_closed("CLOSED")
    assert not lock_is_closed("BLOCKED")
    assert labeled_number(1, lock_status="OPEN")["label"] == UNLOCKED


def test_story_host_labels_unlocked_and_refuses_untrusted_forecast(tmp_path):
    computer = tmp_path / "computer"
    result = run_story_host(computer, period="2026-09", lock_status="BLOCKED")
    assert result["unlocked"] is True
    assert result["trusted"] is False
    assert result["forecast_status"] == "REFUSED"
    flux = json.loads((computer / result["flux_path"]).read_text())
    assert flux["unlocked"] is True
    assert UNLOCKED in flux["narrative"]
    numbers = flux.get("numbers") or {}
    for row in numbers.values():
        if isinstance(row, dict) and "value" in row:
            assert row["label"] == UNLOCKED
    forecast = json.loads((computer / result["forecast_path"]).read_text())
    assert forecast["status"] == "REFUSED"
    assert forecast["beginning_cash"] is None
    assert forecast["trusted_cash"]["forecast_may_start"] is False
    assert UNLOCKED in forecast["narrative"]
    board = json.loads((computer / result["board_path"]).read_text())
    assert UNLOCKED in board["executive_narrative"]
    md = (computer / "workspace" / "story" / "2026-09" / "board.md").read_text()
    assert UNLOCKED in md
    trusted = forecast_starting_balance("2026-09", computer)
    assert trusted["forecast_may_start"] is False
    assert trusted["beginning_cash"] is None


def test_story_does_not_treat_gl_packet_as_trusted(tmp_path):
    computer = tmp_path / "computer"
    dest = computer / "workspace" / "cash" / "trusted"
    dest.mkdir(parents=True)
    dest.joinpath("2026-09.json").write_text(
        json.dumps(
            {
                "object": "trusted_cash",
                "period": "2026-09",
                "trusted": False,
                "forecast_may_start": False,
                "kernel_allow": False,
                "period_status": "UNRECONCILED",
                "unexplained_difference": 12.40,
                "reasons": ["unexplained_difference_minor:1240"],
            }
        )
        + "\n"
    )
    result = run_story_host(computer, period="2026-09", lock_status="BLOCKED")
    forecast = json.loads((computer / result["forecast_path"]).read_text())
    assert forecast["status"] == "REFUSED"
    assert forecast["beginning_cash"] is None
    assert result["trusted"] is False


def test_forecast_snapshot_create_only(tmp_path):
    from reporting.models import CashForecastSnapshot
    from reporting.store import configure_paths

    configure_paths(tmp_path / "reporting")
    snapshot = CashForecastSnapshot(
        forecast_id="CF-TEST-IMMUTABLE",
        as_of_date="2026-09-30",
        beginning_cash=100.0,
    )
    saved = save_snapshot(snapshot)
    with pytest.raises(ValueError, match="immutable|already"):
        save_snapshot(saved)
