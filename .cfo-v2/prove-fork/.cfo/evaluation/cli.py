"""CLI for the CFO evaluation harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.report import format_summary
from evaluation.runner import ALL_ORDER, run_benchmark


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evaluate-cfo")
    parser.add_argument("--data-root", default="data/demo")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--output", default="")
    parser.add_argument("--compare-to", default="")
    parser.add_argument("--domain", action="append", dest="domains")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--live", action="store_true")
    return parser


def run_evaluate(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    domains = None
    if args.domains and not args.all:
        aliases = {
            "ap_ar": ["ap", "ar"],
            "reporting_forecasting": ["reporting", "forecasting"],
            "forecast": ["forecasting"],
        }
        selected = []
        for item in args.domains:
            selected.extend(aliases.get(item, [item]))
        domains = [item for item in selected if item in ALL_ORDER]
    result = run_benchmark(
        data_root=Path(args.data_root),
        seed=args.seed,
        period=args.month,
        domains=domains,
        output=Path(args.output) if args.output else None,
        compare_to=Path(args.compare_to) if args.compare_to else None,
        live=args.live,
    )
    print(format_summary(result))
    dest = Path(result.output_dir) if result.output_dir else Path("runs") / "evaluation" / result.run_id
    print(f"\nWrote {dest / 'benchmark.json'}")
    return 0 if result.overall_metrics.cases_error == 0 else 1
