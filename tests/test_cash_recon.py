from __future__ import annotations

from cash_recon.demo import load_demo_dataset, seed_provider_payouts
from cash_recon.engine import propose_matches
from cash_recon.mathutil import cents
from cash_recon.models import BANK_FEE_ACCOUNT, BankTransaction, FeeEvidence, LedgerEntry, PeriodBalances
from cash_recon.normalize import prepare_bank, prepare_ledger
from cash_recon.store import matches_for_period, traces_for_period
from cash_recon.validate import compute_tie_out, period_status
from cash_recon.workflow import run_cash_reconciliation


def _bank(**kwargs) -> BankTransaction:
    item = BankTransaction.model_validate(kwargs)
    return prepare_bank([item])[0]


def _ledger(**kwargs) -> LedgerEntry:
    item = LedgerEntry.model_validate(kwargs)
    return prepare_ledger([item])[0]


def _fee(**kwargs) -> FeeEvidence:
    item = FeeEvidence.model_validate(kwargs)
    if not item.amount_minor:
        item.amount_minor = cents(item.amount)
    return item


def _balances(opening: float = 0.0) -> PeriodBalances:
    minor = cents(opening)
    return PeriodBalances(
        opening_bank=opening,
        opening_ledger=opening,
        as_of_date="2026-09-30",
        opening_bank_minor=minor,
        opening_ledger_minor=minor,
    )


def _by_type(matches) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for item in matches:
        grouped.setdefault(item.match_type, []).append(item)
    return grouped


def test_exact_match_same_amount_compatible_date():
    bank = [_bank(transaction_id="B1", date="2026-09-04", amount=-4250, description="ACH OUT ACME INDUSTRIAL 8391", counterparty="ACME INDUSTRIAL", period="2026-09")]
    ledger = [_ledger(entry_id="L1", date="2026-09-04", amount=-4250, counterparty="Acme Industrial", reference="INV-1042", period="2026-09")]
    proposed = propose_matches(bank, ledger, [], "2026-09")
    exact = [item for item in proposed if item.match_type == "EXACT_MATCH"]
    assert len(exact) == 1
    assert exact[0].bank_transaction_ids == ["B1"]
    assert exact[0].ledger_entry_ids == ["L1"]
    assert exact[0].difference_minor == 0
    assert exact[0].confidence == 1.0
    report = run_cash_reconciliation("2026-09", balances=_balances(10000), bank=bank, ledger=ledger, fees=[], reset=True)
    match = next(item for item in report.matches if item.match_type == "EXACT_MATCH")
    assert match.status == "MATCHED"
    assert match.human_review is False


def test_grouped_payment_three_invoices():
    bank = [_bank(transaction_id="B2", date="2026-09-08", amount=-18500, description="ACH OUT NORTHLINE FAB", counterparty="NORTHLINE FAB", period="2026-09")]
    ledger = [
        _ledger(entry_id="INV-201", date="2026-09-07", amount=-5000, counterparty="Northline Fabrication", period="2026-09"),
        _ledger(entry_id="INV-202", date="2026-09-07", amount=-7500, counterparty="Northline Fabrication", period="2026-09"),
        _ledger(entry_id="INV-203", date="2026-09-08", amount=-6000, counterparty="Northline Fabrication", period="2026-09"),
    ]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    grouped = [item for item in report.matches if item.match_type == "GROUPED_MATCH"]
    assert len(grouped) == 1
    assert grouped[0].status == "MATCHED"
    assert set(grouped[0].ledger_entry_ids) == {"INV-201", "INV-202", "INV-203"}
    assert grouped[0].bank_amount_minor == grouped[0].ledger_amount_minor
    assert not any(item.match_type == "UNMATCHED_LEDGER" for item in report.matches)


def test_wire_net_of_bank_fee():
    bank = [_bank(transaction_id="B3", date="2026-09-11", amount=-10025, description="WIRE TRANSFER INTL REF 729103", reference="729103", period="2026-09")]
    ledger = [_ledger(entry_id="L3", date="2026-09-11", amount=-10000, counterparty="Helios Hardware", reference="WIRE-729103", period="2026-09")]
    fees = [_fee(evidence_id="ADV-729103", date="2026-09-11", amount=25, reference="729103", description="Correspondent bank fee")]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=fees, reset=True)
    fee = next(item for item in report.matches if item.match_type == "FEE_NETTED")
    assert fee.status == "EXPLAINED_EXCEPTION"
    assert fee.difference_minor == cents(-25)
    assert fee.proposed_adjusting_entries
    assert fee.proposed_adjusting_entries[0].posted is False
    accounts = {line.account for line in fee.proposed_adjusting_entries[0].lines}
    assert BANK_FEE_ACCOUNT in accounts or "6100-Bank-Fees" in accounts


