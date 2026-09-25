"""Verifier Handle payloads for bank-rec. Queue owner is ctl-cash, never a person."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atomic_json import write_json_atomic
from cash_recon.models import ReconciliationMatch

_PACKETS_DIR: Path | None = None
_HANDLES_DIR: Path | None = None


def configure_handle_dirs(*, packets_dir: Path | None = None, handles_dir: Path | None = None) -> None:
    global _PACKETS_DIR, _HANDLES_DIR
    if packets_dir is not None:
        path = Path(packets_dir)
        path.mkdir(parents=True, exist_ok=True)
        _PACKETS_DIR = path
    if handles_dir is not None:
        path = Path(handles_dir)
        path.mkdir(parents=True, exist_ok=True)
        _HANDLES_DIR = path


def _root_branch(name: str) -> Path:
    computer = os.environ.get("HARNESS_COMPUTER")
    if computer:
        path = Path(computer) / "runs" / "cash_recon" / name
        path.mkdir(parents=True, exist_ok=True)
        return path
    from cash_recon.store import RUNS_DIR

    path = Path(RUNS_DIR) / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def packets_dir() -> Path:
    if _PACKETS_DIR is not None:
        return _PACKETS_DIR
    return _root_branch("packets")


def handles_dir() -> Path:
    if _HANDLES_DIR is not None:
        return _HANDLES_DIR
    return _root_branch("handles")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    write_json_atomic(path, payload)
    return path


def write_packet(name: str, payload: dict[str, Any]) -> Path:
    return _write_json(packets_dir() / f"{name}.json", payload)


def write_handle(name: str, payload: dict[str, Any]) -> Path:
    path = handles_dir() / f"{name}.json"
    key = payload.get("idempotencyKey")
    if path.exists() and key:
        existing = json.loads(path.read_text())
        if existing.get("idempotencyKey") == key:
            if existing.get("kernelStatus") != payload.get("kernelStatus") or existing.get("to") != payload.get("to"):
                raise ValueError(f"idempotency_mismatch:{name}")
            return path
    return _write_json(path, payload)


def _unposted(match: ReconciliationMatch) -> bool:
    return all(not entry.posted for entry in match.proposed_adjusting_entries)


def investigate_wake(match: ReconciliationMatch, *, period: str, case_id: str) -> Path:
    """Same Bot, Profile investigate. Not a child. Not approval."""
    packet_path = write_packet(
        f"cash-investigate-{match.reconciliation_id}",
        {
            "object": "unmatched_bank_line",
            "period": period,
            "case_id": case_id,
            "reconciliation_id": match.reconciliation_id,
            "candidate_id": match.candidate_id,
            "match_type": match.match_type,
            "kernel_status": match.status,
            "difference_minor": match.difference_minor,
            "queue_owner": "cash",
            "human_queue": False,
        },
    )
    return write_handle(
        f"cash-{match.reconciliation_id}-investigate",
        {
            "from": "cash",
            "to": "cash",
            "toSlug": "cash",
            "profile": "investigate",
            "kind": "a2a_handoff",
            "status": "accepted",
            "prompt": (
                f"profile: investigate\n"
                f"Investigate {match.reconciliation_id} ({match.match_type}). "
                f"Case path: runs/cash_recon/cases/{case_id}.json. "
                "Do not invent an explanation. Do not ask a human."
            ),
            "paths": [str(packet_path)],
            "kernelStatus": match.status,
            "queueOwner": "cash",
            "humanQueue": False,
            "idempotencyKey": f"cash:investigate:{period}:{match.reconciliation_id}:{match.match_type}",
            "createdAt": _now(),
        },
    )


def verifier_handle(match: ReconciliationMatch, *, period: str, case_id: str) -> tuple[Path, Path]:
    """Fail-closed rec → Handle ctl-cash / review-rec. Not a human queue item."""
    if not _unposted(match):
        raise ValueError("refuse Handle: proposed fee journal is posted")
    packet_path = write_packet(
        f"cash-rec-{match.reconciliation_id}",
        {
            "object": "unmatched_bank_line",
            "period": period,
            "case_id": case_id,
            "reconciliation_id": match.reconciliation_id,
            "candidate_id": match.candidate_id,
            "match_type": match.match_type,
            "kernel_status": match.status,
            "difference": match.difference,
            "difference_minor": match.difference_minor,
            "explanation": match.explanation,
            "control_findings": list(match.control_findings),
            "proposed_adjusting_entries_posted": False,
            "queue_owner": "ctl-cash",
            "human_queue": False,
        },
    )
    handle_path = write_handle(
        f"cash-{match.reconciliation_id}-ctl-cash",
        {
            "from": "cash",
            "to": "ctl-cash",
            "toSlug": "ctl-cash",
            "profile": "review-rec",
            "kind": "a2a_handoff",
            "status": "accepted",
            "prompt": (
                f"profile: review-rec\n"
                f"Concur or refuse bank-rec {match.reconciliation_id}. "
                f"Kernel status is {match.status} ({match.match_type}). "
                "Do not force MATCHED. Do not ask a human. Packet path is the evidence."
            ),
            "paths": [str(packet_path)],
            "kernelStatus": match.status,
            "queueOwner": "ctl-cash",
            "queue": {"owner": "ctl-cash", "profile": "review-rec"},
            "humanQueue": False,
            "idempotencyKey": f"cash:review-rec:{period}:{match.reconciliation_id}:{match.status}",
            "createdAt": _now(),
        },
    )
    return handle_path, packet_path


NEEDS_INVESTIGATION = {
    "FEE_NETTED",
    "TIMING_DIFFERENCE",
    "POSSIBLE_DUPLICATE_BANK_TXN",
    "POSSIBLE_DUPLICATE_REFUND",
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
    "UNEXPLAINED_DIFFERENCE",
    "UNMATCHED_BANK",
    "UNMATCHED_LEDGER",
}


def persist_rec_queue(*, period: str, case_id: str, matches: list[ReconciliationMatch]) -> list[Path]:
    written: list[Path] = []
    for match in matches:
        if match.match_type in NEEDS_INVESTIGATION or match.human_review:
            written.append(investigate_wake(match, period=period, case_id=case_id))
        if match.human_review or match.status == "HUMAN_REVIEW" or match.match_type == "UNEXPLAINED_DIFFERENCE":
            handle_path, packet_path = verifier_handle(match, period=period, case_id=case_id)
            written.extend([handle_path, packet_path])
    return written
