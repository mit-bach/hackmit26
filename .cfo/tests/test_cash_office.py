"""Prompt 04 cash office: identifier trust, $12.40 gate, Stripe Grants, Harness Handles."""

from __future__ import annotations

import json
from pathlib import Path

from cash_recon.concur import review_rec
from cash_recon.demo import load_demo_dataset
from cash_recon.engine import generate_all_candidates, propose_matches
from cash_recon.identifiers import choose_candidate_for_line
from cash_recon.mathutil import cents
from cash_recon.models import (
    BankTransaction,
    FeeEvidence,
    LedgerEntry,
    MatchCandidate,
    PeriodBalances,
    PipeIdentifier,
    ReconciliationMatch,
)
from cash_recon.normalize import prepare_bank, prepare_ledger
from cash_recon.office import persist_harness_rec_queue, run_cash_office, write_trusted_cash_packet
from cash_recon.tools import bind_identifiers, read_pipe_identifier, unbind_case
from cash_recon.validate import period_status, validate_candidate
from cash_recon.workflow import run_cash_reconciliation
from integrations.agent import payout_agent
from integrations.cash import reconcile_payout
from integrations.demo import process_provider
from integrations.office import land_payout_handles
from integrations.store import get_payout
from integrations.tools import read_payout_waterfall

REPO = Path(__file__).resolve().parents[2]
GRANTS = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.json"


def _candidate(**kwargs) -> MatchCandidate:
    bank_minor = int(kwargs.get("bank_amount_minor") or cents(kwargs.get("bank_amount", 0)))
    ledger_minor = int(kwargs.get("ledger_amount_minor") or cents(kwargs.get("ledger_amount", 0)))
    return MatchCandidate(
        candidate_id=kwargs["candidate_id"],
        match_type=kwargs["match_type"],
        bank_transaction_ids=list(kwargs["bank_transaction_ids"]),
        ledger_entry_ids=list(kwargs.get("ledger_entry_ids") or []),
        bank_amount=kwargs.get("bank_amount", 0),
        ledger_amount=kwargs.get("ledger_amount", 0),
        difference=kwargs.get("difference", 0),
        bank_amount_minor=bank_minor,
        ledger_amount_minor=ledger_minor,
        difference_minor=bank_minor - ledger_minor,
        score=float(kwargs.get("score", 1.0)),
        evidence=list(kwargs.get("evidence") or []),
        fee_evidence_ids=list(kwargs.get("fee_evidence_ids") or []),
    )


def _match_from_candidate(candidate: MatchCandidate, *, status: str) -> ReconciliationMatch:
    return ReconciliationMatch(
        reconciliation_id=candidate.candidate_id,
        period="2026-09",
        bank_transaction_ids=list(candidate.bank_transaction_ids),
        ledger_entry_ids=list(candidate.ledger_entry_ids),
        match_type=candidate.match_type,
        bank_amount=candidate.bank_amount,
        ledger_amount=candidate.ledger_amount,
        difference=candidate.difference,
        bank_amount_minor=candidate.bank_amount_minor,
        ledger_amount_minor=candidate.ledger_amount_minor,
        difference_minor=candidate.difference_minor,
        status=status,  # type: ignore[arg-type]
        explanation="",
        evidence=list(candidate.evidence),
        candidate_id=candidate.candidate_id,
        human_review=status == "HUMAN_REVIEW",
        proposed_adjusting_entries=list(candidate.proposed_adjusting_entries),
    )


def test_identifier_trust_does_not_re_guess_when_apply_named_the_customer():
    acme = _candidate(
        candidate_id="EXACT_MATCH:B1:L-ACME",
        match_type="EXACT_MATCH",
        bank_transaction_ids=["B1"],
        ledger_entry_ids=["L-ACME"],
        bank_amount=1000,
        ledger_amount=1000,
        score=1.1,
    )
    other = _candidate(
        candidate_id="EXACT_MATCH:B1:L-OTHER",
        match_type="EXACT_MATCH",
        bank_transaction_ids=["B1"],
        ledger_entry_ids=["L-OTHER"],
        bank_amount=1000,
        ledger_amount=1000,
        score=2.0,
    )
    ident = PipeIdentifier(
        source="apply",
        bank_transaction_id="B1",
        payment_id="PAY-001",
        invoice_ids=["INV-001"],
        ledger_entry_ids=["L-ACME"],
        customer_id="CUST-ACME",
        counterparty="Acme Industrial",
    )
    tick = choose_candidate_for_line("B1", [acme, other], [ident])
    assert tick.identifier_present is True
    assert tick.fail_closed is False
    assert tick.guessed_counterparty is False
    assert tick.selected_candidate_id == "EXACT_MATCH:B1:L-ACME"
    assert tick.selected_candidate_id != "EXACT_MATCH:B1:L-OTHER"


