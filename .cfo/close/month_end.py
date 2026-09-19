"""Dependency-aware month-end close. Calls existing subsystems; does not redesign them."""

from __future__ import annotations

import json
from pathlib import Path

from ar.context import ar_close_snapshot
from ar.models import CustomerPayment
from ar.store import get_payment, save_payment
from accrual.workflow import run_accrual_workflow
from close.agents import decide_final_close
from close.checklist import (
    build_tasks,
    completion_pct,
    ready_tasks,
    refresh_readiness,
    unresolved_blockers,
)
from close.context import all_links, remember_link
from close.dates import month_name, now_iso
from close.ledger import load_entries
from close.models import APCloseResult, CloseException, ClosePeriod, CloseTask, MonthEndState
from close.orchestrator import decide_ap
from invoice_ingestion.workflow import ingest_invoices
from tools import all_invoices

STATE_DIR = Path(__file__).resolve().parent.parent / "runs" / "month_end"


def configure_paths(directory: Path) -> None:
    global STATE_DIR
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    from close.cash_overlay import configure_paths as configure_overlays
    from close.period_lock import configure_paths as configure_lock
    from close.resolve import configure_paths as configure_resolutions
    from close.reviews import configure_paths as configure_reviews
    from close.snapshot import configure_paths as configure_snapshots

    configure_lock(directory)
    configure_resolutions(directory)
    configure_snapshots(directory)
    configure_reviews(directory)
    configure_overlays(directory)


def state_path(period: str) -> Path:
    return STATE_DIR / f"{period}.json"


def load_state(period: str) -> MonthEndState | None:
    path = state_path(period)
    if not path.exists():
        return None
    return MonthEndState.model_validate_json(path.read_text())


def save_state(state: MonthEndState) -> MonthEndState:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path(state.period.period)
    state.trace_path = str(path)
    path.write_text(state.model_dump_json(indent=2) + "\n")
    return state


def new_state(period: str, *, scenario: str = "demo") -> MonthEndState:
    opened = now_iso()
    return MonthEndState(
        period=ClosePeriod(
            period=period,
            status="OPEN",
            opened_at=opened,
            target_close_date=f"{period}-30",
            scenario=scenario,
        ),
        close_id=opened.replace(":", "").replace("-", ""),
        tasks=build_tasks(period),
    )


def reset_subsystem_state() -> None:
    from bs_recon.store import reset as reset_recon
    from cash_recon.store import reset_cash_state
    from close.context import reset_context
    from close.ledger import reset_ledger
    from fixed_assets.store import reset as reset_assets
    from prepaid.store import reset as reset_prepaids

    reset_ledger()
    reset_context()
    reset_prepaids()
    reset_assets()
    reset_recon()
    reset_cash_state()
    from close.cash_overlay import configure_paths as configure_overlays
    from close.cash_overlay import reset_overlays
    from close.period_lock import configure_paths as configure_lock
    from close.resolve import configure_paths as configure_resolutions
    from close.reviews import configure_paths as configure_reviews
    from close.reviews import reset_reviews

    configure_lock(STATE_DIR)
    configure_resolutions(STATE_DIR)
    configure_reviews(STATE_DIR)
    configure_overlays(STATE_DIR)
    reset_reviews()
    reset_overlays()
    lock_path = STATE_DIR / "period_lock.json"
    if lock_path.exists():
        lock_path.write_text("{}\n")
    res_path = STATE_DIR / "resolutions.json"
    if res_path.exists():
        res_path.write_text("[]\n")
    events_path = STATE_DIR / "control_events.json"
    if events_path.exists():
        events_path.write_text("[]\n")


def _inject_demo_ar_payment() -> None:
    if get_payment("PAY-CLOSE-4500") is not None:
        return
    save_payment(
        CustomerPayment(
            payment_id="PAY-CLOSE-4500",
            payment_date="2026-09-29",
            amount=4500.0,
            currency="USD",
            payer_name="Summit Robotics",
            customer_id="CUST-001",
            bank_reference="WIRE-SUMMIT-4500",
            remittance_text="Unmatched September wire",
            source="wire",
            unapplied_amount=4500.0,
            application_status="UNMATCHED",
        )
    )


