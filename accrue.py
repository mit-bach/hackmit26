#!/usr/bin/env python3
"""Run discovery, the Accrual Agent, reconciliation, or a historical backtest.

Usage:
    python accrue.py discover 2026-09
    python accrue.py 2026-09
    python accrue.py reconcile 2026-09
    python accrue.py backtest
    python accrue.py demo
    python accrue.py open 2026-09
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from accrual.report import (
    format_backtest,
    format_close_summary,
    format_discovery,
    format_period_report,
    format_reconciliation,
    format_vendor_trace,
)

load_dotenv(Path(__file__).resolve().parent / ".env")

PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def _period_or_default(raw: str | None) -> str:
    period = (raw or "2026-09").strip()
    if not PERIOD_RE.match(period):
        raise ValueError(f"Period must look like YYYY-MM, got {period!r}")
    return period


def _require_api_key() -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return None
    return (
        "OPENAI_API_KEY is not set.\n"
        "Copy .env.example to .env and add your key, then rerun:\n"
        "  python accrue.py 2026-09"
    )


def _print_reconcile(results) -> None:
    if not results:
        print("No open accruals could be matched to a later invoice.")
        return
    print("\n\n".join(format_reconciliation(item) for item in results))


def _featured(report, vendor: str):
    return next((item for item in report.traces if item.vendor == vendor), None)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.strip())
        return 0

    command = argv[0].strip().lower()
    try:
        if command == "discover":
            period = _period_or_default(argv[1] if len(argv) > 1 else None)
            from accrual.discovery import discover_period

            print(format_discovery(discover_period(period)))
            return 0

        if command == "backtest":
            from accrual.backtest import run_backtest

            report = run_backtest()
            print(format_backtest(report))
            return 0

        if command == "reconcile":
            period = _period_or_default(argv[1] if len(argv) > 1 else None)
            from accrual.workflow import run_reconcile_workflow

            print(f"Reconciling open accruals for {period}\n", flush=True)
            _print_reconcile(run_reconcile_workflow(period))
            return 0

        if command == "open":
            period = _period_or_default(argv[1] if len(argv) > 1 else None)
            from accrual.ledger import get_open_accruals
            import json

            rows = get_open_accruals(period=period)
            print(json.dumps([item.model_dump(mode="json") for item in rows], indent=2))
            return 0

        if command == "demo":
            missing = _require_api_key()
            if missing:
                print(missing)
                return 1
            from accrual.workflow import run_demo

            print("DISCOVER → ESTIMATE → BOOK → MEASURE → RECONCILE\n", flush=True)
            print("STEP 1  Scan the September close.", flush=True)
            print("STEP 2  Infer which expenses should exist.", flush=True)
            print("STEP 3  Compare those expectations against invoices received.", flush=True)
            print("STEP 4  Identify missing bills.\n", flush=True)
            report, results, discovery, backtest = run_demo()
            print(format_discovery(discovery))
            print()
            print("STEP 5  Aether: competing estimates, usage-based choice.")
            card = _featured(report, "Aether Compute")
            if card:
                print(format_vendor_trace(card))
                print()
            print("STEP 6  Harbor: recent average vs seasonal evidence.")
            card = _featured(report, "Harbor Electric")
            if card:
                print(format_vendor_trace(card))
                print()
            print("STEP 7  Helios: goods received but invoice missing.")
            card = _featured(report, "Helios Hardware")
            if card:
                print(format_vendor_trace(card))
                print()
            print("STEP 8  Book supported accruals.\n")
            print(format_close_summary(report))
            print()
            print("STEP 9  Historical backtest metrics.\n")
            print(format_backtest(backtest))
            print()
            print("STEP 10  Reveal the later Aether invoice and reconcile.\n")
            _print_reconcile(results)
            return 0

        period = _period_or_default(
            argv[0] if command not in {"accrue", "accrual"} else (argv[1] if len(argv) > 1 else None)
        )
        missing = _require_api_key()
        if missing:
            print(missing)
            return 1

        from accrual.workflow import run_accrual_workflow

        report = run_accrual_workflow(period)
        print()
        if report.discovery:
            print(format_discovery(report.discovery))
            print()
        print(format_period_report(report))
        return 0
    except ValueError as exc:
        print(exc)
        return 1
    except Exception as exc:
        print(f"The Accrual Agent failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
