"""Tests for the shared CFO sample-data generator."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.mathutil import cents
from integrations.cash import reconcile_payout
from tools import exception_types_for, load_invoice

from sample_data.orchestrator import generate_sample_data
from sample_data.paths import apply_data_root, reset_data_root
from sample_data.registry import required_ids
from sample_data.validators import validate_dataset


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
    apply_data_root(output)
    try:
        invoice = load_invoice("INV-001")
        assert invoice is not None
        assert exception_types_for("INV-001") == []
        assert "duplicate" in exception_types_for("INV-006")
        assert "duplicate" in exception_types_for("INV-007")
        assert "partial_receipt" in exception_types_for("INV-003")
    finally:
        reset_data_root()


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
    apply_data_root(output)
    try:
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
    finally:
        reset_data_root()


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
