"""Cross-workflow evidence chain using existing IDs. Does not copy source records."""

from __future__ import annotations

from audit.dataset import AuditDataset
from audit.models import AuditRun


ANCHOR_INVOICE = "INV-AUD-OK-001"


def evidence_chain(
    dataset: AuditDataset,
    run: AuditRun | None = None,
    invoice_id: str = ANCHOR_INVOICE,
) -> dict:
    approvals = [item.approval_id for item in dataset.approvals if item.object_id == invoice_id]
    payments = [
        item.payment_id
        for item in dataset.payments
        if invoice_id in item.invoice_ids or set(item.approval_ids) & set(approvals)
    ]
    journals = [
        item.entry_id
        for item in dataset.journals
        if invoice_id in item.related_source_ids or any(pay in item.related_source_ids for pay in payments)
    ]
    bank = [
        item.transaction_id
        for item in dataset.bank
        if invoice_id in (item.reference or "") or invoice_id in (item.description or "")
    ]
    ledger = [
        item.entry_id
        for item in dataset.ledger
        if invoice_id in (item.reference or "") or invoice_id in (item.description or "")
    ]
    reconciliations = [
        item.reconciliation_id
        for item in dataset.reconciliations
        if set(item.bank_transaction_ids) & set(bank) or set(item.ledger_entry_ids) & set(ledger)
    ]
    sample_ids: list[str] = []
    finding_ids: list[str] = []
    if run is not None:
        tracked = set(payments + approvals + journals + bank + ledger + reconciliations + [invoice_id])
        for sample in run.samples:
            if tracked & set(sample.sampled_ids):
                sample_ids.append(sample.sample_id)
        for finding in run.findings:
            ids = set(
                finding.affected_object_ids
                + finding.invoice_ids
                + finding.payment_ids
                + finding.approval_ids
                + finding.journal_entry_ids
                + finding.reconciliation_ids
            )
            if tracked & ids:
                finding_ids.append(finding.finding_id)
    complete = bool(invoice_id and approvals and payments and (bank or ledger) and reconciliations)
    return {
        "invoice_id": invoice_id,
        "approval_ids": approvals,
        "payment_ids": payments,
        "journal_ids": journals,
        "bank_ids": bank,
        "ledger_ids": ledger,
        "reconciliation_ids": reconciliations,
        "sample_ids": sample_ids,
        "finding_ids": finding_ids,
        "complete": complete,
    }


def format_chain(chain: dict) -> str:
    def _row(label: str, values) -> str:
        if isinstance(values, list):
            text = ", ".join(values) or "(none)"
        else:
            text = str(values)
        return f"{label}: {text}"

    return "\n".join(
        [
            "CROSS-WORKFLOW EVIDENCE TRACE",
            _row("invoice", chain["invoice_id"]),
            _row("  → AP approval", chain["approval_ids"]),
            _row("  → payment", chain["payment_ids"]),
            _row("  → bank", chain["bank_ids"]),
            _row("  → ledger", chain["ledger_ids"]),
            _row("  → reconciliation", chain["reconciliation_ids"]),
            _row("  → journal", chain["journal_ids"]),
            _row("  → audit sample", chain["sample_ids"]),
            _row("  → audit finding", chain["finding_ids"]),
            f"complete: {str(chain['complete']).lower()}",
        ]
    )
