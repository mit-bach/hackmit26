"""Tests for the shared CFO sample-data generator."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.mathutil import cents
from integrations.cash import reconcile_payout
from tools import exception_types_for, load_invoice

from sample_data.orchestrator import generate_sample_data
from sample_data.paths import data_root, snapshot_loader_paths
from sample_data.pnl import (
    COGS_ACCOUNTS,
    OPERATIONAL_AP_IDS,
    cogs_invoice_ids,
    quantity_rate_amount,
    validate_fact_arithmetic,
)
from sample_data.registry import required_ids
from sample_data.validators import validate_dataset, validate_pnl_integrity


def _canonical(ctx):
    return {
        "invoices": [item.model_dump(mode="json") for item in ctx.ap_invoices.values()],
        "ar": [item.model_dump(mode="json") for item in ctx.ar_invoices.values()],
        "bank": [item.model_dump(mode="json") for item in ctx.bank_transactions.values()],
        "journal": [item.model_dump(mode="json") for item in ctx.journal_entries.values()],
        "scenarios": sorted(ctx.scenarios),
        "forecast": [item.model_dump(mode="json") for item in ctx.forecast_weeks],
    }


def test_deterministic_generation():
    left = _canonical(generate_sample_data(seed=42, period="2026-09", output=None))
    right = _canonical(generate_sample_data(seed=42, period="2026-09", output=None))
    assert left == right


def test_full_validator_passes():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    validate_dataset(ctx)
    assert set(required_ids()) <= set(ctx.scenarios)


def test_id_uniqueness_and_foreign_keys(tmp_path):
    ctx = generate_sample_data(seed=42, period="2026-09", output=tmp_path / "demo")
    ids = (
        list(ctx.ap_invoices)
        + list(ctx.ar_invoices)
        + list(ctx.ar_payments)
        + list(ctx.bank_transactions)
        + list(ctx.journal_entries)
    )
    assert len(ids) == len(set(ids))
    for payment in ctx.vendor_payments.values():
        for invoice_id in payment.invoice_ids:
            assert invoice_id in ctx.ap_invoices


def test_ap_three_way_and_duplicate(tmp_path, monkeypatch):
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    with data_root(output):
        invoice = load_invoice("INV-001")
        assert invoice is not None
        assert exception_types_for("INV-001") == []
        assert "duplicate" in exception_types_for("INV-006")
        assert "duplicate" in exception_types_for("INV-007")
        assert "partial_receipt" in exception_types_for("INV-003")


def test_ar_aging_and_ambiguous_cash():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    from ar.aging import aging_bucket, days_past_due

    as_of = "2026-09-30"
    buckets = {
        aging_bucket(days_past_due(ctx.ar_invoices[key].due_date, as_of))
        for key in ("INV-AR-001", "INV-AR-002", "INV-AR-003", "INV-AR-004", "INV-AR-005")
    }
    assert buckets == {"CURRENT", "1-30", "31-60", "61-90", "90+"}
    lumen = [ctx.ar_invoices["INV-AR-010"], ctx.ar_invoices["INV-AR-011"]]
    assert lumen[0].outstanding_amount == lumen[1].outstanding_amount
    assert ctx.ar_payments["PAY-004"].amount == lumen[0].outstanding_amount
    assert "INV-AR" not in ctx.ar_payments["PAY-004"].remittance_text


def test_cash_recon_planted_cases():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    grouped = sum(ctx.ledger_cash[key].amount_minor for key in ("GL-AP-201", "GL-AP-202", "GL-AP-203"))
    assert grouped == ctx.bank_transactions["TXN-2026-09-008"].amount_minor
    assert ctx.bank_transactions["TXN-2026-09-011"].amount_minor == -1_002_500
    assert ctx.ledger_cash["GL-AP-WIRE"].amount_minor == -1_000_000
    assert "TXN-2026-09-012A" in ctx.bank_transactions and "TXN-2026-09-012B" in ctx.bank_transactions
    delta = ctx.bank_transactions["TXN-2026-09-015"].amount_minor - ctx.ledger_cash["GL-AR-NS"].amount_minor
    assert delta == 1240
    assert dollars_of(delta) == 12.4


def test_stripe_payout_math_ties():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    assert len(ctx.stripe_payouts) == 3
    for payout in ctx.stripe_payouts:
        breakdown = reconcile_payout(payout)
        assert breakdown.expected_payout_minor == breakdown.actual_payout_minor
        assert breakdown.difference == 0


def test_close_accrual_prepaid_and_evidence():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    assert any(item.vendor == "Harbor Electric" for item in ctx.accruals)
    assert any(item.vendor == "Lindholm & Ruiz LLP" for item in ctx.accruals)
    insurance = next(item for item in ctx.prepaids if item.prepaid_id == "PRE-INS-001")
    posted = [line.amount for line in ctx.prepaid_schedule if line.prepaid_id == insurance.prepaid_id]
    assert abs(sum(posted) - insurance.total_amount) < 0.02
    for link in ctx.identity_links:
        assert link.source_document_id in set(ctx.ap_invoices) | set(ctx.ar_invoices)


def test_audit_round_number_post_close_self_approval():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    payment = next(item for item in ctx.audit_payments if item.payment_id == "PAY-AP-009")
    assert payment.amount == 50000
    assert any(item.entry_id == "JE-POST-CLOSE-001" for item in ctx.audit_journals)
    approval = next(item for item in ctx.audit_approvals if item.approval_id == "APR-INV-SELF")
    assert approval.requester_id == approval.approver_id
    assert ctx.expected is not None
    codes = {item.expected_reason_code for item in ctx.expected.audit_findings}
    assert "SELF_APPROVAL" in codes
    assert "ROUND_NUMBER" in codes


def test_cogs_quantity_times_rate_equals_line_amount():
    assert validate_fact_arithmetic() == []
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    checked = 0
    for entry in ctx.journal_entries.values():
        if entry.debit_account not in COGS_ACCOUNTS:
            continue
        computed = quantity_rate_amount(entry.quantity, entry.rate)
        if computed is None:
            continue
        assert cents(computed) == entry.amount_minor, entry.entry_id
        checked += 1
    assert checked >= 10


def test_operational_ap_invoices_are_not_posted_to_cogs():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    for entry in ctx.journal_entries.values():
        if entry.debit_account in COGS_ACCOUNTS:
            assert entry.source_document_id not in OPERATIONAL_AP_IDS, entry.entry_id
            assert entry.source_document_id in cogs_invoice_ids()
        if entry.source_document_id in {"INV-001", "INV-002", "INV-006", "INV-016", "INV-017"}:
            assert entry.debit_account not in COGS_ACCOUNTS
    cogs_sources = [
        entry.source_document_id
        for entry in ctx.journal_entries.values()
        if entry.debit_account in COGS_ACCOUNTS and entry.period == "2026-09"
    ]
    assert len(cogs_sources) == len(set(cogs_sources))


def test_reporting_cogs_equals_journal_cogs_once():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    assert validate_pnl_integrity(ctx) == []
    sep_hosting = sum(
        entry.amount
        for entry in ctx.journal_entries.values()
        if entry.period == "2026-09" and entry.category == "hosting"
    )
    assert sep_hosting == 95_000


def test_reporting_ties_and_gross_margin():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    rev = {"2026-08": 0, "2026-09": 0}
    cogs = {"2026-08": 0, "2026-09": 0}
    for line in ctx.reporting_lines:
        if line.account_class == "revenue" and line.side == "credit":
            rev[line.period] += cents(line.amount)
        if line.account_class == "cogs" and line.side == "debit":
            cogs[line.period] += cents(line.amount)
    assert rev["2026-08"] == 100_000_000
    assert rev["2026-09"] == 100_000_000
    assert cogs["2026-08"] == 36_000_000
    assert cogs["2026-09"] == 39_000_000
    gm_aug = 1 - cogs["2026-08"] / rev["2026-08"]
    gm_sep = 1 - cogs["2026-09"] / rev["2026-09"]
    assert abs((gm_aug - gm_sep) - 0.03) < 1e-9
    assert any(line.source_document_id == "INV-SUP-SEP-001" for line in ctx.reporting_lines)


def test_forecast_weeks_and_actuals():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    assert len(ctx.forecast_weeks) == 13
    actual_ids = {item.source_id for item in ctx.forecast_actuals}
    assert "INV-AR-014" in actual_ids
    assert "INV-012" in actual_ids
    assert ctx.forecast_actuals[0].bank_transaction_id in ctx.bank_transactions or ctx.forecast_actuals[0].bank_transaction_id == "BNK-AR-FC-001"


def test_expected_audit_findings_are_discoverable(tmp_path):
    output = tmp_path / "demo"
    ctx = generate_sample_data(seed=42, period="2026-09", output=output)
    with data_root(output):
        from audit.controls import run_duplicate_vendors
        from audit.store import load_operational_decisions, load_vendors

        result = run_duplicate_vendors(
            vendors=load_vendors(),
            decisions=load_operational_decisions(),
            audit_run_id="TEST",
        )
        assert result.result == "FAIL"
        assert any(item.object_id in {"VEND-001", "VEND-001-DUP"} for item in result.exceptions)
        payload = json.loads((output / "expected_results.json").read_text())
        assert payload["audit_findings"]
        assert ctx.expected is not None


def test_all_journals_balance():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    for entry in ctx.journal_entries.values():
        assert entry.amount_minor > 0
        assert entry.debit_account != entry.credit_account


def test_writes_manifest(tmp_path):
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["seed"] == 42
    assert manifest["period"] == "2026-09"
    assert manifest["validation"] == "PASS"
    assert (output / "expected_results.json").exists()
    assert (output / "invoices.json").exists()


def dollars_of(amount_minor: int) -> float:
    return round(amount_minor / 100.0, 2)


PLANTED_DISCREPANCY_IDS = {
    "INV-003",
    "INV-006",
    "INV-007",
    "PAY-004",
    "TXN-2026-09-011",
    "TXN-2026-09-015",
    "JE-POST-CLOSE-001",
    "PAY-AP-009",
    "APR-INV-SELF",
    "VEND-001-DUP",
}


def test_workflows_surface_planted_discrepancies(tmp_path):
    """Planted exceptions must be raised by the live AP/AR/cash/audit/reporting workflows."""
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    with data_root(output):
        assert exception_types_for("INV-001") == []
        assert "duplicate" in exception_types_for("INV-006")
        assert "partial_receipt" in exception_types_for("INV-003")

        from ar.store import reset_state
        from ar.workflow import run_cash_apply

        reset_state()
        assert run_cash_apply("PAY-004", live=False, persist=False).final.decision == "HUMAN_REVIEW"
        assert run_cash_apply("PAY-005", live=False, persist=False).final.decision == "HUMAN_REVIEW"

        from cash_recon.demo import load_demo_dataset, seed_provider_payouts
        from cash_recon.store import reset_cash_state
        from cash_recon.workflow import run_cash_reconciliation

        reset_cash_state()
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
        by_bank = {bank_id: match for match in report.matches for bank_id in match.bank_transaction_ids}
        assert by_bank["TXN-2026-09-011"].match_type == "FEE_NETTED"
        assert by_bank["TXN-2026-09-015"].status == "HUMAN_REVIEW"
        assert by_bank["TXN-2026-09-021"].status == "HUMAN_REVIEW"
        assert by_bank["TXN-2026-09-019A"].match_type == "PROVIDER_PAYOUT"
        assert by_bank["TXN-2026-09-022S"].match_type == "PROVIDER_PAYOUT"
        assert by_bank["TXN-2026-09-026S"].match_type == "PROVIDER_PAYOUT"

        from audit.workflow import run_audit
        from tools import has_duplicate_vendor_invoice_number

        run = run_audit("2026-09", seed=42, use_agent=False, persist=False)
        found = set()
        for finding in run.findings:
            found.update(
                finding.affected_object_ids
                + finding.invoice_ids
                + finding.payment_ids
                + finding.approval_ids
                + finding.journal_entry_ids
                + finding.vendor_ids
            )
        assert found & {"VEND-001", "VEND-001-DUP"}
        assert "PAY-AP-009" in found
        assert "JE-POST-CLOSE-001" in found
        assert "APR-INV-SELF" in found
        assert has_duplicate_vendor_invoice_number("INV-006")

        from reporting.ledger import reset_ledger
        from reporting.seed import seed_demo_ledger
        from reporting.statements import build_income_statement
        from reporting.variance import analyze_variance

        reset_ledger()
        seed_demo_ledger()
        statement = build_income_statement("2026-09")
        assert abs(statement.cogs - 390_000) < 0.02
        assert abs(statement.revenue - 1_000_000) < 0.02
        explanation = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
        drivers = set()
        for contributor in explanation.contributors:
            drivers.update(contributor.source_transaction_ids)
        assert {"TXN-SUP-SEP-001", "TXN-FRT-SEP-001", "TXN-HOST-SEP-001"} <= drivers
        assert "INV-001" not in drivers
        assert "INV-017" not in drivers


def test_expected_discrepancy_ids_are_present():
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    known = (
        set(ctx.ap_invoices)
        | set(ctx.ar_payments)
        | set(ctx.bank_transactions)
        | {item.entry_id for item in ctx.audit_journals}
        | {item.payment_id for item in ctx.audit_payments}
        | {item.approval_id for item in ctx.audit_approvals}
        | set(ctx.vendors)
    )
    missing = PLANTED_DISCREPANCY_IDS - known
    assert not missing
    assert set(required_ids()) <= set(ctx.scenarios)
    assert ctx.bank_transactions["TXN-2026-09-015"].amount_minor - ctx.ledger_cash["GL-AR-NS"].amount_minor == 1240


def test_generator_does_not_leak_state_between_calls():
    first = generate_sample_data(seed=42, period="2026-09", output=None)
    first.ap_invoices["INV-001"].amount = 1.0
    first.scenarios.clear()
    second = generate_sample_data(seed=42, period="2026-09", output=None)
    assert second.ap_invoices["INV-001"].amount != 1.0
    assert set(required_ids()) <= set(second.scenarios)
    assert _canonical(first) != _canonical(second)
    assert _canonical(second) == _canonical(generate_sample_data(seed=42, period="2026-09", output=None))


def test_apply_data_root_restores_prior_loader_paths(tmp_path):
    before = snapshot_loader_paths()
    output = tmp_path / "demo"
    generate_sample_data(seed=42, period="2026-09", output=output)
    with data_root(output):
        from tools import DATA_DIR

        assert Path(DATA_DIR) == output
        assert snapshot_loader_paths() != before
    assert snapshot_loader_paths() == before


def test_full_suite_order_does_not_affect_generation(tmp_path):
    dirty = tmp_path / "dirty-demo"
    generate_sample_data(seed=7, period="2026-09", output=dirty)
    with data_root(dirty):
        assert load_invoice("INV-001") is not None
    ctx = generate_sample_data(seed=42, period="2026-09", output=None)
    validate_dataset(ctx)
    assert set(required_ids()) <= set(ctx.scenarios)
    assert ctx.bank_transactions["TXN-2026-09-015"].amount_minor - ctx.ledger_cash["GL-AR-NS"].amount_minor == 1240
