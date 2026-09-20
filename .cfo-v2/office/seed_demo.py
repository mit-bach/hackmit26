"""Seed demo inbox, Stripe pack, and pay pool onto the CFO V2 Computer.

Run from the git repo root:

    HARNESS_COMPUTER=.cfo-v2/office/computer PYTHONPATH=.cfo \\
      .cfo/.venv/bin/python .cfo-v2/office/seed_demo.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KERNEL = REPO / ".cfo"
OFFICE = REPO / ".cfo-v2" / "office"
COMPUTER = Path(os.environ.get("HARNESS_COMPUTER") or OFFICE / "computer")

if str(KERNEL) not in sys.path:
    sys.path.insert(0, str(KERNEL))


def main() -> int:
    os.environ["HARNESS_COMPUTER"] = str(COMPUTER)
    os.environ.setdefault("CFO_EVAL_PHASE", "operational")
    from cfo_kernel.paths import attach_computer
    from inbox.demo import format_demo, run_demo_inbox
    from scheduling.pool import seed_demo_pool
    from simulations.stripe.persist import persist_pack

    bound = attach_computer(COMPUTER)
    pack_dir = persist_pack(bound.data / "simulations" / "stripe")
    inbox = run_demo_inbox(full=False, reset=True, persist=True)
    pool = seed_demo_pool()
    summary = {
        "computer": str(bound.root),
        "data": str(bound.data),
        "runs": str(bound.runs),
        "stripe_pack": str(pack_dir),
        "inbox_handoffs": len(inbox),
        "pay_pool": pool,
        "talking_points": [
            "Open Email. Set Transcript detail to Full. Ask it to call list_email_candidates for 2026-09.",
            "Open AP. Ask it to load invoice ING-001 with tools.get_invoice (demo-inbox already landed it).",
            "Inspector → Pi events / Pi RPC shows the live Harness stream, not a mascot-only status.",
            "There is no live mailbox. demo-inbox wrote traces under computer/runs/inbox.",
            "Stripe objects live under computer/data/simulations/stripe (office world pack).",
        ],
    }
    dest = OFFICE / "DEMO-WALKTHROUGH.md"
    dest.write_text(_markdown(summary, inbox, format_demo), encoding="utf-8")
    (bound.runs / "demo-seed.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {dest}")
    return 0


def _markdown(summary: dict, inbox: list, format_demo) -> str:
    body = format_demo(inbox)
    points = "\n".join(f"- {item}" for item in summary["talking_points"])
    pool = ", ".join(summary["pay_pool"]) or "(none — pool uses policy-eligible invoices)"
    return (
        "# Office demo walkthrough\n\n"
        "Seeded without live email. Kernel traces and the Stripe pack are on this Computer.\n\n"
        f"- Computer: `{summary['computer']}`\n"
        f"- Inbox handoffs: {summary['inbox_handoffs']}\n"
        f"- Pay pool: {pool}\n"
        f"- Stripe pack: `{summary['stripe_pack']}`\n\n"
        "## What to show\n\n"
        f"{points}\n\n"
        "## Inbox seed\n\n"
        "```\n"
        f"{body.strip()}\n"
        "```\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
