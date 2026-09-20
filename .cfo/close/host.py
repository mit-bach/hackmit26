"""Month-end host. Bot close sequences Profiles as separate Wakes.

Routine ``month-end`` wakes Profile ``coordinate``. Coordinate reads
``ready_tasks`` and sends a new Wake to this same Bot with the next
treatment Profile. Grants never union. This host does not mark CLOSED.
``ctl-books`` / ``lock`` concurs after ``evaluate_close_gates`` passes.
The one Kernel lock door is ``close.month_end``.
``close.orchestrator.run_cfo_close`` is a test packet, not period lock.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from atomic_json import write_json_atomic
from close.agents import deterministic_coordinate
from close.checklist import ready_tasks, refresh_readiness, unresolved_blockers
from close.gating import evaluate_close_gates
from close.models import MonthEndState
from close.month_end import configure_paths, run_month_end
from close.profile_grants import (
    CREATE_ACCRUAL,
    DISPLAY_NAMES,
    LOCK_DOOR,
    PROFILE_OPS,
    TEST_PACKET,
    assert_profile_grant,
    mutating_ops,
)

CLOSE_BOT_ID = "bot_close"
CLOSE_SLUG = "close"
CTL_BOOKS_BOT_ID = "bot_ctl_books"
CTL_BOOKS_SLUG = "ctl-books"
STORY_BOT_ID = "bot_story"
STORY_SLUG = "story"
AUDIT_BOT_ID = "bot_audit"
AUDIT_SLUG = "audit"
COORDINATE_PROFILE = "coordinate"
REVIEW_TREATMENT_PROFILE = "review-treatment"
LOCK_PROFILE = "lock"

TREATMENT_TASKS: dict[str, str] = {
    "accruals": "accrue",
    "prepaid": "prepaid",
    "depreciation": "assets",
    "bs_recon": "bs",
}

PEER_TASKS: dict[str, tuple[str, str]] = {
    "ingest": ("email", "invoice"),
    "ap": ("ap", "prepare"),
    "ar": ("collect", "chase"),
    "cash": ("cash", "match"),
}

LOCK_TASKS = frozenset({"exceptions", "final_review", "mark_closed"})


class CloseHostError(ValueError):
    """Fail-closed host error."""


class CloseHostRun(BaseModel):
    period: str
    status: str
    gate_passed: bool
    marked_closed: bool
    lock_door: str = LOCK_DOOR
    test_packet: str = TEST_PACKET
    pack_path: str = ""
    wake_paths: list[str] = Field(default_factory=list)
    handle_paths: list[str] = Field(default_factory=list)
    profiles_worn: list[str] = Field(default_factory=list)
    blocked_on: list[str] = Field(default_factory=list)
    live_handles: bool = False


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / ".cfo-v2" / "office" / "computer"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _relative(computer_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(computer_root.resolve()))
    except ValueError:
        return str(path)


def _work(computer: Path, period: str) -> Path:
    path = computer / "workspace" / "close" / period
    path.mkdir(parents=True, exist_ok=True)
    (path / "wakes").mkdir(exist_ok=True)
    (path / "handles").mkdir(exist_ok=True)
    return path


def _write_idempotent(path: Path, payload: dict, key: str) -> Path:
    if path.exists():
        existing = json.loads(path.read_text())
        if isinstance(existing, dict) and existing.get("idempotencyKey") == key:
            return path
        if isinstance(existing, dict) and existing.get("idempotencyKey") not in {None, key}:
            raise CloseHostError(f"idempotency_mismatch:{path.name}")
    write_json_atomic(path, payload)
    return path


def assert_no_grant_union(profile: str) -> None:
    if profile not in PROFILE_OPS:
        raise CloseHostError(f"unknown close profile {profile}")
    if profile != "accrue" and CREATE_ACCRUAL in PROFILE_OPS[profile]:
        raise CloseHostError(f"forbidden: close/{profile} holds {CREATE_ACCRUAL}")
    if mutating_ops(COORDINATE_PROFILE):
        raise CloseHostError("forbidden: close/coordinate has mutating Catalog ops")


def write_coordinate_wake(
    computer: Path,
    *,
    period: str,
    seq: int,
    state: MonthEndState,
) -> Path:
    assert_no_grant_union(COORDINATE_PROFILE)
    for op_id in PROFILE_OPS[COORDINATE_PROFILE]:
        assert_profile_grant(COORDINATE_PROFILE, op_id)
    decision = deterministic_coordinate(state)
    work = _work(computer, period)
    key = f"close:{period}:coordinate:{seq}"
    ready = [item.task_id for item in ready_tasks(state.tasks)]
    payload = {
        "version": "1",
        "bus": "harness",
        "kind": "profile_wake",
        "status": "accepted",
        "done": False,
        "id": f"h_close_{period}_coordinate_{seq:03d}",
        "from": CLOSE_BOT_ID,
        "fromSlug": CLOSE_SLUG,
        "to": CLOSE_BOT_ID,
        "toSlug": CLOSE_SLUG,
        "profile": COORDINATE_PROFILE,
        "displayName": DISPLAY_NAMES[COORDINATE_PROFILE],
        "ops": list(PROFILE_OPS[COORDINATE_PROFILE]),
        "mutatingOps": list(mutating_ops(COORDINATE_PROFILE)),
        "task_id": "coordinate",
        "period": period,
        "next_tasks": decision.next_tasks or ready,
        "blocked_tasks": decision.blocked_tasks,
        "can_close": decision.can_close,
        "mark_closed": False,
        "lock_door": LOCK_DOOR,
        "prompt": (
            f"profile: {COORDINATE_PROFILE}\n"
            f"Read ready_tasks for {period}. Send a new Wake to Bot close "
            "with the next treatment Profile. Do not union Grants. "
            "Do not mark CLOSED. Do not ask a human."
        ),
        "idempotencyKey": key,
        "createdAt": _now(),
        "live_sent": False,
    }
    path = work / "wakes" / f"{seq:03d}-coordinate.json"
    return _write_idempotent(path, payload, key)


def write_treatment_wake(
    computer: Path,
    *,
    period: str,
    seq: int,
    task_id: str,
    profile: str,
) -> Path:
    assert_no_grant_union(profile)
    for op_id in PROFILE_OPS[profile]:
        assert_profile_grant(profile, op_id)
    work = _work(computer, period)
    key = f"close:{period}:{profile}:{task_id}"
    payload = {
        "version": "1",
        "bus": "harness",
        "kind": "profile_wake",
        "status": "accepted",
        "done": False,
        "id": f"h_close_{period}_{profile}_{task_id}",
        "from": CLOSE_BOT_ID,
        "fromSlug": CLOSE_SLUG,
        "fromProfile": COORDINATE_PROFILE,
        "to": CLOSE_BOT_ID,
        "toSlug": CLOSE_SLUG,
        "profile": profile,
        "displayName": DISPLAY_NAMES[profile],
        "ops": list(PROFILE_OPS[profile]),
        "mutatingOps": list(mutating_ops(profile)),
        "task_id": task_id,
        "period": period,
        "prompt": (
            f"profile: {profile}\n"
            f"Run close task {task_id} for {period}. "
            "Choose among Kernel candidates. Do not invent amounts. "
            "After this treatment, Handle ctl-books / review-treatment."
        ),
        "idempotencyKey": key,
        "createdAt": _now(),
        "live_sent": False,
    }
    path = work / "wakes" / f"{seq:03d}-{CLOSE_SLUG}-{profile}.json"
    return _write_idempotent(path, payload, key)


def write_peer_handle(
    computer: Path,
    *,
    period: str,
    seq: int,
    task_id: str,
    slug: str,
    profile: str,
) -> Path:
    work = _work(computer, period)
    key = f"close:{period}:peer:{task_id}"
    bot_id = f"bot_{slug.replace('-', '_')}"
    payload = {
        "version": "1",
        "bus": "harness",
        "op": "bot_send_prompt",
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "id": f"h_close_{period}_{task_id}",
        "from": CLOSE_BOT_ID,
        "fromSlug": CLOSE_SLUG,
        "fromProfile": COORDINATE_PROFILE,
        "to": bot_id,
        "toSlug": slug,
        "profile": profile,
        "task_id": task_id,
        "period": period,
        "prompt": (
            f"profile: {profile}\n"
            f"Close checklist task {task_id} for {period} is ready. "
            "Peer Handle is not approval. Do not ask a human."
        ),
        "idempotencyKey": key,
        "createdAt": _now(),
        "live_sent": False,
        "note": "Session 01/02 execute this as bot_send_prompt. Kernel still ran the checklist handler.",
    }
    path = work / "handles" / f"{seq:03d}-{slug}-{task_id}.json"
    return _write_idempotent(path, payload, key)


def write_ctl_books_handle(
    computer: Path,
    *,
    period: str,
    profile: str,
    pack_path: Path,
    kernel_status: str,
    task_id: str = "",
) -> Path:
    work = _work(computer, period)
    rel = _relative(computer, pack_path)
    suffix = task_id or profile
    key = f"close:{period}:ctl-books:{profile}:{suffix}"
    payload = {
        "version": "1",
        "bus": "harness",
        "op": "bot_send_prompt",
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "id": f"h_close_{period}_ctl_books_{suffix}",
        "from": CLOSE_BOT_ID,
        "fromSlug": CLOSE_SLUG,
        "to": CTL_BOOKS_BOT_ID,
        "toSlug": CTL_BOOKS_SLUG,
        "profile": profile,
        "period": period,
        "task_id": task_id,
        "kernelStatus": kernel_status,
        "queueOwner": CTL_BOOKS_SLUG,
        "queue": {"owner": CTL_BOOKS_SLUG, "profile": profile},
        "humanQueue": False,
        "paths": [rel],
        "prompt": (
            f"profile: {profile}\n"
            f"Concur or refuse close packet {rel} for {period}. "
            f"Kernel status is {kernel_status}. "
            "Do not create_accrual. Do not flip period lock unless "
            "evaluate_close_gates already passed. Do not ask a human."
        ),
        "idempotencyKey": key,
        "createdAt": _now(),
        "live_sent": False,
        "note": "Session 09 owns live ctl-books. This Handle is the queue item.",
    }
    path = work / "handles" / f"ctl-books-{suffix}.json"
    return _write_idempotent(path, payload, key)


def write_pack_peer_handle(
    computer: Path,
    *,
    period: str,
    slug: str,
    bot_id: str,
    profile: str,
    pack_path: Path,
    lock_status: str,
) -> Path:
    work = _work(computer, period)
    rel = _relative(computer, pack_path)
    key = f"close:{period}:{slug}:pack"
    payload = {
        "version": "1",
        "bus": "harness",
        "op": "bot_send_prompt",
        "kind": "a2a_handoff",
        "status": "accepted",
        "done": False,
        "id": f"h_close_{period}_{slug}",
        "from": CLOSE_BOT_ID,
        "fromSlug": CLOSE_SLUG,
        "to": bot_id,
        "toSlug": slug,
        "profile": profile,
        "paths": [rel],
        "prompt": (
            f"profile: {profile}\n"
            f"Close pack for {period} is at {rel}. lock_status={lock_status}. "
            "Peer Handle is not approval. Do not ask a human."
        ),
        "idempotencyKey": key,
        "createdAt": _now(),
        "live_sent": False,
    }
    path = work / "handles" / f"{slug}-pack.json"
    return _write_idempotent(path, payload, key)


def write_pack(computer: Path, state: MonthEndState, gate) -> Path:
    work = _work(computer, state.period.period)
    path = work / "pack.json"
    payload = {
        "period": state.period.period,
        "status": state.period.status,
        "close_id": state.close_id,
        "lock_door": LOCK_DOOR,
        "test_packet": TEST_PACKET,
        "marked_closed": state.period.status == "CLOSED",
        "gate_passed": gate.passed,
        "gate_blockers": list(gate.blockers),
        "task_status": {item.task_id: item.status for item in state.tasks},
        "exceptions": [item.model_dump(mode="json") for item in state.exceptions],
        "fail_closed": list(state.human_review_items),
        "queue_owner": CTL_BOOKS_SLUG,
        "human_queue": False,
        "trace_path": state.trace_path,
        "createdAt": _now(),
    }
    write_json_atomic(path, payload)
    return path


def _next_ready(state: MonthEndState) -> str | None:
    refresh_readiness(state.tasks)
    queue = [
        item
        for item in ready_tasks(state.tasks)
        if item.task_id not in LOCK_TASKS
    ]
    if not queue:
        return None
    return queue[0].task_id


def run_close_host(
    period: str,
    *,
    scenario: str = "demo",
    live: bool = False,
    reset: bool = True,
    computer_root: Path | None = None,
    state_dir: Path | None = None,
) -> CloseHostRun:
    """Coordinate → one Profile Wake at a time → Handle ctl-books. Never lock."""
    assert_no_grant_union(COORDINATE_PROFILE)
    if mutating_ops(COORDINATE_PROFILE):
        raise CloseHostError("close/coordinate has mutating Catalog ops")
    if CREATE_ACCRUAL in PROFILE_OPS["prepaid"]:
        raise CloseHostError("close/prepaid cannot hold create_accrual")

    computer = Path(computer_root) if computer_root is not None else default_computer_root()
    if state_dir is not None:
        configure_paths(Path(state_dir))

    first = True
    seq = 1
    wake_paths: list[str] = []
    handle_paths: list[str] = []
    profiles_worn: list[str] = []
    state: MonthEndState | None = None
    ran_tasks: list[str] = []

    while True:
        if len(ran_tasks) > 20:
            raise CloseHostError("close host exceeded task budget; refusing to loop")
        if first:
            state = run_month_end(
                period,
                scenario=scenario,
                live=live,
                reset=reset,
                retry_failed=False,
                allow_close=False,
                only_tasks=[],
            )
            first = False
            refresh_readiness(state.tasks)
        assert state is not None
        coord_path = write_coordinate_wake(computer, period=period, seq=seq, state=state)
        wake_paths.append(str(coord_path))
        profiles_worn.append(COORDINATE_PROFILE)
        seq += 1
        task_id = _next_ready(state)
        if task_id is None:
            break
        if task_id in TREATMENT_TASKS:
            profile = TREATMENT_TASKS[task_id]
            wake_paths.append(
                str(
                    write_treatment_wake(
                        computer,
                        period=period,
                        seq=seq,
                        task_id=task_id,
                        profile=profile,
                    )
                )
            )
            profiles_worn.append(profile)
        elif task_id in PEER_TASKS:
            slug, profile = PEER_TASKS[task_id]
            handle_paths.append(
                str(
                    write_peer_handle(
                        computer,
                        period=period,
                        seq=seq,
                        task_id=task_id,
                        slug=slug,
                        profile=profile,
                    )
                )
            )
        seq += 1
        ran_tasks.append(task_id)
        state = run_month_end(
            period,
            scenario=scenario,
            live=live,
            reset=False,
            retry_failed=False,
            allow_close=False,
            only_tasks=[task_id],
        )

    assert state is not None
    gate = evaluate_close_gates(state)
    state.gate = gate
    pack_path = write_pack(computer, state, gate)
    # Write treatment Handles after the pack exists.
    for task_id, profile in TREATMENT_TASKS.items():
        by_id = {item.task_id: item for item in state.tasks}
        if task_id not in by_id or by_id[task_id].status == "NOT_STARTED":
            continue
        handle_paths.append(
            str(
                write_ctl_books_handle(
                    computer,
                    period=period,
                    profile=REVIEW_TREATMENT_PROFILE,
                    pack_path=pack_path,
                    kernel_status=by_id[task_id].status,
                    task_id=task_id,
                )
            )
        )
    lock_status = "READY_TO_CLOSE" if gate.passed else state.period.status
    handle_paths.append(
        str(
            write_ctl_books_handle(
                computer,
                period=period,
                profile=LOCK_PROFILE,
                pack_path=pack_path,
                kernel_status=lock_status,
                task_id="mark_closed",
            )
        )
    )
    handle_paths.append(
        str(
            write_pack_peer_handle(
                computer,
                period=period,
                slug=STORY_SLUG,
                bot_id=STORY_BOT_ID,
                profile="flux",
                pack_path=pack_path,
                lock_status=state.period.status,
            )
        )
    )
    handle_paths.append(
        str(
            write_pack_peer_handle(
                computer,
                period=period,
                slug=AUDIT_SLUG,
                bot_id=AUDIT_BOT_ID,
                profile="interpret",
                pack_path=pack_path,
                lock_status=state.period.status,
            )
        )
    )
    blocked = [item.detail for item in state.exceptions]
    blocked.extend(item.blocker_reason for item in unresolved_blockers(state.tasks) if item.blocker_reason)
    result = CloseHostRun(
        period=period,
        status=state.period.status,
        gate_passed=gate.passed,
        marked_closed=state.period.status == "CLOSED",
        pack_path=str(pack_path),
        wake_paths=wake_paths,
        handle_paths=sorted(set(handle_paths)),
        profiles_worn=profiles_worn,
        blocked_on=blocked,
        live_handles=False,
    )
    write_json_atomic(_work(computer, period) / "host-run.json", result.model_dump(mode="json"))
    return result
