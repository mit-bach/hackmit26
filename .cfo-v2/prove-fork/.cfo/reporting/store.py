"""Immutable forecast snapshots and reporting traces."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from datetime import datetime, timezone

from reporting.models import CashForecastSnapshot, ReportingRun


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "reporting"
FORECAST_DIR = STATE_DIR / "forecasts"
TRACE_DIR = STATE_DIR / "traces"

_snapshots: dict[str, CashForecastSnapshot] = {}


def configure_paths(directory: Path) -> None:
    global STATE_DIR, FORECAST_DIR, TRACE_DIR, _snapshots
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    FORECAST_DIR = directory / "forecasts"
    TRACE_DIR = directory / "traces"
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    _snapshots = {}


def reset_store() -> None:
    _snapshots.clear()


@contextmanager
def isolated_store(directory: Path):
    global STATE_DIR, FORECAST_DIR, TRACE_DIR, _snapshots
    previous = (STATE_DIR, FORECAST_DIR, TRACE_DIR, dict(_snapshots))
    configure_paths(directory)
    try:
        yield
    finally:
        STATE_DIR, FORECAST_DIR, TRACE_DIR = previous[0], previous[1], previous[2]
        _snapshots = previous[3]


def _forecast_path(forecast_id: str) -> Path:
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    return FORECAST_DIR / f"{forecast_id}.json"


def next_version(as_of_date: str) -> int:
    prefix = f"CF-{as_of_date}-v"
    versions = []
    for item in list_snapshots():
        if item.forecast_id.startswith(prefix):
            versions.append(item.version)
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    for path in FORECAST_DIR.glob(f"CF-{as_of_date}-v*.json"):
        suffix = path.stem.split("-v")[-1]
        if suffix.isdigit():
            versions.append(int(suffix))
    return max(versions, default=0) + 1


def save_snapshot(snapshot: CashForecastSnapshot) -> CashForecastSnapshot:
    if snapshot.forecast_id in _snapshots:
        raise ValueError(f"Forecast {snapshot.forecast_id} is immutable and already stored.")
    path = _forecast_path(snapshot.forecast_id)
    if path.exists():
        raise ValueError(f"Forecast {snapshot.forecast_id} already exists on disk and will not be overwritten.")
    frozen = snapshot.model_copy(update={"immutable": True, "created_at": snapshot.created_at or _now()})
    path.write_text(frozen.model_dump_json(indent=2) + "\n")
    _snapshots[frozen.forecast_id] = frozen
    return frozen.model_copy(update={"trace_path": str(path)})


def load_snapshot(forecast_id: str) -> CashForecastSnapshot | None:
    if forecast_id in _snapshots:
        return _snapshots[forecast_id]
    path = _forecast_path(forecast_id)
    if not path.exists():
        return None
    item = CashForecastSnapshot.model_validate_json(path.read_text())
    _snapshots[forecast_id] = item
    return item


def list_snapshots() -> list[CashForecastSnapshot]:
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    for item in _snapshots.values():
        rows.append(item)
        seen.add(item.forecast_id)
    for path in sorted(FORECAST_DIR.glob("CF-*.json")):
        if path.stem in seen:
            continue
        rows.append(CashForecastSnapshot.model_validate_json(path.read_text()))
    return sorted(rows, key=lambda item: (item.as_of_date, item.version))


def latest_snapshot(as_of_date: str = "") -> CashForecastSnapshot | None:
    rows = list_snapshots()
    if as_of_date:
        rows = [item for item in rows if item.as_of_date == as_of_date]
    return rows[-1] if rows else None


def save_run(run: ReportingRun) -> Path:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACE_DIR / f"{run.run_id}.json"
    path.write_text(run.model_dump_json(indent=2) + "\n")
    return path


def save_json(name: str, payload) -> Path:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACE_DIR / f"{name}.json"
    if hasattr(payload, "model_dump_json"):
        path.write_text(payload.model_dump_json(indent=2) + "\n")
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
