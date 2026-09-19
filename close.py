#!/usr/bin/env python3
"""Month-end close checklist.

Usage:
    python close.py run --period 2026-09
    python close.py status --period 2026-09
    python close.py reviews --period 2026-09
    python close.py review --period 2026-09 --review-id <id>
    python close.py resolve --period 2026-09 --review-id <id>
    python close.py rerun --period 2026-09
    python close.py finalize --period 2026-09
    python close.py prepaid --period 2026-09
    python close.py depreciate --period 2026-09
    python close.py eval-live --deterministic
    python close.py eval-live --live --repeat 2
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from close.cli import run_month_end_cli

load_dotenv(Path(__file__).resolve().parent / ".env")


def main(argv: list[str] | None = None) -> int:
    return run_month_end_cli(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
