"""JSON helpers. Never invent finance fields."""

from __future__ import annotations

import json
from typing import Any

from cfo_kernel.rpc import to_jsonable


def dump(value: Any) -> Any:
    payload = to_jsonable(value)
    return json.loads(json.dumps(payload, default=str))


def read_json(path) -> Any:
    from pathlib import Path

    target = Path(path)
    if not target.is_file():
        return None
    return json.loads(target.read_text())


def money(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def cents_to_dollars(cents: int | None) -> float:
    if cents is None:
        return 0.0
    return round(int(cents) / 100.0, 2)
