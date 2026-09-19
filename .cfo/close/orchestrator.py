"""AP / accrual / payment-schedule packet.

This is not the period-close engine. Month-end close lives in
``close.month_end`` / ``close.engine``. ``decide_ap`` is reused by the
canonical close checklist. ``run_cfo_close`` remains for AP/schedule
invariant tests and does not write period status, reviews, or locks.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from accrual.trace import new_run_id
from accrual.workflow import run_accrual_workflow, run_reconcile_workflow
from close.models import (
    APCloseResult,
    AuditRefs,
    CloseException,
    CloseRun,
    IntegrationSummary,
)
from close.safeguards import apply_close_safeguards, assert_close_invariants
from invoice_ingestion.workflow import ingest_invoices
from models import PaymentAuditResult, ScheduleTrace
from scheduling.cash import (
    apply_cash_and_policy_net,
    compute_metrics,
    load_cash_position,
    policy_eligible_for_pool,
    spendable_cash,
)
from scheduling.pool import add_approved, save_pool
from scheduling.workflow import candidates_from_pool, run_schedule_workflow
from tools import all_invoices, collect_case_evidence, load_invoice
from workflow import _blocking_approve_violations

CLOSE_DIR = Path(__file__).resolve().parent.parent / "runs" / "close"
FEATURED_AP = ("INV-001", "INV-016")
DEMO_RECONCILE = ("Aether Compute",)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _policy_ap_decision(invoice_id: str) -> APCloseResult:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Unknown invoice {invoice_id}")
    evidence = collect_case_evidence(invoice_id)
    violations = _blocking_approve_violations(evidence)
    hold = bool(violations) or not policy_eligible_for_pool(invoice_id)
    return APCloseResult(
        invoice_id=invoice_id,
        vendor=invoice.vendor,
        amount=invoice.amount,
        decision="HOLD" if hold else "APPROVE",
        exceptions=list(evidence.exception_types),
        source="ap_policy",
        ap_decision_id=f"ap-policy/{invoice_id}",
    )


def _live_ap_decision(invoice_id: str) -> APCloseResult:
    from workflow import run_ap_workflow

    invoice = load_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Unknown invoice {invoice_id}")
    trace = run_ap_workflow(invoice_id)
    return APCloseResult(
        invoice_id=invoice_id,
        vendor=invoice.vendor,
        amount=invoice.amount,
        decision=trace.final.decision,  # type: ignore[arg-type]
        exceptions=list(trace.deterministic_evidence.exception_types),
        source="ap_workflow",
        trace_path=trace.trace_path,
        ap_decision_id=trace.trace_path or invoice_id,
    )


def decide_ap(
    invoice_id: str,
    *,
    live: bool,
    featured: set[str],
) -> APCloseResult:
    """Live AP only for featured invoices. Everyone else uses the AP hard policy."""
    if live and invoice_id in featured:
        return _live_ap_decision(invoice_id)
    return _policy_ap_decision(invoice_id)


def _run_integrations() -> list[IntegrationSummary]:
    from integrations.demo import process_provider
    from integrations.store import reset_integration_state

    reset_integration_state()
    rows: list[IntegrationSummary] = []
    for name in ("gmail", "outlook", "xero", "coupa", "netsuite", "stripe", "adyen"):
        for item in process_provider(name):
            rows.append(
                IntegrationSummary(
                    provider=item.provider,
                    action=item.action,
                    status=item.status,
                    invoice_numbers=list(item.invoice_numbers),
                    payout_id=item.payout_id,
                    duplicate=item.duplicate,
                    message=item.message,
                )
            )
    return rows


def _run_schedule(*, live: bool) -> ScheduleTrace:
    if live:
        return run_schedule_workflow()
    cash = load_cash_position()
    candidates = candidates_from_pool()
    if not candidates:
        raise ValueError("Approved invoice pool is empty after AP close.")
    plan = apply_cash_and_policy_net(candidates, [item.invoice_id for item in candidates], cash)
    metrics = compute_metrics(candidates, plan, cash)
    return ScheduleTrace(
        as_of_date=cash.as_of_date,
        started_at=_now(),
        cash=cash,
        spendable_cash=spendable_cash(cash),
        candidates=candidates,
        plan=plan,
        metrics=metrics,
        audit=PaymentAuditResult(passed=plan.reserve_ok, findings=["Deterministic cash/policy net"]),
    )


def _exceptions(state: CloseRun) -> list[CloseException]:
    rows: list[CloseException] = []
    for item in state.ap_results:
        if item.decision == "HOLD":
            reason = item.exceptions[0] if item.exceptions else "held"
            rows.append(CloseException(kind="ap_hold", ref=item.invoice_id, detail=f"{item.vendor}: {reason}"))
    if state.accrual:
        for item in state.accrual.uncertain_items:
            rows.append(
                CloseException(
                    kind="accrual_insufficient",
                    ref=item.vendor,
                    detail=f"{item.vendor}: insufficient accrual evidence",
                )
            )
    for warning in state.safeguards:
        rows.append(CloseException(kind="safeguard", ref=warning.split(":")[-1], detail=warning))
    return rows


def run_cfo_close(
    period: str,
    *,
    live: bool | None = None,
    featured_ap: tuple[str, ...] | None = None,
    reconcile_vendors: tuple[str, ...] = (),
    use_agent_accrual: bool | None = None,
) -> CloseRun:
    live = bool(os.environ.get("OPENAI_API_KEY")) if live is None else live
    featured = set(featured_ap if featured_ap is not None else (FEATURED_AP if live else ()))
    use_agent_accrual = live if use_agent_accrual is None else use_agent_accrual
    close_id = new_run_id()
    started = _now()

    print(f"CFO close {period} ({close_id})", flush=True)
    inbox = list(all_invoices())
    invoice_ids = [item.invoice_id for item in inbox]

    print("1. Ingest available financial documents", flush=True)
    ingestion = ingest_invoices(period=period, use_llm=False, forward_to_ap=False, run_ap=False)

    print("2. Replay provider integrations (cash events stay off the AP inbox)", flush=True)
    integrations = _run_integrations()

    print(f"3. AP validation for {len(invoice_ids)} received invoices", flush=True)
    save_pool([])
    ap_results: list[APCloseResult] = []
    for invoice_id in invoice_ids:
        result = decide_ap(invoice_id, live=live, featured=featured)
        if result.decision == "APPROVE":
            add_approved(invoice_id, source=result.source, confidence=None)
        ap_results.append(result)

    print("4. Accrual discovery and booking", flush=True)
    accrual = run_accrual_workflow(period, reset=True, use_agent=use_agent_accrual)

    approved_ids = [item.invoice_id for item in ap_results if item.decision == "APPROVE"]
    held_ids = [item.invoice_id for item in ap_results if item.decision == "HOLD"]
    state = CloseRun(
        period=period,
        close_id=close_id,
        started_at=started,
        invoices_received=len(invoice_ids),
        invoice_ids=invoice_ids,
        ingestion_canonical=len(ingestion.canonical_invoices),
        ingestion_duplicates=ingestion.duplicates_removed,
        integrations=integrations,
        ap_results=ap_results,
        approved_ids=approved_ids,
        held_ids=held_ids,
        discovery=accrual.discovery,
        accrual=accrual,
        spendable_cash=spendable_cash(),
        audit=AuditRefs(
            close_id=close_id,
            ingestion_trace=ingestion.trace_path,
            ap_traces=[item.trace_path for item in ap_results if item.trace_path],
            accrual_trace_dir=accrual.trace_dir,
        ),
    )
    state.safeguards = apply_close_safeguards(state)

    print("5. Payment scheduling from the approved pool only", flush=True)
    payment = _run_schedule(live=live)
    state.payment = payment
    state.audit.payment_plan_trace = payment.trace_path

    if reconcile_vendors:
        print("6. Reconcile later invoices for featured accruals", flush=True)
        state.reconciliations = run_reconcile_workflow(period, vendors=list(reconcile_vendors))
        state.audit.reconciliation_traces = [
            item.reconciliation_trace_id or item.trace_id or ""
            for item in state.reconciliations
            if item.reconciliation_trace_id or item.trace_id
        ]

    from calendar import monthrange

    from ar.context import ar_close_snapshot

    if len(period) == 7:
        year, month = int(period[:4]), int(period[5:7])
        period_end = f"{period}-{monthrange(year, month)[1]:02d}"
    else:
        period_end = period
    state.ar = ar_close_snapshot(period_end)

    state.exceptions = _exceptions(state)
    state.safeguards = list(dict.fromkeys(state.safeguards + apply_close_safeguards(state)))
    assert_close_invariants(state)

    CLOSE_DIR.mkdir(parents=True, exist_ok=True)
    path = CLOSE_DIR / f"{period}-{close_id}.json"
    path.write_text(state.model_dump_json(indent=2) + "\n")
    state.trace_path = str(path)
    return state


def run_demo_close(period: str = "2026-09") -> CloseRun:
    """Connected story using the same orchestrator and real workflows."""
    live = bool(os.environ.get("OPENAI_API_KEY"))
    return run_cfo_close(
        period,
        live=live,
        featured_ap=FEATURED_AP if live else (),
        reconcile_vendors=DEMO_RECONCILE,
        use_agent_accrual=live,
    )
