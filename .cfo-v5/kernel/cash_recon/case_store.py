"""Disk-backed cash recon bind so a second process can investigate.

Sidecar-internal. Not a Catalog op. The model never calls this.
On-disk path: <computer>/runs/cash_recon/cases/<case_id>.json
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from atomic_json import write_json_atomic
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry, MatchCandidate

SCHEMA = "cfo.cash_recon.case.v1"

_CASE_DIR: Path | None = None


def configure_case_dir(directory: Path | None) -> Path:
    global _CASE_DIR
    if directory is None:
        _CASE_DIR = None
        return case_dir()
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    _CASE_DIR = path
    return path


def case_dir() -> Path:
    if _CASE_DIR is not None:
        return _CASE_DIR
    explicit = os.environ.get("CFO_CASH_CASE_DIR")
    if explicit:
        path = Path(explicit)
        path.mkdir(parents=True, exist_ok=True)
        return path
    computer = os.environ.get("HARNESS_COMPUTER")
    if computer:
        path = Path(computer) / "runs" / "cash_recon" / "cases"
        path.mkdir(parents=True, exist_ok=True)
        return path
    from cash_recon.store import RUNS_DIR

    path = Path(RUNS_DIR) / "cases"
    path.mkdir(parents=True, exist_ok=True)
    return path


def case_path(case_id: str) -> Path:
    safe = case_id.replace("/", "_").replace("..", "_")
    return case_dir() / f"{safe}.json"


def _dump_item(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump(mode="json")
    if isinstance(item, dict):
        return dict(item)
    raise TypeError(f"cannot persist {type(item)!r}")


def _assert_unposted(candidates: list[Any]) -> None:
    for candidate in candidates:
        entries = getattr(candidate, "proposed_adjusting_entries", None)
        if entries is None and isinstance(candidate, dict):
            entries = candidate.get("proposed_adjusting_entries") or []
        for entry in entries or []:
            posted = getattr(entry, "posted", None)
            if posted is None and isinstance(entry, dict):
                posted = entry.get("posted")
            if posted:
                raise ValueError("proposed fee journals must stay unposted; refuse persist")


def content_hash(*, bank: list[Any], ledger: list[Any], fees: list[Any], candidates: list[Any]) -> str:
    payload = {
        "bank": [_dump_item(item) for item in bank],
        "ledger": [_dump_item(item) for item in ledger],
        "fees": [_dump_item(item) for item in fees],
        "candidates": [_dump_item(item) for item in candidates],
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def save_bound_case(
    case_id: str,
    *,
    bank: list[Any],
    ledger: list[Any],
    fees: list[Any],
    candidates: list[Any],
    idempotency_key: str | None = None,
) -> Path:
    """Atomically persist the bound session case. Rebind of the same case_id is allowed."""
    _assert_unposted(candidates)
    key = idempotency_key or f"cash-case:{case_id}"
    digest = content_hash(bank=bank, ledger=ledger, fees=fees, candidates=candidates)
    path = case_path(case_id)
    if path.exists():
        existing = json.loads(path.read_text())
        if existing.get("content_hash") == digest and existing.get("idempotency_key") == key:
            return path
    payload = {
        "schema": SCHEMA,
        "case_id": case_id,
        "idempotency_key": key,
        "content_hash": digest,
        "bank": [_dump_item(item) for item in bank],
        "ledger": [_dump_item(item) for item in ledger],
        "fees": [_dump_item(item) for item in fees],
        "candidates": [_dump_item(item) for item in candidates],
    }
    write_json_atomic(path, payload)
    return path


def load_bound_case(case_id: str) -> dict[str, Any] | None:
    path = case_path(case_id)
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"cash case {case_id} must be a JSON object")
    return raw


def hydrate_bound_case(raw: dict[str, Any]) -> tuple[
    dict[str, BankTransaction],
    dict[str, LedgerEntry],
    dict[str, FeeEvidence],
    list[MatchCandidate],
]:
    bank = {
        item.transaction_id: item
        for item in (BankTransaction.model_validate(row) for row in raw.get("bank") or [])
    }
    ledger = {
        item.entry_id: item
        for item in (LedgerEntry.model_validate(row) for row in raw.get("ledger") or [])
    }
    fees = {
        item.evidence_id: item
        for item in (FeeEvidence.model_validate(row) for row in raw.get("fees") or [])
    }
    candidates = [MatchCandidate.model_validate(row) for row in raw.get("candidates") or []]
    return bank, ledger, fees, candidates


def case_file_exists(case_id: str) -> bool:
    return case_path(case_id).exists()
