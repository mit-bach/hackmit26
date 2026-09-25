"""Office close host. Sequences grain Profiles. Does not lock the period.

Kernel module named by office/bots/close/HOST.md. This is not a sixteenth Bot
and not Runner.run_sync. Verifier Handles go to ctl-books with one Profile
per treatment so Grants are never unioned.

When HARNESS_COMPUTER is set, Kernel state lands under Computer runs/month_end
and the period pack under workspace/close/packets/<period>.json. That is the office path.
.close/runs is not the office demo destination.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from close.gating import evaluate_close_gates
from close.month_end import configure_paths, run_month_end
from close.profile_grants import (
    CREATE_ACCRUAL,
    LOCK_DOOR,
    TEST_PACKET,
    mutating_ops,
    PROFILE_OPS,
)
from harness_handles import default_computer_root, write_peer_handle

TASK_PROFILE = {
    "accruals": "accrue",
    "prepaid": "prepaid",
    "depreciation": "assets",
    "bs_recon": "bs",
}

TASK_HANDLE = {
    "prepaid": ("ctl-books", "review-treatment"),
    "depreciation": ("ctl-books", "review-assets"),
    "bs_recon": ("ctl-books", "review-bs"),
    "cash": ("ctl-cash", "review-rec"),
    "ap": ("ctl-pay", "review-match"),
    "ar": ("collect", "chase"),
    "ingest": ("email", "invoice"),
}


class CloseHostResult(dict):
    """Dict that also exposes attributes so Kernel tests can use either style."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def _looks_like_period(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.split("-")
    return len(parts) == 2 and len(parts[0]) == 4 and parts[0].isdigit() and parts[1].isdigit()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def _handle_payload(to_slug: str, profile: str, paths: list[str], prompt: str, extra: dict | None = None) -> dict:
    payload = {
        "toSlug": to_slug,
        "to": f"bot_{to_slug.replace('-', '_')}",
        "from": "bot_close",
        "fromSlug": "close",
        "profile": profile,
        "kind": "a2a_handoff",
        "paths": paths,
        "prompt": prompt,
        "status": "accepted",
        "done": False,
        "bus": "harness",
        "humanQueue": False,
        "queue_owner": to_slug,
        "live_sent": False,
    }
    if extra:
        payload.update(extra)
    return payload


def _blocked_on(state, gates) -> list[str]:
    rows: list[str] = []
    rows.extend(list(gates.blockers or []))
    for item in state.exceptions:
        detail = getattr(item, "detail", "") or ""
        if detail and detail not in rows:
            rows.append(detail)
    for item in state.human_review_items:
        if item and item not in rows:
            rows.append(item)
    return rows