def test_duplicate_refund_one_matched_second_flagged():
    bank = [
        _bank(transaction_id="B4A", date="2026-09-12", amount=-250, description="REFUND CARD 8892", reference="8892", counterparty="LUMEN LABS", transaction_type="card_refund", period="2026-09"),
        _bank(transaction_id="B4B", date="2026-09-12", amount=-250, description="REFUND CARD 8892", reference="8892", counterparty="LUMEN LABS", transaction_type="card_refund", period="2026-09"),
    ]
    ledger = [_ledger(entry_id="REF-772", date="2026-09-12", amount=-250, counterparty="Lumen Labs", reference="REF-772", entry_type="refund", period="2026-09")]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    matched = [item for item in report.matches if item.status == "MATCHED"]
    flagged = [item for item in report.matches if item.match_type == "POSSIBLE_DUPLICATE_REFUND"]
    assert len(matched) == 1
    assert matched[0].ledger_entry_ids == ["REF-772"]
    assert len(flagged) == 1
    assert flagged[0].status == "HUMAN_REVIEW"
    assert "POSSIBLE_DUPLICATE_REFUND" in flagged[0].control_findings
    evidence = " ".join(flagged[0].evidence)
    assert "25000" in evidence or "amount:" in evidence
    assert "8892" in evidence or "LUMEN" in evidence.upper() or "Lumen" in evidence


def test_unexplained_difference_12_40_goes_to_human_review():
    bank = [_bank(transaction_id="B5", date="2026-09-15", amount=12412.40, description="CUSTOMER PAYMENT NORTHSTAR LLC", counterparty="NORTHSTAR LLC", period="2026-09")]
    ledger = [_ledger(entry_id="L5", date="2026-09-15", amount=12400, counterparty="Northstar LLC", reference="INV-AR-880", period="2026-09")]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    item = next(row for row in report.matches if row.match_type == "UNEXPLAINED_DIFFERENCE")
    assert item.difference == 12.4
    assert item.difference_minor == 1240
    assert item.status == "HUMAN_REVIEW"
    assert "Unexplained difference: $12.40" in item.explanation
    assert item.human_review is True
    note = next(trace.investigation for trace in report.traces if trace.final.reconciliation_id == item.reconciliation_id)
    assert note is not None
    assert any("no evidence" in finding.lower() or "cannot" in finding.lower() or "unexplained" in finding.lower() for finding in note.findings)


def test_timing_difference_adjacent_period():
    bank = [_bank(transaction_id="B6", date="2026-10-01", amount=-3180, description="ACH OUT HARBOR ELECTRIC", counterparty="HARBOR ELECTRIC", period="2026-10")]
    ledger = [_ledger(entry_id="L6", date="2026-09-30", amount=-3180, counterparty="Harbor Electric", reference="INV-HE-330", period="2026-09")]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    timing = next(item for item in report.matches if item.match_type == "TIMING_DIFFERENCE")
    assert timing.status == "OUTSTANDING_TIMING_ITEM"
    assert timing.human_review is False
    assert "B6" in timing.bank_transaction_ids
    assert "L6" in timing.ledger_entry_ids


def test_duplicate_gl_posting():
    bank = [_bank(transaction_id="B7", date="2026-09-18", amount=-1200, description="ACH OUT OFFICE DEPOT #4410", counterparty="OFFICE DEPOT", period="2026-09")]
    ledger = [
        _ledger(entry_id="OD-1", date="2026-09-18", amount=-1200, counterparty="Office Depot", reference="INV-OD-4410", period="2026-09"),
        _ledger(entry_id="OD-2", date="2026-09-18", amount=-1200, counterparty="Office Depot", reference="INV-OD-4410", period="2026-09"),
    ]
    report = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    matched = [item for item in report.matches if item.status == "MATCHED"]
    flagged = [item for item in report.matches if item.match_type == "POSSIBLE_DUPLICATE_LEDGER_ENTRY"]
    assert len(matched) == 1
    assert len(matched[0].ledger_entry_ids) == 1
    assert len(flagged) == 1
    assert flagged[0].status == "HUMAN_REVIEW"
    assert flagged[0].ledger_entry_ids != matched[0].ledger_entry_ids


