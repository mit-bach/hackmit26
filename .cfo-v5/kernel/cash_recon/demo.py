"""Load the seeded one-month bank/ledger demo. Does not post to AP or Stripe."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry, PeriodBalances

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "data" / "cash_recon"
ROOT = _DEFAULT_ROOT


def configure_root(directory: Path | None = None) -> Path:
    """Point the cash-recon demo loader at an alternate fixture directory."""
    global ROOT
    ROOT = Path(directory) if directory is not None else _DEFAULT_ROOT
    return ROOT


def _read(name: str):
    path = ROOT / name
    from evaluation.isolation import assert_operational_read_allowed

    assert_operational_read_allowed(path)
    return json.loads(path.read_text())


def _fill_bank(row: dict) -> BankTransaction:
    item = BankTransaction.model_validate(row)
    if not item.period:
        item.period = period_of(item.date)
    if not item.amount_minor:
        item.amount_minor = cents(item.amount)
    return item


def _fill_ledger(row: dict) -> LedgerEntry:
    item = LedgerEntry.model_validate(row)
    if not item.period:
        item.period = period_of(item.date)
    if not item.amount_minor:
        item.amount_minor = cents(item.amount)
    return item


def _fill_fee(row: dict) -> FeeEvidence:
    item = FeeEvidence.model_validate(row)
    if not item.amount_minor:
        item.amount_minor = cents(item.amount)
    return item


def load_demo_dataset() -> tuple[PeriodBalances, list[BankTransaction], list[LedgerEntry], list[FeeEvidence]]:
    raw = _read("balances.json")
    balances = PeriodBalances.model_validate(raw)
    balances.opening_bank_minor = cents(balances.opening_bank)
    balances.opening_ledger_minor = cents(balances.opening_ledger)
    bank = [_fill_bank(row) for row in _read("bank_statement.json")]
    ledger = [_fill_ledger(row) for row in _read("ledger.json")]
    fees = [_fill_fee(row) for row in _read("fee_evidence.json")]
    return balances, bank, ledger, fees


def load_ground_truth() -> dict:
    from evaluation.isolation import operational_phase

    if operational_phase():
        return {}
    return _read("ground_truth.json")


def seed_provider_payouts() -> None:
    """Replay existing Stripe/Adyen adapters so monthly recon can delegate.

    Presence of some other Stripe payout (for example an August memory fixture)
    must not skip the September demo payouts the bank statement expects.
    """
    from integrations.demo import process_provider
    from integrations.store import get_payout

    if get_payout("po_1HackMIT97420") is None:
        process_provider("stripe")
    try:
        if get_payout("3JZKT2B4N7Q1P8R5S6T0") is None:
            process_provider("adyen")
    except FileNotFoundError:
        pass
