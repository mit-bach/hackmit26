"""OpenAI Agents SDK wrappers for the five sample-data generators."""

from __future__ import annotations

from sample_data.agents.base import build_agent

apar_sample_data_agent = build_agent(
    "AP/AR Sample Data Agent",
    "Select approved AP and AR scenario templates for the shared company dataset.",
)
cash_recon_sample_data_agent = build_agent(
    "Cash Recon Sample Data Agent",
    "Select approved cash and Stripe scenario templates from existing AP/AR events.",
)
close_sample_data_agent = build_agent(
    "Close Sample Data Agent",
    "Select approved month-end close templates that consume AP, AR, and cash balances.",
)
audit_controls_sample_data_agent = build_agent(
    "Audit Controls Sample Data Agent",
    "Select approved audit and control templates from existing populations.",
)
reporting_forecasting_sample_data_agent = build_agent(
    "Reporting Forecasting Sample Data Agent",
    "Select approved reporting and forecast templates that aggregate the existing ledger.",
)
