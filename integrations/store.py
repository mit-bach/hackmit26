"""Lightweight JSON event store under runs/integrations/. Not Kafka."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from integrations.models import ProviderPayout, WebhookEvent

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs" / "integrations"
STATE_PATH = RUNS_DIR / "state.json"

_events: dict[tuple[str, str], WebhookEvent] = {}
_payouts: dict[str, ProviderPayout] = {}
_gmail_history: dict[str, str] = {}
_outlook_subs: dict[str, dict] = {}
_sync_cursors: dict[str, str] = {}


def payload_hash(raw: bytes | str) -> str:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def reset_integration_state() -> None:
    _events.clear()
    _payouts.clear()
    _gmail_history.clear()
    _outlook_subs.clear()
    _sync_cursors.clear()


def remember_event(event: WebhookEvent) -> WebhookEvent:
    key = (event.provider, event.provider_event_id)
    existing = _events.get(key)
    if existing is not None:
        existing.receipt_count += 1
        existing.processing_status = "duplicate"
        existing.result = existing.result or "already_processed"
        _persist()
        return existing
    _events[key] = event
    _persist()
    return event


def get_event(provider: str, event_id: str) -> WebhookEvent | None:
    return _events.get((provider, event_id))


def update_event(event: WebhookEvent) -> None:
    _events[(event.provider, event.provider_event_id)] = event
    _persist()


def all_events() -> list[WebhookEvent]:
    return list(_events.values())


def remember_payout(payout: ProviderPayout) -> ProviderPayout:
    existing = _payouts.get(payout.payout_id)
    if existing is not None:
        if payout.status:
            existing.status = payout.status
        if payout.lines:
            existing.lines = payout.lines
        existing.source_event_type = payout.source_event_type
        existing.event_id = payout.event_id
        _persist()
        return existing
    _payouts[payout.payout_id] = payout
    _persist()
    return payout


def get_payout(payout_id: str) -> ProviderPayout | None:
    return _payouts.get(payout_id)


def all_payouts() -> list[ProviderPayout]:
    return list(_payouts.values())


def gmail_history_id(mailbox: str) -> str | None:
    return _gmail_history.get(mailbox)


def set_gmail_history_id(mailbox: str, history_id: str) -> None:
    _gmail_history[mailbox] = str(history_id)
    _persist()


def outlook_subscription(sub_id: str) -> dict | None:
    return _outlook_subs.get(sub_id)


def remember_outlook_subscription(payload: dict) -> None:
    sub_id = str(payload.get("id") or "")
    if sub_id:
        _outlook_subs[sub_id] = payload
        _persist()


def sync_cursor(provider: str) -> str | None:
    return _sync_cursors.get(provider)


def set_sync_cursor(provider: str, value: str) -> None:
    _sync_cursors[provider] = value
    _persist()


def _persist() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(
            {
                "events": [item.model_dump(mode="json") for item in _events.values()],
                "payouts": [item.model_dump(mode="json") for item in _payouts.values()],
                "gmail_history": _gmail_history,
                "outlook_subscriptions": _outlook_subs,
                "sync_cursors": _sync_cursors,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )


def write_trace(name: str, payload: dict[str, Any]) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path
