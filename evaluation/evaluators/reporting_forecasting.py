"""Evaluate existing reporting statements, variance analysis, and 13-week forecast."""

from __future__ import annotations

from reporting.forecast import build_forecast, week_starts
from reporting.ledger import lines_for, reset_ledger
from reporting.models import ForecastLine
from reporting.seed import seed_demo_ledger
from reporting.sources import ap_forecast_lines, ar_forecast_lines, load_actuals, payroll_forecast_lines
from reporting.statements import build_income_statement, get_metric, period_report
from reporting.variance import analyze_variance
from reporting.workflow import run_reporting_workflow
from evaluation.comparison import case_result, error_case, fail_case, score_variance_explanation
from evaluation.models import EvaluationCaseResult
from evaluation.scoring import summarize_function


def run_reporting(period: str, expected, comparison_period: str = "2026-08") -> tuple:
    reset_ledger()
    seed_demo_ledger()
    cases: list[EvaluationCaseResult] = []
    try:
        current, prior, metrics = period_report(period, comparison_period=comparison_period)
        explanation = analyze_variance("gross_margin_pct", period, comparison_period)
    except Exception as exc:
        case = error_case(case_id="REPORT-WORKFLOW", domain="reporting", scenario_id="SCN-REPORT-001", reason=str(exc))
        summary = summarize_function("reporting", [case])
        summary.workflow_error = str(exc)
        return summary, {"metrics_tie_to_gl": False}

    gm = get_metric(metrics, "gross_margin_pct", kind="prior_period")
    revenue = get_metric(metrics, "revenue", kind="prior_period")
    cogs = get_metric(metrics, "cogs", kind="prior_period")
    cases.append(
        case_result(
            case_id="REPORT-REVENUE",
            domain="reporting",
            scenario_id="SCN-REPORT-002",
            expected=1_000_000.0,
            actual=round(current.revenue, 2),
            source_ids=["4000-Revenue"],
            equal=lambda exp, act: abs(exp - act) < 0.02,
        )
    )
    cases.append(
        case_result(
            case_id="REPORT-COGS",
            domain="reporting",
            scenario_id="SCN-REPORT-002",
            expected=390_000.0,
            actual=round(current.cogs, 2),
            source_ids=["5200-Supplier"],
            equal=lambda exp, act: abs(exp - act) < 0.02,
        )
    )
    expected_gm = 0.61
    cases.append(
        case_result(
            case_id="REPORT-GM",
            domain="reporting",
            scenario_id="SCN-REPORT-001",
            expected=expected_gm,
            actual=round(current.gross_margin_pct, 4),
            source_ids=["4000-Revenue", "5200-Supplier"],
            equal=lambda exp, act: abs(exp - act) < 0.002,
        )
    )
    direction_ok = (gm.absolute_variance or 0) < 0
    cases.append(
        case_result(
            case_id="REPORT-GM-DIRECTION",
            domain="reporting",
            scenario_id="SCN-REPORT-001",
            expected="decline",
            actual="decline" if direction_ok else "increase",
            source_ids=["gross_margin_pct"],
        )
    )
    magnitude_ok = abs((gm.absolute_variance or 0) + 0.03) < 0.002
    cases.append(
        case_result(
            case_id="REPORT-GM-MAGNITUDE",
            domain="reporting",
            scenario_id="SCN-REPORT-001",
            expected=-0.03,
            actual=round(gm.absolute_variance or 0, 4),
            source_ids=["gross_margin_pct"],
            equal=lambda exp, act: abs(exp - act) < 0.002,
        )
    )

    expected_drivers = list(expected.gross_margin_drivers if expected else [])
    if not expected_drivers:
        expected_drivers = ["TXN-SUP-SEP-001", "TXN-FRT-SEP-001", "TXN-REV-SEP-001", "TXN-HOST-SEP-001"]
    found: set[str] = set()
    for contributor in explanation.contributors:
        found.update(contributor.source_transaction_ids)
        found.update(contributor.source_document_ids)
        found.update(txn.transaction_id for txn in contributor.transactions)
    headline_ok = all(item.score == 1 for item in cases if item.case_id in {"REPORT-GM", "REPORT-GM-DIRECTION", "REPORT-GM-MAGNITUDE"})
    cases.append(
        score_variance_explanation(
            case_id="REPORT-DRIVERS",
            scenario_id="SCN-REPORT-001",
            headline_ok=headline_ok,
            expected_drivers=expected_drivers,
            actual_drivers=sorted(found),
        )
    )

    lines = lines_for(period=period) + lines_for(period=comparison_period)
    unsupported = [item for item in lines if not item.entry_id]
    cases.append(
        case_result(
            case_id="REPORT-TRACE",
            domain="reporting",
            scenario_id="SCN-REPORT-002",
            expected=0,
            actual=len(unsupported),
            source_ids=[item.line_id for item in unsupported[:5]],
        )
    )

    summary = summarize_function("reporting", cases)
    driver_score = next((item.score for item in cases if item.case_id == "REPORT-DRIVERS"), 0.0)
    number_ok = all(item.score == 1 for item in cases if item.case_id in {"REPORT-REVENUE", "REPORT-COGS", "REPORT-GM"})
    if number_ok and driver_score < 1:
        for item in cases:
            if item.case_id == "REPORT-DRIVERS":
                item.error_type = item.error_type or "VARIANCE_DRIVER_MISATTRIBUTED"
    summary.metrics = {
        "financial_metric_accuracy": round(
            sum(item.score for item in cases if item.case_id in {"REPORT-REVENUE", "REPORT-COGS", "REPORT-GM"}) / 3, 4
        ),
        "variance_direction_accuracy": next((item.score for item in cases if item.case_id == "REPORT-GM-DIRECTION"), 0.0),
        "variance_magnitude_accuracy": next((item.score for item in cases if item.case_id == "REPORT-GM-MAGNITUDE"), 0.0),
        "driver_recall": driver_score,
        "driver_precision": driver_score,
        "ledger_traceability": next((item.score for item in cases if item.case_id == "REPORT-TRACE"), 0.0),
    }
    raw = {
        "revenue": current.revenue,
        "cogs": current.cogs,
        "gross_margin_pct": current.gross_margin_pct,
        "prior_gross_margin_pct": prior.gross_margin_pct if prior else None,
        "driver_transactions": sorted(found),
        "metrics_tie_to_gl": not unsupported,
        "pretends_cash_reconciled": False,
    }
    _ = revenue, cogs
    return summary, raw


