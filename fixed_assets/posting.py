from __future__ import annotations

from close.context import remember_link
from close.dates import money, period_from_date
from close.ledger import find_by_key, post_entry
from fixed_assets.models import DepreciationScheduleLine, FixedAsset
from fixed_assets.schedule import generate_schedule, line_for_period
from fixed_assets.store import get_asset, lines_for, upsert_asset, upsert_line


def capitalize_asset(asset: FixedAsset) -> dict | None:
    if not asset.evidence_refs or not asset.source_document_id:
        raise ValueError("Missing evidence: capitalization requires a source document.")
    key = f"fa-capital:{asset.asset_id}"
    existing = find_by_key(key)
    if existing:
        return existing
    journal = post_entry(
        period=period_from_date(asset.acquisition_date),
        memo=f"Capitalize {asset.asset_id} {asset.description}",
        debit_account=asset.asset_account,
        credit_account="Accounts Payable",
        amount=asset.cost,
        entry_type="fixed_asset_capitalization",
        idempotency_key=key,
        source_document_id=asset.source_document_id,
        transaction_id=asset.transaction_id or asset.asset_id,
        evidence_refs=list(asset.evidence_refs),
        related_ids={"asset_id": asset.asset_id},
    )
    remember_link(
        source_document_id=asset.source_document_id,
        transaction_id=asset.transaction_id or asset.asset_id,
        journal_entry_id=journal["entry_id"],
        account_id=asset.asset_account,
        extra={"asset_id": asset.asset_id, "kind": "capitalization"},
    )
    return journal


def post_depreciation(asset: FixedAsset, period: str) -> DepreciationScheduleLine | None:
    if not asset.evidence_refs or not asset.source_document_id:
        raise ValueError("Missing evidence: depreciation requires source support.")
    placed = period_from_date(asset.placed_in_service_date)
    if period < placed:
        raise ValueError("Depreciation cannot begin before the placed-in-service date.")
    existing = next((line for line in lines_for(asset.asset_id) if line.period == period and line.status == "posted"), None)
    if existing:
        return existing
    line = line_for_period(asset, period)
    if line is None:
        return None
    posted = lines_for(asset.asset_id, status="posted")
    accum = money(sum(item.depreciation_amount for item in posted))
    basis = money(asset.cost - asset.salvage_value)
    if money(accum + line.depreciation_amount) - 0.001 > basis:
        raise ValueError("Accumulated depreciation may not exceed depreciable basis.")
    key = f"fa-depr:{asset.asset_id}:{period}"
    already = find_by_key(key)
    if already:
        saved = line.model_copy(
            update={"status": "posted", "journal_entry_id": already["entry_id"], "posted_in_period": period}
        )
        return upsert_line(saved)
    label = "Amortize" if asset.asset_class == "intangible" else "Depreciate"
    journal = post_entry(
        period=period,
        memo=f"{label} {asset.asset_id} {asset.description} for {period}",
        debit_account=asset.depreciation_expense_account,
        credit_account=asset.accumulated_depreciation_account,
        amount=line.depreciation_amount,
        entry_type="intangible_amortization" if asset.asset_class == "intangible" else "depreciation",
        idempotency_key=key,
        source_document_id=asset.source_document_id,
        transaction_id=asset.transaction_id or asset.asset_id,
        evidence_refs=list(asset.evidence_refs),
        related_ids={"asset_id": asset.asset_id, "service_period": period},
    )
    saved = line.model_copy(
        update={"status": "posted", "journal_entry_id": journal["entry_id"], "posted_in_period": period}
    )
    upsert_line(saved)
    remember_link(
        source_document_id=asset.source_document_id,
        transaction_id=asset.transaction_id or asset.asset_id,
        journal_entry_id=journal["entry_id"],
        account_id=asset.depreciation_expense_account,
        extra={"asset_id": asset.asset_id, "kind": "depreciation", "period": period},
    )
    schedule = generate_schedule(asset)
    if period == schedule[-1].period:
        upsert_asset(asset.model_copy(update={"status": "fully_depreciated"}))
    return saved


def register_totals() -> tuple[float, float, float]:
    from fixed_assets.store import load_assets, load_schedule

    cost = money(sum(item.cost for item in load_assets() if item.status != "duplicate"))
    accum = money(sum(line.depreciation_amount for line in load_schedule() if line.status == "posted"))
    return cost, accum, money(cost - accum)


def get_posted_line(asset_id: str, period: str) -> DepreciationScheduleLine | None:
    asset = get_asset(asset_id)
    if asset is None:
        return None
    return next((line for line in lines_for(asset_id) if line.period == period and line.status == "posted"), None)
