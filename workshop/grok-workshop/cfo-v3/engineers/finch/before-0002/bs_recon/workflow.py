from __future__ import annotations

from close.context import remember_link
from close.dates import money, now_iso
from bs_recon.agent import bs_preparer, bs_reviewer, deterministic_prepare, deterministic_review
from bs_recon.engine import classify_packet, status_for
from bs_recon.models import BalanceSheetReconciliation, ReconRun, ReconTrace
from bs_recon.packets import build_packets
from bs_recon.store import save_reconciliation, save_trace
from bs_recon.tools import bind_packets
from skills.loader import usage_from_agent


def _decide(packet, *, use_agent: bool):
    if use_agent:
        from agent import run_agent

        preparer = run_agent(
            bs_preparer,
            f"Prepare the {packet.account_id} reconciliation for {packet.period}.",
        )
        reviewer = run_agent(
            bs_reviewer,
            (
                f"Review {packet.account_id}. Preparer finding={preparer.finding} "
                f"status={preparer.status}. {preparer.explanation}"
            ),
        )
        return preparer, reviewer, True
    preparer = deterministic_prepare(packet)
    return preparer, deterministic_review(packet, preparer), False


def run_balance_sheet_reconciliations(
    period: str,
    *,
    use_agent: bool = False,
    ap_results: list | None = None,
    scenario: str = "demo",
) -> ReconRun:
    packets = build_packets(period, ap_results=ap_results, scenario=scenario)
    bind_packets(period, packets)
    rows = []
    traces = []
    exceptions = []
    used_agent = False
    signed = 0
    for packet in packets:
        finding = classify_packet(packet)
        preparer, reviewer, live = _decide(packet, use_agent=use_agent)
        used_agent = used_agent or live
        if preparer.finding != finding:
            preparer = preparer.model_copy(update={"finding": finding, "status": status_for(finding)})
        status = status_for(finding)
        if reviewer.sign_off and finding in {"exact_match", "explained_timing_difference"}:
            status = "SIGNED_OFF"
            signed += 1
        elif finding == "explained_timing_difference":
            status = "EXPLAINED_DIFFERENCE"
        elif reviewer.decision == "REQUEST_EVIDENCE":
            status = "BLOCKED"
        elif reviewer.decision in {"ESCALATE", "REJECT"}:
            status = "HUMAN_REVIEW"
        recon = BalanceSheetReconciliation(
            reconciliation_id=f"BSR-{period}-{packet.account_id.replace(' ', '')}",
            period=period,
            account_id=packet.account_id,
            account_name=packet.account_name,
            ledger_balance=money(packet.ledger_balance),
            evidence_balance=money(packet.evidence_balance),
            difference=money(packet.ledger_balance - packet.evidence_balance),
            status=status,  # type: ignore[arg-type]
            evidence_refs=list(packet.evidence_refs),
            reconciling_items=list(packet.reconciling_items),
            explanation=preparer.explanation,
            finding=finding,
            created_at=now_iso(),
            reviewed_at=now_iso() if reviewer else None,
            ledger_source=packet.ledger_source,
            calculations=dict(packet.calculations),
            review_decision=reviewer.decision,
            supporting_balance=money(packet.evidence_balance),
            supporting_source=packet.evidence_source,
            review_status=reviewer.decision,
            blocking_items=[item.item_id for item in packet.reconciling_items if item.classification == "unexplained_difference"],
        )
        save_reconciliation(recon)
        remember_link(
            account_id=packet.account_id,
            reconciliation_id=recon.reconciliation_id,
            extra={"finding": finding, "status": status},
        )
        trace = ReconTrace(
            reconciliation_id=recon.reconciliation_id,
            period=period,
            account_id=packet.account_id,
            packet=packet,
            preparer=preparer,
            reviewer=reviewer,
            final=recon,
            agents=[usage_from_agent(bs_preparer), usage_from_agent(bs_reviewer)] if live else [],
            used_agent=live,
        )
        save_trace(trace)
        rows.append(recon)
        traces.append(trace)
        if status in {"HUMAN_REVIEW", "BLOCKED"}:
            exceptions.append(
                f"{packet.account_id}: {recon.explanation} "
                f"(difference {recon.difference:,.2f})"
            )
    return ReconRun(
        period=period,
        reconciliations=rows,
        traces=traces,
        exceptions=exceptions,
        signed_off=signed,
        used_agent=used_agent,
    )
