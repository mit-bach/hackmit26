"""Prove every close CLI path uses one month-end engine."""

from __future__ import annotations

import inspect

from close.engine import CANONICAL_RUN, finalize_close, load_state, rerun_affected, run_month_end
from close.month_end import run_month_end as month_end_run
from close.period_lock import ClosedPeriodError


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def test_canonical_run_is_month_end_run():
    assert CANONICAL_RUN is month_end_run
    assert CANONICAL_RUN is run_month_end


def test_close_cli_modules_do_not_call_cfo_packet():
    import close.cli as cli
    import main

    assert "run_cfo_close" not in inspect.getsource(main.run_close_cli)
    assert "run_cfo_close" not in inspect.getsource(main.run_demo_close_cli)
    assert "orchestrator" not in inspect.getsource(main.run_demo_close_cli)
    assert "from close.engine import run_month_end" in inspect.getsource(main.run_demo_close_cli)
    assert "from close.engine import" in inspect.getsource(cli)
    assert "from close.month_end import" not in inspect.getsource(cli)


def test_main_close_period_is_close_month_alias(monkeypatch):
    seen: list[list[str]] = []

    def fake(argv):
        seen.append(list(argv))
        return 0

    monkeypatch.setattr("close.cli.run_close_month_cli", fake)
    from main import run_close_cli

    assert run_close_cli(["2026-09", "--deterministic"]) == 0
    assert seen[0][:3] == ["--month", "2026-09", "--reset"]
    assert "--deterministic" in seen[0]


def test_demo_close_uses_canonical_engine(monkeypatch):
    called = []

    class Dummy:
        period = type("P", (), {"period": "2026-09", "status": "BLOCKED"})()
        tasks = []
        exceptions = []
        human_review_items = ["Cash unexplained $12.40 remains"]

    def fake(*args, **kwargs):
        called.append(kwargs)
        return Dummy()

    monkeypatch.setattr("close.engine.run_month_end", fake)
    monkeypatch.setattr("close.report.format_month_end_demo", lambda state: "DEMO")
    from main import run_demo_close_cli

    assert run_demo_close_cli(["2026-09"]) == 0
    assert called[0]["scenario"] == "demo"
    assert called[0]["reset"] is True
    assert called[0]["allow_close"] is False


def test_aliases_share_one_period_store(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    first = run_month_end("2026-09", scenario="demo", live=False, reset=True)
    loaded = load_state("2026-09")
    assert loaded is not None
    assert loaded.close_id == first.close_id
    assert loaded.period.status == first.period.status == "BLOCKED"
    second = run_month_end("2026-09", scenario="demo", live=False, reset=False)
    assert second.close_id == first.close_id
    assert second.period.status == "BLOCKED"


def test_cfo_packet_does_not_write_period_state(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    monkeypatch.setattr("close.orchestrator.CLOSE_DIR", tmp_path / "cfo-packet")
    assert load_state("2026-09") is None
    from close.orchestrator import run_cfo_close

    packet = run_cfo_close("2026-09", live=False, featured_ap=(), use_agent_accrual=False)
    assert packet.period == "2026-09"
    assert load_state("2026-09") is None
    assert not hasattr(packet, "tasks") or not getattr(packet, "tasks", None)


def test_review_resolution_updates_canonical_store(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    from close.actions import resolve_review_item
    from close.reviews import load_reviews

    cash = next(item for item in load_reviews("2026-09") if item.source_workflow == "cash")
    resolve_review_item(cash.review_id, action="post_correcting_entry", period="2026-09")
    updated = next(item for item in load_reviews("2026-09") if item.review_id == cash.review_id)
    assert updated.status == "RESOLVED"
    assert updated.journal_entry_ids


def test_snapshots_and_lock_come_from_one_engine(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    initial = run_month_end("2026-09", scenario="seed_demo", live=False, reset=True)
    assert initial.period.status == "BLOCKED"
    from close.actions import resolve_review_item
    from close.reviews import load_reviews

    cash = next(item for item in load_reviews("2026-09") if item.source_workflow == "cash")
    resolve_review_item(cash.review_id, action="post_correcting_entry", period="2026-09")
    rerun_affected("2026-09")
    closed = finalize_close("2026-09", live=False)
    assert closed.period.status == "CLOSED"
    from close.snapshot import list_snapshots

    snaps = list_snapshots("2026-09")
    assert len(snaps) == 1
    assert snaps[0].period == "2026-09"
    from close.cli import run_post_journal_cli

    assert run_post_journal_cli(
        ["--date", "2026-09-29", "--debit", "Insurance Expense", "--credit", "Cash", "--amount", "100"]
    ) == 1
    from close.ledger import post_entry

    try:
        post_entry(
            period="2026-09",
            memo="late September entry",
            debit_account="Insurance Expense",
            credit_account="Cash",
            amount=100,
            entry_type="manual",
            idempotency_key="canonical-post-close",
            source_document_id="MANUAL",
            evidence_refs=["MANUAL"],
        )
        raise AssertionError("closed-period lock did not apply")
    except ClosedPeriodError as exc:
        assert exc.event.event_type == "POST_CLOSE_ENTRY_ATTEMPT"
        assert exc.event.decision == "REJECTED"


def test_rerun_after_close_is_idempotent(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="clean", live=False, reset=True)
    from close.ledger import load_entries
    from close.snapshot import list_snapshots

    journals = [item["entry_id"] for item in load_entries()]
    snaps = [item.snapshot_id for item in list_snapshots("2026-09")]
    again = run_month_end("2026-09", scenario="clean", live=False, reset=False)
    assert again.period.status == "CLOSED"
    assert [item["entry_id"] for item in load_entries()] == journals
    assert [item.snapshot_id for item in list_snapshots("2026-09")] == snaps
