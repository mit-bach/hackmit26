"""Economic-linkage checks for bank-to-ledger matches.

A reconciliation is valid only when evidence supports the relationship.
Equal amounts are never enough by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from cash_recon.models import BankTransaction, LedgerEntry, MatchCandidate
from cash_recon.normalize import (
    combined_text,
    counterparties_compatible,
    extract_invoice_ids,
    overlap_score,
    tokens,
)

MATCHED_TYPES = frozenset({"EXACT_MATCH", "GROUPED_MATCH", "FEE_NETTED", "PROVIDER_PAYOUT"})


@dataclass(frozen=True)
class Linkage:
    supported: bool
    reasons: tuple[str, ...]
    missing: tuple[str, ...]


def _shared_reference(bank: BankTransaction, ledger: LedgerEntry) -> bool:
    bank_text = combined_text(bank).lower()
    ledger_text = combined_text(ledger).lower()
    if bank.reference and bank.reference.lower() in ledger_text:
        return True
    if ledger.reference and ledger.reference.lower() in bank_text:
        return True
    bank_invoices = {item.lower() for item in extract_invoice_ids(bank_text)}
    ledger_invoices = {item.lower() for item in extract_invoice_ids(ledger_text)}
    if bank_invoices and ledger_invoices and bank_invoices & ledger_invoices:
        return True
    return False


def economic_link_supported(bank: BankTransaction, ledger: LedgerEntry) -> Linkage:
    """True only when entity, date-compatible type, and identity evidence agree."""
    reasons: list[str] = []
    missing: list[str] = []
    both_named = bool((bank.counterparty or "").strip() and (ledger.counterparty or "").strip())
    compatible = both_named and counterparties_compatible(bank.counterparty, ledger.counterparty)
    party_score = overlap_score(combined_text(bank), combined_text(ledger))
    shared_ref = _shared_reference(bank, ledger)
    same_provider = bool(bank.provider and ledger.counterparty and bank.provider.lower() in ledger.counterparty.lower())
    if compatible:
        reasons.append("counterparty")
    if shared_ref:
        reasons.append("shared_reference")
    if same_provider:
        reasons.append("provider")
    if party_score >= 0.34:
        reasons.append(f"token_overlap:{party_score:.2f}")
    if not both_named:
        missing.append("counterparty")
    if both_named and not compatible:
        missing.append("compatible_entity")
    if not shared_ref:
        missing.append("shared_reference")
    supported = bool(reasons)
    if not supported:
        missing.append("economic_linkage")
    return Linkage(supported=supported, reasons=tuple(reasons), missing=tuple(dict.fromkeys(missing)))


def candidate_link_supported(candidate: MatchCandidate, bank: list[BankTransaction], ledger: list[LedgerEntry]) -> Linkage:
    if candidate.match_type == "PROVIDER_PAYOUT":
        if candidate.provider and candidate.provider_payout_id:
            return Linkage(True, ("provider_payout",), ())
        return Linkage(False, (), ("provider_payout",))
    banks = {item.transaction_id: item for item in bank}
    ledgers = {item.entry_id: item for item in ledger}
    txn_rows = [banks[item] for item in candidate.bank_transaction_ids if item in banks]
    ledger_rows = [ledgers[item] for item in candidate.ledger_entry_ids if item in ledgers]
    if not txn_rows or (candidate.match_type in MATCHED_TYPES and not ledger_rows):
        return Linkage(False, (), ("records",))
    if candidate.match_type in {"UNMATCHED_BANK", "UNMATCHED_LEDGER", "UNEXPLAINED_DIFFERENCE", "POSSIBLE_DUPLICATE_REFUND", "POSSIBLE_DUPLICATE_BANK_TXN", "POSSIBLE_DUPLICATE_LEDGER_ENTRY", "TIMING_DIFFERENCE"}:
        return Linkage(True, ("non_match_disposition",), ())
    reasons: list[str] = []
    missing: list[str] = []
    for txn in txn_rows:
        for entry in ledger_rows:
            link = economic_link_supported(txn, entry)
            reasons.extend(link.reasons)
            missing.extend(link.missing)
    if not reasons:
        return Linkage(False, (), tuple(dict.fromkeys(missing or ["economic_linkage"])))
    return Linkage(True, tuple(dict.fromkeys(reasons)), ())


def amount_only_match(bank: BankTransaction, ledger: LedgerEntry) -> bool:
    """True when the only shared fact is the dollar amount."""
    if bank.amount_minor != ledger.amount_minor:
        return False
    link = economic_link_supported(bank, ledger)
    return not link.supported
