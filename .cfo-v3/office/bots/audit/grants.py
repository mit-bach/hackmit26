"""Grant sets for Bot audit Profiles interpret and report.

Production omits get_audit_ground_truth. Evaluation may include it after
workflows finish. Profiles are never unioned.
"""

from __future__ import annotations

AUDIT_SLUG = "audit"
AUDIT_BOT_ID = "bot_audit"
INTERPRET_PROFILE = "interpret"
REPORT_PROFILE = "report"

INTERPRET_OPS: tuple[str, ...] = (
    "audit.tools.get_audit_period",
    "audit.tools.get_audit_payments",
    "audit.tools.get_audit_journals",
    "audit.tools.get_audit_approvals",
    "audit.tools.get_audit_vendors",
    "audit.tools.get_audit_invoices",
    "audit.tools.get_operational_decisions",
    "audit.tools.get_planted_reconciliations",
    "audit.tools.get_audit_policy",
)

GROUND_TRUTH_OP = "audit.tools.get_audit_ground_truth"

INTERPRET_EVAL_OPS: tuple[str, ...] = INTERPRET_OPS + (GROUND_TRUTH_OP,)

REPORT_OPS: tuple[str, ...] = ()

FORBIDDEN_OPS: tuple[str, ...] = (
    "accrual.tools.create_accrual",
    "accrual.tools.reconcile_accrual_with_invoice",
    "scheduling.tools.release_pay_run",
    "tools.get_invoice",
    "tools.get_purchase_order",
    "tools.get_goods_receipt",
    "tools.find_duplicate_invoices",
    "tools.get_case_evidence",
)


class GrantError(PermissionError):
    """Profile is not allowed to call this Catalog op."""


def grants_for(slug: str, profile: str, *, phase: str = "operational") -> tuple[str, ...]:
    if slug != AUDIT_SLUG:
        raise GrantError(f"audit grants do not own slug {slug!r}")
    if phase not in {"operational", "evaluation"}:
        raise GrantError(f"unknown phase {phase!r}")
    if profile == INTERPRET_PROFILE:
        if phase == "evaluation":
            return INTERPRET_EVAL_OPS
        return INTERPRET_OPS
    if profile == REPORT_PROFILE:
        return REPORT_OPS
    raise GrantError(
        f"Bot audit does not wear Profile {profile!r}. "
        "Wear interpret or report. Do not union them."
    )


def assert_op_allowed(
    slug: str,
    profile: str,
    op: str,
    *,
    phase: str = "operational",
) -> None:
    allowed = grants_for(slug, profile, phase=phase)
    if op in FORBIDDEN_OPS or op not in allowed:
        raise GrantError(f"forbidden: {slug}/{profile} cannot call {op}")
    if op == GROUND_TRUTH_OP and phase == "operational":
        raise GrantError(f"forbidden: {slug}/{profile} cannot call {op}")