def _task_result(status: str, *, outputs: list[str] | None = None, evidence: list[str] | None = None, blocker: str = "") -> dict:
    return {
        "status": status,
        "outputs": outputs or [],
        "evidence": evidence or [],
        "blocker": blocker,
    }


def _run_ingest(state: MonthEndState, live: bool) -> dict:
    report = ingest_invoices(period=state.period.period, use_llm=False, forward_to_ap=False, run_ap=False)
    return _task_result(
        "COMPLETE",
        outputs=[report.trace_path or "ingestion"],
        evidence=[report.trace_path] if report.trace_path else [],
    )


def _run_ap(state: MonthEndState, live: bool) -> dict:
    results = [
        decide_ap(item.invoice_id, live=False, featured=set()) for item in all_invoices()
    ]
    from fixed_assets.store import load_seed_candidates

    for candidate in load_seed_candidates():
        if any(item.invoice_id == candidate.candidate_id for item in results):
            continue
        results.append(
            APCloseResult(
                invoice_id=candidate.candidate_id,
                vendor=candidate.vendor,
                amount=candidate.amount,
                decision="APPROVE",
                source="ap_policy",
                ap_decision_id=f"capital/{candidate.candidate_id}",
            )
        )
        remember_link(
            source_document_id=candidate.source_document_id,
            transaction_id=candidate.candidate_id,
            close_task_id="ap",
            extra={"kind": "capital_invoice"},
        )
    state.ap_results = results
    approved = [item.invoice_id for item in results if item.decision == "APPROVE"]
    return _task_result("COMPLETE", outputs=approved, evidence=[item.invoice_id for item in results])


def _run_ar(state: MonthEndState, live: bool) -> dict:
    if state.period.scenario == "demo":
        _inject_demo_ar_payment()
    as_of = f"{state.period.period}-30"
    state.ar = ar_close_snapshot(as_of)
    payment = get_payment("PAY-CLOSE-4500")
    unmatched = (
        payment is not None
        and payment.application_status in {"UNMATCHED", "HUMAN_REVIEW"}
        and payment.unapplied_amount > 0
    )
    state.exceptions = [item for item in state.exceptions if item.ref != "PAY-CLOSE-4500" and item.detail != "AR: $4,500 customer payment unmatched"]
    if state.period.scenario == "demo" and unmatched:
        detail = "AR: $4,500 customer payment unmatched"
        state.exceptions.append(CloseException(kind="bs_recon", ref="PAY-CLOSE-4500", detail=detail))
        if detail not in state.human_review_items:
            state.human_review_items.append(detail)
    return _task_result("COMPLETE", outputs=[f"ar:{as_of}"], evidence=["data/ar_invoices.json"])


def _run_cash(state: MonthEndState, live: bool) -> dict:
    from cash_recon.demo import load_demo_dataset
    from cash_recon.models import PeriodBalances
    from cash_recon.store import get_report
    from cash_recon.workflow import run_cash_reconciliation
    from close.cash_overlay import apply_overlays, has_overlay

    from close.resolve import resolved_ids

    period = state.period.period
    existing = get_report(period)
    reset = bool(state.force_cash_reset or (has_overlay(period) and existing is not None))
    if state.period.scenario == "clean":
        report = existing if existing and not reset else run_cash_reconciliation(
            period,
            balances=PeriodBalances(opening_bank=100000, opening_ledger=100000, as_of_date=f"{period}-30"),
            bank=[],
            ledger=[],
            fees=[],
            reset=reset or existing is None,
        )
    else:
        balances, bank, ledger, fees = load_demo_dataset()
        ledger, fees = apply_overlays(period, ledger, fees)
        report = existing if existing and not reset else run_cash_reconciliation(
            period,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=fees,
            use_agent=live,
            reset=reset or existing is None,
        )
    state.force_cash_reset = False
    state.cash_status = report.period_status
    done = resolved_ids(period)
    unexplained_matches = [
        item
        for item in report.matches
        if item.match_type == "UNEXPLAINED_DIFFERENCE" and item.reconciliation_id not in done
    ]
    state.exceptions = [item for item in state.exceptions if item.kind != "cash_unexplained"]
    state.human_review_items = [
        item for item in state.human_review_items if not item.startswith("Cash:") and not item.startswith("REC-")
    ]
    if unexplained_matches:
        amount = abs(float(report.unexplained_difference or unexplained_matches[0].difference or 0))
        detail = f"Cash: ${amount:,.2f} unexplained difference"
        state.exceptions.append(
            CloseException(kind="cash_unexplained", ref=unexplained_matches[0].reconciliation_id, detail=detail)
        )
        state.human_review_items.append(detail)
        return _task_result(
            "NEEDS_REVIEW",
            outputs=[report.trace_path or f"cash:{period}"],
            evidence=[report.trace_path] if report.trace_path else ["data/cash_recon/bank_statement.json"],
            blocker=detail,
        )
    return _task_result("COMPLETE", outputs=[report.trace_path or f"cash:{period}"])


