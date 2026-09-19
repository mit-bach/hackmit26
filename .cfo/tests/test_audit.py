from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from audit.controls import (
    classify_post_close,
    classify_round_number,
    is_round_amount,
    run_duplicate_invoices,
    run_duplicate_vendors,
    run_post_close_entries,
    run_round_number_payments,
    run_segregation_of_duties,
)
from audit.eval import evaluate_run
from audit.findings import assign_severity
from audit.models import (
    AccountingPeriod,
    AuditApproval,
    AuditJournalEntry,
    AuditPayment,
    AuditVendor,
    ControlException,
    PopulationItem,
)
from audit.policy import AuditPolicy, RoundNumberPolicy, SodPolicy, SodRule, default_policy
from audit.reperformance import reperform_accrual, reperform_cash_match
from audit.report import compute_stats, format_audit_report
from audit.sampling import sample_population
from audit.store import (
    load_invoices,
    load_operational_decisions,
    load_planted_reconciliations,
    load_recon_source,
    load_vendors,
)
from audit.workflow import run_audit
from tools import has_duplicate_vendor_invoice_number, load_duplicate_invoices

ROOT = Path(__file__).resolve().parents[1]


def _item(object_id: str, amount: float = 0, **attrs) -> PopulationItem:
    return PopulationItem(object_id=object_id, object_type="payment", amount=amount, attributes=attrs)


def test_random_sample_is_reproducible_and_seed_sensitive():
    population = [_item(f"TX-{index:03d}", amount=100 + index) for index in range(20)]
    first = sample_population(
        population, sample_size=5, method="random", seed=26, audit_run_id="r1", period="2026-09", population_name="tx"
    )
    second = sample_population(
        population, sample_size=5, method="random", seed=26, audit_run_id="r1", period="2026-09", population_name="tx"
    )
    other = sample_population(
        population, sample_size=5, method="random", seed=99, audit_run_id="r1", period="2026-09", population_name="tx"
    )
    known = {item.object_id for item in population}
    assert first.sampled_ids == second.sampled_ids
    assert first.eligible_ids == [item.object_id for item in population]
    assert first.population_size == 20
    assert first.seed == 26
    assert set(first.sampled_ids) <= known
    assert first.sampled_ids != other.sampled_ids


def test_risk_sample_selects_planted_high_risk_records():
    population = [
        _item("SAFE-1", 200),
        _item("SAFE-2", 300),
        _item("RISK-1", 50000, round_number=True, new_vendor=True, self_approval=True),
        _item("RISK-2", 15000, posted_after_close=True, control_failure=True),
    ]
    sample = sample_population(
        population,
        sample_size=2,
        method="risk_based",
        seed=1,
        audit_run_id="r1",
        period="2026-09",
        population_name="tx",
    )
    assert set(sample.sampled_ids) == {"RISK-1", "RISK-2"}
    assert sample.risk_scores["RISK-1"] > 0
    replay = sample_population(
        population,
        sample_size=2,
        method="risk_based",
        seed=1,
        audit_run_id="r1",
        period="2026-09",
        population_name="tx",
    )
    assert replay.sampled_ids == sample.sampled_ids
    assert replay.risk_scores == sample.risk_scores


