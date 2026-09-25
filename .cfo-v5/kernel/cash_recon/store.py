"""In-memory cash-reconciliation store with JSON traces. Not a production ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cash_recon.models import CashReconciliationReport, MatchTrace, ReconciliationMatch

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs" / "cash_recon"
TRACES_DIR = ROOT / "traces" / "cash_recon"

_matches: dict[str, ReconciliationMatch] = {}
_traces: dict[str, MatchTrace] = {}
_reports: dict[str, CashReconciliationReport] = {}


def configure_paths(*, runs_dir: Path | None = None, traces_dir: Path | None = None) -> None:
    global RUNS_DIR, TRACES_DIR
    if runs_dir is not None:
        RUNS_DIR = Path(runs_dir)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if traces_dir is not None:
        TRACES_DIR = Path(traces_dir)
        TRACES_DIR.mkdir(parents=True, exist_ok=True)


def reset_cash_state() -> None:
    _matches.clear()
    _traces.clear()
    _reports.clear()


def clear_period(period: str) -> None:
    for key in [key for key, item in _matches.items() if item.period == period]:
        del _matches[key]
    for key in [key for key, item in _traces.items() if item.period == period]:
        del _traces[key]
    _reports.pop(period, None)


def match_lookup_key(period: str, match_key: str) -> str:
    return f"{period}:{match_key}"


def remember_match(row: ReconciliationMatch) -> tuple[ReconciliationMatch, bool]:
    key = match_lookup_key(row.period, row.match_key or row.reconciliation_id)
    existing = _matches.get(key)
    if existing is not None:
        return existing, False
    _matches[key] = row
    return row, True


def get_match(reconciliation_id: str) -> ReconciliationMatch | None:
    for item in _matches.values():
        if item.reconciliation_id == reconciliation_id:
            return item
    return None


def matches_for_period(period: str) -> list[ReconciliationMatch]:
    return [item for item in _matches.values() if item.period == period]


def _trace_key(trace: MatchTrace) -> str:
    return f"{trace.period}:{trace.reconciliation_id}"


def remember_trace(trace: MatchTrace) -> tuple[MatchTrace, bool]:
    key = _trace_key(trace)
    existing = _traces.get(key)
    if existing is not None:
        existing.replay = True
        return existing, False
    _traces[key] = trace
    return trace, True


def get_trace(reconciliation_id: str) -> MatchTrace | None:
    matches = [item for item in _traces.values() if item.reconciliation_id == reconciliation_id]
    if not matches:
        return None
    return matches[-1]


def traces_for_period(period: str) -> list[MatchTrace]:
    return [item for item in _traces.values() if item.period == period]


def remember_report(report: CashReconciliationReport) -> tuple[CashReconciliationReport, bool]:
    existing = _reports.get(report.period)
    if existing is not None and existing.matches:
        existing.replay = True
        return existing, False
    _reports[report.period] = report
    return report, True


def get_report(period: str) -> CashReconciliationReport | None:
    return _reports.get(period)


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        text = payload.model_dump_json(indent=2)
    else:
        text = json.dumps(payload, indent=2, default=str)
    path.write_text(text + "\n")
    return path


def save_trace(trace: MatchTrace, *, run_id: str) -> MatchTrace:
    directory = TRACES_DIR / trace.period / run_id
    path = write_json(directory / f"{trace.reconciliation_id}.json", trace)
    trace.trace_path = str(path)
    return trace


def save_report(report: CashReconciliationReport) -> CashReconciliationReport:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = write_json(RUNS_DIR / f"{report.period}-{report.run_id}.json", report)
    report.trace_path = str(path)
    report.trace_dir = str(TRACES_DIR / report.period / report.run_id)
    return report


def find_trace(reconciliation_id: str) -> MatchTrace | None:
    stored = get_trace(reconciliation_id)
    if stored is not None:
        return stored
    if not TRACES_DIR.exists():
        return None
    needle = f"{reconciliation_id}.json"
    for path in TRACES_DIR.rglob(needle):
        payload = json.loads(path.read_text())
        trace = MatchTrace.model_validate(payload)
        trace.trace_path = str(path)
        return trace
    return None
