from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from agent import agent_for_ap_profile, investigator_agent, preparer_agent, run_agent
from ap_grants import (
    AP_BOT_ID,
    AP_SLUG,
    CTL_PAY_BOT_ID,
    CTL_PAY_MATCH_PROFILE,
    CTL_PAY_SLUG,
    INVESTIGATE_PROFILE,
    PREPARE_PROFILE,
    PROFILE_DISPLAY,
    GrantError,
    grants_for,
)
from atomic_json import write_json_atomic
from harness_handles import relative_to_computer, write_peer_handle
from models import (
    APCaseEvidence,
    DecisionTrace,
    FinalAPDecision,
    InvestigationReport,
    PreparerRecommendation,
)
from skills.loader import usage_from_agent
from tools import DataFileError, collect_case_evidence, load_invoice, vendor_alias_established


def _default_runs_dir() -> Path:
    computer = os.environ.get("HARNESS_COMPUTER")
    if computer:
        return Path(computer) / "runs"
    return Path(__file__).resolve().parent / "runs"


RUNS_DIR = _default_runs_dir()
MAX_RECONSIDERATIONS = 0

_active_profile: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def must_hold(evidence: APCaseEvidence) -> list[str]:
    """Hard policy holds that an APPROVE cannot survive."""
    violations: list[str] = []
    if evidence.duplicate_detected:
        violations.append("P-002 duplicate vendor invoice number")
    if not evidence.po_exists:
        violations.append("P-008 missing purchase order")
    elif not evidence.po_approved:
        violations.append("P-003 unapproved purchase order")
    if evidence.receipt_status in {"missing", "not_received"}:
        violations.append("P-004 goods not received")
    if evidence.receipt_status == "partial":
        violations.append("P-005 partial receipt paid in full")
    if (
        evidence.po_exists
        and not evidence.vendor_exact_match
        and "vendor_mismatch" in evidence.exception_types
        and not vendor_alias_established(evidence)
    ):
        violations.append("P-006 unknown vendor identity with no supporting prior case")
    if (
        "material_amount_mismatch" in evidence.exception_types
        and not evidence.within_amount_tolerance
    ):
        violations.append("P-009 amount variance exceeds published tolerance")
    if "approval_limit_exceeded" in evidence.exception_types:
        violations.append("P-010 purchase order exceeds recorded approval authority")
    return violations


def _blocking_approve_violations(evidence: APCaseEvidence) -> list[str]:
    return must_hold(evidence)


def kernel_allow_approve(evidence: APCaseEvidence) -> bool:
    return not must_hold(evidence)


def _needs_investigation(evidence: APCaseEvidence, preparer: PreparerRecommendation) -> bool:
    if evidence.exception_types:
        return True
    return preparer.recommendation == "INVESTIGATE"


@contextmanager
def profile_turn(profile: str) -> Iterator[str]:
    """One Profile per turn. Nesting would union Grants."""
    global _active_profile
    grants_for(AP_SLUG, profile)
    if _active_profile is not None:
        raise GrantError(
            f"cannot nest Profile {profile!r} onto {_active_profile!r}; do not union Grants"
        )
    _active_profile = profile
    try:
        yield profile
    finally:
        _active_profile = None


def wake_bot(
    *,
    slug: str,
    profile: str,
    prompt: str,
    paths: list[str],
    invoice_id: str,
) -> PreparerRecommendation | InvestigationReport:
    """Write a next-wake record, then run the bound Profile.

    Tests patch ``run_agent``. Office-live AP uses ``run_ap_kernel`` and
    Harness Handles. This function is the Kernel test host, not the Bot bus.
    """
    if slug != AP_SLUG:
        raise GrantError(f"AP host cannot wake slug {slug!r}")
    agent = agent_for_ap_profile(profile)
    record = {
        "bot": slug,
        "botId": AP_BOT_ID,
        "profile": profile,
        "displayName": PROFILE_DISPLAY[profile],
        "grants": list(grants_for(slug, profile)),
        "invoice_id": invoice_id,
        "prompt": prompt,
        "paths": paths,
        "createdAt": _now(),
        "kind": "wake",
    }
    wake_path = Path(RUNS_DIR) / "ap" / "wakes" / f"{invoice_id}-{profile}.json"
    write_json_atomic(wake_path, record)
    with profile_turn(profile):
        return run_agent(agent, prompt)


