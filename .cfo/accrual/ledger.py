from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from accrual.estimation import money
from accrual.models import JournalEntry, JournalLine, OpenAccrual, ReconciliationResult, TraceJournal
from accrual.store import LIABILITY_ACCOUNT, expense_account_for

LEDGER_DIR = Path(__file__).resolve().parent.parent / "runs" / "accruals"
ACCRUALS_PATH = LEDGER_DIR / "open_accruals.json"
JOURNALS_PATH = LEDGER_DIR / "journal_entries.json"


@contextmanager
def isolated_ledger(directory: Path):
    """Point ledger files at a temp directory so compare/eval cannot mutate the close books."""
    global LEDGER_DIR, ACCRUALS_PATH, JOURNALS_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    previous = (LEDGER_DIR, ACCRUALS_PATH, JOURNALS_PATH)
    LEDGER_DIR = directory
    ACCRUALS_PATH = directory / "open_accruals.json"
    JOURNALS_PATH = directory / "journal_entries.json"
    try:
        yield
    finally:
        LEDGER_DIR, ACCRUALS_PATH, JOURNALS_PATH = previous


def configure_paths(directory: Path) -> None:
    """Point open-accrual JSON at a Computer/runs tree."""
    global LEDGER_DIR, ACCRUALS_PATH, JOURNALS_PATH
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    LEDGER_DIR = directory
    ACCRUALS_PATH = directory / "open_accruals.json"
    JOURNALS_PATH = directory / "journal_entries.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return raw


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2) + "\n")


def load_accruals() -> list[OpenAccrual]:
    return [OpenAccrual.model_validate(item) for item in _read(ACCRUALS_PATH)]


def load_journal_entries() -> list[JournalEntry]:
    return [JournalEntry.model_validate(item) for item in _read(JOURNALS_PATH)]


def save_accruals(rows: list[OpenAccrual]) -> None:
    _write(ACCRUALS_PATH, [item.model_dump() for item in rows])


def save_journal_entries(rows: list[JournalEntry]) -> None:
    _write(JOURNALS_PATH, [item.model_dump() for item in rows])


def reset_period(period: str) -> None:
    save_accruals([item for item in load_accruals() if item.period != period])
    save_journal_entries([item for item in load_journal_entries() if item.period != period])


def get_open_accruals(period: str = "", vendor: str = "") -> list[OpenAccrual]:
    rows = [item for item in load_accruals() if item.status == "open"]
    if period:
        rows = [item for item in rows if item.period == period]
    if vendor:
        rows = [item for item in rows if item.vendor.lower() == vendor.lower()]
    return rows


def find_accrual(accrual_id: str) -> OpenAccrual | None:
    for item in load_accruals():
        if item.accrual_id == accrual_id:
            return item
    return None


def void_open_accrual(vendor: str, period: str) -> None:
    """Drop an open accrual the agent booked before validation rejected the decision."""
    current = load_accruals()
    dropped = [
        item
        for item in current
        if item.vendor.lower() == vendor.lower() and item.period == period and item.status == "open"
    ]
    if not dropped:
        return
    dropped_ids = {item.accrual_id for item in dropped}
    dropped_journals = {item.journal_entry_id for item in dropped}
    save_accruals([item for item in current if item.accrual_id not in dropped_ids])
    save_journal_entries(
        [
            item
            for item in load_journal_entries()
            if item.entry_id not in dropped_journals and item.related_accrual_id not in dropped_ids
        ]
    )


def find_open_accrual(vendor: str, period: str) -> OpenAccrual | None:
    for item in get_open_accruals(period=period, vendor=vendor):
        return item
    return None


def _next_id(prefix: str, existing: list[str]) -> str:
    numbers = []
    for item in existing:
        if not item.startswith(prefix):
            continue
        suffix = item[len(prefix) :].lstrip("-")
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def build_journal_entry(
    *,
    vendor: str,
    period: str,
    amount: float,
    expense_account: str,
    entry_type: str,
    memo: str,
    related_accrual_id: str | None = None,
    debit_account: str | None = None,
    credit_account: str | None = None,
) -> JournalEntry:
    amount = money(amount)
    if amount <= 0:
        raise ValueError("Journal amount must be positive.")
    stamp = period.replace("-", "")
    existing = [item.entry_id for item in load_journal_entries()]
    if entry_type == "accrual":
        debit_account = debit_account or expense_account
        credit_account = credit_account or LIABILITY_ACCOUNT
    elif entry_type == "reversal":
        debit_account = debit_account or LIABILITY_ACCOUNT
        credit_account = credit_account or expense_account
    else:
        debit_account = debit_account or expense_account
        credit_account = credit_account or "Accounts Payable"
    return JournalEntry(
        entry_id=_next_id(f"JE-{stamp}", existing),
        period=period,
        vendor=vendor,
        memo=memo,
        debit=JournalLine(account=debit_account, amount=amount),
        credit=JournalLine(account=credit_account, amount=amount),
        entry_type=entry_type,  # type: ignore[arg-type]
        related_accrual_id=related_accrual_id,
        created_at=_now(),
    )


