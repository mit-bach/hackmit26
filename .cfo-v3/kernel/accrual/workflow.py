from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents import RunHooks
from agents.tool_context import ToolContext

from agent import run_agent
from accrual.agent import accrual_agent
from accrual.estimation import candidates_for, compute_estimate, invoice_already_received
from accrual.ledger import create_accrual, journal_for, reconcile_accrual, reset_period, void_open_accrual
from accrual.cutoff import data_cutoff
from accrual.discovery import discover_period, missing_bill_candidates, received_expenses
from accrual.models import AccrualDecision, AccrualPeriodReport, DiscoveryResult, ReconciliationResult, VendorDecisionTrace
from accrual.store import build_estimate_context, later_invoices_for
from accrual.trace import (
    build_trace,
    make_trace_id,
    new_run_id,
    run_dir,
    save_discovery,
    save_period_report,
    save_reconciliation,
    save_trace,
    vendor_slug,
)
from accrual.validate import failed_safe_decision, validate_agent_decision
from memory.format import format_precedents
from memory.hooks import apply_accrual_precedent, lookup_for_accrual, write_accrual_memory

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"
MAX_AGENT_TURNS = 12
DEMO_PERIOD = "2026-09"
DEMO_VENDORS = [
    "Aether Compute",
    "Harbor Electric",
    "Helios Hardware",
    "Amazon Web Services",
    "NewForge Consulting",
]


