"""Delegate Stripe/Adyen payouts to the existing adapters. Do not reimplement payout math."""

from __future__ import annotations

from integrations.cash import reconcile_payout, to_minor
from integrations.models import ProviderPayout, ReconciliationBreakdown
from integrations.store import all_payouts, get_payout, get_reconciliation, remember_reconciliation

from cash_recon.mathutil import cents, date_diff_days, date_gap, dollars
from cash_recon.models import (
    BANK_FEE_ACCOUNT,
    CASH_ACCOUNT,
    BankTransaction,
    LedgerEntry,
    MatchCandidate,
    ProposedJournalEntry,
    ProposedJournalLine,
)
from cash_recon.normalize import combined_text, detect_provider
from cash_recon.candidates import _candidate


def _payout_amount_minor(payout: ProviderPayout) -> int:
    return int(payout.amount)


def _breakdown_for(payout: ProviderPayout) -> ReconciliationBreakdown:
    existing = get_reconciliation(payout.payout_id)
    if existing is not None:
        return existing
    breakdown = reconcile_payout(payout)
    remember_reconciliation(breakdown)
    return breakdown


def list_provider_payouts() -> list[ProviderPayout]:
    return list(all_payouts())


def is_provider_bank_txn(txn: BankTransaction) -> str | None:
    return detect_provider(combined_text(txn), txn.provider)


def provider_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    payouts: list[ProviderPayout] | None = None,
) -> list[MatchCandidate]:
    payouts = payouts if payouts is not None else list_provider_payouts()
    rows: list[MatchCandidate] = []
    for txn in bank:
        provider = is_provider_bank_txn(txn)
        if not provider:
            continue
        matches = [
            payout
            for payout in payouts
            if payout.provider == provider and _payout_amount_minor(payout) == abs(txn.amount_minor)
        ]
        if not matches:
            matches = [
                payout
                for payout in payouts
                if payout.provider == provider and payout.bank_deposit_amount is not None and cents(payout.bank_deposit_amount) == txn.amount_minor
            ]
        if not matches:
            continue
        payout = matches[0]
        if len(matches) > 1:
            dated = [
                item
                for item in matches
                if item.arrival_date and date_diff_days(txn.date, item.arrival_date) is not None
            ]
            if dated:
                payout = min(dated, key=lambda item: date_gap(txn.date, item.arrival_date))
        breakdown = _breakdown_for(payout)
        books = [
            entry
            for entry in ledger
            if entry.amount_minor == txn.amount_minor
            and (
                payout.payout_id in combined_text(entry)
                or provider in combined_text(entry).lower()
                or (entry.raw_metadata or {}).get("payout_id") == payout.payout_id
                or (entry.raw_metadata or {}).get("provider") == provider
            )
        ]
        if not books:
            books = [
                entry
                for entry in ledger
                if entry.amount_minor == txn.amount_minor
                and entry.entry_type in {"processor_payout", "provider_payout"}
            ]
        if len(books) != 1:
            nearby = [
                entry
                for entry in ledger
                if entry.amount_minor == txn.amount_minor and date_gap(txn.date, entry.date) <= 2
            ]
            if len(nearby) == 1:
                books = nearby
        evidence = [
            f"provider:{provider}",
            f"payout_id:{payout.payout_id}",
            f"provider_status:{breakdown.status}",
            f"expected_payout:{breakdown.expected_payout_minor}",
            f"actual_payout:{breakdown.actual_payout_minor}",
            f"bank_matched:{breakdown.bank_matched}",
        ]
        if breakdown.exceptions:
            evidence.extend(f"exception:{item}" for item in breakdown.exceptions)
        provider_status = breakdown.status
        bank_equals_payout = (
            txn.amount_minor == breakdown.expected_payout_minor == breakdown.actual_payout_minor
        )
        if provider_status == "AWAITING_BANK" and bank_equals_payout:
            provider_status = "MATCH"
            evidence.append("bank_arrived:statement_equals_provider_net")
        matched = provider_status == "MATCH" and len(books) == 1
        rows.append(
            _candidate(
                "PROVIDER_PAYOUT",
                [txn],
                books[:1],
                evidence=evidence,
                score=2.5 if matched else 1.0,
                confidence=1.0 if matched else 0.4,
                provider=provider,
                provider_payout_id=payout.payout_id,
                provider_status=provider_status,
                ambiguities=[] if matched else ["provider_payout_not_clean"],
            )
        )
    return rows


