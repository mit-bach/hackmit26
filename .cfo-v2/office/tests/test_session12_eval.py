"""Eval isolation and fail-closed close. HUMAN_REVIEW is not MATCHED."""

from __future__ import annotations

from pathlib import Path

import pytest

from close.month_end import run_month_end
from evaluation.isolation import AnswerKeyIsolationError, operational_input_files, operational_phase_guard
from evaluation.keys import load_expected_results
from evaluation.scoring import score_case

REPO = Path(__file__).resolve().parents[3]
DEMO = REPO / ".cfo" / "data" / "demo"


def test_evaluate_cfo_still_isolates_answer_keys() -> None:
    allowed = operational_input_files(DEMO)
    assert not any(path.name == "expected_results.json" for path in allowed)
    assert not any(path.name == "ground_truth.json" for path in allowed)
    with operational_phase_guard():
        with pytest.raises(AnswerKeyIsolationError):
            load_expected_results(DEMO)


def test_human_review_fixture_is_not_remapped_to_matched() -> None:
    status, _score, error, _reason = score_case(expected="HUMAN_REVIEW", actual="MATCHED")
    assert status != "PASS"
    assert error == "UNSAFE_AUTO_RESOLUTION"
    held, held_score, held_error, _held_reason = score_case(
        expected="HUMAN_REVIEW", actual="HUMAN_REVIEW"
    )
    assert held == "EXPECTED_HUMAN_REVIEW"
    assert held_score == 1.0
    assert held_error is None


def test_close_stays_blocked_on_twelve_forty_without_source_mutation(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")
    blocked = run_month_end(
        "2026-09", scenario="demo", live=False, reset=True, allow_close=False
    )
    assert blocked.period.status == "BLOCKED"
    details = " ".join(item.detail for item in blocked.exceptions)
    reviews = " ".join(blocked.human_review_items)
    blob = f"{details} {reviews}"
    assert "12.40" in blob or "12.4" in blob
    by_id = {item.task_id: item for item in blocked.tasks}
    assert by_id["mark_closed"].status != "COMPLETE"
