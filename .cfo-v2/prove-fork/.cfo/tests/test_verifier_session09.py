"""Session 09: Verifier Bots own concurrence. People are not in the completion path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cash_recon.workflow import run_cash_reconciliation
from close.gating import evaluate_close_gates
from close.month_end import load_state, run_month_end
from scheduling.pool import load_pool
from verifier.concurrence import (
    ConcurrenceRefused,
    apply_ctl_books_lock,
    apply_ctl_cash_rec,
    apply_ctl_pay_match,
)
from verifier.grants import RECORD_TOOLS, VerifierGrantError, assert_op_allowed, denied_ops
from verifier.queue_owners import owner_for
from workflow import commit_to_pay_pool, complete_ctl_pay_handle, run_ap_workflow


REPO = Path(__file__).resolve().parents[2]
KERNEL = REPO / ".cfo"
CLIENT = REPO / ".cfo-v2"
HOST_PATHS = (
    KERNEL / "workflow.py",
    KERNEL / "scheduling" / "host.py",
    KERNEL / "ar" / "workflow.py",
    KERNEL / "cash_recon" / "workflow.py",
    KERNEL / "close" / "host.py",
    CLIENT / "office" / "computer" / "cfo" / "extensions" / "index.ts",
    CLIENT / "office" / "computer" / "cfo" / "extensions" / "call.ts",
    CLIENT / "office" / "computer" / "cfo" / "extensions" / "intercept.ts",
)


def test_ap_cannot_finalize_approve_without_ctl_pay(monkeypatch, tmp_path):
    def fake_run(agent, prompt):
        from models import PreparerRecommendation

        if agent.name != "AP Preparer":
            raise AssertionError(f"unexpected {agent.name}")
        return PreparerRecommendation(
            invoice_id="INV-001",
            recommendation="APPROVE",
            confidence=0.9,
            reasons=["clean"],
            evidence_used=["INV-001"],
            exception_types=[],
        )

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)
    trace = run_ap_workflow("INV-001")
    assert trace.posted_to_pool is False
    assert load_pool() == []
    assert commit_to_pay_pool("INV-001", kernel_allow=True, ctl_pay_concurred=False) is False
    assert load_pool() == []
    with pytest.raises(ConcurrenceRefused, match="forbidden: ap"):
        complete_ctl_pay_handle("INV-001", bot_decision="CONCUR", source_slug="ap")
    first = complete_ctl_pay_handle("INV-001", bot_decision="CONCUR", source_slug="ctl-pay")
    assert first["posted_to_pool"] is False
    assert first["audit_handle"] is not None
    second = complete_ctl_pay_handle(
        "INV-001", bot_decision="CONCUR", source_slug="ctl-pay", audit_wake=True
    )
    assert second["posted_to_pool"] is True
    assert any(row["invoice_id"] == "INV-001" for row in load_pool())


def test_ctl_pay_cannot_call_record_tools_or_create_accrual():
    for op in RECORD_TOOLS:
        with pytest.raises(VerifierGrantError):
            assert_op_allowed("ctl-pay", "review-match", op)
        with pytest.raises(VerifierGrantError):
            assert_op_allowed("ctl-pay", "review-pay", op)
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-pay", "review-pay", "scheduling.tools.get_payment_candidates")
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-pay", "review-pay", "scheduling.tools.get_approved_pool")
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-pay", "review-match", "accrual.tools.create_accrual")
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-pay", "review-pay", "accrual.tools.create_accrual")
    denied = denied_ops("ctl-pay", "review-pay")
    assert "scheduling.tools.get_payment_candidates" in denied
    assert_op_allowed("ctl-pay", "review-match", "tools.get_case_evidence")


def test_ctl_books_cannot_create_accrual_or_lock_when_gates_fail():
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-books", "lock", "accrual.tools.create_accrual")
    with pytest.raises(VerifierGrantError):
        assert_op_allowed("ctl-books", "review-treatment", "accrual.tools.create_accrual")
    missing = apply_ctl_books_lock("2099-01", bot_decision="CONCUR")
    assert missing["decision"] == "REFUSE"
    assert missing["closed"] is False
    state = run_month_end("2026-09", reset=True, allow_close=False)
    gate = evaluate_close_gates(state)
    assert gate.passed is False
    locked = apply_ctl_books_lock("2026-09", bot_decision="CONCUR")
    assert locked["decision"] == "REFUSE"
    assert locked["gate_passed"] is False
    assert locked["closed"] is False
    latest = load_state("2026-09")
    assert latest is not None
    assert latest.period.status != "CLOSED"


def test_planted_12_40_concurrence_does_not_reconcile():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    assert report.period_status != "RECONCILED"
    result = apply_ctl_cash_rec("2026-09", bot_decision="CONCUR")
    assert result["decision"] == "REFUSE"
    assert result["reconciled"] is False
    assert result["period_status"] != "RECONCILED"
    assert "UNEXPLAINED_DIFFERENCE" in result["unexplained"]


def test_human_review_queue_owner_is_verifier():
    apply_q = owner_for("apply", "HUMAN_REVIEW")
    assert apply_q == {"owner": "ctl-cash", "profile": "review-apply"}
    cash_q = owner_for("cash", "HUMAN_REVIEW")
    assert cash_q == {"owner": "ctl-cash", "profile": "review-rec"}
    pay_q = owner_for("pay", "RELEASE")
    assert pay_q == {"owner": "ctl-pay", "profile": "review-pay"}
    lock_q = owner_for("close", "LOCK")
    assert lock_q == {"owner": "ctl-books", "profile": "lock"}


def test_production_hosts_have_no_human_completion_path():
    for path in HOST_PATHS:
        text = path.read_text(encoding="utf-8")
        assert "ask_user(" not in text, path
        assert "waiting on human" not in text.lower(), path
        assert "ar-review-correct" not in text, path
    grants = json.loads(
        (CLIENT / "office" / "computer" / "cfo" / "grants.json").read_text(encoding="utf-8")
    )
    payment_audit = grants["byDisplayName"]["Payment Audit"]["ops"]
    assert "scheduling.tools.get_payment_candidates" not in payment_audit
    roster = json.loads(
        (CLIENT / "office" / "computer" / "harness" / "roster.json").read_text(encoding="utf-8")
    )
    slugs = [row["slug"] for row in roster["bots"]]
    assert slugs.count("ctl-pay") == 1
    assert slugs.count("ctl-cash") == 1
    assert slugs.count("ctl-books") == 1
    assert "ctl-collect" not in slugs
    assert "ctl-story" not in slugs
    for row in roster["bots"]:
        if row["slug"] in {"ctl-pay", "ctl-cash", "ctl-books"}:
            assert row["approvalLevel"] == "never"


def test_wrong_bot_cannot_concur_pay_run(tmp_path):
    with pytest.raises(ConcurrenceRefused, match="forbidden: ap"):
        apply_ctl_pay_match(
            "INV-001",
            packet={"invoice_id": "INV-001"},
            bot_decision="CONCUR",
            handle_path=tmp_path / "missing.json",
            source_slug="ap",
        )