def test_round_number_control_flags_expected_cases():
    vendors = [
        AuditVendor(vendor_id="VEND-ACME", vendor_name="Acme Supplies", first_seen="2024-01-15"),
        AuditVendor(vendor_id="VEND-NEWCO", vendor_name="Northwind Phantom LLC", first_seen="2026-09-15", unusual=True),
        AuditVendor(vendor_id="VEND-FIGMA", vendor_name="Figma", first_seen="2023-03-01"),
    ]
    payments = [
        AuditPayment(
            payment_id="PAY-OK",
            amount=1247.33,
            vendor_id="VEND-ACME",
            vendor_name="Acme Supplies",
            payment_date="2026-09-12",
            source="automated",
        ),
        AuditPayment(
            payment_id="PAY-SUSP",
            amount=50000,
            vendor_id="VEND-NEWCO",
            vendor_name="Northwind Phantom LLC",
            payment_date="2026-09-20",
            source="manual",
            payment_method="wire",
        ),
        AuditPayment(
            payment_id="PAY-SAAS",
            amount=100,
            vendor_id="VEND-FIGMA",
            vendor_name="Figma",
            payment_date="2026-09-08",
            source="automated",
            recurring=True,
        ),
    ]
    result = run_round_number_payments(
        payments=payments, vendors=vendors, policy=default_policy(), audit_run_id="r1"
    )
    by_id = {item.object_id: item for item in result.exceptions}
    assert "PAY-OK" not in by_id
    assert by_id["PAY-SUSP"].result == "EXCEPTION"
    assert by_id["PAY-SUSP"].facts["round_number_divisors"] == [100.0, 1000.0, 10000.0]
    assert by_id["PAY-SUSP"].facts["new_vendor"] is True
    assert by_id["PAY-SUSP"].facts["manual"] is True
    assert by_id["PAY-SAAS"].result == "PASS"
    assert by_id["PAY-SAAS"].facts["ordinary"] is True
    assert is_round_amount(1247.33, [100, 1000, 10000]) == []


def test_round_number_thresholds_are_configurable():
    payment = AuditPayment(
        payment_id="PAY-100",
        amount=100,
        vendor_id="VEND-FIGMA",
        vendor_name="Figma",
        payment_date="2026-09-08",
        source="automated",
        recurring=True,
    )
    vendor = AuditVendor(vendor_id="VEND-FIGMA", vendor_name="Figma", first_seen="2023-03-01")
    tight = AuditPolicy(round_number=RoundNumberPolicy(divisors=[10000], min_amount=100))
    result = run_round_number_payments(
        payments=[payment], vendors=[vendor], policy=tight, audit_run_id="r1"
    )
    assert result.exceptions == []
    assert classify_round_number(payment, vendor, [100.0], RoundNumberPolicy())[1] is True


def test_post_close_classifications():
    closed = AccountingPeriod(period="2026-09", status="CLOSED", close_timestamp="2026-10-03T18:00:00Z")
    missing = AccountingPeriod(period="2026-08", status="OPEN")
    pre = AuditJournalEntry(
        entry_id="JE-PRE",
        period="2026-09",
        effective_date="2026-09-28",
        posting_date="2026-09-28",
        posting_timestamp="2026-09-28T10:00:00Z",
        amount=100,
    )
    authorized = AuditJournalEntry(
        entry_id="JE-AUTH",
        period="2026-09",
        effective_date="2026-09-30",
        posting_date="2026-10-04",
        posting_timestamp="2026-10-04T12:00:00Z",
        amount=250,
        authorization_id="AUTH-1",
        authorized=True,
    )
    unauthorized = AuditJournalEntry(
        entry_id="JE-BAD",
        period="2026-09",
        effective_date="2026-09-30",
        posting_date="2026-10-05",
        posting_timestamp="2026-10-05T09:00:00Z",
        amount=15000,
        authorized=False,
    )
    memo_only = AuditJournalEntry(
        entry_id="JE-MEMO",
        period="2026-09",
        effective_date="2026-09-30",
        posting_date="2026-10-05",
        posting_timestamp="2026-10-05T09:00:00Z",
        amount=100,
        memo="authorized post-close adjustment",
        authorized=False,
        authorization_id=None,
    )
    assert classify_post_close(pre, closed) == "PASS"
    assert classify_post_close(authorized, closed) == "AUTHORIZED_POST_CLOSE_ADJUSTMENT"
    assert classify_post_close(unauthorized, closed) == "UNAUTHORIZED_POST_CLOSE_ENTRY"
    assert classify_post_close(memo_only, closed) == "UNAUTHORIZED_POST_CLOSE_ENTRY"
    assert classify_post_close(pre, missing) == "HUMAN_REVIEW"
    result = run_post_close_entries(
        journals=[pre, authorized, unauthorized], period=closed, audit_run_id="r1"
    )
    by_id = {item.object_id: item for item in result.exceptions}
    assert "JE-PRE" not in by_id
    assert by_id["JE-AUTH"].result == "PASS"
    assert by_id["JE-BAD"].result == "FAIL"


