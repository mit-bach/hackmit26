"""Unlocked story packets. If lock_status is not CLOSED, every number is UNLOCKED."""

from __future__ import annotations

from typing import Any

UNLOCKED = "UNLOCKED"


def lock_is_closed(lock_status: str | None) -> bool:
    return (lock_status or "").strip().upper() == "CLOSED"


def labeled_number(value: Any, *, lock_status: str | None, evidence_id: str = "") -> dict[str, Any]:
    row: dict[str, Any] = {"value": value, "evidence_id": evidence_id}
    if not lock_is_closed(lock_status):
        row["label"] = UNLOCKED
    return row


def stamp_amounts(payload: Any, *, lock_status: str | None, evidence_id: str = "") -> Any:
    """Wrap numeric leaves so unlocked drafts cannot look closed."""
    if lock_is_closed(lock_status):
        return payload
    if isinstance(payload, bool):
        return payload
    if isinstance(payload, (int, float)):
        return labeled_number(payload, lock_status=lock_status, evidence_id=evidence_id)
    if isinstance(payload, list):
        return [stamp_amounts(item, lock_status=lock_status, evidence_id=evidence_id) for item in payload]
    if isinstance(payload, dict):
        if "value" in payload and "label" in payload:
            return payload
        return {
            key: stamp_amounts(val, lock_status=lock_status, evidence_id=str(val) if key.endswith("_id") else evidence_id)
            for key, val in payload.items()
        }
    return payload


def prefix_unlocked(text: str, *, lock_status: str | None) -> str:
    if lock_is_closed(lock_status):
        return text
    if text.startswith(UNLOCKED):
        return text
    return f"{UNLOCKED}. {text}" if text else UNLOCKED
