"""Demo and eval entrypoints for cross-period organizational memory."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from memory.eval import format_eval_summary, persist_eval, run_memory_evaluation
from memory.format import format_lookup_trace
from memory.scenarios import (
    isolated_memory_workspace,
    run_harbor_cross_period,
    run_prepaid_cross_period,
    run_stripe_cross_period,
)
from memory.store import current_directory, load_memories


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _print_stripe(story: dict) -> None:
    aug = story["august_trace"]
    sep = story["september_trace"]
    print("August 2026 — Stripe payout difference")
    if aug is not None:
        print(f"  match {aug.final.reconciliation_id} {aug.final.match_type} {aug.final.status}")
        print(f"  bank ${aug.final.bank_amount:,.2f}  ledger ${aug.final.ledger_amount:,.2f}  diff ${aug.final.difference:,.2f}")
        print(f"  {aug.final.explanation}")
    print()
    print("September 2026 — later-period retrieval")
    if sep is not None:
        print(f"  match {sep.final.reconciliation_id} {sep.final.match_type} {sep.final.status}")
        print(f"  bank ${sep.final.bank_amount:,.2f}  ledger ${sep.final.ledger_amount:,.2f}  diff ${sep.final.difference:,.2f}")
        print()
        lookup = sep.memory_lookup
        if lookup is not None:
            print(format_lookup_trace(lookup))
        else:
            print("memory_lookup was not recorded on the September trace.")
    print()
    print(f"Memory records now stored: {', '.join(item.decision_id for item in load_memories()) or '(none)'}")
    print(f"Store: {current_directory() / 'decisions.json'}")


def _print_prepaid(story: dict) -> None:
    aug = story["august_trace"]
    sep = story["september_trace"]
    print("August 2026 — CloudCo prepaid treatment")
    if aug is not None:
        print(f"  {aug.prepaid_id} → {aug.selected_method}")
        print(f"  {aug.explanation}")
    print()
    print("September 2026 — CloudCo retrieves the August precedent")
    if sep is not None:
        print(f"  {sep.prepaid_id} → {sep.selected_method}")
        lookup = sep.memory_lookup
        if lookup is not None:
            print()
            print(format_lookup_trace(lookup))
    print()
    print(f"Memory records now stored: {', '.join(item.decision_id for item in load_memories()) or '(none)'}")


def _print_harbor(story: dict) -> None:
    aug = story["august_trace"]
    sep = story["september_trace"]
    print("August 2026 — Harbor Electric seasonal utility accrual")
    if aug is not None:
        print(f"  {aug.vendor} → {aug.final_method} {aug.final_amount}")
        print(f"  {aug.rationale}")
        if aug.written_memory_id:
            print(f"  wrote {aug.written_memory_id}")
    print()
    print("September 2026 — month-end retrieves the August methodology")
    if sep is not None:
        print(f"  {sep.vendor} → {sep.final_method} {sep.final_amount}")
        lookup = sep.memory_lookup
        if lookup is not None:
            print()
            print(format_lookup_trace(lookup))
        print()
        print(story["september_packet"])
    print()
    print(f"Memory records now stored: {', '.join(item.decision_id for item in load_memories()) or '(none)'}")


def run_memory_demo(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the August → September memory demo.")
    parser.add_argument("--story", choices=["stripe", "prepaid", "close", "accrual", "both"], default="stripe")
    parser.add_argument("--memory-off", action="store_true", help="Run the later period without retrieval.")
    args = parser.parse_args(argv)
    enabled = not args.memory_off
    dest = Path("runs") / "memory_demo" / f"DEMO-{_stamp()}"
    with isolated_memory_workspace(dest):
        if args.story in {"stripe", "both"}:
            _print_stripe(run_stripe_cross_period(memory_enabled=enabled))
            print()
        if args.story in {"prepaid", "both"}:
            _print_prepaid(run_prepaid_cross_period(memory_enabled=enabled))
        if args.story in {"close", "accrual", "both"}:
            _print_harbor(run_harbor_cross_period(memory_enabled=enabled))
        print(f"\nDemo workspace: {dest}")
    return 0


def run_memory_eval(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate memory ON vs OFF.")
    parser.add_argument("--output", default="", help="Directory for JSON + summary.md")
    args = parser.parse_args(argv)
    dest_dir = Path(args.output) if args.output else Path("runs") / "memory_eval" / f"MEM-{_stamp()}"
    with isolated_memory_workspace(dest_dir / "workspace"):
        payload = run_memory_evaluation()
    persist_eval(payload, dest_dir / "eval.json")
    print(format_eval_summary(payload))
    print()
    print(f"Wrote {dest_dir / 'eval.json'}")
    print(f"Wrote {dest_dir / 'summary.md'}")
    return 0
