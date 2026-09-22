"""Straight-line depreciation. Agents do not invent these amounts."""

from __future__ import annotations

from close.dates import add_months, money, period_from_date
from fixed_assets.models import DepreciationScheduleLine, FixedAsset

CAPITALIZATION_THRESHOLD = 5000.0
MIN_LIFE_MONTHS = 12


def depreciable_basis(asset: FixedAsset) -> float:
    basis = money(asset.cost - asset.salvage_value)
    if asset.cost < 0 or asset.salvage_value < 0:
        raise ValueError("Asset cost and salvage value cannot be negative.")
    if basis < 0:
        raise ValueError("Salvage value cannot exceed cost.")
    if asset.useful_life_months <= 0:
        raise ValueError("Useful life must be a positive number of months.")
    return basis


def generate_schedule(asset: FixedAsset) -> list[DepreciationScheduleLine]:
    basis = depreciable_basis(asset)
    start = period_from_date(asset.placed_in_service_date)
    monthly = money(basis / asset.useful_life_months) if asset.useful_life_months else 0
    book = money(asset.cost)
    accum = 0.0
    lines: list[DepreciationScheduleLine] = []
    for index in range(asset.useful_life_months):
        period = add_months(start, index)
        beginning = book
        remaining = money(basis - accum)
        amount = monthly if index < asset.useful_life_months - 1 else remaining
        amount = money(min(amount, remaining))
        ending = money(beginning - amount)
        if ending + 0.001 < asset.salvage_value:
            ending = money(asset.salvage_value)
            amount = money(beginning - ending)
        accum = money(accum + amount)
        if accum - 0.001 > basis:
            raise ValueError("Accumulated depreciation would exceed depreciable basis.")
        if ending + 0.001 < asset.salvage_value:
            raise ValueError("Ending book value would drop below salvage value.")
        lines.append(
            DepreciationScheduleLine(
                asset_id=asset.asset_id,
                period=period,
                beginning_book_value=beginning,
                depreciation_amount=amount,
                ending_book_value=ending,
            )
        )
        book = ending
    if money(sum(line.depreciation_amount for line in lines)) != basis:
        raise ValueError("Schedule does not reconcile to original depreciable basis.")
    if lines and money(lines[-1].ending_book_value) != money(asset.salvage_value):
        raise ValueError("Final book value does not equal salvage value.")
    return lines


def line_for_period(asset: FixedAsset, period: str) -> DepreciationScheduleLine | None:
    placed = period_from_date(asset.placed_in_service_date)
    if period < placed:
        return None
    for line in generate_schedule(asset):
        if line.period == period:
            return line
    return None


def should_capitalize(amount: float, useful_life_months: int) -> bool:
    return amount >= CAPITALIZATION_THRESHOLD and useful_life_months >= MIN_LIFE_MONTHS
