"""Fail-closed recovery for messy inputs. Never invent missing finance data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RecoveryError(ValueError):
    """Recoverable input was unusable; workflow must not fabricate a record."""


def parse_json_text(raw: str, *, label: str = "payload") -> tuple[Any | None, str | None]:
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"{label} is not valid JSON: {exc.msg}"


def parse_csv_text(raw: str, *, required: tuple[str, ...] = ()) -> tuple[list[dict] | None, str | None]:
    import csv
    import io

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except csv.Error as exc:
        return None, f"csv_parse_error:{exc}"
    if reader.fieldnames is None:
        return None, "csv_missing_header"
    missing = [name for name in required if name not in reader.fieldnames]
    if missing:
        return None, "csv_missing_columns:" + ",".join(missing)
    try:
        rows = list(reader)
    except csv.Error as exc:
        return None, f"csv_row_error:{exc}"
    return rows, None


def read_optional_attachment(path: Path | None) -> tuple[str | None, str | None]:
    if path is None:
        return None, "missing_optional_attachment"
    try:
        return path.read_text(), None
    except FileNotFoundError:
        return None, "unavailable_attachment"
    except OSError as exc:
        return None, f"attachment_unreadable:{exc}"


def replay_event(event_id: str, seen: set[str]) -> tuple[str, bool]:
    """Duplicate API events are acknowledged, not posted twice."""
    if event_id in seen:
        return "duplicate_ignored", False
    seen.add(event_id)
    return "accepted", True


def missing_stripe_metadata(payout: dict) -> list[str]:
    needed = ("id", "amount", "currency")
    return [key for key in needed if payout.get(key) in (None, "")]


def recover_or_skip(raw: str, *, kind: str = "json") -> dict[str, Any]:
    """Public recovery path used by workflows and evals. Does not invent records."""
    if kind == "csv":
        rows, error = parse_csv_text(raw, required=("date", "amount"))
        return {"ok": error is None, "rows": rows or [], "error": error, "invented": False}
    payload, error = parse_json_text(raw)
    return {"ok": error is None, "payload": payload, "error": error, "invented": False}
