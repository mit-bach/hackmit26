"""CLI for the finance inbox demo."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from inbox.demo import format_demo, run_demo_inbox
from inbox.store import configure_runs_dir

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def run_demo_inbox_cli(argv: list[str]) -> int:
    full = "--full" in argv
    reset = "--reset" in argv
    live = "--llm" in argv
    unknown = [item for item in argv if item not in {"--full", "--reset", "--llm"}]
    if unknown:
        print(f"Unknown demo-inbox option: {unknown[0]}")
        print("Usage: python main.py demo-inbox [--full] [--reset] [--llm]")
        return 1
    if live and not os.environ.get("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set.\n"
            "The required inbox demo is deterministic. Rerun without --llm:\n"
            "  python main.py demo-inbox"
        )
        return 1
    configure_runs_dir()
    results = run_demo_inbox(full=full, reset=reset, persist=True)
    print(format_demo(results), end="")
    return 0
