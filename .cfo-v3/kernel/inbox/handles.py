"""Email outbound Handle so World can answer missing-field mail."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from inbox import store as inbox_store


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def email_outbound_handle(
    *,
    thread_id: str,
    message_id: str,
    to_name: str,
    to_address: str,
) -> Path:
    handles = inbox_store.RUNS_DIR / "handles"
    packets = inbox_store.RUNS_DIR / "packets"
    handles.mkdir(parents=True, exist_ok=True)
    packets.mkdir(parents=True, exist_ok=True)
    packet = {
        "object": "simulated_message",
        "thread_id": thread_id,
        "message_id": message_id,
        "to_name": to_name,
        "to_address": to_address,
        "human_queue": False,
    }
    packet_path = packets / f"email-outbound-{message_id}.json"
    packet_path.write_text(json.dumps(packet, indent=2) + "\n")
    handle = {
        "from": "email",
        "to": "world",
        "toSlug": "world",
        "profile": "vendor",
        "kind": "a2a_handoff",
        "status": "accepted",
        "prompt": (
            f"profile: vendor\n"
            f"Finance asked {to_name} for missing invoice fields in thread {thread_id}. "
            "get_inbox_thread then reply_in_thread as that vendor. "
            "Do not send_office_outbound. Do not dispatch."
        ),
        "paths": [str(packet_path)],
        "queueOwner": "world",
        "humanQueue": False,
        "idempotencyKey": f"email:outbound:{message_id}",
        "createdAt": _now(),
    }
    handle_path = handles / f"email-outbound-{message_id}-world.json"
    handle_path.write_text(json.dumps(handle, indent=2) + "\n")
    return handle_path
