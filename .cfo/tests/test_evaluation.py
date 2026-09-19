"""Prove the CFO evaluation harness is trustworthy and answer-key isolated."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.comparison import (
    case_result,
    compare_metrics,
    score_audit_findings,
    score_cash_disposition,
    score_journal_entry,
    score_variance_explanation,
)
from evaluation.isolation import (
    AnswerKeyIsolationError,
    operational_input_files,
    operational_phase_guard,
)
from evaluation.keys import load_expected_results
from evaluation.lineage import evaluate_lineage
from evaluation.scoring import score_case, summarize_function
from tools import _read_json

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo"


def test_expected_results_cannot_enter_operational_context(monkeypatch):
    allowed = operational_input_files(DEMO)
    assert not any(path.name == "expected_results.json" for path in allowed)
    assert not any(path.name == "ground_truth.json" for path in allowed)
    with operational_phase_guard():
        with pytest.raises(AnswerKeyIsolationError):
            load_expected_results(DEMO)
        with pytest.raises(AnswerKeyIsolationError):
            _read_json(DEMO / "expected_results.json")
    reads: list[str] = []
    original = Path.read_text

    def spy(self, *args, **kwargs):
        reads.append(Path(self).name)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", spy)
    from tools import load_invoice

    invoice = load_invoice("INV-001")
    assert invoice is not None
    assert "expected_results.json" not in reads


def test_wrong_match_fails():
    status, score, error, _reason = score_case(expected="MATCHED", actual="HUMAN_REVIEW")
    assert status == "PARTIAL"
    assert error == "UNNECESSARY_HUMAN_REVIEW"
    case = case_result(
        case_id="T-WRONG",
        domain="cash",
        scenario_id="SCN-CASH-001",
        expected="MATCHED",
        actual="UNMATCHED_BANK",
    )
    assert case.status == "FAIL"
    assert case.score == 0
    assert case.error_type == "WRONG_MATCH"


def test_correct_match_passes():
    case = case_result(
        case_id="T-OK",
        domain="ap",
        scenario_id="SCN-AP-001",
        expected="APPROVE",
        actual="APPROVE",
        source_ids=["INV-001"],
    )
    assert case.status == "PASS"
    assert case.score == 1.0


def test_expected_human_review_gets_full_credit():
    status, score, error, _reason = score_case(
        expected="HUMAN_REVIEW",
        actual="HUMAN_REVIEW",
        review_class="HUMAN_REVIEW_EXPECTED",
    )
    assert status == "EXPECTED_HUMAN_REVIEW"
    assert score == 1.0
    assert error is None


def test_needless_human_review_is_penalized():
    status, score, error, _reason = score_case(
        expected="AUTO_APPLY",
        actual="HUMAN_REVIEW",
        review_class="AUTO_RESOLVE_EXPECTED",
    )
    assert status == "PARTIAL"
    assert score == 0.5
    assert error == "UNNECESSARY_HUMAN_REVIEW"


def test_false_positive_audit_finding_is_penalized():
    cases = score_audit_findings(["INV-006"], ["INV-006", "INV-001"])
    extra = next(item for item in cases if item.error_type == "FALSE_AUDIT_FINDING")
    assert extra.status == "FAIL"
    assert extra.score == 0
    summary = summarize_function("audit", cases)
    assert summary.cases_failed >= 1


def test_missed_audit_finding_is_penalized():
    cases = score_audit_findings(["INV-006", "JE-POST-CLOSE-001"], ["INV-006"])
    missed = next(item for item in cases if item.error_type == "CONTROL_FAILURE_MISSED")
    assert missed.status == "FAIL"
    assert "JE-POST-CLOSE-001" in missed.source_ids


def test_correct_grouped_cash_match_passes():
    case = score_cash_disposition(
        object_id="TXN-2026-09-008",
        scenario_id="SCN-CASH-002",
        expected_type="GROUPED_MATCH",
        expected_status="MATCHED",
        actual_type="GROUPED_MATCH",
        actual_status="MATCHED",
    )
    assert case.status == "PASS"
    assert case.score == 1.0


def test_forced_match_of_unexplained_difference_fails():
    case = score_cash_disposition(
        object_id="TXN-2026-09-015",
        scenario_id="SCN-CASH-005",
        expected_type="UNEXPLAINED_DIFFERENCE",
        expected_status="HUMAN_REVIEW",
        actual_type="EXACT_MATCH",
        actual_status="MATCHED",
        human=True,
    )
    assert case.status == "FAIL"
    assert case.error_type == "WRONG_MATCH"
    assert case.score == 0


def test_wrong_journal_account_fails_even_if_totals_balance():
    expected = {
        "account": "6100-PrepaidExpense",
        "debit": 1250.0,
        "credit": 0.0,
        "period": "2026-09",
        "source_ids": ["PRE-SFT-001"],
    }
    actual = {
        "account": "1000-Cash",
        "debit": 1250.0,
        "credit": 0.0,
        "period": "2026-09",
        "source_ids": ["PRE-SFT-001"],
    }
    case = score_journal_entry(
        case_id="JE-WRONG-ACCOUNT",
        scenario_id="SCN-CLOSE-003",
        expected=expected,
        actual=actual,
    )
    assert case.status == "FAIL"
    assert case.error_type == "WRONG_ACCOUNT"


def test_wrong_variance_explanation_fails_when_headline_is_right():
    case = score_variance_explanation(
        case_id="VAR-WRONG",
        scenario_id="SCN-REPORT-001",
        headline_ok=True,
        expected_drivers=["TXN-SUP-SEP-001", "TXN-FRT-SEP-001"],
        actual_drivers=["TXN-UNRELATED"],
    )
    assert case.status == "FAIL"
    assert case.error_type == "VARIANCE_DRIVER_MISATTRIBUTED"


def test_broken_cross_function_reference_is_detected():
    stories = evaluate_lineage(
        {
            "cash": {"by_bank": {"TXN-2026-09-015": {"status": "HUMAN_REVIEW", "match_type": "UNEXPLAINED_DIFFERENCE"}}},
            "close": {"cash_fully_reconciled": True, "cash_blocked": False, "period_blocked": False},
            "reporting": {"metrics_tie_to_gl": True, "pretends_cash_reconciled": False},
            "forecast": {"missing_source_ids": []},
            "ap": {"decisions": {}},
        }
    )
    consistency = next(item for item in stories if item.storyline_id == "CROSS-FUNCTION")
    assert any(case.error_type == "BROKEN_LINEAGE" for case in consistency.assertions)
    assert consistency.contradictions


def test_benchmark_scoring_is_deterministic():
    first = [
        case_result(case_id="A", domain="ap", scenario_id="SCN-AP-001", expected="APPROVE", actual="APPROVE"),
        case_result(case_id="B", domain="ar", scenario_id="SCN-AR-009", expected="HUMAN_REVIEW", actual="HUMAN_REVIEW", review_class="HUMAN_REVIEW_EXPECTED"),
    ]
    second = [
        case_result(case_id="A", domain="ap", scenario_id="SCN-AP-001", expected="APPROVE", actual="APPROVE"),
        case_result(case_id="B", domain="ar", scenario_id="SCN-AR-009", expected="HUMAN_REVIEW", actual="HUMAN_REVIEW", review_class="HUMAN_REVIEW_EXPECTED"),
    ]
    left = summarize_function("ap", first)
    right = summarize_function("ap", second)
    assert left.model_dump() == right.model_dump()
    deltas = compare_metrics({"score": left.score}, {"score": right.score})
    assert deltas[0].delta == 0
    assert not deltas[0].regression
