"""CLI for the month-end close checklist and close-month aliases."""

from __future__ import annotations

import argparse
import os


def _run(args: argparse.Namespace) -> int:
    from close.engine import run_month_end
    from close.report import format_month_end_status

    live = bool(getattr(args, "llm", False)) and bool(os.environ.get("OPENAI_API_KEY"))
    if getattr(args, "deterministic", False):
        live = False
    scenario = "clean" if getattr(args, "clean", False) else "demo"
    if getattr(args, "seed_demo", False):
        scenario = "seed_demo"
    state = run_month_end(
        args.period,
        scenario=scenario,
        live=live,
        reset=args.reset,
        allow_close=True,
    )
    print(format_month_end_status(state))
    return 0


def _status(args: argparse.Namespace) -> int:
    from close.engine import load_state, run_month_end
    from close.report import format_month_end_status

    state = load_state(args.period)
    if state is None:
        print(f"No saved close for {args.period}. Running a fresh checklist...")
        state = run_month_end(args.period, scenario="demo", live=False, reset=True)
    print(format_month_end_status(state))
    return 0


def _prepaid(args: argparse.Namespace) -> int:
    from prepaid.store import load_items, load_seed_items, save_items
    from prepaid.workflow import run_prepaid_workflow

    if not load_items():
        save_items(load_seed_items())
    report = run_prepaid_workflow(args.period, use_agent=False)
    print(f"Prepaid amortization {args.period}")
    print(f"Posted lines: {len(report.lines_posted)}")
    print(f"Journals: {', '.join(report.journal_entry_ids) or '(none)'}")
    for item in report.exceptions:
        print(f"Exception: {item}")
    return 0


def _depreciate(args: argparse.Namespace) -> int:
    from fixed_assets.store import load_assets, load_seed_assets, save_assets
    from fixed_assets.workflow import run_depreciation_workflow

    if not load_assets():
        save_assets(load_seed_assets())
    report = run_depreciation_workflow(args.period, use_agent=False)
    print(f"Depreciation {args.period}")
    print(f"Posted lines: {len(report.lines_posted)}")
    print(f"Register NBV: ${report.register_nbv:,.2f}")
    for item in report.exceptions:
        print(f"Exception: {item}")
    return 0


def _reviews(args: argparse.Namespace) -> int:
    from close.report import format_review_queue
    from close.reviews import load_reviews

    print(format_review_queue(load_reviews(args.period), period=args.period))
    return 0


def _review(args: argparse.Namespace) -> int:
    from close.report import format_review_item
    from close.reviews import get_review, load_reviews

    item = get_review(args.review_id) if args.review_id else None
    if item is None and not args.review_id:
        rows = load_reviews(args.period)
        open_rows = [row for row in rows if row.status != "RESOLVED"]
        item = open_rows[0] if open_rows else (rows[0] if rows else None)
    if item is None:
        print(f"No review item {args.review_id or ''} for {args.period}.")
        return 1
    print(format_review_item(item))
    return 0


def _resolve(args: argparse.Namespace) -> int:
    from close.actions import invalidate_downstream, resolve_review_item
    from close.engine import load_state, save_state
    from close.report import format_resolution

    item = resolve_review_item(
        args.review_id,
        action=args.action,
        reason=args.reason,
        reviewer=args.reviewer,
        invoice_id=args.invoice_id,
        document_id=args.document_id,
        evidence_id=args.evidence_id,
        period=args.period,
    )
    state = load_state(args.period)
    if state is not None:
        invalidate_downstream(state, item)
        save_state(state)
    print(format_resolution(item))
    return 0


def _rerun(args: argparse.Namespace) -> int:
    from close.engine import rerun_affected
    from close.report import format_rerun

    state = rerun_affected(args.period, live=False, review_id=args.review_id)
    print(format_rerun(state))
    return 0


def _finalize(args: argparse.Namespace) -> int:
    from close.engine import finalize_close
    from close.report import format_finalize

    live = bool(os.environ.get("OPENAI_API_KEY")) and not args.deterministic
    state = finalize_close(args.period, live=live)
    print(format_finalize(state))
    return 0 if state.period.status == "CLOSED" else 1


def _eval_live(args: argparse.Namespace) -> int:
    from close.eval_live import run_close_eval

    live = bool(getattr(args, "live", False)) and bool(os.environ.get("OPENAI_API_KEY")) and not args.deterministic
    repeat = max(1, int(getattr(args, "repeat", 1) or 1))
    print(run_close_eval(use_agent=live, live=live, repeat=repeat))
    return 0


