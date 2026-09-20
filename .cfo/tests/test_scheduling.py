from __future__ import annotations

import json
from pathlib import Path

import pytest

from models import (
    CashPosition,
    InvestigationReport,
    PaymentAuditResult,
    PaymentPlan,
    PreparerRecommendation,
    ScheduledPayment,
)
from scheduling.cash import (
    apply_cash_and_policy_net,
    compute_metrics,
    load_cash_position,
    payment_candidate,
    policy_eligible_for_pool,
    spendable_cash,
)
from scheduling.grants import (
    AP_RECORD_OP_IDS,
    PAY_SCHEDULE_OP_IDS,
    ap_record_export_names,
    pay_schedule_export_names,
    profile_allows,
)
from scheduling.host import ConcurrenceRefused, apply_review_pay_concurrence
from scheduling.pool import load_pool, seed_demo_pool
from scheduling.workflow import run_schedule_workflow
from tools import all_invoices
from workflow import run_ap_workflow


def _candidates_for(*invoice_ids: str):
    return [payment_candidate(invoice_id) for invoice_id in invoice_ids]


def test_invoices_have_payment_fields():
    invoices = all_invoices()
    assert len(invoices) == 20
    for invoice in invoices:
        assert invoice.payment_terms
        assert invoice.late_fee_percent == 1.5
        assert invoice.vendor_priority in {"critical", "high", "normal", "low"}


def test_spendable_cash_is_python_arithmetic():
    cash = load_cash_position()
    assert cash.as_of_date == "2026-09-19"
    assert spendable_cash(cash) == 115000


def test_open_discount_and_unnecessary_early_facts():
    four = payment_candidate("INV-004")
    assert four.discount_open is True
    assert four.discount_amount == 65.6
    assert four.pay_amount_if_this_week == 3214.4
    assert four.unnecessary_if_paid_early is False

    github = payment_candidate("INV-009")
    assert github.discount_open is False
    assert github.unnecessary_if_paid_early is True
    assert github.amount == 21000

    acme = payment_candidate("INV-001")
    assert acme.discount_open is False
    assert acme.unnecessary_if_paid_early is True

    aws = payment_candidate("INV-002")
    assert aws.due_within_horizon is True
    assert aws.unnecessary_if_paid_early is False

    gcp = payment_candidate("INV-006")
    assert gcp.late is True
    assert gcp.due_date == "2026-09-18"


def test_held_invoices_are_not_policy_eligible():
    eligible = {invoice.invoice_id for invoice in all_invoices() if policy_eligible_for_pool(invoice.invoice_id)}
    assert "INV-001" in eligible
    assert "INV-011" in eligible
    assert "INV-012" in eligible
    assert "INV-017" in eligible
    for blocked in ["INV-010", "INV-013", "INV-014", "INV-015", "INV-016", "INV-018", "INV-019", "INV-020"]:
        assert blocked not in eligible


def test_seed_demo_pool_excludes_holds():
    added = seed_demo_pool()
    ids = {row["invoice_id"] for row in load_pool()}
    assert set(added) == ids
    assert "INV-020" not in ids
    assert "INV-018" not in ids
    assert "INV-009" in ids
    assert "INV-017" in ids


def test_policy_net_strips_unnecessary_early_payments():
    candidates = _candidates_for("INV-002", "INV-006", "INV-009", "INV-004")
    plan = apply_cash_and_policy_net(candidates, ["INV-009", "INV-006", "INV-002", "INV-004"])
    paid = {row.invoice_id for row in plan.pay_this_week}
    assert "INV-009" not in paid
    assert paid == {"INV-006", "INV-002", "INV-004"}
    assert plan.reserve_ok is True


def test_policy_net_backfills_due_invoices_and_discounts():
    candidates = _candidates_for("INV-002", "INV-006", "INV-007", "INV-009")
    plan = apply_cash_and_policy_net(candidates, [])
    paid = {row.invoice_id for row in plan.pay_this_week}
    assert paid == {"INV-002", "INV-006", "INV-007"}
    assert "INV-009" not in paid


def test_policy_net_never_pays_invoice_outside_pool():
    candidates = _candidates_for("INV-001")
    plan = apply_cash_and_policy_net(candidates, ["INV-020"])
    assert [row.invoice_id for row in plan.pay_this_week] == []
    assert plan.defer[0].invoice_id == "INV-001"


def test_cash_reserve_blocks_overspending():
    cash = CashPosition(
        as_of_date="2026-09-19",
        bank_balance=110000,
        minimum_cash_reserve=100000,
        expected_receipts_next_7_days=0,
        payroll_next_7_days=0,
        other_committed_outflows=0,
        payment_horizon_days=7,
    )
    assert spendable_cash(cash) == 10000
    candidates = _candidates_for("INV-002", "INV-006")
    plan = apply_cash_and_policy_net(candidates, ["INV-002", "INV-006"], cash)
    paid = {row.invoice_id for row in plan.pay_this_week}
    assert paid == {"INV-006"}
    assert "INV-002" not in paid
    assert plan.reserve_ok is True
    assert plan.cash_after_payments >= cash.minimum_cash_reserve


