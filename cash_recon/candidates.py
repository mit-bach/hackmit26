"""Candidate generation. Python enumerates; agents may only choose among these."""

from __future__ import annotations

from itertools import combinations

from cash_recon.mathutil import adjacent_period, cents, date_diff_days, date_gap, dollars
from cash_recon.models import (
    BANK_FEE_ACCOUNT,
    CASH_ACCOUNT,
    BankTransaction,
    FeeEvidence,
    LedgerEntry,
    MatchCandidate,
    ProposedJournalEntry,
    ProposedJournalLine,
)
from cash_recon.normalize import combined_text, counterparties_compatible, looks_like_refund, overlap_score, tokens

MAX_GROUP_SIZE = 4
MAX_GROUP_POOL = 12
EXACT_DATE_WINDOW = 3
GROUP_DATE_WINDOW = 7
FEE_DATE_WINDOW = 2
DUPLICATE_DATE_WINDOW = 2
TIMING_DATE_WINDOW = 5
NEAR_AMOUNT_WINDOW = 5000  # $50.00 in cents; $12.40 is inside, large gaps are not


def _cid(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


def _candidate(
    match_type: str,
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    *,
    evidence: list[str],
    score: float,
    confidence: float,
    fee_ids: list[str] | None = None,
    provider: str | None = None,
    provider_payout_id: str | None = None,
    provider_status: str | None = None,
    proposed: list[ProposedJournalEntry] | None = None,
    ambiguities: list[str] | None = None,
) -> MatchCandidate:
    bank_minor = sum(item.amount_minor for item in bank)
    ledger_minor = sum(item.amount_minor for item in ledger)
    difference_minor = bank_minor - ledger_minor
    return MatchCandidate(
        candidate_id=_cid(
            match_type,
            ",".join(item.transaction_id for item in bank) or "-",
            ",".join(item.entry_id for item in ledger) or "-",
        ),
        match_type=match_type,  # type: ignore[arg-type]
        bank_transaction_ids=[item.transaction_id for item in bank],
        ledger_entry_ids=[item.entry_id for item in ledger],
        bank_amount=dollars(bank_minor),
        ledger_amount=dollars(ledger_minor),
        difference=dollars(difference_minor),
        bank_amount_minor=bank_minor,
        ledger_amount_minor=ledger_minor,
        difference_minor=difference_minor,
        confidence=confidence,
        score=score,
        evidence=evidence,
        ambiguities=list(ambiguities or []),
        fee_evidence_ids=list(fee_ids or []),
        provider=provider,
        provider_payout_id=provider_payout_id,
        provider_status=provider_status,
        proposed_adjusting_entries=list(proposed or []),
    )


def _date_ok(left: str, right: str, window: int) -> bool:
    delta = date_diff_days(left, right)
    return delta is not None and delta <= window


def _group_fits_bank(txn: BankTransaction, combo: tuple[LedgerEntry, ...] | list[LedgerEntry]) -> bool:
    """Grouped matches must be one vendor and share a real token with the bank."""
    vendors = {item.counterparty.lower() for item in combo if item.counterparty}
    if len(vendors) > 1:
        return False
    if not txn.counterparty:
        return True
    if any(counterparties_compatible(txn.counterparty, item.counterparty) for item in combo):
        return True
    vendor_tokens: set[str] = set()
    for item in combo:
        vendor_tokens.update(tokens(item.counterparty))
    return bool(tokens(txn.counterparty) & vendor_tokens)


def _same_sign(left: int, right: int) -> bool:
    if left == 0 or right == 0:
        return False
    return (left > 0) == (right > 0)


def exact_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    *,
    window: int = EXACT_DATE_WINDOW,
) -> list[MatchCandidate]:
    rows: list[MatchCandidate] = []
    for txn in bank:
        for entry in ledger:
            if txn.amount_minor != entry.amount_minor:
                continue
            if not _same_sign(txn.amount_minor, entry.amount_minor):
                continue
            if not _date_ok(txn.date, entry.date, window):
                continue
            party_score = overlap_score(combined_text(txn), combined_text(entry))
            compatible = counterparties_compatible(txn.counterparty, entry.counterparty)
            if txn.counterparty and entry.counterparty and not compatible and party_score < 0.2:
                continue
            reference_hit = bool(txn.reference and txn.reference.lower() in combined_text(entry).lower())
            invoice_hit = bool(entry.reference and entry.reference.lower() in combined_text(txn).lower())
            score = 1.0
            score += 0.25 if party_score else 0.0
            score += party_score
            score += 0.4 if reference_hit or invoice_hit else 0.0
            delta = date_diff_days(txn.date, entry.date) or 0
            score += max(0.0, (window - delta) / max(window, 1) * 0.2)
            evidence = [
                f"amount:{txn.amount_minor}",
                f"bank_date:{txn.date}",
                f"ledger_date:{entry.date}",
                f"counterparty_overlap:{party_score:.2f}",
            ]
            if reference_hit:
                evidence.append(f"bank_reference:{txn.reference}")
            if invoice_hit:
                evidence.append(f"ledger_reference:{entry.reference}")
            if not compatible and txn.counterparty and entry.counterparty:
                evidence.append("counterparty_mismatch")
            confidence = 1.0 if compatible and txn.amount_minor == entry.amount_minor else 0.7
            rows.append(
                _candidate(
                    "EXACT_MATCH",
                    [txn],
                    [entry],
                    evidence=evidence,
                    score=score,
                    confidence=confidence,
                    ambiguities=["counterparty_mismatch"] if (txn.counterparty and entry.counterparty and not compatible) else [],
                )
            )
    return rows


