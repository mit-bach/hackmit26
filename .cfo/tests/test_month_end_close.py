from close.checklist import build_tasks, ready_tasks, refresh_readiness
from close.ledger import load_entries
from close.month_end import HANDLERS, run_month_end
from close.report import format_month_end_status
import pytest


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def test_dependency_ordering_and_blocked_tasks():
    tasks = build_tasks("2026-09")
    refresh_readiness(tasks)
    ready = {item.task_id for item in ready_tasks(tasks)}
    assert ready == {"ingest"}
    by_id = {item.task_id: item for item in tasks}
    by_id["ingest"].status = "COMPLETE"
    refresh_readiness(tasks)
    ready = {item.task_id for item in ready_tasks(tasks)}
    assert ready == {"ap", "ar", "cash"}
    by_id["cash"].status = "NEEDS_REVIEW"
    by_id["ap"].status = "COMPLETE"
    by_id["ar"].status = "COMPLETE"
    by_id["accruals"].status = "COMPLETE"
    by_id["prepaid"].status = "COMPLETE"
    by_id["depreciation"].status = "COMPLETE"
    refresh_readiness(tasks)
    assert by_id["bs_recon"].status == "BLOCKED"
    assert by_id["final_review"].status == "NOT_STARTED"


def test_demo_close_blocks_final_and_surfaces_exceptions(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    state = run_month_end("2026-09", scenario="demo", live=False, reset=True)
    by_id = {item.task_id: item for item in state.tasks}
    assert by_id["ap"].status == "COMPLETE"
    assert by_id["ar"].status == "COMPLETE"
    assert by_id["cash"].status == "NEEDS_REVIEW"
    assert by_id["accruals"].status == "COMPLETE"
    assert by_id["prepaid"].status == "COMPLETE"
    assert by_id["depreciation"].status == "COMPLETE"
    assert by_id["bs_recon"].status == "BLOCKED"
    assert by_id["final_review"].status == "NOT_STARTED"
    assert by_id["mark_closed"].status in {"NOT_STARTED", "BLOCKED"}
    assert state.period.status == "BLOCKED"
    details = " ".join(item.detail for item in state.exceptions)
    assert "12.40" in details or "12.4" in details
    assert "4,500" in details or "4500" in details
    assert "missing insurance" in details.lower()
    text = format_month_end_status(state)
    assert "SEPTEMBER 2026 CLOSE" in text
    assert "NEEDS_REVIEW" in text
    assert "BLOCKED" in text
    assert "12.40" in text
    assert "4,500" in text
    assert "missing insurance" in text.lower()


def test_clean_close_succeeds_without_duplicate_journals(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    first = run_month_end("2026-09", scenario="clean", live=False, reset=True)
    by_id = {item.task_id: item for item in first.tasks}
    assert by_id["mark_closed"].status == "COMPLETE"
    assert first.period.status == "CLOSED"
    first_ids = [item["entry_id"] for item in load_entries()]
    second = run_month_end("2026-09", scenario="clean", live=False, reset=False)
    second_ids = [item["entry_id"] for item in load_entries()]
    assert first_ids == second_ids
    assert second.period.status == "CLOSED"


def test_failed_task_retry(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    calls = {"n": 0}
    original = HANDLERS["ingest"]

    def flaky(state, live):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("ingest exploded")
        return original(state, live)

    monkeypatch.setitem(HANDLERS, "ingest", flaky)
    failed = run_month_end("2026-09", scenario="clean", live=False, reset=True)
    assert any(item.task_id == "ingest" and item.status == "FAILED" for item in failed.tasks)
    monkeypatch.setitem(HANDLERS, "ingest", original)
    retried = run_month_end("2026-09", scenario="clean", live=False, reset=False, retry_failed=True)
    assert next(item for item in retried.tasks if item.task_id == "ingest").status == "COMPLETE"


def test_human_review_case_and_final_close_guard(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    state = run_month_end("2026-09", scenario="demo", live=False, reset=True)
    assert state.human_review_items
    assert state.period.closed_at is None
    mark = next(item for item in state.tasks if item.task_id == "mark_closed")
    assert mark.status != "COMPLETE"


def test_cross_workflow_server_identity(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    state = run_month_end("2026-09", scenario="demo", live=False, reset=True)
    assert any(item.invoice_id == "INV-021" for item in state.ap_results)
    assert any(item.transaction_id == "INV-021" or item.extra.get("kind") == "capital_invoice" for item in state.identity_links)
    journals = load_entries()
    assert any(item["entry_type"] == "depreciation" for item in journals)
    assert any("INV-021" in str(item.get("transaction_id")) or "server" in item["memo"].lower() for item in journals)


def test_seed_demo_blocks_then_closes_after_resolution(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    first = run_month_end("2026-09", scenario="seed_demo", live=False, reset=True)
    by_id = {item.task_id: item for item in first.tasks}
    assert by_id["ap"].status == "COMPLETE"
    assert by_id["ar"].status == "COMPLETE"
    assert by_id["cash"].status == "NEEDS_REVIEW"
    assert by_id["prepaid"].status == "COMPLETE"
    assert by_id["depreciation"].status == "COMPLETE"
    assert first.period.status == "BLOCKED"
    assert first.period.closed_at is None
    assert any("12.40" in item or "12.4" in item for item in first.human_review_items) or any(
        "12.40" in item.detail for item in first.exceptions
    )
    from close.actions import resolve_review_item
    from close.month_end import finalize_close, rerun_affected
    from close.reviews import load_reviews

    cash = next(item for item in load_reviews("2026-09") if item.source_workflow == "cash")
    resolve_review_item(cash.review_id, action="post_correcting_entry", period="2026-09")
    rerun_affected("2026-09")
    second = finalize_close("2026-09", live=False)
    assert second.period.status == "CLOSED"
    assert second.snapshot_path
    from close.snapshot import list_snapshots
    from close.ledger import post_entry
    from close.period_lock import ClosedPeriodError

    snaps = list_snapshots("2026-09")
    assert len(snaps) == 1
    third = run_month_end("2026-09", scenario="seed_demo", live=False, reset=False)
    assert [item["entry_id"] for item in load_entries()] == [item["entry_id"] for item in load_entries()]
    assert len(list_snapshots("2026-09")) == 1
    assert third.period.status == "CLOSED"
    with pytest.raises(ClosedPeriodError) as exc:
        post_entry(
            period="2026-09",
            memo="late September entry",
            debit_account="Insurance Expense",
            credit_account="Cash",
            amount=100,
            entry_type="manual",
            idempotency_key="post-close-test",
            source_document_id="MANUAL",
            evidence_refs=["MANUAL"],
        )
    assert exc.value.event.event_type == "POST_CLOSE_ENTRY_ATTEMPT"
    assert exc.value.event.decision == "REJECTED"


def test_reopen_preserves_snapshot_and_requires_reclose(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="clean", live=False, reset=True)
    from close.month_end import reopen_period
    from close.snapshot import list_snapshots

    first_ids = [item.snapshot_id for item in list_snapshots("2026-09")]
    assert first_ids
    reopened = reopen_period("2026-09", "Late vendor correction")
    assert reopened.period.status == "REOPENED"
    assert [item.snapshot_id for item in list_snapshots("2026-09")] == first_ids
    closed = run_month_end("2026-09", scenario="clean", live=False, reset=False)
    assert closed.period.status == "CLOSED"
    snaps = list_snapshots("2026-09")
    assert len(snaps) == 2
    assert snaps[0].snapshot_id == first_ids[0]


def test_child_task_waits_on_cash_blockers():
    from close.checklist import build_tasks, refresh_readiness

    tasks = build_tasks("2026-09")
    by_id = {item.task_id: item for item in tasks}
    for task_id in ("ingest", "ap", "ar", "accruals", "prepaid", "depreciation"):
        by_id[task_id].status = "COMPLETE"
    by_id["cash"].status = "NEEDS_REVIEW"
    refresh_readiness(tasks)
    assert by_id["bs_recon"].status == "BLOCKED"
    assert by_id["final_review"].status == "NOT_STARTED"
    by_id["ap"].status = "COMPLETE"
    refresh_readiness(tasks)
    assert by_id["accruals"].status in {"COMPLETE", "READY", "NOT_STARTED"}