def _evidence_path(invoice_id: str) -> Path:
    return Path(RUNS_DIR) / "ap" / "packets" / f"{invoice_id}.evidence.json"


def _packet_path(invoice_id: str) -> Path:
    return Path(RUNS_DIR) / "ap" / "packets" / f"{invoice_id}.json"


def _handle_path(invoice_id: str) -> Path:
    return Path(RUNS_DIR) / "ap" / "handles" / f"{invoice_id}.json"


def _close_handle_path(invoice_id: str) -> Path:
    return Path(RUNS_DIR) / "ap" / "handles" / f"{invoice_id}-close.json"


def is_unreceived_period_work(evidence: APCaseEvidence) -> bool:
    return evidence.receipt_status in {"missing", "not_received"}


def kernel_preparer_recommendation(evidence: APCaseEvidence) -> PreparerRecommendation:
    """Deterministic prepare. Does not call Runner."""
    holds = must_hold(evidence)
    if holds:
        rec = "HOLD"
        reasons = [f"Kernel must_hold: {item}" for item in holds]
    elif evidence.exception_types:
        rec = "INVESTIGATE"
        reasons = [f"Kernel exception_types: {', '.join(evidence.exception_types)}"]
    else:
        rec = "APPROVE"
        reasons = ["Kernel three-way facts are clean."]
    return PreparerRecommendation(
        invoice_id=evidence.invoice_id,
        recommendation=rec,
        confidence=0.9 if rec == "APPROVE" else 0.7,
        reasons=reasons,
        evidence_used=[evidence.invoice_id],
        exception_types=list(evidence.exception_types),
    )


def kernel_investigation(
    evidence: APCaseEvidence,
    memory_block: str = "",
) -> InvestigationReport:
    """Deterministic investigate. Does not call Runner. Does not pay."""
    holds = must_hold(evidence)
    rec = "HOLD" if holds else "APPROVE"
    findings = [f"Kernel exception_types: {item}" for item in evidence.exception_types]
    if memory_block:
        findings.append("Retrieved operational AP memory. Precedent cannot override must_hold.")
    if holds:
        findings.extend(f"Kernel must_hold: {item}" for item in holds)
    return InvestigationReport(
        invoice_id=evidence.invoice_id,
        issues_investigated=list(evidence.exception_types),
        findings=findings or ["No extra vendor-specific facts beyond Kernel types."],
        relevant_precedents=[],
        relevant_policies=[],
        unresolved_risks=list(holds),
        recommendation=rec,
        confidence=0.7,
    )


def _write_evidence(invoice_id: str, evidence: APCaseEvidence) -> Path:
    path = _evidence_path(invoice_id)
    write_json_atomic(path, evidence.model_dump(mode="json"))
    return path


def _run_preparer(invoice_id: str, evidence_path: Path) -> PreparerRecommendation:
    rel = evidence_path.as_posix()
    return wake_bot(
        slug=AP_SLUG,
        profile=PREPARE_PROFILE,
        prompt=(
            f"profile: {PREPARE_PROFILE}\n"
            f"Prepare AP case {invoice_id}.\n"
            f"Kernel evidence path: {rel}\n"
            "Call get_case_evidence. Do not recalculate. Do not pay."
        ),
        paths=[rel],
        invoice_id=invoice_id,
    )


def _run_investigator(
    invoice_id: str,
    evidence_path: Path,
    preparer_path: Path,
    memory_block: str = "",
) -> InvestigationReport:
    rel = evidence_path.as_posix()
    prep = preparer_path.as_posix()
    extra = f"\n\n{memory_block}" if memory_block else ""
    return wake_bot(
        slug=AP_SLUG,
        profile=INVESTIGATE_PROFILE,
        prompt=(
            f"profile: {INVESTIGATE_PROFILE}\n"
            f"Investigate exceptions on invoice {invoice_id}.\n"
            f"Kernel evidence path: {rel}\n"
            f"Preparer packet path: {prep}\n"
            "Search policies and prior cases. If nothing supports payment, HOLD. Do not pay."
            f"{extra}"
        ),
        paths=[rel, prep],
        invoice_id=invoice_id,
    )


