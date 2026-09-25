from __future__ import annotations

import json
from pathlib import Path

from prepaid.models import PrepaidItem, PrepaidScheduleLine

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "close" / "prepaids.json"
STATE_DIR = ROOT / "runs" / "month_end"
ITEMS_PATH = STATE_DIR / "prepaids.json"
SCHEDULE_PATH = STATE_DIR / "prepaid_schedule.json"

_items: list[dict] | None = None
_lines: list[dict] | None = None


def configure_paths(directory: Path, *, seed_path: Path | None = None) -> None:
    global STATE_DIR, ITEMS_PATH, SCHEDULE_PATH, SEED_PATH, _items, _lines
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    ITEMS_PATH = directory / "prepaids.json"
    SCHEDULE_PATH = directory / "prepaid_schedule.json"
    if seed_path is not None:
        SEED_PATH = Path(seed_path)
    _items = None
    _lines = None


def reset() -> None:
    global _items, _lines
    _items = []
    _lines = []
    _write(ITEMS_PATH, [])
    _write(SCHEDULE_PATH, [])


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return raw


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2) + "\n")


def load_seed_items() -> list[PrepaidItem]:
    return [PrepaidItem.model_validate(item) for item in _read(SEED_PATH)]


def load_items() -> list[PrepaidItem]:
    global _items
    if _items is None:
        if ITEMS_PATH.exists():
            _items = _read(ITEMS_PATH)
        elif SEED_PATH.exists():
            _items = _read(SEED_PATH)
            _write(ITEMS_PATH, _items)
        else:
            _items = []
    return [PrepaidItem.model_validate(item) for item in _items]


def save_items(rows: list[PrepaidItem]) -> None:
    global _items
    payload = [item.model_dump() for item in rows]
    _write(ITEMS_PATH, payload)
    _items = payload


def get_item(prepaid_id: str) -> PrepaidItem | None:
    for item in load_items():
        if item.prepaid_id == prepaid_id:
            return item
    return None


def upsert_item(item: PrepaidItem) -> PrepaidItem:
    rows = [row for row in load_items() if row.prepaid_id != item.prepaid_id]
    rows.append(item)
    save_items(rows)
    return item


def load_schedule() -> list[PrepaidScheduleLine]:
    global _lines
    if _lines is None:
        _lines = _read(SCHEDULE_PATH) if SCHEDULE_PATH.exists() else []
    return [PrepaidScheduleLine.model_validate(item) for item in _lines]


def save_schedule(rows: list[PrepaidScheduleLine]) -> None:
    global _lines
    payload = [item.model_dump() for item in rows]
    _write(SCHEDULE_PATH, payload)
    _lines = payload


def lines_for(prepaid_id: str, status: str = "") -> list[PrepaidScheduleLine]:
    rows = [item for item in load_schedule() if item.prepaid_id == prepaid_id]
    if status:
        rows = [item for item in rows if item.status == status]
    return rows


def upsert_line(line: PrepaidScheduleLine) -> PrepaidScheduleLine:
    rows = [
        item
        for item in load_schedule()
        if not (item.prepaid_id == line.prepaid_id and item.period == line.period)
    ]
    rows.append(line)
    save_schedule(rows)
    return line
