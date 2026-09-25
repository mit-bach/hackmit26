"""Python-owned validation. Agents cannot override these checks."""

from __future__ import annotations

from cash_recon.mathutil import dollars
from cash_recon.models import (
    BankTransaction,
    LedgerEntry,
    MatchCandidate,
    PeriodBalances,
    ReconciliationMatch,
    TieOut,
    ValidationResult,
)

MATCHED_TYPES = {"EXACT_MATCH", "GROUPED_MATCH", "PROVIDER_PAYOUT"}
EXPLAINED_TYPES = {"FEE_NETTED"}
TIMING_TYPES = {"TIMING_DIFFERENCE"}
HUMAN_TYPES = {
    "POSSIBLE_DUPLICATE_BANK_TXN",
    "POSSIBLE_DUPLICATE_REFUND",
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
    "UNEXPLAINED_DIFFERENCE",
    "UNMATCHED_BANK",
    "UNMATCHED_LEDGER",
}

DISPOSITION_FOR = {
    "EXACT_MATCH": "MATCHED",
    "GROUPED_MATCH": "MATCHED",
    "PROVIDER_PAYOUT": "MATCHED",
    "FEE_NETTED": "EXPLAINED_EXCEPTION",
    "TIMING_DIFFERENCE": "OUTSTANDING_TIMING_ITEM",
    "POSSIBLE_DUPLICATE_BANK_TXN": "HUMAN_REVIEW",
    "POSSIBLE_DUPLICATE_REFUND": "HUMAN_REVIEW",
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY": "HUMAN_REVIEW",
    "UNEXPLAINED_DIFFERENCE": "HUMAN_REVIEW",
    "UNMATCHED_BANK": "HUMAN_REVIEW",
    "UNMATCHED_LEDGER": "HUMAN_REVIEW",
}


def expected_disposition(match_type: str, *, provider_status: str | None = None) -> str:
    if match_type == "PROVIDER_PAYOUT" and provider_status and provider_status != "MATCH":
        return "HUMAN_REVIEW"
    return DISPOSITION_FOR.get(match_type, "HUMAN_REVIEW")


def control_finding_for(match_type: str) -> str | None:
    if match_type in {
        "POSSIBLE_DUPLICATE_REFUND",
        "POSSIBLE_DUPLICATE_BANK_TXN",
        "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
        "UNEXPLAINED_DIFFERENCE",
    }:
        return match_type
    return None