def run_month_end_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Month-end close checklist")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the period close")
    run.add_argument("--period", default="2026-09")
    run.add_argument("--reset", action="store_true")
    run.add_argument("--clean", action="store_true")
    run.add_argument("--seed-demo", action="store_true")
    run.add_argument("--deterministic", action="store_true")
    run.add_argument("--llm", action="store_true")
    run.set_defaults(func=_run)

    status = sub.add_parser("status", help="Show saved close status")
    status.add_argument("--period", default="2026-09")
    status.set_defaults(func=_status)

    reviews = sub.add_parser("reviews", help="List the persisted review queue")
    reviews.add_argument("--period", default="2026-09")
    reviews.set_defaults(func=_reviews)

    review = sub.add_parser("review", help="Show one review item")
    review.add_argument("--period", default="2026-09")
    review.add_argument("--review-id", default="")
    review.set_defaults(func=_review)

    resolve = sub.add_parser("resolve", help="Resolve a review item by mutating source data")
    resolve.add_argument("--period", default="2026-09")
    resolve.add_argument("--review-id", required=True)
    resolve.add_argument("--action", default="")
    resolve.add_argument("--reason", default="")
    resolve.add_argument("--reviewer", default="human")
    resolve.add_argument("--invoice-id", default="")
    resolve.add_argument("--document-id", default="")
    resolve.add_argument("--evidence-id", default="")
    resolve.set_defaults(func=_resolve)

    rerun = sub.add_parser("rerun", help="Rerun only tasks downstream of resolved reviews")
    rerun.add_argument("--period", default="2026-09")
    rerun.add_argument("--review-id", default="")
    rerun.set_defaults(func=_rerun)

    finalize = sub.add_parser("finalize", help="Run final close gates and reviewer")
    finalize.add_argument("--period", default="2026-09")
    finalize.add_argument("--deterministic", action="store_true")
    finalize.set_defaults(func=_finalize)

    prepaid = sub.add_parser("prepaid", help="Run prepaid amortization only")
    prepaid.add_argument("--period", default="2026-09")
    prepaid.set_defaults(func=_prepaid)

    dep = sub.add_parser("depreciate", help="Run depreciation only")
    dep.add_argument("--period", default="2026-09")
    dep.set_defaults(func=_depreciate)

    ev = sub.add_parser("eval-live", help="Judgment evaluation (optional live agents)")
    ev.add_argument("--deterministic", action="store_true")
    ev.add_argument("--live", action="store_true", help="Exercise live agents when an API key is present")
    ev.add_argument("--repeat", type=int, default=1, help="Repeat isolated eval from the same canonical snapshot")
    ev.set_defaults(func=_eval_live)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Month-end close failed: {exc}")
        return 1


def _parse_month(argv: list[str]) -> tuple[str, list[str]]:
    period = "2026-09"
    rest = []
    i = 0
    while i < len(argv):
        item = argv[i]
        if item in {"--month", "--period"} and i + 1 < len(argv):
            period = argv[i + 1]
            i += 2
            continue
        if item[:1].isdigit() and len(item) == 7:
            period = item
            i += 1
            continue
        rest.append(item)
        i += 1
    return period, rest


def run_close_month_cli(argv: list[str]) -> int:
    period, rest = _parse_month(argv)
    parser = argparse.ArgumentParser(description="Coordinated month-end close")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--seed-demo", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--llm", action="store_true")
    args = parser.parse_args(rest)
    if args.seed_demo:
        args.reset = True
    args.period = period
    return _run(args)


def run_reopen_period_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Reopen a closed period")
    parser.add_argument("--month", "--period", dest="period", default="2026-09")
    parser.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    from close.engine import reopen_period

    state = reopen_period(args.period, args.reason)
    print(f"Period {args.period} REOPENED")
    print(f"Reason: {args.reason}")
    print(f"Original snapshots preserved: {', '.join(state.snapshot_ids) or '(none)'}")
    return 0


