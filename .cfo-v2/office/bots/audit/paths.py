"""Path leases for Bot audit writes.

Writes are allowed only under workspace/audit/ and runs/audit/.
Harness lease files remain the backstop when two Bots edit the same path.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

AUDIT_WRITE_PREFIXES: tuple[str, ...] = (
    "workspace/audit/",
    "runs/audit/",
)

AUDIT_BOT_ID = "bot_audit"


class PathLeaseError(PermissionError):
    """Bot audit cannot write this Computer path."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def posix_rel(path: str) -> str:
    text = path.replace("\\", "/").lstrip("./")
    while text.startswith("/"):
        text = text[1:]
    if ".." in Path(text).parts:
        raise PathLeaseError(f"forbidden: path escapes Computer ({path})")
    return text


def write_allowed(rel_path: str) -> bool:
    rel = posix_rel(rel_path)
    for prefix in AUDIT_WRITE_PREFIXES:
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            return True
    return False


def assert_write_allowed(rel_path: str) -> str:
    rel = posix_rel(rel_path)
    if not write_allowed(rel):
        raise PathLeaseError(f"forbidden: bot_audit cannot write {rel}")
    return rel


def lease_dir(computer: Path) -> Path:
    return Path(computer) / "harness" / "leases"


def lease_file(computer: Path, rel_path: str) -> Path:
    rel = assert_write_allowed(rel_path)
    target = str((Path(computer) / rel).resolve())
    digest = hashlib.sha256(target.encode("utf-8")).hexdigest()[:16]
    return lease_dir(computer) / f"{digest}.json"


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = text if text.endswith("\n") else text + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def acquire_lease(computer: Path, rel_path: str, bot_id: str = AUDIT_BOT_ID) -> Path:
    rel = assert_write_allowed(rel_path)
    folder = lease_dir(computer)
    folder.mkdir(parents=True, exist_ok=True)
    file = lease_file(computer, rel)
    record = {
        "path": rel,
        "botId": bot_id,
        "pid": os.getpid(),
        "updatedAt": _now(),
    }
    write_json_atomic(file, record)
    return file


def release_lease(computer: Path, rel_path: str, bot_id: str = AUDIT_BOT_ID) -> None:
    file = lease_file(computer, rel_path)
    if not file.is_file():
        return
    raw = json.loads(file.read_text(encoding="utf-8"))
    if raw.get("botId") != bot_id:
        return
    raw["pid"] = 0
    raw["updatedAt"] = _now()
    write_json_atomic(file, raw)


def leased_write_json(computer: Path, rel_path: str, value: object) -> Path:
    rel = assert_write_allowed(rel_path)
    acquire_lease(computer, rel)
    target = Path(computer) / rel
    try:
        write_json_atomic(target, value)
    finally:
        release_lease(computer, rel)
    return target


def leased_write_text(computer: Path, rel_path: str, text: str) -> Path:
    rel = assert_write_allowed(rel_path)
    acquire_lease(computer, rel)
    target = Path(computer) / rel
    try:
        write_text_atomic(target, text)
    finally:
        release_lease(computer, rel)
    return target