def test_stripe_and_adyen_delegate_to_existing_adapters():
    seed_provider_payouts()
    _, bank, ledger, fees = load_demo_dataset()
    stripe_bank = [item for item in bank if item.provider == "stripe" or "STRIPE" in item.description]
    adyen_bank = [item for item in bank if item.provider == "adyen" or "ADYEN" in item.description]
    stripe_ledger = [item for item in ledger if (item.raw_metadata or {}).get("provider") == "stripe"]
    adyen_ledger = [item for item in ledger if (item.raw_metadata or {}).get("provider") == "adyen"]
    report = run_cash_reconciliation(
        "2026-09",
        balances=_balances(500000),
        bank=stripe_bank + adyen_bank,
        ledger=stripe_ledger + adyen_ledger,
        fees=[],
        reset=True,
    )
    providers = {item.provider: item for item in report.matches if item.match_type == "PROVIDER_PAYOUT"}
    assert "stripe" in providers
    assert providers["stripe"].provider_payout_id == "po_1HackMIT97420"
    assert providers["stripe"].provider_status == "MATCH"
    assert providers["stripe"].status == "MATCHED"
    assert "adyen" in providers
    assert providers["adyen"].provider_payout_id == "3JZKT2B4N7Q1P8R5S6T0"
    assert providers["adyen"].provider_status == "MATCH"
    assert providers["adyen"].status == "MATCHED"


def test_arithmetic_integrity_cannot_close_if_untied():
    balances = _balances(100)
    bank = [_bank(transaction_id="BX", date="2026-09-01", amount=50, period="2026-09")]
    ledger = [_ledger(entry_id="LX", date="2026-09-01", amount=40, period="2026-09")]
    report = run_cash_reconciliation("2026-09", balances=balances, bank=bank, ledger=ledger, fees=[], reset=True)
    assert report.arithmetic_tied is True
    empty_tie = compute_tie_out(
        balances,
        bank,
        ledger,
        [],
        period="2026-09",
        bank={item.transaction_id: item for item in bank},
        ledger={item.entry_id: item for item in ledger},
    )
    assert empty_tie.tied is False
    assert period_status(empty_tie, []) == "FAILED_TIE"
    assert report.period_status != "RECONCILED"


def test_idempotent_second_run_does_not_duplicate():
    bank = [_bank(transaction_id="B1", date="2026-09-04", amount=-100, counterparty="Acme", period="2026-09")]
    ledger = [_ledger(entry_id="L1", date="2026-09-04", amount=-100, counterparty="Acme", period="2026-09")]
    first = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=True)
    n_matches = len(matches_for_period("2026-09"))
    n_traces = len(traces_for_period("2026-09"))
    second = run_cash_reconciliation("2026-09", balances=_balances(), bank=bank, ledger=ledger, fees=[], reset=False)
    assert second.replay is True
    assert [item.reconciliation_id for item in second.matches] == [item.reconciliation_id for item in first.matches]
    assert len(matches_for_period("2026-09")) == n_matches
    assert len(traces_for_period("2026-09")) == n_traces


def test_seeded_demo_covers_required_cases():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    by_type = _by_type(report.matches)
    assert report.arithmetic_tied is True
    assert report.period_status != "RECONCILED"
    assert by_type.get("EXACT_MATCH")
    grouped = by_type["GROUPED_MATCH"][0]
    assert len(grouped.ledger_entry_ids) == 3
    assert grouped.status == "MATCHED"
    fee = by_type["FEE_NETTED"][0]
    assert fee.status == "EXPLAINED_EXCEPTION"
    assert abs(fee.difference) == 25
    refund = by_type["POSSIBLE_DUPLICATE_REFUND"][0]
    assert refund.status == "HUMAN_REVIEW"
    unexplained = by_type["UNEXPLAINED_DIFFERENCE"][0]
    assert unexplained.difference_minor == 1240
    assert unexplained.status == "HUMAN_REVIEW"
    assert "Unexplained difference: $12.40" in unexplained.explanation
    timing = by_type["TIMING_DIFFERENCE"][0]
    assert timing.status == "OUTSTANDING_TIMING_ITEM"
    dup_gl = by_type["POSSIBLE_DUPLICATE_LEDGER_ENTRY"][0]
    assert dup_gl.status == "HUMAN_REVIEW"
    providers = {item.provider for item in by_type["PROVIDER_PAYOUT"]}
    assert providers == {"stripe", "adyen"}
    assert by_type.get("UNMATCHED_BANK")
    assert report.human_review_count >= 3
    assert report.metrics is not None
    assert report.metrics.false_matches == 0
    assert report.metrics.arithmetic_tied is True
    assert report.traces
    assert all(trace.validation is not None for trace in report.traces)
    assert all(trace.reviewer is not None for trace in report.traces)
    assert all(not entry.posted for match in report.matches for entry in match.proposed_adjusting_entries)
