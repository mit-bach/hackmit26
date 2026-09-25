from __future__ import annotations

from agents import Agent
from pydantic import BaseModel, Field

from reporting.tools import (
    get_cash_forecast,
    get_forecast_checks,
    get_forecast_snapshot,
    get_period_metrics,
    get_trusted_cash_status,
    get_variance_facts,
    get_variance_trace,
)

SAFETY = """
Safety rules:
- Use Python facts from the tools. Do not recalculate totals, margins, or forecast arithmetic.
- Never invent contributors, invoices, customers, or cash movements.
- Residual amounts stay unexplained. Do not fill them with a business story.
- Every material claim must cite a metric id, transaction id, forecast id, or trace id already in the facts.
- Precedent and judgment cannot override a failed Python reconciliation.
- If lock_status is not CLOSED, label every number UNLOCKED.
- Forecast starting balance is trusted cash. Unreconciled GL cash is not trusted cash.
""".strip()


class VarianceAgentResult(BaseModel):
    narrative: str
    unsupported_claims: list[str] = Field(default_factory=list)
    escalate: bool = False


class ForecastAgentResult(BaseModel):
    judgments: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    narrative: str = ""


class ForecastVarianceAgentResult(BaseModel):
    narrative: str
    unsupported_claims: list[str] = Field(default_factory=list)


class BoardAgentResult(BaseModel):
    executive_narrative: str
    attention_items: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)


class ReviewerAgentResult(BaseModel):
    decision: str
    reasons: list[str] = Field(default_factory=list)
    escalate: bool = False


VARIANCE_TOOLS = [get_period_metrics, get_variance_facts, get_variance_trace]
FORECAST_TOOLS = [get_cash_forecast, get_forecast_snapshot, get_forecast_checks, get_trusted_cash_status]
BOARD_TOOLS = [get_period_metrics, get_variance_facts, get_cash_forecast, get_trusted_cash_status]


variance_analysis_agent = Agent(
    name="Variance Analysis Agent",
    instructions="""
You explain a financial variance that Python already computed.

Call get_variance_facts. Use only those contributors. Label them verified or likely
exactly as Python did. Leave the residual unexplained.

Write a controller-style narrative. Do not add causes that are not in the facts.
Return VarianceAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=VARIANCE_TOOLS,
    output_type=VarianceAgentResult,
)

reporting_reviewer_agent = Agent(
    name="Reporting Reviewer Agent",
    instructions="""
You review a variance explanation or board pack.

Confirm that Python totals reconcile, contributors sum to the dollar variance,
and the narrative does not invent unsupported causes. Escalate material residuals
or broken ties.

Return ReviewerAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=VARIANCE_TOOLS,
    output_type=ReviewerAgentResult,
)

board_reporting_agent = Agent(
    name="Board Reporting Agent",
    instructions="""
You write a compact board narrative from Python financial statements, variances,
and the 13-week cash forecast.

Choose which verified facts deserve attention. Do not invent strategy commentary.
Every material sentence must stay faithful to the supplied metric and evidence ids.

Return BoardAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=BOARD_TOOLS,
    output_type=BoardAgentResult,
)

cash_forecast_agent = Agent(
    name="Cash Forecast Agent",
    instructions="""
Call get_trusted_cash_status first. If forecast_may_start is false, write
REFUSED. Do not start thirteen weeks from unreconciled GL cash.

Python may already have built a 13-week forecast from AP, AR, and payroll
lines. Interpret timing risk, low-confidence collections, and held AP only
when trusted cash exists. Do not change amounts or invent inflows.

If lock_status is not CLOSED, label every number UNLOCKED.

Return ForecastAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=FORECAST_TOOLS,
    output_type=ForecastAgentResult,
)

forecast_reviewer_agent = Agent(
    name="Forecast Reviewer Agent",
    instructions="""
You review a cash forecast or forecast-vs-actual analysis.

Check that weeks roll forward, held invoices are not committed, low-confidence AR
is flagged, and forecast-vs-actual contributors reconcile to the miss.

Return ReviewerAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=FORECAST_TOOLS,
    output_type=ReviewerAgentResult,
)

forecast_variance_agent = Agent(
    name="Forecast Variance Agent",
    instructions="""
You explain a forecast-versus-actual miss from Python contributors.

Keep timing, amount, new/unforecast, removed/cancelled, and unexplained separate.
Do not invent a cause for the residual.

Return ForecastVarianceAgentResult.
""".strip() + "\n\n" + SAFETY,
    tools=FORECAST_TOOLS,
    output_type=ForecastVarianceAgentResult,
)
