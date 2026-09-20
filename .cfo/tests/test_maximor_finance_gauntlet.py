"""Maximor Finance Gauntlet: production workflows, hidden answers."""

from __future__ import annotations

from pathlib import Path

from evaluation.isolation import AnswerKeyIsolationError, operational_phase_guard
from evals.maximor_finance_gauntlet.runner import run_gauntlet
from invoice_ingestion.traps import analyze_document
from cash_recon.evidence import amount_only_match, economic_link_supported
from cash_recon.models import BankTransaction, LedgerEntry
from cash_recon.normalize import prepare_bank, prepare_ledger
from cfo.recovery import recover_or_skip, replay_event


GAUNTLET = Path(__file__).resolve().parents[1] / "evals" / "maximor_finance_gauntlet"


def test_private_answers_are_blocked_in_operational_phase():
    gold = GAUNTLET / "private_answers" / "documents.py"
    with operational_phase_guard():
        with __import__("pytest").raises(AnswerKeyIsolationError):
            from evaluation.isolation import assert_operational_read_allowed

            assert_operational_read_allowed(gold)


def test_operational_modules_do_not_import_private_answers():
    forbidden = []
    root = Path(__file__).resolve().parents[1]
    skip = {"evals/maximor_finance_gauntlet/private_answers", "evals/maximor_finance_gauntlet/runner.py", "evals/maximor_finance_gauntlet/modes.py"}
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("evals/maximor_finance_gauntlet/private_answers"):
            continue
        if rel in skip or rel.startswith("tests/"):
            continue
        if "maximor_finance_gauntlet/runner" in rel:
            continue
        text = path.read_text()
        if "maximor_finance_gauntlet.private_answers" in text and "evaluation_phase" not in text:
            forbidden.append(rel)
    assert forbidden == []


def test_void_and_stripe_payout_are_not_payables():
    voided = analyze_document(
        "INVOICE\nVendor: Harbor Electric\nInvoice number: HE-4402\nInvoice date: 2026-09-07\nAmount due: 199.00\nVOIDED INVOICE — do not pay this invoice\n"
    )
    assert voided.classification == "not_invoice"
    assert voided.payable is False
    stripe = analyze_document("STRIPE PAYOUT po_1MaximorFees settled to bank. Automatic payout. This is not a vendor invoice.")
    assert stripe.classification == "not_invoice"
    assert stripe.payable is False


def test_revision_extracts_superseded_number():
    analysis = analyze_document(
        "INVOICE\nVendor: Harbor Electric\nInvoice number: HE-4401-R\nInvoice date: 2026-09-06\nAmount due: 4300.00\nThis invoice replaces invoice HE-4401\n"
    )
    assert analysis.classification == "invoice"
    assert analysis.supersedes == "HE-4401"
    assert "revised_invoice" in analysis.flags


def test_amount_only_is_not_economic_linkage():
    bank = prepare_bank(
        [BankTransaction.model_validate({"transaction_id": "B", "date": "2026-09-12", "amount": -5000, "description": "ACH OUT ORBIT", "counterparty": "ORBIT ANALYTICS", "period": "2026-09"})]
    )[0]
    ledger = prepare_ledger(
        [LedgerEntry.model_validate({"entry_id": "L", "date": "2026-09-12", "amount": -5000, "counterparty": "Quiet Harbor Capital", "reference": "QH-99", "period": "2026-09"})]
    )[0]
    assert amount_only_match(bank, ledger) is True
    assert economic_link_supported(bank, ledger).supported is False


def test_recovery_does_not_invent_records():
    result = recover_or_skip("{bad", kind="json")
    assert result["ok"] is False
    assert result["invented"] is False
    seen: set[str] = set()
    assert replay_event("evt_1", seen)[1] is True
    assert replay_event("evt_1", seen)[0] == "duplicate_ignored"


def test_gauntlet_core_families_run():
    payload = run_gauntlet(include_existing=False, memory_enabled=True, shared_state=True)
    card = payload["scorecard"]
    assert card["total_scenarios"] >= 20
    by_family = card["by_family"]
    for family in ("documents", "cash", "questions", "rubrics", "consistency", "long_horizon", "recovery"):
        assert family in by_family, family
        assert by_family[family]["total"] >= 1
    failed = [item for item in payload["cases"] if not item["passed"]]
    assert failed == [], failed


def test_gauntlet_modes_use_real_configuration_switches():
    from evals.maximor_finance_gauntlet.modes import run_modes

    payload = run_modes(include_existing=False)
    by_id = {item["mode_id"]: item for item in payload["modes"]}
    assert by_id["B"]["memory_enabled"] is False
    assert by_id["C"]["shared_state"] is False
    assert by_id["A"]["memory_enabled"] is True
    assert by_id["A"]["shared_state"] is True
    assert "memory_on_vs_off" in payload["comparison"]
    assert "shared_state_on_vs_off" in payload["comparison"]
