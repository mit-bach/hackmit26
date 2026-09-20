"""Read-only tools for cash-reconciliation agents. They cannot post or delete."""

from __future__ import annotations

from agents import function_tool

from cash_recon.models import MatchCandidate
from memory.tools import get_decision_memories


_BANK = {}
_LEDGER = {}
_FEES = {}
_CANDIDATES: list[MatchCandidate] = []


def bind_case(*, bank, ledger, fees, candidates) -> None:
    global _BANK, _LEDGER, _FEES, _CANDIDATES
    _BANK = {item.transaction_id: item for item in bank}
    _LEDGER = {item.entry_id: item for item in ledger}
    _FEES = {item.evidence_id: item for item in fees}
    _CANDIDATES = list(candidates)


@function_tool
def get_bank_transaction(transaction_id: str) -> dict:
    item = _BANK.get(transaction_id)
    if item is None:
        return {"error": f"unknown bank transaction {transaction_id}"}
    return item.model_dump(mode="json")


@function_tool
def get_ledger_entry(entry_id: str) -> dict:
    item = _LEDGER.get(entry_id)
    if item is None:
        return {"error": f"unknown ledger entry {entry_id}"}
    return item.model_dump(mode="json")


@function_tool
def get_fee_evidence(evidence_id: str) -> dict:
    item = _FEES.get(evidence_id)
    if item is None:
        return {"error": f"unknown fee evidence {evidence_id}"}
    return item.model_dump(mode="json")


@function_tool
def get_match_candidates(case_id: str = "") -> list[dict]:
    rows = _CANDIDATES
    if case_id:
        rows = [item for item in rows if case_id in item.candidate_id or case_id in item.bank_transaction_ids or case_id in item.ledger_entry_ids]
    return [item.model_dump(mode="json") for item in rows]


@function_tool
def get_candidate(candidate_id: str) -> dict:
    for item in _CANDIDATES:
        if item.candidate_id == candidate_id:
            return item.model_dump(mode="json")
    return {"error": f"unknown candidate {candidate_id}"}
