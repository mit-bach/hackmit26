from __future__ import annotations

from agents import function_tool

from prepaid.models import PrepaidItem
from prepaid.schedule import generate_schedule, treatment_candidates
from prepaid.store import get_item, lines_for, load_items


def _dump(model) -> dict:
    return model.model_dump(mode="json")


@function_tool
def get_prepaid(prepaid_id: str) -> dict:
    """Load one prepaid register item. Does not calculate a schedule."""
    item = get_item(prepaid_id)
    if item is None:
        return {"found": False, "prepaid_id": prepaid_id}
    return {"found": True, **_dump(item)}


@function_tool
def list_prepaids() -> dict:
    """List prepaid register items."""
    rows = load_items()
    return {"found": True, "count": len(rows), "items": [_dump(item) for item in rows]}


@function_tool
def get_prepaid_treatment_candidates(prepaid_id: str) -> dict:
    """Python treatment candidates and amounts. Do not recalculate."""
    item = get_item(prepaid_id)
    if item is None:
        return {"found": False, "prepaid_id": prepaid_id}
    return {
        "found": True,
        "prepaid_id": prepaid_id,
        "candidates": [_dump(item) for item in treatment_candidates(item)],
        "evidence_refs": list(item.evidence_refs),
        "source_document_id": item.source_document_id,
    }


@function_tool
def get_prepaid_schedule(prepaid_id: str, method: str = "") -> dict:
    """Return the Python amortization schedule for a method."""
    item = get_item(prepaid_id)
    if item is None:
        return {"found": False, "prepaid_id": prepaid_id}
    schedule = generate_schedule(item, method or None)
    posted = {(line.period, line.status) for line in lines_for(prepaid_id)}
    return {
        "found": True,
        "prepaid_id": prepaid_id,
        "method": method or item.amortization_method,
        "total": item.total_amount,
        "schedule": [_dump(line) for line in schedule],
        "already_posted_periods": [period for period, status in posted if status == "posted"],
    }


def packet_for(item: PrepaidItem) -> dict:
    return {
        "item": _dump(item),
        "candidates": [_dump(row) for row in treatment_candidates(item)],
        "posted_periods": [line.period for line in lines_for(item.prepaid_id) if line.status == "posted"],
    }
