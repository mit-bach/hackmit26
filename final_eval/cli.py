"""CLI for the final judge discrepancy benchmark."""

from __future__ import annotations

import argparse

from final_eval.runner import run_final_benchmark


def run_final_eval(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="final-eval")
    parser.add_argument("--live", action="store_true", help="Run the real agent subset when credentials exist")
    parser.add_argument("--skip-holdout-generate", action="store_true")
    args = parser.parse_args(argv)
    dest = run_final_benchmark(live=args.live, regenerate_holdout=not args.skip_holdout_generate)
    print((dest / "summary.md").read_text())
    print(f"\nWrote {dest}")
    return 0
