"""Read-only tools for cash-reconciliation agents. They cannot post or delete."""

from __future__ import annotations

import os

from agents import function_tool

from cash_recon.case_store import (
    case_file_exists,
    hydrate_bound_case,
    load_bound_case,
    save_bound_case,
)
from cash_recon.identifiers import identifier_for_bank
from cash_recon.models import MatchCandidate, PipeIdentifier
from memory.tools import get_decision_memories

_BANK: dict = {}
_LEDGER: dict = {}
_FEES: dict = {}
_CANDIDATES: list[MatchCandidate] = []
_IDENTIFIERS: list[PipeIdentifier] = []
_ACTIVE_CASE_ID = ""


def unbind_case() -> None:
    global _BANK, _LEDGER, _FEES, _CANDIDATES, _IDENTIFIERS, _ACTIVE_CASE_ID
    _BANK = {}
    _LEDGER = {}
    _FEES = {}
    _CANDIDATES = []
    _IDENTIFIERS = []
    _ACTIVE_CASE_ID = ""


def active_case_id() -> str:
    return _ACTIVE_CASE_ID


def bind_case(
    *,
    bank,
    ledger,
    fees,
    candidates,
    case_id: str | None = None,
    persist: bool = True,
    idempotency_key: str | None = None,
) -> str:
    """Host-side session bind. Not a Catalog op. Persists so a second process can investigate."""
    global _BANK, _LEDGER, _FEES, _CANDIDATES, _ACTIVE_CASE_ID
    _BANK = {item.transaction_id: item for item in bank}
    _LEDGER = {item.entry_id: item for item in ledger}
    _FEES = {item.evidence_id: item for item in fees}
    _CANDIDATES = list(candidates)
    _ACTIVE_CASE_ID = case_id or os.environ.get("CFO_CASH_CASE_ID") or "active"
    if persist:
        save_bound_case(
            _ACTIVE_CASE_ID,
            bank=list(_BANK.values()),
            ledger=list(_LEDGER.values()),
            fees=list(_FEES.values()),
            candidates=_CANDIDATES,
            idempotency_key=idempotency_key,
        )
    return _ACTIVE_CASE_ID


def bind_identifiers(identifiers: list[PipeIdentifier] | None) -> int:
    """Host-side bind of apply/pay identifiers. Not a Catalog op."""
    global _IDENTIFIERS
    _IDENTIFIERS = list(identifiers or [])
    return len(_IDENTIFIERS)


def load_case_into_memory(case_id: str) -> bool:
    raw = load_bound_case(case_id)
    if raw is None:
        return False
    global _BANK, _LEDGER, _FEES, _CANDIDATES, _ACTIVE_CASE_ID
    _BANK, _LEDGER, _FEES, _CANDIDATES = hydrate_bound_case(raw)
    _ACTIVE_CASE_ID = case_id
    return True


def _ensure_loaded(case_id: str = "") -> None:
    if _CANDIDATES or _BANK or _LEDGER:
        return
    target = case_id or _ACTIVE_CASE_ID or os.environ.get("CFO_CASH_CASE_ID") or ""
    if target:
        load_case_into_memory(target)


def read_bank_transaction(transaction_id: str) -> dict:
    _ensure_loaded()
    item = _BANK.get(transaction_id)
    if item is None:
        return {"error": f"unknown bank transaction {transaction_id}"}
    return item.model_dump(mode="json")


def read_ledger_entry(entry_id: str) -> dict:
    _ensure_loaded()
    item = _LEDGER.get(entry_id)
    if item is None:
        return {"error": f"unknown ledger entry {entry_id}"}
    return item.model_dump(mode="json")


def read_fee_evidence(evidence_id: str) -> dict:
    _ensure_loaded()
    item = _FEES.get(evidence_id)
    if item is None:
        return {"error": f"unknown fee evidence {evidence_id}"}
    return item.model_dump(mode="json")


def read_match_candidates(case_id: str = "") -> list[dict]:
    if case_id and case_file_exists(case_id):
        load_case_into_memory(case_id)
        return [item.model_dump(mode="json") for item in _CANDIDATES]
    _ensure_loaded(case_id)
    rows = _CANDIDATES
    if case_id:
        rows = [
            item
            for item in rows
            if case_id in item.candidate_id
            or case_id in item.bank_transaction_ids
            or case_id in item.ledger_entry_ids
        ]
    return [item.model_dump(mode="json") for item in rows]


def read_candidate(candidate_id: str) -> dict:
    _ensure_loaded()
    for item in _CANDIDATES:
        if item.candidate_id == candidate_id:
            return item.model_dump(mode="json")
    return {"error": f"unknown candidate {candidate_id}"}


def read_pipe_identifier(bank_transaction_id: str) -> dict:
    """Read apply/pay identity for this bank line. Missing identity is fail-closed, not a guess."""
    _ensure_loaded()
    bank = _BANK.get(bank_transaction_id)
    reference = bank.reference if bank is not None else ""
    ident = identifier_for_bank(
        bank_transaction_id, _IDENTIFIERS, bank_reference=reference
    )
    if ident is None:
        return {
            "bank_transaction_id": bank_transaction_id,
            "identifier_present": False,
            "fail_closed": True,
            "reason": "apply/pay have not identified this line. Do not invent the counterparty.",
        }
    payload = ident.model_dump(mode="json")
    payload["identifier_present"] = True
    payload["fail_closed"] = False
    return payload


@function_tool
def get_bank_transaction(transaction_id: str) -> dict:
    return read_bank_transaction(transaction_id)


@function_tool
def get_ledger_entry(entry_id: str) -> dict:
    return read_ledger_entry(entry_id)


@function_tool
def get_fee_evidence(evidence_id: str) -> dict:
    return read_fee_evidence(evidence_id)


@function_tool
def get_match_candidates(case_id: str = "") -> list[dict]:
    return read_match_candidates(case_id)


@function_tool
def get_candidate(candidate_id: str) -> dict:
    return read_candidate(candidate_id)


@function_tool
def get_pipe_identifier(bank_transaction_id: str) -> dict:
    return read_pipe_identifier(bank_transaction_id)
