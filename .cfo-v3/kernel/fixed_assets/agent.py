from __future__ import annotations

from agents import Agent

from fixed_assets.models import AssetDecision, AssetReview, CapitalCandidate, FixedAsset
from fixed_assets.schedule import should_capitalize
from fixed_assets.store import find_duplicates
from fixed_assets.tools import (
    get_capital_candidates,
    get_depreciation_schedule,
    get_fixed_asset,
    list_fixed_assets,
)

FA_TOOLS = [get_fixed_asset, list_fixed_assets, get_depreciation_schedule, get_capital_candidates]

SAFETY = """
Safety rules:
- Never invent cost, salvage, useful life, or depreciation amounts.
- Use get_depreciation_schedule for arithmetic. Do not recalculate.
- Duplicate vendor + cost + acquisition date must be flagged, not silently entered twice.
- Do not depreciate before the placed-in-service date.
- Missing acquisition evidence blocks capitalization.
""".strip()

fixed_asset_preparer = Agent(
    name="Fixed Asset Preparer",
    instructions="""
You prepare fixed-asset capitalization and depreciation.

Decide whether an AP purchase is a capital asset or an expense using the Python
capitalization flag and evidence. If a duplicate register item exists, choose
duplicate_review. Copy schedule amounts from Python.
""".strip() + "\n\n" + SAFETY,
    tools=FA_TOOLS,
    output_type=AssetDecision,
)

fixed_asset_reviewer = Agent(
    name="Fixed Asset Reviewer",
    instructions="""
You independently review a capitalization or depreciation proposal.

Approve only when evidence exists, the asset is not a silent duplicate, and
Python schedule amounts are used. Escalate unclear capital-versus-expense cases.
Reject missing evidence or arithmetic that does not match Python.
""".strip() + "\n\n" + SAFETY,
    tools=FA_TOOLS,
    output_type=AssetReview,
)


def deterministic_prepare(subject: FixedAsset | CapitalCandidate) -> AssetDecision:
    asset_id = subject.asset_id if isinstance(subject, FixedAsset) else subject.candidate_id
    evidence = list(subject.evidence_refs)
    source = subject.source_document_id
    duplicates = find_duplicates(subject)
    if isinstance(subject, FixedAsset):
        duplicates = [item for item in duplicates if item.asset_id != subject.asset_id]
    if duplicates:
        return AssetDecision(
            asset_id=asset_id,
            decision="duplicate_review",
            confidence=0.9,
            reasoning_summary=f"Matches existing asset {duplicates[0].asset_id}.",
            evidence_used=evidence,
            duplicate_of=duplicates[0].asset_id,
        )
    if not evidence or not source:
        return AssetDecision(
            asset_id=asset_id,
            decision="insufficient_evidence",
            confidence=0.2,
            reasoning_summary="Acquisition evidence is missing.",
            evidence_used=evidence,
        )
    amount = subject.cost if isinstance(subject, FixedAsset) else subject.amount
    life = subject.useful_life_months
    if should_capitalize(amount, life):
        return AssetDecision(
            asset_id=asset_id,
            decision="capitalize",
            confidence=0.88,
            reasoning_summary="Cost and useful life meet the Python capitalization policy.",
            evidence_used=evidence,
        )
    return AssetDecision(
        asset_id=asset_id,
        decision="expense",
        confidence=0.8,
        reasoning_summary="Below the capitalization threshold or useful life.",
        evidence_used=evidence,
    )


def deterministic_review(subject: FixedAsset | CapitalCandidate, preparer: AssetDecision) -> AssetReview:
    asset_id = subject.asset_id if isinstance(subject, FixedAsset) else subject.candidate_id
    if preparer.decision == "duplicate_review":
        return AssetReview(
            asset_id=asset_id,
            decision="ESCALATE",
            agree_with_preparer=True,
            reasons=["Duplicate asset flagged for review rather than a second register entry."],
            evidence_used=list(subject.evidence_refs),
        )
    if not subject.evidence_refs or not subject.source_document_id:
        return AssetReview(
            asset_id=asset_id,
            decision="REQUEST_EVIDENCE",
            agree_with_preparer=preparer.decision == "insufficient_evidence",
            reasons=["Acquisition support is missing."],
        )
    if preparer.decision == "insufficient_evidence":
        return AssetReview(
            asset_id=asset_id,
            decision="REJECT",
            agree_with_preparer=False,
            reasons=["Evidence is present; insufficient_evidence is not supported."],
            evidence_used=list(subject.evidence_refs),
        )
    return AssetReview(
        asset_id=asset_id,
        decision="APPROVE",
        agree_with_preparer=True,
        reasons=["Evidence supports the asset and the Python capitalization rule was followed."],
        evidence_used=list(subject.evidence_refs),
    )