def _propose(
    evidence: APCaseEvidence,
    preparer: PreparerRecommendation,
    investigation: InvestigationReport | None,
) -> tuple[str, list[str], float, list[str], list[str]]:
    holds = must_hold(evidence)
    if investigation is not None:
        rec = investigation.recommendation
        confidence = investigation.confidence
        reasons = list(investigation.findings) or [investigation.recommendation]
        evidence_used = list(preparer.evidence_used)
    else:
        rec = preparer.recommendation
        confidence = preparer.confidence
        reasons = list(preparer.reasons)
        evidence_used = list(preparer.evidence_used)
    if rec == "INVESTIGATE":
        rec = "HOLD"
        reasons.append("Final AP state cannot be INVESTIGATE; held.")
    if holds:
        rec = "HOLD"
        reasons.extend(f"Kernel must_hold: {item}" for item in holds)
        confidence = min(confidence, 0.7)
    if rec not in {"APPROVE", "HOLD"}:
        rec = "HOLD"
        reasons.append("Unknown recommendation held closed.")
    return rec, reasons, confidence, evidence_used, holds


def _write_match_packet(
    invoice_id: str,
    evidence_path: Path,
    preparer: PreparerRecommendation,
    investigation: InvestigationReport | None,
    proposed: str,
    holds: list[str],
) -> Path:
    profiles = [PREPARE_PROFILE]
    if investigation is not None:
        profiles.append(INVESTIGATE_PROFILE)
    payload = {
        "invoice_id": invoice_id,
        "bot": AP_SLUG,
        "profiles_run": profiles,
        "evidence_path": evidence_path.as_posix(),
        "preparer": preparer.model_dump(mode="json"),
        "investigation": investigation.model_dump(mode="json") if investigation else None,
        "kernel_holds": holds,
        "proposed_decision": proposed,
        "posted_to_pool": False,
    }
    path = _packet_path(invoice_id)
    write_json_atomic(path, payload)
    return path


def _write_ctl_pay_handle(
    invoice_id: str,
    packet_path: Path,
    proposed: str,
    *,
    computer_root: Path | None = None,
) -> dict | None:
    if proposed != "APPROVE":
        return None
    handle_id = f"h_{uuid4()}"
    rel = packet_path.as_posix()
    prompt = (
        f"profile: {CTL_PAY_MATCH_PROFILE}\n"
        f"Review AP match packet at {rel}\n"
        "Concur or refuse. Do not ask a human. Peer Handle is not approval."
    )
    payload = {
        "id": handle_id,
        "from": AP_BOT_ID,
        "fromSlug": AP_SLUG,
        "to": CTL_PAY_BOT_ID,
        "toSlug": CTL_PAY_SLUG,
        "profile": CTL_PAY_MATCH_PROFILE,
        "prompt": prompt,
        "paths": [rel],
        "kind": "a2a_handoff",
        "status": "accepted",
        "conversation": {
            "kind": "peer_dm",
            "fromId": AP_BOT_ID,
            "toId": CTL_PAY_BOT_ID,
        },
        "verifier_missing": False,
        "invoice_id": invoice_id,
        "createdAt": _now(),
        "path": str(_handle_path(invoice_id)),
        "queue": {"owner": CTL_PAY_SLUG, "profile": CTL_PAY_MATCH_PROFILE},
        "humanQueue": False,
        "done": False,
        "bus": "harness",
        "op": "bot_send_prompt",
    }
    write_json_atomic(_handle_path(invoice_id), payload)
    computer = computer_root
    if computer is None:
        env = os.environ.get("HARNESS_COMPUTER")
        computer = Path(env) if env else None
    if computer is not None:
        try:
            rel_paths = [relative_to_computer(computer, packet_path)]
            dest, harness = write_peer_handle(
                computer,
                from_slug=AP_SLUG,
                to_slug=CTL_PAY_SLUG,
                profile=CTL_PAY_MATCH_PROFILE,
                paths=rel_paths,
                prompt=prompt,
                extra={"invoice_id": invoice_id, "verifier_missing": False},
                handle_id=handle_id,
            )
            payload["harness_path"] = str(dest)
            payload["id"] = harness["id"]
        except OSError:
            pass
    return payload


