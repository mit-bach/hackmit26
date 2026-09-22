"""Cross-function lineage assertions. Downstream must not contradict upstream."""

from __future__ import annotations

from evaluation.comparison import case_result, fail_case
from evaluation.models import EndToEndResult, EvaluationCaseResult
from evaluation.scoring import summarize_function


STORYLINES = (
    {
        "storyline_id": "STORY-CLEAN",
        "document_id": "INV-001",
        "bank_id": "TXN-2026-09-018A",
        "payment_id": "PAY-AP-001",
        "kind": "clean",
    },
    {
        "storyline_id": "STORY-RESOLVED",
        "document_id": "INV-017",
        "bank_id": "TXN-2026-09-011",
        "payment_id": "PAY-AP-017",
        "kind": "resolved_exception",
    },
    {
        "storyline_id": "STORY-UNRESOLVED",
        "document_id": "INV-AR-013",
        "bank_id": "TXN-2026-09-015",
        "payment_id": "PAY-006",
        "kind": "unresolved_review",
    },
)


def evaluate_lineage(raw: dict) -> list[EndToEndResult]:
    ap = raw.get("ap") or {}
    cash = raw.get("cash") or {}
    close = raw.get("close") or {}
    audit = raw.get("audit") or {}
    reporting = raw.get("reporting") or {}
    forecast = raw.get("forecast") or {}
    results = []
    results.append(_clean(ap, cash, close, audit, forecast))
    results.append(_resolved(ap, cash, close))
    results.append(_unresolved(cash, close, audit, reporting))
    results.append(_consistency(ap, cash, close, reporting, forecast))
    return results


def _clean(ap, cash, close, audit, forecast) -> EndToEndResult:
    assertions: list[EvaluationCaseResult] = []
    ap_decision = (ap.get("decisions") or {}).get("INV-001")
    assertions.append(
        case_result(
            case_id="E2E-CLEAN-AP",
            domain="end_to_end",
            scenario_id="STORY-CLEAN",
            expected="APPROVE",
            actual=ap_decision,
            source_ids=["INV-001"],
        )
    )
    cash_status = (cash.get("by_bank") or {}).get("TXN-2026-09-018A", {}).get("status")
    assertions.append(
        case_result(
            case_id="E2E-CLEAN-CASH",
            domain="end_to_end",
            scenario_id="STORY-CLEAN",
            expected="MATCHED",
            actual=cash_status,
            source_ids=["TXN-2026-09-018A", "PAY-AP-001"],
        )
    )
    blocked = set(close.get("blockers") or [])
    assertions.append(
        case_result(
            case_id="E2E-CLEAN-CLOSE",
            domain="end_to_end",
            scenario_id="STORY-CLEAN",
            expected=False,
            actual="INV-001" in blocked or "TXN-2026-09-018A" in blocked,
            source_ids=["INV-001"],
            equal=lambda exp, act: exp == act,
        )
    )
    contradictions = [item.reason for item in assertions if item.status == "FAIL"]
    score = sum(item.score for item in assertions) / len(assertions)
    return EndToEndResult(
        storyline_id="STORY-CLEAN",
        status="PASS" if score == 1 else ("PARTIAL" if score >= 0.5 else "FAIL"),
        score=round(score, 4),
        assertions=assertions,
        contradictions=contradictions,
    )


def _resolved(ap, cash, close) -> EndToEndResult:
    assertions = []
    cash_row = (cash.get("by_bank") or {}).get("TXN-2026-09-011") or {}
    assertions.append(
        case_result(
            case_id="E2E-RESOLVED-FEE",
            domain="end_to_end",
            scenario_id="STORY-RESOLVED",
            expected="FEE_NETTED",
            actual=cash_row.get("match_type"),
            source_ids=["INV-017", "TXN-2026-09-011", "FEE-729103"],
        )
    )
    if cash_row.get("status") == "MATCHED" and cash_row.get("match_type") != "FEE_NETTED":
        assertions.append(
            fail_case(
                case_id="E2E-RESOLVED-NOT-FORCED",
                domain="end_to_end",
                scenario_id="STORY-RESOLVED",
                expected="FEE_NETTED",
                actual=cash_row.get("status"),
                error_type="WRONG_MATCH",
                reason="Fee-netted wire was treated as an exact match",
                source_ids=["TXN-2026-09-011"],
            )
        )
    score = sum(item.score for item in assertions) / len(assertions) if assertions else 0.0
    return EndToEndResult(
        storyline_id="STORY-RESOLVED",
        status="PASS" if score == 1 else ("PARTIAL" if score >= 0.5 else "FAIL"),
        score=round(score, 4),
        assertions=assertions,
        contradictions=[item.reason for item in assertions if item.status == "FAIL"],
    )