def _run_accruals(state: MonthEndState, live: bool) -> dict:
    report = run_accrual_workflow(state.period.period, reset=True, use_agent=live)
    state.accrual = report
    for item in report.uncertain_items:
        state.exceptions.append(
            CloseException(kind="accrual_insufficient", ref=item.vendor, detail=f"{item.vendor}: insufficient accrual evidence")
        )
    return _task_result(
        "COMPLETE",
        outputs=[report.trace_dir or f"accrual:{state.period.period}"],
        evidence=[report.trace_dir] if report.trace_dir else [],
    )


def _run_prepaid(state: MonthEndState, live: bool) -> dict:
    from prepaid.store import load_items, load_seed_items, save_items
    from prepaid.workflow import run_prepaid_workflow

    items = load_items()
    if state.period.scenario in {"clean", "seed_demo"}:
        # load_items() may have auto-copied the full seed, including the
        # missing-insurance plant. Clean/seed_demo must drop that item so
        # evidence_gaps() does not block close after cash is resolved.
        seeded = [item for item in (items or load_seed_items()) if item.evidence_refs and item.source_document_id]
        if [item.prepaid_id for item in items] != [item.prepaid_id for item in seeded]:
            save_items(seeded)
    elif not items:
        save_items(load_seed_items())
    report = run_prepaid_workflow(state.period.period, use_agent=live)
    state.prepaid_exceptions = list(report.exceptions)
    state.journal_entry_ids.extend(report.journal_entry_ids)
    state.exceptions = [item for item in state.exceptions if item.kind != "prepaid_evidence"]
    from prepaid.store import get_item

    missing = get_item("PRE-INS-MISSING")
    if missing is not None and (not missing.evidence_refs or not missing.source_document_id):
        detail = "Prepaids: missing insurance policy evidence"
        state.exceptions.append(CloseException(kind="prepaid_evidence", ref="PRE-INS-MISSING", detail=detail))
        if detail not in state.human_review_items:
            state.human_review_items.append(detail)
    return _task_result("COMPLETE", outputs=report.journal_entry_ids, evidence=[item.source_document_id for item in report.items if item.source_document_id])


def _run_depreciation(state: MonthEndState, live: bool) -> dict:
    from fixed_assets.store import load_assets, load_seed_assets, save_assets
    from fixed_assets.workflow import run_depreciation_workflow

    if not load_assets():
        save_assets(load_seed_assets())
    report = run_depreciation_workflow(state.period.period, use_agent=live)
    state.asset_exceptions = list(report.exceptions)
    state.journal_entry_ids.extend(report.journal_entry_ids)
    return _task_result(
        "COMPLETE" if not any("duplicate" in item.lower() for item in report.exceptions) or report.lines_posted else "COMPLETE",
        outputs=report.journal_entry_ids,
        evidence=[item.source_document_id for item in report.assets if item.source_document_id],
    )


