"""Held-out discrepancy benchmark isolation and scoring contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from discrepancy.holdout_catalog import KNOWN_PLANTED_VALUES, holdout_contracts, holdout_ids
from evaluation.isolation import (
    AnswerKeyIsolationError,
    is_answer_key,
    operational_input_files,
    operational_phase_guard,
)
from final_eval.metrics import audit_confusion, cash_split, classify_audit_finding, close_journal_scores

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT = ROOT / "data" / "discrepancy_holdout"


def test_holdout_ids_do_not_reuse_fix_set_values():
    ids = holdout_ids()
    overlap = ids & KNOWN_PLANTED_VALUES["ids"]
    assert not overlap
    texts = " ".join(item.description for item in holdout_contracts())
    assert "12.40" not in texts
    assert "INV-1048" not in texts
    assert any("$8.37" in item.description for item in holdout_contracts())
    assert any("$41.25" in item.description for item in holdout_contracts())
    assert any("$73.90" in item.description for item in holdout_contracts())
    assert any("ABC/23781" in item.description for item in holdout_contracts())


def test_holdout_contracts_are_answer_keys():
    assert is_answer_key("holdout_contracts.json")
    assert is_answer_key("discrepancy_contracts.json")
    if HOLDOUT.exists():
        allowed = operational_input_files(HOLDOUT)
        assert not any(path.name == "holdout_contracts.json" for path in allowed)
        with operational_phase_guard():
            from tools import _read_json

            with pytest.raises(AnswerKeyIsolationError):
                _read_json(HOLDOUT / "evaluation" / "holdout_contracts.json")


def test_holdout_ap_quantity_uses_new_values():
    if not HOLDOUT.exists():
        pytest.skip("held-out dataset not generated")
    from close.orchestrator import decide_ap
    from sample_data.paths import data_root
    from tools import exception_types_for

    with data_root(HOLDOUT):
        assert "partial_receipt" in exception_types_for("INV-HO-QTY")
        assert decide_ap("INV-HO-QTY", live=False, featured=set()).decision == "HOLD"
        assert "duplicate" in exception_types_for("INV-HO-NORM-A")
        assert decide_ap("INV-HO-NORM-A", live=False, featured=set()).decision == "HOLD"


def test_close_journal_scores_require_source_fields():
    incomplete = [{"debit_account": "Cash", "credit_account": "AP", "amount": 10, "period": "2026-09"}]
    scored = close_journal_scores(incomplete)
    assert scored["close_je_accuracy"] == 0
    complete = [
        {
            "debit_account": "Insurance Expense",
            "credit_account": "Prepaid Expense",
            "amount": 1500,
            "period": "2026-09",
            "entry_type": "amortization",
            "source_document_id": "PRE-HO-001",
        }
    ]
    scored = close_journal_scores(complete)
    assert scored["close_je_accuracy"] == 1
    assert scored["close_source_traceability"] == 1


def test_audit_round_number_is_risk_indicator():
    assert classify_audit_finding({"result": "EXCEPTION", "control_id": "AUD-RND-001"}) == "RISK_INDICATOR"
    assert classify_audit_finding({"result": "FAIL", "control_id": "AUD-SOD-001"}) == "CONFIRMED_CONTROL_FAILURE"
    matrix = audit_confusion(
        [
            {"result": "FAIL", "affected_object_ids": ["APR-HO-SELF"], "control_id": "AUD-SOD-001"},
            {"result": "EXCEPTION", "affected_object_ids": ["PAY-CLEAN"], "control_id": "AUD-RND-001"},
        ],
        {"APR-HO-SELF"},
    )
    assert matrix["true_positives"] == 1
    assert matrix["false_positives_confirmed"] == 0
    assert matrix["false_positives_risk_indicator"] == 1


def test_unexplained_residual_window_is_not_demo_sized():
    from cash_recon.candidates import near_amount_window

    assert near_amount_window(1240) >= 1240
    assert near_amount_window(915000) >= 7390


def test_multiple_exact_ledger_candidates_are_not_auto_matched():
    from cash_recon.engine import propose_matches
    from cash_recon.models import BankTransaction, LedgerEntry

    bank = [
        BankTransaction(
            transaction_id="TXN-HO-MULTI",
            date="2026-09-25",
            amount=1880.0,
            amount_minor=188000,
            description="ACH REDWOOD",
            counterparty="Redwood Clinics",
            period="2026-09",
        )
    ]
    ledger = [
        LedgerEntry(
            entry_id="GL-HO-MULTI-A",
            date="2026-09-25",
            amount=1880.0,
            amount_minor=188000,
            account="Cash",
            counterparty="Redwood Clinics",
            period="2026-09",
            description="Candidate A",
        ),
        LedgerEntry(
            entry_id="GL-HO-MULTI-B",
            date="2026-09-25",
            amount=1880.0,
            amount_minor=188000,
            account="Cash",
            counterparty="Redwood Clinics",
            period="2026-09",
            description="Candidate B",
        ),
    ]
    selected = propose_matches(bank, ledger, [], "2026-09")
    exact = [item for item in selected if item.match_type == "EXACT_MATCH" and "TXN-HO-MULTI" in item.bank_transaction_ids]
    assert not exact


def test_post_close_uses_calendar_period_end():
    from audit.controls import classify_post_close
    from audit.models import AccountingPeriod, AuditJournalEntry

    period = AccountingPeriod(period="2026-09", status="CLOSED", close_timestamp="2026-10-03T18:00:00Z")
    entry = AuditJournalEntry(
        entry_id="JE-HO-POST",
        period="2026-09",
        effective_date="2026-09-30",
        posting_date="2026-10-03",
        posting_timestamp="2026-10-03T09:15:00Z",
        amount=3180.0,
        authorized=False,
    )
    assert classify_post_close(entry, period) == "UNAUTHORIZED_POST_CLOSE_ENTRY"


def test_missing_support_control_finds_flagged_payment():
    from audit.controls import run_missing_support_payments
    from audit.models import AuditPayment

    payments = [
        AuditPayment(payment_id="PAY-HO-NOSUP", amount=4110.0, vendor_id="VEND-HO", vendor_name="Pinecrest", payment_date="2026-09-17", missing_support=True),
        AuditPayment(payment_id="PAY-CLEAN", amount=100.0, vendor_id="VEND-HO", vendor_name="Pinecrest", payment_date="2026-09-17", missing_support=False),
    ]
    result = run_missing_support_payments(payments=payments, audit_run_id="TEST")
    assert result.result == "FAIL"
    assert any(item.object_id == "PAY-HO-NOSUP" for item in result.exceptions)


def test_fee_evidence_matches_on_transaction_id():
    from cash_recon.candidates import fee_candidates
    from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry

    bank = [
        BankTransaction(
            transaction_id="TXN-HO-FEE",
            date="2026-09-20",
            amount=-5028.0,
            amount_minor=-502800,
            description="WIRE VESPER NET FEE",
            counterparty="Vesper Facilities",
            period="2026-09",
        )
    ]
    ledger = [
        LedgerEntry(
            entry_id="GL-HO-FEE",
            date="2026-09-20",
            amount=-5000.0,
            amount_minor=-500000,
            counterparty="Vesper Facilities",
            period="2026-09",
        )
    ]
    fees = [
        FeeEvidence(
            evidence_id="FEE-HO-28",
            date="2026-09-20",
            amount=28.0,
            amount_minor=2800,
            reference="TXN-HO-FEE",
            description="Outbound wire fee",
        )
    ]
    rows = fee_candidates(bank, ledger, fees)
    assert any(item.match_type == "FEE_NETTED" for item in rows)


def test_reviewer_rejects_matched_when_residual_is_unexplained():
    from cash_recon.candidates import near_amount_candidates
    from cash_recon.models import BankTransaction, LedgerEntry, PreparerSelection
    from cash_recon.validate import validate_candidate
    from cash_recon.workflow import deterministic_review

    txn = BankTransaction(
        transaction_id="TXN-HO-7390",
        date="2026-09-19",
        amount=9150.0,
        amount_minor=915000,
        description="WIRE SOLSTICE",
        counterparty="Solstice Media",
        period="2026-09",
    )
    entry = LedgerEntry(
        entry_id="GL-HO-7390",
        date="2026-09-19",
        amount=9076.1,
        amount_minor=907610,
        counterparty="Solstice Media",
        period="2026-09",
    )
    candidate = near_amount_candidates([txn], [entry], [])[0]
    validation = validate_candidate(candidate, {txn.transaction_id: txn}, {entry.entry_id: entry})
    preparer = PreparerSelection(
        case_id=candidate.candidate_id,
        selected_candidate_id=candidate.candidate_id,
        disposition="MATCHED",
        confidence=0.9,
        reasons=["force match"],
        evidence_used=[],
    )
    reviewer = deterministic_review(candidate, preparer, validation, None)
    assert reviewer.disposition != "MATCHED"
    assert reviewer.human_review is True


def test_approval_threshold_control_flags_limit_breach():
    from audit.controls import run_approval_threshold_invoices
    from sample_data.paths import data_root

    if not HOLDOUT.exists():
        pytest.skip("held-out dataset not generated")
    with data_root(HOLDOUT):
        result = run_approval_threshold_invoices(audit_run_id="TEST")
    assert any(item.object_id == "INV-HO-LIMIT" for item in result.exceptions)


def test_operational_modules_do_not_read_holdout_answer_keys():
    forbidden = ("holdout_catalog", "holdout_contracts", "discrepancy_contracts", "expected_results")
    skip_parts = {"evaluation", "discrepancy", "final_eval", "tests", "sample_data", "eval.py", "demo", "evals"}
    hits = []
    for path in ROOT.rglob("*.py"):
        if any(part in path.parts or path.name in skip_parts for part in skip_parts):
            continue
        text = path.read_text()
        if any(token in text for token in forbidden):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


def test_awaiting_bank_becomes_match_when_deposit_arrives():
    from cash_recon.demo import load_demo_dataset, seed_provider_payouts
    from cash_recon.store import reset_cash_state
    from cash_recon.workflow import run_cash_reconciliation
    from sample_data.paths import data_root

    reset_cash_state()
    with data_root(ROOT / "data" / "demo"):
        seed_provider_payouts()
        balances, bank, ledger, fees = load_demo_dataset()
        report = run_cash_reconciliation(
            "2026-09",
            seed_demo=False,
            use_agent=False,
            reset=True,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=fees,
        )
    by_id = {}
    for item in report.matches:
        for bank_id in item.bank_transaction_ids:
            by_id[bank_id] = item
    refunds = by_id["TXN-2026-09-022S"]
    disputes = by_id["TXN-2026-09-026S"]
    assert refunds.match_type == "PROVIDER_PAYOUT"
    assert refunds.status == "MATCHED"
    assert disputes.match_type == "PROVIDER_PAYOUT"
    assert disputes.status == "MATCHED"


def test_cash_provider_awareness_separate_from_arithmetic():
    matches = {
        "TXN-HO-837": {"difference": 8.37, "status": "HUMAN_REVIEW"},
        "TXN-HO-STRIPE": {"difference": 180.0, "status": "MATCHED", "provider": "stripe", "evidence": ["provider:stripe"]},
    }
    split = cash_split(matches, {"TXN-HO-837": 837}, ["TXN-HO-STRIPE"])
    assert split["cash_arithmetic_accuracy"] == 1
    assert split["provider_awareness_accuracy"] == 1
