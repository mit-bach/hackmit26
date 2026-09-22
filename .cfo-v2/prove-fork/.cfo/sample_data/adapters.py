"""Deterministic adapters between existing domain representations.

When two workflows already model the same object differently, convert
explicitly. Never invent a second copy with a new amount or identity.
"""

from __future__ import annotations

from audit.models import AuditInvoice, AuditJournalEntry, AuditPayment, AuditVendor
from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, LedgerEntry
from integrations.models import ProviderPayout
from models import Invoice
from reporting.models import ReportingLine

from sample_data.context import dollars
from sample_data.models import JournalEntryRecord, VendorPayment


def invoice_to_audit(invoice: Invoice, vendor_id: str, period: str, *, decision: str | None = None, duplicate: bool | None = None) -> AuditInvoice:
    return AuditInvoice(
        invoice_id=invoice.invoice_id,
        vendor_id=vendor_id,
        vendor=invoice.vendor,
        vendor_invoice_number=invoice.vendor_invoice_number,
        amount=invoice.amount,
        invoice_date=invoice.invoice_date,
        period=period,
        source="canonical_ap",
        operational_decision=decision,
        operational_duplicate_detected=duplicate,
    )


def vendor_to_audit(vendor_id: str, vendor_name: str, first_seen: str, *, unusual: bool = False) -> AuditVendor:
    return AuditVendor(
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        first_seen=first_seen,
        status="active",
        unusual=unusual,
    )


def vendor_payment_to_audit(payment: VendorPayment, period: str, approval_ids: list[str]) -> AuditPayment:
    return AuditPayment(
        payment_id=payment.payment_id,
        amount=dollars(payment.amount_minor),
        currency="USD",
        vendor_id=payment.vendor_id,
        vendor_name=payment.vendor,
        payment_date=payment.payment_date,
        payment_method=payment.method,
        source="manual" if payment.round_number or payment.on_hold_invoice else "automated",
        invoice_ids=list(payment.invoice_ids),
        approval_ids=approval_ids,
        initiator_id=payment.initiator_id,
        approver_id=payment.approver_id,
        period=period,
        recurring=False,
        description=payment.description,
        missing_support=payment.on_hold_invoice or payment.round_number,
    )


def journal_to_audit(entry: JournalEntryRecord) -> AuditJournalEntry:
    return AuditJournalEntry(
        entry_id=entry.entry_id,
        period=entry.period,
        effective_date=entry.effective_date,
        posting_date=entry.posting_date,
        posting_timestamp=entry.posting_timestamp,
        amount=entry.amount,
        vendor=entry.vendor,
        memo=entry.memo,
        poster_id=entry.poster_id,
        poster_role="controller" if entry.authorized else "staff_accountant",
        entry_source="manual" if entry.post_close else "automated",
        authorization_id=entry.authorization_id,
        authorized=entry.authorized,
        related_source_ids=list(entry.related_ids),
        debit_account=entry.debit_account,
        credit_account=entry.credit_account,
        preparer_id=entry.poster_id,
        approver_id=entry.approver_id,
    )


def journal_to_reporting_lines(entry: JournalEntryRecord, account_class: str, side: str) -> ReportingLine:
    posted_account = entry.debit_account if side == "debit" else entry.credit_account
    return ReportingLine(
        line_id=f"{entry.entry_id}-{side[:1].upper()}",
        entry_id=entry.entry_id,
        transaction_id=entry.transaction_id or entry.entry_id,
        period=entry.period,
        posting_date=entry.posting_date,
        account=posted_account,
        account_class=account_class,  # type: ignore[arg-type]
        side=side,  # type: ignore[arg-type]
        amount=entry.amount,
        memo=entry.memo,
        vendor=entry.vendor,
        customer=entry.customer,
        product=entry.product,
        category=entry.category,
        quantity=entry.quantity,
        rate=entry.rate,
        source_workflow="sample_data",
        source_document_id=entry.source_document_id,
        ledger_entry_id=entry.entry_id,
        evidence_refs=list(entry.evidence_refs),
        idempotency_key=f"{entry.entry_id}-{side}",
    )


def cash_bank(
    transaction_id: str,
    date: str,
    amount_minor: int,
    *,
    description: str,
    reference: str = "",
    counterparty: str = "",
    transaction_type: str = "other",
    source: str = "operating_account",
    provider: str | None = None,
    metadata: dict | None = None,
) -> BankTransaction:
    return BankTransaction(
        transaction_id=transaction_id,
        date=date,
        amount=dollars(amount_minor),
        currency="USD",
        description=description,
        reference=reference,
        counterparty=counterparty,
        transaction_type=transaction_type,
        source=source,
        provider=provider,
        period=period_of(date),
        amount_minor=amount_minor,
        raw_metadata=metadata or {},
    )


def cash_ledger(
    entry_id: str,
    date: str,
    amount_minor: int,
    *,
    counterparty: str = "",
    reference: str = "",
    description: str = "",
    entry_type: str = "other",
    metadata: dict | None = None,
) -> LedgerEntry:
    return LedgerEntry(
        entry_id=entry_id,
        date=date,
        amount=dollars(amount_minor),
        currency="USD",
        account="1000-Cash",
        counterparty=counterparty,
        reference=reference,
        description=description,
        entry_type=entry_type,
        period=period_of(date),
        source="gl",
        amount_minor=amount_minor,
        raw_metadata=metadata or {},
    )


def payout_to_bank(payout: ProviderPayout, transaction_id: str, date: str) -> BankTransaction:
    return cash_bank(
        transaction_id,
        date,
        int(payout.amount),
        description=f"{payout.provider.upper()} PAYOUT {payout.payout_id}",
        reference=payout.payout_id,
        counterparty=payout.provider.upper(),
        transaction_type="payout",
        provider=payout.provider,
        metadata={"payout_id": payout.payout_id, "provider": payout.provider},
    )


def payout_to_ledger(payout: ProviderPayout, entry_id: str, date: str) -> LedgerEntry:
    return cash_ledger(
        entry_id,
        date,
        int(payout.amount),
        counterparty=payout.provider.title(),
        reference=payout.payout_id,
        description=f"{payout.provider} payout {payout.payout_id}",
        entry_type="provider_payout",
        metadata={"payout_id": payout.payout_id, "provider": payout.provider},
    )


def assert_same_amount(left_minor: int, right_minor: int, label: str) -> None:
    if left_minor != right_minor:
        raise ValueError(f"{label}: amount mismatch {left_minor} vs {right_minor}")


def invoice_cents(invoice: Invoice) -> int:
    return cents(invoice.amount)
