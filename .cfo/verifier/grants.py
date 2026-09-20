"""Verifier Grant checks. Catalog overrides are the denylist SoT."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

RECORD_TOOLS: frozenset[str] = frozenset(
    {
        "tools.get_invoice",
        "tools.get_purchase_order",
        "tools.get_goods_receipt",
        "tools.find_duplicate_invoices",
    }
)
ACCRUAL_WRITES: frozenset[str] = frozenset(
    {
        "accrual.tools.create_accrual",
        "accrual.tools.reconcile_accrual_with_invoice",
    }
)
PAY_REBUILD: frozenset[str] = frozenset(
    {
        "scheduling.tools.get_payment_candidates",
        "scheduling.tools.get_approved_pool",
    }
)

# Defense in depth if catalog.overrides.json is missing.
DEFAULT_DISPLAY_DENY: dict[str, frozenset[str]] = {
    "AP Reviewer": RECORD_TOOLS | ACCRUAL_WRITES | PAY_REBUILD,
    "AP Approver": RECORD_TOOLS | ACCRUAL_WRITES | PAY_REBUILD,
    "AP Audit": RECORD_TOOLS | ACCRUAL_WRITES | PAY_REBUILD | frozenset({"tools.get_prior_cases"}),
    "Payment Audit": PAY_REBUILD | ACCRUAL_WRITES | RECORD_TOOLS,
    "Cash Application Reviewer": ACCRUAL_WRITES | RECORD_TOOLS | PAY_REBUILD,
    "Cash Reconciliation Reviewer": ACCRUAL_WRITES | RECORD_TOOLS | PAY_REBUILD,
    "Prepaid Reviewer": ACCRUAL_WRITES,
    "Fixed Asset Reviewer": ACCRUAL_WRITES,
    "Balance Sheet Reconciliation Reviewer": ACCRUAL_WRITES,
    "Month-End Close Reviewer": ACCRUAL_WRITES,
}

DEFAULT_PROFILE_DENY: dict[str, frozenset[str]] = {
    "ctl-pay/review-match": RECORD_TOOLS | ACCRUAL_WRITES | PAY_REBUILD,
    "ctl-pay/review-pay": PAY_REBUILD | ACCRUAL_WRITES | RECORD_TOOLS,
    "ctl-cash/review-apply": ACCRUAL_WRITES | RECORD_TOOLS | PAY_REBUILD,
    "ctl-cash/review-rec": ACCRUAL_WRITES | RECORD_TOOLS | PAY_REBUILD,
    "ctl-books/review-treatment": ACCRUAL_WRITES,
    "ctl-books/lock": ACCRUAL_WRITES,
}

PROFILE_DISPLAY: dict[str, str] = {
    "ctl-pay/review-match": "AP Reviewer",
    "ctl-pay/review-pay": "Payment Audit",
    "ctl-cash/review-apply": "Cash Application Reviewer",
    "ctl-cash/review-rec": "Cash Reconciliation Reviewer",
    "ctl-books/review-treatment": "Prepaid Reviewer",
    "ctl-books/lock": "Month-End Close Reviewer",
}

ALLOWED_AFTER_DENY: dict[str, frozenset[str]] = {
    "ctl-pay/review-match": frozenset(
        {
            "tools.get_case_evidence",
            "tools.get_company_policies",
            "tools.find_relevant_policies",
            "tools.get_prior_cases",
        }
    ),
    "ctl-pay/review-pay": frozenset(
        {
            "scheduling.tools.get_cash_position",
            "scheduling.tools.get_treasury_policies",
        }
    ),
    "ctl-cash/review-apply": frozenset(
        {
            "ar.tools.get_cash_application_facts",
            "ar.tools.get_ar_customer",
            "ar.tools.get_ar_precedents",
        }
    ),
    "ctl-cash/review-rec": frozenset(
        {
            "cash_recon.tools.get_bank_transaction",
            "cash_recon.tools.get_ledger_entry",
            "cash_recon.tools.get_fee_evidence",
            "cash_recon.tools.get_match_candidates",
            "cash_recon.tools.get_candidate",
        }
    ),
    "ctl-books/review-treatment": frozenset(
        {
            "prepaid.tools.get_prepaid",
            "prepaid.tools.list_prepaids",
            "prepaid.tools.get_prepaid_treatment_candidates",
            "prepaid.tools.get_prepaid_schedule",
        }
    ),
    "ctl-books/lock": frozenset(),
}


class VerifierGrantError(PermissionError):
    """Verifier Bot is not allowed to call this Catalog op."""


def computer_cfo_dir() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env) / "cfo"
    return Path(__file__).resolve().parents[2] / ".cfo-v2" / "office" / "computer" / "cfo"


def overrides_path() -> Path:
    return computer_cfo_dir() / "catalog.overrides.json"


@lru_cache(maxsize=4)
def load_overrides(path: str | None = None) -> dict:
    file_path = Path(path) if path else overrides_path()
    if not file_path.is_file():
        return {"grantDenylist": {}, "profileDenylist": {}}
    raw = json.loads(file_path.read_text())
    return raw if isinstance(raw, dict) else {}


def _as_frozen(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        return frozenset()
    return frozenset(item for item in value if isinstance(item, str))


def denied_ops(slug: str, profile: str, *, audit_wake: bool = False, overrides: dict | None = None) -> frozenset[str]:
    key = f"{slug}/{profile}"
    data = overrides if overrides is not None else load_overrides()
    denied = set(DEFAULT_PROFILE_DENY.get(key, frozenset()))
    display = PROFILE_DISPLAY.get(key, "")
    denied |= set(DEFAULT_DISPLAY_DENY.get(display, frozenset()))
    grant_deny = data.get("grantDenylist") or {}
    profile_deny = data.get("profileDenylist") or {}
    if isinstance(grant_deny, dict) and display in grant_deny:
        denied |= set(_as_frozen(grant_deny[display]))
    if isinstance(profile_deny, dict) and key in profile_deny:
        denied |= set(_as_frozen(profile_deny[key]))
    if audit_wake:
        denied.add("tools.get_prior_cases")
    return frozenset(denied)


def allowed_ops(slug: str, profile: str, *, audit_wake: bool = False) -> frozenset[str]:
    key = f"{slug}/{profile}"
    base = set(ALLOWED_AFTER_DENY.get(key, frozenset()))
    base -= set(denied_ops(slug, profile, audit_wake=audit_wake))
    if audit_wake:
        base.discard("tools.get_prior_cases")
    return frozenset(base)


def assert_op_allowed(slug: str, profile: str, op: str, *, audit_wake: bool = False) -> None:
    if slug not in {"ctl-pay", "ctl-cash", "ctl-books"}:
        raise VerifierGrantError(f"{slug} is not a Verifier Bot")
    denied = denied_ops(slug, profile, audit_wake=audit_wake)
    allowed = allowed_ops(slug, profile, audit_wake=audit_wake)
    if op in denied or op not in allowed:
        raise VerifierGrantError(f"forbidden: {slug}/{profile} cannot call {op}")


def profile_allows(slug: str, profile: str, op: str, *, audit_wake: bool = False) -> bool:
    try:
        assert_op_allowed(slug, profile, op, audit_wake=audit_wake)
        return True
    except VerifierGrantError:
        return False
