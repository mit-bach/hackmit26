"""Deterministic month-of-activity matching. Authoritative for selection math."""

from __future__ import annotations

from collections import defaultdict

from cash_recon.candidates import (
    duplicate_bank_candidate,
    duplicate_bank_groups,
    duplicate_ledger_candidate,
    duplicate_ledger_groups,
    exact_candidates,
    fee_candidates,
    grouped_candidates,
    near_amount_candidates,
    timing_candidates,
    unmatched_bank_candidate,
    unmatched_ledger_candidate,
)
from cash_recon.mathutil import date_gap
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry, MatchCandidate
from cash_recon.normalize import prepare_bank, prepare_ledger
from cash_recon.providers import provider_candidates

PRIORITY = {
    "PROVIDER_PAYOUT": 0,
    "GROUPED_MATCH": 1,
    "FEE_NETTED": 2,
    "EXACT_MATCH": 3,
    "TIMING_DIFFERENCE": 4,
    "UNEXPLAINED_DIFFERENCE": 5,
    "POSSIBLE_DUPLICATE_REFUND": 6,
    "POSSIBLE_DUPLICATE_BANK_TXN": 7,
    "POSSIBLE_DUPLICATE_LEDGER_ENTRY": 8,
    "UNMATCHED_BANK": 9,
    "UNMATCHED_LEDGER": 10,
}


def _unique_best(rows: list[MatchCandidate], *, margin: float = 0.15) -> MatchCandidate | None:
    if not rows:
        return None
    ordered = sorted(rows, key=lambda item: (-item.score, item.candidate_id))
    best = ordered[0]
    if len(ordered) > 1 and abs(ordered[1].score - best.score) < margin:
        if set(ordered[1].ledger_entry_ids) != set(best.ledger_entry_ids) or set(ordered[1].bank_transaction_ids) != set(
            best.bank_transaction_ids
        ):
            return None
    return best


def _consume(candidate: MatchCandidate, used_bank: set[str], used_ledger: set[str]) -> None:
    used_bank.update(candidate.bank_transaction_ids)
    used_ledger.update(candidate.ledger_entry_ids)


def _available_bank(rows: list[BankTransaction], used: set[str]) -> list[BankTransaction]:
    return [item for item in rows if item.transaction_id not in used]


def _available_ledger(rows: list[LedgerEntry], used: set[str]) -> list[LedgerEntry]:
    return [item for item in rows if item.entry_id not in used]


def _by_bank(rows: list[MatchCandidate]) -> dict[str, list[MatchCandidate]]:
    grouped: dict[str, list[MatchCandidate]] = defaultdict(list)
    for row in rows:
        if len(row.bank_transaction_ids) != 1:
            continue
        grouped[row.bank_transaction_ids[0]].append(row)
    return grouped


def generate_all_candidates(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
    period: str,
) -> list[MatchCandidate]:
    """All legally computable candidates. Used for traces even after assignment."""
    bank = prepare_bank(bank)
    ledger = prepare_ledger(ledger)
    rows: list[MatchCandidate] = []
    rows.extend(provider_candidates(bank, ledger))
    rows.extend(exact_candidates(bank, ledger))
    rows.extend(grouped_candidates(bank, ledger))
    rows.extend(fee_candidates(bank, ledger, fees))
    rows.extend(timing_candidates(bank, ledger, period))
    rows.extend(near_amount_candidates(bank, ledger, fees))
    return rows


