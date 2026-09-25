"""Per-Profile Grants for Bot close. Never union these sets in one Wake."""

from __future__ import annotations

CREATE_ACCRUAL = "accrual.tools.create_accrual"
RECONCILE_ACCRUAL = "accrual.tools.reconcile_accrual_with_invoice"

WRITE_OPS: frozenset[str] = frozenset({CREATE_ACCRUAL, RECONCILE_ACCRUAL})

ACCRUE_OPS: tuple[str, ...] = (
    "accrual.tools.get_expected_invoices",
    "accrual.tools.get_current_period_invoices",
    "accrual.tools.get_vendor_invoice_history",
    "accrual.tools.get_purchase_orders",
    "accrual.tools.get_goods_receipts",
    "accrual.tools.get_vendor_contract",
    "accrual.tools.get_vendor_usage",
    "accrual.tools.get_estimate_candidates",
    "accrual.tools.compute_accrual_estimate",
    CREATE_ACCRUAL,
    "accrual.tools.get_open_accruals",
    RECONCILE_ACCRUAL,
)

PREPAID_OPS: tuple[str, ...] = (
    "prepaid.tools.get_prepaid",
    "prepaid.tools.list_prepaids",
    "prepaid.tools.get_prepaid_treatment_candidates",
    "prepaid.tools.get_prepaid_schedule",
)

ASSETS_OPS: tuple[str, ...] = (
    "fixed_assets.tools.get_fixed_asset",
    "fixed_assets.tools.list_fixed_assets",
    "fixed_assets.tools.get_depreciation_schedule",
    "fixed_assets.tools.get_capital_candidates",
)

BS_OPS: tuple[str, ...] = (
    "bs_recon.tools.get_reconciliation_packet",
    "bs_recon.tools.list_reconciling_items",
)

COORDINATE_OPS: tuple[str, ...] = ()

PROFILE_OPS: dict[str, tuple[str, ...]] = {
    "accrue": ACCRUE_OPS,
    "prepaid": PREPAID_OPS,
    "assets": ASSETS_OPS,
    "bs": BS_OPS,
    "coordinate": COORDINATE_OPS,
}

DISPLAY_NAMES: dict[str, str] = {
    "accrue": "Accrual Agent",
    "prepaid": "Prepaid Preparer",
    "assets": "Fixed Asset Preparer",
    "bs": "Balance Sheet Reconciliation Preparer",
    "coordinate": "Close Manager",
}

OUTPUT_TYPES: dict[str, str] = {
    "accrue": "AccrualDecision",
    "prepaid": "PrepaidDecision",
    "assets": "AssetDecision",
    "bs": "ReconDecision",
    "coordinate": "CloseManagerDecision",
}

SKILLS: dict[str, tuple[str, ...]] = {
    "accrue": ("accrual-evidence-evaluation", "accrual-method-selection"),
    "prepaid": ("prepaid-expense-accounting",),
    "assets": ("fixed-asset-depreciation",),
    "bs": ("balance-sheet-reconciliation",),
    "coordinate": ("month-end-close-coordination",),
}

LOCK_DOOR = "close.month_end"
TEST_PACKET = "close.orchestrator.run_cfo_close"


def profile_allows(profile: str, op_id: str) -> bool:
    return op_id in PROFILE_OPS.get(profile, ())


def mutating_ops(profile: str) -> tuple[str, ...]:
    return tuple(op for op in PROFILE_OPS.get(profile, ()) if op in WRITE_OPS)


def assert_profile_grant(profile: str, op_id: str) -> None:
    if not profile_allows(profile, op_id):
        raise PermissionError(f"forbidden: close/{profile} cannot call {op_id}")
