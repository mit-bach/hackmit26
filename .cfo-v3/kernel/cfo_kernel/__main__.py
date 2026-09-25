"""python -m cfo_kernel --computer <dir>"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from cfo_kernel.paths import DEFAULT_COMPUTER, attach_computer
from cfo_kernel.server import run_http, run_stdio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CFO Kernel sidecar. Serves Catalog ops over loopback HTTP JSON. "
            "Not a Bot. Does not bind HARNESS_BOT. Does not drain inboxes."
        )
    )
    parser.add_argument(
        "--computer",
        default=os.environ.get("HARNESS_COMPUTER") or str(DEFAULT_COMPUTER),
        help="Computer root (HARNESS_COMPUTER). Contains cfo/, data/, runs/.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Loopback port. 0 = ephemeral, written to cfo/kernel.port",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Newline JSON on stdin/stdout instead of HTTP",
    )
    args = parser.parse_args(argv)
    if os.environ.get("HARNESS_BOT"):
        print(
            "cfo_kernel: sidecar is not a Bot; ignoring HARNESS_BOT",
            file=sys.stderr,
        )
    os.environ.setdefault("CFO_EVAL_PHASE", "operational")
    computer = attach_computer(Path(args.computer))
    if args.stdio:
        run_stdio(computer)
        return 0
    run_http(args.host, args.port, computer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
