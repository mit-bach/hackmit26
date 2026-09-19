"""Compare the live Accrual Agent to the deterministic evidence-type policy."""

from __future__ import annotations

from accrual.diagnostics import historical_method_mapes, method_diagnostics
from accrual.estimation import candidates_for
from accrual.ledger import isolated_ledger
from accrual.models import ComparisonRecord, ComparisonReport
from accrual.policy import preferred_candidate
from accrual.store import build_estimate_context
from accrual.trace import TRACES_ROOT, new_run_id
from accrual.workflow import DEMO_VENDORS, _run_vendor, _skip_received
from accrual.discovery import discover_vendor


def compare_vendor(vendor: str, period: str, run_id: str = "") -> ComparisonRecord:
    context = build_estimate_context(vendor, period)
    policy = preferred_candidate(context)
    applicable = [item.method for item in candidates_for(context) if item.applicable]
    discovery = discover_vendor(vendor, period, run_id=run_id or "compare")
    run_id = run_id or new_run_id()
    if discovery.invoice_received:
        decision, trace = _skip_received(discovery, run_id)
    else:
        decision, trace = _run_vendor(vendor, period, run_id, discovery=discovery)
    warnings = list(trace.diagnostic_warnings)
    if not warnings:
        warnings = method_diagnostics(
            agent_method=decision.estimation_method,
            agent_status=decision.status,
            context=context,
            policy=policy,
        )
    agree = None
    if decision.status == "accrual_required" and policy and policy.method:
        agree = decision.estimation_method == policy.method and decision.estimated_amount == policy.amount
    elif decision.status != "accrual_required" and policy is None:
        agree = True
    mapes = historical_method_mapes()
    return ComparisonRecord(
        vendor=vendor,
        period=period,
        policy_method=policy.method if policy else None,
        policy_amount=policy.amount if policy else None,
        agent_method=decision.estimation_method,
        agent_amount=decision.estimated_amount,
        agent_status=decision.status,
        agree=agree,
        diagnostic_warnings=warnings,
        candidate_methods=applicable,
        agent_mape=mapes.get(decision.estimation_method or ""),
        policy_mape=mapes.get(policy.method) if policy and policy.method else None,
        discovery_trace_id=discovery.discovery_trace_id,
        accrual_trace_id=trace.trace_id,
    )


def compare_period(period: str, vendors: list[str] | None = None) -> ComparisonReport:
    vendors = vendors or DEMO_VENDORS
    run_id = new_run_id()
    directory = TRACES_ROOT / "compare" / run_id
    rows: list[ComparisonRecord] = []
    with isolated_ledger(directory / "ledger"):
        for vendor in vendors:
            rows.append(compare_vendor(vendor, period, run_id=f"{run_id}-{vendor}"))
    report = ComparisonReport(
        period=period,
        comparisons=rows,
        agreements=sum(1 for item in rows if item.agree is True),
        disagreements=sum(1 for item in rows if item.agree is False),
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "results.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    report.trace_path = str(path)
    return report