def create_accrual(
    *,
    vendor: str,
    period: str,
    amount: float,
    method: str,
    confidence: float,
    evidence: list[str],
    reasoning_summary: str,
    expense_account: str = "",
    trace_id: str = "",
    discovery_trace_id: str = "",
) -> OpenAccrual:
    existing = find_open_accrual(vendor, period)
    if existing:
        updates = {}
        if trace_id and not existing.trace_id:
            updates["trace_id"] = trace_id
        if discovery_trace_id and not existing.discovery_trace_id:
            updates["discovery_trace_id"] = discovery_trace_id
        if updates:
            existing = existing.model_copy(update=updates)
            save_accruals(
                [existing if item.accrual_id == existing.accrual_id else item for item in load_accruals()]
            )
        return existing

    amount = money(amount)
    if amount <= 0:
        raise ValueError("Accrual amount must be positive.")
    expense_account = expense_account or expense_account_for(vendor, period)
    stamp = period.replace("-", "")
    accrual_id = _next_id(f"ACC-{stamp}", [item.accrual_id for item in load_accruals()])
    journal = build_journal_entry(
        vendor=vendor,
        period=period,
        amount=amount,
        expense_account=expense_account,
        entry_type="accrual",
        memo=f"Accrue {vendor} expense for {period} via {method}",
        related_accrual_id=accrual_id,
    )
    record = OpenAccrual(
        accrual_id=accrual_id,
        vendor=vendor,
        period=period,
        estimated_amount=amount,
        expense_account=expense_account,
        liability_account=LIABILITY_ACCOUNT,
        estimation_method=method,
        confidence=confidence,
        evidence=evidence,
        reasoning_summary=reasoning_summary,
        journal_entry_id=journal.entry_id,
        created_at=_now(),
        trace_id=trace_id or None,
        discovery_trace_id=discovery_trace_id or None,
    )
    accruals = load_accruals()
    journals = load_journal_entries()
    accruals.append(record)
    journals.append(journal)
    save_accruals(accruals)
    save_journal_entries(journals)
    return record


def journal_for(entry_id: str) -> JournalEntry | None:
    for item in load_journal_entries():
        if item.entry_id == entry_id:
            return item
    return None


def reconcile_accrual(
    accrual_id: str,
    invoice_id: str,
    actual_amount: float,
) -> ReconciliationResult:
    record = find_accrual(accrual_id)
    if record is None:
        raise ValueError(f"Accrual {accrual_id} was not found.")
    if record.status != "open":
        raise ValueError(f"Accrual {accrual_id} is {record.status}, not open.")

    actual_amount = money(actual_amount)
    if actual_amount <= 0:
        raise ValueError("Actual invoice amount must be positive.")
    error = money(actual_amount - record.estimated_amount)
    absolute_error = money(abs(error))
    percentage_error = (
        round(absolute_error / record.estimated_amount * 100, 2)
        if record.estimated_amount
        else None
    )
    reversal = build_journal_entry(
        vendor=record.vendor,
        period=record.period,
        amount=record.estimated_amount,
        expense_account=record.expense_account,
        entry_type="reversal",
        memo=f"Reverse {record.accrual_id} after invoice {invoice_id}",
        related_accrual_id=record.accrual_id,
    )
    invoice_entry = build_journal_entry(
        vendor=record.vendor,
        period=record.period,
        amount=actual_amount,
        expense_account=record.expense_account,
        entry_type="invoice",
        memo=f"Book actual invoice {invoice_id} for {record.vendor} {record.period}",
        related_accrual_id=record.accrual_id,
    )

    updated = record.model_copy(
        update={
            "status": "reconciled",
            "reversal_entry_id": reversal.entry_id,
            "invoice_entry_id": invoice_entry.entry_id,
            "actual_invoice_id": invoice_id,
            "actual_amount": actual_amount,
            "estimation_error": error,
            "reconciled_at": _now(),
        }
    )
    accruals = [updated if item.accrual_id == accrual_id else item for item in load_accruals()]
    journals = load_journal_entries() + [reversal, invoice_entry]
    save_accruals(accruals)
    save_journal_entries(journals)
    return ReconciliationResult(
        accrual_id=record.accrual_id,
        vendor=record.vendor,
        period=record.period,
        estimated_amount=record.estimated_amount,
        actual_invoice_id=invoice_id,
        actual_amount=actual_amount,
        estimation_error=error,
        absolute_error=absolute_error,
        percentage_error=percentage_error,
        reversal_entry_id=reversal.entry_id,
        invoice_entry_id=invoice_entry.entry_id,
        trace_id=record.trace_id,
        discovery_trace_id=record.discovery_trace_id,
        accrual_trace_id=record.trace_id,
        expense_account=record.expense_account,
        reversal=TraceJournal(
            entry_id=reversal.entry_id,
            debit_account=reversal.debit.account,
            credit_account=reversal.credit.account,
            amount=reversal.debit.amount,
        ),
        invoice_entry=TraceJournal(
            entry_id=invoice_entry.entry_id,
            debit_account=invoice_entry.debit.account,
            credit_account=invoice_entry.credit.account,
            amount=invoice_entry.debit.amount,
        ),
    )
