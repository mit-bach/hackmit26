"""Harness Handle files on the Computer. Accept is not complete.

Kernel hosts emit these so office-live work is a Handle, not Runner.
The sender never marks complete. Peer Handle is not approval.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from atomic_json import write_json_atomic


def bot_id_for_slug(slug: str) -> str:
    return "bot_" + slug.replace("-", "_")


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path("/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3")


def new_handle_id() -> str:
    return f"h_{uuid4()}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def relative_to_computer(computer_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(computer_root.resolve()))
    except ValueError:
        return str(path)


def write_peer_handle(
    computer_root: Path,
    *,
    from_slug: str,
    to_slug: str,
    profile: str,
    paths: list[str],
    prompt: str,
    extra: dict | None = None,
    handle_id: str | None = None,
) -> tuple[Path, dict]:
    """Write an accepted Handle on the destination Bot. Status is not done."""
    hid = handle_id or new_handle_id()
    from_id = bot_id_for_slug(from_slug)
    to_id = bot_id_for_slug(to_slug)
    created = now_iso()
    payload: dict = {
        "id": hid,
        "from": from_id,
        "fromSlug": from_slug,
        "to": to_id,
        "toSlug": to_slug,
        "profile": profile,
        "prompt": prompt,
        "paths": list(paths),
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "conversation": {
            "kind": "peer_dm",
            "fromId": from_id,
            "toId": to_id,
        },
        "createdAt": created,
        "updatedAt": created,
        "bus": "harness",
        "op": "bot_send_prompt",
        "humanQueue": False,
        "queue": {"owner": to_slug, "profile": profile},
    }
    if extra:
        payload.update(extra)
    dest = computer_root / "harness" / "bots" / to_id / "handles" / f"{hid}.json"
    write_json_atomic(dest, payload)
    return dest, payload
