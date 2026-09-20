"""Office close host. Sequences grain Profiles. Does not lock the period.

Kernel module named by office/bots/close/HOST.md. This is not a sixteenth Bot
and not Runner.run_sync. Verifier Handles go to ctl-books with one Profile
per treatment so Grants are never unioned.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from close.gating import evaluate_close_gates
from close.month_end import configure_paths, run_month_end

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


def default_computer_root() -> Path:
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / ".cfo-v2" / "office" / "computer"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def _handle_payload(to_slug: str, profile: str, paths: list[str], prompt: str) -> dict:
    return {
        "toSlug": to_slug,
        "to": f"bot_{to_slug.replace('-', '_')}",
        "from": "bot_close",
        "profile": profile,
        "kind": "a2a_handoff",
        "paths": paths,
        "prompt": prompt,
    }


def run_close_host(
    computer: Path | None = None,
    period: str = "2026-09",
    *,
    scenario: str = "demo",
    live: bool = False,
    reset: bool = True,
) -> dict:
    """Run month-end completeness and write Handle payloads. Never mark CLOSED."""
    computer = Path(computer) if computer is not None else default_computer_root()
    configure_paths(computer / "runs" / "month_end")
    state = run_month_end(
        period,
        scenario=scenario,
        live=live,
        reset=reset,
        allow_close=False,
    )
    prefix = f"workspace/close/{period}"
    pack_rel = f"{prefix}/pack.json"
    pack = {
        "period": period,
        "status": state.period.status,
        "close_id": state.close_id,
        "tasks": [item.model_dump(mode="json") for item in state.tasks],
        "exceptions": [item.model_dump(mode="json") for item in state.exceptions],
        "lock_door": "close.month_end",
        "marked_closed": False,
    }
    _write_json(computer / pack_rel, pack)
    gates = evaluate_close_gates(state)
    _write_json(
        computer / f"{prefix}/gates.json",
        gates.model_dump(mode="json") if hasattr(gates, "model_dump") else {"result": str(gates)},
    )

    wakes: list[dict] = []
    handles: list[dict] = []
    wakes.append(
        {
            "profile": "coordinate",
            "slug": "close",
            "period": period,
            "path": f"{prefix}/wakes/000-coordinate.json",
        }
    )
    _write_json(computer / f"{prefix}/wakes/000-coordinate.json", wakes[-1])

    for index, task in enumerate(state.tasks, start=1):
        profile = TASK_PROFILE.get(task.task_id)
        if profile:
            wake = {
                "profile": profile,
                "slug": "close",
                "period": period,
                "task_id": task.task_id,
                "status": task.status,
            }
            wake_rel = f"{prefix}/wakes/{index:03d}-close-{profile}.json"
            _write_json(computer / wake_rel, wake)
            wakes.append(wake)
        dest = TASK_HANDLE.get(task.task_id)
        if dest:
            to_slug, handle_profile = dest
            handle = _handle_payload(
                to_slug,
                handle_profile,
                [pack_rel],
                f"profile: {handle_profile}\nReview {task.task_id} for {period} at {pack_rel}. Never ask a human.",
            )
            handle_rel = f"{prefix}/handles/{to_slug}-{task.task_id}.json"
            _write_json(computer / handle_rel, handle)
            handles.append(handle)

    lock = _handle_payload(
        "ctl-books",
        "lock",
        [pack_rel],
        f"profile: lock\nEvaluate close gates for {period} at {pack_rel}. Do not mark CLOSED. Never ask a human.",
    )
    _write_json(computer / f"{prefix}/handles/ctl-books-lock.json", lock)
    handles.append(lock)
    story = _handle_payload(
        "story",
        "flux",
        [pack_rel],
        f"profile: flux\nNarrate Kernel facts from {pack_rel}. Never ask a human.",
    )
    _write_json(computer / f"{prefix}/handles/story-pack.json", story)
    handles.append(story)
    audit = _handle_payload(
        "audit",
        "interpret",
        [pack_rel],
        f"profile: interpret\nSample the close pack at {pack_rel}. Never ask a human.",
    )
    _write_json(computer / f"{prefix}/handles/audit-pack.json", audit)
    handles.append(audit)

    host_run = {
        "period": period,
        "status": state.period.status,
        "marked_closed": False,
        "lock_door": "close.month_end",
        "wakes": wakes,
        "handles": handles,
        "pack_path": pack_rel,
    }
    _write_json(computer / f"{prefix}/host-run.json", host_run)
    return host_run
