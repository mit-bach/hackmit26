"""Structured audit correction history. Does not change deterministic controls."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from audit.models import AuditCorrection, AuditFinding
from audit import store as audit_store


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def history_path() -> Path:
    return Path(audit_store.RUNS_DIR) / "corrections.json"


def load_corrections() -> list[AuditCorrection]:
    path = history_path()
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [AuditCorrection.model_validate(item) for item in raw]


def save_corrections(rows: list[AuditCorrection]) -> Path:
    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([item.model_dump(mode="json") for item in rows], indent=2) + "\n")
    return path


def record_correction(
    *,
    issue_key: str,
    object_id: str,
    control_id: str,
    finding_id: str = "",
    action: str = "corrective_action",
    notes: str = "",
    valid: bool = True,
) -> AuditCorrection:
    rows = load_corrections()
    correction = AuditCorrection(
        correction_id=f"COR-{len(rows) + 1:03d}",
        issue_key=issue_key,
        finding_id=finding_id,
        object_id=object_id,
        control_id=control_id,
        valid=valid,
        action=action,
        recorded_at=_now(),
        notes=notes,
    )
    rows.append(correction)
    save_corrections(rows)
    return correction


def annotate_findings(findings: list[AuditFinding], corrections: list[AuditCorrection] | None = None) -> list[AuditFinding]:
    """Mark repeat issues. Does not change control predicates."""
    history = corrections if corrections is not None else load_corrections()
    by_key = {item.issue_key: item for item in history if item.valid}
    annotated = []
    for finding in findings:
        key = finding.issue_key or f"{finding.control_id}:{finding.affected_object_ids[0]}"
        prior = by_key.get(key)
        if prior:
            finding = finding.model_copy(
                update={
                    "issue_key": key,
                    "recurring": True,
                    "prior_correction_id": prior.correction_id,
                    "recommended_follow_up": (
                        f"Repeat finding after correction {prior.correction_id}: {prior.notes or prior.action}."
                    ),
                }
            )
        annotated.append(finding)
    return annotated
