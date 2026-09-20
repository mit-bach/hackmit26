"""Read-only organizational memory tool for agents."""

from __future__ import annotations

from agents import function_tool

from memory.format import PRECEDENT_INSTRUCTION, format_precedents
from memory.models import MemoryQuery
from memory.retrieve import lookup_memories


def retrieve_decision_memories(
    workflow: str = "",
    entity_id: str = "",
    situation_type: str = "",
    period: str = "",
    entity_type: str = "",
) -> dict:
    query = MemoryQuery(
        workflow=workflow or None,
        entity_id=entity_id or None,
        situation_type=situation_type or None,
        entity_type=entity_type or None,
        prior_to_period=period or None,
        exclude_period=period or None,
        limit=5,
    )
    lookup = lookup_memories(query)
    return {
        "memory_enabled": lookup.memory_enabled,
        "queried": lookup.queried,
        "retrieved": list(lookup.retrieved),
        "precedents": [item.model_dump(mode="json") for item in lookup.precedents],
        "instruction": PRECEDENT_INSTRUCTION,
        "summary": format_precedents(lookup),
    }


@function_tool
def get_decision_memories(
    workflow: str = "",
    entity_id: str = "",
    situation_type: str = "",
    period: str = "",
    entity_type: str = "",
) -> dict:
    """Retrieve prior-period organizational decisions. Precedent, not a binding rule."""
    return retrieve_decision_memories(
        workflow=workflow,
        entity_id=entity_id,
        situation_type=situation_type,
        period=period,
        entity_type=entity_type,
    )