def test_self_approval_policy():
    policy = default_policy()
    separated = AuditApproval(
        approval_id="APR-OK",
        object_type="invoice",
        object_id="INV-1",
        requester_id="U1",
        reviewer_id="U2",
        approver_id="U3",
        amount=100,
    )
    same = AuditApproval(
        approval_id="APR-BAD",
        object_type="invoice",
        object_id="INV-2",
        requester_id="U1",
        reviewer_id="U2",
        approver_id="U1",
        amount=100,
    )
    missing = AuditApproval(
        approval_id="APR-MISS",
        object_type="invoice",
        object_id="INV-3",
        requester_id="U1",
        reviewer_id="U2",
        approver_id=None,
        amount=100,
    )
    result = run_segregation_of_duties(
        approvals=[separated, same, missing], policy=policy, audit_run_id="r1"
    )
    by_id = {item.object_id: item for item in result.exceptions}
    assert "APR-OK" not in by_id
    assert by_id["APR-BAD"].result == "FAIL"
    assert by_id["APR-BAD"].facts["violated_rule"] == "SOD-001"
    assert by_id["APR-MISS"].result == "HUMAN_REVIEW"
    permissive = AuditPolicy(
        sod=SodPolicy(
            rules=[
                SodRule(
                    rule_id="SOD-NONE",
                    object_types=["journal"],
                    forbidden_pairs=[("preparer_id", "approver_id")],
                    policy_reference="X",
                )
            ]
        )
    )
    skipped = run_segregation_of_duties(approvals=[same], policy=permissive, audit_run_id="r1")
    assert skipped.exceptions == []


def test_duplicate_controls_reuse_existing_detectors():
    assert has_duplicate_vendor_invoice_number("INV-010")
    assert "INV-018" in [item.invoice_id for item in load_duplicate_invoices("INV-010")]
    result = run_duplicate_invoices(
        audit_invoices=load_invoices(),
        decisions=load_operational_decisions(),
        audit_run_id="r1",
    )
    failed = {item.object_id: item for item in result.exceptions if item.result == "FAIL"}
    assert "AUD-INV-MISS-1" in failed
    assert "AUD-INV-MISS-2" in failed
    assert "INV-010" not in failed
    assert "INV-018" not in failed
    vendors = run_duplicate_vendors(
        vendors=load_vendors(), decisions=load_operational_decisions(), audit_run_id="r1"
    )
    assert any(item.object_id == "VEND-ACME" and item.result == "FAIL" for item in vendors.exceptions)


def test_reperformance_agrees_and_detects_planted_error():
    planted = {item.reconciliation_id: item for item in load_planted_reconciliations()}
    bank, ledger, fees = load_recon_source()
    agree = reperform_cash_match(planted["REC-AUD-AGREE"], bank, ledger, fees, audit_run_id="r1")
    disagree = reperform_cash_match(planted["REC-AUD-DISAGREE"], bank, ledger, fees, audit_run_id="r1")
    assert agree.agreed is True
    assert agree.result == "PASS"
    assert agree.used_original_as_input is False
    assert "original_status" not in json.dumps(agree.independent_result)
    assert disagree.agreed is False
    assert disagree.result == "FAIL"
    assert disagree.independent_result["match_type"] != planted["REC-AUD-DISAGREE"].original_match_type or (
        disagree.independent_result["difference"] != 0
    )
    accrual_ok = reperform_accrual(planted["REC-AUD-ACCRUAL-AGREE"], audit_run_id="r1")
    accrual_bad = reperform_accrual(planted["REC-AUD-ACCRUAL-DISAGREE"], audit_run_id="r1", tolerance=0.01)
    assert accrual_ok.agreed is True
    assert accrual_bad.agreed is False
    wide = reperform_accrual(planted["REC-AUD-ACCRUAL-DISAGREE"], audit_run_id="r1", tolerance=500)
    assert wide.agreed is True


