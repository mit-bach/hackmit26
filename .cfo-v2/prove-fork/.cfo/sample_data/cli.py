"""CLI for generating, validating, and summarizing the shared demo dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from sample_data.orchestrator import generate_sample_data, validate_sample_data
from sample_data.paths import OFFICE_WORLD
from sample_data.report import format_summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="generate-sample-data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--output", default=str(OFFICE_WORLD))
    return parser


def run_generate(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    output = Path(args.output)
    ctx = generate_sample_data(seed=args.seed, period=args.month, output=output)
    print(format_summary(ctx, data_root=output))
    print(f"\nWrote {output / 'manifest.json'}")
    return 0


def run_validate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate-sample-data")
    parser.add_argument("--data-root", default=str(OFFICE_WORLD))
    args = parser.parse_args(argv)
    manifest = validate_sample_data(args.data_root)
    print(f"Validated {args.data_root}")
    print(f"Seed: {manifest.seed}")
    print(f"Period: {manifest.period}")
    print(f"Scenarios: {len(manifest.scenario_ids)}")
    print("Cross-domain validation: PASS")
    return 0


def run_summary(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sample-data-summary")
    parser.add_argument("--data-root", default=str(OFFICE_WORLD))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    args = parser.parse_args(argv)
    ctx = generate_sample_data(seed=args.seed, period=args.month, output=None)
    print(format_summary(ctx, data_root=Path(args.data_root)))
    return 0
