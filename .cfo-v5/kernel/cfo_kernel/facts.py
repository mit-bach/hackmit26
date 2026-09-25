"""Kernel facts the workflow engine reads. Not a Bot."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from cfo_kernel.paths import attach_computer, current


def bill_facts(invoice_id: str) -> dict:
    from tools import collect_case_evidence
    from workflow import must_hold

    evidence = collect_case_evidence(invoice_id)
    holds = must_hold(evidence)
    invoice = evidence.invoice
    receipt = evidence.goods_receipt
    exceptions = list(evidence.exception_types)
    clean = (
        not holds
        and not exceptions
        and bool(evidence.amount_matches)
        and bool(evidence.po_approved)
        and evidence.receipt_status == "full"
        and not evidence.duplicate_detected
    )
    return {
        "invoice_id": invoice_id,
        "amount": None if invoice is None else invoice.amount,
        "po_id": None if invoice is None else invoice.po_id,
        "receipt_id": None if receipt is None else receipt.receipt_id,
        "must_hold": holds,
        "exception_types": exceptions,
        "clean": clean,
    }


def cash_requires_sign_off(amount: float, disposition: str) -> dict:
    from cash_recon.engine import requires_sign_off

    return {
        "required": requires_sign_off(amount, disposition),
        "amount": amount,
        "disposition": disposition,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m cfo_kernel.facts bill INVOICE | signoff AMOUNT DISPOSITION", file=sys.stderr)
        return 2
    env_root = os.environ.get("HARNESS_COMPUTER")
    root = Path(env_root) if env_root else current().root
    attach_computer(root)
    command = argv[1]
    if command == "bill":
        print(json.dumps(bill_facts(argv[2])))
        return 0
    if command == "signoff":
        print(json.dumps(cash_requires_sign_off(float(argv[2]), argv[3])))
        return 0
    print(f"unknown facts command {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
