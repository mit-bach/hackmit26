"""Closed-period control. A CLOSED month cannot be mutated by the normal posting path."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from close.models import CloseControlEvent, ClosePeriodStatus

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
LOCK_PATH = STATE_DIR / "period_lock.json"
EVENTS_PATH = STATE_DIR / "control_events.json"


class ClosedPeriodError(RuntimeError):
    def __init__(self, event: CloseControlEvent):
        super().__init__(
            f"{event.event_type}: period {event.period} is closed; entry was {event.decision}."
        )
        self.event = event


def configure_paths(directory: Path) -> None:
    global STATE_DIR, LOCK_PATH, EVENTS_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    LOCK_PATH = directory / "period_lock.json"
    EVENTS_PATH = directory / "control_events.json"


def _read_lock() -> dict:
    if not LOCK_PATH.exists():
        return {}
    payload = json.loads(LOCK_PATH.read_text())
    return payload if isinstance(payload, dict) else {}


def _write_lock(payload: dict) -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def period_status(period: str) -> ClosePeriodStatus:
    row = _read_lock().get(period) or {}
    return row.get("status") or "OPEN"  # type: ignore[return-value]


def is_period_closed(period: str) -> bool:
    return period_status(period) == "CLOSED"


def mark_period(period: str, status: ClosePeriodStatus, **extra) -> None:
    payload = _read_lock()
    row = dict(payload.get(period) or {})
    row["status"] = status
    row.update(extra)
    payload[period] = row
    _write_lock(payload)


def load_events(period: str = "") -> list[CloseControlEvent]:
    if not EVENTS_PATH.exists():
        return []
    rows = json.loads(EVENTS_PATH.read_text())
    events = [CloseControlEvent.model_validate(item) for item in rows]
    if period:
        events = [item for item in events if item.period == period]
    return events


def record_event(event: CloseControlEvent) -> CloseControlEvent:
    rows = [item.model_dump() for item in load_events()]
    key = (event.event_type, event.period, json.dumps(event.attempted_entry, sort_keys=True), event.reason)
    for existing in rows:
        existing_key = (
            existing.get("event_type"),
            existing.get("period"),
            json.dumps(existing.get("attempted_entry") or {}, sort_keys=True),
            existing.get("reason"),
        )
        if existing_key == key:
            return CloseControlEvent.model_validate(existing)
    rows.append(event.model_dump())
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_PATH.write_text(json.dumps(rows, indent=2) + "\n")
    return event


def assert_period_open(
    period: str,
    *,
    attempted_entry: dict | None = None,
    actor: str = "",
    reason: str = "",
    allow_closed: bool = False,
) -> CloseControlEvent | None:
    if not is_period_closed(period):
        return None
    event = CloseControlEvent(
        event_id=f"PCE-{period}-{now_iso().replace(':', '')}",
        event_type="POST_CLOSE_ENTRY_ATTEMPT",
        period=period,
        created_at=now_iso(),
        actor=actor or "system",
        reason=reason or "Journal dated in a closed period",
        decision="APPROVED" if allow_closed else "REJECTED",
        attempted_entry=dict(attempted_entry or {}),
        audit_trace=str(EVENTS_PATH),
    )
    stored = record_event(event)
    if allow_closed:
        return stored
    raise ClosedPeriodError(stored)
