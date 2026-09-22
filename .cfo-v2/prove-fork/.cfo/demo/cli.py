"""CLI for demo inventory, validation, reset, export, and evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from demo.reset import DEFAULT_RUNTIME, reset_demo_runtime
from demo.validate import validate_demo_pack
from sample_data.paths import OFFICE_WORLD


def run_validate_demo(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate-demo")
    parser.add_argument("--data-root", default=str(OFFICE_WORLD))
    args = parser.parse_args(argv)
    errors = validate_demo_pack(args.data_root)
    if errors:
        print("Demo validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"Validated {args.data_root}")
    print("Demo export + cross-domain validation: PASS")
    return 0


def run_reset_demo(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reset-demo")
    parser.add_argument("--dest", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--source", default=str(OFFICE_WORLD))
    args = parser.parse_args(argv)
    dest = reset_demo_runtime(Path(args.dest), source=Path(args.source))
    print(f"Reset runtime workspace at {dest}")
    print("Canonical office world was not modified.")
    return 0


def run_demo_eval_cli(argv: list[str] | None = None) -> int:
    from evals.demo_company import main

    return main(argv)


def run_export_demo(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="export-demo")
    parser.add_argument("--output", default=str(OFFICE_WORLD))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    args = parser.parse_args(argv)
    from sample_data.orchestrator import generate_sample_data

    generate_sample_data(seed=args.seed, period=args.month, output=Path(args.output))
    print(f"Wrote demo pack to {args.output}")
    return 0
