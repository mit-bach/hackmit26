from __future__ import annotations

import json
from pathlib import Path

import pytest

from ap_grants import (
    APPROVER_OPS,
    FORBIDDEN_AP_OPS,
    INVESTIGATE_OPS,
    POLICY_OPS,
    PREPARE_OPS,
    GrantError,
    assert_op_allowed,
    grants_for,
)
from models import (
    InvestigationReport,
    PreparerRecommendation,
)
from scheduling.pool import load_pool
from tools import collect_case_evidence
from workflow import (
    MAX_RECONSIDERATIONS,
    commit_to_pay_pool,
    kernel_allow_approve,
    must_hold,
    run_ap_workflow,
    wake_bot,
)


def _packet(invoice_id: str, kind: str, rec: str, **extra):
    if kind == "preparer":
        return PreparerRecommendation(
            invoice_id=invoice_id,
            recommendation=rec,
            confidence=0.8,
            reasons=[f"preparer {rec}"],
            evidence_used=[invoice_id],
            exception_types=extra.get("exception_types", []),
        )
    if kind == "investigator":
        return InvestigationReport(
            invoice_id=invoice_id,
            issues_investigated=extra.get("exception_types", []),
            findings=["investigated"],
            relevant_precedents=extra.get("precedents", []),
            relevant_policies=extra.get("policies", []),
            unresolved_risks=[],
            recommendation=rec,
            confidence=0.8,
        )
    raise ValueError(kind)


def test_mocked_clean_case_skips_investigator(monkeypatch, tmp_path):
    calls = []

    def fake_run(agent, prompt):
        calls.append(agent.name)
        invoice_id = "INV-001"
        if agent.name == "AP Preparer":
            return _packet(invoice_id, "preparer", "APPROVE")
        if agent.name == "Exception Investigator":
            raise AssertionError("Investigator should not run on a clean match")
        raise AssertionError(f"Bot ap must not run {agent.name}")

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-001")
    assert "Exception Investigator" not in calls
    assert calls == ["AP Preparer"]
    assert "AP Reviewer" not in calls
    assert "AP Approver" not in calls
    assert "AP Audit" not in calls
    assert trace.investigation is None
    assert trace.reviewer is None
    assert trace.approver is None
    assert trace.audit is None
    assert trace.final.decision == "APPROVE"
    assert trace.final.investigation_performed is False
    assert trace.posted_to_pool is False
    assert must_hold(trace.deterministic_evidence) == []
    assert kernel_allow_approve(trace.deterministic_evidence) is True
    assert trace.verifier_handle is not None
    assert trace.verifier_handle["toSlug"] == "ctl-pay"
    assert trace.verifier_handle["profile"] == "review-match"
    assert trace.verifier_handle["verifier_missing"] is False
    assert trace.verifier_handle["queue"]["owner"] == "ctl-pay"
    assert Path(trace.packet_path).is_file()
    saved = json.loads(Path(trace.trace_path).read_text())
    assert saved["final"]["decision"] == "APPROVE"
    assert saved["posted_to_pool"] is False
    assert saved["trace_path"]
    roles = [item.role for item in trace.agents]
    assert roles == ["AP Preparer"]
    preparer = saved["agents"][0]
    assert preparer["role"] == "AP Preparer"
    assert [item["name"] for item in preparer["skills"]] == ["three-way-match-analysis", "superseded-document-handling"]
    assert "body" not in preparer["skills"][0]
    assert preparer["skills"][0]["injected"] is True
    assert len(preparer["skills"][0]["content_hash"]) == 64
    assert load_pool() == []


def test_mocked_exception_runs_investigator(monkeypatch, tmp_path):
    calls = []

    def fake_run(agent, prompt):
        calls.append(agent.name)
        invoice_id = "INV-017"
        if agent.name == "AP Preparer":
            return _packet(invoice_id, "preparer", "INVESTIGATE", exception_types=["vendor_mismatch"])
        if agent.name == "Exception Investigator":
            return _packet(
                invoice_id,
                "investigator",
                "APPROVE",
                exception_types=["vendor_mismatch"],
                precedents=["CASE-001"],
                policies=["P-007"],
            )
        raise AssertionError(f"Bot ap must not run {agent.name}")

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-017")
    assert calls == ["AP Preparer", "Exception Investigator"]
    assert [item["profile"] for item in trace.wakes] == ["prepare", "investigate"]
    assert trace.investigation is not None
    assert trace.final.decision == "APPROVE"
    assert trace.final.investigation_performed is True
    assert trace.posted_to_pool is False
    assert kernel_allow_approve(trace.deterministic_evidence) is True


