"""Regression tests for planted-discrepancy detection. Agents never see discrepancy IDs."""

from __future__ import annotations

from pathlib import Path

import pytest

from ar.cash import extract_invoice_ids, generate_cash_candidates, policy_cash_decision
from ar.models import Customer, CustomerInvoice, CustomerPayment
from bs_recon.packets import _gl_control_balance, ap_packet, ar_packet
from close.orchestrator import decide_ap
from reporting.forecast import review_forecast_integrity
from reporting.models import CashForecastSnapshot, ForecastLine
from reporting.seed import seed_demo_ledger
from reporting.variance import analyze_variance, flag_unsupported_claims
from scheduling.cash import policy_eligible_for_pool
from tools import (
    exception_types_for,
    load_duplicate_invoices,
    normalize_invoice_number,
    normalize_vendor,
)

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "discrepancy_demo"


def _invoice(**overrides) -> CustomerInvoice:
    payload = dict(
        invoice_id="INV-X",
        customer_id="CUST-1",
        customer_name="Pinnacle Retail",
        invoice_date="2026-09-01",
        due_date="2026-10-01",
        original_amount=10000.0,
        outstanding_amount=10000.0,
        status="OPEN",
    )
    payload.update(overrides)
    return CustomerInvoice.model_validate(payload)


def _payment(**overrides) -> CustomerPayment:
    payload = dict(
        payment_id="PAY-X",
        payment_date="2026-09-20",
        amount=9600.0,
        currency="USD",
        payer_name="Pinnacle Retail",
        customer_id="CUST-1",
        remittance_text="",
        invoice_reference="",
        source="ach",
        unapplied_amount=9600.0,
        application_status="UNMATCHED",
    )
    payload.update(overrides)
    return CustomerPayment.model_validate(payload)


def test_ap_quantity_and_price_and_missing_receipt():
    from sample_data.paths import data_root

    if not DISC.exists():
        pytest.skip("discrepancy dataset not generated")
    with data_root(DISC):
        assert "partial_receipt" in exception_types_for("INV-003")
        assert decide_ap("INV-003", live=False, featured=set()).decision == "HOLD"
        assert "material_amount_mismatch" in exception_types_for("INV-004")
        assert decide_ap("INV-004", live=False, featured=set()).decision == "HOLD"
        assert "goods_not_received" in exception_types_for("INV-005")
        assert decide_ap("INV-005", live=False, featured=set()).decision == "HOLD"


def test_duplicate_invoice_is_surfaced():
    from sample_data.paths import data_root

    if not DISC.exists():
        pytest.skip("discrepancy dataset not generated")
    with data_root(DISC):
        assert "duplicate" in exception_types_for("INV-006")
        assert decide_ap("INV-006", live=False, featured=set()).decision == "HOLD"


def test_normalized_duplicate_invoice_is_surfaced():
    assert normalize_invoice_number("INV-1048") == normalize_invoice_number("INV 1048")
    assert normalize_vendor("Acme Software Inc.") == normalize_vendor("ACME SOFTWARE, INC")
    if not DISC.exists():
        pytest.skip("discrepancy dataset not generated")
    from sample_data.paths import data_root

    with data_root(DISC):
        dups = load_duplicate_invoices("INV-DISC-1048A")
        assert {item.invoice_id for item in dups} >= {"INV-DISC-1048B"}
        assert "duplicate" in exception_types_for("INV-DISC-1048A")
        assert decide_ap("INV-DISC-1048A", live=False, featured=set()).decision == "HOLD"


def test_approval_threshold_is_held():
    from sample_data.paths import data_root

    source = DISC if DISC.exists() else ROOT / "data" / "demo"
    if not source.exists():
        pytest.skip("demo dataset not generated")
    with data_root(source):
        assert "approval_limit_exceeded" in exception_types_for("INV-009")
        assert decide_ap("INV-009", live=False, featured=set()).decision == "HOLD"


def test_self_approval_and_payment_on_hold():
    from audit.store import load_approvals
    from sample_data.paths import data_root

    source = DISC if DISC.exists() else ROOT / "data" / "demo"
    if not source.exists():
        pytest.skip("demo dataset not generated")
    with data_root(source):
        selfs = [item for item in load_approvals() if item.requester_id and item.requester_id == item.approver_id]
        assert selfs
        assert policy_eligible_for_pool("INV-010") is False


def test_ar_partial_payment_is_preserved():
    invoice = _invoice(invoice_id="INV-DISC-PARTIAL", outstanding_amount=10000.0)
    payment = _payment(
        payment_id="PAY-DISC-PARTIAL",
        remittance_text="Partial INV-DISC-PARTIAL",
        invoice_reference="INV-DISC-PARTIAL",
        amount=9600.0,
    )
    customer = Customer(customer_id="CUST-1", customer_name="Pinnacle Retail")
    facts = generate_cash_candidates(payment, invoices=[invoice], customers=[customer])
    assert "INV-DISC-PARTIAL" in facts.remittance_invoice_ids
    proposal = policy_cash_decision(facts)
    assert proposal.decision == "AUTO_APPLY"
    assert proposal.applications[0].amount == 9600.0
    assert invoice.outstanding_amount == 10000.0


