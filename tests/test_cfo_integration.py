from close.ledger import load_entries, post_entry
from close.period_lock import ClosedPeriodError
from cfo.assertions import check_duplicate_propagation
from cfo.company import FEATURED, INTENDED_AUGUST, INTENDED_SEPTEMBER, PERIOD, money
from cfo.scenario import run_cfo_scenario
from close.orchestrator import decide_ap
from scheduling.cash import policy_eligible_for_pool
from scheduling.pool import load_pool, seed_demo_pool
import pytest


def _patch_accrual(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    monkeypatch.setattr("accrual.ledger.LEDGER_DIR", tmp_path)
    monkeypatch.setattr("accrual.workflow.RUNS_DIR", tmp_path / "accrual-runs")


@pytest.fixture
def cfo(tmp_path, monkeypatch):
    _patch_accrual(tmp_path, monkeypatch)
    return run_cfo_scenario(persist=False)


def test_shared_identity_across_workflows(cfo):
    by_id = {item["chain_id"]: item for item in cfo["chains"]}
    clean = by_id["CHAIN-AP-CLEAN"]
    assert clean["invoice_id"] == "INV-001"
    assert clean["approval_id"]
    assert clean["close_run_id"] == cfo["closed_close"].close_id
    assert clean["audit_run_id"] == cfo["audit_run"].audit_run_id

    brk = by_id["CHAIN-CASH-BREAK"]
    assert brk["bank_transaction_id"] == FEATURED["cash_break_bank"]
    assert brk["reconciliation_id"]
    assert brk["review_id"]
    assert brk["journal_entry_id"] == FEATURED["cash_correction_journal"]
    assert brk["snapshot_id"]
    assert brk["close_run_id"] == cfo["closed_close"].close_id

    grouped = by_id["CHAIN-CASH-GROUPED"]
    assert grouped["reconciliation_id"]
    assert "GROUPED_MATCH" in grouped["status"]


def test_amount_consistency(cfo):
    matched = cfo["ap_results"]["INV-001"]
    assert money(matched.amount) == 12450.0
    assert matched.decision == "APPROVE"

    statement = cfo["statement"]
    prior = cfo["prior_statement"]
    assert money(statement.revenue) == INTENDED_SEPTEMBER["revenue"]
    assert money(statement.cogs) == INTENDED_SEPTEMBER["cogs"]
    assert money(statement.gross_profit) == money(statement.revenue - statement.cogs)
    assert money(statement.gross_profit) == INTENDED_SEPTEMBER["gross_profit"]
    assert abs(statement.gross_margin_pct - INTENDED_SEPTEMBER["gross_margin_pct"]) < 0.0001
    assert abs(prior.gross_margin_pct - INTENDED_AUGUST["gross_margin_pct"]) < 0.0001

    brk = next(
        item
        for item in cfo["blocked_cash"].matches
        if FEATURED["cash_break_bank"] in item.bank_transaction_ids
    )
    assert money(abs(brk.difference)) == 12.40


def test_duplicate_invoice_never_becomes_payment():
    result = decide_ap("INV-018", live=False, featured=set())
    assert result.decision == "HOLD"
    assert not policy_eligible_for_pool("INV-018")
    seed_demo_pool()
    assert "INV-018" not in {item.get("invoice_id") for item in load_pool()}
    checks = check_duplicate_propagation({"INV-018": result})
    assert all(item["passed"] for item in checks)


def test_cash_break_blocks_close(cfo):
    blocked = cfo["blocked_close"]
    assert blocked.period.status == "BLOCKED"
    details = " ".join(item.detail for item in blocked.exceptions)
    reviews = " ".join(blocked.human_review_items)
    assert "12.40" in details or "12.4" in details or "12.40" in reviews
    cash_task = next(item for item in blocked.tasks if item.task_id == "cash")
    assert cash_task.status == "NEEDS_REVIEW"
    assert cfo["blocked_cash"].period_status != "RECONCILED" or money(
        cfo["blocked_cash"].unexplained_difference
    ) == 12.40


def test_resolution_then_successful_close(cfo):
    closed = cfo["closed_close"]
    assert closed.period.status == "CLOSED"
    assert closed.snapshot_path
    assert cfo["closed_reporting"]["books_closed"] is True
    assert cfo["closed_reporting"]["snapshot_id"]
    assert cfo["closed_cash"] is not None
    assert money(cfo["closed_cash"].unexplained_difference) == 0


def test_reporting_from_close_consistency(cfo):
    blocked_view = cfo["blocked_reporting"]
    closed_view = cfo["closed_reporting"]
    assert blocked_view["close_status"] == "BLOCKED"
    assert blocked_view["books_closed"] is False
    assert closed_view["close_status"] == "CLOSED"
    assert closed_view["books_closed"] is True
    assert closed_view["snapshot_id"]
    assert closed_view["snapshot_id"] != blocked_view.get("snapshot_id")
    statement = cfo["statement"]
    assert money(statement.cogs) == 390_000
    overage = [
        contrib
        for item in cfo["reporting_run"].variances
        for contrib in item.contributors
        if "hosting" in contrib.label.lower() or "TXN-HOST-SEP-OVERAGE" in contrib.source_transaction_ids
    ]
    assert overage


def test_forecast_actualization(cfo):
    forecast = cfo["forecast"]
    assert forecast is not None
    assert forecast.weeks
    held = [line for line in forecast.lines if line.source_id == "INV-016" and line.committed]
    assert held == []
    fva = cfo["forecast_variance"]
    assert fva is not None
    assert fva.contributors or abs(fva.total_ending_cash_variance) <= 0.02


def test_post_close_protection(cfo):
    assert cfo["post_close_rejected"] is True
    assert "REJECTED" in cfo["post_close_detail"]
    with pytest.raises(ClosedPeriodError) as exc:
        post_entry(
            period=PERIOD,
            memo="second unauthorized entry",
            debit_account="Insurance Expense",
            credit_account="Cash",
            amount=50,
            entry_type="manual",
            idempotency_key="cfo-test-post-close-2",
            source_document_id="CFO-TEST",
            evidence_refs=["CFO-TEST"],
        )
    assert exc.value.event.decision == "REJECTED"


def test_audit_over_operational_state(cfo):
    dataset = cfo["audit_dataset"]
    invoice_ids = {item.invoice_id for item in dataset.invoices}
    assert {"INV-001", "INV-018", "INV-016"} <= invoice_ids
    recon_banks = {bank_id for item in dataset.reconciliations for bank_id in item.bank_transaction_ids}
    assert FEATURED["cash_break_bank"] in recon_banks or FEATURED["cash_grouped_bank"] in recon_banks
    run = cfo["audit_run"]
    assert run.samples
    assert run.controls
    assert run.reperformance
    assert run.findings
    assert cfo["independence"]["passed"] is True
    assert cfo["independence"]["used_original_as_input"] is False
    assert cfo["independence"]["disagreement_detected"] is True


def test_human_reviews_are_visible(cfo):
    objects = {item["object_id"] for item in cfo["human_reviews"]}
    assert any("INV-018" in item or "INV-016" in item for item in objects)
    assert any("PAY" in item or "AMBIGUOUS" in item or "005" in item for item in objects)
    assert any(FEATURED["cash_break_bank"] in item for item in objects)
    assert all(item["status"] == "HUMAN_REVIEW" for item in cfo["human_reviews"])
    assert all(item["required_decision"] for item in cfo["human_reviews"])


def test_final_state_and_metrics(cfo):
    metrics = cfo["metrics"]
    assert metrics["workflows_completed"] == metrics["workflows_expected"]
    assert metrics["human_reviews_surfaced"] >= 3
    assert metrics["control_exceptions_surfaced"] >= 1
    assert metrics["close_gates_respected"] is True
    assert metrics["report_to_ledger_checks_passed"] is True
    assert metrics["audit_evidence_completeness"] is True
    assert metrics["integration_assertions_passed"] == metrics["integration_assertions_total"]
    assert 0 < metrics["score"] <= 1
    failed = [item["name"] for item in cfo["checks"] if not item["passed"]]
    assert failed == []
    assert cfo["closed_close"].period.status == "CLOSED"
    assert not any(item.get("source_document_id") == "INV-018" for item in load_entries())