def _unresolved(cash, close, audit, reporting) -> EndToEndResult:
    assertions = []
    cash_row = (cash.get("by_bank") or {}).get("TXN-2026-09-015") or {}
    actual_disp = cash_row.get("status") or cash_row.get("match_type")
    assertions.append(
        case_result(
            case_id="E2E-UNRESOLVED-CASH",
            domain="end_to_end",
            scenario_id="STORY-UNRESOLVED",
            expected="HUMAN_REVIEW",
            actual=actual_disp,
            source_ids=["TXN-2026-09-015", "INV-AR-013"],
            review_class="HUMAN_REVIEW_EXPECTED",
        )
    )
    if cash_row.get("status") == "MATCHED":
        assertions.append(
            fail_case(
                case_id="E2E-UNRESOLVED-FORCED",
                domain="end_to_end",
                scenario_id="STORY-UNRESOLVED",
                expected="HUMAN_REVIEW",
                actual="MATCHED",
                error_type="WRONG_MATCH",
                reason="Forced a match on the $12.40 unexplained difference",
                source_ids=["TXN-2026-09-015"],
                review_class="HUMAN_REVIEW_EXPECTED",
            )
        )
    close_blocked = bool(close.get("cash_blocked") or close.get("period_blocked"))
    assertions.append(
        case_result(
            case_id="E2E-UNRESOLVED-CLOSE",
            domain="end_to_end",
            scenario_id="STORY-UNRESOLVED",
            expected=True,
            actual=close_blocked,
            source_ids=["TXN-2026-09-015"],
        )
    )
    if reporting.get("pretends_cash_reconciled"):
        assertions.append(
            fail_case(
                case_id="E2E-UNRESOLVED-REPORTING",
                domain="end_to_end",
                scenario_id="STORY-UNRESOLVED",
                expected="open",
                actual="reconciled",
                error_type="BROKEN_LINEAGE",
                reason="Reporting treated cash as fully reconciled while $12.40 remains open",
                source_ids=["TXN-2026-09-015"],
            )
        )
    score = sum(item.score for item in assertions) / len(assertions) if assertions else 0.0
    return EndToEndResult(
        storyline_id="STORY-UNRESOLVED",
        status="PASS" if score == 1 else ("PARTIAL" if score >= 0.5 else "FAIL"),
        score=round(score, 4),
        assertions=assertions,
        contradictions=[item.reason for item in assertions if item.status == "FAIL"],
    )


def _consistency(ap, cash, close, reporting, forecast) -> EndToEndResult:
    assertions = []
    held = {key for key, value in (ap.get("decisions") or {}).items() if value == "HOLD"}
    paid_holds = set(ap.get("paid_while_held") or [])
    if paid_holds & held:
        assertions.append(
            case_result(
                case_id="E2E-HOLD-PAID-PLANTED",
                domain="end_to_end",
                scenario_id="SCN-AUDIT-007",
                expected="control_exception",
                actual="control_exception",
                source_ids=sorted(paid_holds & held),
                reason="Payment-on-hold is a planted control exception, not an AP agent contradiction",
            )
        )
    gm_tied = bool(reporting.get("metrics_tie_to_gl", True))
    assertions.append(
        case_result(
            case_id="E2E-REPORT-GL",
            domain="end_to_end",
            scenario_id="SCN-REPORT-002",
            expected=True,
            actual=gm_tied,
            source_ids=["4000-Revenue", "5200-Supplier"],
        )
    )
    missing_forecast = list(forecast.get("missing_source_ids") or [])
    assertions.append(
        case_result(
            case_id="E2E-FORECAST-SOURCES",
            domain="end_to_end",
            scenario_id="SCN-REPORT-003",
            expected=[],
            actual=missing_forecast,
            source_ids=missing_forecast,
            error_type="FORECAST_SOURCE_MISSING" if missing_forecast else None,
        )
        if not missing_forecast
        else fail_case(
            case_id="E2E-FORECAST-SOURCES",
            domain="end_to_end",
            scenario_id="SCN-REPORT-003",
            expected=[],
            actual=missing_forecast,
            error_type="FORECAST_SOURCE_MISSING",
            reason="Forecast lines point at unknown source IDs",
            source_ids=missing_forecast,
        )
    )
    cash_open = (cash.get("by_bank") or {}).get("TXN-2026-09-015", {}).get("status") == "MATCHED"
    close_says_ok = close.get("cash_fully_reconciled")
    if cash_open is False and close_says_ok:
        assertions.append(
            fail_case(
                case_id="E2E-CASH-CLOSE-CONTRADICTION",
                domain="end_to_end",
                scenario_id="STORY-UNRESOLVED",
                expected="open",
                actual="reconciled",
                error_type="BROKEN_LINEAGE",
                reason="Cash recon left $12.40 open but close reported cash reconciled",
                source_ids=["TXN-2026-09-015"],
            )
        )
    score = sum(item.score for item in assertions) / len(assertions) if assertions else 1.0
    return EndToEndResult(
        storyline_id="CROSS-FUNCTION",
        status="PASS" if score == 1 else ("PARTIAL" if score >= 0.5 else "FAIL"),
        score=round(score, 4),
        assertions=assertions,
        contradictions=[item.reason for item in assertions if item.status == "FAIL"],
    )


def lineage_function_result(stories: list[EndToEndResult]):
    cases = [item for story in stories for item in story.assertions]
    return summarize_function("end_to_end", cases)
