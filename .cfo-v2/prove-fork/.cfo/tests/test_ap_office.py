"""Prompt 03 AP office: Kernel bill intake, must_hold, pay-run Handles, memory.

These tests are Kernel hosts plus Harness Handle files. They are not office-live
Pi on 8800. RUN.md is not rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ap_intake import land_email_bill
from inbox.fixtures import spec_acme_inv001
from models import Invoice, PaymentAuditResult
from scheduling.cash import apply_cash_and_policy_net, payment_candidate, policy_eligible_for_pool
from scheduling.host import apply_review_pay_concurrence
from scheduling.pool import seed_demo_pool
from scheduling.workflow import run_schedule_workflow
from tools import (
    collect_case_evidence,
    invoice_lookup,
    register_runtime_invoice,
    vendor_alias_established,
)
from workflow import must_hold, run_ap_kernel


def _learn_invoice(invoice_id: str, vin: str, *, invoice_date: str, due_date: str) -> Invoice:
    return Invoice(
        invoice_id=invoice_id,
        vendor="Amazon Web Service",
        po_id="PO-102",
        amount=8320,
        invoice_date=invoice_date,
        due_date=due_date,
        vendor_invoice_number=vin,
        description="Runtime alias bill. Not a prior_cases.json edit.",
        payment_terms="net 30",
        late_fee_percent=1.5,
        vendor_priority="high",
    )


def test_email_lands_canonical_inv001_get_invoice_finds_it(tmp_path, monkeypatch):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path / "runs")
    computer = tmp_path / "computer"
    landed = land_email_bill(spec_acme_inv001(), computer_root=computer, persist=False)
    assert landed["invoice_id"] == "INV-001"
    assert landed["found"] is True
    lookup = invoice_lookup("INV-001")
    assert lookup["found"] is True
    assert lookup["invoice"]["vendor_invoice_number"] == "ACM-2026-4410"
    assert lookup["invoice"]["po_id"] == "PO-101"
    handle = landed["email_ap_handle"]
    assert handle["toSlug"] == "ap"
    assert handle["profile"] == "prepare"
    assert handle["done"] is False
    assert handle["status"] == "accepted"
    dest = Path(landed["email_ap_handle_path"])
    assert dest.is_file()
    assert dest.parent.name == "handles"
    assert dest.parents[1].name == "bot_ap"
    packet = json.loads(Path(landed["match_trace"].packet_path).read_text())
    assert packet["invoice_id"] == "INV-001"
    assert packet["kernel_holds"] == []
    assert packet["proposed_decision"] == "APPROVE"
    assert landed["match_trace"].verifier_handle is not None
    assert landed["match_trace"].verifier_handle["toSlug"] == "ctl-pay"
    assert landed["match_trace"].verifier_handle["profile"] == "review-match"
    ctl_files = list((computer / "harness" / "bots" / "bot_ctl_pay" / "handles").glob("*.json"))
    assert ctl_files
    ctl = json.loads(ctl_files[0].read_text())
    assert ctl["fromSlug"] == "ap"
    assert ctl["profile"] == "review-match"
    assert "kernel_holds" in json.dumps(packet)


def test_dual_intake_does_not_mint_a_second_kernel_id(tmp_path, monkeypatch):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path / "runs")
    computer = tmp_path / "computer"
    first = land_email_bill(spec_acme_inv001(), computer_root=computer, persist=False, match=False)
    second = land_email_bill(spec_acme_inv001(), computer_root=computer, persist=False, match=False)
    assert first["invoice_id"] == "INV-001"
    assert second["invoice_id"] == "INV-001"
    assert invoice_lookup("INV-001")["found"] is True


def test_inv_s12_marker_is_not_a_kernel_invoice():
    lookup = invoice_lookup("INV-S12")
    assert lookup["found"] is False
    assert "not found" in lookup["error"].lower()


def test_hold_invoice_absent_from_pay_this_week():
    assert policy_eligible_for_pool("INV-018") is False
    evidence = collect_case_evidence("INV-018")
    assert "duplicate" in evidence.exception_types
    assert must_hold(evidence)
    plan = apply_cash_and_policy_net(
        [payment_candidate("INV-002"), payment_candidate("INV-018")],
        ["INV-018", "INV-002"],
    )
    paid = {row.invoice_id for row in plan.pay_this_week}
    assert "INV-018" not in paid
    assert "INV-002" in paid


def test_run_ap_kernel_does_not_call_runner(tmp_path, monkeypatch):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path / "runs")

    def boom(*_args, **_kwargs):
        raise AssertionError("run_ap_kernel must not call run_agent / Runner")

    monkeypatch.setattr("workflow.run_agent", boom)
    computer = tmp_path / "computer"
    trace = run_ap_kernel("INV-001", computer_root=computer)
    assert trace.final.decision == "APPROVE"
    assert must_hold(trace.deterministic_evidence) == []
    assert trace.verifier_handle["toSlug"] == "ctl-pay"
    assert trace.agents == []


def test_unreceived_period_work_handles_close_not_approval(tmp_path, monkeypatch):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path / "runs")
    computer = tmp_path / "computer"
    trace = run_ap_kernel("INV-015", computer_root=computer)
    assert trace.deterministic_evidence.receipt_status == "not_received"
    assert any("P-004" in item for item in trace.kernel_holds)
    assert trace.final.decision == "HOLD"
    assert trace.verifier_handle is None
    assert trace.close_handle is not None
    assert trace.close_handle["toSlug"] == "close"
    assert trace.close_handle["profile"] == "coordinate"
    assert trace.close_handle["approval"] is False
    close_files = list((computer / "harness" / "bots" / "bot_close" / "handles").glob("*.json"))
    assert close_files
    payload = json.loads(close_files[0].read_text())
    assert payload["fromSlug"] == "ap"
    assert payload["toSlug"] == "close"
    assert payload["approval"] is False
    assert "not approval" in payload["prompt"].lower()


def test_payment_run_handle_to_ctl_pay_then_cash_executed_false(tmp_path):
    seed_demo_pool()
    computer = tmp_path / "computer"
    trace = run_schedule_workflow(computer_root=computer, runs_dir=tmp_path / "runs")
    paid = {row.invoice_id for row in trace.plan.pay_this_week}
    assert "INV-018" not in paid
    assert "INV-009" not in paid
    handles = list((computer / "harness" / "bots" / "bot_ctl_pay" / "handles").glob("*.json"))
    assert handles
    wake = json.loads(handles[0].read_text())
    assert wake["fromSlug"] == "pay"
    assert wake["toSlug"] == "ctl-pay"
    assert wake["profile"] == "review-pay"
    assert wake["status"] == "accepted"
    assert wake["done"] is False
    assert wake["op"] == "bot_send_prompt"
    packet = json.loads(Path(trace.plan_packet_path).read_text())
    assert packet["executed"] is False
    result = apply_review_pay_concurrence(
        plan_packet_path=Path(trace.plan_packet_path),
        concurrence=PaymentAuditResult(
            passed=True, findings=["Kernel reserve_ok and packet complete"]
        ),
        source_slug="ctl-pay",
        computer_root=computer,
    )
    assert result["executed"] is False
    cash_handles = list((computer / "harness" / "bots" / "bot_cash" / "handles").glob("*.json"))
    assert cash_handles
    cash = json.loads(cash_handles[0].read_text())
    assert cash["toSlug"] == "cash"
    assert cash["executed"] is False
    outflows = json.loads(Path(result["outflow_packet_path"]).read_text())
    assert outflows["executed"] is False


def test_operational_alias_memory_without_editing_prior_cases(tmp_path, monkeypatch):
    monkeypatch.setattr("workflow.RUNS_DIR", tmp_path / "runs")
    prior = Path(__file__).resolve().parents[1] / "data" / "prior_cases.json"
    before = prior.read_text()
    computer = tmp_path / "computer"
    first = _learn_invoice(
        "INV-LEARN-A", "AWS-LEARN-001", invoice_date="2026-09-12", due_date="2026-10-12"
    )
    second = _learn_invoice(
        "INV-LEARN-B", "AWS-LEARN-002", invoice_date="2026-10-05", due_date="2026-11-04"
    )
    dup = _learn_invoice(
        "INV-LEARN-DUP", "AWS-LEARN-001", invoice_date="2026-09-20", due_date="2026-10-20"
    )
    register_runtime_invoice(first)
    evidence_a = collect_case_evidence("INV-LEARN-A")
    assert "vendor_mismatch" in evidence_a.exception_types
    assert evidence_a.vendors_are_similar is True
    assert vendor_alias_established(evidence_a) is False
    assert any("P-006" in item for item in must_hold(evidence_a))
    trace_a = run_ap_kernel("INV-LEARN-A", computer_root=computer)
    assert trace_a.final.decision == "HOLD"
    assert trace_a.written_memory_id
    assert vendor_alias_established(collect_case_evidence("INV-LEARN-A")) is True
    register_runtime_invoice(second)
    evidence_b = collect_case_evidence("INV-LEARN-B")
    assert vendor_alias_established(evidence_b) is True
    assert must_hold(evidence_b) == []
    trace_b = run_ap_kernel("INV-LEARN-B", computer_root=computer)
    assert trace_b.final.decision == "APPROVE"
    assert trace_b.memory_lookup is not None
    assert trace_b.memory_lookup.retrieved
    assert trace_b.memory_lookup.precedent_used is True
    assert trace_b.verifier_handle is not None
    register_runtime_invoice(dup)
    evidence_dup = collect_case_evidence("INV-LEARN-DUP")
    assert "duplicate" in evidence_dup.exception_types
    assert vendor_alias_established(evidence_dup) is True
    holds = must_hold(evidence_dup)
    assert any("P-002" in item for item in holds)
    trace_dup = run_ap_kernel("INV-LEARN-DUP", computer_root=computer)
    assert trace_dup.final.decision == "HOLD"
    assert prior.read_text() == before


def test_ctl_pay_grants_keep_denylist_no_record_tools():
    from verifier.grants import RECORD_TOOLS, VerifierGrantError, assert_op_allowed

    assert_op_allowed("ctl-pay", "review-match", "tools.get_case_evidence")
    for op in RECORD_TOOLS:
        with pytest.raises(VerifierGrantError):
            assert_op_allowed("ctl-pay", "review-match", op)
        with pytest.raises(VerifierGrantError):
            assert_op_allowed("ctl-pay", "review-pay", op)
    grants = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / ".cfo-v2"
            / "office"
            / "computer"
            / "cfo"
            / "grants.json"
        ).read_text()
    )
    reviewer = grants["byDisplayName"]["AP Reviewer"]
    assert "tools.get_case_evidence" in reviewer["ops"]
    assert "tools.get_invoice" not in reviewer["ops"]
    audit = grants["byDisplayName"]["Payment Audit"]
    assert "scheduling.tools.get_payment_candidates" not in audit["ops"]
    assert "payment-prioritization" not in (audit.get("skills") or [])
    assert "early-payment-discount-evaluation" not in (audit.get("skills") or [])