class ToolCallRecorder(RunHooks):
    """Record tools the agent actually called. Does not print."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def on_tool_start(self, context, agent, tool) -> None:
        args = ""
        if isinstance(context, ToolContext) and context.tool_arguments:
            args = str(context.tool_arguments)
        label = f"{tool.name}({args})" if args else tool.name
        self.calls.append(label)


def _force_no_accrual(decision: AccrualDecision, invoice_ids: list[str]) -> AccrualDecision:
    return decision.model_copy(
        update={
            "status": "no_accrual_needed",
            "estimated_amount": None,
            "estimation_method": None,
            "journal_entry": None,
            "accrual_id": None,
            "reasoning_summary": (
                "Current-period invoice already received "
                f"({', '.join(invoice_ids)}). No accrual."
            ),
        }
    )


def _force_goods_receipt(vendor: str, period: str, decision: AccrualDecision) -> AccrualDecision:
    context = build_estimate_context(vendor, period)
    candidate = compute_estimate(context, "goods_receipt")
    if not candidate.applicable or candidate.amount is None:
        return decision
    return decision.model_copy(
        update={
            "status": "accrual_required",
            "estimated_amount": candidate.amount,
            "estimation_method": "goods_receipt",
            "expense_account": context.expense_account or decision.expense_account,
            "confidence": max(decision.confidence, 0.9),
            "reasoning_summary": (
                "Goods were received and no invoice exists, so the receipt amount was accrued."
            ),
        }
    )


def _book(decision: AccrualDecision, trace_id: str, discovery_trace_id: str = "") -> AccrualDecision:
    if decision.status != "accrual_required" or not decision.estimation_method:
        return decision.model_copy(update={"journal_entry": None, "accrual_id": None})
    if decision.estimated_amount is None or decision.estimated_amount <= 0:
        return decision.model_copy(
            update={
                "status": "insufficient_evidence",
                "estimated_amount": None,
                "journal_entry": None,
                "accrual_id": None,
            }
        )
    context = build_estimate_context(decision.vendor, decision.period)
    candidate = compute_estimate(context, decision.estimation_method)
    if not candidate.applicable or candidate.amount is None:
        return decision.model_copy(
            update={
                "status": "insufficient_evidence",
                "estimated_amount": None,
                "journal_entry": None,
                "accrual_id": None,
                "reasoning_summary": (
                    decision.reasoning_summary
                    + f" Python rejected method {decision.estimation_method}."
                ).strip(),
            }
        )
    record = create_accrual(
        vendor=decision.vendor,
        period=decision.period,
        amount=candidate.amount,
        method=decision.estimation_method,
        confidence=decision.confidence,
        evidence=decision.evidence,
        reasoning_summary=decision.reasoning_summary,
        expense_account=context.expense_account,
        trace_id=trace_id,
        discovery_trace_id=discovery_trace_id,
    )
    return decision.model_copy(
        update={
            "estimated_amount": candidate.amount,
            "expense_account": context.expense_account,
            "accrual_id": record.accrual_id,
            "journal_entry": journal_for(record.journal_entry_id),
            "trace_id": trace_id,
        }
    )


def finalize_vendor_close(
    vendor: str,
    period: str,
    raw_decision: AccrualDecision,
    run_id: str,
    tools_called: list[str] | None = None,
    discovery: DiscoveryResult | None = None,
    memory_lookup=None,
) -> tuple[AccrualDecision, VendorDecisionTrace]:
    """Apply validation and deterministic safety rules to a raw agent decision."""
    context = build_estimate_context(vendor, period)
    lookup = memory_lookup or lookup_for_accrual(vendor, period)
    candidates = candidates_for(context)
    raw = raw_decision.model_copy(update={"vendor": vendor, "period": period, "journal_entry": None})
    errors = validate_agent_decision(raw, candidates)
    decision = failed_safe_decision(raw, errors) if errors else raw
    safety: list[str] = []

    if invoice_already_received(context):
        decision = _force_no_accrual(decision, [item.invoice_id for item in context.current_invoices])
        safety.append("invoice_already_received")
    else:
        receipt = compute_estimate(context, "goods_receipt")
        if receipt.applicable and receipt.amount and decision.status != "accrual_required":
            decision = _force_goods_receipt(vendor, period, decision)
            safety.append("unbilled_goods_receipt")

    if decision.status in {"no_accrual_needed", "insufficient_evidence"}:
        void_open_accrual(vendor, period)
        decision = decision.model_copy(update={"journal_entry": None, "accrual_id": None, "estimated_amount": None})
    else:
        decision = _book(
            decision,
            make_trace_id(period, run_id, vendor),
            discovery.discovery_trace_id if discovery else "",
        )

    lookup = apply_accrual_precedent(context, decision.estimation_method, decision.status, lookup)
    if lookup.precedent_used and lookup.retrieved:
        prior_id = lookup.retrieved[0]
        decision = decision.model_copy(
            update={
                "reasoning_summary": (
                    f"{decision.reasoning_summary} Prior {prior_id} used the same "
                    f"{decision.estimation_method} methodology; current evidence still supports it."
                ).strip(),
                "evidence": list(dict.fromkeys(list(decision.evidence) + [prior_id])),
            }
        )
    written = write_accrual_memory(decision, trace_id=make_trace_id(period, run_id, vendor))

    trace = build_trace(
        context=context,
        raw_decision=raw_decision.model_copy(update={"vendor": vendor, "period": period}),
        final=decision,
        run_id=run_id,
        validation_errors=errors,
        safety_rules=safety,
        tools_called=tools_called or [],
        discovery_trace_id=discovery.discovery_trace_id if discovery else None,
        expectation_confidence=discovery.expectation_confidence if discovery else None,
        memory_lookup=lookup,
        written_memory_id=written[0].decision_id if written is not None else None,
    )
    return decision.model_copy(
        update={
            "trace_id": trace.trace_id,
            "discovery_trace_id": discovery.discovery_trace_id if discovery else None,
        }
    ), trace


def _safe_raw_decision(vendor: str, period: str, exc: Exception) -> AccrualDecision:
    return AccrualDecision(
        vendor=vendor,
        period=period,
        status="insufficient_evidence",
        estimated_amount=None,
        confidence=0,
        reasoning_summary=f"Agent output failed safely: {exc}",
        evidence=[],
    )


def _skip_received(found: DiscoveryResult, run_id: str) -> tuple[AccrualDecision, VendorDecisionTrace]:
    raw = AccrualDecision(
        vendor=found.vendor,
        period=found.period,
        status="no_accrual_needed",
        estimated_amount=None,
        confidence=found.expectation_confidence,
        reasoning_summary=found.reason,
        evidence=[signal.detail for signal in found.signals],
        discovery_trace_id=found.discovery_trace_id,
    )
    return finalize_vendor_close(found.vendor, found.period, raw, run_id, discovery=found)


def _run_vendor(
    vendor: str,
    period: str,
    run_id: str,
    discovery: DiscoveryResult | None = None,
) -> tuple[AccrualDecision, VendorDecisionTrace]:
    signal_line = ""
    if discovery:
        signal_line = (
            f"Discovery: expected={discovery.expense_expected} "
            f"missing={discovery.missing_bill_candidate} "
            f"expectation_confidence={discovery.expectation_confidence:.2f}. "
            f"{discovery.reason}"
        )
    recorder = ToolCallRecorder()
    lookup = lookup_for_accrual(vendor, period)
    memory_block = format_precedents(lookup)
    try:
        decision = run_agent(
            accrual_agent,
            (
                f"Close period {period} for vendor {vendor}.\n"
                "Decide accrual_required, no_accrual_needed, or insufficient_evidence.\n"
                f"{signal_line}\n"
                f"{memory_block}\n"
                "Use tools to load evidence and Python estimate candidates. "
                "Copy the Python amount exactly. Do not invent amounts."
            ),
            max_turns=MAX_AGENT_TURNS,
            hooks=recorder,
        )
        if not isinstance(decision, AccrualDecision):
            raise TypeError(f"Accrual Agent returned {type(decision).__name__}, not AccrualDecision")
    except Exception as exc:
        decision = _safe_raw_decision(vendor, period, exc)
    return finalize_vendor_close(
        vendor, period, decision, run_id, recorder.calls, discovery=discovery, memory_lookup=lookup
    )


def _run_policy_vendor(
    vendor: str,
    period: str,
    run_id: str,
    discovery: DiscoveryResult | None = None,
) -> tuple[AccrualDecision, VendorDecisionTrace]:
    """Book from the evidence-type policy. Used by tests and deterministic close."""
    from accrual.policy import preferred_candidate

    context = build_estimate_context(vendor, period)
    candidate = preferred_candidate(context)
    if candidate and candidate.amount is not None:
        raw = AccrualDecision(
            vendor=vendor,
            period=period,
            status="accrual_required",
            estimated_amount=candidate.amount,
            confidence=discovery.expectation_confidence if discovery else 0.85,
            estimation_method=candidate.method,
            evidence=[candidate.rationale],
            reasoning_summary=candidate.rationale,
            discovery_trace_id=discovery.discovery_trace_id if discovery else None,
        )
    else:
        raw = AccrualDecision(
            vendor=vendor,
            period=period,
            status="insufficient_evidence",
            estimated_amount=None,
            confidence=discovery.expectation_confidence if discovery else 0,
            reasoning_summary=(
                discovery.reason if discovery else "No applicable Python estimate candidate."
            ),
            evidence=[signal.detail for signal in discovery.signals] if discovery else [],
            discovery_trace_id=discovery.discovery_trace_id if discovery else None,
        )
    return finalize_vendor_close(vendor, period, raw, run_id, discovery=discovery)


def _save_legacy_report(report: AccrualPeriodReport) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"accrual-{report.period}-{stamp}.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    return path


def run_accrual_workflow(
    period: str,
    reset: bool = True,
    vendors: list[str] | None = None,
    run_id: str | None = None,
    use_agent: bool = True,
    hide_period_invoices: bool = False,
) -> AccrualPeriodReport:
    run_id = run_id or new_run_id()
    with data_cutoff(period, hide_period_invoices=hide_period_invoices, allow_later_invoices=False):
        return _run_accrual_workflow(
            period,
            reset=reset,
            vendors=vendors,
            run_id=run_id,
            use_agent=use_agent,
        )


def _run_accrual_workflow(
    period: str,
    reset: bool,
    vendors: list[str] | None,
    run_id: str,
    use_agent: bool,
) -> AccrualPeriodReport:
    discovery = discover_period(period, run_id=run_id)
    if vendors:
        wanted = {name.lower() for name in vendors}
        ordered = []
        by_name = {item.vendor.lower(): item for item in discovery.results}
        for name in vendors:
            found = by_name.get(name.lower())
            if found:
                ordered.append(found)
        extras = [item for item in discovery.results if item.vendor.lower() in wanted and item not in ordered]
        filtered = ordered + extras
        discovery = discovery.model_copy(
            update={
                "results": filtered,
                "expected_count": sum(1 for item in filtered if item.expense_expected),
                "invoices_received_count": sum(1 for item in filtered if item.invoice_received),
                "missing_count": sum(1 for item in filtered if item.missing_bill_candidate),
            }
        )

    if reset:
        reset_period(period)

    directory = run_dir(period, run_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "_discovery.json").write_text(discovery.model_dump_json(indent=2) + "\n")
    for item in discovery.results:
        save_discovery(item, directory / "discovery")

    missing = missing_bill_candidates(discovery)
    received = received_expenses(discovery)
    print(
        f"Closing {period} — discovered {discovery.expected_count} expected, "
        f"{discovery.invoices_received_count} already invoiced, "
        f"{discovery.missing_count} missing bills\n",
        flush=True,
    )

    decisions: list[AccrualDecision] = []
    traces: list[VendorDecisionTrace] = []

    for item in received:
        print(f"Skipping {item.vendor} — invoice already received", flush=True)
        decision, trace = _skip_received(item, run_id)
        save_trace(trace, directory)
        decisions.append(decision)
        traces.append(trace)

    for item in missing:
        print(f"Estimating missing bill: {item.vendor}...", flush=True)
        runner = _run_vendor if use_agent else _run_policy_vendor
        decision, trace = runner(item.vendor, period, run_id, discovery=item)
        save_trace(trace, directory)
        decisions.append(decision)
        traces.append(trace)

    created = [item for item in decisions if item.status == "accrual_required"]
    skipped = [item for item in decisions if item.status == "no_accrual_needed"]
    uncertain = [item for item in decisions if item.status == "insufficient_evidence"]
    total = round(sum(item.estimated_amount or 0 for item in created), 2)
    ranked = sorted(created, key=lambda item: item.estimated_amount or 0, reverse=True)

    report = AccrualPeriodReport(
        period=period,
        vendors_reviewed=len(decisions),
        accruals_created=created,
        no_accrual_needed=skipped,
        uncertain_items=uncertain,
        total_accrued_expense=total,
        traces=traces,
        discovery=discovery,
        ranked_missing=ranked,
        trace_dir=str(directory),
    )
    report.trace_path = str(save_period_report(report, directory))
    _save_legacy_report(report)
    return report


def run_reconcile_workflow(
    period: str,
    vendors: list[str] | None = None,
    run_id: str | None = None,
) -> list[ReconciliationResult]:
    from accrual.ledger import get_open_accruals

    run_id = run_id or new_run_id()
    directory = run_dir(period, run_id) / "reconcile"
    wanted = {name.lower() for name in vendors} if vendors else None
    results: list[ReconciliationResult] = []
    open_rows = get_open_accruals(period=period)
    if wanted:
        open_rows = [item for item in open_rows if item.vendor.lower() in wanted]

    if not open_rows:
        print("No open accruals to reconcile.", flush=True)
        return []

    for accrual in open_rows:
        later = later_invoices_for(accrual.vendor, accrual.period)
        if not later:
            print(f"{accrual.vendor}: still open — no later invoice\n", flush=True)
            continue
        invoice = later[0]
        result = reconcile_accrual(accrual.accrual_id, invoice.invoice_id, invoice.amount)
        result = result.model_copy(
            update={
                "reconciliation_trace_id": f"{period}/{run_id}/reconcile/{vendor_slug(accrual.vendor)}",
            }
        )
        save_reconciliation(result, directory)
        results.append(result)
    return results


def run_demo(period: str = DEMO_PERIOD):
    """Discover → estimate → book → measure → reconcile, using the normal workflows."""
    from accrual.backtest import run_backtest
    from accrual.discovery import discover_period

    run_id = new_run_id()
    with data_cutoff(period, hide_period_invoices=False, allow_later_invoices=False):
        discovery = discover_period(period, run_id=run_id)
    report = run_accrual_workflow(period, reset=True, vendors=DEMO_VENDORS, run_id=run_id)
    backtest = run_backtest()
    results = run_reconcile_workflow(period, vendors=["Aether Compute"], run_id=f"{run_id}-reconcile")
    return report, results, discovery, backtest
