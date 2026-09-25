"""Weekly pay-run host. Bot pay proposes. Kernel nets. ctl-pay concurs.

This module is the Routine ``weekly-pay-run`` wake body. It does not run
Payment Audit in-process. It does not execute ACH. It writes a next-wake
record that session 01/02 execute as Harness ``bot_send_prompt``.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from atomic_json import write_json_atomic
from harness_handles import write_peer_handle
from models import (
    CashPosition,
    PaymentAuditResult,
    PaymentCandidate,
    PaymentPlan,
    ScheduleTrace,
    ScheduledPayment,
)
from scheduling.cash import (
    apply_cash_and_policy_net,
    compute_metrics,
    load_cash_position,
    spendable_cash,
)
from scheduling.grants import AP_RECORD_OP_IDS, PAY_SCHEDULE_OP_IDS, profile_allows
from scheduling.pool import candidates_from_pool, load_pool

Chooser = Callable[[list[PaymentCandidate], CashPosition], PaymentPlan]

PAY_BOT_ID = "bot_pay"
PAY_SLUG = "pay"
CTL_PAY_BOT_ID = "bot_ctl_pay"
CTL_PAY_SLUG = "ctl-pay"
CASH_BOT_ID = "bot_cash"
CASH_SLUG = "cash"
SCHEDULE_PROFILE = "schedule"
REVIEW_PAY_PROFILE = "review-pay"
PENDING_AUDIT_FINDING = (
    "Pay-run concurrence is Handle ctl-pay/review-pay. Pay does not self-approve."
)


class PayHostError(ValueError):
    """Fail-closed host error."""


class IdempotencyMismatch(PayHostError):
    """Same idempotency key, different request hash."""


class ConcurrenceRefused(PayHostError):
    """Verifier did not concur, or pay tried to self-approve."""


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path("/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3")


def kernel_runs_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "runs"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_handle_id() -> str:
    return f"h_{uuid.uuid4()}"


def _dump(model: object) -> dict:
    return model.model_dump(mode="json")  # type: ignore[union-attr]


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def claim_idempotency(path: Path, request_hash: str, result: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"request_hash": request_hash, "result": result}
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        existing = json.loads(path.read_text())
        if not isinstance(existing, dict):
            raise IdempotencyMismatch(f"corrupt idempotency file {path}") from exc
        if existing.get("request_hash") != request_hash:
            raise IdempotencyMismatch(
                f"idempotency_mismatch for {path.name}"
            ) from exc
        stored = existing.get("result")
        if not isinstance(stored, dict):
            raise IdempotencyMismatch(f"corrupt idempotency result {path}") from exc
        return stored
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps(record, indent=2, default=str) + "\n")
    return result


def greedy_propose(
    candidates: list[PaymentCandidate], cash: CashPosition
) -> PaymentPlan:
    """Propose every pool ID. Kernel policy net binds. Totals here are discarded."""
    paid = [
        ScheduledPayment(
            invoice_id=item.invoice_id,
            amount=item.pay_amount_if_this_week,
            reason="Chooser proposed the approved pool. Kernel policy net binds.",
        )
        for item in candidates
    ]
    return PaymentPlan(
        as_of_date=cash.as_of_date,
        pay_this_week=paid,
        defer=[],
        total_payout=0.0,
        cash_after_payments=0.0,
        reserve_ok=True,
        reasons=["Chooser proposed the full approved pool. Kernel policy net binds."],
        confidence=0.5,
    )


def proposed_ids_from_plan(
    proposed: PaymentPlan, candidates: list[PaymentCandidate]
) -> list[str]:
    allowed = {item.invoice_id for item in candidates}
    ids: list[str] = []
    seen: set[str] = set()
    for row in proposed.pay_this_week:
        if row.invoice_id not in allowed or row.invoice_id in seen:
            continue
        ids.append(row.invoice_id)
        seen.add(row.invoice_id)
    return ids


def pending_audit(plan: PaymentPlan) -> PaymentAuditResult:
    violations: list[str] = []
    if not plan.reserve_ok:
        violations.append("P-013 minimum cash reserve")
    return PaymentAuditResult(
        passed=False,
        findings=[PENDING_AUDIT_FINDING],
        policy_violations=violations,
    )


def assert_schedule_grant(op_id: str) -> None:
    if not profile_allows(SCHEDULE_PROFILE, op_id):
        raise PayHostError(f"forbidden: pay/{SCHEDULE_PROFILE} cannot call {op_id}")
    if op_id in AP_RECORD_OP_IDS:
        raise PayHostError(f"forbidden: pay cannot load AP RECORD_TOOLS ({op_id})")


def _relative(computer_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(computer_root.resolve()))
    except ValueError:
        return str(path)


def write_plan_packet(
    computer_root: Path,
    *,
    plan_id: str,
    cash: CashPosition,
    candidates: list[PaymentCandidate],
    proposed_ids: list[str],
    plan: PaymentPlan,
    metrics: object,
) -> Path:
    path = computer_root / "workspace" / "pay" / "plans" / f"{plan_id}.json"
    write_json_atomic(
        path,
        {
            "plan_id": plan_id,
            "bot": PAY_SLUG,
            "profile": SCHEDULE_PROFILE,
            "as_of_date": cash.as_of_date,
            "proposed_ids": proposed_ids,
            "cash": _dump(cash),
            "spendable_cash": spendable_cash(cash),
            "candidates": [_dump(item) for item in candidates],
            "plan": _dump(plan),
            "metrics": _dump(metrics),
            "executed": False,
            "self_approved": False,
        },
    )
    return path


def write_ctl_pay_wake(
    computer_root: Path,
    *,
    plan_id: str,
    plan_path: Path,
    handle_id: str,
) -> Path:
    rel_plan = _relative(computer_root, plan_path)
    created = _now()
    payload = {
        "version": "1",
        "bus": "harness",
        "op": "bot_send_prompt",
        "status": "accepted",
        "done": False,
        "id": handle_id,
        "from": PAY_BOT_ID,
        "fromSlug": PAY_SLUG,
        "to": CTL_PAY_BOT_ID,
        "toSlug": CTL_PAY_SLUG,
        "profile": REVIEW_PAY_PROFILE,
        "kind": "a2a_handoff",
        "conversation": {
            "kind": "peer_dm",
            "fromId": PAY_BOT_ID,
            "toId": CTL_PAY_BOT_ID,
        },
        "paths": [rel_plan],
        "prompt": (
            f"profile: {REVIEW_PAY_PROFILE}\n"
            f"Review the payment-run draft at {rel_plan}.\n"
            "Concur only if Kernel reserve_ok is true and the packet is complete.\n"
            "Do not rebuild the plan. Do not execute ACH or wire. Do not ask a human."
        ),
        "createdAt": created,
        "updatedAt": created,
        "note": (
            "Session 01/02 execute this as bot_send_prompt. "
            "Pay does not mark complete. Peer Handle is not approval."
        ),
        "plan_id": plan_id,
    }
    wake_path = computer_root / "workspace" / "pay" / "wakes" / f"{handle_id}.json"
    write_json_atomic(wake_path, payload)
    write_peer_handle(
        computer_root,
        from_slug=PAY_SLUG,
        to_slug=CTL_PAY_SLUG,
        profile=REVIEW_PAY_PROFILE,
        paths=[rel_plan],
        prompt=payload["prompt"],
        extra={"plan_id": plan_id},
        handle_id=handle_id,
    )
    return wake_path


def write_expected_outflows(
    computer_root: Path,
    *,
    plan_id: str,
    plan: PaymentPlan,
    candidates: list[PaymentCandidate],
    concurrence: PaymentAuditResult,
) -> Path:
    by_id = {item.invoice_id: item for item in candidates}
    wires = []
    for row in plan.pay_this_week:
        item = by_id.get(row.invoice_id)
        wires.append(
            {
                "invoice_id": row.invoice_id,
                "amount": row.amount,
                "vendor": item.vendor if item else None,
                "direction": "outflow",
                "capture_discount": row.capture_discount,
            }
        )
    path = (
        computer_root
        / "workspace"
        / "cash"
        / "expected-outflows"
        / f"{plan_id}.json"
    )
    write_json_atomic(
        path,
        {
            "kind": "expected_outflows",
            "source": PAY_SLUG,
            "after": f"{CTL_PAY_SLUG}/{REVIEW_PAY_PROFILE}",
            "plan_id": plan_id,
            "as_of_date": plan.as_of_date,
            "wires": wires,
            "total_payout": plan.total_payout,
            "reserve_ok": plan.reserve_ok,
            "executed": False,
            "concurrence": _dump(concurrence),
        },
    )
    return path


def write_cash_wake(
    computer_root: Path,
    *,
    plan_id: str,
    outflow_path: Path,
    handle_id: str,
) -> Path:
    rel = _relative(computer_root, outflow_path)
    created = _now()
    payload = {
        "version": "1",
        "bus": "harness",
        "op": "bot_send_prompt",
        "status": "accepted",
        "done": False,
        "id": handle_id,
        "from": PAY_BOT_ID,
        "fromSlug": PAY_SLUG,
        "to": CASH_BOT_ID,
        "toSlug": CASH_SLUG,
        "profile": "match",
        "kind": "a2a_handoff",
        "conversation": {
            "kind": "peer_dm",
            "fromId": PAY_BOT_ID,
            "toId": CASH_BOT_ID,
        },
        "paths": [rel],
        "prompt": (
            f"profile: match\n"
            f"Identified AP wires after {CTL_PAY_SLUG}/{REVIEW_PAY_PROFILE} concurrence. "
            f"Packet: {rel}. Do not treat as posted cash. Pay did not execute ACH."
        ),
        "createdAt": created,
        "updatedAt": created,
        "plan_id": plan_id,
    }
    path = computer_root / "workspace" / "cash" / "wakes" / f"{handle_id}.json"
    write_json_atomic(path, payload)
    write_peer_handle(
        computer_root,
        from_slug=PAY_SLUG,
        to_slug=CASH_SLUG,
        profile="match",
        paths=[rel],
        prompt=payload["prompt"],
        extra={"plan_id": plan_id, "executed": False},
        handle_id=handle_id,
    )
    return path


def run_schedule_host(
    *,
    chooser: Chooser | None = None,
    computer_root: Path | None = None,
    runs_dir: Path | None = None,
    idempotency_key: str | None = None,
) -> ScheduleTrace:
    """Load pool + cash → candidates → chooser → policy net → Handle ctl-pay."""
    for op_id in PAY_SCHEDULE_OP_IDS:
        assert_schedule_grant(op_id)

    computer = Path(computer_root) if computer_root is not None else default_computer_root()
    runs = Path(runs_dir) if runs_dir is not None else kernel_runs_dir()
    cash = load_cash_position()
    pool_rows = load_pool()
    candidates = candidates_from_pool()
    if not candidates:
        raise PayHostError(
            "Approved invoice pool is empty. Run AP validation on invoices first, "
            "or seed a demo pool with: python main.py schedule --seed-demo"
        )

    started_at = _now()
    print(f"Payment schedule as of {cash.as_of_date}", flush=True)
    print(f"Spendable cash: ${spendable_cash(cash):,.2f}", flush=True)
    print(f"Approved pool: {len(candidates)} invoices", flush=True)
    print(flush=True)

    propose = chooser or greedy_propose
    proposed = propose(candidates, cash)
    proposed_ids = proposed_ids_from_plan(proposed, candidates)
    plan = apply_cash_and_policy_net(candidates, proposed_ids, cash)
    plan = plan.model_copy(
        update={
            "reasons": list(proposed.reasons) + plan.reasons,
            "confidence": proposed.confidence,
        }
    )
    metrics = compute_metrics(candidates, plan, cash)
    audit = pending_audit(plan)

    pool_ids = sorted(str(row.get("invoice_id")) for row in pool_rows)
    request_hash = _canonical_hash(
        {
            "as_of_date": cash.as_of_date,
            "pool_ids": pool_ids,
            "proposed_ids": proposed_ids,
            "pay_this_week": [row.invoice_id for row in plan.pay_this_week],
        }
    )
    plan_id = f"plan_{cash.as_of_date}_{request_hash[:12]}"
    key = idempotency_key or f"pay-schedule:{cash.as_of_date}:{request_hash[:16]}"
    idemp_path = computer / "cfo" / "idempotency" / f"{key.replace(':', '_')}.json"

    if idemp_path.exists():
        existing = json.loads(idemp_path.read_text())
        if not isinstance(existing, dict) or existing.get("request_hash") != request_hash:
            raise IdempotencyMismatch(f"idempotency_mismatch for {idemp_path.name}")
        stored = existing.get("result")
        if isinstance(stored, dict) and stored.get("trace"):
            return ScheduleTrace.model_validate(stored["trace"])

    runs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trace_path = runs / f"schedule-{stamp}.json"
    handle_id = _new_handle_id()
    plan_path = write_plan_packet(
        computer,
        plan_id=plan_id,
        cash=cash,
        candidates=candidates,
        proposed_ids=proposed_ids,
        plan=plan,
        metrics=metrics,
    )
    wake_path = write_ctl_pay_wake(
        computer, plan_id=plan_id, plan_path=plan_path, handle_id=handle_id
    )
    trace = ScheduleTrace(
        as_of_date=cash.as_of_date,
        started_at=started_at,
        cash=cash,
        spendable_cash=spendable_cash(cash),
        candidates=candidates,
        plan=plan,
        metrics=metrics,
        audit=audit,
        agents=[],
        trace_path=str(trace_path),
        plan_packet_path=str(plan_path),
        verifier_wake_path=str(wake_path),
        outflow_packet_path=None,
    )
    stored = claim_idempotency(
        idemp_path,
        request_hash,
        {
            "plan_id": plan_id,
            "handle_id": handle_id,
            "trace": trace.model_dump(mode="json"),
        },
    )
    if stored.get("handle_id") != handle_id:
        return ScheduleTrace.model_validate(stored["trace"])
    trace_path.write_text(trace.model_dump_json(indent=2) + "\n")
    return trace


def apply_review_pay_concurrence(
    *,
    plan_packet_path: Path,
    concurrence: PaymentAuditResult,
    source_slug: str,
    computer_root: Path | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Kernel door after ctl-pay / review-pay. Pay must not call this as itself."""
    if source_slug != CTL_PAY_SLUG:
        raise ConcurrenceRefused(
            f"forbidden: {source_slug} cannot concur a pay-run; owner is {CTL_PAY_SLUG}"
        )
    if not concurrence.passed:
        raise ConcurrenceRefused("ctl-pay refused the payment-run draft")

    computer = Path(computer_root) if computer_root is not None else default_computer_root()
    raw = json.loads(Path(plan_packet_path).read_text())
    if not isinstance(raw, dict):
        raise PayHostError("plan packet must be a JSON object")
    plan = PaymentPlan.model_validate(raw["plan"])
    candidates = [
        PaymentCandidate.model_validate(item) for item in raw.get("candidates") or []
    ]
    if not plan.reserve_ok:
        raise ConcurrenceRefused("Kernel reserve_ok is false; refuse release")

    proposed_ids = [row.invoice_id for row in plan.pay_this_week]
    cash = CashPosition.model_validate(raw["cash"])
    netted = apply_cash_and_policy_net(candidates, proposed_ids, cash)
    if {row.invoice_id for row in netted.pay_this_week} != {
        row.invoice_id for row in plan.pay_this_week
    }:
        raise ConcurrenceRefused("Kernel policy net no longer matches the draft")
    if not netted.reserve_ok:
        raise ConcurrenceRefused("Kernel reserve_ok is false after re-net")

    plan_id = str(raw.get("plan_id") or "plan")
    key = idempotency_key or f"pay-outflows:{plan_id}"
    idemp_path = computer / "cfo" / "idempotency" / f"{key.replace(':', '_')}.json"
    request_hash = _canonical_hash(
        {"plan_id": plan_id, "pay_this_week": proposed_ids, "source": source_slug}
    )

    outflow_path = write_expected_outflows(
        computer,
        plan_id=plan_id,
        plan=netted,
        candidates=candidates,
        concurrence=concurrence,
    )
    cash_handle = _new_handle_id()
    cash_wake = write_cash_wake(
        computer, plan_id=plan_id, outflow_path=outflow_path, handle_id=cash_handle
    )
    result = {
        "plan_id": plan_id,
        "outflow_packet_path": str(outflow_path),
        "cash_wake_path": str(cash_wake),
        "executed": False,
        "wires": json.loads(outflow_path.read_text())["wires"],
    }
    return claim_idempotency(idemp_path, request_hash, result)