def test_findings_and_report_counts_stay_linked():
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False)
    failed_controls = [item for item in run.controls if item.result == "FAIL"]
    assert failed_controls
    assert all(item.finding_id.startswith("FND-") for item in run.findings)
    assert all(item.affected_object_ids and item.evidence_ids for item in run.findings)
    assert all(item.control_id for item in run.findings)
    ordinary = next(item for item in run.controls if item.control_id == "AUD-RND-001")
    assert not any(exc.object_id == "PAY-AUD-001" and exc.result != "PASS" for exc in ordinary.exceptions)
    assert not any("PAY-AUD-001" in item.affected_object_ids for item in run.findings)
    assert any("PAY-AUD-002" in item.affected_object_ids for item in run.findings)
    assert run.stats.finding_count == len(run.findings)
    assert run.stats.passed == sum(1 for item in run.controls if item.result == "PASS")
    assert run.stats.failed == sum(1 for item in run.controls if item.result == "FAIL")
    report = format_audit_report(run)
    assert str(run.stats.finding_count) in report
    assert run.findings[0].finding_id in report
    exposures = [item.monetary_exposure for item in run.findings if item.affected_object_ids == ["PAY-AUD-002"]]
    assert exposures and exposures[0] == 50000
    assert run.source_records_mutated is False


def test_severity_is_not_automatically_high():
    policy = default_policy().severity
    low = ControlException(
        object_id="X",
        object_type="payment",
        result="EXCEPTION",
        detail="small",
        facts={"new_vendor": False, "manual": False},
        monetary_exposure=100,
    )
    high = ControlException(
        object_id="Y",
        object_type="journal_entry",
        result="FAIL",
        detail="post-close",
        monetary_exposure=15000,
    )
    assert assign_severity("AUD-RND-001", low, policy)[0] == "MEDIUM"
    assert assign_severity("AUD-PCE-001", high, policy)[0] == "CRITICAL"


def test_full_audit_eval_catches_planted_cases():
    invoices_before = (ROOT / "data" / "invoices.json").read_text()
    run = run_audit("2026-09", seed=26, use_agent=False, persist=True)
    assert (ROOT / "data" / "invoices.json").read_text() == invoices_before
    metrics = evaluate_run(run)
    assert metrics.planted_exceptions == 10
    assert metrics.false_negatives == 0
    assert metrics.control_detection_rate == 1.0
    assert metrics.reperformance_agreement_accuracy == 1.0
    assert metrics.evidence_link_completeness == 1.0
    assert set(metrics.detected_ids) == set(metrics.planted_ids)
    assert run.interpretation is not None
    assert "AUD-RND-001" in run.interpretation.what_was_tested
    assert run.agents
    assert run.agents[0].role == "Auditor Agent"
    assert [item.name for item in run.agents[0].skills] == [
        "audit-sampling-interpretation",
        "control-testing-interpretation",
        "reconciliation-reperformance-review",
        "segregation-of-duties-interpretation",
    ]
    assert any(item.reconciliation_id == "REC-AUD-AGREE" and item.agreed for item in run.reperformance)
    assert any(item.reconciliation_id == "REC-AUD-DISAGREE" and not item.agreed for item in run.reperformance)
    assert compute_stats(run).finding_ids == [item.finding_id for item in run.findings]


def test_audit_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "audit-demo", "--period", "2026-09", "--seed", "26"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "INDEPENDENT AUDITOR DEMO" in result.stdout
    assert "We ran the finance workflow first" in result.stdout
    assert "PAY-AUD-002" in result.stdout
    assert "REC-AUD-DISAGREE" in result.stdout
    assert "Control detection rate: 100.00%" in result.stdout
