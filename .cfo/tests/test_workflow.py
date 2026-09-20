from __future__ import annotations

import json
from pathlib import Path

from models import (
    ApproverDecision,
    AuditResult,
    FinalAPDecision,
    InvestigationReport,
    PreparerRecommendation,
    ReviewerDecision,
)
from workflow import MAX_RECONSIDERATIONS, run_ap_workflow


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
    if kind == "reviewer":
        return ReviewerDecision(
            invoice_id=invoice_id,
            recommendation=rec,
            confidence=0.85,
            reasons=[f"reviewer {rec}"],
            objections=[],
            evidence_used=[invoice_id],
        )
    if kind == "approver":
        return ApproverDecision(
            invoice_id=invoice_id,
            decision=rec,
            confidence=0.9,
            reasons=[f"approver {rec}"],
            evidence_used=[invoice_id],
            policies_used=extra.get("policies", []),
        )
    if kind == "audit":
        passed = extra.get("passed", rec == "HOLD" or extra.get("ok", True))
        return AuditResult(
            invoice_id=invoice_id,
            passed=passed,
            findings=["audit"],
            requires_reconsideration=extra.get("requires_reconsideration", False),
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
        if agent.name == "AP Reviewer":
            return _packet(invoice_id, "reviewer", "APPROVE")
        if agent.name == "AP Approver":
            return _packet(invoice_id, "approver", "APPROVE", policies=["P-001"])
        if agent.name == "AP Audit":
            return _packet(invoice_id, "audit", "APPROVE", passed=True)
        raise AssertionError(agent.name)

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-001")
    assert "Exception Investigator" not in calls
    assert calls == ["AP Preparer", "AP Reviewer", "AP Approver", "AP Audit"]
    assert trace.investigation is None
    assert trace.final.decision == "APPROVE"
    assert trace.final.investigation_performed is False
    saved = json.loads(Path(trace.trace_path).read_text())
    assert saved["final"]["decision"] == "APPROVE"
    assert saved["trace_path"]
    roles = [item.role for item in trace.agents]
    assert roles == ["AP Preparer", "AP Reviewer", "AP Approver", "AP Audit"]
    preparer = saved["agents"][0]
    assert preparer["role"] == "AP Preparer"
    assert [item["name"] for item in preparer["skills"]] == ["three-way-match-analysis", "superseded-document-handling"]
    assert "body" not in preparer["skills"][0]
    assert preparer["skills"][0]["injected"] is True
    assert len(preparer["skills"][0]["content_hash"]) == 64


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
        if agent.name == "AP Reviewer":
            return _packet(invoice_id, "reviewer", "APPROVE")
        if agent.name == "AP Approver":
            return _packet(invoice_id, "approver", "APPROVE", policies=["P-007"])
        if agent.name == "AP Audit":
            return _packet(invoice_id, "audit", "APPROVE", passed=True)
        raise AssertionError(agent.name)

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-017")
    assert calls == [
        "AP Preparer",
        "Exception Investigator",
        "AP Reviewer",
        "AP Approver",
        "AP Audit",
    ]
    assert trace.investigation is not None
    assert trace.final.decision == "APPROVE"
    assert trace.final.investigation_performed is True


def test_mocked_duplicate_safety_net_reconsiders_once(monkeypatch, tmp_path):
    calls = []

    def fake_run(agent, prompt):
        calls.append(agent.name)
        invoice_id = "INV-018"
        if agent.name == "AP Preparer":
            return _packet(invoice_id, "preparer", "HOLD", exception_types=["duplicate"])
        if agent.name == "Exception Investigator":
            return _packet(invoice_id, "investigator", "HOLD", exception_types=["duplicate"])
        if agent.name == "AP Reviewer":
            return _packet(invoice_id, "reviewer", "APPROVE")
        if agent.name == "AP Approver":
            return _packet(invoice_id, "approver", "APPROVE")
        if agent.name == "AP Audit":
            return AuditResult(
                invoice_id=invoice_id,
                passed=True,
                findings=["model tried to pass it"],
                requires_reconsideration=False,
            )
        raise AssertionError(agent.name)

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)

    trace = run_ap_workflow("INV-018")
    assert MAX_RECONSIDERATIONS == 1
    assert calls.count("AP Approver") == 2
    assert calls.count("AP Audit") == 2
    assert trace.final.decision == "HOLD"
    assert trace.final.reconsideration_performed is True
    assert trace.reconsideration["previous"]["approver"]["decision"] == "APPROVE"
    assert trace.final.decision in {"APPROVE", "HOLD"}
    saved = json.loads(Path(trace.trace_path).read_text())
    assert saved["reconsideration"]["previous"]["approver"]["decision"] == "APPROVE"


def test_final_never_investigate(monkeypatch, tmp_path):
    def fake_run(agent, prompt):
        invoice_id = "INV-016"
        mapping = {
            "AP Preparer": _packet(invoice_id, "preparer", "INVESTIGATE", exception_types=["missing_po"]),
            "Exception Investigator": _packet(invoice_id, "investigator", "HOLD"),
            "AP Reviewer": _packet(invoice_id, "reviewer", "HOLD"),
            "AP Approver": _packet(invoice_id, "approver", "HOLD"),
            "AP Audit": _packet(invoice_id, "audit", "HOLD", passed=True),
        }
        return mapping[agent.name]

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)
    trace = run_ap_workflow("INV-016")
    assert trace.final.decision in {"APPROVE", "HOLD"}
    assert trace.preparer.recommendation == "INVESTIGATE"
    assert isinstance(trace.final, FinalAPDecision)
