from __future__ import annotations

from prepaid.agent import deterministic_prepare, deterministic_review, prepaid_preparer, prepaid_reviewer
from prepaid.models import PrepaidRun, PrepaidTrace
from prepaid.posting import amortize_item, remaining_by_account
from prepaid.schedule import generate_schedule, treatment_candidates
from prepaid.store import get_item, load_items, upsert_item
from skills.loader import usage_from_agent


def _decide(item, *, use_agent: bool):
    if use_agent:
        from agent import run_agent

        preparer = run_agent(prepaid_preparer, f"Prepare prepaid amortization for {item.prepaid_id}.")
        reviewer = run_agent(
            prepaid_reviewer,
            f"Review prepaid {item.prepaid_id}. Preparer selected {preparer.selected_method}: {preparer.reasoning_summary}",
        )
        return preparer, reviewer, True
    preparer = deterministic_prepare(item.prepaid_id)
    reviewer = deterministic_review(item.prepaid_id, preparer)
    return preparer, reviewer, False


def run_prepaid_workflow(period: str, *, use_agent: bool = False) -> PrepaidRun:
    traces: list[PrepaidTrace] = []
    posted_all = []
    skipped = []
    journals: list[str] = []
    exceptions: list[str] = []
    used_agent = False
    for item in load_items():
        try:
            candidates = treatment_candidates(item)
        except ValueError as exc:
            reason = str(exc)
            skipped.append({"prepaid_id": item.prepaid_id, "reason": reason})
            exceptions.append(f"{item.prepaid_id}: {reason}")
            upsert_item(item.model_copy(update={"status": "review"}))
            traces.append(
                PrepaidTrace(
                    prepaid_id=item.prepaid_id,
                    period=period,
                    explanation=reason,
                    selected_method="insufficient_evidence",
                )
            )
            continue
        preparer, reviewer, live = _decide(item, use_agent=use_agent)
        used_agent = used_agent or live
        agents = []
        if live:
            agents = [usage_from_agent(prepaid_preparer), usage_from_agent(prepaid_reviewer)]
        if reviewer.decision != "APPROVE" or preparer.selected_method == "insufficient_evidence":
            reason = reviewer.reasons[0] if reviewer.reasons else preparer.reasoning_summary
            skipped.append({"prepaid_id": item.prepaid_id, "reason": reason})
            exceptions.append(f"{item.prepaid_id}: {reason}")
            upsert_item(item.model_copy(update={"status": "review" if reviewer.decision != "REJECT" else "blocked"}))
            traces.append(
                PrepaidTrace(
                    prepaid_id=item.prepaid_id,
                    period=period,
                    candidates=candidates,
                    preparer=preparer,
                    reviewer=reviewer,
                    selected_method=preparer.selected_method,
                    explanation=reason,
                    agents=agents,
                    used_agent=live,
                )
            )
            continue
        method = preparer.selected_method or item.amortization_method
        posted = amortize_item(item.prepaid_id, period, method=method)
        posted_all.extend(posted)
        journals.extend(line.journal_entry_id for line in posted if line.journal_entry_id)
        refreshed = get_item(item.prepaid_id) or item
        traces.append(
            PrepaidTrace(
                prepaid_id=item.prepaid_id,
                period=period,
                candidates=candidates,
                preparer=preparer,
                reviewer=reviewer,
                selected_method=method,
                lines_posted=posted,
                journal_entry_ids=[line.journal_entry_id or "" for line in posted if line.journal_entry_id],
                explanation=(
                    f"{method} schedule of {len(generate_schedule(refreshed, method))} lines; "
                    f"{len(posted)} posted through {period}."
                    + (" Late discovery catch-up included." if item.late_discovery else "")
                ),
                agents=agents,
                used_agent=live,
            )
        )
    return PrepaidRun(
        period=period,
        items=load_items(),
        lines_posted=posted_all,
        skipped=skipped,
        traces=traces,
        journal_entry_ids=journals,
        remaining_by_account=remaining_by_account(),
        exceptions=exceptions,
        used_agent=used_agent,
    )