def grouped_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
) -> list[MatchCandidate]:
    rows: list[MatchCandidate] = []
    for txn in bank:
        pool = [
            entry
            for entry in ledger
            if _same_sign(txn.amount_minor, entry.amount_minor)
            and abs(entry.amount_minor) < abs(txn.amount_minor)
            and _date_ok(txn.date, entry.date, GROUP_DATE_WINDOW)
        ]
        preferred = [
            entry
            for entry in pool
            if txn.counterparty and counterparties_compatible(txn.counterparty, entry.counterparty)
        ]
        if preferred:
            pool = preferred
        pool.sort(key=lambda item: (date_gap(txn.date, item.date), abs(item.amount_minor)))
        pool = pool[:MAX_GROUP_POOL]
        if len(pool) < 2:
            continue
        max_size = min(MAX_GROUP_SIZE, len(pool))
        exact_found = False
        for size in range(2, max_size + 1):
            for combo in combinations(pool, size):
                total = sum(item.amount_minor for item in combo)
                if total != txn.amount_minor:
                    continue
                if not _group_fits_bank(txn, combo):
                    continue
                exact_found = True
                vendors = {item.counterparty.lower() for item in combo if item.counterparty}
                same_vendor = len(vendors) == 1
                evidence = [
                    f"group_sum:{total}",
                    f"bank_amount:{txn.amount_minor}",
                    f"members:{','.join(item.entry_id for item in combo)}",
                    f"same_vendor:{same_vendor}",
                ]
                score = 2.0 + (0.5 if same_vendor else 0.0) + size * 0.05
                rows.append(
                    _candidate(
                        "GROUPED_MATCH",
                        [txn],
                        list(combo),
                        evidence=evidence,
                        score=score,
                        confidence=1.0 if same_vendor else 0.85,
                    )
                )
        vendor_group = preferred if len(preferred) >= 2 else []
        if vendor_group and not exact_found:
            total = sum(item.amount_minor for item in vendor_group)
            residual = txn.amount_minor - total
            residual_limit = max(NEAR_AMOUNT_WINDOW, int(abs(txn.amount_minor) * 0.05))
            if residual != 0 and abs(residual) <= residual_limit * 4:
                rows.append(
                    _candidate(
                        "UNEXPLAINED_DIFFERENCE",
                        [txn],
                        list(vendor_group),
                        evidence=[
                            f"group_sum:{total}",
                            f"bank_amount:{txn.amount_minor}",
                            f"residual:{residual}",
                            f"unexplained_group_difference:{dollars(residual)}",
                            f"members:{','.join(item.entry_id for item in vendor_group)}",
                        ],
                        score=1.3,
                        confidence=0.75,
                        ambiguities=[f"Grouped ACH residual {dollars(residual)} is unexplained"],
                    )
                )
    return rows