def test_mocked_duplicate_must_hold_vetoes_approve(monkeypatch, tmp_path):
    calls = []

    def fake_run(agent, prompt):
        calls.append(agent.name)
        invoice_id = "INV-018"
        if agent.name == "AP Preparer":
            return _packet(invoice_id, "preparer", "HOLD", exception_types=["duplicate"])
        if agent.name == "Exception Investigator":
            return _packet(invoice_id, "investigator", "APPROVE", exception_types=["duplicate"])
        raise AssertionError(f"Bot ap must not run {agent.name}")

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-018")
    assert MAX_RECONSIDERATIONS == 0
    assert calls == ["AP Preparer", "Exception Investigator"]
    assert calls.count("AP Approver") == 0
    assert calls.count("AP Audit") == 0
    assert any("P-002" in item for item in must_hold(trace.deterministic_evidence))
    assert kernel_allow_approve(trace.deterministic_evidence) is False
    assert trace.final.decision == "HOLD"
    assert trace.final.reconsideration_performed is False
    assert trace.verifier_handle is None
    assert trace.posted_to_pool is False
    assert load_pool() == []
    saved = json.loads(Path(trace.trace_path).read_text())
    assert saved["final"]["decision"] == "HOLD"
    assert saved["kernel_holds"]


def test_final_never_investigate(monkeypatch, tmp_path):
    def fake_run(agent, prompt):
        invoice_id = "INV-016"
        mapping = {
            "AP Preparer": _packet(invoice_id, "preparer", "INVESTIGATE", exception_types=["missing_po"]),
            "Exception Investigator": _packet(invoice_id, "investigator", "HOLD"),
        }
        if agent.name not in mapping:
            raise AssertionError(f"Bot ap must not run {agent.name}")
        return mapping[agent.name]

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)
    trace = run_ap_workflow("INV-016")
    assert trace.final.decision in {"APPROVE", "HOLD"}
    assert trace.final.decision == "HOLD"
    assert trace.preparer.recommendation == "INVESTIGATE"
    assert trace.posted_to_pool is False


def test_inv001_kernel_can_approve_without_posting():
    evidence = collect_case_evidence("INV-001")
    assert evidence.exception_types == []
    assert kernel_allow_approve(evidence) is True
    assert must_hold(evidence) == []


def test_inv018_kernel_still_hold():
    evidence = collect_case_evidence("INV-018")
    assert "duplicate" in evidence.exception_types
    assert kernel_allow_approve(evidence) is False
    assert any("P-002" in item for item in must_hold(evidence))


def test_commit_to_pay_pool_requires_verifier_and_kernel(monkeypatch, tmp_path):
    assert commit_to_pay_pool("INV-001", kernel_allow=True, ctl_pay_concurred=False) is False
    assert load_pool() == []
    assert commit_to_pay_pool("INV-018", kernel_allow=False, ctl_pay_concurred=True) is False
    assert load_pool() == []
    assert commit_to_pay_pool("INV-001", kernel_allow=True, ctl_pay_concurred=True, confidence=0.9)
    assert [row["invoice_id"] for row in load_pool()] == ["INV-001"]


def test_prepare_cannot_call_approver_policy_set():
    for op in POLICY_OPS:
        with pytest.raises(GrantError, match="forbidden"):
            assert_op_allowed("ap", "prepare", op)
    assert "tools.get_company_policies" in APPROVER_OPS
    assert "tools.get_company_policies" not in PREPARE_OPS
    assert "tools.get_invoice" in PREPARE_OPS
    assert "tools.get_invoice" not in APPROVER_OPS


def test_ap_cannot_call_accrual_or_pay_run():
    for profile in ("prepare", "investigate"):
        for op in FORBIDDEN_AP_OPS:
            with pytest.raises(GrantError, match="forbidden"):
                assert_op_allowed("ap", profile, op)


def test_investigate_replaces_grants_and_includes_policy():
    assert grants_for("ap", "investigate") == INVESTIGATE_OPS
    assert_op_allowed("ap", "investigate", "tools.get_prior_cases")
    assert_op_allowed("ap", "prepare", "tools.get_invoice")


def test_ap_cannot_wear_ctl_pay_profile():
    with pytest.raises(GrantError):
        grants_for("ap", "review-match")
    with pytest.raises(GrantError):
        grants_for("ap", "approve")
    with pytest.raises(PermissionError, match="ctl-pay"):
        wake_bot(
            slug="ap",
            profile="review-match",
            prompt="no",
            paths=[],
            invoice_id="INV-001",
        )


def test_no_ask_user_in_ap_path():
    root = Path(__file__).resolve().parents[1]
    for rel in ("workflow.py", "agent.py", "ap_grants.py", "tools.py"):
        text = (root / rel).read_text()
        assert "ask_user(" not in text
    assert "do not call ask_user" in (root / "agent.py").read_text().lower()
    assert "Runner.run_sync" not in (root / "workflow.py").read_text()
