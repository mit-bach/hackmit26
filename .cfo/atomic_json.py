"""Atomic JSON writes for Kernel stores that more than one Bot process shares."""

from __future__ import annotations

import fcntl
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    os.replace(tmp, path)


def read_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return raw


def with_file_lock(lock_path: Path, body: Callable[[], T]) -> T:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            return body()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