def _write_close_handle(
    invoice_id: str,
    packet_path: Path,
    evidence: APCaseEvidence,
    *,
    computer_root: Path | None = None,
) -> dict | None:
    if not is_unreceived_period_work(evidence):
        return None
    handle_id = f"h_{uuid4()}"
    rel = packet_path.as_posix()
    prompt = (
        f"profile: coordinate\n"
        f"Unreceived period work on bill {invoice_id}. Packet: {rel}\n"
        "This Handle is accrual input. It is not approval. Do not pay."
    )
    payload = {
        "id": handle_id,
        "from": AP_BOT_ID,
        "fromSlug": AP_SLUG,
        "to": "bot_close",
        "toSlug": "close",
        "profile": "coordinate",
        "prompt": prompt,
        "paths": [rel],
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "invoice_id": invoice_id,
        "approval": False,
        "createdAt": _now(),
        "path": str(_close_handle_path(invoice_id)),
        "queue": {"owner": "close", "profile": "coordinate"},
        "humanQueue": False,
        "bus": "harness",
        "op": "bot_send_prompt",
    }
    write_json_atomic(_close_handle_path(invoice_id), payload)
    computer = computer_root
    if computer is None:
        env = os.environ.get("HARNESS_COMPUTER")
        computer = Path(env) if env else None
    if computer is not None:
        try:
            rel_paths = [relative_to_computer(computer, packet_path)]
            dest, harness = write_peer_handle(
                computer,
                from_slug=AP_SLUG,
                to_slug="close",
                profile="coordinate",
                paths=rel_paths,
                prompt=prompt,
                extra={"invoice_id": invoice_id, "approval": False},
                handle_id=handle_id,
            )
            payload["harness_path"] = str(dest)
            payload["id"] = harness["id"]
        except OSError:
            pass
    return payload


def commit_to_pay_pool(
    invoice_id: str,
    *,
    kernel_allow: bool,
    ctl_pay_concurred: bool,
    confidence: float | None = None,
) -> bool:
    """Session 09 calls this after ctl-pay concurs. The AP host never auto-calls it."""
    if not kernel_allow or not ctl_pay_concurred:
        return False
    from scheduling.pool import add_approved

    add_approved(invoice_id, source="ctl_pay", confidence=confidence)
    return True


def complete_ctl_pay_handle(
    invoice_id: str,
    *,
    bot_decision: str,
    source_slug: str,
    audit_wake: bool = False,
    runs_dir: Path | None = None,
) -> dict:
    """Kernel door for ctl-pay concurrence. Bot ap cannot call this as itself."""
    import json

    from verifier.concurrence import apply_ctl_pay_match

    packet_path = _packet_path(invoice_id)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise ValueError(f"AP packet {packet_path} is not an object")
    return apply_ctl_pay_match(
        invoice_id,
        packet=packet,
        bot_decision=bot_decision,
        handle_path=_handle_path(invoice_id),
        audit_wake=audit_wake,
        source_slug=source_slug,
        runs_dir=runs_dir or Path(RUNS_DIR),
    )