def processor_reductions_minor(breakdown: ReconciliationBreakdown) -> dict[str, int]:
    fees = abs(to_minor(breakdown.fees))
    chargebacks = abs(to_minor(breakdown.chargebacks))
    refunds = abs(to_minor(breakdown.refunds))
    return {
        "fees": fees,
        "chargebacks": chargebacks,
        "refunds": refunds,
        "total": fees + chargebacks + refunds,
        "gross": to_minor(breakdown.gross_payments),
    }


def _provider_related(entry: LedgerEntry, provider: str, payout_id: str) -> bool:
    text = combined_text(entry).lower()
    meta = entry.raw_metadata or {}
    return (
        payout_id in text
        or provider in text
        or meta.get("payout_id") == payout_id
        or str(meta.get("provider") or "").lower() == provider
        or entry.entry_type in {"processor_gross", "processor_payout", "provider_payout"}
    )


def provider_netted_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    payouts: list[ProviderPayout] | None = None,
) -> list[MatchCandidate]:
    """Gross books vs net Stripe/Adyen deposit when processor reductions explain the gap."""
    payouts = payouts if payouts is not None else list_provider_payouts()
    rows: list[MatchCandidate] = []
    for txn in bank:
        provider = is_provider_bank_txn(txn)
        if not provider:
            continue
        matches = [
            payout
            for payout in payouts
            if payout.provider == provider
            and (
                _payout_amount_minor(payout) == abs(txn.amount_minor)
                or (payout.bank_deposit_amount is not None and cents(payout.bank_deposit_amount) == txn.amount_minor)
            )
        ]
        if not matches:
            continue
        payout = matches[0]
        breakdown = _breakdown_for(payout)
        reductions = processor_reductions_minor(breakdown)
        if reductions["total"] <= 0 or reductions["gross"] <= 0:
            continue
        books = [
            entry
            for entry in ledger
            if abs(entry.amount_minor) == reductions["gross"] and _provider_related(entry, provider, payout.payout_id)
        ]
        if len(books) != 1:
            continue
        entry = books[0]
        difference_minor = txn.amount_minor - entry.amount_minor
        if abs(difference_minor) != reductions["total"]:
            continue
        fee_id = f"{provider}:{payout.payout_id}:processor_reductions"
        cash_side = "credit" if txn.amount_minor < 0 else "debit"
        expense_side = "debit" if cash_side == "credit" else "credit"
        proposed = ProposedJournalEntry(
            memo=f"Record {provider} fees and chargebacks on {payout.payout_id}",
            related_bank_ids=[txn.transaction_id],
            related_ledger_ids=[entry.entry_id],
            support=fee_id,
            posted=False,
            lines=[
                ProposedJournalLine(
                    account=BANK_FEE_ACCOUNT,
                    amount=dollars(reductions["total"]),
                    amount_minor=reductions["total"],
                    side=expense_side,  # type: ignore[arg-type]
                ),
                ProposedJournalLine(
                    account=CASH_ACCOUNT,
                    amount=dollars(reductions["total"]),
                    amount_minor=reductions["total"],
                    side=cash_side,  # type: ignore[arg-type]
                ),
            ],
        )
        evidence = [
            f"provider:{provider}",
            f"payout_id:{payout.payout_id}",
            f"gross:{reductions['gross']}",
            f"stripe_fee:{reductions['fees']}" if provider == "stripe" else f"processor_fee:{reductions['fees']}",
            f"chargeback:{reductions['chargebacks']}",
            f"refund:{reductions['refunds']}",
            f"processor_reductions:{reductions['total']}",
            "reductions_equal_difference",
            f"bank_amount:{txn.amount_minor}",
            f"ledger_amount:{entry.amount_minor}",
        ]
        rows.append(
            _candidate(
                "FEE_NETTED",
                [txn],
                [entry],
                evidence=evidence,
                score=2.2,
                confidence=0.96,
                fee_ids=[fee_id],
                proposed=[proposed],
                provider=provider,
                provider_payout_id=payout.payout_id,
                provider_status="MATCH",
            )
        )
    return rows


def get_named_payout(payout_id: str) -> ProviderPayout | None:
    return get_payout(payout_id)
