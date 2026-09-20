"""Existing Python validators still run after mutating Kernel ops.

The model cannot talk past must_hold or a failed evaluate_close_gates.
HUMAN_REVIEW / HOLD / BLOCKED stay fail-closed. Sidecar never auto-posts.
"""

from __future__ import annotations

from typing import Any

from cfo_kernel import LOCK_OP

FAIL_CLOSED = frozenset({"HUMAN_REVIEW", "HOLD", "BLOCKED", "INSUFFICIENT"})


class GateFailed(RuntimeError):
    """Kernel close gate refused a lock."""


def is_fail_closed(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    for key in ("status", "decision", "reviewer_status", "disposition"):
        if result.get(key) in FAIL_CLOSED:
            return True
    return False


def apply_ap_must_hold(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    if result.get("decision") != "APPROVE":
        return result
    invoice_id = result.get("invoice_id")
    if not invoice_id:
        return result
    from tools import collect_case_evidence
    from workflow import _blocking_approve_violations

    evidence = collect_case_evidence(str(invoice_id))
    violations = _blocking_approve_violations(evidence)
    if not violations:
        return result
    out = dict(result)
    out["decision"] = "HOLD"
    out["must_hold"] = violations
    return out


def apply_close_gates(op: str, result: Any) -> Any:
    if op != LOCK_OP:
        return result
    from close.gating import evaluate_close_gates
    from close.models import MonthEndState

    state = result
    if isinstance(result, dict):
        state = MonthEndState.model_validate(result)
    if not isinstance(state, MonthEndState):
        return result
    gate = evaluate_close_gates(state)
    if state.period.status == "CLOSED" and not gate.passed:
        raise GateFailed(
            "evaluate_close_gates failed; Sidecar will not treat the period as locked. "
            + "; ".join(gate.blockers[:5])
        )
    return result


def after_mutate(op: str, result: Any) -> Any:
    """Run Kernel post-conditions. Never auto-post a fail-closed status."""
    held = apply_ap_must_hold(result)
    if is_fail_closed(held if isinstance(held, dict) else {}):
        return held
    return apply_close_gates(op, held)
