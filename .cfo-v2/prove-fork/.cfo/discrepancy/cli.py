"""CLI for discrepancy data generation and evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from discrepancy.evaluate import run_discrepancy_benchmark
from discrepancy.fixes import all_fixes
from discrepancy.generate import generate_discrepancy_data, generate_holdout_data
from discrepancy.report import format_discrepancy_report


def run_generate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate-discrepancy-data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--output", default="data/discrepancy_demo")
    args = parser.parse_args(argv)
    dest = generate_discrepancy_data(seed=args.seed, period=args.month, output=args.output)
    print(f"Wrote discrepancy dataset to {dest}")
    print(f"Contracts: {dest / 'evaluation' / 'discrepancy_contracts.json'}")
    return 0


def run_generate_holdout(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate-holdout-data")
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--output", default="data/discrepancy_holdout")
    args = parser.parse_args(argv)
    dest = generate_holdout_data(seed=args.seed, period=args.month, output=args.output)
    print(f"Wrote held-out discrepancy dataset to {dest}")
    print(f"Contracts: {dest / 'evaluation' / 'holdout_contracts.json'}")
    return 0


def _persist(dest: Path, result, name: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / name).write_text(result.model_dump_json(indent=2) + "\n")
    failures = [item.model_dump(mode="json") for fn in result.function_results for item in fn.cases if not item.passed]
    prefix = "initial" if "initial" in name else "final"
    (dest / f"{prefix}_failures.json").write_text(json.dumps(failures, indent=2) + "\n")


def run_evaluate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluate-discrepancies")
    parser.add_argument("--data-root", default="data/discrepancy_demo")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--output", default="")
    parser.add_argument("--phase", default="final")
    args = parser.parse_args(argv)
    result = run_discrepancy_benchmark(
        data_root=Path(args.data_root),
        seed=args.seed,
        period=args.month,
        output=Path(args.output) if args.output else None,
        phase=args.phase,
    )
    dest = Path(result.output_dir)
    _persist(dest, result, "final_results.json" if args.phase == "final" else "initial_results.json")
    initial = None
    initial_path = Path("runs/discrepancy_eval/INITIAL-2026-09-42/initial_results.json")
    if args.phase == "final" and initial_path.exists():
        from discrepancy.models import DiscrepancyBenchmark

        initial = DiscrepancyBenchmark.model_validate_json(initial_path.read_text())
        (dest / "initial_results.json").write_text(initial_path.read_text())
        fail_src = initial_path.parent / "initial_failures.json"
        if fail_src.exists():
            (dest / "initial_failures.json").write_text(fail_src.read_text())
    fixes = all_fixes() if args.phase == "final" else []
    if fixes:
        (dest / "fixes.json").write_text(
            __import__("json").dumps([item.model_dump(mode="json") for item in fixes], indent=2) + "\n"
        )
        (dest / "regression_tests.json").write_text(
            __import__("json").dumps([item.regression_test for item in fixes], indent=2) + "\n"
        )
    report = format_discrepancy_report(result, initial=initial, fixes=fixes or None)
    (dest / "summary.md").write_text(report + "\n")
    print(report)
    print(f"\nWrote {dest}")
    return 0 if result.failed == 0 else 1
