"""Grant sets for Bots apply and collect. Skills never grant tools."""

from __future__ import annotations

APPLY_OPS: frozenset[str] = frozenset(
    {
        "ar.tools.get_cash_application_facts",
        "ar.tools.get_ar_customer",
        "ar.tools.get_ar_precedents",
    }
)
COLLECT_OPS: frozenset[str] = frozenset(
    {
        "ar.tools.get_collection_candidates",
        "ar.tools.get_collection_invoice_facts",
        "ar.tools.get_ar_customer",
        "ar.tools.get_ar_precedents",
    }
)

PROFILE_OPS: dict[tuple[str, str], frozenset[str]] = {
    ("apply", "apply"): APPLY_OPS,
    ("collect", "chase"): COLLECT_OPS,
}

MUST_NOT_APPLY: frozenset[str] = frozenset(
    {
        "accrual.tools.create_accrual",
        "accrual.tools.reconcile_accrual_with_invoice",
        "scheduling.tools.get_approved_pool",
        "scheduling.tools.get_payment_candidates",
        "scheduling.tools.get_cash_position",
        "ar.tools.get_collection_candidates",
        "ar.tools.get_collection_invoice_facts",
        "ar.tools.get_ar_close_snapshot",
        "audit.tools.get_audit_ground_truth",
    }
)
MUST_NOT_COLLECT: frozenset[str] = frozenset(
    {
        "ar.tools.get_cash_application_facts",
        "accrual.tools.create_accrual",
        "scheduling.tools.get_approved_pool",
        "scheduling.tools.get_payment_candidates",
        "ar.tools.get_ar_close_snapshot",
        "audit.tools.get_audit_ground_truth",
    }
)


def ops_for(slug: str, profile: str) -> frozenset[str]:
    return PROFILE_OPS.get((slug, profile), frozenset())


def profile_allows(slug: str, profile: str, op: str) -> bool:
    allowed = ops_for(slug, profile)
    if not allowed:
        return False
    if slug == "apply" and op in MUST_NOT_APPLY:
        return False
    if slug == "collect" and op in MUST_NOT_COLLECT:
        return False
    return op in allowed


def tool_export_names(tools: list) -> set[str]:
    names: set[str] = set()
    for tool in tools:
        name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if name:
            names.add(str(name))
    return names