def validate_candidate(
    candidate: MatchCandidate,
    bank: dict[str, BankTransaction],
    ledger: dict[str, LedgerEntry],
) -> ValidationResult:
    errors: list[str] = []
    reasons: list[str] = []
    txns = [bank[item] for item in candidate.bank_transaction_ids if item in bank]
    entries = [ledger[item] for item in candidate.ledger_entry_ids if item in ledger]
    if len(txns) != len(candidate.bank_transaction_ids):
        errors.append("missing_bank_transaction")
    if len(entries) != len(candidate.ledger_entry_ids):
        errors.append("missing_ledger_entry")
    bank_minor = sum(item.amount_minor for item in txns)
    ledger_minor = sum(item.amount_minor for item in entries)
    if bank_minor != candidate.bank_amount_minor:
        errors.append("bank_amount_mismatch")
    if ledger_minor != candidate.ledger_amount_minor:
        errors.append("ledger_amount_mismatch")
    if (bank_minor - ledger_minor) != candidate.difference_minor:
        errors.append("difference_mismatch")
    if candidate.match_type in MATCHED_TYPES and candidate.difference_minor != 0:
        errors.append("matched_with_difference")
    if candidate.match_type == "GROUPED_MATCH":
        if len(entries) < 2:
            errors.append("grouped_match_requires_multiple_ledger_entries")
        if bank_minor != ledger_minor:
            errors.append("grouped_sum_does_not_equal_bank")
    if candidate.match_type == "FEE_NETTED":
        if not candidate.fee_evidence_ids:
            errors.append("fee_netted_without_evidence")
            reasons.append("fee_explanation_lacks_evidence")
        if not candidate.proposed_adjusting_entries:
            errors.append("fee_netted_missing_proposed_entry")
        if abs(candidate.difference_minor) != abs(sum(line.amount_minor for je in candidate.proposed_adjusting_entries for line in je.lines) // 2 if candidate.proposed_adjusting_entries else -1):
            if candidate.proposed_adjusting_entries:
                fee_line = abs(candidate.proposed_adjusting_entries[0].lines[0].amount_minor)
                if fee_line != abs(candidate.difference_minor):
                    errors.append("proposed_fee_does_not_equal_difference")
    if candidate.match_type == "UNEXPLAINED_DIFFERENCE":
        reasons.append("unexplained_difference")
        if candidate.difference_minor == 0:
            errors.append("unexplained_with_zero_difference")
    if candidate.match_type == "PROVIDER_PAYOUT" and candidate.provider_status != "MATCH":
        reasons.append("provider_payout_not_matched")
    if "counterparty_mismatch" in candidate.ambiguities:
        reasons.append("counterparty_mismatch")
    if candidate.match_type in HUMAN_TYPES:
        reasons.append("requires_human_review")
    human = bool(reasons) or candidate.match_type in HUMAN_TYPES
    if errors:
        human = True
        reasons.append("arithmetic_failed")
    return ValidationResult(passed=not errors, errors=errors, human_review_required=human, reasons=list(dict.fromkeys(reasons)))


def reconciling_impact(
    match: ReconciliationMatch,
    period: str,
    bank: dict[str, BankTransaction],
    ledger: dict[str, LedgerEntry],
) -> int:
    """In-period bank minus in-period ledger. Adjacent-period legs are excluded."""
    bank_minor = sum(
        bank[item].amount_minor
        for item in match.bank_transaction_ids
        if item in bank and bank[item].period == period
    )
    ledger_minor = sum(
        ledger[item].amount_minor
        for item in match.ledger_entry_ids
        if item in ledger and ledger[item].period == period
    )
    return bank_minor - ledger_minor


def compute_tie_out(
    balances: PeriodBalances,
    period_bank: list[BankTransaction],
    period_ledger: list[LedgerEntry],
    matches: list[ReconciliationMatch],
    *,
    period: str,
    bank: dict[str, BankTransaction] | None = None,
    ledger: dict[str, LedgerEntry] | None = None,
) -> TieOut:
    bank_map = bank or {item.transaction_id: item for item in period_bank}
    ledger_map = ledger or {item.entry_id: item for item in period_ledger}
    bank_ending_minor = balances.opening_bank_minor + sum(item.amount_minor for item in period_bank)
    ledger_ending_minor = balances.opening_ledger_minor + sum(item.amount_minor for item in period_ledger)
    break_minor = bank_ending_minor - ledger_ending_minor
    items = []
    reconciling_minor = 0
    for match in matches:
        impact = reconciling_impact(match, period, bank_map, ledger_map)
        reconciling_minor += impact
        if impact == 0 and match.match_type in MATCHED_TYPES:
            continue
        items.append(
            {
                "reconciliation_id": match.reconciliation_id,
                "match_type": match.match_type,
                "status": match.status,
                "impact": dollars(impact),
                "impact_minor": impact,
                "explanation": match.explanation,
            }
        )
    tied = reconciling_minor == break_minor
    formula = "bank_ending - ledger_ending = sum(in-period bank − in-period ledger) across matches"
    return TieOut(
        bank_ending=dollars(bank_ending_minor),
        ledger_ending=dollars(ledger_ending_minor),
        bank_ending_minor=bank_ending_minor,
        ledger_ending_minor=ledger_ending_minor,
        break_amount=dollars(break_minor),
        break_minor=break_minor,
        reconciling_sum=dollars(reconciling_minor),
        reconciling_sum_minor=reconciling_minor,
        tied=tied,
        items=items,
        formula=formula,
    )


def period_status(tie_out: TieOut, matches: list[ReconciliationMatch]) -> str:
    if not tie_out.tied:
        return "FAILED_TIE"
    blocking = [
        item
        for item in matches
        if item.status == "HUMAN_REVIEW" or item.match_type == "UNEXPLAINED_DIFFERENCE"
    ]
    if blocking:
        return "OPEN"
    return "RECONCILED"


def force_human_review(match: ReconciliationMatch, reason: str) -> ReconciliationMatch:
    findings = list(match.control_findings)
    if reason not in findings:
        findings.append(reason)
    return match.model_copy(
        update={
            "status": "HUMAN_REVIEW",
            "reviewer_status": "HUMAN_REVIEW",
            "human_review": True,
            "control_findings": findings,
        }
    )