def _build_final(
    evidence: APCaseEvidence,
    proposed: str,
    reasons: list[str],
    confidence: float,
    evidence_used: list[str],
    investigation_performed: bool,
    pending_verifier: bool,
) -> FinalAPDecision:
    audit_status = "PENDING_CTL_PAY" if pending_verifier else "KERNEL_HOLD"
    if proposed == "HOLD" and not pending_verifier:
        audit_status = "HELD" if not must_hold(evidence) else "KERNEL_HOLD"
    return FinalAPDecision(
        invoice_id=evidence.invoice_id,
        decision=proposed,  # type: ignore[arg-type]
        confidence=confidence,
        reasons=reasons,
        amount_difference=evidence.amount_difference,
        duplicate_detected=evidence.duplicate_detected,
        receipt_status=evidence.receipt_status,
        evidence_used=evidence_used,
        investigation_performed=investigation_performed,
        audit_status=audit_status,
        reconsideration_performed=False,
    )


def _save_trace(trace: DecisionTrace) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RUNS_DIR / f"{trace.invoice_id}-{stamp}.json"
    trace.trace_path = str(path)
    write_json_atomic(path, trace.model_dump(mode="json"))
    return path


def run_ap_workflow(invoice_id: str) -> DecisionTrace:
    if load_invoice(invoice_id) is None:
        raise DataFileError(f"Invoice {invoice_id} was not found")

    started_at = _now()
    evidence = collect_case_evidence(invoice_id)
    evidence_path = _write_evidence(invoice_id, evidence)

    print(f"Invoice: {invoice_id}", flush=True)
    print(f"Python facts: exceptions={evidence.exception_types or ['none']}", flush=True)
    print(flush=True)

    invoice_date = evidence.invoice.invoice_date if evidence.invoice else started_at[:10]
    period = invoice_date[:7] if invoice_date else started_at[:7]
    from memory.format import format_precedents
    from memory.hooks import (
        apply_ap_precedent,
        lookup_for_ap,
        write_ap_alias_memory,
        write_ap_memory,
    )

    memory_lookup = lookup_for_ap(evidence, period)
    memory_block = format_precedents(memory_lookup)

    preparer = _run_preparer(invoice_id, evidence_path)
    preparer_note = Path(RUNS_DIR) / "ap" / "packets" / f"{invoice_id}.prepare.json"
    write_json_atomic(preparer_note, preparer.model_dump(mode="json"))

    investigation = None
    if _needs_investigation(evidence, preparer):
        investigation = _run_investigator(
            invoice_id, evidence_path, preparer_note, memory_block=memory_block
        )

    proposed, reasons, confidence, evidence_used, holds = _propose(
        evidence, preparer, investigation
    )
    memory_lookup = apply_ap_precedent(evidence, memory_lookup, holds)
    packet_path = _write_match_packet(
        invoice_id, evidence_path, preparer, investigation, proposed, holds
    )
    handle = _write_ctl_pay_handle(invoice_id, packet_path, proposed)
    close_handle = _write_close_handle(invoice_id, packet_path, evidence)
    pending = handle is not None
    final = _build_final(
        evidence,
        proposed,
        reasons,
        confidence,
        evidence_used,
        investigation_performed=investigation is not None,
        pending_verifier=pending,
    )

    ran = [preparer_agent]
    if investigation is not None:
        ran.append(investigator_agent)

    if investigation is not None and memory_lookup.precedents:
        extra = [
            f"{item.decision_id}: {item.reusable_precedent}" for item in memory_lookup.precedents
        ]
        investigation = investigation.model_copy(
            update={"relevant_precedents": list(dict.fromkeys(list(investigation.relevant_precedents) + extra))}
        )
        memory_lookup.decision = final.decision
    written = write_ap_memory(evidence, final, period=period, trace_id=invoice_id)
    alias = write_ap_alias_memory(evidence, period=period, trace_id=invoice_id)
    written_id = written[0].decision_id if written is not None else None
    if written_id is None and alias is not None:
        written_id = alias[0].decision_id
    trace = DecisionTrace(
        invoice_id=invoice_id,
        started_at=started_at,
        deterministic_evidence=evidence,
        preparer=preparer,
        investigation=investigation,
        reviewer=None,
        approver=None,
        audit=None,
        reconsideration=None,
        final=final,
        agents=[usage_from_agent(item) for item in ran],
        packet_path=str(packet_path),
        verifier_handle=handle,
        close_handle=close_handle,
        kernel_holds=holds,
        posted_to_pool=False,
        memory_lookup=memory_lookup,
        written_memory_id=written_id,
        wakes=[
            {
                "slug": AP_SLUG,
                "profile": PREPARE_PROFILE,
                "path": str(Path(RUNS_DIR) / "ap" / "wakes" / f"{invoice_id}-{PREPARE_PROFILE}.json"),
            }
        ],
    )
    if investigation is not None:
        trace.wakes.append(
            {
                "slug": AP_SLUG,
                "profile": INVESTIGATE_PROFILE,
                "path": str(
                    Path(RUNS_DIR) / "ap" / "wakes" / f"{invoice_id}-{INVESTIGATE_PROFILE}.json"
                ),
            }
        )
    _save_trace(trace)
    return trace