def run_close_host(
    computer: Path | str | None = None,
    period: str = "2026-09",
    *,
    scenario: str = "demo",
    live: bool = False,
    reset: bool = True,
    computer_root: Path | str | None = None,
    state_dir: Path | str | None = None,
) -> CloseHostResult:
    """Run month-end completeness and write Handle payloads. Never mark CLOSED."""
    if _looks_like_period(computer):
        period = str(computer)
        computer = None
    root = Path(computer_root or computer or default_computer_root())
    root.mkdir(parents=True, exist_ok=True)
    runs_dir = Path(state_dir) if state_dir is not None else (root / "runs" / "month_end")
    configure_paths(runs_dir)
    state = run_month_end(
        period,
        scenario=scenario,
        live=live,
        reset=reset,
        allow_close=False,
    )
    desk = "workspace/close"
    pack_rel = f"{desk}/packets/{period}.json"
    html_rel = f"{desk}/packets/{period}.html"
    gates_rel = f"runs/month_end/{period}-gates.json"
    gates = evaluate_close_gates(state)
    blocked = _blocked_on(state, gates)
    pack = {
        "period": period,
        "status": state.period.status,
        "close_id": state.close_id,
        "tasks": [item.model_dump(mode="json") for item in state.tasks],
        "exceptions": [item.model_dump(mode="json") for item in state.exceptions],
        "lock_door": LOCK_DOOR,
        "test_packet": TEST_PACKET,
        "marked_closed": False,
        "gate_passed": gates.passed,
        "queue_owner": "ctl-books",
        "human_queue": False,
        "blocked_on": blocked,
        "runs_dir": str(runs_dir),
    }
    _write_json(root / pack_rel, pack)
    html_path = root / html_rel
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"<title>{period} close</title></head><body>"
        f"<h1>{period}</h1>"
        f"<p>Status {state.period.status}. Gate passed: {gates.passed}.</p>"
        f"<p>Blocked on: {blocked}. The month stays open while an unexplained difference remains.</p>"
        "</body></html>\n"
    )
    _write_json(root / gates_rel, gates.model_dump(mode="json"))

    wakes: list[dict] = []
    handles: list[dict] = []
    coordinate_wake = {
        "profile": "coordinate",
        "slug": "close",
        "period": period,
        "path": f"{desk}/handles/{period}-coordinate.json",
        "ops": list(PROFILE_OPS["coordinate"]),
        "mutatingOps": list(mutating_ops("coordinate")),
        "mark_closed": False,
        "office_live_catalog_caller": False,
    }
    _write_json(root / f"{desk}/handles/{period}-coordinate.json", coordinate_wake)
    wakes.append(coordinate_wake)

    for index, task in enumerate(state.tasks, start=1):
        profile = TASK_PROFILE.get(task.task_id)
        if profile:
            ops = list(PROFILE_OPS.get(profile, ()))
            wake = {
                "profile": profile,
                "slug": "close",
                "period": period,
                "task_id": task.task_id,
                "status": task.status,
                "ops": ops,
                "mutatingOps": list(mutating_ops(profile)),
                "mark_closed": False,
            }
            if profile != "accrue":
                assert CREATE_ACCRUAL not in ops
            wake_rel = f"{desk}/handles/{period}-{index:03d}-{profile}.json"
            _write_json(root / wake_rel, wake)
            wakes.append(wake)
        dest = TASK_HANDLE.get(task.task_id)
        if dest:
            to_slug, handle_profile = dest
            prompt = (
                f"profile: {handle_profile}\n"
                f"Review {task.task_id} for {period} at {pack_rel}. "
                "Never ask a human. Peer Handle is not approval."
            )
            handle = _handle_payload(to_slug, handle_profile, [pack_rel], prompt)
            handle_rel = f"{desk}/handles/{period}-{to_slug}-{task.task_id}.json"
            _write_json(root / handle_rel, handle)
            write_peer_handle(
                root,
                from_slug="close",
                to_slug=to_slug,
                profile=handle_profile,
                paths=[pack_rel],
                prompt=prompt,
                extra={"humanQueue": False, "live_sent": False, "task_id": task.task_id},
            )
            handles.append(handle)

    lock_prompt = (
        f"profile: lock\n"
        f"Read the finance gate for {period} at {gates_rel}. "
        f"Pack is {pack_rel}. gate_passed={gates.passed}. "
        "Do not mark CLOSED. Kernel close.month_end is the only lock door. "
        "Never ask a human."
    )
    lock = _handle_payload(
        "ctl-books",
        "lock",
        [pack_rel, gates_rel],
        lock_prompt,
        extra={
            "gate_passed": gates.passed,
            "lock_door": LOCK_DOOR,
            "can_mark_closed": False,
        },
    )
    _write_json(root / f"{desk}/handles/{period}-ctl-books-lock.json", lock)
    write_peer_handle(
        root,
        from_slug="close",
        to_slug="ctl-books",
        profile="lock",
        paths=[pack_rel, gates_rel],
        prompt=lock_prompt,
        extra={
            "humanQueue": False,
            "gate_passed": gates.passed,
            "lock_door": LOCK_DOOR,
            "can_mark_closed": False,
            "live_sent": False,
        },
    )
    handles.append(lock)

    lock_status = state.period.status
    story_prompt = (
        f"profile: flux\n"
        f"Narrate Kernel facts from {pack_rel}. lock_status={lock_status}. "
        "If lock_status is not CLOSED, label every number UNLOCKED. "
        "Do not start a forecast from unreconciled GL cash. Never ask a human."
    )
    story = _handle_payload("story", "flux", [pack_rel], story_prompt, extra={"lock_status": lock_status})
    _write_json(root / f"{desk}/handles/{period}-story-pack.json", story)
    write_peer_handle(
        root,
        from_slug="close",
        to_slug="story",
        profile="flux",
        paths=[pack_rel],
        prompt=story_prompt,
        extra={"lock_status": lock_status, "humanQueue": False, "live_sent": False},
    )
    handles.append(story)

    audit_prompt = (
        f"profile: interpret\n"
        f"Sample the close pack at {pack_rel}. Cite Kernel finding IDs only. "
        "Do not load get_audit_ground_truth. Do not fix the books. Never ask a human."
    )
    audit = _handle_payload("audit", "interpret", [pack_rel], audit_prompt)
    _write_json(root / f"{desk}/handles/{period}-audit-pack.json", audit)
    write_peer_handle(
        root,
        from_slug="close",
        to_slug="audit",
        profile="interpret",
        paths=[pack_rel],
        prompt=audit_prompt,
        extra={"humanQueue": False, "live_sent": False},
    )
    handles.append(audit)

    profiles_worn = list(dict.fromkeys(item["profile"] for item in wakes))
    host_run = {
        "period": period,
        "status": state.period.status,
        "marked_closed": False,
        "lock_door": LOCK_DOOR,
        "test_packet": TEST_PACKET,
        "gate_passed": gates.passed,
        "blocked_on": blocked,
        "wakes": wakes,
        "handles": handles,
        "pack_path": pack_rel,
        "profiles_worn": profiles_worn,
        "live_handles": False,
        "runs_dir": str(runs_dir),
        "computer_root": str(root),
        "harness_computer": os.environ.get("HARNESS_COMPUTER") or "",
    }
    _write_json(root / f"runs/month_end/{period}-host-run.json", host_run)
    return CloseHostResult(host_run)
