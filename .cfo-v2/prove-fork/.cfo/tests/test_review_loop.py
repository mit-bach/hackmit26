from ar.store import get_invoice, get_payment
from close.actions import resolve_review_item
from close.agents import decide_final_close
from close.cash_overlay import has_overlay, load_overlay
from close.gating import evaluate_close_gates
from close.ledger import load_entries
from close.models import CloseGateResult, FinalCloseVerdict
from close.month_end import finalize_close, rerun_affected, run_month_end
from close.reviews import load_reviews
from prepaid.store import get_item


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


def _by_workflow(period="2026-09"):
    return {item.source_workflow: item for item in load_reviews(period)}


def _resolve_all():
    rows = _by_workflow()
    cash = resolve_review_item(rows["cash"].review_id, action="post_correcting_entry")
    ar = resolve_review_item(rows["ar"].review_id, action="apply_payment", invoice_id="INV-AR-050")
    prepaid = resolve_review_item(rows["prepaid"].review_id, action="attach_evidence", document_id="DOC-NS-FLOOD-2026")
    return cash, ar, prepaid


def test_review_items_persist_and_do_not_duplicate(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    first = run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    rows = load_reviews("2026-09")
    assert {item.source_workflow for item in rows} == {"cash", "ar", "prepaid"}
    assert first.period.status == "BLOCKED"
    run_month_end("2026-09", scenario="demo", live=False, reset=False, retry_failed=False, allow_close=False)
    again = load_reviews("2026-09")
    assert len(again) == 3
    assert {item.review_id for item in again} == {item.review_id for item in rows}


def test_reviewer_action_mutates_source_objects(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    invoice_before = get_invoice("INV-AR-050")
    assert invoice_before is not None
    before_outstanding = invoice_before.outstanding_amount
    cash, ar, prepaid = _resolve_all()
    assert cash.status == "RESOLVED"
    assert has_overlay("2026-09")
    overlay = load_overlay("2026-09")
    assert overlay["ledger_entries"]
    assert overlay["ledger_entries"][0]["amount"] == 12.4
    payment = get_payment("PAY-CLOSE-4500")
    invoice = get_invoice("INV-AR-050")
    assert payment is not None and payment.application_status == "APPLIED"
    assert payment.unapplied_amount == 0
    assert invoice is not None
    assert invoice.outstanding_amount == before_outstanding - 4500
    assert ar.source_object_after["invoice_after"]["INV-AR-050"]["outstanding_amount"] == invoice.outstanding_amount
    item = get_item("PRE-INS-MISSING")
    assert item is not None
    assert item.source_document_id == "DOC-NS-FLOOD-2026"
    assert "DOC-NS-FLOOD-2026" in item.evidence_refs
    assert prepaid.source_object_before["source_document_id"] == ""
    assert prepaid.source_object_after["source_document_id"] == "DOC-NS-FLOOD-2026"


def test_downstream_invalidation_reruns_only_affected_tasks(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    initial = run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    completed_before = {item.task_id: item.status for item in initial.tasks}
    _resolve_all()
    rerun = rerun_affected("2026-09")
    assert "accruals" not in rerun.rerun_tasks
    assert "depreciation" not in rerun.rerun_tasks
    assert "ingest" not in rerun.rerun_tasks
    assert "ap" not in rerun.rerun_tasks
    assert set(rerun.rerun_tasks) <= {"cash", "ar", "prepaid", "bs_recon", "exceptions", "final_review", "mark_closed"}
    assert "cash" in rerun.invalidated_tasks
    assert "ar" in rerun.invalidated_tasks
    assert "prepaid" in rerun.invalidated_tasks
    assert completed_before["accruals"] == "COMPLETE"
    assert next(item.status for item in rerun.tasks if item.task_id == "accruals") == "COMPLETE"
    assert next(item.status for item in rerun.tasks if item.task_id == "depreciation") == "COMPLETE"


def test_journal_idempotency_after_resolution(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    _resolve_all()
    first = rerun_affected("2026-09")
    first_ids = [item["entry_id"] for item in load_entries()]
    second = rerun_affected("2026-09")
    second_ids = [item["entry_id"] for item in load_entries()]
    assert first_ids == second_ids
    assert first.period.status != "CLOSED"
    assert second.period.status != "CLOSED"


def test_unresolved_and_rejected_reviews_block_close(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    blocked = finalize_close("2026-09", live=False)
    assert blocked.period.status != "CLOSED"
    assert blocked.period.closed_at is None
    rows = _by_workflow()
    rejected = resolve_review_item(rows["cash"].review_id, action="reject", reason="Leave the $12.40 unexplained.")
    assert rejected.status == "REJECTED"
    still = finalize_close("2026-09", live=False)
    assert still.period.status != "CLOSED"
    assert still.final_verdict is not None
    assert still.final_verdict.decision != "APPROVE_CLOSE"


def test_missing_evidence_cannot_be_bypassed(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    rows = _by_workflow()
    resolve_review_item(rows["cash"].review_id, action="post_correcting_entry")
    resolve_review_item(rows["ar"].review_id, action="apply_payment", invoice_id="INV-AR-050")
    rerun_affected("2026-09")
    item = get_item("PRE-INS-MISSING")
    assert item is not None
    assert not item.source_document_id
    closed = finalize_close("2026-09", live=False)
    assert closed.period.status != "CLOSED"
    assert closed.gate is not None
    assert closed.gate.evidence_complete is False


def test_final_reviewer_cannot_override_deterministic_blocker(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    state = run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    gate = evaluate_close_gates(state)
    assert gate.passed is False
    forced = FinalCloseVerdict(
        period="2026-09",
        decision="APPROVE_CLOSE",
        reasons=["Agent tried to force the close."],
        reviewer="rogue-agent",
        gate_passed=True,
    )

    def fake_decide(current, current_gate, *, live=False, reviewer="Month-End Close Reviewer"):
        return forced

    monkeypatch.setattr("close.agents.decide_final_close", fake_decide)
    result = finalize_close("2026-09", live=False)
    assert result.period.status != "CLOSED"
    assert result.final_verdict is not None
    assert result.final_verdict.decision == "REJECT_CLOSE"
    assert result.final_verdict.overridden_by_python is True


def test_all_blockers_resolved_allows_close_lifecycle(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    initial = run_month_end("2026-09", scenario="demo", live=False, reset=True, allow_close=False)
    by_id = {item.task_id: item for item in initial.tasks}
    assert by_id["cash"].status == "NEEDS_REVIEW"
    assert by_id["bs_recon"].status == "BLOCKED"
    assert initial.period.status == "BLOCKED"
    details = " ".join(item.description for item in load_reviews("2026-09"))
    assert "12.40" in details or "12.4" in details
    assert "4,500" in details or "4500" in details
    assert "missing insurance" in details.lower()
    _resolve_all()
    rerun = rerun_affected("2026-09")
    rerun_ids = {item.task_id: item.status for item in rerun.tasks}
    assert rerun_ids["cash"] == "COMPLETE"
    assert rerun_ids["ar"] == "COMPLETE"
    assert rerun_ids["prepaid"] == "COMPLETE"
    assert rerun_ids["bs_recon"] == "COMPLETE"
    assert rerun_ids["exceptions"] == "COMPLETE"
    assert rerun_ids["final_review"] != "COMPLETE"
    assert rerun.period.status != "CLOSED"
    closed = finalize_close("2026-09", live=False)
    assert closed.gate is not None and closed.gate.passed
    assert closed.final_verdict is not None
    assert closed.final_verdict.decision == "APPROVE_CLOSE"
    assert closed.period.status == "CLOSED"
    assert closed.period.approved_by
    assert closed.period.closed_at
    assert next(item.status for item in closed.tasks if item.task_id == "mark_closed") == "COMPLETE"
    links = [item for item in closed.identity_links if item.review_id]
    assert links


def test_decide_final_close_ignores_agent_when_blocked():
    from close.models import ClosePeriod, MonthEndState

    state = MonthEndState(
        period=ClosePeriod(period="2026-09", opened_at="2026-09-01T00:00:00Z", status="BLOCKED"),
        close_id="test",
    )
    gate = CloseGateResult(period="2026-09", passed=False, blockers=["open review"])
    verdict = decide_final_close(state, gate, live=False)
    assert verdict.decision == "REJECT_CLOSE"
    assert verdict.gate_passed is False
