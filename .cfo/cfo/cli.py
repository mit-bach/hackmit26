"""CLI for the connected Office-of-the-CFO demo."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _persist_packet(dest: Path, payload: dict, text: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "packet.md").write_text(text + "\n")
    summary = {
        "company": payload.get("company"),
        "period": payload.get("period"),
        "close_status": payload["closed_close"].period.status,
        "close_id": payload["closed_close"].close_id,
        "harbor_prior_decision": (payload.get("august_memory") or {}).get("harbor_memory_id"),
        "harbor_september_memory": getattr(payload.get("harbor_trace"), "written_memory_id", None),
        "checks_passed": sum(1 for item in payload["checks"] if item["passed"]),
        "checks_total": len(payload["checks"]),
        "metrics": payload.get("metrics"),
        "failed": [item["name"] for item in payload["checks"] if not item["passed"]],
    }
    (dest / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")


def run_cfo_demo_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the connected Maximor September CFO demo.")
    parser.add_argument("--output", default="", help="Directory for packet.md and summary.json")
    parser.add_argument(
        "--no-isolate",
        action="store_true",
        help="Write into the default run directories instead of an isolated demo workspace.",
    )
    args = parser.parse_args(argv)

    from cfo.report import format_cfo_demo
    from cfo.scenario import run_cfo_scenario

    dest = Path(args.output) if args.output else Path("runs") / "cfo_demo" / f"CFO-{_stamp()}"
    if args.no_isolate:
        payload = run_cfo_scenario(persist=True)
        text = format_cfo_demo(payload)
        _persist_packet(dest, payload, text)
    else:
        from cfo.workspace import isolated_cfo_workspace

        with isolated_cfo_workspace(dest / "workspace"):
            payload = run_cfo_scenario(persist=True)
            text = format_cfo_demo(payload)
            _persist_packet(dest, payload, text)

    print(text)
    print()
    print(f"Wrote {dest / 'packet.md'}")
    print(f"Wrote {dest / 'summary.json'}")
    failed = [item for item in payload["checks"] if not item["passed"]]
    return 0 if not failed and payload["closed_close"].period.status == "CLOSED" else 1
