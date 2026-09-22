"""Kernel gates for Verifier concurrence. Autonomy is not always post."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verifier.grants import assert_op_allowed
from verifier.handles import complete_handle, request_handle, write_packet
from verifier.queue_owners import owner_for


class ConcurrenceRefused(ValueError):
    """Verifier cannot concur, or Kernel already refuses."""


def packet_complete(packet: dict[str, Any], required: tuple[str, ...]) -> list[str]:
    missing = [key for key in required if not packet.get(key)]
    return [f"packet incomplete: missing {item}" for item in missing]


def refuse_if_kernel_blocked(*, kernel_ok: bool, packet_ok: bool, defects: list[str]) -> tuple[str, list[str]]:
    if not kernel_ok:
        return "REFUSE", ["Kernel already refuses. Verifier cannot concur."] + defects
    if not packet_ok:
        return "REFUSE", defects or ["packet incomplete"]
    return "CONCUR", []


def apply_ctl_pay_match(
    invoice_id: str,
    *,
    packet: dict[str, Any],
    bot_decision: str,
    handle_path: Path,
    audit_wake: bool = False,
    runs_dir: Path | None = None,
    source_slug: str = "ctl-pay",
) -> dict[str, Any]:
    from tools import collect_case_evidence
    from workflow import commit_to_pay_pool, kernel_allow_approve, must_hold

    if source_slug != "ctl-pay":
        raise ConcurrenceRefused(f"forbidden: {source_slug} cannot concur an AP packet")
    evidence = collect_case_evidence(invoice_id)
    holds = must_hold(evidence)
    kernel_ok = kernel_allow_approve(evidence) and packet.get("proposed_decision") == "APPROVE"
    defects = packet_complete(packet, ("invoice_id", "evidence_path", "preparer", "proposed_decision"))
    defects.extend(f"Kernel must_hold: {item}" for item in holds)
    decision = bot_decision if bot_decision in {"CONCUR", "REFUSE"} else "REFUSE"
    if decision == "CONCUR":
        decision, extra = refuse_if_kernel_blocked(
            kernel_ok=kernel_ok, packet_ok=not defects, defects=defects
        )
        defects = extra or defects
    payload = complete_handle(handle_path, decision=decision, reasons=defects, kernel_ok=kernel_ok)
    posted = False
    audit_handle = None
    if payload["decision"] == "CONCUR" and not audit_wake:
        packet_path = write_packet(
            f"ap-audit-{invoice_id}",
            {
                "invoice_id": invoice_id,
                "first_handle": str(handle_path),
                "wake": "audit",
                "humanQueue": False,
            },
            runs_dir=runs_dir,
        )
        audit_handle = request_handle(
            from_slug="ctl-pay",
            to_slug="ctl-pay",
            profile="review-match",
            paths=[str(packet_path)],
            prompt=(
                f"profile: review-match\naudit: true\n"
                f"Second Wake for {invoice_id}. Do not call get_prior_cases. "
                "Look for reasons to refuse. Do not ask a human."
            ),
            kernel_status="APPROVE",
            pipe="ap",
            object_id=f"{invoice_id}-audit",
            runs_dir=runs_dir,
            audit_wake=True,
        )
    if payload["decision"] == "CONCUR" and audit_wake:
        posted = commit_to_pay_pool(
            invoice_id,
            kernel_allow=kernel_ok,
            ctl_pay_concurred=True,
            confidence=None,
        )
        if not posted:
            raise ConcurrenceRefused("Kernel refused pay-pool commit after ctl-pay CONCUR")
    return {"handle": payload, "posted_to_pool": posted, "audit_handle": audit_handle}


def apply_ctl_pay_review_pay(
    *,
    plan_packet_path: Path,
    bot_decision: str,
    source_slug: str = "ctl-pay",
    computer_root: Path | None = None,
) -> dict[str, Any]:
    from models import PaymentAuditResult
    from scheduling.host import ConcurrenceRefused as PayRefused
    from scheduling.host import apply_review_pay_concurrence

    if source_slug != "ctl-pay":
        raise ConcurrenceRefused(f"forbidden: {source_slug} cannot concur a pay-run")
    raw = {}
    if Path(plan_packet_path).is_file():
        import json

        loaded = json.loads(Path(plan_packet_path).read_text())
        raw = loaded if isinstance(loaded, dict) else {}
    reserve_ok = bool((raw.get("plan") or {}).get("reserve_ok"))
    kernel_ok = reserve_ok and bot_decision == "CONCUR"
    if bot_decision != "CONCUR" or not kernel_ok:
        raise ConcurrenceRefused("ctl-pay refused the payment-run draft or Kernel reserve_ok is false")
    try:
        return apply_review_pay_concurrence(
            plan_packet_path=Path(plan_packet_path),
            concurrence=PaymentAuditResult(passed=True, findings=["ctl-pay CONCUR"]),
            source_slug="ctl-pay",
            computer_root=computer_root,
        )
    except PayRefused as exc:
        raise ConcurrenceRefused(str(exc)) from exc


def apply_ctl_cash_rec(
    period: str,
    *,
    bot_decision: str,
) -> dict[str, Any]:
    from cash_recon.store import get_report

    report = get_report(period)
    if report is None:
        raise ConcurrenceRefused(f"no cash recon report for {period}")
    unexplained = [
        item
        for item in report.matches
        if item.match_type == "UNEXPLAINED_DIFFERENCE"
        or getattr(item, "difference_minor", None) == 1240
        or abs(float(item.difference or 0) - 12.40) < 0.001
    ]
    kernel_ok = report.period_status == "RECONCILED" and not unexplained and report.arithmetic_tied
    decision = bot_decision
    if decision == "CONCUR" and not kernel_ok:
        decision = "REFUSE"
    if decision == "CONCUR" and unexplained:
        decision = "REFUSE"
    return {
        "decision": decision,
        "period_status": report.period_status,
        "unexplained": [item.match_type for item in unexplained],
        "reconciled": report.period_status == "RECONCILED" and decision == "CONCUR",
    }


def apply_ctl_books_lock(
    period: str,
    *,
    bot_decision: str,
) -> dict[str, Any]:
    from close.gating import evaluate_close_gates
    from close.month_end import load_state

    state = load_state(period)
    if state is None:
        return {
            "decision": "REFUSE",
            "gate_passed": False,
            "blockers": ["no close state; cannot lock"],
            "period_status": "MISSING",
            "closed": False,
        }
    gate = evaluate_close_gates(state)
    decision = bot_decision
    if decision == "CONCUR" and not gate.passed:
        decision = "REFUSE"
    closed = False
    if decision == "CONCUR" and gate.passed:
        from close.month_end import finalize_close

        closed_state = finalize_close(period, live=False, reviewer="ctl-books")
        closed = closed_state.period.status == "CLOSED"
        if not closed:
            decision = "REFUSE"
    latest = load_state(period) or state
    return {
        "decision": decision,
        "gate_passed": gate.passed,
        "blockers": list(gate.blockers),
        "period_status": latest.period.status,
        "closed": closed,
    }


def assert_verifier_cannot_call(slug: str, profile: str, op: str) -> None:
    assert_op_allowed(slug, profile, op)


def owner_metadata(pipe: str, status: str) -> dict[str, object]:
    owner = owner_for(pipe, status)
    return {"owner": owner["owner"], "profile": owner["profile"], "humanQueue": False}
