"""Shared general ledger for close workflows. Accrual books stay authoritative for accruals."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import money, now_iso

LEDGER_DIR = Path(__file__).resolve().parent.parent / "runs" / "month_end"
JOURNALS_PATH = LEDGER_DIR / "journal_entries.json"

_entries: list[dict] | None = None
_replay_hits = 0


def configure_paths(directory: Path) -> None:
    global LEDGER_DIR, JOURNALS_PATH, _entries
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    LEDGER_DIR = directory
    JOURNALS_PATH = directory / "journal_entries.json"
    _entries = None


def reset_ledger() -> None:
    global _entries, _replay_hits
    _entries = []
    _replay_hits = 0
    _write([])


def replay_hit_count() -> int:
    return _replay_hits


def _read() -> list[dict]:
    global _entries
    if _entries is not None:
        return _entries
    if not JOURNALS_PATH.exists():
        _entries = []
        return _entries
    raw = json.loads(JOURNALS_PATH.read_text())
    if not isinstance(raw, list):
        raise ValueError("journal_entries.json must contain a JSON array")
    _entries = raw
    return _entries


def _write(rows: list[dict]) -> None:
    global _entries
    JOURNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNALS_PATH.write_text(json.dumps(rows, indent=2) + "\n")
    _entries = rows


def load_entries() -> list[dict]:
    return [dict(item) for item in _read()]


def find_by_key(idempotency_key: str) -> dict | None:
    for item in _read():
        if item.get("idempotency_key") == idempotency_key:
            return dict(item)
    return None


def find_entry(entry_id: str) -> dict | None:
    for item in _read():
        if item.get("entry_id") == entry_id:
            return dict(item)
    return None


def _next_id(period: str) -> str:
    stamp = period.replace("-", "")
    prefix = f"JE-{stamp}-"
    numbers = []
    for item in _read():
        entry_id = str(item.get("entry_id", ""))
        if entry_id.startswith(prefix) and entry_id[len(prefix) :].isdigit():
            numbers.append(int(entry_id[len(prefix) :]))
    return f"{prefix}{max(numbers, default=0) + 1:03d}"


def post_entry(
    *,
    period: str,
    memo: str,
    debit_account: str,
    credit_account: str,
    amount: float,
    entry_type: str,
    idempotency_key: str,
    source_document_id: str = "",
    transaction_id: str = "",
    evidence_refs: list[str] | None = None,
    related_ids: dict | None = None,
    actor: str = "",
    allow_closed: bool = False,
) -> dict:
    global _replay_hits
    amount = money(amount)
    if amount <= 0:
        raise ValueError("Journal amount must be positive.")
    if not evidence_refs:
        raise ValueError("Every journal entry must link to source evidence.")
    existing = find_by_key(idempotency_key)
    if existing:
        _replay_hits += 1
        return existing
    from close.period_lock import assert_period_open

    assert_period_open(
        period,
        attempted_entry={
            "memo": memo,
            "debit_account": debit_account,
            "credit_account": credit_account,
            "amount": amount,
            "entry_type": entry_type,
            "idempotency_key": idempotency_key,
        },
        actor=actor,
        allow_closed=allow_closed,
    )
    if money(amount) != money(amount):
        raise ValueError("Journal is not balanced.")
    entry = {
        "entry_id": _next_id(period),
        "period": period,
        "memo": memo,
        "debit_account": debit_account,
        "credit_account": credit_account,
        "debit": amount,
        "credit": amount,
        "entry_type": entry_type,
        "idempotency_key": idempotency_key,
        "source_document_id": source_document_id,
        "transaction_id": transaction_id,
        "evidence_refs": list(evidence_refs),
        "related_ids": dict(related_ids or {}),
        "created_at": now_iso(),
    }
    rows = _read()
    rows.append(entry)
    _write(rows)
    return dict(entry)


def account_balance(account: str, period: str = "") -> float:
    """Net debit-minus-credit activity, optionally limited to one period."""
    total = 0.0
    for item in _read():
        if period and item.get("period") != period:
            continue
        if item.get("debit_account") == account:
            total = money(total + float(item["debit"]))
        if item.get("credit_account") == account:
            total = money(total - float(item["credit"]))
    return money(total)


def entries_for(
    *,
    period: str = "",
    entry_type: str = "",
    transaction_id: str = "",
    account: str = "",
) -> list[dict]:
    rows = load_entries()
    if period:
        rows = [item for item in rows if item.get("period") == period]
    if entry_type:
        rows = [item for item in rows if item.get("entry_type") == entry_type]
    if transaction_id:
        rows = [item for item in rows if item.get("transaction_id") == transaction_id]
    if account:
        rows = [
            item
            for item in rows
            if item.get("debit_account") == account or item.get("credit_account") == account
        ]
    return rows
