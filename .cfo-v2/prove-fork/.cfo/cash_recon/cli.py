"""CLI for monthly cash / bank reconciliation."""

from __future__ import annotations

import os


def _period(argv: list[str], default: str = "2026-09") -> str:
    if "--month" in argv:
        index = argv.index("--month")
        if index + 1 >= len(argv):
            raise ValueError("Usage: python main.py reconcile-cash --month 2026-09 --seed-demo")
        return argv[index + 1]
    rest = [item for item in argv if not item.startswith("--")]
    return rest[0] if rest else default


def run_reconcile_cash(argv: list[str]) -> int:
    try:
        period = _period(argv)
    except ValueError as exc:
        print(exc)
        return 1
    use_agent = "--llm" in argv
    if use_agent and not os.environ.get("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set.\n"
            "Copy .env.example to .env and add your key, or omit --llm for the deterministic engine."
        )
        return 1
    from cash_recon.report import format_cash_report
    from cash_recon.store import reset_cash_state
    from cash_recon.workflow import run_cash_reconciliation

    if "--reset" in argv:
        reset_cash_state()
    report = run_cash_reconciliation(period, seed_demo=True, use_agent=use_agent, reset="--reset" in argv)
    print(format_cash_report(report))
    return 0


def run_reconcile_trace(argv: list[str]) -> int:
    if not argv:
        print("Usage: python main.py reconcile-trace REC-001")
        return 1
    reconciliation_id = argv[0].strip().upper()
    from cash_recon.report import format_match_trace
    from cash_recon.store import find_trace
    from cash_recon.workflow import run_cash_reconciliation

    trace = find_trace(reconciliation_id)
    if trace is None:
        run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False)
        trace = find_trace(reconciliation_id)
    if trace is None:
        print(f"Unknown reconciliation ID: {reconciliation_id}")
        return 1
    print(format_match_trace(trace))
    return 0


def run_eval_cash(argv: list[str]) -> int:
    period = "2026-09"
    try:
        period = _period(argv, default="2026-09")
    except ValueError as exc:
        print(exc)
        return 1
    from cash_recon.eval import format_metrics
    from cash_recon.store import get_report
    from cash_recon.workflow import run_cash_reconciliation

    report = get_report(period) or run_cash_reconciliation(period, seed_demo=True, use_agent=False)
    if report.metrics is None:
        from cash_recon.eval import evaluate_report

        report.metrics = evaluate_report(report)
    print(format_metrics(report.metrics))
    return 0
