"""Post an AP payment through cash recon, the shared GL, and reporting."""

from __future__ import annotations

from close.context import remember_link
from close.dates import period_from_date
from close.ledger import post_entry
from reporting.ledger import post_balanced_entry
from reporting.models import CashActualMovement
from tools import load_invoice


def post_ap_payment(
    invoice_id: str,
    *,
    payment_date: str,
    bank_transaction_id: str = "",
    reconciliation_id: str = "",
    amount: float | None = None,
    trace_id: str = "",
) -> dict:
    invoice = load_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Unknown invoice {invoice_id}")
    paid = float(amount if amount is not None else invoice.amount)
    period = period_from_date(payment_date)
    bank_transaction_id = bank_transaction_id or f"BNK-{invoice_id}"
    reconciliation_id = reconciliation_id or f"REC-{invoice_id}"
    evidence = [f"invoice:{invoice_id}", f"bank:{bank_transaction_id}", f"recon:{reconciliation_id}"]
    gl = post_entry(
        period=period,
        memo=f"Pay {invoice_id} {invoice.vendor}",
        debit_account="Accounts Payable",
        credit_account="Cash",
        amount=paid,
        entry_type="ap_payment",
        idempotency_key=f"pay:{invoice_id}:{payment_date}",
        source_document_id=invoice_id,
        transaction_id=invoice_id,
        evidence_refs=evidence,
        related_ids={
            "bank_transaction_id": bank_transaction_id,
            "reconciliation_id": reconciliation_id,
        },
    )
    reporting_lines = post_balanced_entry(
        period=period,
        posting_date=payment_date,
        debit_account="Accounts Payable",
        credit_account="Cash",
        amount=paid,
        memo=f"Pay {invoice_id} {invoice.vendor}",
        transaction_id=invoice_id,
        source_workflow="ap",
        source_document_id=invoice_id,
        vendor=invoice.vendor,
        evidence_refs=evidence + [gl["entry_id"]],
        trace_ids=[trace_id] if trace_id else [],
        idempotency_key=f"rpt-pay:{invoice_id}:{payment_date}",
    )
    link = remember_link(
        source_document_id=invoice_id,
        transaction_id=invoice_id,
        journal_entry_id=gl["entry_id"],
        account_id="Accounts Payable",
        reconciliation_id=reconciliation_id,
        extra={
            "bank_transaction_id": bank_transaction_id,
            "reporting_entry_id": reporting_lines[0].entry_id,
        },
    )
    movement = CashActualMovement(
        movement_id=f"ACT-{invoice_id}",
        source_type="invoice",
        source_id=invoice_id,
        date=payment_date,
        amount=-abs(paid),
        kind="outflow",
        description=f"Paid {invoice.vendor}",
        bank_transaction_id=bank_transaction_id,
        ledger_entry_id=gl["entry_id"],
        reconciliation_id=reconciliation_id,
        evidence_refs=evidence,
    )
    return {
        "invoice_id": invoice_id,
        "journal": gl,
        "reporting_lines": [item.model_dump() for item in reporting_lines],
        "link": link.model_dump(),
        "movement": movement.model_dump(),
        "bank_transaction_id": bank_transaction_id,
        "reconciliation_id": reconciliation_id,
    }