def test_pay_identifier_ticks_wire_without_second_vendor_guess():
    named = _candidate(
        candidate_id="EXACT_MATCH:W1:GL-INV-001",
        match_type="EXACT_MATCH",
        bank_transaction_ids=["W1"],
        ledger_entry_ids=["GL-INV-001"],
        bank_amount=-12450,
        ledger_amount=-12450,
        score=1.0,
    )
    guess = _candidate(
        candidate_id="EXACT_MATCH:W1:GL-OTHER",
        match_type="EXACT_MATCH",
        bank_transaction_ids=["W1"],
        ledger_entry_ids=["GL-OTHER"],
        bank_amount=-12450,
        ledger_amount=-12450,
        score=3.0,
    )
    ident = PipeIdentifier(
        source="pay",
        bank_transaction_id="W1",
        invoice_ids=["INV-001"],
        ledger_entry_ids=["GL-INV-001"],
        vendor="Acme Industrial",
    )
    tick = choose_candidate_for_line("W1", [named, guess], [ident])
    assert tick.selected_candidate_id == "EXACT_MATCH:W1:GL-INV-001"


def test_missing_identifier_fails_closed_and_does_not_scrape_memo():
    guess = _candidate(
        candidate_id="EXACT_MATCH:B9:L-GUESSED",
        match_type="EXACT_MATCH",
        bank_transaction_ids=["B9"],
        ledger_entry_ids=["L-GUESSED"],
        bank_amount=500,
        ledger_amount=500,
    )
    tick = choose_candidate_for_line("B9", [guess], [], require_identifier=True)
    assert tick.identifier_present is False
    assert tick.fail_closed is True
    assert tick.selected_candidate_id is None
    assert "fail closed" in tick.reason.lower() or "have not identified" in tick.reason.lower()


def test_get_pipe_identifier_read_does_not_invent():
    unbind_case()
    bind_identifiers(
        [
            PipeIdentifier(
                source="apply",
                bank_transaction_id="B1",
                invoice_ids=["INV-001"],
                customer_id="CUST-ACME",
            )
        ]
    )
    found = read_pipe_identifier("B1")
    assert found["identifier_present"] is True
    assert found["customer_id"] == "CUST-ACME"
    missing = read_pipe_identifier("B-MISSING")
    assert missing["identifier_present"] is False
    assert missing["fail_closed"] is True
    unbind_case()


def test_northstar_12_40_stays_unexplained_and_blocks_reconciled():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    item = next(row for row in report.matches if "TXN-2026-09-015" in row.bank_transaction_ids)
    assert item.match_type == "UNEXPLAINED_DIFFERENCE"
    assert item.difference_minor == 1240
    assert item.status == "HUMAN_REVIEW"
    assert item.status != "MATCHED"
    assert report.period_status != "RECONCILED"
    ident = PipeIdentifier(
        source="apply",
        bank_transaction_id="TXN-2026-09-015",
        payment_id="PAY-006",
        invoice_ids=["INV-AR-013"],
        ledger_entry_ids=["GL-AR-NS"],
        counterparty="Northstar LLC",
    )
    universe = generate_all_candidates(*load_demo_dataset()[1:], "2026-09")
    tick = choose_candidate_for_line("TXN-2026-09-015", universe, [ident])
    assert tick.identifier_present is True
    chosen = next(row for row in universe if row.candidate_id == tick.selected_candidate_id)
    assert chosen.match_type == "UNEXPLAINED_DIFFERENCE"
    assert chosen.difference_minor == 1240
    verdict = review_rec(item, requested_status="MATCHED")
    assert verdict.decision == "REFUSE"
    assert verdict.can_mark_matched is False
    assert verdict.can_mark_reconciled is False
    fee_story = review_rec(item, requested_status="EXPLAINED_EXCEPTION")
    assert fee_story.decision == "REFUSE"
    stay = review_rec(item)
    assert stay.decision == "CONCUR"
    assert stay.can_mark_reconciled is False
    from cash_recon.validate import compute_tie_out

    balances, bank, ledger, _fees = load_demo_dataset()
    period_bank = [row for row in bank if row.period == "2026-09"]
    period_ledger = [row for row in ledger if row.period == "2026-09"]
    tie = compute_tie_out(
        balances,
        period_bank,
        period_ledger,
        report.matches,
        period="2026-09",
        bank={row.transaction_id: row for row in bank},
        ledger={row.entry_id: row for row in ledger},
    )
    assert period_status(tie, report.matches) != "RECONCILED"


