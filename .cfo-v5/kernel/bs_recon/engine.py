"""Deterministic balance-sheet matching. Agents classify; they never force a match."""

from __future__ import annotations

from close.dates import money
from bs_recon.models import Finding, ReconPacket, ReconcilingItem

STALE_AFTER_DAYS = 45


def explained_total(items: list[ReconcilingItem]) -> float:
    return money(
        sum(
            item.amount
            for item in items
            if item.classification in {"timing_difference", "exact_match"} and item.status != "unexplained"
        )
    )


def arithmetic_consistent(packet: ReconPacket) -> bool:
    if not packet.reconciling_items:
        return True
    difference = money(packet.ledger_balance - packet.evidence_balance)
    residual = money(difference - money(sum(item.amount for item in packet.reconciling_items)))
    return residual == 0


def classify_packet(packet: ReconPacket) -> Finding:
    difference = money(packet.ledger_balance - packet.evidence_balance)
    if packet.duplicate_support:
        return "duplicate_support"
    if packet.missing_evidence or (not packet.evidence_refs and packet.evidence_balance == 0 and difference != 0):
        return "missing_evidence"
    if packet.stale_evidence:
        return "stale_evidence"
    if packet.reconciling_items and not arithmetic_consistent(packet):
        return "arithmetic_inconsistency"
    if difference == 0 and not any(item.classification == "unexplained_difference" for item in packet.reconciling_items):
        return "exact_match"
    residual = money(difference - explained_total(packet.reconciling_items))
    if residual == 0 and any(item.classification == "timing_difference" for item in packet.reconciling_items):
        return "explained_timing_difference"
    return "unexplained_difference"


def status_for(finding: Finding) -> str:
    return {
        "exact_match": "MATCHED",
        "explained_timing_difference": "EXPLAINED_DIFFERENCE",
        "unexplained_difference": "HUMAN_REVIEW",
        "missing_evidence": "BLOCKED",
        "stale_evidence": "HUMAN_REVIEW",
        "duplicate_support": "HUMAN_REVIEW",
        "arithmetic_inconsistency": "BLOCKED",
    }[finding]


def can_sign_off(finding: Finding) -> bool:
    return finding in {"exact_match", "explained_timing_difference"}
