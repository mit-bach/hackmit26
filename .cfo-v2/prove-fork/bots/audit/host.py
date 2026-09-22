"""Routine post-close-assurance wake body for Bot audit.

Python samples and re-performs. This host writes interpretation and report
packets under the Computer. It does not bind HARNESS_BOT. It does not drain
inboxes. Live bot_send_prompt is session 01/02.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from audit.report import format_audit_report
from audit.store import configure_paths
from audit.workflow import run_audit
from evaluation.isolation import evaluation_phase, operational_phase_guard

from bots.audit.grants import (
    AUDIT_BOT_ID,
    AUDIT_SLUG,
    INTERPRET_PROFILE,
    REPORT_PROFILE,
    GrantError,
    assert_op_allowed,
)
from bots.audit.paths import leased_write_json, leased_write_text, posix_rel

GROUND_TRUTH_OP = "audit.tools.get_audit_ground_truth"
CREATE_ACCRUAL_OP = "accrual.tools.create_accrual"


class AssuranceHostError(ValueError):
    """Fail-closed assurance host error."""


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "computer"


def _idempotency_key(period: str, pack_path: str, seed: int) -> str:
    blob = f"{period}|{pack_path}|{seed}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:24]


def _protocol_tail(computer: Path, limit: int = 20) -> list[str]:
    path = Path(computer) / "harness" / "protocol.jsonl"
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()[-limit:]


def _refuse_operational_eval_tool(phase: str) -> None:
    if phase != "operational":
        return
    try:
        assert_op_allowed(AUDIT_SLUG, INTERPRET_PROFILE, GROUND_TRUTH_OP, phase=phase)
    except GrantError:
        return
    raise AssuranceHostError("forbidden: operational interpret granted get_audit_ground_truth")


def run_assurance_host(
    computer: Path,
    period: str = "2026-09",
    *,
    pack_path: str = "",
    seed: int = 26,
    phase: str = "operational",
    persist: bool = True,
) -> dict:
    if phase not in {"operational", "evaluation"}:
        raise AssuranceHostError(f"unknown phase {phase!r}")
    _refuse_operational_eval_tool(phase)
    assert_op_allowed(
        AUDIT_SLUG,
        INTERPRET_PROFILE,
        "audit.tools.get_operational_decisions",
        phase=phase,
    )
    try:
        assert_op_allowed(AUDIT_SLUG, INTERPRET_PROFILE, CREATE_ACCRUAL_OP, phase=phase)
        raise AssuranceHostError("forbidden: interpret must not hold create_accrual")
    except GrantError:
        pass

    computer = Path(computer)
    computer.mkdir(parents=True, exist_ok=True)
    pack_rel = posix_rel(pack_path) if pack_path else ""
    if pack_rel:
        pack_file = computer / pack_rel
        if pack_file.is_file():
            pack_file.read_text(encoding="utf-8")

    runs_dir = computer / "runs" / "audit"
    configure_paths(runs_dir=runs_dir)
    guard = operational_phase_guard if phase == "operational" else evaluation_phase
    with guard():
        run = run_audit(period, seed=seed, use_agent=False, persist=persist)

    if run.source_records_mutated:
        raise AssuranceHostError("audit mutated source records")

    interpretation = run.interpretation.model_dump(mode="json") if run.interpretation else {}
    stats = run.stats.model_dump(mode="json")
    report_text = run.report_text or format_audit_report(run)
    cited = list(run.stats.finding_ids)
    key = _idempotency_key(period, pack_rel, seed)
    tail = _protocol_tail(computer)
    prefix = f"workspace/audit/{period}"
    wake = {
        "profile": INTERPRET_PROFILE,
        "slug": AUDIT_SLUG,
        "botId": AUDIT_BOT_ID,
        "period": period,
        "packPath": pack_rel,
        "protocolTailTool": "bot_get_agent_transcript_tail",
        "protocolTailLines": tail,
        "idempotencyKey": key,
        "phase": phase,
    }
    interpret_packet = {
        "profile": INTERPRET_PROFILE,
        "outputType": "AuditorInterpretation",
        "audit_run_id": run.audit_run_id,
        "interpretation": interpretation,
        "stats": stats,
        "finding_ids": cited,
        "source_records_mutated": run.source_records_mutated,
        "kernel_run_path": f"runs/audit/{period}-{run.audit_run_id}.json",
    }
    report_packet = {
        "profile": REPORT_PROFILE,
        "outputType": "AuditReportAgentOutput",
        "audit_run_id": run.audit_run_id,
        "narrative": report_text,
        "finding_ids_cited": cited,
        "unused_invented_ids": [],
        "stats": stats,
    }
    next_wake = {
        "toSlug": AUDIT_SLUG,
        "to": AUDIT_BOT_ID,
        "from": AUDIT_BOT_ID,
        "profile": REPORT_PROFILE,
        "kind": "a2a_handoff",
        "paths": [f"{prefix}/interpretation.json"],
        "prompt": (
            f"profile: {REPORT_PROFILE}\n"
            f"Write the audit report from ReportStats at {prefix}/interpretation.json. "
            "Do not invent IDs. Do not ask a human."
        ),
    }
    leased_write_json(computer, f"{prefix}/wake.json", wake)
    leased_write_json(computer, f"{prefix}/interpretation.json", interpret_packet)
    leased_write_json(computer, f"{prefix}/report.json", report_packet)
    leased_write_text(computer, f"{prefix}/report.md", report_text)
    leased_write_json(computer, f"{prefix}/next-wake.json", next_wake)
    leased_write_json(
        computer,
        f"runs/audit/{period}-host-{key}.json",
        {
            "audit_run_id": run.audit_run_id,
            "period": period,
            "idempotencyKey": key,
            "finding_ids": cited,
            "source_records_mutated": False,
        },
    )
    return {
        "audit_run_id": run.audit_run_id,
        "period": period,
        "finding_ids": cited,
        "finding_count": run.stats.finding_count,
        "source_records_mutated": False,
        "workspace": prefix,
        "next_wake": next_wake,
        "kernel_trace_path": run.trace_path,
    }
