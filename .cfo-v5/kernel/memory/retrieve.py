"""Structured matching for prior-period decision memories.

Retrieval is field-based first. Semantic search is not used.
"""

from __future__ import annotations

from memory.models import DecisionMemory, MemoryLookup, MemoryQuery, RetrievedPrecedent
from memory.policy import memory_enabled
from memory.store import load_memories


def _period_key(period: str) -> str:
    return period or ""


def _tag_overlap(query_tags: list[str], record_tags: list[str]) -> int:
    if not query_tags:
        return 0
    left = {item.lower() for item in query_tags}
    right = {item.lower() for item in record_tags}
    return len(left & right)


def _score(query: MemoryQuery, record: DecisionMemory) -> float | None:
    if query.workflow and record.workflow != query.workflow:
        return None
    if query.entity_type and record.entity_type != query.entity_type:
        return None
    if query.situation_type and record.situation_type != query.situation_type:
        return None
    if query.accounting_category and record.accounting_category != query.accounting_category:
        return None
    if query.exclude_period and record.period == query.exclude_period:
        return None
    if query.prior_to_period and _period_key(record.period) >= _period_key(query.prior_to_period):
        return None

    score = 1.0
    if query.entity_id:
        if record.entity_id.lower() == query.entity_id.lower():
            score += 5.0
        else:
            score -= 4.0
            if score <= 0:
                return None
    overlap = _tag_overlap(query.tags, record.tags)
    if query.tags and overlap == 0:
        score -= 0.5
    score += overlap * 0.75
    score += min(record.support_count, 3) * 0.1
    return score


def _to_precedent(record: DecisionMemory, score: float) -> RetrievedPrecedent:
    return RetrievedPrecedent(
        decision_id=record.decision_id,
        period=record.period,
        workflow=record.workflow,
        entity_id=record.entity_id,
        situation_type=record.situation_type,
        situation_summary=record.situation_summary,
        decision=record.decision,
        reasoning_summary=record.reasoning_summary,
        accounting_treatment=record.accounting_treatment,
        reusable_precedent=record.reusable_precedent,
        outcome=record.outcome,
        score=round(score, 3),
        tags=list(record.tags),
    )


def search_memories(query: MemoryQuery) -> list[RetrievedPrecedent]:
    ranked: list[tuple[float, DecisionMemory]] = []
    for record in load_memories():
        score = _score(query, record)
        if score is None:
            continue
        ranked.append((score, record))
    ranked.sort(key=lambda item: (-item[0], item[1].period, item[1].decision_id))
    return [_to_precedent(record, score) for score, record in ranked[: query.limit]]


def lookup_memories(query: MemoryQuery) -> MemoryLookup:
    enabled = memory_enabled()
    payload = query.model_dump(mode="json")
    if not enabled:
        return MemoryLookup(
            queried=False,
            memory_enabled=False,
            query=payload,
            retrieved=[],
            precedents=[],
        )
    precedents = search_memories(query)
    return MemoryLookup(
        queried=True,
        memory_enabled=True,
        query=payload,
        retrieved=[item.decision_id for item in precedents],
        precedents=precedents,
    )
