from __future__ import annotations

from close.dates import now_iso, period_from_date
from fixed_assets.agent import (
    deterministic_prepare,
    deterministic_review,
    fixed_asset_preparer,
    fixed_asset_reviewer,
)
from fixed_assets.models import AssetRun, AssetTrace, CapitalCandidate, FixedAsset
from fixed_assets.posting import capitalize_asset, post_depreciation, register_totals
from fixed_assets.store import (
    find_duplicates,
    get_asset,
    load_assets,
    load_seed_candidates,
    next_asset_id,
    upsert_asset,
)
from skills.loader import usage_from_agent


def _asset_from_candidate(candidate: CapitalCandidate) -> FixedAsset:
    return FixedAsset(
        asset_id=next_asset_id(),
        description=candidate.description,
        vendor=candidate.vendor,
        acquisition_date=candidate.invoice_date,
        placed_in_service_date=candidate.invoice_date,
        cost=candidate.amount,
        salvage_value=candidate.salvage_value,
        useful_life_months=candidate.useful_life_months,
        asset_account=candidate.asset_account,
        accumulated_depreciation_account=candidate.accumulated_depreciation_account,
        depreciation_expense_account=candidate.depreciation_expense_account,
        evidence_refs=list(candidate.evidence_refs),
        asset_class=candidate.asset_class,
        source_document_id=candidate.source_document_id,
        transaction_id=candidate.transaction_id or candidate.candidate_id,
        created_at=now_iso(),
    )


def _decide(subject, *, use_agent: bool):
    if use_agent:
        from agent import run_agent

        label = subject.asset_id if isinstance(subject, FixedAsset) else subject.candidate_id
        preparer = run_agent(fixed_asset_preparer, f"Prepare fixed-asset treatment for {label}.")
        reviewer = run_agent(
            fixed_asset_reviewer,
            f"Review {label}. Preparer decided {preparer.decision}: {preparer.reasoning_summary}",
        )
        return preparer, reviewer, True
    return deterministic_prepare(subject), deterministic_review(subject, deterministic_prepare(subject)), False


def _ingest_candidates(period: str, *, use_agent: bool) -> tuple[list[AssetTrace], list[dict], list[str], bool]:
    traces: list[AssetTrace] = []
    duplicates: list[dict] = []
    exceptions: list[str] = []
    used_agent = False
    for candidate in load_seed_candidates():
        existing = find_duplicates(candidate)
        preparer, reviewer, live = _decide(candidate, use_agent=use_agent)
        used_agent = used_agent or live
        agents = [usage_from_agent(fixed_asset_preparer), usage_from_agent(fixed_asset_reviewer)] if live else []
        if preparer.decision == "duplicate_review" or existing:
            match_id = preparer.duplicate_of or (existing[0].asset_id if existing else "")
            duplicates.append({"candidate_id": candidate.candidate_id, "duplicate_of": match_id})
            exceptions.append(f"{candidate.candidate_id}: duplicate of {match_id}")
            traces.append(
                AssetTrace(
                    asset_id=candidate.candidate_id,
                    period=period,
                    preparer=preparer,
                    reviewer=reviewer,
                    explanation=f"Duplicate of {match_id}; not entered a second time.",
                    duplicate_of=match_id,
                    agents=agents,
                    used_agent=live,
                )
            )
            continue
        if reviewer.decision != "APPROVE" or preparer.decision != "capitalize":
            reason = reviewer.reasons[0] if reviewer.reasons else preparer.reasoning_summary
            exceptions.append(f"{candidate.candidate_id}: {reason}")
            traces.append(
                AssetTrace(
                    asset_id=candidate.candidate_id,
                    period=period,
                    preparer=preparer,
                    reviewer=reviewer,
                    explanation=reason,
                    agents=agents,
                    used_agent=live,
                )
            )
            continue
        asset = _asset_from_candidate(candidate)
        upsert_asset(asset)
        capitalize_asset(asset)
        traces.append(
            AssetTrace(
                asset_id=asset.asset_id,
                period=period,
                preparer=preparer,
                reviewer=reviewer,
                explanation=f"Capitalized {asset.description} from {asset.source_document_id}.",
                agents=agents,
                used_agent=live,
            )
        )
    return traces, duplicates, exceptions, used_agent


def run_depreciation_workflow(period: str, *, use_agent: bool = False) -> AssetRun:
    ingest_traces, duplicates, exceptions, used_agent = _ingest_candidates(period, use_agent=use_agent)
    posted_all = []
    journals: list[str] = []
    traces = list(ingest_traces)
    for asset in load_assets():
        if asset.status == "duplicate":
            continue
        if period < period_from_date(asset.placed_in_service_date):
            continue
        if not asset.evidence_refs or not asset.source_document_id:
            exceptions.append(f"{asset.asset_id}: missing acquisition evidence")
            continue
        line = post_depreciation(asset, period)
        if line is None:
            continue
        posted_all.append(line)
        if line.journal_entry_id:
            journals.append(line.journal_entry_id)
        traces.append(
            AssetTrace(
                asset_id=asset.asset_id,
                period=period,
                lines_posted=[line],
                journal_entry_ids=[line.journal_entry_id] if line.journal_entry_id else [],
                explanation=(
                    f"{'Amortized' if asset.asset_class == 'intangible' else 'Depreciated'} "
                    f"{asset.asset_id} {line.depreciation_amount:.2f}; "
                    f"ending book value {line.ending_book_value:.2f}."
                ),
                used_agent=use_agent,
            )
        )
    cost, accum, nbv = register_totals()
    return AssetRun(
        period=period,
        assets=load_assets(),
        lines_posted=posted_all,
        duplicates=duplicates,
        traces=traces,
        journal_entry_ids=journals,
        register_cost=cost,
        register_accum=accum,
        register_nbv=nbv,
        exceptions=exceptions,
        used_agent=used_agent,
    )
