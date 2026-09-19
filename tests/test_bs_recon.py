from bs_recon.engine import can_sign_off, classify_packet, status_for
from bs_recon.models import ReconPacket, ReconcilingItem
from bs_recon.agent import deterministic_prepare, deterministic_review
from bs_recon.workflow import run_balance_sheet_reconciliations
from prepaid.models import PrepaidItem
from prepaid.store import save_items


def _packet(**overrides) -> ReconPacket:
    payload = dict(
        account_id="Prepaid Expenses",
        account_name="Prepaid Expenses",
        period="2026-09",
        ledger_balance=11000,
        evidence_balance=11000,
        ledger_source="gl",
        evidence_source="register",
        evidence_refs=["DOC-INS-2026"],
        reconciling_items=[],
    )
    payload.update(overrides)
    return ReconPacket.model_validate(payload)


def test_exact_match_can_sign_off():
    packet = _packet()
    assert classify_packet(packet) == "exact_match"
    preparer = deterministic_prepare(packet)
    reviewer = deterministic_review(packet, preparer)
    assert reviewer.sign_off is True
    assert reviewer.decision == "APPROVE"


def test_explained_difference():
    packet = _packet(
        ledger_balance=11849.90,
        evidence_balance=12100,
        reconciling_items=[
            ReconcilingItem(
                item_id="AE",
                description="Later invoice timing",
                amount=-250.10,
                source="later_invoices",
                classification="timing_difference",
                status="explained",
                evidence_refs=["INV-AE-2026-09"],
            )
        ],
    )
    assert classify_packet(packet) == "explained_timing_difference"
    assert status_for("explained_timing_difference") == "EXPLAINED_DIFFERENCE"
    assert can_sign_off("explained_timing_difference")


def test_unexplained_difference_not_forced():
    packet = _packet(
        account_id="Cash",
        ledger_balance=10012.40,
        evidence_balance=10000,
        reconciling_items=[
            ReconcilingItem(
                item_id="DIFF",
                description="$12.40 unexplained",
                amount=12.40,
                source="cash_recon",
                classification="unexplained_difference",
            )
        ],
    )
    assert classify_packet(packet) == "unexplained_difference"
    reviewer = deterministic_review(packet, deterministic_prepare(packet))
    assert reviewer.sign_off is False
    assert reviewer.decision == "ESCALATE"


def test_missing_evidence_blocks_signoff():
    packet = _packet(
        ledger_balance=3600,
        evidence_balance=0,
        evidence_refs=[],
        missing_evidence=True,
    )
    assert classify_packet(packet) == "missing_evidence"
    reviewer = deterministic_review(packet, deterministic_prepare(packet))
    assert reviewer.decision == "REQUEST_EVIDENCE"
    assert reviewer.sign_off is False


def test_ledger_subledger_disagreement():
    packet = _packet(
        account_id="Accounts Receivable",
        ledger_balance=104500,
        evidence_balance=100000,
        reconciling_items=[
            ReconcilingItem(
                item_id="PAY-CLOSE-4500",
                description="unmatched payment",
                amount=4500,
                source="ar",
                classification="unexplained_difference",
            )
        ],
    )
    assert classify_packet(packet) == "unexplained_difference"


def test_reviewer_rejection_and_workflow_statuses(tmp_path, monkeypatch):
    monkeypatch.setattr("accrual.ledger.ACCRUALS_PATH", tmp_path / "open_accruals.json")
    monkeypatch.setattr("accrual.ledger.JOURNALS_PATH", tmp_path / "journal_entries.json")
    save_items(
        [
            PrepaidItem(
                prepaid_id="PRE-INS-001",
                vendor="Hartford Insurance",
                description="policy",
                source_document_id="DOC-INS-2026",
                total_amount=12000,
                start_date="2026-09-01",
                end_date="2027-08-31",
                initial_account="Prepaid Insurance",
                expense_account="Insurance Expense",
                evidence_refs=["DOC-INS-2026"],
                created_at="2026-09-01T00:00:00Z",
            )
        ]
    )
    report = run_balance_sheet_reconciliations("2026-09", scenario="clean")
    by_id = {item.account_id: item for item in report.reconciliations}
    assert by_id["Fixed Assets"].status in {"SIGNED_OFF", "MATCHED"}
    signed = [item for item in report.reconciliations if item.status == "SIGNED_OFF"]
    assert signed
    assert "Accumulated Depreciation" in by_id
    assert by_id["Accumulated Depreciation"].status in {"SIGNED_OFF", "MATCHED"}
    packet = _packet(missing_evidence=True, evidence_refs=[], ledger_balance=1, evidence_balance=0)
    reviewer = deterministic_review(packet, deterministic_prepare(packet))
    assert reviewer.decision != "APPROVE"
