"""Grant set for Bot pay Profile schedule.

Payment Audit is not this Bot. Session 09 maps that Display name to ctl-pay.
"""

from __future__ import annotations

from agent import RECORD_TOOLS, POLICY_TOOLS
from scheduling.tools import (
    get_approved_pool,
    get_cash_position,
    get_payment_candidates,
    get_treasury_policies,
)

PAY_SCHEDULE_OP_IDS: frozenset[str] = frozenset(
    {
        "scheduling.tools.get_cash_position",
        "scheduling.tools.get_approved_pool",
        "scheduling.tools.get_payment_candidates",
        "scheduling.tools.get_treasury_policies",
    }
)

AP_RECORD_OP_IDS: frozenset[str] = frozenset(
    {
        "tools.get_invoice",
        "tools.get_purchase_order",
        "tools.get_goods_receipt",
        "tools.find_duplicate_invoices",
        "tools.get_case_evidence",
    }
)

PAY_SCHEDULE_TOOLS = [
    get_cash_position,
    get_approved_pool,
    get_payment_candidates,
    get_treasury_policies,
]


def tool_export_name(tool: object) -> str:
    name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
    if not isinstance(name, str) or not name:
        raise TypeError(f"tool has no export name: {tool!r}")
    return name


def pay_schedule_export_names() -> frozenset[str]:
    return frozenset(tool_export_name(tool) for tool in PAY_SCHEDULE_TOOLS)


def ap_record_export_names() -> frozenset[str]:
    return frozenset(tool_export_name(tool) for tool in RECORD_TOOLS)


def ap_policy_export_names() -> frozenset[str]:
    return frozenset(tool_export_name(tool) for tool in POLICY_TOOLS)


def profile_allows(profile: str, op_id: str) -> bool:
    if profile != "schedule":
        return False
    return op_id in PAY_SCHEDULE_OP_IDS