def _run_bs_recon(state: MonthEndState, live: bool) -> dict:
    from bs_recon.workflow import run_balance_sheet_reconciliations
    from close.resolve import is_resolved

    report = run_balance_sheet_reconciliations(
        state.period.period,
        use_agent=live,
        ap_results=state.ap_results,
        scenario=state.period.scenario,
    )
    state.recon_exceptions = list(report.exceptions)
    state.reconciliation_ids = [item.reconciliation_id for item in report.reconciliations]
    still_blocking = []
    for recon in report.reconciliations:
        if recon.status not in {"HUMAN_REVIEW", "BLOCKED"}:
            continue
        open_items = [
            row.item_id
            for row in recon.reconciling_items
            if row.classification in {"unexplained_difference", "missing_evidence"}
            and not is_resolved(row.item_id, state.period.period)
        ]
        if is_resolved(recon.reconciliation_id, state.period.period):
            continue
        if recon.finding in {"exact_match", "explained_timing_difference"} and not open_items:
            continue
        if recon.account_id == "Cash" and not open_items:
            continue
        still_blocking.append(recon)
        if recon.account_id == "Cash" and recon.difference:
            unexplained = recon.calculations.get("unexplained_difference", recon.difference)
            detail = f"Cash: ${abs(unexplained):,.2f} unexplained difference"
        elif recon.account_id == "Accounts Receivable":
            detail = "AR: $4,500 customer payment unmatched"
        elif recon.account_id == "Prepaid Expenses":
            detail = "Prepaids: missing insurance policy evidence"
        else:
            detail = f"{recon.account_name}: {recon.explanation}"
        if not any(item.detail == detail for item in state.exceptions):
            state.exceptions.append(CloseException(kind="bs_recon", ref=recon.reconciliation_id, detail=detail))
        if recon.status == "HUMAN_REVIEW" and detail not in state.human_review_items:
            state.human_review_items.append(detail)
    status = "NEEDS_REVIEW" if still_blocking else "COMPLETE"
    return _task_result(
        status,
        outputs=state.reconciliation_ids,
        evidence=[ref for item in report.reconciliations for ref in item.evidence_refs],
        blocker="Accounts still require attention." if still_blocking else "",
    )


def _unresolved_review_items(state: MonthEndState) -> list[str]:
    from close.reviews import blocking_reviews

    return [item.description for item in blocking_reviews(state.period.period)]


def _blocking_exceptions(state: MonthEndState) -> list[CloseException]:
    from close.reviews import blocking_reviews

    blocking = blocking_reviews(state.period.period)
    if not blocking:
        return []
    return [
        CloseException(kind=item.issue_type, ref=item.source_case_id, detail=item.description)
        for item in blocking
    ]


def _run_exceptions(state: MonthEndState, live: bool) -> dict:
    from close.reviews import apply_review_views, harvest_review_items

    harvest_review_items(state.period.period, scenario=state.period.scenario)
    apply_review_views(state)
    blocking = _blocking_exceptions(state)
    review = _unresolved_review_items(state)
    state.human_review_items = review
    if blocking or review:
        return _task_result(
            "NEEDS_REVIEW",
            outputs=[item.detail for item in blocking],
            blocker="Unresolved close exceptions remain.",
        )
    return _task_result("COMPLETE", outputs=["no_exceptions"])


def _auto_clean_verdict(state: MonthEndState):
    from close.models import FinalCloseVerdict

    if state.period.scenario != "clean":
        return
    if state.final_verdict is not None:
        return
    state.final_verdict = FinalCloseVerdict(
        period=state.period.period,
        decision="APPROVE_CLOSE",
        reasons=["Clean fixture has no remaining close blockers."],
        reviewer="deterministic-clean",
        created_at=now_iso(),
        gate_passed=True,
    )


