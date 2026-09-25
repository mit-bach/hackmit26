from __future__ import annotations

from agents import Agent

from bs_recon.engine import can_sign_off, classify_packet, status_for
from bs_recon.models import ReconDecision, ReconPacket, ReconReview
from bs_recon.tools import get_reconciliation_packet, list_reconciling_items

RECON_TOOLS = [get_reconciliation_packet, list_reconciling_items]

SAFETY = """
Safety rules:
- Never invent ledger balances, evidence amounts, or reconciling items.
- Never silently force a reconciliation to match.
- Copy Python findings when the packet is exact, missing evidence, or arithmetically inconsistent.
- Escalate unexplained differences. Do not relabel them as timing without a Python timing item.
""".strip()

bs_preparer = Agent(
    name="Balance Sheet Reconciliation Preparer",
    instructions="""
You prepare a balance-sheet reconciliation from a Python packet.

Use the packet's ledger balance, evidence balance, and reconciling items.
Classify the difference. If evidence is missing, do not sign off.
If the difference is unexplained, escalate to human review.
""".strip() + "\n\n" + SAFETY,
    tools=RECON_TOOLS,
    output_type=ReconDecision,
)

bs_reviewer = Agent(
    name="Balance Sheet Reconciliation Reviewer",
    instructions="""
You independently review a balance-sheet reconciliation.

Inspect the packet, not just the preparer narrative.
Approve and allow sign-off only for exact matches or explained timing differences
that Python already supports. Reject or request evidence when support is missing.
Escalate unexplained differences. Never force a match.
""".strip() + "\n\n" + SAFETY,
    tools=RECON_TOOLS,
    output_type=ReconReview,
)


def deterministic_prepare(packet: ReconPacket) -> ReconDecision:
    finding = classify_packet(packet)
    status = status_for(finding)
    escalate = finding in {
        "unexplained_difference",
        "missing_evidence",
        "stale_evidence",
        "duplicate_support",
        "arithmetic_inconsistency",
    }
    explanations = {
        "exact_match": "Ledger equals independent evidence.",
        "explained_timing_difference": "The difference is fully supported by timing reconciling items.",
        "unexplained_difference": "An unexplained difference remains. Do not force a match.",
        "missing_evidence": "Supporting documents are missing.",
        "stale_evidence": "Evidence is stale relative to the close date.",
        "duplicate_support": "The same support was used more than once.",
        "arithmetic_inconsistency": "Reconciling items do not bridge ledger to evidence.",
    }
    return ReconDecision(
        account_id=packet.account_id,
        finding=finding,
        status=status,  # type: ignore[arg-type]
        explanation=explanations[finding],
        confidence=0.95 if finding == "exact_match" else 0.7,
        escalate=escalate,
        evidence_used=list(packet.evidence_refs),
    )


def deterministic_review(packet: ReconPacket, preparer: ReconDecision) -> ReconReview:
    finding = classify_packet(packet)
    if finding == "missing_evidence":
        return ReconReview(
            account_id=packet.account_id,
            decision="REQUEST_EVIDENCE",
            sign_off=False,
            agree_with_preparer=preparer.finding == finding,
            reasons=["Cannot sign off while supporting documents are missing."],
        )
    if finding in {"unexplained_difference", "arithmetic_inconsistency", "duplicate_support", "stale_evidence"}:
        return ReconReview(
            account_id=packet.account_id,
            decision="ESCALATE",
            sign_off=False,
            agree_with_preparer=preparer.finding == finding,
            reasons=["Difference is not supported well enough to sign off."],
            evidence_used=list(packet.evidence_refs),
        )
    if can_sign_off(finding):
        return ReconReview(
            account_id=packet.account_id,
            decision="APPROVE",
            sign_off=True,
            agree_with_preparer=True,
            reasons=["Independent review agrees with the Python-supported finding."],
            evidence_used=list(packet.evidence_refs),
        )
    return ReconReview(
        account_id=packet.account_id,
        decision="REJECT",
        sign_off=False,
        agree_with_preparer=False,
        reasons=["Reviewer will not force a match."],
    )