def test_helios_fee_netted_requires_kernel_fee_evidence():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    fee = next(row for row in report.matches if "TXN-2026-09-011" in row.bank_transaction_ids)
    assert fee.match_type == "FEE_NETTED"
    assert fee.status == "EXPLAINED_EXCEPTION"
    kernel_fee_ids = {row.evidence_id for row in load_demo_dataset()[3]}
    blob = " ".join(fee.evidence) + " " + " ".join(
        entry.support for entry in fee.proposed_adjusting_entries
    )
    assert kernel_fee_ids
    assert any(item in blob for item in kernel_fee_ids)
    validation = validate_candidate(
        next(
            cand
            for trace in report.traces
            for cand in trace.candidates
            if cand.candidate_id == fee.candidate_id
        ),
        {row.transaction_id: row for row in load_demo_dataset()[1]},
        {row.entry_id: row for row in load_demo_dataset()[2]},
    )
    assert "fee_netted_without_evidence" not in validation.errors
    bank = [
        BankTransaction(
            transaction_id="TXN-2026-09-011",
            date="2026-09-11",
            amount=-10025,
            description="WIRE TRANSFER INTL REF 729103",
            reference="729103",
            period="2026-09",
            amount_minor=-1_002_500,
        )
    ]
    ledger = [
        LedgerEntry(
            entry_id="GL-AP-WIRE",
            date="2026-09-11",
            amount=-10000,
            counterparty="Helios Hardware",
            reference="WIRE-729103",
            period="2026-09",
            amount_minor=-1_000_000,
        )
    ]
    bank = prepare_bank(bank)
    ledger = prepare_ledger(ledger)
    without_fee = propose_matches(bank, ledger, [], "2026-09")
    assert not any(item.match_type == "FEE_NETTED" for item in without_fee)
    with_fee = propose_matches(
        bank,
        ledger,
        [
            FeeEvidence(
                evidence_id="FEE-729103",
                date="2026-09-11",
                amount=25,
                reference="729103",
                amount_minor=2500,
            )
        ],
        "2026-09",
    )
    netted = [item for item in with_fee if item.match_type == "FEE_NETTED"]
    assert netted
    assert "FEE-729103" in netted[0].fee_evidence_ids
    verdict = review_rec(_match_from_candidate(netted[0], status="EXPLAINED_EXCEPTION"))
    assert verdict.decision == "CONCUR"
    bare = _match_from_candidate(
        _candidate(
            candidate_id="FEE_NETTED:X:Y",
            match_type="FEE_NETTED",
            bank_transaction_ids=["X"],
            ledger_entry_ids=["Y"],
            bank_amount=-10025,
            ledger_amount=-10000,
            difference=-25,
            bank_amount_minor=-1_002_500,
            ledger_amount_minor=-1_000_000,
        ),
        status="EXPLAINED_EXCEPTION",
    )
    refused = review_rec(bare)
    assert refused.decision == "REFUSE"


def test_stripe_unpack_emits_zero_invoice_candidates():
    process_provider("stripe")
    payout = get_payout("po_1HackMIT97420")
    assert payout is not None
    breakdown = reconcile_payout(payout)
    waterfall = read_payout_waterfall("po_1HackMIT97420")
    assert waterfall["invoice_candidates"] == 0
    assert "InvoiceCandidate" not in json.dumps(waterfall)
    assert breakdown.status in {"MATCH", "AWAITING_BANK", "MISMATCH", "NEEDS_REVIEW"}
    assert payout_agent.name == "Stripe Payout Agent"
    grants = json.loads(GRANTS.read_text())
    ops = grants["byDisplayName"]["Stripe Payout Agent"]["ops"]
    assert "integrations.tools.get_payout_waterfall" in ops
    assert "integrations.tools.get_processor_payout" in ops
    assert not any(item.startswith("accrual.tools.") for item in ops)
    assert not any(item.startswith("invoice_ingestion.tools.") for item in ops)
    catalog = json.loads((REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "catalog.json").read_text())
    op_ids = [item["id"] for item in catalog["ops"]]
    assert "cash_recon.tools.bind_case" not in op_ids
    assert "cash_recon.tools.get_pipe_identifier" in op_ids
    assert "integrations.tools.get_payout_waterfall" in op_ids


def test_stripe_land_handles_are_harness_not_invoice(tmp_path):
    process_provider("stripe")
    computer = tmp_path / "computer"
    landed = land_payout_handles("po_1HackMIT97420", computer_root=computer)
    assert landed["invoice_candidates"] == 0
    packet = json.loads(Path(landed["packet_path"]).read_text())
    assert packet["invoice_candidates"] == 0
    cash = json.loads(Path(landed["deposit_handle"]).read_text())
    assert cash["toSlug"] == "cash"
    assert cash["fromSlug"] == "stripe"
    assert cash["done"] is False
    apply = json.loads(Path(landed["charges_handle"]).read_text())
    assert apply["toSlug"] == "apply"


