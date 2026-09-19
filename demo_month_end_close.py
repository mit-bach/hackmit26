#!/usr/bin/env python3
"""Judge-friendly September 2026 month-end close demo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _initial():
    from close.month_end import run_month_end
    from close.report import format_month_end_demo

    print("PHASE 1 — INITIAL CLOSE", flush=True)
    state = run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    print(format_month_end_demo(state))
    return state


def _resolve_all(period: str):
    from close.actions import resolve_review_item
    from close.report import format_resolution
    from close.reviews import load_reviews

    rows = {item.source_workflow: item for item in load_reviews(period)}
    resolved = []
    cash = resolve_review_item(
        rows["cash"].review_id,
        action="post_correcting_entry",
        reason="Classify the $12.40 Northstar wire difference and post the approved correcting receipt.",
        reviewer="cash-reviewer",
    )
    ar = resolve_review_item(
        rows["ar"].review_id,
        action="apply_payment",
        invoice_id="INV-AR-050",
        reason="Associate PAY-CLOSE-4500 with INV-AR-050 and apply cash.",
        reviewer="ar-reviewer",
    )
    prepaid = resolve_review_item(
        rows["prepaid"].review_id,
        action="attach_evidence",
        document_id="DOC-NS-FLOOD-2026",
        reason="Attach the Northshore flood policy packet.",
        reviewer="prepaid-reviewer",
    )
    for item in (cash, ar, prepaid):
        resolved.append(item)
        print(format_resolution(item))
        print()
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="September month-end close demo")
    parser.add_argument("--resolve", action="store_true", help="Resolve planted blockers and close the period")
    args = parser.parse_args(argv)

    from close.month_end import finalize_close, rerun_affected
    from close.report import format_finalize, format_month_end_demo, format_rerun

    live = bool(os.environ.get("OPENAI_API_KEY"))
    print("Running September 2026 month-end close...", flush=True)
    print("OFFICE OF THE CFO — MONTH-END CLOSE")
    print()
    phase1 = _initial()
    if not args.resolve:
        if live:
            print("\n(Live API key detected; demo stayed deterministic so judges see a stable checklist.)")
        return 0

    print()
    print("PHASE 2 — REVIEW")
    print()
    _resolve_all(phase1.period.period)
    print("PHASE 3 — TARGETED RERUN")
    print()
    phase3 = rerun_affected(phase1.period.period, live=False)
    print(format_rerun(phase3))
    print()
    print("PHASE 4 — FINAL REVIEW")
    print()
    phase4 = finalize_close(phase1.period.period, live=False)
    print(format_finalize(phase4))
    return 0 if phase4.period.status == "CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