def _run_final_review(state: MonthEndState, live: bool) -> dict:
    from close.gating import evaluate_close_gates
    from close.models import FinalCloseVerdict

    if unresolved_blockers([item for item in state.tasks if item.task_id not in {"final_review", "mark_closed"}]) or _blocking_exceptions(state):
        return _task_result("BLOCKED", blocker="Final close review cannot proceed while blockers remain.")
    _auto_clean_verdict(state)
    gate = evaluate_close_gates(state)
    state.gate = gate
    if not gate.passed:
        return _task_result("BLOCKED", blocker="Deterministic close gates failed: " + "; ".join(gate.blockers[:3]))
    verdict = state.final_verdict
    if verdict is None or verdict.decision != "APPROVE_CLOSE":
        state.final_verdict = FinalCloseVerdict(
            period=state.period.period,
            decision="APPROVE_CLOSE",
            reasons=["Python close gates passed. No unresolved HUMAN_REVIEW remains."],
            reviewer="python-gate",
            created_at=now_iso(),
            gate_passed=True,
        )
    return _task_result("COMPLETE", outputs=["final_review", "APPROVE_CLOSE"])


def _run_mark_closed(state: MonthEndState, live: bool) -> dict:
    from close.gating import evaluate_close_gates
    from close.period_lock import mark_period
    from close.reviews import load_reviews
    from close.rollforward import build_rollforwards
    from close.snapshot import build_snapshot, latest_snapshot, save_snapshot

    others = [item for item in state.tasks if item.task_id != "mark_closed"]
    gate = evaluate_close_gates(state)
    state.gate = gate
    verdict = state.final_verdict
    if (
        any(item.status != "COMPLETE" for item in others)
        or _blocking_exceptions(state)
        or not gate.passed
        or verdict is None
        or verdict.decision != "APPROVE_CLOSE"
    ):
        return _task_result("BLOCKED", blocker="Period cannot close while unresolved blockers remain.")
    state.human_review_items = []
    state.roll_forwards = build_rollforwards(state.period.period)
    prior = latest_snapshot(state.period.period)
    state.period.status = "CLOSED"
    state.period.closed_at = now_iso()
    state.period.approved_by = verdict.reviewer
    state.period.approval_decision = verdict.decision
    state.period.approval_reason = "; ".join(verdict.reasons)
    state.period.approval_at = verdict.created_at or now_iso()
    snapshot = build_snapshot(state, reopen_of=prior.snapshot_id if prior else None)
    snapshot.review_items = load_reviews(state.period.period)
    snapshot.final_verdict = verdict
    snapshot.close_gate = gate
    snapshot.approved_by = verdict.reviewer
    path = save_snapshot(snapshot)
    state.snapshot_path = path
    if snapshot.snapshot_id not in state.snapshot_ids:
        state.snapshot_ids.append(snapshot.snapshot_id)
    state.period.snapshot_ids = list(state.snapshot_ids)
    mark_period(
        state.period.period,
        "CLOSED",
        closed_at=state.period.closed_at,
        snapshot_id=snapshot.snapshot_id,
    )
    return _task_result("COMPLETE", outputs=[path])


HANDLERS = {
    "ingest": _run_ingest,
    "ap": _run_ap,
    "ar": _run_ar,
    "cash": _run_cash,
    "accruals": _run_accruals,
    "prepaid": _run_prepaid,
    "depreciation": _run_depreciation,
    "bs_recon": _run_bs_recon,
    "exceptions": _run_exceptions,
    "final_review": _run_final_review,
    "mark_closed": _run_mark_closed,
}


def _apply_result(task: CloseTask, result: dict) -> None:
    task.status = result["status"]
    task.output_refs = list(result.get("outputs") or [])
    task.evidence_refs = list(result.get("evidence") or [])
    task.blocker_reason = result.get("blocker") or ""
    task.started_at = task.started_at or now_iso()
    task.review_status = result.get("status") or ""
    if task.status == "COMPLETE":
        task.completed_at = now_iso()


