from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path

from audit.compare import compare_runs
from audit.controls import (
    classify_post_close,
    classify_round_number,
    fixture_invoice_key,
    run_duplicate_invoices,
    run_post_close_entries,
    run_round_number_payments,
    run_segregation_of_duties,
)
from audit.dataset import FALSE_POSITIVE_GUARD_IDS, clean_dataset, extra_clean_records
from audit.eval import evaluate_run
from audit.evidence import validate_run_evidence
from audit.harness import (
    mutate_add_authorization,
    mutate_formatted_duplicate,
    mutate_post_close_timestamp,
    mutate_remove_authorization,
    mutate_round_to_50000,
    mutate_round_to_manual,
    mutate_round_vendor_new,
    mutate_self_approve,
    passing_post_close_entry,
    passing_round_payment,
    passing_sod_approval,
    passing_unique_invoice,
)
from audit.history import annotate_findings, record_correction
from audit.independence import (
    independent_signatures_exclude_original,
    prove_accrual_independence,
    prove_ar_independence,
    prove_bank_independence,
    prove_stripe_independence,
    run_independence_suite,
)
from audit.models import AccountingPeriod, OperationalDecision
from audit.mutations import apply_mutations
from audit.policy import default_policy
from audit.reperformance import (
    independent_accrual_error,
    independent_ar_application,
    independent_cash_result,
    reperform_cash_match,
)
from audit.trace import evidence_chain
from audit.workflow import run_audit

ROOT = Path(__file__).resolve().parents[1]


def _ids(run) -> set[str]:
    found = set()
    for item in run.findings:
        found.update(item.affected_object_ids)
        found.update(item.payment_ids)
        found.update(item.invoice_ids)
        found.update(item.vendor_ids)
        found.update(item.approval_ids)
        found.update(item.journal_entry_ids)
        found.update(item.reconciliation_ids)
    return found


def test_adversarial_runtime_mutations_are_detected_without_labels():
    clean = clean_dataset("2026-09")
    mutated, mutations = apply_mutations(clean)
    assert {item.mutation_id for item in mutations} == {
        "corrupt_recon_status",
        "corrupt_recon_amount",
        "self_approve",
        "post_close_unauthorized",
        "duplicate_invoice_format",
        "near_duplicate_vendor",
        "round_manual_wire",
        "stripe_fee_arithmetic",
        "ar_cash_assignment",
    }
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=mutated)
    by_control = {}
    for finding in run.findings:
        by_control.setdefault(finding.control_id, set()).update(
            finding.affected_object_ids
            + finding.payment_ids
            + finding.invoice_ids
            + finding.vendor_ids
            + finding.approval_ids
            + finding.journal_entry_ids
            + finding.reconciliation_ids
        )
    for mutation in mutations:
        assert mutation.object_id in by_control.get(mutation.control_id, set()), mutation.mutation_id
    assert not any("planted" in item.description.lower() for item in mutations)
    assert validate_run_evidence(run) == []


def test_clean_baseline_does_not_flag_false_positive_guards():
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=clean_dataset("2026-09"))
    found = _ids(run)
    assert run.findings == []
    assert all(item.result == "PASS" for item in run.controls)
    assert not (found & FALSE_POSITIVE_GUARD_IDS)
    assert "PAY-AUD-003" not in found
    assert "JE-AUD-002" not in found


def test_reperformance_independence_for_each_pathway():
    assert independent_signatures_exclude_original() == []
    for name in ("original", "original_result", "planted", "original_status"):
        assert name not in inspect.signature(independent_cash_result).parameters
        assert name not in inspect.signature(independent_accrual_error).parameters
        assert name not in inspect.signature(independent_ar_application).parameters
    data = clean_dataset("2026-09")
    rows = {
        item["name"]: item
        for item in [
            prove_bank_independence(data),
            prove_stripe_independence(data),
            prove_ar_independence(data),
            prove_accrual_independence(data),
        ]
    }
    assert set(rows) == {
        "bank_reconciliation",
        "stripe_reconciliation",
        "ar_cash_application",
        "accrual_reperformance",
    }
    for item in rows.values():
        assert item["used_original_as_input"] is False
        assert item["independent_unchanged"] is True
        assert item["before_agreed"] is True
        assert item["after_agreed"] is False
        assert item["passed"] is True
    assert all(item["passed"] for item in run_independence_suite(data))


