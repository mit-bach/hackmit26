"""Developer inspection of assigned skills. Does not dump skill bodies."""

from __future__ import annotations

from skills.assignments import AGENT_SKILLS, resolve_agent_name, skills_for
from skills.loader import load_skill, skill_usage_for


def live_agent_instructions(agent_name: str) -> str:
    from agent import (
        approver_agent,
        audit_agent,
        investigator_agent,
        preparer_agent,
        reviewer_agent,
    )
    from accrual.agent import accrual_agent
    from inbox.agents import counterparty_message_agent, finance_inbox_agent
    from invoice_ingestion.agents import AGENTS
    from scheduling.agent import payment_audit_agent, scheduler_agent
    from ar.agents import cash_application_agent, cash_reviewer_agent, collections_agent
    from cash_recon.agent import (
        investigator_agent as cash_recon_investigator,
        preparer_agent as cash_recon_preparer,
        reviewer_agent as cash_recon_reviewer,
    )
    from reporting.agents import (
        board_reporting_agent,
        cash_forecast_agent,
        forecast_reviewer_agent,
        forecast_variance_agent,
        reporting_reviewer_agent,
        variance_analysis_agent,
    )
    from prepaid.agent import prepaid_preparer, prepaid_reviewer
    from fixed_assets.agent import fixed_asset_preparer, fixed_asset_reviewer
    from bs_recon.agent import bs_preparer, bs_reviewer
    from close.agents import close_manager, month_end_reviewer
    from sample_data.agents.sdk import (
        apar_sample_data_agent,
        audit_controls_sample_data_agent,
        cash_recon_sample_data_agent,
        close_sample_data_agent,
        reporting_forecasting_sample_data_agent,
    )
    from audit.agent import audit_report_agent, auditor_agent

    mapping = {
        preparer_agent.name: preparer_agent,
        investigator_agent.name: investigator_agent,
        reviewer_agent.name: reviewer_agent,
        approver_agent.name: approver_agent,
        audit_agent.name: audit_agent,
        accrual_agent.name: accrual_agent,
        scheduler_agent.name: scheduler_agent,
        payment_audit_agent.name: payment_audit_agent,
        collections_agent.name: collections_agent,
        cash_application_agent.name: cash_application_agent,
        cash_reviewer_agent.name: cash_reviewer_agent,
        cash_recon_preparer.name: cash_recon_preparer,
        cash_recon_investigator.name: cash_recon_investigator,
        cash_recon_reviewer.name: cash_recon_reviewer,
        prepaid_preparer.name: prepaid_preparer,
        prepaid_reviewer.name: prepaid_reviewer,
        fixed_asset_preparer.name: fixed_asset_preparer,
        fixed_asset_reviewer.name: fixed_asset_reviewer,
        bs_preparer.name: bs_preparer,
        bs_reviewer.name: bs_reviewer,
        month_end_reviewer.name: month_end_reviewer,
        close_manager.name: close_manager,
        apar_sample_data_agent.name: apar_sample_data_agent,
        cash_recon_sample_data_agent.name: cash_recon_sample_data_agent,
        close_sample_data_agent.name: close_sample_data_agent,
        audit_controls_sample_data_agent.name: audit_controls_sample_data_agent,
        reporting_forecasting_sample_data_agent.name: reporting_forecasting_sample_data_agent,
        auditor_agent.name: auditor_agent,
        audit_report_agent.name: audit_report_agent,
        variance_analysis_agent.name: variance_analysis_agent,
        reporting_reviewer_agent.name: reporting_reviewer_agent,
        board_reporting_agent.name: board_reporting_agent,
        cash_forecast_agent.name: cash_forecast_agent,
        forecast_reviewer_agent.name: forecast_reviewer_agent,
        forecast_variance_agent.name: forecast_variance_agent,
        counterparty_message_agent.name: counterparty_message_agent,
        finance_inbox_agent.name: finance_inbox_agent,
    }
    mapping.update({agent.name: agent for agent in AGENTS.values()})
    agent = mapping.get(agent_name)
    if agent is None or not isinstance(getattr(agent, "instructions", None), str):
        return ""
    return agent.instructions


def format_skills_index() -> str:
    lines: list[str] = []
    for agent_name, skill_names in AGENT_SKILLS.items():
        lines.append(agent_name)
        if skill_names:
            lines.extend(f"  {name}" for name in skill_names)
        else:
            lines.append("  (none)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_agent_skills(query: str, instructions: str | None = None) -> str:
    agent_name = resolve_agent_name(query)
    assigned = skills_for(agent_name)
    if instructions is None:
        instructions = live_agent_instructions(agent_name)
    usage = skill_usage_for(agent_name, instructions)
    lines = [agent_name]
    if not assigned:
        lines.append("  (none)")
        return "\n".join(lines) + "\n"
    for ref in usage.skills:
        skill = load_skill(ref.name)
        lines.append(f"  {ref.name}")
        lines.append(f"    {skill['description']}")
        lines.append(f"    {ref.path}")
        lines.append(f"    content_hash: {ref.content_hash}")
        if instructions is not None:
            lines.append(f"    injected: {'yes' if ref.injected else 'no'}")
    for error in usage.load_errors:
        lines.append(f"  ERROR: {error}")
    return "\n".join(lines) + "\n"