def test_harness_handle_path_cash_ctl_cash_trusted_blocked_on_12_40(tmp_path):
    computer = tmp_path / "computer"
    result = run_cash_office(
        "2026-09",
        computer_root=computer,
        identifiers=[
            PipeIdentifier(
                source="apply",
                bank_transaction_id="TXN-2026-09-015",
                payment_id="PAY-006",
                invoice_ids=["INV-AR-013"],
                ledger_entry_ids=["GL-AR-NS"],
            )
        ],
        require_identifier=False,
        seed_demo=True,
        reset=True,
    )
    report = result["report"]
    item = next(row for row in report.matches if "TXN-2026-09-015" in row.bank_transaction_ids)
    assert item.match_type == "UNEXPLAINED_DIFFERENCE"
    ctl = list((computer / "harness" / "bots" / "bot_ctl_cash" / "handles").glob("*.json"))
    assert ctl
    wake = json.loads(ctl[0].read_text())
    assert wake["fromSlug"] == "cash"
    assert wake["toSlug"] == "ctl-cash"
    assert wake["profile"] == "review-rec"
    assert wake["done"] is False
    trusted = result["trusted_cash"]
    assert trusted.trusted is False
    assert trusted.close_handle is False
    packet = json.loads(Path(trusted.packet_path).read_text())
    assert packet["close_may_read"] is True
    assert packet["forecast_may_start"] is False
    assert packet["trusted"] is False
    close_files = list((computer / "harness" / "bots" / "bot_close" / "handles").glob("*.json"))
    assert close_files == []


def test_trusted_cash_handle_to_close_only_when_kernel_allows(tmp_path):
    computer = tmp_path / "computer"
    report = run_cash_reconciliation(
        "2026-09",
        balances=PeriodBalances(
            opening_bank=0,
            opening_ledger=0,
            as_of_date="2026-09-30",
            opening_bank_minor=0,
            opening_ledger_minor=0,
        ),
        bank=[
            BankTransaction(
                transaction_id="B-CLEAN",
                date="2026-09-04",
                amount=-100,
                description="ACH OUT ACME INV-001",
                counterparty="Acme",
                reference="INV-001",
                period="2026-09",
                amount_minor=-10000,
            )
        ],
        ledger=[
            LedgerEntry(
                entry_id="L-CLEAN",
                date="2026-09-04",
                amount=-100,
                counterparty="Acme",
                reference="INV-001",
                period="2026-09",
                amount_minor=-10000,
            )
        ],
        fees=[],
        reset=True,
        use_agent=False,
        seed_providers=False,
    )
    assert report.period_status == "RECONCILED"
    concurrences = [review_rec(item) for item in report.matches]
    trusted = write_trusted_cash_packet(computer, report, concurrences=concurrences)
    assert trusted.trusted is True
    assert trusted.close_handle is True
    close_files = list((computer / "harness" / "bots" / "bot_close" / "handles").glob("*.json"))
    assert close_files
    payload = json.loads(close_files[0].read_text())
    assert payload["toSlug"] == "close"
    assert payload["fromSlug"] == "cash"
    assert payload["trusted"] is True


def test_persist_harness_rec_queue_writes_bot_ctl_cash(tmp_path):
    computer = tmp_path / "computer"
    match = ReconciliationMatch(
        reconciliation_id="REC-NS",
        period="2026-09",
        bank_transaction_ids=["TXN-2026-09-015"],
        ledger_entry_ids=["GL-AR-NS"],
        match_type="UNEXPLAINED_DIFFERENCE",
        bank_amount=12412.40,
        ledger_amount=12400,
        difference=12.40,
        bank_amount_minor=1_241_240,
        ledger_amount_minor=1_240_000,
        difference_minor=1240,
        status="HUMAN_REVIEW",
        human_review=True,
        candidate_id="UNEXPLAINED_DIFFERENCE:TXN-2026-09-015:GL-AR-NS",
    )
    persist_harness_rec_queue(computer, period="2026-09", case_id="2026-09", matches=[match])
    files = list((computer / "harness" / "bots" / "bot_ctl_cash" / "handles").glob("*.json"))
    assert files
    payload = json.loads(files[0].read_text())
    assert payload["op"] == "bot_send_prompt"
    assert payload["humanQueue"] is False
    rec_packet = computer / "workspace" / "cash" / "rec" / "REC-NS.json"
    assert rec_packet.is_file()
    assert payload["paths"] == ["workspace/cash/rec/REC-NS.json"]
