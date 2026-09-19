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
    from invoice_ingestion.agents import AGENTS
    from scheduling.agent import payment_audit_agent, scheduler_agent

    mapping = {
        preparer_agent.name: preparer_agent,
        investigator_agent.name: investigator_agent,
        reviewer_agent.name: reviewer_agent,
        approver_agent.name: approver_agent,
        audit_agent.name: audit_agent,
        accrual_agent.name: accrual_agent,
        scheduler_agent.name: scheduler_agent,
        payment_audit_agent.name: payment_audit_agent,
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