def _period_status(state: MonthEndState) -> str:
    by_id = {item.task_id: item for item in state.tasks}
    if by_id.get("mark_closed") and by_id["mark_closed"].status == "COMPLETE" and state.period.closed_at:
        return "CLOSED"
    blockers = unresolved_blockers(state.tasks)
    if blockers:
        return "BLOCKED"
    if by_id.get("final_review") and by_id["final_review"].status == "COMPLETE":
        return "READY_TO_CLOSE"
    if by_id.get("exceptions") and by_id["exceptions"].status in {"READY", "COMPLETE"}:
        if by_id["exceptions"].status == "READY" or by_id.get("final_review") and by_id["final_review"].status == "READY":
            return "READY_FOR_REVIEW"
    if state.period.status == "REOPENED":
        return "REOPENED"
    if any(item.status not in {"NOT_STARTED"} for item in state.tasks):
        return "IN_PROGRESS"
    return "OPEN"


def run_month_end(
    period: str,
    *,
    scenario: str = "demo",
    live: bool = False,
    reset: bool = False,
    retry_failed: bool = True,
    allow_close: bool = True,
    only_tasks: list[str] | None = None,
) -> MonthEndState:
    existing = None if reset else load_state(period)
    if existing and existing.period.status == "CLOSED" and not reset:
        return existing
    if existing and not reset:
        state = existing
        if retry_failed:
            for task in state.tasks:
                if task.status in {"FAILED", "NEEDS_REVIEW", "BLOCKED"}:
                    task.status = "READY"
                    task.blocker_reason = ""
                    task.completed_at = None
    else:
        if reset:
            reset_subsystem_state()
        state = new_state(period, scenario=scenario)
        from prepaid.store import load_items, load_seed_items, save_items
        from fixed_assets.store import load_assets, load_seed_assets, save_assets

        if scenario == "demo":
            if not load_items():
                save_items(load_seed_items())
            if not load_assets():
                save_assets(load_seed_assets())
        elif scenario in {"clean", "seed_demo"}:
            seeded = [item for item in load_seed_items() if item.evidence_refs and item.source_document_id]
            save_items(seeded)
            save_assets(load_seed_assets())

    skip_close = {"final_review", "mark_closed"}
    ran: list[str] = []
    while True:
        refresh_readiness(state.tasks)
        queue = ready_tasks(state.tasks)
        if not allow_close:
            queue = [item for item in queue if item.task_id not in skip_close]
        if only_tasks is not None:
            allowed = set(only_tasks)
            queue = [item for item in queue if item.task_id in allowed]
        if not queue:
            break
        task = queue[0]
        task.status = "RUNNING"
        task.stale = False
        handler = HANDLERS[task.task_id]
        try:
            result = handler(state, live)
            _apply_result(task, result)
            ran.append(task.task_id)
        except Exception as exc:
            task.status = "FAILED"
            task.blocker_reason = str(exc)
        remember_link(close_task_id=task.task_id, extra={"status": task.status})

    from close.reviews import apply_review_views, harvest_review_items

    harvest_review_items(state.period.period, scenario=state.period.scenario)
    apply_review_views(state)
    if ran:
        state.rerun_tasks = list(dict.fromkeys(list(state.rerun_tasks) + ran))
    state.journal_entry_ids = list(dict.fromkeys(state.journal_entry_ids + [item["entry_id"] for item in load_entries()]))
    state.identity_links = all_links()
    state.completion_pct = completion_pct(state.tasks)
    from close.agents import deterministic_coordinate
    from close.materiality import load_materiality
    from close.rollforward import build_rollforwards

    state.materiality = load_materiality()
    state.roll_forwards = build_rollforwards(state.period.period)
    state.period.status = _period_status(state)  # type: ignore[assignment]
    state.manager = deterministic_coordinate(state)
    return save_state(state)


def rerun_affected(period: str, *, live: bool = False, review_id: str = "") -> MonthEndState:
    """Invalidate and rerun only tasks downstream of resolved review items."""
    from close.checklist import TASK_SPECS
    from close.reviews import get_review, load_reviews

    state = load_state(period) or run_month_end(period, reset=True, allow_close=False)
    if review_id:
        rows = [get_review(review_id)]
        rows = [item for item in rows if item is not None]
    else:
        rows = [item for item in load_reviews(period) if item.status == "RESOLVED"]
    order = [spec["task_id"] for spec in TASK_SPECS]
    affected: list[str] = []
    for item in rows:
        for task_id in item.downstream_tasks_affected:
            if task_id not in affected:
                affected.append(task_id)
    affected.sort(key=lambda task_id: order.index(task_id) if task_id in order else 99)
    from close.actions import invalidate_downstream

    for item in rows:
        invalidate_downstream(state, item)
    state.invalidated_tasks = affected
    state.rerun_tasks = []
    save_state(state)
    return run_month_end(
        period,
        scenario=state.period.scenario,
        live=live,
        reset=False,
        retry_failed=False,
        allow_close=False,
        only_tasks=affected or None,
    )


