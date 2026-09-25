"""Atomic idempotency claims under Computer cfo/idempotency/."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from atomic_json import read_json_object, write_json_atomic

from cfo_kernel.paths import Computer


def request_hash(op: str, args: dict) -> str:
    canonical = json.dumps(
        {"op": op, "args": args},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _path(computer: Computer, key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return computer.idempotency_dir / f"{digest}.json"


def claim(
    computer: Computer, *, key: str, op: str, args: dict
) -> tuple[str, dict | None]:
    """Return ('new'|'replay'|'mismatch'|'in_progress', stored_or_none)."""
    path = _path(computer, key)
    digest = request_hash(op, args)
    record = {
        "key": key,
        "op": op,
        "hash": digest,
        "status": "pending",
        "response": None,
    }
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError:
        existing = read_json_object(path)
        if existing.get("hash") != digest:
            return "mismatch", existing
        if existing.get("status") == "complete":
            return "replay", existing
        return "in_progress", existing
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")
    return "new", record


def complete(computer: Computer, *, key: str, op: str, args: dict, response: dict) -> None:
    path = _path(computer, key)
    write_json_atomic(
        path,
        {
            "key": key,
            "op": op,
            "hash": request_hash(op, args),
            "status": "complete",
            "response": response,
        },
    )