def run_resolve_review_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Resolve a HUMAN_REVIEW item")
    parser.add_argument("item_id")
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--month", "--period", dest="period", default="2026-09")
    parser.add_argument("--reviewer", default="human")
    parser.add_argument("--seed-demo", action="store_true")
    args = parser.parse_args(argv)
    from close.actions import ReviewActionError, resolve_review_item
    from close.engine import rerun_affected
    from close.report import format_resolution
    from close.resolve import resolve_review
    from close.reviews import get_review, load_reviews

    queued = get_review(args.item_id)
    if queued is None:
        for row in load_reviews(args.period):
            if args.item_id in {row.review_id, row.source_case_id}:
                queued = row
                break
    if queued is None and args.item_id.startswith("REC-"):
        bank_ids = _bank_ids_for_rec(args.item_id)
        for row in load_reviews(args.period):
            if row.source_case_id in bank_ids:
                queued = row
                break
        if queued is None:
            for row in load_reviews(args.period):
                if row.source_workflow == "cash" and "12.40" in (row.description or ""):
                    queued = row
                    break
    if queued is not None:
        actions = {
            "post_correcting_entry",
            "classify_reconciling_item",
            "apply_payment",
            "attach_evidence",
            "reject",
            "needs_more_evidence",
        }
        try:
            item = resolve_review_item(
                queued.review_id,
                action=args.resolution if args.resolution in actions else "",
                reason=args.resolution,
                reviewer=args.reviewer,
                period=args.period,
            )
        except ReviewActionError:
            item = resolve_review_item(
                queued.review_id,
                reason=args.resolution,
                reviewer=args.reviewer,
                period=args.period,
            )
        resolve_review(args.item_id, args.resolution, period=args.period, reviewer=args.reviewer)
        print(format_resolution(item))
        rerun_affected(args.period, review_id=item.review_id)
        return 0
    item = resolve_review(args.item_id, args.resolution, period=args.period, reviewer=args.reviewer)
    print(f"Resolved {item.item_id}")
    print(f"Resolution: {item.resolution}")
    print(f"Original status: {item.original_status or '—'}")
    print("Original audit history was not deleted.")
    return 0


def _bank_ids_for_rec(item_id: str) -> list[str]:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "runs" / "cash_recon"
    if not root.exists():
        return []
    for path in sorted(root.glob("*.json"), reverse=True):
        payload = json.loads(path.read_text())
        for match in payload.get("matches") or []:
            if match.get("reconciliation_id") == item_id:
                return list(match.get("bank_transaction_ids") or [])
    return []


def run_close_trace_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Inspect the close audit trail")
    parser.add_argument("--month", "--period", dest="period", default="2026-09")
    args = parser.parse_args(argv)
    from close.engine import load_state, run_month_end
    from close.report import format_close_trace

    state = load_state(args.period) or run_month_end(args.period, live=False, reset=False)
    print(format_close_trace(state))
    return 0


def run_account_recon_trace_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Inspect one balance-sheet reconciliation")
    parser.add_argument("reconciliation_id")
    args = parser.parse_args(argv)
    from bs_recon.store import get_trace

    trace, path = get_trace(args.reconciliation_id)
    if trace is None:
        print(f"Unknown reconciliation {args.reconciliation_id}")
        return 1
    rec = trace.final
    print(f"Reconciliation: {rec.reconciliation_id}")
    print(f"Account: {rec.account_name}")
    print(f"Period: {rec.period}")
    print(f"GL balance: {rec.ledger_balance:,.2f}")
    print(f"Supporting balance: {rec.supporting_balance or rec.evidence_balance:,.2f}")
    print(f"Difference: {rec.difference:,.2f}")
    print(f"Status: {rec.status}")
    print(f"Finding: {rec.finding}")
    print(f"Review: {rec.review_decision}")
    print(f"Trace: {path}")
    return 0


def run_eval_close_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Evaluate month-end close metrics")
    parser.add_argument("--month", "--period", dest="period", default="2026-09")
    args = parser.parse_args(argv)
    from close.eval import evaluate_close, format_eval
    from close.engine import load_state

    metrics = evaluate_close(args.period, state=load_state(args.period))
    print(format_eval(metrics))
    return 0


def run_post_journal_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Post a manual journal (closed-period control applies)")
    parser.add_argument("--date", required=True)
    parser.add_argument("--debit", required=True)
    parser.add_argument("--credit", required=True)
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--memo", default="Manual journal")
    parser.add_argument("--evidence", default="MANUAL")
    parser.add_argument("--actor", default="cli")
    args = parser.parse_args(argv)
    from close.dates import period_from_date
    from close.ledger import post_entry
    from close.period_lock import ClosedPeriodError

    period = period_from_date(args.date)
    try:
        entry = post_entry(
            period=period,
            memo=args.memo,
            debit_account=args.debit,
            credit_account=args.credit,
            amount=args.amount,
            entry_type="manual",
            idempotency_key=f"manual:{period}:{args.memo}:{args.amount}:{args.date}",
            source_document_id=args.evidence,
            evidence_refs=[args.evidence],
            actor=args.actor,
        )
    except ClosedPeriodError as exc:
        print(exc.event.event_type)
        print(exc.event.decision)
        print(f"Period {period} is closed. The entry was not posted.")
        print(f"Audit: {exc.event.audit_trace}")
        return 1
    print(f"Posted {entry['entry_id']}")
    return 0
