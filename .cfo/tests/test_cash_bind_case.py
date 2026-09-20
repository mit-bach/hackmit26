"""Session 07: bound cash case survives a second process; $12.40 stays unexplained."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cash_recon.case_store import case_dir, case_path, load_bound_case
from cash_recon.handles import handles_dir, packets_dir
from cash_recon.tools import bind_case, read_candidate, read_match_candidates, unbind_case
from cash_recon.workflow import run_cash_reconciliation
from integrations.cash import reconcile_payout
from integrations.store import get_payout

REPO = Path(__file__).resolve().parents[2]
KERNEL = REPO / ".cfo"
GRANTS = REPO / ".cfo-v2" / "office" / "computer" / "cfo" / "grants.json"

CASH_DISPLAY_NAMES = (
    "Cash Reconciliation Preparer",
    "Cash Exception Investigator",
)

FORBIDDEN_OPS = (
    "accrual.tools.create_accrual",
    "accrual.tools.reconcile_accrual_with_invoice",
    "scheduling.tools.get_approved_pool",
    "scheduling.tools.get_payment_candidates",
    "scheduling.tools.get_cash_position",
    "scheduling.tools.get_treasury_policies",
)

CASH_OPS = (
    "cash_recon.tools.get_bank_transaction",
    "cash_recon.tools.get_ledger_entry",
    "cash_recon.tools.get_fee_evidence",
    "cash_recon.tools.get_match_candidates",
    "cash_recon.tools.get_candidate",
)


def test_seeded_12_40_is_not_matched_and_period_not_reconciled():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    unexplained = [item for item in report.matches if item.match_type == "UNEXPLAINED_DIFFERENCE"]
    assert len(unexplained) == 1
    item = unexplained[0]
    assert item.difference_minor == 1240
    assert item.status != "MATCHED"
    assert item.status == "HUMAN_REVIEW"
    assert item.human_review is True
    assert report.period_status != "RECONCILED"
    assert report.period_status == "OPEN"
    assert "Unexplained difference: $12.40" in item.explanation
    handle = handles_dir() / f"cash-{item.reconciliation_id}-ctl-cash.json"
    packet = packets_dir() / f"cash-rec-{item.reconciliation_id}.json"
    assert handle.exists()
    assert packet.exists()
    payload = json.loads(handle.read_text())
    assert payload["toSlug"] == "ctl-cash"
    assert payload["profile"] == "review-rec"
    assert payload["humanQueue"] is False
    assert payload["queueOwner"] == "ctl-cash"
    assert payload["kernelStatus"] == "HUMAN_REVIEW"


def test_bound_case_survives_unbind_and_second_process():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    unexplained = next(item for item in report.matches if item.match_type == "UNEXPLAINED_DIFFERENCE")
    case_file = case_path("2026-09")
    assert case_file.exists()
    raw = load_bound_case("2026-09")
    assert raw is not None
    assert raw["schema"] == "cfo.cash_recon.case.v1"
    assert raw["case_id"] == "2026-09"
    candidate_id = unexplained.candidate_id
    unbind_case()
    loaded = read_match_candidates("2026-09")
    assert loaded
    found = read_candidate(candidate_id)
    assert found.get("match_type") == "UNEXPLAINED_DIFFERENCE"
    assert found.get("difference_minor") == 1240

    script = (
        "from cash_recon.tools import unbind_case, read_candidate, read_match_candidates\n"
        "unbind_case()\n"
        "rows = read_match_candidates('2026-09')\n"
        f"row = read_candidate({candidate_id!r})\n"
        "assert rows, 'empty candidates after reload'\n"
        "assert row.get('match_type') == 'UNEXPLAINED_DIFFERENCE'\n"
        "assert row.get('difference_minor') == 1240\n"
        "assert row.get('status') != 'MATCHED'\n"
        "print('ok', row['difference_minor'])\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(KERNEL)
    env["CFO_CASH_CASE_DIR"] = str(case_dir())
    env["CFO_CASH_CASE_ID"] = "2026-09"
    env.pop("HARNESS_COMPUTER", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok 1240" in result.stdout


def test_stripe_payout_uses_kernel_waterfall_math():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    stripe = next(item for item in report.matches if item.match_type == "PROVIDER_PAYOUT" and item.provider == "stripe")
    assert stripe.provider_payout_id == "po_1HackMIT97420"
    assert stripe.provider_status == "MATCH"
    assert stripe.status == "MATCHED"
    payout = get_payout("po_1HackMIT97420")
    assert payout is not None
    breakdown = reconcile_payout(payout)
    assert breakdown.status == "MATCH"
    assert breakdown.expected_payout_minor == breakdown.actual_payout_minor
    evidence = " ".join(stripe.evidence)
    assert f"expected_payout:{breakdown.expected_payout_minor}" in evidence
    assert f"actual_payout:{breakdown.actual_payout_minor}" in evidence
    assert "provider:stripe" in evidence


def test_fee_journals_stay_unposted():
    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    fee = next(item for item in report.matches if item.match_type == "FEE_NETTED")
    assert fee.proposed_adjusting_entries
    assert all(not entry.posted for entry in fee.proposed_adjusting_entries)
    assert all(not entry.posted for match in report.matches for entry in match.proposed_adjusting_entries)
    raw = load_bound_case("2026-09")
    assert raw is not None
    for candidate in raw["candidates"]:
        for entry in candidate.get("proposed_adjusting_entries") or []:
            assert entry.get("posted") is False


def test_cash_grants_cannot_create_accrual_or_release_pay_run():
    grants = json.loads(GRANTS.read_text())
    by_name = grants["byDisplayName"]
    for display in CASH_DISPLAY_NAMES:
        ops = by_name[display]["ops"]
        assert ops == list(CASH_OPS)
        for forbidden in FORBIDDEN_OPS:
            assert forbidden not in ops
        assert not any(item.startswith("accrual.tools.") for item in ops)
        assert not any(item.startswith("scheduling.tools.") for item in ops)
        assert not any("release" in item for item in ops)
        assert not any("pay_run" in item or "pay-run" in item for item in ops)
    reviewer = by_name["Cash Reconciliation Reviewer"]["ops"]
    assert "accrual.tools.create_accrual" not in reviewer
