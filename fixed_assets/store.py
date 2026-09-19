from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from fixed_assets.models import CapitalCandidate, DepreciationScheduleLine, FixedAsset
from tools import normalize_vendor

ROOT = Path(__file__).resolve().parent.parent
SEED_ASSETS = ROOT / "data" / "close" / "fixed_assets.json"
SEED_CANDIDATES = ROOT / "data" / "close" / "capital_invoices.json"
STATE_DIR = ROOT / "runs" / "month_end"
ASSETS_PATH = STATE_DIR / "fixed_assets.json"
SCHEDULE_PATH = STATE_DIR / "depreciation_schedule.json"

_assets: list[dict] | None = None
_lines: list[dict] | None = None


def configure_paths(directory: Path, *, seed_assets: Path | None = None, seed_candidates: Path | None = None) -> None:
    global STATE_DIR, ASSETS_PATH, SCHEDULE_PATH, SEED_ASSETS, SEED_CANDIDATES, _assets, _lines
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    ASSETS_PATH = directory / "fixed_assets.json"
    SCHEDULE_PATH = directory / "depreciation_schedule.json"
    if seed_assets is not None:
        SEED_ASSETS = Path(seed_assets)
    if seed_candidates is not None:
        SEED_CANDIDATES = Path(seed_candidates)
    _assets = None
    _lines = None


def reset() -> None:
    global _assets, _lines
    _assets = []
    _lines = []
    _write(ASSETS_PATH, [])
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


def load_seed_candidates() -> list[CapitalCandidate]:
    return [CapitalCandidate.model_validate(item) for item in _read(SEED_CANDIDATES)]


def load_seed_assets() -> list[FixedAsset]:
    return [FixedAsset.model_validate(item) for item in _read(SEED_ASSETS)]


def load_assets() -> list[FixedAsset]:
    global _assets
    if _assets is None:
        if ASSETS_PATH.exists():
            _assets = _read(ASSETS_PATH)
        elif SEED_ASSETS.exists():
            _assets = _read(SEED_ASSETS)
            _write(ASSETS_PATH, _assets)
        else:
            _assets = []
    return [FixedAsset.model_validate(item) for item in _assets]


def save_assets(rows: list[FixedAsset]) -> None:
    global _assets
    payload = [item.model_dump() for item in rows]
    _write(ASSETS_PATH, payload)
    _assets = payload


def get_asset(asset_id: str) -> FixedAsset | None:
    for item in load_assets():
        if item.asset_id == asset_id:
            return item
    return None


def find_duplicates(candidate: CapitalCandidate | FixedAsset) -> list[FixedAsset]:
    vendor = normalize_vendor(candidate.vendor)
    cost = round(float(candidate.cost if isinstance(candidate, FixedAsset) else candidate.amount), 2)
    acquired = candidate.acquisition_date if isinstance(candidate, FixedAsset) else candidate.invoice_date
    matches = []
    for asset in load_assets():
        if (
            normalize_vendor(asset.vendor) == vendor
            and round(asset.cost, 2) == cost
            and asset.acquisition_date == acquired
        ):
            matches.append(asset)
    return matches


def next_asset_id() -> str:
    numbers = []
    for item in load_assets():
        suffix = item.asset_id.rsplit("-", 1)[-1]
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"FA-{max(numbers, default=0) + 1:03d}"


def upsert_asset(asset: FixedAsset) -> FixedAsset:
    rows = [item for item in load_assets() if item.asset_id != asset.asset_id]
    if not asset.created_at:
        asset = asset.model_copy(update={"created_at": now_iso()})
    rows.append(asset)
    save_assets(rows)
    return asset


def load_schedule() -> list[DepreciationScheduleLine]:
    global _lines
    if _lines is None:
        _lines = _read(SCHEDULE_PATH) if SCHEDULE_PATH.exists() else []
    return [DepreciationScheduleLine.model_validate(item) for item in _lines]


def save_schedule(rows: list[DepreciationScheduleLine]) -> None:
    global _lines
    payload = [item.model_dump() for item in rows]
    _write(SCHEDULE_PATH, payload)
    _lines = payload


def lines_for(asset_id: str, status: str = "") -> list[DepreciationScheduleLine]:
    rows = [item for item in load_schedule() if item.asset_id == asset_id]
    if status:
        rows = [item for item in rows if item.status == status]
    return rows


def upsert_line(line: DepreciationScheduleLine) -> DepreciationScheduleLine:
    rows = [
        item
        for item in load_schedule()
        if not (item.asset_id == line.asset_id and item.period == line.period)
    ]
    rows.append(line)
    save_schedule(rows)
    return line
