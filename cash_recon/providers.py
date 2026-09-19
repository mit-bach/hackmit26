"""Delegate Stripe/Adyen payouts to the existing adapters. Do not reimplement payout math."""

from __future__ import annotations

from integrations.cash import reconcile_payout
from integrations.models import ProviderPayout, ReconciliationBreakdown
from integrations.store import all_payouts, get_payout, get_reconciliation, remember_reconciliation

from cash_recon.mathutil import cents, date_diff_days, date_gap
from cash_recon.models import BankTransaction, LedgerEntry, MatchCandidate
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
        matched = breakdown.status == "MATCH" and len(books) == 1
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
                provider_status=breakdown.status,
                ambiguities=[] if matched else ["provider_payout_not_clean"],
            )
        )
    return rows


def get_named_payout(payout_id: str) -> ProviderPayout | None:
    return get_payout(payout_id)
