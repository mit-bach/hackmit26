"""Helpers for comparing workflow outputs to expected results."""

from __future__ import annotations

from typing import Any, Iterable

from evaluation.models import EvaluationCaseResult, RegressionDelta
from evaluation.scoring import score_case


def case_result(
    *,
    case_id: str,
    domain,
    scenario_id: str,
    expected,
    actual,
    source_ids: list[str] | None = None,
    review_class="AUTO_RESOLVE_EXPECTED",
    equal=None,
    error_type=None,
    reason: str = "",
    diagnostics: dict | None = None,
    agent_run_id: str = "",
) -> EvaluationCaseResult:
    status, score, inferred_error, inferred_reason = score_case(
        expected=expected,
        actual=actual,
        review_class=review_class,
        equal=equal,
    )
    requires_hr = review_class == "HUMAN_REVIEW_EXPECTED" or status == "EXPECTED_HUMAN_REVIEW"
    return EvaluationCaseResult(
        case_id=case_id,
        domain=domain,
        scenario_id=scenario_id,
        status=status,
        expected=expected,
        actual=actual,
        score=score,
        reason=reason or inferred_reason,
        source_ids=list(source_ids or []),
        agent_run_id=agent_run_id,
        requires_human_review=requires_hr,
        review_class=review_class,
        error_type=error_type or inferred_error,
        diagnostics=diagnostics or {},
    )


def fail_case(
    *,
    case_id: str,
    domain,
    scenario_id: str,
    expected,
    actual,
    error_type,
    reason: str,
    source_ids: list[str] | None = None,
    review_class="AUTO_RESOLVE_EXPECTED",
    diagnostics: dict | None = None,
    score: float = 0.0,
    status="FAIL",
) -> EvaluationCaseResult:
    return EvaluationCaseResult(
        case_id=case_id,
        domain=domain,
        scenario_id=scenario_id,
        status=status,
        expected=expected,
        actual=actual,
        score=score,
        reason=reason,
        source_ids=list(source_ids or []),
        review_class=review_class,
        requires_human_review=review_class == "HUMAN_REVIEW_EXPECTED",
        error_type=error_type,
        diagnostics=diagnostics or {},
    )


def error_case(*, case_id: str, domain, scenario_id: str, reason: str, source_ids=None) -> EvaluationCaseResult:
    return EvaluationCaseResult(
        case_id=case_id,
        domain=domain,
        scenario_id=scenario_id,
        status="ERROR",
        score=0.0,
        reason=reason,
        source_ids=list(source_ids or []),
        error_type="WORKFLOW_ERROR",
    )


def set_equal(left: Iterable[Any], right: Iterable[Any]) -> bool:
    return set(left) == set(right)


def contains_all(actual: Iterable[Any], expected: Iterable[Any]) -> bool:
    return set(expected) <= set(actual)


def score_journal_entry(
    *,
    case_id: str,
    scenario_id: str,
    expected: dict,
    actual: dict,
    domain="close",
) -> EvaluationCaseResult:
    """Compare one journal line on account, debit, credit, period, and sources."""
    exp_total = float(expected.get("debit") or 0) + float(expected.get("credit") or 0)
    act_total = float(actual.get("debit") or 0) + float(actual.get("credit") or 0)
    totals_ok = abs(exp_total - act_total) < 0.02
    if expected.get("account") != actual.get("account"):
        return fail_case(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=expected,
            actual=actual,
            error_type="WRONG_ACCOUNT",
            reason="Journal account is wrong even if the entry totals balance",
            source_ids=list(expected.get("source_ids") or []),
        )
    if expected.get("period") and expected.get("period") != actual.get("period"):
        return fail_case(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=expected,
            actual=actual,
            error_type="WRONG_PERIOD",
            reason="Journal period does not match",
            source_ids=list(expected.get("source_ids") or []),
        )
    if abs(float(expected.get("debit") or 0) - float(actual.get("debit") or 0)) >= 0.02 or abs(
        float(expected.get("credit") or 0) - float(actual.get("credit") or 0)
    ) >= 0.02:
        return fail_case(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=expected,
            actual=actual,
            error_type="WRONG_AMOUNT",
            reason="Journal debit/credit amounts do not match",
            source_ids=list(expected.get("source_ids") or []),
        )
    sources_ok = contains_all(actual.get("source_ids") or [], expected.get("source_ids") or [])
    if not sources_ok:
        return fail_case(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=expected,
            actual=actual,
            error_type="UNSUPPORTED_SOURCE",
            reason="Journal source references are incomplete",
            source_ids=list(expected.get("source_ids") or []),
        )
    return case_result(
        case_id=case_id,
        domain=domain,
        scenario_id=scenario_id,
        expected=expected,
        actual=actual,
        source_ids=list(expected.get("source_ids") or []),
        equal=lambda _e, _a: totals_ok and sources_ok,
    )


