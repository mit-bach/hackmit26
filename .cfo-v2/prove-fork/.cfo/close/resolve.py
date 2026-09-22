"""Human review resolutions. Original cash/AP/AR/recon traces are never deleted."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from close.models import ReviewResolution

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
RESOLUTIONS_PATH = STATE_DIR / "resolutions.json"


def configure_paths(directory: Path) -> None:
    global STATE_DIR, RESOLUTIONS_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    RESOLUTIONS_PATH = directory / "resolutions.json"


def load_resolutions(period: str = "") -> list[ReviewResolution]:
    if not RESOLUTIONS_PATH.exists():
        return []
    rows = json.loads(RESOLUTIONS_PATH.read_text())
    items = [ReviewResolution.model_validate(item) for item in rows]
    if period:
        items = [item for item in items if item.period == period]
    return items


def is_resolved(item_id: str, period: str = "") -> bool:
    return any(item.item_id == item_id for item in load_resolutions(period))


def resolved_ids(period: str = "") -> set[str]:
    return {item.item_id for item in load_resolutions(period)}


def remember_resolution(item: ReviewResolution) -> ReviewResolution:
    rows = load_resolutions()
    for existing in rows:
        if existing.item_id == item.item_id and existing.period == item.period:
            return existing
    rows.append(item)
    RESOLUTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESOLUTIONS_PATH.write_text(json.dumps([row.model_dump() for row in rows], indent=2) + "\n")
    return item


def _lookup_original(item_id: str, period: str) -> tuple[str, str]:
    from cash_recon.store import get_match
    from bs_recon.store import load_reconciliations

    match = get_match(item_id)
    if match is not None:
        return match.status, match.explanation
    for rec in load_reconciliations(period):
        if rec.reconciliation_id == item_id:
            return rec.status, rec.explanation
        for row in rec.reconciling_items:
            if row.item_id == item_id:
                return row.status, row.description
    return "", ""


def resolve_review(
    item_id: str,
    resolution: str,
    *,
    period: str = "2026-09",
    reviewer: str = "human",
) -> ReviewResolution:
    if not resolution.strip():
        raise ValueError("A resolution explanation is required.")
    original_status, original_detail = _lookup_original(item_id, period)
    item = ReviewResolution(
        resolution_id=f"RES-{item_id}",
        item_id=item_id,
        period=period,
        resolution=resolution.strip(),
        reviewer=reviewer,
        created_at=now_iso(),
        original_status=original_status,
        original_detail=original_detail,
    )
    return remember_resolution(item)
