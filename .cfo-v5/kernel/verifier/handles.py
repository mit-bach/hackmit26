"""Persist Verifier Handle payloads. Accept is not complete. A person is not the queue."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from atomic_json import write_json_atomic
from verifier.queue_owners import owner_for, payload_for


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def kernel_runs_dir() -> Path:
    return default_computer_root() / "runs"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return f"h_{uuid4()}"


def handles_dir(runs_dir: Path | None = None) -> Path:
    return Path(runs_dir or kernel_runs_dir()) / "verifier" / "handles"


def packets_dir(runs_dir: Path | None = None) -> Path:
    return Path(runs_dir or kernel_runs_dir()) / "verifier" / "packets"


def write_packet(name: str, payload: dict[str, Any], *, runs_dir: Path | None = None) -> Path:
    path = packets_dir(runs_dir) / f"{name}.json"
    write_json_atomic(path, payload)
    return path


def write_handle(payload: dict[str, Any], *, runs_dir: Path | None = None, name: str | None = None) -> Path:
    handle_id = str(payload.get("id") or _new_id())
    payload = dict(payload)
    payload.setdefault("id", handle_id)
    payload.setdefault("status", "accepted")
    payload.setdefault("done", False)
    payload.setdefault("humanQueue", False)
    payload.setdefault("createdAt", _now())
    payload["updatedAt"] = _now()
    filename = name or handle_id
    path = handles_dir(runs_dir) / f"{filename}.json"
    write_json_atomic(path, payload)
    return path


def read_handle(path: Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"handle {path} is not an object")
    return raw


def complete_handle(
    path: Path,
    *,
    decision: str,
    reasons: list[str],
    kernel_ok: bool,
) -> dict[str, Any]:
    payload = read_handle(path)
    final = decision
    notes = list(reasons)
    if final == "CONCUR" and not kernel_ok:
        final = "REFUSE"
        notes = ["Kernel already refuses. Verifier cannot concur."] + notes
    payload["status"] = "completed"
    payload["done"] = True
    payload["decision"] = final
    payload["reasons"] = notes
    payload["kernelOk"] = kernel_ok
    payload["humanQueue"] = False
    payload["updatedAt"] = _now()
    write_json_atomic(Path(path), payload)
    return payload


def request_handle(
    *,
    from_slug: str,
    to_slug: str,
    profile: str,
    paths: list[str],
    prompt: str,
    kernel_status: str,
    pipe: str,
    object_id: str,
    runs_dir: Path | None = None,
    audit_wake: bool = False,
) -> dict[str, Any]:
    owner = owner_for(pipe, kernel_status)
    handle_id = _new_id()
    payload = {
        "id": handle_id,
        "fromSlug": from_slug,
        "toSlug": to_slug,
        "to": f"bot_{to_slug.replace('-', '_')}",
        "profile": profile,
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "paths": paths,
        "prompt": prompt,
        "kernelStatus": kernel_status,
        "queueOwner": payload_for(pipe, kernel_status),
        "humanQueue": False,
        "auditWake": audit_wake,
        "objectId": object_id,
        "op": "bot_send_prompt",
        "ask_user": False,
    }
    if owner["owner"] != to_slug or owner["profile"] != profile:
        payload["queueOwner"] = {"owner": to_slug, "profile": profile, "kernelStatus": kernel_status, "humanQueue": False}
    path = write_handle(payload, runs_dir=runs_dir, name=f"{to_slug}-{object_id}-{profile}")
    payload["path"] = str(path)
    return payload
