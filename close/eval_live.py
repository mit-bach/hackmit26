"""Judgment cases for month-end close. Deterministic ground truth; live agents optional."""

from __future__ import annotations

from close.eval_cases import CANONICAL_CASES as CASES
from close.eval_harness import format_eval_report, run_isolated_eval_repeats


def run_close_eval(*, use_agent: bool = False, live: bool = False, repeat: int = 1) -> str:
    reports = run_isolated_eval_repeats(live=bool(live or use_agent), repeat=repeat)
    return format_eval_report(reports)
