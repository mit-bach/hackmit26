from __future__ import annotations

import json
from pathlib import Path

from bs_recon.models import BalanceSheetReconciliation, ReconTrace

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
RECON_PATH = STATE_DIR / "reconciliations.json"
TRACES_DIR = STATE_DIR / "recon_traces"

_rows: list[dict] | None = None


def configure_paths(directory: Path) -> None:
    global STATE_DIR, RECON_PATH, TRACES_DIR, _rows
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    RECON_PATH = directory / "reconciliations.json"
    TRACES_DIR = directory / "recon_traces"
    _rows = None


def reset() -> None:
    global _rows
    _rows = []
    RECON_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECON_PATH.write_text("[]\n")


def _read() -> list[dict]:
    global _rows
    if _rows is not None:
        return _rows
    if not RECON_PATH.exists():
        _rows = []
        return _rows
    _rows = json.loads(RECON_PATH.read_text())
    return _rows


def save_reconciliation(row: BalanceSheetReconciliation) -> BalanceSheetReconciliation:
    global _rows
    rows = [item for item in _read() if item.get("reconciliation_id") != row.reconciliation_id]
    rows.append(row.model_dump())
    RECON_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECON_PATH.write_text(json.dumps(rows, indent=2) + "\n")
    _rows = rows
    return row


def load_reconciliations(period: str = "") -> list[BalanceSheetReconciliation]:
    rows = [BalanceSheetReconciliation.model_validate(item) for item in _read()]
    if period:
        rows = [item for item in rows if item.period == period]
    return rows


def save_trace(trace: ReconTrace) -> str:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{trace.reconciliation_id}.json"
    path.write_text(trace.model_dump_json(indent=2) + "\n")
    return str(path)


def get_trace(reconciliation_id: str):
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{reconciliation_id}.json"
    if path.exists():
        return ReconTrace.model_validate_json(path.read_text()), path
    matches = sorted(TRACES_DIR.glob(f"*{reconciliation_id}*.json"))
    if matches:
        return ReconTrace.model_validate_json(matches[0].read_text()), matches[0]
    for rec in load_reconciliations():
        if rec.reconciliation_id == reconciliation_id or rec.reconciliation_id.endswith(reconciliation_id):
            candidate = TRACES_DIR / f"{rec.reconciliation_id}.json"
            if candidate.exists():
                return ReconTrace.model_validate_json(candidate.read_text()), candidate
    return None, None
