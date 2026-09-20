"""Verifier Handle payloads. Queue owner is a Bot, never the human Operator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ar.models import CashApplyTrace, CollectionDecision, CollectionFacts, CustomerPayment
from ar import store as ar_store
from atomic_json import write_json_atomic


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    write_json_atomic(path, payload)
    return path


def write_packet(name: str, payload: dict[str, Any]) -> Path:
    ar_store.PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    return _write_json(ar_store.PACKETS_DIR / f"{name}.json", payload)


def write_handle(name: str, payload: dict[str, Any]) -> Path:
    ar_store.HANDLES_DIR.mkdir(parents=True, exist_ok=True)
    path = ar_store.HANDLES_DIR / f"{name}.json"
    if path.exists():
        existing = json.loads(path.read_text())
        if existing.get("idempotencyKey") == payload.get("idempotencyKey"):
            return path
    return _write_json(path, payload)


def apply_verifier_handle(trace: CashApplyTrace) -> tuple[Path, Path]:
    """Fail-closed apply → Handle ctl-cash / review-apply. Not a human queue item."""
    packet = {
        "object": "unapplied_cash",
        "payment_id": trace.payment_id,
        "kernel_status": trace.final.decision,
        "as_of": trace.as_of_date,
        "reason": trace.final.reason,
        "ambiguities": list(trace.final.ambiguities),
        "review_question": trace.final.review_question,
        "applications": [row.model_dump(mode="json") for row in trace.final.applications],
        "candidates": [row.model_dump(mode="json") for row in trace.facts.candidates],
        "trace_path": trace.trace_path,
        "queue_owner": "ctl-cash",
        "queue_profile": "review-apply",
        "human_queue": False,
    }
    packet_path = write_packet(f"apply-{trace.payment_id}", packet)
    handle = {
        "from": "apply",
        "to": "ctl-cash",
        "toSlug": "ctl-cash",
        "profile": "review-apply",
        "kind": "a2a_handoff",
        "status": "accepted",
        "prompt": (
            f"profile: review-apply\n"
            f"Concur or refuse cash application for {trace.payment_id}. "
            f"Packet path is the evidence. Kernel status is {trace.final.decision}. "
            "Do not AUTO_APPLY past a Kernel refuse. Do not ask a human."
        ),
        "paths": [str(packet_path)],
        "kernelStatus": trace.final.decision,
        "queueOwner": "ctl-cash",
        "queue": {"owner": "ctl-cash", "profile": "review-apply"},
        "humanQueue": False,
        "idempotencyKey": f"apply:{trace.payment_id}:{trace.final.decision}",
        "createdAt": _now(),
    }
    handle_path = write_handle(f"apply-{trace.payment_id}-ctl-cash", handle)
    return handle_path, packet_path


def collect_drain_handle(as_of: str, payments: list[CustomerPayment]) -> Path:
    payment_ids = [item.payment_id for item in payments]
    packet_path = write_packet(
        f"collect-drain-{as_of}",
        {
            "object": "unapplied_cash",
            "as_of": as_of,
            "payment_ids": payment_ids,
            "reason": "Aging Routine woke collect before apply drained new deposits.",
            "human_queue": False,
        },
    )
    return write_handle(
        f"collect-drain-{as_of}",
        {
            "from": "collect",
            "to": "apply",
            "toSlug": "apply",
            "profile": "apply",
            "kind": "a2a_handoff",
            "status": "accepted",
            "prompt": (
                f"profile: apply\n"
                f"Drain new deposits dated on or before {as_of} before collect may chase. "
                f"Payment ids: {', '.join(payment_ids)}. Wake names the packet path."
            ),
            "paths": [str(packet_path)],
            "queueOwner": "apply",
            "humanQueue": False,
            "idempotencyKey": f"collect:drain:{as_of}:{','.join(payment_ids)}",
            "createdAt": _now(),
        },
    )


def collect_writeoff_handle(facts: CollectionFacts, decision: CollectionDecision) -> Path:
    packet_path = write_packet(
        f"collect-writeoff-{facts.invoice_id}",
        {
            "object": "open_invoice",
            "invoice_id": facts.invoice_id,
            "customer_id": facts.customer_id,
            "outstanding_amount": facts.outstanding_amount,
            "days_past_due": facts.days_past_due,
            "action": decision.action,
            "reason": decision.reason,
            "queue_owner": "ctl-pay",
            "human_queue": False,
        },
    )
    return write_handle(
        f"collect-{facts.invoice_id}-ctl-pay",
        {
            "from": "collect",
            "to": "ctl-pay",
            "toSlug": "ctl-pay",
            "profile": "review-pay",
            "kind": "a2a_handoff",
            "status": "accepted",
            "prompt": (
                f"profile: review-pay\n"
                f"Write-off or reserve packet for {facts.invoice_id}. "
                "Concur only if the Kernel allows taking this balance off the books. "
                "Do not ask a human."
            ),
            "paths": [str(packet_path)],
            "queueOwner": "ctl-pay",
            "queue": {"owner": "ctl-pay", "profile": "review-pay"},
            "humanQueue": False,
            "idempotencyKey": f"collect:writeoff:{facts.invoice_id}:{decision.action}",
            "createdAt": _now(),
        },
    )


def persist_drain(as_of: str, payment_ids: list[str]) -> Path:
    return _write_json(
        ar_store.DRAIN_PATH,
        {
            "as_of": as_of,
            "drained_payment_ids": payment_ids,
            "drained_at": _now(),
        },
    )