def run_forecast(period: str, expected, *, as_of: str = "2026-09-19") -> tuple:
    cases: list[EvaluationCaseResult] = []
    try:
        snapshot = build_forecast(as_of, prior=None, version=1)
    except Exception as exc:
        try:
            run = run_reporting_workflow(period, as_of=as_of, live=False, persist=False, seed=True)
            snapshot = run.forecast
        except Exception as exc2:
            case = error_case(case_id="FC-WORKFLOW", domain="forecasting", scenario_id="SCN-REPORT-003", reason=str(exc2 or exc))
            summary = summarize_function("forecasting", [case])
            summary.workflow_error = str(exc2)
            return summary, {}

    weeks = snapshot.weeks if snapshot else []
    cases.append(
        case_result(
            case_id="FC-WEEKS",
            domain="forecasting",
            scenario_id="SCN-REPORT-003",
            expected=13,
            actual=len(weeks),
            source_ids=[item.week_start for item in weeks],
        )
    )
    math_ok = True
    for week in weeks:
        expected_end = round(
            week.beginning_cash + week.ar_collections + week.other_inflows - week.ap_payments - week.payroll - week.other_outflows,
            2,
        )
        if abs(expected_end - week.ending_cash) > 0.02:
            math_ok = False
            cases.append(
                fail_case(
                    case_id=f"FC-MATH-{week.week_start}",
                    domain="forecasting",
                    scenario_id="SCN-REPORT-003",
                    expected=expected_end,
                    actual=week.ending_cash,
                    error_type="WRONG_AMOUNT",
                    reason=f"Week {week.week_start} does not roll forward",
                    source_ids=[week.week_start],
                )
            )
    if math_ok:
        cases.append(
            case_result(
                case_id="FC-MATH",
                domain="forecasting",
                scenario_id="SCN-REPORT-003",
                expected=True,
                actual=True,
                source_ids=[item.week_start for item in weeks],
            )
        )

    known_sources = set()
    for loader in (ar_forecast_lines, ap_forecast_lines, payroll_forecast_lines):
        try:
            known_sources.update(item.source_id for item in loader())
        except Exception:
            pass
    missing = []
    for line in snapshot.lines:
        if line.source_id and line.source_id not in known_sources and line.source_type in {"invoice", "receivable", "payroll"}:
            missing.append(line.source_id)

    cases.append(
        case_result(
            case_id="FC-SOURCES",
            domain="forecasting",
            scenario_id="SCN-REPORT-003",
            expected=[],
            actual=missing[:10],
            source_ids=missing[:10],
            equal=lambda exp, act: not act,
        )
        if not missing
        else fail_case(
            case_id="FC-SOURCES",
            domain="forecasting",
            scenario_id="SCN-REPORT-003",
            expected=[],
            actual=missing[:10],
            error_type="FORECAST_SOURCE_MISSING",
            reason="Forecast lines point at unknown AP/AR/payroll IDs",
            source_ids=missing[:10],
        )
    )

    actuals = load_actuals()
    expected_misses = list(expected.forecast_miss_drivers if expected else [])
    actual_ids = {item.source_id for item in actuals} | {
        getattr(item, "bank_transaction_id", "")
        for item in actuals
        if getattr(item, "bank_transaction_id", "")
    }
    mapped = [item for item in expected_misses if item in actual_ids]
    cases.append(
        case_result(
            case_id="FC-ACTUALS",
            domain="forecasting",
            scenario_id="SCN-REPORT-004",
            expected=expected_misses,
            actual=sorted(actual_ids),
            source_ids=expected_misses,
            equal=lambda exp, act: set(exp) <= set(act) if exp else True,
        )
    )
    for scenario_id, source_id in (
        ("SCN-REPORT-004", "INV-AR-014"),
        ("SCN-REPORT-005", "INV-012"),
        ("SCN-REPORT-006", "PR-2026-10-02"),
        ("SCN-REPORT-007", "po_1MaximorFees"),
        ("SCN-REPORT-008", "BNK-UNX-001"),
    ):
        cases.append(
            case_result(
                case_id=f"FC-{scenario_id}",
                domain="forecasting",
                scenario_id=scenario_id,
                expected=True,
                actual=source_id in actual_ids,
                source_ids=[source_id],
            )
        )

    starts = week_starts(as_of, 13)
    cases.append(
        case_result(
            case_id="FC-HORIZON",
            domain="forecasting",
            scenario_id="SCN-REPORT-003",
            expected=13,
            actual=len(starts),
        )
    )

    summary = summarize_function("forecasting", cases)
    summary.metrics = {
        "forecast_math_accuracy": 1.0 if math_ok else 0.0,
        "source_schedule_coverage": 1.0 if not missing else 0.0,
        "actual_mapping_accuracy": next((item.score for item in cases if item.case_id == "FC-ACTUALS"), 0.0),
        "miss_detection_accuracy": round(
            sum(
                item.score
                for item in cases
                if item.case_id.startswith("FC-SCN-REPORT-00")
            )
            / 5,
            4,
        ),
        "miss_driver_accuracy": round(len(mapped) / len(expected_misses), 4) if expected_misses else 1.0,
    }
    raw = {
        "weeks": len(weeks),
        "missing_source_ids": missing,
        "actual_source_ids": sorted(actual_ids),
        "beginning_cash": snapshot.beginning_cash if snapshot else None,
    }
    _ = ForecastLine
    return summary, raw
