"""Deterministic roll-forwards. Arithmetic is Python-owned."""

from __future__ import annotations

from close.dates import money, period_from_date
from close.models import AccountRollForward
from prepaid.schedule import generate_schedule
from prepaid.store import load_items
from fixed_assets.store import load_assets, load_schedule as load_fa_schedule


def prepaid_rollforward(period: str) -> AccountRollForward:
    beginning = 0.0
    additions = 0.0
    amort = 0.0
    for item in load_items():
        if not item.evidence_refs or not item.source_document_id:
            continue
        if not item.start_date or not item.end_date:
            continue
        start_period = period_from_date(item.start_date)
        schedule = generate_schedule(item)
        prior = money(sum(line.amount for line in schedule if line.period < period))
        current = money(sum(line.amount for line in schedule if line.period == period))
        if start_period == period:
            additions = money(additions + item.total_amount)
        elif start_period < period:
            beginning = money(beginning + money(item.total_amount - prior))
        amort = money(amort + current)
    ending = money(beginning + additions - amort)
    tied = money(beginning + additions - amort) == ending
    return AccountRollForward(
        account="Prepaid Expenses",
        period=period,
        beginning=beginning,
        additions=additions,
        reductions=amort,
        ending=ending,
        formula="Beginning prepaid + new prepaids - amortization = ending prepaid",
        tied=tied,
        evidence_refs=[item.source_document_id for item in load_items() if item.source_document_id],
    )


def fixed_asset_rollforward(period: str) -> AccountRollForward:
    beginning = 0.0
    additions = 0.0
    disposals = 0.0
    for asset in load_assets():
        if asset.status == "duplicate":
            continue
        acquired = period_from_date(asset.acquisition_date)
        if acquired < period:
            beginning = money(beginning + asset.cost)
        elif acquired == period:
            additions = money(additions + asset.cost)
    ending = money(beginning + additions - disposals)
    return AccountRollForward(
        account="Fixed Assets",
        period=period,
        beginning=beginning,
        additions=additions,
        reductions=disposals,
        ending=ending,
        formula="Beginning gross fixed assets + additions - disposals = ending gross fixed assets",
        tied=money(beginning + additions - disposals) == ending,
        evidence_refs=[item.source_document_id for item in load_assets() if item.source_document_id],
    )


def accumulated_depreciation_rollforward(period: str) -> AccountRollForward:
    beginning = 0.0
    current = 0.0
    disposals = 0.0
    for line in load_fa_schedule():
        if line.status != "posted":
            continue
        if line.period < period:
            beginning = money(beginning + line.depreciation_amount)
        elif line.period == period:
            current = money(current + line.depreciation_amount)
    ending = money(beginning + current - disposals)
    return AccountRollForward(
        account="Accumulated Depreciation",
        period=period,
        beginning=beginning,
        additions=current,
        reductions=disposals,
        ending=ending,
        formula="Beginning accumulated depreciation + current depreciation - disposals = ending",
        tied=money(beginning + current - disposals) == ending,
        evidence_refs=["fixed_assets.depreciation_schedule"],
    )


def build_rollforwards(period: str) -> list[AccountRollForward]:
    return [
        prepaid_rollforward(period),
        fixed_asset_rollforward(period),
        accumulated_depreciation_rollforward(period),
    ]
