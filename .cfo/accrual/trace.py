from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from accrual.agent import accrual_agent
from accrual.estimation import EstimateContext, candidates_for, invoice_already_received
from accrual.models import (
    AccrualDecision,
    AgentSelection,
    CandidateEstimateView,
    JournalEntry,
    ReconciliationResult,
    TraceEvidence,
    TraceJournal,
    VendorDecisionTrace,
)
from accrual.report import method_label
from accrual.validate import status_label
from skills.loader import usage_from_agent

TRACES_ROOT = Path(__file__).resolve().parent.parent / "traces" / "accruals"


def vendor_slug(vendor: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", vendor.lower()).strip("_")


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_dir(period: str, run_id: str) -> Path:
    return TRACES_ROOT / period / run_id


def make_trace_id(period: str, run_id: str, vendor: str) -> str:
    return f"{period}/{run_id}/{vendor_slug(vendor)}"


def compact_invoice(invoice) -> dict:
    return {
        "invoice_id": invoice.invoice_id,
        "service_period": invoice.service_period,
        "amount": invoice.amount,
        "description": invoice.description,
        "po_id": invoice.po_id,
    }


def snapshot_evidence(context: EstimateContext) -> TraceEvidence:
    contract = context.contract.model_dump(mode="json") if context.contract else None
    usage = context.usage.model_dump(mode="json") if context.usage else None
    receipts = []
    for purchase_order, receipt in context.goods_receipts:
        row = receipt.model_dump(mode="json")
        row["po_id"] = purchase_order.po_id
        row["vendor"] = purchase_order.vendor
        receipts.append(row)
    return TraceEvidence(
        historical_invoices=[compact_invoice(item) for item in context.historical_invoices],
        current_invoices=[compact_invoice(item) for item in context.current_invoices],
        contract=contract,
        usage=usage,
        purchase_orders=[item.model_dump(mode="json") for item in context.purchase_orders],
        goods_receipts=receipts,
    )


def candidate_views(context: EstimateContext) -> list[CandidateEstimateView]:
    return [
        CandidateEstimateView(
            method=item.method,
            label=method_label(item.method),
            amount=item.amount,
            applicable=item.applicable,
        )
        for item in candidates_for(context)
    ]


def journal_view(entry: JournalEntry | None) -> TraceJournal | None:
    if entry is None:
        return None
    return TraceJournal(
        entry_id=entry.entry_id,
        debit_account=entry.debit.account,
        credit_account=entry.credit.account,
        amount=entry.debit.amount,
    )


def agent_selection_from(decision: AccrualDecision) -> AgentSelection:
    return AgentSelection(
        decision=status_label(decision.status),
        method=decision.estimation_method,
        amount=decision.estimated_amount,
        confidence=decision.confidence,
        reason=decision.reasoning_summary,
    )


def build_trace(
    *,
    context: EstimateContext,
    raw_decision: AccrualDecision,
    final: AccrualDecision,
    run_id: str,
    validation_errors: list[str],
    safety_rules: list[str],
    tools_called: list[str],
    discovery_trace_id: str | None = None,
    expectation_confidence: float | None = None,
    memory_lookup=None,
    written_memory_id: str | None = None,
) -> VendorDecisionTrace:
    from accrual.diagnostics import method_diagnostics
    from accrual.policy import preferred_candidate

    policy = preferred_candidate(context)
    warnings = method_diagnostics(
        agent_method=final.estimation_method,
        agent_status=final.status,
        context=context,
        policy=policy,
    )
    agree = None
    if final.status == "accrual_required" and policy and policy.method:
        agree = final.estimation_method == policy.method
    elif final.status != "accrual_required" and policy is None:
        agree = True
    return VendorDecisionTrace(
        trace_id=make_trace_id(context.period, run_id, context.vendor),
        vendor=context.vendor,
        period=context.period,
        invoice_received=invoice_already_received(context),
        evidence=snapshot_evidence(context),
        candidate_estimates=candidate_views(context),
        agent_selection=agent_selection_from(raw_decision),
        validation_errors=validation_errors,
        safety_rules_triggered=safety_rules,
        final_decision=final.status,
        final_method=final.estimation_method,
        final_amount=final.estimated_amount,
        confidence=final.confidence,
        rationale=final.reasoning_summary,
        journal_entry=journal_view(final.journal_entry),
        accrual_id=final.accrual_id,
        tools_called=tools_called,
        discovery_trace_id=discovery_trace_id,
        expectation_confidence=expectation_confidence,
        estimate_confidence=final.confidence,
        agent=usage_from_agent(accrual_agent),
        policy_method=policy.method if policy else None,
        policy_amount=policy.amount if policy else None,
        policy_agreement=agree,
        diagnostic_warnings=warnings,
        memory_lookup=memory_lookup,
        written_memory_id=written_memory_id,
    )


def save_trace(trace: VendorDecisionTrace, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{vendor_slug(trace.vendor)}.json"
    path.write_text(trace.model_dump_json(indent=2) + "\n")
    return path


def save_period_report(report, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "_period.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    return path


def save_discovery(result, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{vendor_slug(result.vendor)}.json"
    path.write_text(result.model_dump_json(indent=2) + "\n")
    return path


def save_reconciliation(result: ReconciliationResult, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{vendor_slug(result.vendor)}.json"
    path.write_text(json.dumps(result.model_dump(mode="json"), indent=2) + "\n")
    return path
