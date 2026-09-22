"""Deterministic reporting demo. No API key required."""

from __future__ import annotations

from reporting.report import format_reporting_run
from reporting.workflow import DEFAULT_AS_OF, DEFAULT_PERIOD, run_reporting_workflow


def run_demo(period: str = DEFAULT_PERIOD, as_of: str = DEFAULT_AS_OF, *, live: bool = False) -> str:
    run = run_reporting_workflow(period, as_of=as_of, live=live, seed=True, persist=True)
    return format_reporting_run(run)


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    live = "--llm" in args
    args = [item for item in args if item != "--llm"]
    period = args[0] if args else DEFAULT_PERIOD
    as_of = args[1] if len(args) > 1 else DEFAULT_AS_OF
    print(run_demo(period, as_of, live=live))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
