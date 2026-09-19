"""Deterministic scoring. An LLM never grades amounts, matches, or findings."""

from __future__ import annotations

from collections import Counter

from evaluation.models import (
    CaseStatus,
    EndToEndResult,
    ErrorType,
    EvaluationCaseResult,
    FunctionEvaluationResult,
    HumanReviewMetrics,
    OverallMetrics,
    ReviewClass,
)

UNSAFE_WEIGHT = 1.5


def score_case(
    *,
    expected,
    actual,
    review_class: ReviewClass = "AUTO_RESOLVE_EXPECTED",
    equal=None,
) -> tuple[CaseStatus, float, ErrorType | None, str]:
    """Compare one expected vs actual outcome."""
    matcher = equal or (lambda left, right: left == right)
    expected_review = review_class == "HUMAN_REVIEW_EXPECTED" or _is_human_review(expected)
    actual_review = _is_human_review(actual)

    if expected_review and actual_review:
        return "EXPECTED_HUMAN_REVIEW", 1.0, None, "Human review returned as intended"
    if expected_review and not actual_review:
        if matcher(expected, actual):
            return "PARTIAL", 0.5, "UNSAFE_AUTO_RESOLUTION", "Auto-resolved a human-review case"
        return "FAIL", 0.0, "UNSAFE_AUTO_RESOLUTION", "Auto-resolved a human-review case incorrectly"
    if actual_review and not expected_review:
        return "PARTIAL", 0.5, "UNNECESSARY_HUMAN_REVIEW", "Needless escalation of an auto-resolvable case"
    if matcher(expected, actual):
        return "PASS", 1.0, None, "Actual matches expected"
    return "FAIL", 0.0, "WRONG_MATCH", "Actual does not match expected"


def _is_human_review(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.upper() in {"HUMAN_REVIEW", "EXPECTED_HUMAN_REVIEW"}
    if isinstance(value, dict):
        for key in ("decision", "disposition", "status", "expected_behavior"):
            item = value.get(key)
            if isinstance(item, str) and item.upper() in {"HUMAN_REVIEW", "UNEXPLAINED_DIFFERENCE"}:
                return True
    return False


def summarize_function(domain, cases: list[EvaluationCaseResult]) -> FunctionEvaluationResult:
    passed = sum(1 for item in cases if item.status in {"PASS", "EXPECTED_HUMAN_REVIEW"})
    partial = sum(1 for item in cases if item.status == "PARTIAL")
    failed = sum(1 for item in cases if item.status == "FAIL")
    errors = sum(1 for item in cases if item.status == "ERROR")
    total = len(cases)
    score = round(sum(item.score for item in cases) / total, 4) if total else 0.0
    accuracy = round(passed / total, 4) if total else 0.0
    fp = sum(1 for item in cases if item.error_type == "FALSE_POSITIVE_EXCEPTION")
    fn = sum(
        1
        for item in cases
        if item.error_type in {"MISSED_EXCEPTION", "CONTROL_FAILURE_MISSED", "FALSE_NEGATIVE"}
        or item.error_type == "CONTROL_FAILURE_MISSED"
    )
    fn = sum(
        1
        for item in cases
        if item.error_type in {"MISSED_EXCEPTION", "CONTROL_FAILURE_MISSED"}
    )
    hr_cases = [item for item in cases if item.review_class == "HUMAN_REVIEW_EXPECTED"]
    hr_correct = [
        item
        for item in hr_cases
        if item.status in {"PASS", "EXPECTED_HUMAN_REVIEW"} or item.requires_human_review
    ]
    precision = None
    recall = None
    predicted_pos = [item for item in cases if item.diagnostics.get("predicted_positive")]
    actual_pos = [item for item in cases if item.diagnostics.get("expected_positive")]
    if predicted_pos or actual_pos:
        tp = sum(1 for item in predicted_pos if item.diagnostics.get("expected_positive"))
        precision = round(tp / len(predicted_pos), 4) if predicted_pos else 0.0
        recall = round(tp / len(actual_pos), 4) if actual_pos else 0.0
    return FunctionEvaluationResult(
        domain=domain,
        cases_total=total,
        cases_passed=passed,
        cases_partial=partial,
        cases_failed=failed,
        cases_error=errors,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        false_positive_count=fp,
        false_negative_count=fn,
        human_review_cases=len(hr_cases),
        correct_human_review_cases=len(hr_correct),
        score=score,
        case_results=cases,
    )


def human_review_metrics(cases: list[EvaluationCaseResult]) -> HumanReviewMetrics:
    expected_hr = [item for item in cases if item.review_class == "HUMAN_REVIEW_EXPECTED"]
    predicted_hr = [
        item
        for item in cases
        if item.status == "EXPECTED_HUMAN_REVIEW" or _is_human_review(item.actual)
    ]
    true_hr = [item for item in predicted_hr if item.review_class == "HUMAN_REVIEW_EXPECTED"]
    unsafe = [
        item
        for item in expected_hr
        if item.error_type == "UNSAFE_AUTO_RESOLUTION"
    ]
    needless = [item for item in cases if item.error_type == "UNNECESSARY_HUMAN_REVIEW"]
    precision = (len(true_hr) / len(predicted_hr)) if predicted_hr else 1.0
    recall = (len(true_hr) / len(expected_hr)) if expected_hr else 1.0
    auto_expected = [item for item in cases if item.review_class == "AUTO_RESOLVE_EXPECTED"]
    return HumanReviewMetrics(
        human_review_precision=round(precision, 4),
        human_review_recall=round(recall, 4),
        unnecessary_escalation_rate=round(len(needless) / len(auto_expected), 4) if auto_expected else 0.0,
        unsafe_auto_resolution_rate=round(len(unsafe) / len(expected_hr), 4) if expected_hr else 0.0,
        unsafe_auto_resolution_count=len(unsafe),
        unnecessary_escalation_count=len(needless),
    )


def overall_metrics(
    functions: list[FunctionEvaluationResult],
    end_to_end: list[EndToEndResult],
) -> OverallMetrics:
    cases = [item for fn in functions for item in fn.case_results]
    cases.extend(item for story in end_to_end for item in story.assertions)
    counts = Counter(item.error_type for item in cases if item.error_type)
    passed = sum(1 for item in cases if item.status in {"PASS", "EXPECTED_HUMAN_REVIEW"})
    partial = sum(1 for item in cases if item.status == "PARTIAL")
    failed = sum(1 for item in cases if item.status == "FAIL")
    errors = sum(1 for item in cases if item.status == "ERROR")
    total = len(cases)
    raw = sum(item.score for item in cases)
    unsafe = sum(UNSAFE_WEIGHT - 1.0 for item in cases if item.error_type == "UNSAFE_AUTO_RESOLUTION")
    score = round(max(0.0, (raw - unsafe * 0.25) / total), 4) if total else 0.0
    e2e_scores = [item.score for item in end_to_end]
    consistency = round(sum(e2e_scores) / len(e2e_scores), 4) if e2e_scores else 0.0
    return OverallMetrics(
        cases_total=total,
        cases_passed=passed,
        cases_partial=partial,
        cases_failed=failed,
        cases_error=errors,
        overall_score=score,
        cross_function_consistency_score=consistency,
        human_review=human_review_metrics(cases),
        error_counts={str(key): value for key, value in sorted(counts.items())},
    )