def score_variance_explanation(
    *,
    case_id: str,
    scenario_id: str,
    headline_ok: bool,
    expected_drivers: list[str],
    actual_drivers: list[str],
    domain="reporting",
) -> EvaluationCaseResult:
    """Full credit only when the headline and source transactions are both right."""
    if headline_ok and set(expected_drivers) <= set(actual_drivers) and actual_drivers:
        return case_result(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=sorted(expected_drivers),
            actual=sorted(actual_drivers),
            source_ids=expected_drivers,
            equal=lambda exp, act: set(exp) <= set(act),
        )
    if headline_ok:
        return fail_case(
            case_id=case_id,
            domain=domain,
            scenario_id=scenario_id,
            expected=sorted(expected_drivers),
            actual=sorted(actual_drivers),
            error_type="VARIANCE_DRIVER_MISATTRIBUTED",
            reason="Correct numerical variance but wrong or incomplete source attribution",
            source_ids=expected_drivers,
        )
    return fail_case(
        case_id=case_id,
        domain=domain,
        scenario_id=scenario_id,
        expected=sorted(expected_drivers),
        actual=sorted(actual_drivers),
        error_type="WRONG_AMOUNT",
        reason="Headline variance is wrong",
        source_ids=expected_drivers,
    )


def score_cash_disposition(
    *,
    object_id: str,
    scenario_id: str,
    expected_type: str | None,
    expected_status: str,
    actual_type: str | None,
    actual_status: str | None,
    human: bool = False,
) -> EvaluationCaseResult:
    if object_id == "TXN-2026-09-015" and actual_status == "MATCHED":
        return fail_case(
            case_id=f"CASH-{scenario_id}",
            domain="cash",
            scenario_id=scenario_id,
            expected=expected_status,
            actual=actual_status,
            error_type="WRONG_MATCH",
            reason="Forced a match on the planted $12.40 difference",
            source_ids=[object_id],
            review_class="HUMAN_REVIEW_EXPECTED",
        )
    type_ok = expected_type is None or actual_type == expected_type
    status_ok = actual_status == expected_status or (
        human and actual_status in {"HUMAN_REVIEW", "OUTSTANDING_TIMING_ITEM"}
    )
    if expected_type == "GROUPED_MATCH":
        type_ok = actual_type == "GROUPED_MATCH"
    if type_ok and status_ok:
        return case_result(
            case_id=f"CASH-{scenario_id}",
            domain="cash",
            scenario_id=scenario_id,
            expected={"match_type": expected_type, "status": expected_status},
            actual={"match_type": actual_type, "status": actual_status},
            source_ids=[object_id],
            review_class="HUMAN_REVIEW_EXPECTED" if human else "AUTO_RESOLVE_EXPECTED",
            equal=lambda _e, _a: True,
        )
    return fail_case(
        case_id=f"CASH-{scenario_id}",
        domain="cash",
        scenario_id=scenario_id,
        expected={"match_type": expected_type, "status": expected_status},
        actual={"match_type": actual_type, "status": actual_status},
        error_type="MISSED_EXCEPTION" if human else "WRONG_MATCH",
        reason=f"{object_id}: expected {expected_type}/{expected_status}, got {actual_type}/{actual_status}",
        source_ids=[object_id],
        review_class="HUMAN_REVIEW_EXPECTED" if human else "AUTO_RESOLVE_EXPECTED",
    )


def score_audit_findings(expected_ids: Iterable[str], actual_ids: Iterable[str]) -> list[EvaluationCaseResult]:
    expected = set(expected_ids)
    actual = set(actual_ids)
    cases = []
    for object_id in sorted(expected - actual):
        cases.append(
            fail_case(
                case_id=f"AUDIT-MISS-{object_id}",
                domain="audit",
                scenario_id="SCN-AUDIT-MISS",
                expected="FAIL",
                actual="PASS",
                error_type="CONTROL_FAILURE_MISSED",
                reason=f"Auditor missed {object_id}",
                source_ids=[object_id],
            )
        )
    for object_id in sorted(actual - expected):
        cases.append(
            fail_case(
                case_id=f"AUDIT-FP-{object_id}",
                domain="audit",
                scenario_id="SCN-AUDIT-FP",
                expected="PASS",
                actual="FAIL",
                error_type="FALSE_AUDIT_FINDING",
                reason=f"Unexpected finding on {object_id}",
                source_ids=[object_id],
            )
        )
    for object_id in sorted(expected & actual):
        cases.append(
            case_result(
                case_id=f"AUDIT-HIT-{object_id}",
                domain="audit",
                scenario_id="SCN-AUDIT-HIT",
                expected="FAIL",
                actual="FAIL",
                source_ids=[object_id],
            )
        )
    return cases


def compare_metrics(baseline: dict[str, float], current: dict[str, float], *, threshold: float = 1e-9) -> list[RegressionDelta]:
    keys = sorted(set(baseline) | set(current))
    rows = []
    for key in keys:
        before = float(baseline.get(key, 0.0))
        after = float(current.get(key, 0.0))
        delta = after - before
        rows.append(
            RegressionDelta(
                metric=key,
                baseline=before,
                current=after,
                delta=round(delta, 6),
                regression=delta < -threshold,
            )
        )
    return rows
