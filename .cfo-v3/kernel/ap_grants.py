"""Constructor Grant sets for Bot ap. Compiler (session 01) is the later SoT.

Profiles on this Bot are never unioned. AP Reviewer / Approver / Audit are
not Profiles here; they belong to ctl-pay.
"""

from __future__ import annotations

AP_SLUG = "ap"
AP_BOT_ID = "bot_ap"
CTL_PAY_SLUG = "ctl-pay"
CTL_PAY_BOT_ID = "bot_ctl_pay"
CTL_PAY_MATCH_PROFILE = "review-match"

PREPARE_PROFILE = "prepare"
INVESTIGATE_PROFILE = "investigate"

PROFILE_DISPLAY = {
    PREPARE_PROFILE: "AP Preparer",
    INVESTIGATE_PROFILE: "Exception Investigator",
}

PREPARE_OPS: tuple[str, ...] = (
    "tools.get_invoice",
    "tools.get_purchase_order",
    "tools.get_goods_receipt",
    "tools.find_duplicate_invoices",
    "tools.get_case_evidence",
)

POLICY_OPS: tuple[str, ...] = (
    "tools.get_company_policies",
    "tools.find_relevant_policies",
    "tools.get_prior_cases",
)

INVESTIGATE_OPS: tuple[str, ...] = PREPARE_OPS + POLICY_OPS

# Approver/Reviewer constructor list. Not granted to ap/prepare.
APPROVER_OPS: tuple[str, ...] = (
    "tools.get_case_evidence",
    "tools.get_company_policies",
    "tools.find_relevant_policies",
    "tools.get_prior_cases",
)

FORBIDDEN_AP_OPS: tuple[str, ...] = (
    "accrual.tools.create_accrual",
    "accrual.tools.reconcile_accrual_with_invoice",
    "scheduling.tools.release_pay_run",
    "audit.tools.get_audit_ground_truth",
)

AP_PROFILES: dict[str, tuple[str, ...]] = {
    PREPARE_PROFILE: PREPARE_OPS,
    INVESTIGATE_PROFILE: INVESTIGATE_OPS,
}


class GrantError(PermissionError):
    """Profile is not allowed to call this Catalog op, or is not a Profile on ap."""


def grants_for(slug: str, profile: str) -> tuple[str, ...]:
    if slug != AP_SLUG:
        raise GrantError(f"ap_grants does not own slug {slug!r}")
    ops = AP_PROFILES.get(profile)
    if ops is None:
        raise GrantError(
            f"Bot ap does not wear Profile {profile!r}. "
            "Concurrence Profiles belong to ctl-pay."
        )
    return ops


def assert_op_allowed(slug: str, profile: str, op: str) -> None:
    allowed = grants_for(slug, profile)
    if op in FORBIDDEN_AP_OPS or op not in allowed:
        raise GrantError(f"forbidden: {slug}/{profile} cannot call {op}")
