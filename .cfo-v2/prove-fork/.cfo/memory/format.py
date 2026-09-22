"""Auditor-facing formatting for retrieved precedents and lookup traces."""

from __future__ import annotations

from memory.models import MemoryLookup, RetrievedPrecedent


PRECEDENT_INSTRUCTION = (
    "Use prior decisions as precedent, not as authoritative truth. "
    "Confirm that the current evidence supports the same treatment."
)


def format_precedent(item: RetrievedPrecedent) -> str:
    return (
        f"Prior precedent:\n"
        f"- {item.period}\n"
        f"- {item.situation_summary}\n"
        f"- prior decision: {item.decision}\n"
        f"- treatment: {item.accounting_treatment}\n"
        f"- reusable: {item.reusable_precedent}"
    )


def format_precedents(lookup: MemoryLookup) -> str:
    if not lookup.memory_enabled:
        return "Organizational memory is disabled for this run. Reason from current evidence only."
    if not lookup.precedents:
        return "No prior-period precedent matched this entity and situation."
    blocks = [format_precedent(item) for item in lookup.precedents]
    blocks.append(PRECEDENT_INSTRUCTION)
    return "\n\n".join(blocks)


def format_lookup_trace(lookup: MemoryLookup) -> str:
    query = lookup.query or {}
    retrieved = ", ".join(lookup.retrieved) if lookup.retrieved else "(none)"
    lines = [
        "memory_lookup",
        "query:",
        f"  workflow={query.get('workflow') or ''}",
        f"  entity={query.get('entity_id') or ''}",
        f"  situation_type={query.get('situation_type') or ''}",
        f"retrieved:",
        f"  {retrieved}",
        f"precedent_used:",
        f"  {'yes' if lookup.precedent_used else 'no'}",
        f"precedent_relevance:",
        f"  {lookup.precedent_relevance or '(none)'}",
        f"current_evidence_checked:",
        f"  {'yes' if lookup.current_evidence_checked else 'no'}",
        f"decision:",
        f"  {lookup.decision or '(pending)'}",
    ]
    if lookup.deviation:
        lines.extend(["deviation:", f"  {lookup.deviation}"])
    return "\n".join(lines)
