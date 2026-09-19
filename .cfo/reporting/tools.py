"""Facts exposed to reporting agents. Agents do not browse the raw ledger."""

from __future__ import annotations

from agents import function_tool

from reporting.forecast import build_forecast, validate_forecast
from reporting.models import CashForecastSnapshot
from reporting.statements import period_report
from reporting.store import latest_snapshot, load_snapshot
from reporting.variance import analyze_variance, trace_variance


@function_tool
def get_period_metrics(period: str, comparison_period: str = "") -> dict:
    """Return Python income-statement metrics and period comparisons."""
    current, prior, metrics = period_report(period, comparison_period=comparison_period or None)
    return {
        "current": current.model_dump(mode="json"),
        "prior": prior.model_dump(mode="json") if prior else None,
        "metrics": [item.model_dump(mode="json") for item in metrics],
    }


@function_tool
def get_variance_facts(metric: str, period: str, comparison_period: str = "") -> dict:
    """Return deterministic variance contributors, residuals, and supporting transactions."""
    explanation = analyze_variance(metric, period, comparison_period or None)
    return explanation.model_dump(mode="json")


@function_tool
def get_variance_trace(metric: str, period: str, comparison_period: str = "") -> dict:
    """Return ranked contributors plus drill-down from metric to source evidence."""
    return trace_variance(metric, period, comparison_period or None).model_dump(mode="json")


@function_tool
def get_cash_forecast(as_of: str) -> dict:
    """Build or return the current 13-week cash forecast computed in Python."""
    snapshot = latest_snapshot(as_of) or build_forecast(as_of)
    return snapshot.model_dump(mode="json")


@function_tool
def get_forecast_snapshot(forecast_id: str) -> dict:
    """Return an immutable historical forecast snapshot."""
    snapshot = load_snapshot(forecast_id)
    if snapshot is None:
        return {"error": f"Unknown forecast {forecast_id}"}
    return snapshot.model_dump(mode="json")


@function_tool
def get_forecast_checks(forecast_id: str) -> dict:
    """Return Python arithmetic checks for a stored forecast."""
    snapshot = load_snapshot(forecast_id)
    if snapshot is None:
        return {"error": f"Unknown forecast {forecast_id}"}
    return {"forecast_id": forecast_id, "errors": validate_forecast(snapshot)}


def snapshot_to_facts(snapshot: CashForecastSnapshot) -> dict:
    return {
        "forecast_id": snapshot.forecast_id,
        "weeks": len(snapshot.weeks),
        "beginning_cash": snapshot.beginning_cash,
        "ending_cash": snapshot.weeks[-1].ending_cash if snapshot.weeks else None,
        "held_ap_ids": snapshot.held_ap_ids,
        "low_confidence_lines": snapshot.low_confidence_lines,
        "arithmetic_errors": validate_forecast(snapshot),
    }
