"""Read-only close facts for ctl-books / lock. These ops cannot mark CLOSED."""

from __future__ import annotations

from agents import function_tool

from close.profile_grants import LOCK_DOOR, TEST_PACKET

QUEUE_OWNER = "ctl-books"


def _gate_payload(period: str) -> dict:
    from close.gating import evaluate_close_gates
    from close.month_end import load_state
    from close.period_lock import period_status

    state = load_state(period)
    lock_status = period_status(period)
    if state is None:
        return {
            "found": False,
            "period": period,
            "passed": False,
            "gate_passed": False,
            "blockers": ["no close state; cannot lock"],
            "lock_door": LOCK_DOOR,
            "test_packet": TEST_PACKET,
            "can_mark_closed": False,
            "queue_owner": QUEUE_OWNER,
            "human_queue": False,
            "lock_status": lock_status,
            "period_status": "MISSING",
        }
    gate = evaluate_close_gates(state)
    payload = gate.model_dump(mode="json")
    payload.update(
        {
            "found": True,
            "gate_passed": gate.passed,
            "lock_door": LOCK_DOOR,
            "test_packet": TEST_PACKET,
            "can_mark_closed": False,
            "queue_owner": QUEUE_OWNER,
            "human_queue": False,
            "lock_status": lock_status,
            "period_status": state.period.status,
        }
    )
    return payload


def _packet_payload(period: str) -> dict:
    import json
    import os
    from pathlib import Path

    from close.month_end import load_state
    from close.period_lock import period_status
    from harness_handles import default_computer_root

    computer_env = os.environ.get("HARNESS_COMPUTER")
    computer = Path(computer_env) if computer_env else default_computer_root()
    pack_rel = f"workspace/close/{period}/pack.json"
    pack_path = computer / pack_rel
    pack = None
    if pack_path.is_file():
        pack = json.loads(pack_path.read_text())
    state = load_state(period)
    return {
        "found": pack is not None or state is not None,
        "period": period,
        "pack_path": pack_rel if pack_path.is_file() else "",
        "pack": pack,
        "lock_door": LOCK_DOOR,
        "test_packet": TEST_PACKET,
        "can_mark_closed": False,
        "queue_owner": QUEUE_OWNER,
        "human_queue": False,
        "lock_status": period_status(period),
        "period_status": (pack or {}).get("status")
        or (state.period.status if state is not None else "MISSING"),
        "marked_closed": bool((pack or {}).get("marked_closed")),
        "exceptions": (
            [item.model_dump(mode="json") for item in state.exceptions] if state is not None else []
        ),
    }


@function_tool
def get_close_gates(period: str) -> dict:
    """Return evaluate_close_gates facts. Read-only. Cannot mark CLOSED."""
    return _gate_payload(period)


@function_tool
def get_close_packet(period: str) -> dict:
    """Return the period pack path and Kernel close facts. Read-only. Cannot mark CLOSED."""
    return _packet_payload(period)