def test_metrics_for_policy_plan():
    added = seed_demo_pool()
    candidates = [payment_candidate(invoice_id) for invoice_id in added]
    plan = apply_cash_and_policy_net(candidates, [])
    metrics = compute_metrics(candidates, plan)
    paid = {row.invoice_id for row in plan.pay_this_week}

    assert "INV-002" in paid
    assert "INV-006" in paid
    assert "INV-004" in paid
    assert "INV-007" in paid
    assert "INV-011" in paid
    assert "INV-017" in paid
    assert "INV-009" not in paid
    assert "INV-001" not in paid
    assert "INV-020" not in paid

    assert metrics.invoices_due_this_horizon == 2
    assert metrics.due_invoices_paid_on_time == 2
    assert metrics.on_time_percent == 100.0
    assert metrics.discounts_missed == 0
    assert metrics.discounts_captured == metrics.discounts_available
    assert metrics.unnecessary_early_payments == 0
    assert metrics.reserve_violation is False
    assert metrics.late_fees_avoided == round(8320 * 0.015 + 9180 * 0.015, 2)
    assert plan.cash_after_payments == metrics.total_cash_retained
    assert plan.cash_after_payments >= 100000


def _ap_packets(invoice_id: str, decision: str, exceptions: list[str]):
    def fake_run(agent, prompt):
        if agent.name == "AP Preparer":
            rec = "INVESTIGATE" if exceptions else decision
            return PreparerRecommendation(
                invoice_id=invoice_id,
                recommendation=rec,
                confidence=0.9,
                reasons=[rec],
                evidence_used=[invoice_id],
                exception_types=exceptions,
            )
        if agent.name == "Exception Investigator":
            return InvestigationReport(
                invoice_id=invoice_id,
                issues_investigated=exceptions,
                findings=exceptions,
                recommendation=decision,
                confidence=0.9,
            )
        raise AssertionError(f"Bot ap must not run {agent.name}")

    return fake_run


def test_approve_does_not_write_pool_until_verifier(monkeypatch, tmp_path):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    monkeypatch.setattr("workflow.run_agent", _ap_packets("INV-001", "APPROVE", []))
    run_ap_workflow("INV-001")
    assert load_pool() == []

    monkeypatch.setattr("workflow.run_agent", _ap_packets("INV-018", "HOLD", ["duplicate"]))
    run_ap_workflow("INV-018")
    assert load_pool() == []


def test_host_strips_unnecessary_early_and_handles_ctl_pay(tmp_path):
    seed_demo_pool()

    def chooser(candidates, cash_pos):
        return PaymentPlan(
            as_of_date=cash_pos.as_of_date,
            pay_this_week=[
                ScheduledPayment(invoice_id="INV-009", amount=21000, reason="pay everything"),
                ScheduledPayment(invoice_id="INV-006", amount=9180, reason="late"),
            ],
            defer=[],
            total_payout=30180,
            cash_after_payments=200000,
            reserve_ok=True,
            reasons=["chooser proposed GitHub"],
            confidence=0.5,
        )

    computer = tmp_path / "computer"
    runs = tmp_path / "runs"
    trace = run_schedule_workflow(
        chooser=chooser, computer_root=computer, runs_dir=runs
    )
    paid = {row.invoice_id for row in trace.plan.pay_this_week}
    assert "INV-009" not in paid
    assert "INV-006" in paid
    assert "INV-002" in paid
    assert trace.metrics.unnecessary_early_payments == 0
    assert trace.audit.passed is False
    assert "ctl-pay/review-pay" in trace.audit.findings[0]
    assert list(runs.glob("schedule-*.json"))
    wake = json.loads(Path(trace.verifier_wake_path).read_text())
    assert wake["toSlug"] == "ctl-pay"
    assert wake["profile"] == "review-pay"
    assert wake["status"] == "accepted"
    assert wake["done"] is False
    assert wake["op"] == "bot_send_prompt"
    assert "ask_user" not in json.dumps(wake)
    assert trace.outflow_packet_path is None
    assert list((computer / "workspace" / "cash" / "expected-outflows").glob("*.json")) == []
    packet = json.loads(Path(trace.plan_packet_path).read_text())
    assert packet["executed"] is False
    assert packet["self_approved"] is False


