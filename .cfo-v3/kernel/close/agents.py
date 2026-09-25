"""Close Manager coordinates work. It does not invent balances or force a close."""

from __future__ import annotations

from agents import Agent

from close.checklist import ready_tasks, unresolved_blockers
from close.models import CloseGateResult, CloseManagerDecision, FinalCloseVerdict, MonthEndState
from close.tools import get_close_gates, get_close_packet

SAFETY = """
Safety rules:
- Never invent a cleared status for a blocked or unexplained account.
- Do not mark the period closed. Kernel evaluate_close_gates is the only door that can later mark CLOSED.
- You cannot talk past a failed gate. APPROVE_CLOSE is ignored when gate_passed is false.
- Do not recalculate journal totals; copy checklist and reconciliation statuses.
""".strip()

LOCK_TOOLS = [get_close_gates, get_close_packet]

month_end_reviewer = Agent(
    name="Month-End Close Reviewer",
    instructions="""
You independently review whether the month can close.

Call get_close_gates and get_close_packet. Copy gate_passed and blockers.
You cannot mark CLOSED. Kernel evaluate_close_gates is the only door that
can later mark CLOSED. close.orchestrator.run_cfo_close is a test packet.

Return only one decision: APPROVE_CLOSE, REJECT_CLOSE, or REQUEST_REVIEW.
APPROVE_CLOSE only when gate_passed is true and the packet is complete.
If gates failed, REJECT_CLOSE. Python ignores APPROVE_CLOSE when gates fail.
""".strip() + "\n\n" + SAFETY,
    tools=LOCK_TOOLS,
    output_type=FinalCloseVerdict,
)

MANAGER_SAFETY = """
Safety rules:
- You coordinate. You do not invent balances, journal amounts, or evidence.
- Deterministic Python validation wins if it conflicts with your narrative.
- Never force-close a failed reconciliation or ignore a fail-closed Kernel status.
- HUMAN_REVIEW is a fail-closed Kernel status. The queue owner is ctl-books. Do not ask a human.
- Do not mark CLOSED. Lock is not yours.
- Never alter ledger amounts.
""".strip()

close_manager = Agent(
    name="Close Manager",
    instructions="""
You are the Close Manager. Coordinate the month-end close.

You may inspect task status, identify blocked workflows, select the next
valid task, explain blockers, and summarize unresolved items.

You may not invent balances, override Python validation, force-close failed
reconciliations, ignore fail-closed Kernel statuses, fabricate evidence,
alter ledger amounts, mark CLOSED, or ask a human. Wake the next Profile
on Bot close. Do not union Grants.
""".strip() + "\n\n" + MANAGER_SAFETY,
    output_type=CloseManagerDecision,
)


def deterministic_coordinate(state: MonthEndState) -> CloseManagerDecision:
    ready = [item.task_id for item in ready_tasks(state.tasks)]
    blocked = [item.task_id for item in unresolved_blockers(state.tasks)]
    waiting = list(state.human_review_items)
    can_close = (
        state.period.status in {"READY_TO_CLOSE", "CLOSED"}
        or (
            not blocked
            and not waiting
            and all(item.status == "COMPLETE" for item in state.tasks if item.task_id != "mark_closed")
        )
    )
    if state.period.status == "CLOSED":
        narrative = (
            "September is closed. The persisted snapshot is the official period state. "
            "A later journal dated in this month must go through the post-close control."
        )
    elif can_close:
        narrative = (
            "All required tasks are complete. Handle ctl-books / lock. "
            "Coordinate does not mark CLOSED."
        )
    elif blocked:
        narrative = (
            "Close is blocked. Fail-closed Kernel statuses remain. "
            "Handle ctl-books. Do not mark CLOSED. Do not ask a human."
        )
    else:
        narrative = "Continue the next ready close task. Do not skip dependency order."
    if ready:
        narrative += f" Next permitted task: {ready[0]}."
    return CloseManagerDecision(
        period=state.period.period,
        next_tasks=ready,
        blocked_tasks=blocked,
        waiting_on_humans=waiting,
        narrative=narrative,
        can_close=can_close and not waiting,
    )


def deterministic_final_review(state: MonthEndState, gate: CloseGateResult, *, reviewer: str = "Month-End Close Reviewer") -> FinalCloseVerdict:
    from close.dates import now_iso

    if gate.passed:
        return FinalCloseVerdict(
            period=state.period.period,
            decision="APPROVE_CLOSE",
            reasons=["All deterministic close gates passed."],
            evidence_used=list(state.evidence_refs),
            reviewer=reviewer,
            created_at=now_iso(),
            gate_passed=True,
        )
    return FinalCloseVerdict(
        period=state.period.period,
        decision="REJECT_CLOSE",
        reasons=list(gate.blockers) or ["Deterministic close gates failed."],
        evidence_used=list(state.evidence_refs),
        reviewer=reviewer,
        created_at=now_iso(),
        gate_passed=False,
    )


def decide_final_close(
    state: MonthEndState,
    gate: CloseGateResult,
    *,
    live: bool = False,
    reviewer: str = "Month-End Close Reviewer",
) -> FinalCloseVerdict:
    from close.dates import now_iso
    from close.gating import reviewer_facts

    fallback = deterministic_final_review(state, gate, reviewer=reviewer)
    if not live:
        return fallback
    try:
        from agent import run_agent

        facts = reviewer_facts(state, gate)
        verdict = run_agent(
            month_end_reviewer,
            (
                f"Review whether {state.period.period} can close. "
                f"Use only these Python facts: {facts}"
            ),
        )
        if not isinstance(verdict, FinalCloseVerdict):
            return fallback
        if verdict.decision == "APPROVE_CLOSE" and not gate.passed:
            return verdict.model_copy(
                update={
                    "decision": "REJECT_CLOSE",
                    "reasons": ["Python gate blocked close; agent approval ignored."] + list(verdict.reasons),
                    "gate_passed": False,
                    "overridden_by_python": True,
                    "created_at": verdict.created_at or now_iso(),
                    "reviewer": reviewer,
                }
            )
        return verdict.model_copy(
            update={
                "period": state.period.period,
                "gate_passed": gate.passed and verdict.decision == "APPROVE_CLOSE",
                "reviewer": verdict.reviewer or reviewer,
                "created_at": verdict.created_at or now_iso(),
            }
        )
    except Exception as exc:
        return fallback.model_copy(update={"reasons": list(fallback.reasons) + [f"Live reviewer unavailable: {exc}"]})
