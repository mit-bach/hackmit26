"""CLI for the connected Office-of-the-CFO demo."""

from __future__ import annotations


def run_cfo_demo_cli(argv: list[str] | None = None) -> int:
    _ = argv
    from cfo.report import format_cfo_demo
    from cfo.scenario import run_cfo_scenario

    payload = run_cfo_scenario(persist=True)
    print(format_cfo_demo(payload))
    failed = [item for item in payload["checks"] if not item["passed"]]
    return 0 if not failed and payload["closed_close"].period.status == "CLOSED" else 1
