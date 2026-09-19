from accrual.ledger import (
    ACCRUALS_PATH,
    JOURNALS_PATH,
    create_accrual,
    get_open_accruals,
    journal_for,
    reconcile_accrual,
    reset_period,
)


def test_create_accrual_is_balanced_and_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)

    first = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11849.90,
        method="usage_run_rate",
        confidence=0.91,
        evidence=["September usage 142000 gb_hours"],
        reasoning_summary="Usage times committed rate.",
        expense_account="Cloud Infrastructure Expense",
    )
    second = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=99999,
        method="last_invoice",
        confidence=0.5,
        evidence=[],
        reasoning_summary="should not replace",
        expense_account="Cloud Infrastructure Expense",
    )
    assert first.accrual_id == second.accrual_id
    assert first.estimated_amount == 11849.90
    journal = journal_for(first.journal_entry_id)
    assert journal is not None
    assert journal.debit.amount == journal.credit.amount == 11849.90
    assert journal.debit.account == "Cloud Infrastructure Expense"
    assert journal.credit.account == "Accrued Expenses"
    assert get_open_accruals(period="2026-09")[0].accrual_id == first.accrual_id


def test_reconcile_computes_estimation_error(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")

    record = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11850,
        method="usage_run_rate",
        confidence=0.91,
        evidence=["usage"],
        reasoning_summary="usage",
        expense_account="Cloud Infrastructure Expense",
    )
    result = reconcile_accrual(record.accrual_id, "INV-AE-2026-09", 12100)
    assert result.estimated_amount == 11850
    assert result.actual_amount == 12100
    assert result.estimation_error == 250
    assert get_open_accruals(period="2026-09") == []


def test_reset_period_only_clears_that_month(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")

    create_accrual(
        vendor="CleanSpace Facilities",
        period="2026-08",
        amount=2400,
        method="contract_commitment",
        confidence=0.95,
        evidence=[],
        reasoning_summary="contract",
        expense_account="Facilities Expense",
    )
    create_accrual(
        vendor="CleanSpace Facilities",
        period="2026-09",
        amount=2400,
        method="contract_commitment",
        confidence=0.95,
        evidence=[],
        reasoning_summary="contract",
        expense_account="Facilities Expense",
    )
    reset_period("2026-09")
    remaining = get_open_accruals()
    assert len(remaining) == 1
    assert remaining[0].period == "2026-08"


def test_create_accrual_attaches_missing_trace_id(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    first = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11849.90,
        method="usage_run_rate",
        confidence=0.9,
        evidence=[],
        reasoning_summary="tool booked first",
        expense_account="Cloud Infrastructure Expense",
    )
    assert first.trace_id is None
    second = create_accrual(
        vendor="Aether Compute",
        period="2026-09",
        amount=11849.90,
        method="usage_run_rate",
        confidence=0.9,
        evidence=[],
        reasoning_summary="workflow attaches trace",
        expense_account="Cloud Infrastructure Expense",
        trace_id="2026-09/run/aether_compute",
    )
    assert second.accrual_id == first.accrual_id
    assert second.trace_id == "2026-09/run/aether_compute"


def test_ledger_paths_are_under_runs():
    assert ACCRUALS_PATH.as_posix().endswith("runs/accruals/open_accruals.json")
    assert JOURNALS_PATH.as_posix().endswith("runs/accruals/journal_entries.json")