def test_ar_overpayment_residual_is_preserved():
    invoice = _invoice(invoice_id="INV-OVER", original_amount=8000.0, outstanding_amount=8000.0, customer_id="CUST-1")
    payment = _payment(
        payment_id="PAY-OVER",
        amount=8750.0,
        remittance_text="INV-OVER",
        invoice_reference="INV-OVER",
        unapplied_amount=8750.0,
    )
    customer = Customer(customer_id="CUST-1", customer_name="Pinnacle Retail")
    facts = generate_cash_candidates(payment, invoices=[invoice], customers=[customer])
    proposal = policy_cash_decision(facts)
    assert proposal.decision == "HUMAN_REVIEW"
    assert "750" in proposal.reason or any("750" in item for item in proposal.ambiguities)


def test_ambiguous_remittance_routes_to_human_review():
    from ar.store import reset_state
    from ar.workflow import run_cash_apply
    from sample_data.paths import data_root

    source = DISC if DISC.exists() else ROOT / "data" / "demo"
    if not source.exists():
        pytest.skip("demo dataset not generated")
    with data_root(source):
        reset_state()
        trace = run_cash_apply("PAY-004", live=False, persist=False)
        assert trace.final.decision == "HUMAN_REVIEW"


def test_invalid_invoice_reference_is_surfaced():
    payment = _payment(
        remittance_text="Payment for AR-INV-9999",
        invoice_reference="AR-INV-9999",
        amount=3200.0,
        payer_name="Quiet Harbor",
        customer_id="CUST-5",
    )
    invoice = _invoice(invoice_id="INV-LIVE", customer_id="CUST-5", customer_name="Quiet Harbor")
    customer = Customer(customer_id="CUST-5", customer_name="Quiet Harbor")
    facts = generate_cash_candidates(payment, invoices=[invoice], customers=[customer])
    assert "AR-INV-9999" in facts.missing_invoice_ids
    assert policy_cash_decision(facts).decision == "HUMAN_REVIEW"


def test_customer_identity_conflict_is_surfaced():
    payment = _payment(
        payer_name="Helios Analytics",
        customer_id="CUST-3",
        remittance_text="Northwind Labs INV-AR-001",
        invoice_reference="INV-AR-001",
        amount=8500.0,
    )
    named = _invoice(invoice_id="INV-AR-001", customer_id="CUST-1", customer_name="Northwind Labs", outstanding_amount=8500.0)
    customers = [
        Customer(customer_id="CUST-3", customer_name="Acme Industrial"),
        Customer(customer_id="CUST-1", customer_name="Northwind Labs"),
        Customer(customer_id="CUST-2", customer_name="Helios Analytics"),
    ]
    facts = generate_cash_candidates(payment, invoices=[named], customers=customers)
    assert facts.identity_conflicts
    assert policy_cash_decision(facts).decision == "HUMAN_REVIEW"


def test_double_cash_application_is_caught():
    from ar.models import CashApplicationProposal
    from ar.workflow import run_cash_apply

    payment = _payment(payment_id="PAY-ALREADY", application_status="APPLIED", amount=12000.0, unapplied_amount=0.0)
    facts = generate_cash_candidates(
        payment,
        invoices=[_invoice(invoice_id="INV-AR-007", outstanding_amount=0.0)],
        customers=[Customer(customer_id="CUST-1", customer_name="Pinnacle Retail")],
    )
    assert policy_cash_decision(facts).decision == "UNAPPLIED"
    _ = CashApplicationProposal
    _ = run_cash_apply
    _ = extract_invoice_ids


def test_grouped_ach_residual_is_detected():
    from cash_recon.candidates import grouped_candidates
    from cash_recon.models import BankTransaction, LedgerEntry

    bank = [
        BankTransaction(
            transaction_id="TXN-GRP",
            date="2026-09-18",
            amount=-5850.0,
            amount_minor=-585000,
            counterparty="Northline Fabrication",
        )
    ]
    ledger = [
        LedgerEntry(entry_id="G1", date="2026-09-18", amount=-1000.0, amount_minor=-100000, counterparty="Northline Fabrication"),
        LedgerEntry(entry_id="G2", date="2026-09-18", amount=-2000.0, amount_minor=-200000, counterparty="Northline Fabrication"),
        LedgerEntry(entry_id="G3", date="2026-09-18", amount=-3000.0, amount_minor=-300000, counterparty="Northline Fabrication"),
    ]
    rows = grouped_candidates(bank, ledger)
    unexplained = [item for item in rows if item.match_type == "UNEXPLAINED_DIFFERENCE"]
    assert unexplained
    assert abs(unexplained[0].difference_minor) == 15000
    assert not any(item.match_type == "GROUPED_MATCH" for item in rows)


