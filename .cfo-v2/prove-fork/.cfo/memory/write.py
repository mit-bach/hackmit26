"""Write reusable finance decisions after a real result exists."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from memory.models import DecisionMemory, MemoryEvidence
from memory.store import put_memory

REUSABLE_SITUATIONS = {
    "payout_difference",
    "prepaid_treatment",
    "vendor_invoice_pattern",
    "accrual_methodology",
}

TRIVIAL_CASH_TYPES = {
    "EXACT_MATCH",
    "GROUPED_MATCH",
    "UNMATCHED_BANK",
    "UNMATCHED_LEDGER",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_idempotency_key(*parts: str) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_reusable_cash_decision(*, match_type: str, provider: str | None, status: str, replay: bool) -> bool:
    if replay:
        return False
    if status not in {"MATCHED", "EXPLAINED_EXCEPTION"}:
        return False
    if match_type in TRIVIAL_CASH_TYPES:
        return False
    if match_type == "FEE_NETTED" and (provider or "").lower() == "stripe":
        return True
    if match_type == "PROVIDER_PAYOUT" and (provider or "").lower() in {"stripe", "adyen"}:
        return True
    return False


def is_reusable_prepaid_decision(*, selected_method: str | None, reviewer_decision: str | None) -> bool:
    if reviewer_decision != "APPROVE":
        return False
    return selected_method in {"straight_line_monthly", "daily_prorate", "immediate_expense"}


def is_reusable_ap_decision(*, exception_types: list[str], decision: str) -> bool:
    if decision not in {"APPROVE", "HOLD"}:
        return False
    reusable = {
        "vendor_mismatch",
        "unusual_timing",
        "small_amount_discrepancy",
        "duplicate",
    }
    return bool(set(exception_types) & reusable)


REUSABLE_ACCRUAL_METHODS = {
    "last_invoice",
    "simple_average",
    "recent_average",
    "weighted_recent_average",
    "linear_trend",
    "seasonal_prior_year",
    "contract_commitment",
    "usage_run_rate",
    "goods_receipt",
    "purchase_order",
    "conservative_minimum",
}


def is_reusable_accrual_decision(*, status: str, method: str | None) -> bool:
    if status != "accrual_required":
        return False
    return method in REUSABLE_ACCRUAL_METHODS


def write_decision(
    *,
    period: str,
    workflow: str,
    entity_type: str,
    entity_id: str,
    situation_type: str,
    situation_summary: str,
    evidence: list[MemoryEvidence],
    decision: str,
    reasoning_summary: str,
    accounting_treatment: str,
    outcome: str,
    reusable_precedent: str,
    source_trace_ids: list[str],
    tags: list[str],
    fingerprint: str,
    entity_name: str | None = None,
    accounting_category: str | None = None,
    created_at: str | None = None,
) -> tuple[DecisionMemory, bool]:
    if situation_type not in REUSABLE_SITUATIONS:
        raise ValueError(f"situation_type {situation_type!r} is not a reusable precedent class")
    key = make_idempotency_key(workflow, entity_type, entity_id, situation_type, period, fingerprint)
    record = DecisionMemory(
        decision_id="",
        period=period,
        workflow=workflow,
        entity_type=entity_type,
        entity_id=entity_id,
        situation_type=situation_type,
        situation_summary=situation_summary,
        evidence=evidence,
        decision=decision,
        reasoning_summary=reasoning_summary,
        accounting_treatment=accounting_treatment,
        outcome=outcome,
        reusable_precedent=reusable_precedent,
        source_trace_ids=list(source_trace_ids),
        created_at=created_at or _now(),
        tags=list(dict.fromkeys(tags)),
        idempotency_key=key,
        entity_name=entity_name,
        accounting_category=accounting_category,
    )
    return put_memory(record)
