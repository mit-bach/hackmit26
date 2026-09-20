"""Durable local JSON store for organizational decision memories."""

from __future__ import annotations

import json
from pathlib import Path

from memory.models import DecisionMemory

ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "runs" / "memory"
STATE_PATH = MEMORY_DIR / "decisions.json"

_records: list[DecisionMemory] | None = None


def current_directory() -> Path:
    return MEMORY_DIR


def configure_paths(directory: Path | None = None) -> None:
    global MEMORY_DIR, STATE_PATH, _records
    if directory is None:
        MEMORY_DIR = ROOT / "runs" / "memory"
    else:
        MEMORY_DIR = Path(directory)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH = MEMORY_DIR / "decisions.json"
    _records = None


def reset_memory() -> None:
    global _records
    _records = []
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def _read() -> list[DecisionMemory]:
    if not STATE_PATH.exists():
        return []
    raw = json.loads(STATE_PATH.read_text())
    if isinstance(raw, dict):
        raw = raw.get("decisions") or []
    if not isinstance(raw, list):
        raise ValueError("memory store must contain a JSON array or {decisions: [...]}")
    return [DecisionMemory.model_validate(item) for item in raw]


def _write(rows: list[DecisionMemory]) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump(mode="json") for item in rows]
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def load_memories() -> list[DecisionMemory]:
    global _records
    if _records is None:
        _records = _read()
    return list(_records)


def save_memories(rows: list[DecisionMemory]) -> None:
    global _records
    _records = list(rows)
    _write(_records)


def get_memory(decision_id: str) -> DecisionMemory | None:
    for item in load_memories():
        if item.decision_id == decision_id:
            return item
    return None


def find_by_idempotency_key(key: str) -> DecisionMemory | None:
    for item in load_memories():
        if item.idempotency_key == key:
            return item
    return None


def next_decision_id(period: str) -> str:
    prefix = f"DEC-{period}-"
    existing = [item.decision_id for item in load_memories() if item.decision_id.startswith(prefix)]
    numbers = []
    for decision_id in existing:
        suffix = decision_id[len(prefix) :]
        if suffix.isdigit():
            numbers.append(int(suffix))
    nxt = max(numbers, default=0) + 1
    return f"{prefix}{nxt:03d}"


def put_memory(record: DecisionMemory) -> tuple[DecisionMemory, bool]:
    """Insert or return the existing record for the same idempotency key.

    Returns (record, created).
    """
    existing = find_by_idempotency_key(record.idempotency_key)
    if existing is not None:
        return existing, False
    rows = load_memories()
    if not record.decision_id:
        record = record.model_copy(update={"decision_id": next_decision_id(record.period)})
    elif any(item.decision_id == record.decision_id for item in rows):
        record = record.model_copy(update={"decision_id": next_decision_id(record.period)})
    rows.append(record)
    save_memories(rows)
    return record, True