def fee_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
) -> list[MatchCandidate]:
    rows: list[MatchCandidate] = []
    for txn in bank:
        for entry in ledger:
            if not _same_sign(txn.amount_minor, entry.amount_minor):
                continue
            if not _date_ok(txn.date, entry.date, FEE_DATE_WINDOW):
                continue
            difference = txn.amount_minor - entry.amount_minor
            if difference == 0:
                continue
            fee_minor = abs(difference)
            matches = [
                fee
                for fee in fees
                if fee.amount_minor == fee_minor
                and _date_ok(txn.date, fee.date, FEE_DATE_WINDOW)
                and (
                    not fee.reference
                    or fee.reference.lower() in combined_text(txn).lower()
                    or (entry.reference and fee.reference.lower() in entry.reference.lower())
                )
            ]
            if not matches:
                continue
            if txn.counterparty and entry.counterparty and not counterparties_compatible(txn.counterparty, entry.counterparty):
                if overlap_score(combined_text(txn), combined_text(entry)) < 0.15 and not (
                    txn.reference and txn.reference.lower() in combined_text(entry).lower()
                ):
                    continue
            fee = matches[0]
            cash_side = "credit" if txn.amount_minor < 0 else "debit"
            expense_side = "debit" if cash_side == "credit" else "credit"
            proposed = ProposedJournalEntry(
                memo=f"Record bank fee {fee.evidence_id} on {txn.transaction_id}",
                related_bank_ids=[txn.transaction_id],
                related_ledger_ids=[entry.entry_id],
                support=fee.evidence_id,
                posted=False,
                lines=[
                    ProposedJournalLine(
                        account=BANK_FEE_ACCOUNT,
                        amount=dollars(fee_minor),
                        amount_minor=fee_minor,
                        side=expense_side,  # type: ignore[arg-type]
                    ),
                    ProposedJournalLine(
                        account=CASH_ACCOUNT,
                        amount=dollars(fee_minor),
                        amount_minor=fee_minor,
                        side=cash_side,  # type: ignore[arg-type]
                    ),
                ],
            )
            evidence = [
                f"principal:{entry.amount_minor}",
                f"bank_total:{txn.amount_minor}",
                f"fee:{fee.amount_minor}",
                f"fee_evidence:{fee.evidence_id}",
                f"reference:{fee.reference or txn.reference}",
            ]
            rows.append(
                _candidate(
                    "FEE_NETTED",
                    [txn],
                    [entry],
                    evidence=evidence,
                    score=1.6,
                    confidence=0.95,
                    fee_ids=[fee.evidence_id],
                    proposed=[proposed],
                )
            )
    return rows


def timing_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    period: str,
) -> list[MatchCandidate]:
    rows: list[MatchCandidate] = []
    in_period_bank = [item for item in bank if item.period == period]
    in_period_ledger = [item for item in ledger if item.period == period]
    adjacent_bank = [item for item in bank if item.period != period and adjacent_period(item.period, period)]
    adjacent_ledger = [item for item in ledger if item.period != period and adjacent_period(item.period, period)]
    pairs = [(in_period_ledger, adjacent_bank), (adjacent_ledger, in_period_bank)]
    for books, statements in pairs:
        for entry in books:
            for txn in statements:
                if txn.amount_minor != entry.amount_minor:
                    continue
                if not _same_sign(txn.amount_minor, entry.amount_minor):
                    continue
                if not _date_ok(txn.date, entry.date, TIMING_DATE_WINDOW):
                    continue
                if entry.counterparty and txn.counterparty and not counterparties_compatible(txn.counterparty, entry.counterparty):
                    if overlap_score(combined_text(txn), combined_text(entry)) < 0.2:
                        continue
                evidence = [
                    f"ledger_period:{entry.period}",
                    f"bank_period:{txn.period}",
                    f"amount:{txn.amount_minor}",
                    f"ledger_date:{entry.date}",
                    f"bank_date:{txn.date}",
                ]
                rows.append(
                    _candidate(
                        "TIMING_DIFFERENCE",
                        [txn],
                        [entry],
                        evidence=evidence,
                        score=1.4,
                        confidence=0.9,
                    )
                )
    return rows


def near_amount_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
) -> list[MatchCandidate]:
    rows: list[MatchCandidate] = []
    for txn in bank:
        for entry in ledger:
            if not _same_sign(txn.amount_minor, entry.amount_minor):
                continue
            if not _date_ok(txn.date, entry.date, EXACT_DATE_WINDOW):
                continue
            difference = txn.amount_minor - entry.amount_minor
            if difference == 0:
                continue
            if abs(difference) > NEAR_AMOUNT_WINDOW:
                continue
            if txn.counterparty and entry.counterparty and not counterparties_compatible(txn.counterparty, entry.counterparty):
                if overlap_score(combined_text(txn), combined_text(entry)) < 0.25:
                    continue
            fee_hits = [fee for fee in fees if fee.amount_minor == abs(difference)]
            hypotheses = ["fee", "rounding", "foreign_exchange", "partial_payment", "duplicate_or_missing", "timing_difference"]
            unsupported = list(hypotheses)
            evidence = [
                f"bank_amount:{txn.amount_minor}",
                f"ledger_amount:{entry.amount_minor}",
                f"difference:{difference}",
            ]
            if abs(difference) != 1:
                unsupported = [item for item in unsupported if item != "rounding"]
                evidence.append("rounding_rejected:difference_not_one_cent")
            if not fee_hits:
                unsupported = [item for item in unsupported if item != "fee"]
                evidence.append("fee_rejected:no_fee_evidence")
            evidence.append("no_fx_evidence")
            evidence.append("no_partial_payment_remittance")
            rows.append(
                _candidate(
                    "UNEXPLAINED_DIFFERENCE",
                    [txn],
                    [entry],
                    evidence=evidence,
                    score=0.4,
                    confidence=0.2,
                    ambiguities=unsupported,
                )
            )
    return rows


