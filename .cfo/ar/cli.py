from __future__ import annotations

import os

from ar.report import (
    format_aging,
    format_cash_apply,
    format_collections,
    format_demo,
    format_forecast_demo,
    format_review_item,
    format_review_list,
    format_review_resolution,
)
from ar.review import approve_review, correct_review, parse_apply_spec, reject_review
from ar.store import get_review, open_reviews, reset_state
from ar.workflow import (
    DEFAULT_AS_OF,
    run_aging,
    run_ar_demo,
    run_ar_forecast_demo,
    run_cash_apply,
    run_collections,
)


def _as_of(argv: list[str], default: str = DEFAULT_AS_OF) -> tuple[str, list[str]]:
    as_of = default
    rest: list[str] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--as-of":
            if index + 1 >= len(argv):
                raise ValueError("Usage: --as-of YYYY-MM-DD")
            as_of = argv[index + 1]
            index += 2
            continue
        rest.append(option)
        index += 1
    return as_of, rest


def _live_flag(argv: list[str]) -> tuple[bool, list[str]]:
    live = "--llm" in argv
    return live, [item for item in argv if item != "--llm"]


def _require_key() -> int | None:
    if os.environ.get("OPENAI_API_KEY"):
        return None
    print(
        "OPENAI_API_KEY is not set.\n"
        "Copy .env.example to .env and add your key, or omit --llm to use the deterministic policy."
    )
    return 1


def run_aging_cli(argv: list[str]) -> int:
    reset = "--reset" in argv
    argv = [item for item in argv if item != "--reset"]
    try:
        as_of, rest = _as_of(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if rest:
        print(f"Unknown ar-aging option: {rest[0]}")
        return 1
    if reset:
        reset_state()
    report = run_aging(as_of)
    print(format_aging(report))
    if report.trace_path:
        print(f"\nTrace saved to {report.trace_path}")
    return 0


def run_collections_cli(argv: list[str]) -> int:
    live, argv = _live_flag(argv)
    reset = "--reset" in argv
    argv = [item for item in argv if item != "--reset"]
    try:
        as_of, rest = _as_of(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if rest:
        print(f"Unknown ar-collections option: {rest[0]}")
        return 1
    if reset:
        reset_state()
    if live:
        missing = _require_key()
        if missing is not None:
            return missing
    run = run_collections(as_of, live=live)
    print(format_collections(run))
    if run.trace_path:
        print(f"\nTrace saved to {run.trace_path}")
    return 0


def run_cash_apply_cli(argv: list[str]) -> int:
    live, argv = _live_flag(argv)
    try:
        as_of, rest = _as_of(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if not rest:
        print("Usage: python main.py ar-cash-apply PAY-001 [--as-of 2026-09-30]")
        return 1
    payment_id = rest[0]
    if live:
        missing = _require_key()
        if missing is not None:
            return missing
    try:
        trace = run_cash_apply(payment_id, as_of=as_of, live=live)
    except ValueError as exc:
        print(str(exc))
        return 1
    print(format_cash_apply(trace))
    return 0


def run_demo_cli(argv: list[str]) -> int:
    try:
        as_of, rest = _as_of(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if rest:
        print(f"Unknown ar-demo option: {rest[0]}")
        return 1
    print(format_demo(run_ar_demo(as_of)))
    return 0


def _review_options(argv: list[str]) -> tuple[list[str], str, str, list]:
    reason = ""
    reviewer = "ctl-cash"
    applies = []
    rest: list[str] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--reason":
            if index + 1 >= len(argv):
                raise ValueError("Usage: --reason TEXT")
            reason = argv[index + 1]
            index += 2
            continue
        if option == "--reviewer":
            if index + 1 >= len(argv):
                raise ValueError("Usage: --reviewer NAME")
            reviewer = argv[index + 1]
            index += 2
            continue
        if option == "--apply":
            if index + 1 >= len(argv):
                raise ValueError("Usage: --apply INV-AR-101:10000")
            applies.append(parse_apply_spec(argv[index + 1]))
            index += 2
            continue
        rest.append(option)
        index += 1
    return rest, reason, reviewer, applies


def run_review_list_cli(argv: list[str]) -> int:
    if argv:
        print(f"Unknown ar-review-list option: {argv[0]}")
        return 1
    print(format_review_list(open_reviews()))
    return 0


def run_review_show_cli(argv: list[str]) -> int:
    if not argv:
        print("Usage: python main.py ar-review-show PAY-005")
        return 1
    item = get_review(argv[0])
    if item is None:
        print(f"No review item for {argv[0]}")
        return 1
    print(format_review_item(item))
    return 0


def run_review_approve_cli(argv: list[str]) -> int:
    try:
        rest, reason, reviewer, _applies = _review_options(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if not rest:
        print("Usage: python main.py ar-review-approve PAY-005 [--reason TEXT]")
        return 1
    try:
        item = approve_review(
            rest[0],
            reviewer=reviewer,
            reason=reason or "Approved the proposed allocation.",
        )
    except ValueError as exc:
        print(str(exc))
        return 1
    print(format_review_resolution(item))
    return 0


def run_review_correct_cli(argv: list[str]) -> int:
    """Emergency Kernel door. Happy path is ctl-cash concurrence, not this CLI."""
    try:
        rest, reason, reviewer, applies = _review_options(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if not rest or not applies or not reason:
        print(
            "Usage: python main.py ar-review-correct PAY-005 "
            "--apply INV-AR-101:10000 --apply INV-AR-102:15000 --reason TEXT"
        )
        return 1
    try:
        item = correct_review(rest[0], applies, reason, reviewer=reviewer)
    except ValueError as exc:
        print(str(exc))
        return 1
    print(format_review_resolution(item))
    return 0


def run_review_reject_cli(argv: list[str]) -> int:
    try:
        rest, reason, reviewer, _applies = _review_options(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if not rest or not reason:
        print("Usage: python main.py ar-review-reject PAY-005 --reason TEXT")
        return 1
    try:
        item = reject_review(rest[0], reason, reviewer=reviewer)
    except ValueError as exc:
        print(str(exc))
        return 1
    print(format_review_resolution(item))
    return 0


def run_forecast_demo_cli(argv: list[str]) -> int:
    try:
        as_of, rest = _as_of(argv)
    except ValueError as exc:
        print(exc)
        return 1
    if rest:
        print(f"Unknown ar-forecast-demo option: {rest[0]}")
        return 1
    print(format_forecast_demo(run_ar_forecast_demo(as_of)))
    return 0
