from __future__ import annotations

from agents import function_tool

from fixed_assets.schedule import generate_schedule, should_capitalize
from fixed_assets.store import find_duplicates, get_asset, load_assets, load_seed_candidates


def _dump(model) -> dict:
    return model.model_dump(mode="json")


@function_tool
def get_fixed_asset(asset_id: str) -> dict:
    """Load one asset register record."""
    asset = get_asset(asset_id)
    if asset is None:
        return {"found": False, "asset_id": asset_id}
    return {"found": True, **_dump(asset)}


@function_tool
def list_fixed_assets() -> dict:
    """List the fixed-asset register."""
    rows = load_assets()
    return {"found": True, "count": len(rows), "assets": [_dump(item) for item in rows]}


@function_tool
def get_depreciation_schedule(asset_id: str) -> dict:
    """Python straight-line schedule. Do not recalculate."""
    asset = get_asset(asset_id)
    if asset is None:
        return {"found": False, "asset_id": asset_id}
    schedule = generate_schedule(asset)
    return {
        "found": True,
        "asset_id": asset_id,
        "basis": round(asset.cost - asset.salvage_value, 2),
        "schedule": [_dump(line) for line in schedule],
    }


@function_tool
def get_capital_candidates() -> dict:
    """AP invoices that may be capital assets. Includes Python capitalization flags."""
    rows = []
    for item in load_seed_candidates():
        duplicates = find_duplicates(item)
        rows.append(
            {
                **_dump(item),
                "python_capitalize": should_capitalize(item.amount, item.useful_life_months),
                "duplicate_asset_ids": [asset.asset_id for asset in duplicates],
            }
        )
    return {"found": True, "candidates": rows}