def unmatched_bank_candidate(txn: BankTransaction) -> MatchCandidate:
    return _candidate(
        "UNMATCHED_BANK",
        [txn],
        [],
        evidence=[f"bank:{txn.transaction_id}", f"amount:{txn.amount_minor}", f"description:{txn.description}"],
        score=0.0,
        confidence=0.0,
    )


def unmatched_ledger_candidate(entry: LedgerEntry) -> MatchCandidate:
    return _candidate(
        "UNMATCHED_LEDGER",
        [],
        [entry],
        evidence=[f"ledger:{entry.entry_id}", f"amount:{entry.amount_minor}", f"description:{entry.description}"],
        score=0.0,
        confidence=0.0,
    )


def duplicate_bank_groups(bank: list[BankTransaction]) -> list[list[BankTransaction]]:
    groups: list[list[BankTransaction]] = []
    used: set[str] = set()
    ordered = sorted(bank, key=lambda item: (item.date, item.transaction_id))
    for index, txn in enumerate(ordered):
        if txn.transaction_id in used:
            continue
        cluster = [txn]
        for other in ordered[index + 1 :]:
            if other.transaction_id in used:
                continue
            if other.amount_minor != txn.amount_minor:
                continue
            if not _date_ok(txn.date, other.date, DUPLICATE_DATE_WINDOW):
                continue
            if overlap_score(combined_text(txn), combined_text(other)) < 0.5 and txn.reference != other.reference:
                continue
            cluster.append(other)
        if len(cluster) >= 2:
            for item in cluster:
                used.add(item.transaction_id)
            groups.append(cluster)
    return groups


def duplicate_ledger_groups(ledger: list[LedgerEntry]) -> list[list[LedgerEntry]]:
    groups: list[list[LedgerEntry]] = []
    used: set[str] = set()
    ordered = sorted(ledger, key=lambda item: (item.date, item.entry_id))
    for index, entry in enumerate(ordered):
        if entry.entry_id in used:
            continue
        cluster = [entry]
        for other in ordered[index + 1 :]:
            if other.entry_id in used:
                continue
            if other.amount_minor != entry.amount_minor:
                continue
            if not _date_ok(entry.date, other.date, DUPLICATE_DATE_WINDOW):
                continue
            same_party = counterparties_compatible(entry.counterparty, other.counterparty)
            same_ref = bool(entry.reference and entry.reference == other.reference)
            if not same_party and not same_ref:
                continue
            cluster.append(other)
        if len(cluster) >= 2:
            for item in cluster:
                used.add(item.entry_id)
            groups.append(cluster)
    return groups


def duplicate_bank_candidate(txn: BankTransaction, matched: BankTransaction, ledger: list[LedgerEntry]) -> MatchCandidate:
    refund = looks_like_refund(txn) or any(looks_like_refund(item) for item in ledger)
    match_type = "POSSIBLE_DUPLICATE_REFUND" if refund else "POSSIBLE_DUPLICATE_BANK_TXN"
    evidence = [
        f"amount:{txn.amount_minor}",
        f"customer:{txn.counterparty}",
        f"reference:{txn.reference}",
        f"timing:{txn.date}",
        f"peer:{matched.transaction_id}",
    ]
    if ledger:
        evidence.append(f"ledger_reference:{ledger[0].reference}")
    return _candidate(
        match_type,
        [txn],
        [],
        evidence=evidence,
        score=0.1,
        confidence=0.3,
    )


def duplicate_ledger_candidate(entry: LedgerEntry, matched: LedgerEntry, bank: list[BankTransaction]) -> MatchCandidate:
    evidence = [
        f"amount:{entry.amount_minor}",
        f"counterparty:{entry.counterparty}",
        f"reference:{entry.reference}",
        f"timing:{entry.date}",
        f"peer:{matched.entry_id}",
    ]
    if bank:
        evidence.append(f"bank:{bank[0].transaction_id}")
    return _candidate(
        "POSSIBLE_DUPLICATE_LEDGER_ENTRY",
        [],
        [entry],
        evidence=evidence,
        score=0.1,
        confidence=0.3,
    )


def fee_journal_amount(entry: ProposedJournalEntry) -> int:
    return cents(entry.lines[0].amount) if entry.lines else 0
