"""Trace-friendly skill metadata. Names and hashes only — never skill bodies."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillRef(BaseModel):
    name: str
    path: str
    content_hash: str
    injected: bool = False


class AgentSkillTrace(BaseModel):
    role: str
    skills: list[SkillRef] = Field(default_factory=list)
    load_errors: list[str] = Field(default_factory=list)