def test_policy_net_strips_hold_invoices():
    candidates = _candidates_for("INV-002", "INV-018")
    assert policy_eligible_for_pool("INV-018") is False
    plan = apply_cash_and_policy_net(candidates, ["INV-018", "INV-002"])
    paid = {row.invoice_id for row in plan.pay_this_week}
    assert "INV-018" not in paid
    assert "INV-002" in paid
    hold_defer = next(row for row in plan.defer if row.invoice_id == "INV-018")
    assert "HOLD" in hold_defer.reason


def test_seeded_schedule_defers_inv009_class(tmp_path):
    seed_demo_pool()
    trace = run_schedule_workflow(
        computer_root=tmp_path / "computer",
        runs_dir=tmp_path / "runs",
    )
    paid = {row.invoice_id for row in trace.plan.pay_this_week}
    deferred = {row.invoice_id for row in trace.plan.defer}
    assert "INV-009" not in paid
    assert "INV-009" in deferred
    assert "INV-020" not in paid
    assert "INV-018" not in paid
    assert "INV-018" not in deferred


def test_pay_cannot_load_record_tools():
    assert PAY_SCHEDULE_OP_IDS.isdisjoint(AP_RECORD_OP_IDS)
    assert pay_schedule_export_names().isdisjoint(ap_record_export_names())
    assert profile_allows("schedule", "tools.get_invoice") is False
    assert profile_allows("schedule", "scheduling.tools.get_cash_position") is True
    assert profile_allows("review-pay", "scheduling.tools.get_approved_pool") is False
    fragment = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / ".cfo-v2"
            / "office"
            / "bots"
            / "pay"
            / "grants.fragment.json"
        ).read_text()
    )
    assert "Payment Audit" not in fragment["byDisplayName"]
    ops = fragment["byDisplayName"]["Payment Scheduler"]["ops"]
    assert "tools.get_invoice" not in ops
    assert set(ops) == set(PAY_SCHEDULE_OP_IDS)
    compiled = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / ".cfo-v2"
            / "office"
            / "computer"
            / "cfo"
            / "grants.json"
        ).read_text()
    )
    scheduler_ops = compiled["byDisplayName"]["Payment Scheduler"]["ops"]
    assert "tools.get_invoice" not in scheduler_ops
    assert set(scheduler_ops) == set(PAY_SCHEDULE_OP_IDS)
    roster = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / ".cfo-v2"
            / "office"
            / "computer"
            / "harness"
            / "roster.json"
        ).read_text()
    )
    pay = next(bot for bot in roster["bots"] if bot["slug"] == "pay")
    assert pay["approvalLevel"] == "never"
    assert "tools.get_invoice" not in pay["connectors"]
    assert "scheduling.tools.get_payment_candidates" in pay["connectors"]


def test_pay_cannot_self_approve_and_outflows_wait_on_ctl_pay(tmp_path):
    seed_demo_pool()
    computer = tmp_path / "computer"
    trace = run_schedule_workflow(
        computer_root=computer, runs_dir=tmp_path / "runs"
    )
    with pytest.raises(ConcurrenceRefused, match="cannot concur"):
        apply_review_pay_concurrence(
            plan_packet_path=Path(trace.plan_packet_path),
            concurrence=PaymentAuditResult(passed=True, findings=["pay tried"]),
            source_slug="pay",
            computer_root=computer,
        )
    with pytest.raises(ConcurrenceRefused, match="refused"):
        apply_review_pay_concurrence(
            plan_packet_path=Path(trace.plan_packet_path),
            concurrence=PaymentAuditResult(passed=False, findings=["incomplete"]),
            source_slug="ctl-pay",
            computer_root=computer,
        )
    result = apply_review_pay_concurrence(
        plan_packet_path=Path(trace.plan_packet_path),
        concurrence=PaymentAuditResult(
            passed=True, findings=["Kernel reserve_ok and packet complete"]
        ),
        source_slug="ctl-pay",
        computer_root=computer,
    )
    assert result["executed"] is False
    packet = json.loads(Path(result["outflow_packet_path"]).read_text())
    assert packet["executed"] is False
    assert packet["kind"] == "expected_outflows"
    assert packet["after"] == "ctl-pay/review-pay"
    cash_wake = json.loads(Path(result["cash_wake_path"]).read_text())
    assert cash_wake["toSlug"] == "cash"
    assert cash_wake["op"] == "bot_send_prompt"
    assert "ACH" in cash_wake["prompt"]


def test_pay_host_never_calls_ask_user():
    root = Path(__file__).resolve().parents[1] / "scheduling"
    for path in root.glob("*.py"):
        text = path.read_text()
        assert "ask_user" not in text
        assert "ask the user" not in text.lower()
    bot = Path(__file__).resolve().parents[2] / ".cfo-v2" / "office" / "bots" / "pay"
    for path in bot.rglob("*.md"):
        text = path.read_text().lower()
        assert "ask the user if" not in text
        assert "escalate to management" not in text