def test_cash_unexplained_and_unmatched_rules():
    from cash_recon.validate import DISPOSITION_FOR, expected_disposition

    assert DISPOSITION_FOR["UNEXPLAINED_DIFFERENCE"] == "HUMAN_REVIEW"
    assert DISPOSITION_FOR["UNMATCHED_BANK"] == "HUMAN_REVIEW"
    assert DISPOSITION_FOR["UNMATCHED_LEDGER"] == "HUMAN_REVIEW"
    assert expected_disposition("GROUPED_MATCH") == "MATCHED"
    # A grouped candidate with a residual is not a valid MATCHED group.
    assert DISPOSITION_FOR["UNEXPLAINED_DIFFERENCE"] != "MATCHED"


def test_close_packets_use_gl_when_present(tmp_path, monkeypatch):
    gl = tmp_path / "close" / "gl_balances.json"
    gl.parent.mkdir(parents=True)
    gl.write_text(
        '[{"account":"Accounts Payable","balance":1.0,"period":"2026-09","source_id":"GL-AP-DISC"},'
        '{"account":"Accounts Receivable","balance":0.0,"period":"2026-09","source_id":"GL-AR-DISC"},'
        '{"account":"Suspense","balance":2500.0,"period":"2026-09","source_id":"GL-UNSUP-001"}]\n'
    )
    monkeypatch.setattr("tools.DATA_DIR", tmp_path)
    found = _gl_control_balance("2026-09", {"Accounts Payable"})
    assert found is not None
    assert found[0] == 1.0


def test_ap_gl_discrepancy_blocks_close():
    if not DISC.exists():
        pytest.skip("discrepancy dataset not generated")
    from sample_data.paths import data_root

    with data_root(DISC):
        packet = ap_packet("2026-09")
        assert abs(packet.ledger_balance - packet.evidence_balance) > 0.01
        assert packet.reconciling_items


def test_ar_gl_and_unsupported_balance():
    if not DISC.exists():
        pytest.skip("discrepancy dataset not generated")
    from bs_recon.packets import unsupported_gl_packet
    from sample_data.paths import data_root

    with data_root(DISC):
        packet = ar_packet("2026-09")
        assert abs(packet.ledger_balance - packet.evidence_balance) > 0.01
        extra = unsupported_gl_packet("2026-09")
        assert extra is not None
        assert extra.missing_evidence


def test_board_number_ties_to_gl():
    from reporting.ledger import reset_ledger
    from reporting.statements import period_report

    reset_ledger()
    seed_demo_ledger()
    current, _prior, _metrics = period_report("2026-09", comparison_period="2026-08")
    assert abs(current.revenue - 1_000_000) < 0.02


def test_unsupported_variance_narrative_is_rejected():
    from reporting.ledger import reset_ledger

    reset_ledger()
    seed_demo_ledger()
    explanation = analyze_variance("gross_margin_pct", "2026-09", "2026-08")
    drivers = {txn for item in explanation.contributors for txn in item.source_transaction_ids}
    assert "TXN-REV-SEP-001" in drivers or any(item.category == "revenue" for item in explanation.contributors)
    flags = flag_unsupported_claims(explanation, "Margin fell from supplier cost increases.")
    assert flags


def test_forecast_opening_cash_and_duplicates():
    snapshot = CashForecastSnapshot(
        forecast_id="CF-DRAFT-TEST",
        as_of_date="2026-09-19",
        beginning_cash=1.0,
        lines=[
            ForecastLine(
                line_id="A",
                source_type="invoice",
                source_id="INV-DUP",
                expected_date="2026-09-25",
                amount=-100.0,
                confidence=0.9,
                rationale="copy 1",
            ),
            ForecastLine(
                line_id="B",
                source_type="invoice",
                source_id="INV-DUP",
                expected_date="2026-09-25",
                amount=-100.0,
                confidence=0.9,
                rationale="copy 2",
            ),
            ForecastLine(
                line_id="C",
                source_type="receivable",
                source_id="INV-EARLY",
                expected_date="2026-09-22",
                amount=15000.0,
                confidence=0.4,
                rationale="early",
                evidence_refs=["due:2026-10-31"],
            ),
        ],
    )
    review = review_forecast_integrity(snapshot, "2026-09-19")
    assert "INV-DUP" in review["duplicates"]
    assert review["opening_mismatch"]
    assert "INV-EARLY" in review["early_receipts"]


def test_downstream_unresolved_cash_blocks_close():
    from close.checklist import unresolved_blockers
    from close.month_end import run_month_end

    state = run_month_end("2026-09", live=False, reset=True, scenario="demo")
    tasks = {item.task_id: item for item in state.tasks}
    cash = tasks.get("cash")
    assert cash is not None
    blockers = {item.task_id for item in unresolved_blockers(state.tasks)}
    assert cash.status in {"BLOCKED", "NEEDS_REVIEW", "FAILED"} or "cash" in blockers or state.period.status != "CLOSED"