def test_round_number_control_mutations():
    payment, vendor = passing_round_payment()
    policy = default_policy()
    baseline = run_round_number_payments(
        payments=[payment], vendors=[vendor], policy=policy, audit_run_id="h1"
    )
    assert all(item.result == "PASS" or item.object_id != payment.payment_id for item in baseline.exceptions)
    hits_start = classify_round_number(payment, vendor, [], policy.round_number)
    assert hits_start[0] == "NOT_ROUND"

    amount = mutate_round_to_50000(payment)
    amount_result = run_round_number_payments(
        payments=[amount], vendors=[vendor], policy=policy, audit_run_id="h1"
    )
    amount_exc = next(item for item in amount_result.exceptions if item.object_id == amount.payment_id)
    assert amount_exc.facts["amount"] == 50000
    assert amount_exc.facts["classification"] == "SUSPICIOUS_ROUND"
    assert amount_exc.result == "EXCEPTION"

    manual = mutate_round_to_manual(amount)
    manual_result = run_round_number_payments(
        payments=[manual], vendors=[vendor], policy=policy, audit_run_id="h1"
    )
    manual_exc = next(item for item in manual_result.exceptions if item.object_id == manual.payment_id)
    assert manual_exc.facts["manual"] is True

    new_vendor = mutate_round_vendor_new(vendor)
    combo = run_round_number_payments(
        payments=[manual], vendors=[new_vendor], policy=policy, audit_run_id="h1"
    )
    combo_exc = next(item for item in combo.exceptions if item.object_id == manual.payment_id)
    assert combo_exc.facts["new_vendor"] is True
    assert combo_exc.facts["manual"] is True


def test_post_close_control_mutations():
    closed = AccountingPeriod(period="2026-09", status="CLOSED", close_timestamp="2026-10-03T18:00:00Z")
    start = passing_post_close_entry()
    assert classify_post_close(start, closed) == "PASS"
    after_close = mutate_post_close_timestamp(start)
    assert classify_post_close(after_close, closed) == "UNAUTHORIZED_POST_CLOSE_ENTRY"
    authorized = mutate_add_authorization(after_close)
    assert classify_post_close(authorized, closed) == "AUTHORIZED_POST_CLOSE_ADJUSTMENT"
    stripped = mutate_remove_authorization(authorized)
    assert classify_post_close(stripped, closed) == "UNAUTHORIZED_POST_CLOSE_ENTRY"
    journals = [
        start,
        after_close.model_copy(update={"entry_id": "JE-AFTER"}),
        authorized.model_copy(update={"entry_id": "JE-AUTH"}),
        stripped.model_copy(update={"entry_id": "JE-STRIP"}),
    ]
    result = run_post_close_entries(journals=journals, period=closed, audit_run_id="h1")
    by_id = {item.object_id: item for item in result.exceptions}
    assert start.entry_id not in by_id
    assert by_id["JE-AFTER"].result == "FAIL"
    assert by_id["JE-AUTH"].result == "PASS"
    assert by_id["JE-STRIP"].result == "FAIL"


def test_sod_control_mutation_changes_pass_to_fail():
    start = passing_sod_approval()
    policy = default_policy()
    ok = run_segregation_of_duties(approvals=[start], policy=policy, audit_run_id="h1")
    assert ok.exceptions == []
    bad = mutate_self_approve(start)
    failed = run_segregation_of_duties(approvals=[bad], policy=policy, audit_run_id="h1")
    assert failed.exceptions[0].result == "FAIL"
    assert failed.exceptions[0].facts["requester_id"] == failed.exceptions[0].facts["approver_id"]


def test_duplicate_invoice_canonical_key_catches_formatting():
    original = passing_unique_invoice()
    clone = mutate_formatted_duplicate(original)
    assert fixture_invoice_key(original) == fixture_invoice_key(clone)
    result = run_duplicate_invoices(
        audit_invoices=[original, clone],
        decisions=[
            OperationalDecision(
                object_id=original.invoice_id,
                object_type="invoice",
                workflow="ap",
                decision="APPROVE",
                duplicate_detected=False,
            ),
            OperationalDecision(
                object_id=clone.invoice_id,
                object_type="invoice",
                workflow="ap",
                decision="APPROVE",
                duplicate_detected=False,
            ),
        ],
        audit_run_id="h1",
    )
    failed = {item.object_id for item in result.exceptions if item.result == "FAIL"}
    assert original.invoice_id in failed
    assert clone.invoice_id in failed


def test_false_positive_protection_cases():
    extra = extra_clean_records()
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=clean_dataset("2026-09"))
    found = _ids(run)
    assert "PAY-AUD-003" not in found
    assert "JE-AUD-002" not in found
    assert "APR-CLEAN-SOD" not in found
    assert "VEND-NORTHSTAR" not in found
    assert "VEND-HELIOS" not in found
    assert "INV-CLEAN-SAMEAMT-A" not in found
    assert "INV-CLEAN-SAMEAMT-B" not in found
    assert extra["approvals"][0].requester_id != extra["approvals"][0].approver_id
    assert extra["approvals"][0].requester_id.startswith("USR-JANE")
    assert extra["approvals"][0].approver_id.startswith("USR-JANE")