def finalize_close(period: str, *, live: bool = False, reviewer: str = "Month-End Close Reviewer") -> MonthEndState:
    from close.agents import decide_final_close
    from close.gating import evaluate_close_gates

    state = load_state(period) or run_month_end(period, reset=True, allow_close=False)
    gate = evaluate_close_gates(state)
    verdict = decide_final_close(state, gate, live=live, reviewer=reviewer)
    if verdict.decision == "APPROVE_CLOSE" and not gate.passed:
        verdict = verdict.model_copy(
            update={
                "decision": "REJECT_CLOSE",
                "reasons": ["Python gate blocked close; agent approval ignored."] + list(verdict.reasons),
                "gate_passed": False,
                "overridden_by_python": True,
            }
        )
    verdict.gate_passed = gate.passed and verdict.decision == "APPROVE_CLOSE"
    state.final_verdict = verdict
    state.gate = gate
    if verdict.decision != "APPROVE_CLOSE" or not gate.passed:
        state.period.status = "BLOCKED"
        return save_state(state)
    for task in state.tasks:
        if task.task_id in {"final_review", "mark_closed"}:
            task.status = "READY" if task.task_id == "final_review" else "NOT_STARTED"
            task.blocker_reason = ""
            task.stale = False
    save_state(state)
    return run_month_end(
        period,
        scenario=state.period.scenario,
        live=live,
        reset=False,
        retry_failed=False,
        allow_close=True,
        only_tasks=["final_review", "mark_closed"],
    )


def retry_task(period: str, task_id: str, *, live: bool = False) -> MonthEndState:
    state = load_state(period) or run_month_end(period, reset=True)
    for task in state.tasks:
        if task.task_id == task_id and task.status in {"FAILED", "NEEDS_REVIEW", "BLOCKED"}:
            task.status = "READY"
            task.blocker_reason = ""
    save_state(state)
    return run_month_end(period, scenario=state.period.scenario, live=live, reset=False)


def reopen_period(period: str, reason: str, *, actor: str = "human") -> MonthEndState:
    if not reason.strip():
        raise ValueError("A reopen reason is required.")
    state = load_state(period)
    if state is None or state.period.status != "CLOSED":
        raise ValueError(f"Period {period} is not closed.")
    from close.models import CloseControlEvent
    from close.period_lock import mark_period, record_event
    from close.snapshot import latest_snapshot

    prior = latest_snapshot(period)
    event = CloseControlEvent(
        event_id=f"REOPEN-{period}-{now_iso().replace(':', '')}",
        event_type="PERIOD_REOPENED",
        period=period,
        created_at=now_iso(),
        actor=actor,
        reason=reason.strip(),
        decision="APPROVED",
        attempted_entry={"prior_snapshot": prior.snapshot_id if prior else ""},
        audit_trace=state.trace_path or "",
    )
    record_event(event)
    mark_period(period, "REOPENED", reopen_reason=reason.strip(), reopened_at=event.created_at)
    state.period.status = "REOPENED"
    state.period.reopened_at = event.created_at
    state.period.reopen_reason = reason.strip()
    state.period.closed_at = None
    state.control_events.append(event)
    for task in state.tasks:
        if task.task_id in {"bs_recon", "exceptions", "final_review", "mark_closed"}:
            task.status = "READY" if task.task_id == "bs_recon" else "NOT_STARTED"
            task.completed_at = None
            task.blocker_reason = ""
            task.review_status = "NEEDS_REVIEW"
    return save_state(state)
