"""Write Computer packets. Wake text names a path; tools fetch facts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atomic_json import write_json_atomic


def workspace_root(computer: Path) -> Path:
    return Path(computer) / "workspace" / "sources"


def write_packet(computer: Path, slug: str, source_id: str, payload: dict[str, Any]) -> str:
    safe_id = source_id.replace("/", "_").replace(":", "_")
    path = workspace_root(computer) / slug / f"{safe_id}.json"
    write_json_atomic(path, payload)
    return str(path.relative_to(computer))


def read_packet(computer: Path, relative: str) -> dict[str, Any]:
    raw = json.loads((Path(computer) / relative).read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return raw
