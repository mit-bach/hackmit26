"""Reviewer-authored cash ledger lines and fee evidence applied to the cash recon dataset."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.mathutil import cents
from cash_recon.models import FeeEvidence, LedgerEntry

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
OVERLAY_PATH = STATE_DIR / "cash_overlays.json"


def configure_paths(directory: Path) -> None:
    global STATE_DIR, OVERLAY_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    OVERLAY_PATH = directory / "cash_overlays.json"


def reset_overlays() -> None:
    OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERLAY_PATH.write_text("{}\n")


def _read() -> dict:
    if not OVERLAY_PATH.exists():
        return {}
    raw = json.loads(OVERLAY_PATH.read_text())
    return raw if isinstance(raw, dict) else {}


def _write(payload: dict) -> None:
    OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERLAY_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def load_overlay(period: str) -> dict:
    rows = _read()
    item = rows.get(period) or {}
    return {
        "ledger_entries": list(item.get("ledger_entries") or []),
        "fee_evidence": list(item.get("fee_evidence") or []),
    }


def has_overlay(period: str) -> bool:
    item = load_overlay(period)
    return bool(item["ledger_entries"] or item["fee_evidence"])


def add_ledger_entry(period: str, entry: dict) -> dict:
    rows = _read()
    current = rows.setdefault(period, {"ledger_entries": [], "fee_evidence": []})
    existing = [item for item in current["ledger_entries"] if item.get("entry_id") == entry.get("entry_id")]
    if existing:
        return existing[0]
    current["ledger_entries"].append(entry)
    _write(rows)
    return entry


def add_fee_evidence(period: str, evidence: dict) -> dict:
    rows = _read()
    current = rows.setdefault(period, {"ledger_entries": [], "fee_evidence": []})
    existing = [item for item in current["fee_evidence"] if item.get("evidence_id") == evidence.get("evidence_id")]
    if existing:
        return existing[0]
    current["fee_evidence"].append(evidence)
    _write(rows)
    return evidence


def apply_overlays(period: str, ledger: list[LedgerEntry], fees: list[FeeEvidence]) -> tuple[list[LedgerEntry], list[FeeEvidence]]:
    overlay = load_overlay(period)
    extra_ledger = []
    for row in overlay["ledger_entries"]:
        item = LedgerEntry.model_validate(row)
        if not item.amount_minor:
            item.amount_minor = cents(item.amount)
        extra_ledger.append(item)
    extra_fees = []
    for row in overlay["fee_evidence"]:
        item = FeeEvidence.model_validate(row)
        if not item.amount_minor:
            item.amount_minor = cents(item.amount)
        extra_fees.append(item)
    known_ledger = {item.entry_id for item in ledger}
    known_fees = {item.evidence_id for item in fees}
    merged_ledger = list(ledger) + [item for item in extra_ledger if item.entry_id not in known_ledger]
    merged_fees = list(fees) + [item for item in extra_fees if item.evidence_id not in known_fees]
    return merged_ledger, merged_fees
