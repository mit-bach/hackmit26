from __future__ import annotations

from models import (
    ApproverDecision,
    AuditResult,
    InvestigationReport,
    PreparerRecommendation,
    ReviewerDecision,
)
from invoice_ingestion.workflow import ingest_invoices
from tools import collect_case_evidence, load_invoice
from workflow import run_ap_workflow


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
            relevant_precedents=[],
            relevant_policies=[],
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
    return AuditResult(
        invoice_id=invoice_id,
        passed=extra.get("passed", True),
        findings=["audit"],
        requires_reconsideration=False,
    )


def test_ingested_helios_invoice_runs_existing_ap_workflow(monkeypatch, tmp_path):
    report = ingest_invoices("2026-09", forward_to_ap=True)
    helios = next(item for item in report.canonical_invoices if item.vendor_invoice_number == "HEL-INV-6200")
    invoice_id = helios.canonical_id
    assert load_invoice(invoice_id) is not None
    evidence = collect_case_evidence(invoice_id)
    assert evidence.exception_types == []

    def fake_run(agent, prompt):
        mapping = {
            "AP Preparer": _packet(invoice_id, "preparer", "APPROVE"),
            "AP Reviewer": _packet(invoice_id, "reviewer", "APPROVE"),
            "AP Approver": _packet(invoice_id, "approver", "APPROVE", policies=["P-001"]),
            "AP Audit": _packet(invoice_id, "audit", "APPROVE", passed=True),
        }
        if agent.name == "Exception Investigator":
            raise AssertionError("Investigator should not run on Helios three-way match")
        return mapping[agent.name]

    monkeypatch.setattr("workflow.run_agent", fake_run)
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path)
    trace = run_ap_workflow(invoice_id)
    assert trace.investigation is None
    assert trace.final.decision == "APPROVE"


def test_existing_ap_invoice_still_loads_after_ingestion():
    ingest_invoices("2026-09", forward_to_ap=True)
    assert load_invoice("INV-001").vendor == "Acme Supplies"
    assert load_invoice("INV-016").po_id is None