def run_ap_kernel(invoice_id: str, *, computer_root: Path | None = None) -> DecisionTrace:
    """Office-shaped AP host. Kernel facts win. Does not call Runner."""
    if load_invoice(invoice_id) is None:
        raise DataFileError(f"Invoice {invoice_id} was not found")

    started_at = _now()
    evidence = collect_case_evidence(invoice_id)
    evidence_path = _write_evidence(invoice_id, evidence)
    invoice_date = evidence.invoice.invoice_date if evidence.invoice else started_at[:10]
    period = invoice_date[:7] if invoice_date else started_at[:7]
    from memory.format import format_precedents
    from memory.hooks import (
        apply_ap_precedent,
        lookup_for_ap,
        write_ap_alias_memory,
        write_ap_memory,
    )

    memory_lookup = lookup_for_ap(evidence, period)
    memory_block = format_precedents(memory_lookup)
    preparer = kernel_preparer_recommendation(evidence)
    preparer_note = Path(RUNS_DIR) / "ap" / "packets" / f"{invoice_id}.prepare.json"
    write_json_atomic(preparer_note, preparer.model_dump(mode="json"))
    investigation = None
    if _needs_investigation(evidence, preparer):
        investigation = kernel_investigation(evidence, memory_block=memory_block)
    proposed, reasons, confidence, evidence_used, holds = _propose(
        evidence, preparer, investigation
    )
    memory_lookup = apply_ap_precedent(evidence, memory_lookup, holds)
    packet_path = _write_match_packet(
        invoice_id, evidence_path, preparer, investigation, proposed, holds
    )
    handle = _write_ctl_pay_handle(
        invoice_id, packet_path, proposed, computer_root=computer_root
    )
    close_handle = _write_close_handle(
        invoice_id, packet_path, evidence, computer_root=computer_root
    )
    final = _build_final(
        evidence,
        proposed,
        reasons,
        confidence,
        evidence_used,
        investigation_performed=investigation is not None,
        pending_verifier=handle is not None,
    )
    if investigation is not None and memory_lookup.precedents:
        extra = [
            f"{item.decision_id}: {item.reusable_precedent}" for item in memory_lookup.precedents
        ]
        investigation = investigation.model_copy(
            update={
                "relevant_precedents": list(
                    dict.fromkeys(list(investigation.relevant_precedents) + extra)
                )
            }
        )
        memory_lookup.decision = final.decision
    written = write_ap_memory(evidence, final, period=period, trace_id=invoice_id)
    alias = write_ap_alias_memory(evidence, period=period, trace_id=invoice_id)
    written_id = written[0].decision_id if written is not None else None
    if written_id is None and alias is not None:
        written_id = alias[0].decision_id
    trace = DecisionTrace(
        invoice_id=invoice_id,
        started_at=started_at,
        deterministic_evidence=evidence,
        preparer=preparer,
        investigation=investigation,
        reviewer=None,
        approver=None,
        audit=None,
        reconsideration=None,
        final=final,
        agents=[],
        packet_path=str(packet_path),
        verifier_handle=handle,
        close_handle=close_handle,
        kernel_holds=holds,
        posted_to_pool=False,
        memory_lookup=memory_lookup,
        written_memory_id=written_id,
        wakes=[],
    )
    _save_trace(trace)
    return trace
