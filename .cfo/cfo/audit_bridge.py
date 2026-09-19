"""Map operational September records into the existing Auditor Agent dataset.

Does not rewrite audit controls. Adds the company records the workflows just
produced so sampling and re-performance see the same IDs and amounts.
"""

from __future__ import annotations

from audit.dataset import AuditDataset, load_dataset
from audit.models import AccountingPeriod, AuditInvoice, AuditJournalEntry, PlantedReconciliation
from audit.reperformance import reperform_cash_match
from cash_recon.demo import load_demo_dataset
from cash_recon.models import CashReconciliationReport, ReconciliationMatch
from close.cash_overlay import apply_overlays
from close.ledger import load_entries
from close.models import MonthEndState
from cfo.company import PERIOD
from sample_data.adapters import invoice_to_audit
from tools import all_invoices


def _recon_type(match: ReconciliationMatch) -> str:
    if match.match_type == "PROVIDER_PAYOUT" and (match.provider or "").lower() == "stripe":
        return "stripe_payout"
    if match.match_type == "PROVIDER_PAYOUT":
        return "adyen_payout"
    return "bank_ledger"


def match_to_planted(match: ReconciliationMatch) -> PlantedReconciliation:
    return PlantedReconciliation(
        reconciliation_id=match.reconciliation_id,
        period=match.period,
        recon_type=_recon_type(match),
        bank_transaction_ids=list(match.bank_transaction_ids),
        ledger_entry_ids=list(match.ledger_entry_ids),
        original_match_type=match.match_type,
        original_status=match.status,
        original_bank_amount=match.bank_amount,
        original_ledger_amount=match.ledger_amount,
        original_difference=match.difference,
        planted_error=False,
        invoice_ids=[],
    )


def operational_audit_dataset(
    period: str,
    *,
    close_state: MonthEndState | None = None,
    cash_report: CashReconciliationReport | None = None,
) -> AuditDataset:
    """Audit fixtures plus the operational invoices, cash matches, and close journals."""
    data = load_dataset(period)
    if close_state is not None and close_state.period.status == "CLOSED":
        data.period = AccountingPeriod(
            period=period,
            status="CLOSED",
            close_timestamp=close_state.period.closed_at,
            closed_by=close_state.period.approved_by,
            close_id=close_state.close_id,
        )

    seen_inv = {item.invoice_id for item in data.invoices}
    for invoice in all_invoices():
        if invoice.invoice_id in seen_inv:
            continue
        data.invoices.append(
            invoice_to_audit(invoice, vendor_id=invoice.vendor, period=period)
        )
        seen_inv.add(invoice.invoice_id)

    balances, bank, ledger, fees = load_demo_dataset()
    _ = balances
    if close_state is not None:
        ledger, fees = apply_overlays(close_state.period.period, ledger, fees)
    known_bank = {item.transaction_id for item in data.bank}
    known_ledger = {item.entry_id for item in data.ledger}
    known_fees = {item.evidence_id for item in data.fees}
    data.bank.extend(item for item in bank if item.transaction_id not in known_bank)
    data.ledger.extend(item for item in ledger if item.entry_id not in known_ledger)
    data.fees.extend(item for item in fees if item.evidence_id not in known_fees)

    if cash_report is not None:
        known_rec = {item.reconciliation_id for item in data.reconciliations}
        for match in cash_report.matches:
            if match.reconciliation_id in known_rec:
                continue
            data.reconciliations.append(match_to_planted(match))
            known_rec.add(match.reconciliation_id)

    known_je = {item.entry_id for item in data.journals}
    for row in load_entries():
        entry_id = str(row.get("entry_id") or "")
        if not entry_id or entry_id in known_je:
            continue
        if row.get("period") and row.get("period") != period:
            continue
        data.journals.append(
            AuditJournalEntry(
                entry_id=entry_id,
                period=str(row.get("period") or period),
                effective_date=str(row.get("created_at") or f"{period}-30"),
                posting_date=str(row.get("created_at") or f"{period}-30")[:10],
                posting_timestamp=str(row.get("created_at") or ""),
                amount=float(row.get("debit") or row.get("amount") or 0),
                memo=str(row.get("memo") or ""),
                authorized=True,
                related_source_ids=[
                    str(row.get("source_document_id") or ""),
                    str(row.get("transaction_id") or ""),
                ],
                debit_account=str(row.get("debit_account") or ""),
                credit_account=str(row.get("credit_account") or ""),
            )
        )
        known_je.add(entry_id)
    return data


def prove_operational_independence(
    dataset: AuditDataset,
    match: ReconciliationMatch,
    *,
    audit_run_id: str = "CFO-IND-CASH",
) -> dict:
    """Hold source cash evidence constant; corrupt only the original conclusion."""
    planted = match_to_planted(match)
    before = reperform_cash_match(
        planted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    corrupted = planted.model_copy(
        update={"original_status": "UNMATCHED", "original_match_type": "UNMATCHED_BANK"}
    )
    after = reperform_cash_match(
        corrupted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    return {
        "reconciliation_id": match.reconciliation_id,
        "bank_transaction_ids": list(match.bank_transaction_ids),
        "used_original_as_input": before.used_original_as_input or after.used_original_as_input,
        "independent_unchanged": before.independent_result == after.independent_result,
        "before_agreed": before.agreed,
        "after_agreed": after.agreed,
        "disagreement_detected": before.agreed and not after.agreed,
        "passed": (
            not before.used_original_as_input
            and not after.used_original_as_input
            and before.independent_result == after.independent_result
            and before.agreed
            and not after.agreed
        ),
    }


def featured_independence_match(report: CashReconciliationReport) -> ReconciliationMatch | None:
    """Prefer a clean operational match; fall back to any MATCHED row."""
    exact = next(
        (
            item
            for item in report.matches
            if item.match_type == "EXACT_MATCH" and item.status == "MATCHED"
        ),
        None,
    )
    if exact is not None:
        return exact
    grouped = next(
        (
            item
            for item in report.matches
            if item.match_type == "GROUPED_MATCH" and item.status == "MATCHED"
        ),
        None,
    )
    if grouped is not None:
        return grouped
    return next((item for item in report.matches if item.status == "MATCHED"), None)


def default_operational_dataset(period: str = PERIOD) -> AuditDataset:
    return operational_audit_dataset(period)
