from __future__ import annotations

from reporting.demo import main as run_demo_main
from reporting.forecast import HORIZON_WEEKS, build_forecast, persist_forecast_export
from reporting.report import format_cash_forecast, format_reporting_run
from reporting.store import next_version
from reporting.workflow import DEFAULT_AS_OF, DEFAULT_PERIOD, run_reporting_workflow


def run_demo_reporting(argv: list[str]) -> int:
    return run_demo_main(argv)


def run_reporting(argv: list[str]) -> int:
    live = "--llm" in argv
    argv = [item for item in argv if item != "--llm"]
    period = argv[0] if argv else DEFAULT_PERIOD
    as_of = argv[1] if len(argv) > 1 else DEFAULT_AS_OF
    run = run_reporting_workflow(period, as_of=as_of, live=live, seed=True, persist=True)
    print(format_reporting_run(run))
    return 0


def _parse_forecast_args(argv: list[str]) -> tuple[str, int, list[str]]:
    as_of = "2026-09-30"
    weeks = HORIZON_WEEKS
    rest: list[str] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--as-of":
            as_of = argv[index + 1]
            index += 2
            continue
        if option == "--weeks":
            weeks = int(argv[index + 1])
            index += 2
            continue
        rest.append(option)
        index += 1
    return as_of, weeks, rest


def run_cash_forecast_cli(argv: list[str]) -> int:
    try:
        as_of, weeks, rest = _parse_forecast_args(argv)
    except (IndexError, ValueError):
        print("Usage: python main.py cash-forecast [--as-of 2026-09-30] [--weeks 13]")
        return 1
    if rest:
        print(f"Unknown cash-forecast option: {rest[0]}")
        return 1
    snapshot = build_forecast(as_of, weeks=weeks, version=next_version(as_of))
    export = persist_forecast_export(snapshot)
    snapshot = snapshot.model_copy(update={"trace_id": str(export / "trace.json")})
    print(format_cash_forecast(snapshot))
    print(f"\nForecast saved to {export}")
    return 0
