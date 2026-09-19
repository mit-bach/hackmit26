"""Load dedicated audit fixtures and persist audit runs. Does not edit finance books."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from audit.models import (
    AccountingPeriod,
    AuditApproval,
    AuditInvoice,
    AuditJournalEntry,
    AuditPayment,
    AuditRun,
    AuditVendor,
    OperationalDecision,
    PlantedReconciliation,
)
from audit.policy import AuditPolicy, policy_from_raw
from cash_recon.mathutil import cents, period_of
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "audit"
RUNS_DIR = ROOT / "runs" / "audit"


def configure_paths(*, data_dir: Path | None = None, runs_dir: Path | None = None) -> None:
    global DATA_DIR, RUNS_DIR
    if data_dir is not None:
        DATA_DIR = Path(data_dir)
    if runs_dir is not None:
        RUNS_DIR = Path(runs_dir)


@contextmanager
def isolated_audit(directory: Path):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    previous = (DATA_DIR, RUNS_DIR)
    configure_paths(runs_dir=directory / "runs")
    try:
        yield
    finally:
        DATA_DIR, RUNS_DIR = previous


def _read(name: str, default):
    path = DATA_DIR / name
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _read_list(name: str) -> list:
    raw = _read(name, [])
    if not isinstance(raw, list):
        raise ValueError(f"{name} must contain a JSON array")
    return raw


def load_policy() -> AuditPolicy:
    return policy_from_raw(_read("policy.json", {}))


def load_period(period: str) -> AccountingPeriod:
    rows = [AccountingPeriod.model_validate(item) for item in _read_list("periods.json")]
    for item in rows:
        if item.period == period:
            return item
    return AccountingPeriod(period=period, status="OPEN")


def load_vendors() -> list[AuditVendor]:
    return [AuditVendor.model_validate(item) for item in _read_list("vendors.json")]


def load_invoices() -> list[AuditInvoice]:
    return [AuditInvoice.model_validate(item) for item in _read_list("invoices.json")]


def load_payments() -> list[AuditPayment]:
    return [AuditPayment.model_validate(item) for item in _read_list("payments.json")]


def load_journals() -> list[AuditJournalEntry]:
    return [AuditJournalEntry.model_validate(item) for item in _read_list("journal_entries.json")]


def load_approvals() -> list[AuditApproval]:
    return [AuditApproval.model_validate(item) for item in _read_list("approvals.json")]


def load_operational_decisions() -> list[OperationalDecision]:
    return [OperationalDecision.model_validate(item) for item in _read_list("operational_decisions.json")]


def load_planted_reconciliations() -> list[PlantedReconciliation]:
    return [PlantedReconciliation.model_validate(item) for item in _read_list("reconciliations.json")]


def load_ground_truth() -> dict:
    raw = _read("ground_truth.json", {})
    return raw if isinstance(raw, dict) else {}


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


def load_recon_source() -> tuple[list[BankTransaction], list[LedgerEntry], list[FeeEvidence]]:
    bank = [_fill_bank(row) for row in _read_list("bank.json")]
    ledger = [_fill_ledger(row) for row in _read_list("ledger.json")]
    fees = [FeeEvidence.model_validate(row) for row in _read_list("fee_evidence.json")]
    for fee in fees:
        if not fee.amount_minor:
            fee.amount_minor = cents(fee.amount)
    return bank, ledger, fees


def save_run(run: AuditRun) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{run.period}-{run.audit_run_id}.json"
    path.write_text(run.model_dump_json(indent=2) + "\n")
    run.trace_path = str(path)
    path.write_text(run.model_dump_json(indent=2) + "\n")
    return path
