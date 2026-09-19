#!/usr/bin/env python3
"""Review a single accounts-payable invoice.

Usage:
    python main.py INV-001
    python main.py INV-017 --correct APPROVE --note "Same vendor, name variant only"
    python main.py --list-memory
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from models import APDecision
from tools import DataFileError, load_invoice, python_checks

load_dotenv(Path(__file__).resolve().parent / ".env")

VALID_DECISIONS = ("APPROVE", "HOLD", "HUMAN_REVIEW")


def format_currency(amount: float | None) -> str:
    if amount is None:
        return "n/a"
    return f"${amount:,.2f}"


def format_decision(decision: APDecision) -> str:
    reasons = "\n".join(f"- {reason}" for reason in decision.reasons) or "- (none)"
    evidence = "\n".join(f"- {item}" for item in decision.evidence_used) or "- (none)"
    duplicate = "yes" if decision.duplicate_detected else "no"
    receipt = decision.receipt_status.upper() if decision.receipt_status else "UNKNOWN"
    return (
        f"Invoice: {decision.invoice_id}\n"
        f"Decision: {decision.decision}\n"
        f"Confidence: {decision.confidence:.2f}\n"
        f"Amount difference: {format_currency(decision.amount_difference)}\n"
        f"Duplicate detected: {duplicate}\n"
        f"Receipt status: {receipt}\n"
        f"\n"
        f"Reasons:\n"
        f"{reasons}\n"
        f"\n"
        f"Evidence:\n"
        f"{evidence}"
    )


def require_api_key() -> bool:
    if os.environ.get("OPENAI_API_KEY"):
        return True
    print(
        "OPENAI_API_KEY is not set.\n"
        "Copy .env.example to .env and add your key, or run:\n"
        "  export OPENAI_API_KEY=sk-...\n"
        "Then rerun: python main.py INV-001"
    )
    return False


def review(invoice_id: str) -> int:
    try:
        from agent import review_invoice

        decision = review_invoice(invoice_id)
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1
    except Exception as exc:
        print(f"The AP agent failed: {exc}")
        return 1

    print(format_decision(decision))
    return 0


def list_memory() -> int:
    from memory import load_precedents

    items = load_precedents()
    if not items:
        print("No human corrections stored yet.")
        print('Save one with: python main.py INV-017 --correct APPROVE --note "..."')
        return 0

    print(f"{len(items)} stored correction(s):\n")
    for item in items:
        issues = ", ".join(item.situation.get("issue_types") or [])
        print(f"{item.id}  {item.invoice_id}  ->  {item.corrected_decision}")
        print(f"  issues: {issues or '(none)'}")
        print(f"  note: {item.note}")
        print(f"  saved: {item.created_at}")
        print()
    return 0


def save_and_rereview(invoice_id: str, corrected_decision: str, note: str) -> int:
    from memory import save_correction

    try:
        checks = python_checks(invoice_id)
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1

    record = save_correction(invoice_id, corrected_decision, note, checks)
    issues = ", ".join(record.situation.get("issue_types") or [])
    print(f"Saved {record.id} for {invoice_id} -> {record.corrected_decision}")
    print(f"Issues: {issues or '(none)'}")
    print(f"Note: {record.note}")
    print()
    print("Re-running the agent with this precedent in memory...\n")
    return review(invoice_id)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review an accounts-payable invoice or store a human correction."
    )
    parser.add_argument("invoice_id", nargs="?", help="Invoice ID such as INV-001")
    parser.add_argument(
        "--correct",
        choices=VALID_DECISIONS,
        help="Store a reviewer correction and re-run the agent",
    )
    parser.add_argument(
        "--note",
        default="",
        help="Why the reviewer overrode the agent",
    )
    parser.add_argument(
        "--list-memory",
        action="store_true",
        help="Show stored human corrections",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])

    if args.list_memory:
        return list_memory()

    if not args.invoice_id:
        print("Usage: python main.py INV-001")
        print('       python main.py INV-017 --correct APPROVE --note "Same vendor"')
        print("       python main.py --list-memory")
        return 1

    invoice_id = args.invoice_id.strip().upper()

    try:
        invoice = load_invoice(invoice_id)
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1

    if invoice is None:
        print(f"Unknown invoice ID: {invoice_id}")
        print("Check data/invoices.json for a valid ID such as INV-001.")
        return 1

    if args.correct:
        if not args.note.strip():
            print("Please include --note explaining the correction.")
            print(
                'Example: python main.py INV-017 --correct APPROVE --note '
                '"Acme Supply Co. is the same vendor as Acme Supplies"'
            )
            return 1
        if not require_api_key():
            return 1
        return save_and_rereview(invoice_id, args.correct, args.note)

    if not require_api_key():
        return 1
    return review(invoice_id)


if __name__ == "__main__":
    raise SystemExit(main())