def propose_matches(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
    period: str,
) -> list[MatchCandidate]:
    """Assign a disjoint set of candidates for the period. No LLM."""
    bank = prepare_bank(bank)
    ledger = prepare_ledger(ledger)
    used_bank: set[str] = set()
    used_ledger: set[str] = set()
    selected: list[MatchCandidate] = []

    for candidate in provider_candidates(bank, ledger):
        if any(item in used_bank for item in candidate.bank_transaction_ids):
            continue
        if any(item in used_ledger for item in candidate.ledger_entry_ids):
            continue
        selected.append(candidate)
        _consume(candidate, used_bank, used_ledger)

    period_bank = [item for item in bank if item.period == period]
    period_ledger = [item for item in ledger if item.period == period]
    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)

    for cluster in duplicate_bank_groups(open_bank):
        counterparts = [
            entry
            for entry in open_ledger
            if entry.amount_minor == cluster[0].amount_minor
            and date_gap(cluster[0].date, entry.date) <= 3
        ]
        counterparts.sort(key=lambda item: item.entry_id)
        take = min(len(counterparts), 1)
        if take:
            legit_bank = cluster[0]
            legit_ledger = counterparts[0]
            exact = exact_candidates([legit_bank], [legit_ledger])
            chosen = exact[0] if exact else None
            if chosen is None:
                continue
            selected.append(chosen)
            _consume(chosen, used_bank, used_ledger)
            for extra in cluster[1:]:
                flagged = duplicate_bank_candidate(extra, legit_bank, [legit_ledger])
                selected.append(flagged)
                _consume(flagged, used_bank, used_ledger)
        else:
            for extra in cluster:
                flagged = duplicate_bank_candidate(extra, cluster[0], [])
                selected.append(flagged)
                _consume(flagged, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    for cluster in duplicate_ledger_groups(open_ledger):
        counterparts = [
            txn
            for txn in open_bank
            if txn.amount_minor == cluster[0].amount_minor
        ]
        counterparts.sort(key=lambda item: item.transaction_id)
        if not counterparts:
            continue
        legit_ledger = cluster[0]
        extra_entries = cluster[1:]
        exact = exact_candidates([counterparts[0]], [legit_ledger])
        if not exact:
            continue
        selected.append(exact[0])
        _consume(exact[0], used_bank, used_ledger)
        for extra in extra_entries:
            flagged = duplicate_ledger_candidate(extra, legit_ledger, [counterparts[0]])
            selected.append(flagged)
            _consume(flagged, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    grouped = grouped_candidates(open_bank, open_ledger)
    by_txn = _by_bank(grouped)
    for txn in sorted(open_bank, key=lambda item: item.transaction_id):
        best = _unique_best(by_txn.get(txn.transaction_id, []))
        if best is None:
            continue
        if any(item in used_ledger for item in best.ledger_entry_ids):
            continue
        selected.append(best)
        _consume(best, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    fees_found = fee_candidates(open_bank, open_ledger, fees)
    by_txn = _by_bank(fees_found)
    for txn in sorted(open_bank, key=lambda item: item.transaction_id):
        best = _unique_best(by_txn.get(txn.transaction_id, []))
        if best is None:
            continue
        if any(item in used_ledger for item in best.ledger_entry_ids):
            continue
        selected.append(best)
        _consume(best, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    exact = exact_candidates(open_bank, open_ledger)
    bank_map = _by_bank(exact)
    ledger_hits: dict[str, list[MatchCandidate]] = defaultdict(list)
    for row in exact:
        if len(row.ledger_entry_ids) == 1:
            ledger_hits[row.ledger_entry_ids[0]].append(row)
    for txn in sorted(open_bank, key=lambda item: item.transaction_id):
        options = [row for row in bank_map.get(txn.transaction_id, []) if row.ledger_entry_ids[0] not in used_ledger]
        unique_ledgers = {tuple(row.ledger_entry_ids) for row in options}
        if len(unique_ledgers) != 1:
            continue
        best = _unique_best(options)
        if best is None:
            continue
        ledger_id = best.ledger_entry_ids[0]
        competing = [row for row in ledger_hits.get(ledger_id, []) if row.bank_transaction_ids[0] not in used_bank]
        if len({row.bank_transaction_ids[0] for row in competing}) > 1:
            continue
        if best.ambiguities:
            continue
        selected.append(best)
        _consume(best, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    timing = timing_candidates(bank, ledger, period)
    for candidate in sorted(timing, key=lambda item: item.candidate_id):
        if any(item in used_bank for item in candidate.bank_transaction_ids):
            continue
        if any(item in used_ledger for item in candidate.ledger_entry_ids):
            continue
        in_period_bank = [item for item in candidate.bank_transaction_ids if any(txn.transaction_id == item and txn.period == period for txn in bank)]
        in_period_ledger = [item for item in candidate.ledger_entry_ids if any(entry.entry_id == item and entry.period == period for entry in ledger)]
        if not in_period_bank and not in_period_ledger:
            continue
        selected.append(candidate)
        _consume(candidate, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    near = near_amount_candidates(open_bank, open_ledger, fees)
    by_txn = _by_bank(near)
    for txn in sorted(open_bank, key=lambda item: item.transaction_id):
        options = [row for row in by_txn.get(txn.transaction_id, []) if not any(item in used_ledger for item in row.ledger_entry_ids)]
        best = _unique_best(options, margin=0.05)
        if best is None:
            continue
        selected.append(best)
        _consume(best, used_bank, used_ledger)

    open_bank = _available_bank(period_bank, used_bank)
    open_ledger = _available_ledger(period_ledger, used_ledger)
    for txn in sorted(open_bank, key=lambda item: item.transaction_id):
        selected.append(unmatched_bank_candidate(txn))
        used_bank.add(txn.transaction_id)
    for entry in sorted(open_ledger, key=lambda item: item.entry_id):
        selected.append(unmatched_ledger_candidate(entry))
        used_ledger.add(entry.entry_id)

    selected.sort(key=lambda item: (PRIORITY.get(item.match_type, 99), item.candidate_id))
    return selected
