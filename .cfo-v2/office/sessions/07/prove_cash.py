"""Session 07 disk proof. Writes bound case + ctl-cash packets onto the Computer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
KERNEL = REPO / ".cfo"
COMPUTER = REPO / ".cfo-v2" / "office" / "computer"
GRANTS = COMPUTER / "cfo" / "grants.json"

if str(KERNEL) not in sys.path:
    sys.path.insert(0, str(KERNEL))


def main() -> int:
    from cash_recon.case_store import case_path, configure_case_dir
    from cash_recon.handles import configure_handle_dirs, handles_dir, packets_dir
    from cash_recon.store import configure_paths, reset_cash_state
    from cash_recon.tools import unbind_case
    from cash_recon.workflow import run_cash_reconciliation
    from integrations.cash import reconcile_payout
    from integrations.store import get_payout

    runs = COMPUTER / "runs" / "cash_recon"
    configure_paths(runs_dir=runs, traces_dir=runs / "traces")
    configure_case_dir(runs / "cases")
    configure_handle_dirs(packets_dir=runs / "packets", handles_dir=runs / "handles")
    reset_cash_state()
    unbind_case()

    report = run_cash_reconciliation("2026-09", seed_demo=True, use_agent=False, reset=True)
    unexplained = next(item for item in report.matches if item.match_type == "UNEXPLAINED_DIFFERENCE")
    stripe = next(item for item in report.matches if item.provider == "stripe")
    payout = get_payout(stripe.provider_payout_id or "")
    breakdown = reconcile_payout(payout) if payout is not None else None

    grants = json.loads(GRANTS.read_text())
    for name in ("Cash Reconciliation Preparer", "Cash Exception Investigator"):
        ops = grants["byDisplayName"][name]["ops"]
        assert "accrual.tools.create_accrual" not in ops
        assert not any(item.startswith("scheduling.tools.") for item in ops)

    bound = case_path("2026-09")
    handle = handles_dir() / f"cash-{unexplained.reconciliation_id}-ctl-cash.json"
    packet = packets_dir() / f"cash-rec-{unexplained.reconciliation_id}.json"
    summary = {
        "period": report.period,
        "period_status": report.period_status,
        "arithmetic_tied": report.arithmetic_tied,
        "unexplained_difference_minor": unexplained.difference_minor,
        "unexplained_status": unexplained.status,
        "unexplained_matched": unexplained.status == "MATCHED",
        "stripe_payout_id": stripe.provider_payout_id,
        "stripe_provider_status": stripe.provider_status,
        "stripe_expected_payout_minor": breakdown.expected_payout_minor if breakdown else None,
        "stripe_actual_payout_minor": breakdown.actual_payout_minor if breakdown else None,
        "fee_journals_posted": any(
            entry.posted for match in report.matches for entry in match.proposed_adjusting_entries
        ),
        "bound_case": str(bound),
        "verifier_handle": str(handle),
        "verifier_packet": str(packet),
        "handle_queue_owner": json.loads(handle.read_text())["queueOwner"],
        "handle_human_queue": json.loads(handle.read_text())["humanQueue"],
        "handle_profile": json.loads(handle.read_text())["profile"],
    }
    out = runs / "session-07-summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