def test_recon_difference_inside_tolerance_is_not_a_finding():
    data = clean_dataset("2026-09")
    item = next(row for row in data.reconciliations if row.reconciliation_id == "REC-AUD-AGREE")
    item.original_difference = 0.005
    record = reperform_cash_match(item, data.bank, data.ledger, data.fees, audit_run_id="tol")
    assert record.agreed is True
    assert record.used_original_as_input is False


def test_evidence_validator_rejects_incomplete_findings():
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False)
    assert validate_run_evidence(run) == []
    run.findings[0].evidence_ids = []
    run.findings[0].facts = {}
    assert validate_run_evidence(run)


def test_cross_workflow_trace_uses_existing_ids():
    data = clean_dataset("2026-09")
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=data)
    chain = evidence_chain(data, run)
    assert chain["invoice_id"] == "INV-AUD-OK-001"
    assert "APR-AUD-001" in chain["approval_ids"]
    assert "PAY-AUD-001" in chain["payment_ids"]
    assert "AUD-BNK-001" in chain["bank_ids"]
    assert "AUD-LED-001" in chain["ledger_ids"]
    assert "REC-AUD-AGREE" in chain["reconciliation_ids"]
    assert chain["complete"] is True


def test_audit_run_comparison_and_recurring_correction():
    clean = clean_dataset("2026-09")
    mutated, _mutations = apply_mutations(clean, ["self_approve", "round_manual_wire"])
    first = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=mutated)
    sod = next(item for item in first.findings if item.control_id == "AUD-SOD-001")
    rnd = next(item for item in first.findings if item.control_id == "AUD-RND-001")
    sod_corr = record_correction(
        issue_key=sod.issue_key,
        object_id=sod.affected_object_ids[0],
        control_id=sod.control_id,
        finding_id=sod.finding_id,
        notes="Approver restored.",
    )
    record_correction(
        issue_key=rnd.issue_key,
        object_id=rnd.affected_object_ids[0],
        control_id=rnd.control_id,
        finding_id=rnd.finding_id,
        notes="Wire left in place.",
    )
    from audit.mutations import restore_mutation

    second_data = restore_mutation(mutated.copy(), "self_approve")
    second_data.corrections = [sod_corr]
    # Second run still sees the round-number breach and the recorded SOD correction.
    from audit.history import load_corrections

    second_data.corrections = load_corrections()
    second = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=second_data)
    comparison = compare_runs(first, second)
    assert sod.issue_key in comparison.findings_resolved
    assert rnd.issue_key in comparison.findings_still_open
    assert any(item.issue_key == rnd.issue_key and item.recurring for item in second.findings)
    assert not any(item.control_id == "AUD-SOD-001" for item in second.findings)

    # Same SOD breach again is a repeat finding; controls are unchanged.
    third_data = second_data.copy()
    third_data.approvals = mutated.approvals
    third = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=third_data)
    repeat = next(item for item in third.findings if item.control_id == "AUD-SOD-001")
    assert repeat.recurring is True
    assert repeat.prior_correction_id == sod_corr.correction_id
    annotated = annotate_findings(list(first.findings), [sod_corr])
    assert any(item.recurring for item in annotated)


def test_evaluation_metrics_are_computed_from_execution():
    clean = clean_dataset("2026-09")
    mutated, mutations = apply_mutations(clean)
    run = run_audit("2026-09", seed=26, use_agent=False, persist=False, dataset=mutated)
    independence = run_independence_suite(clean)
    chain = evidence_chain(clean, run)
    metrics = evaluate_run(
        run,
        {"planted_exceptions": [], "expected_pass": []},
        mutations=mutations,
        independence=independence,
        trace=chain,
    )
    assert metrics.runtime_mutations_injected == len(mutations)
    assert metrics.mutations_detected == len(mutations)
    assert metrics.mutation_detection_rate == 1.0
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.reperformance_independence_passed == metrics.reperformance_independence_total == 4
    assert metrics.evidence_complete_findings == metrics.evidence_total_findings
    assert metrics.evidence_total_findings == len(run.findings)
    assert metrics.cross_workflow_trace_complete is True


def test_adversarial_demo_cli_runs_without_api_key():
    env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "audit-demo", "--adversarial", "--period", "2026-09", "--seed", "26"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    for section in (
        "BASELINE",
        "RUNTIME MUTATIONS",
        "AUDIT SAMPLE",
        "CONTROL RESULTS",
        "RE-PERFORMANCE DISAGREEMENTS",
        "FINDINGS",
        "EVIDENCE TRACE",
        "AFTER CORRECTION",
        "EVALUATION",
    ):
        assert section in output
    assert "INV-AUD-OK-001" in output
    assert "used_original_as_input=False" in output
