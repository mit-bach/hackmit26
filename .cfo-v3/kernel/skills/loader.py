"""Trace-only skill hooks.

The office pastes SKILL.md through Harness. This kernel does not load those
files. Callers that used to record which skill text was injected get an empty
trace.
"""

from __future__ import annotations

from skills.models import AgentSkillTrace, SkillRef


def list_skill_names() -> list[str]:
    return []


def load_skill(name: str) -> SkillRef:
    return SkillRef(name=name, path="", content_hash="", injected=False)


def usage_from_agent(agent) -> AgentSkillTrace:
    name = getattr(agent, "name", None)
    role = name if isinstance(name, str) and name else "unknown"
    return AgentSkillTrace(role=role, skills=[], load_errors=[])
