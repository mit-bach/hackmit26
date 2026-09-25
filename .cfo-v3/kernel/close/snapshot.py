"""Persisted close snapshots. History is append-only; old snapshots are never overwritten."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import now_iso
from close.models import CloseSnapshot, MonthEndState

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runs" / "month_end"
SNAPSHOT_DIR = STATE_DIR / "snapshots"


def configure_paths(directory: Path) -> None:
    global STATE_DIR, SNAPSHOT_DIR
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    STATE_DIR = directory
    SNAPSHOT_DIR = directory / "snapshots"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def snapshot_dir() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def list_snapshots(period: str = "") -> list[CloseSnapshot]:
    rows: list[CloseSnapshot] = []
    if not SNAPSHOT_DIR.exists():
        return rows
    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        item = CloseSnapshot.model_validate(payload)
        if period and item.period != period:
            continue
        rows.append(item)
    return rows


def latest_snapshot(period: str) -> CloseSnapshot | None:
    rows = list_snapshots(period)
    return rows[-1] if rows else None


def save_snapshot(snapshot: CloseSnapshot) -> str:
    path = snapshot_dir() / f"{snapshot.snapshot_id}.json"
    if path.exists():
        return str(path)
    path.write_text(snapshot.model_dump_json(indent=2) + "\n")
    return str(path)


def snapshot_id_for(period: str, timestamp: str | None = None) -> str:
    stamp = (timestamp or now_iso()).replace(":", "").replace("-", "")
    seq = len(list(snapshot_dir().glob(f"{period}-*.json"))) + 1
    return f"{period}-{stamp}-{seq:02d}"


def build_snapshot(state: MonthEndState, *, reopen_of: str | None = None) -> CloseSnapshot:
    from bs_recon.store import load_reconciliations
    from close.ledger import account_balance, load_entries
    from close.rollforward import build_rollforwards
    from close.resolve import load_resolutions

    timestamp = now_iso()
    snap_id = snapshot_id_for(state.period.period, timestamp)
    recs = [item.model_dump() for item in load_reconciliations(state.period.period)]
    rolls = {item.account: item for item in (state.roll_forwards or build_rollforwards(state.period.period))}
    approvals = [
        {"reconciliation_id": item.get("reconciliation_id"), "status": item.get("status"), "review_decision": item.get("review_decision")}
        for item in recs
        if item.get("status") in {"SIGNED_OFF", "MATCHED", "EXPLAINED_DIFFERENCE"}
    ]
    cash_state = {
        "status": state.cash_status,
        "human_review_items": list(state.human_review_items),
    }
    try:
        from cash_recon.store import get_report

        report = get_report(state.period.period)
        if report:
            cash_state.update(
                {
                    "bank_ending": report.bank_ending,
                    "ledger_ending": report.ledger_ending,
                    "unexplained_difference": report.unexplained_difference,
                    "period_status": report.period_status,
                    "arithmetic_tied": report.arithmetic_tied,
                    "human_review_count": report.human_review_count,
                }
            )
    except Exception:
        pass
    ledger_balances = {}
    for account in (
        "Cash",
        "Accounts Receivable",
        "Accounts Payable",
        "Accrued Expenses",
        "Prepaid Insurance",
        "Prepaid Software",
        "Prepaid Rent",
        "Computer Equipment",
        "Machinery",
        "Capitalized Software",
        "Accumulated Depreciation - Equipment",
        "Accumulated Depreciation - Machinery",
        "Accumulated Amortization - Software",
        "Insurance Expense",
        "Depreciation Expense",
    ):
        ledger_balances[account] = account_balance(account)
    ar_balance = state.ar.total_ar if state.ar else 0.0
    ap_balance = sum(item.amount for item in state.ap_results if item.decision == "HOLD")
    accrual_total = state.accrual.total_accrued_expense if state.accrual else 0.0
    return CloseSnapshot(
        snapshot_id=snap_id,
        period=state.period.period,
        close_timestamp=timestamp,
        close_status=state.period.status,
        ledger_balances=ledger_balances,
        ap_balance=ap_balance,
        ar_balance=ar_balance,
        cash_reconciliation=cash_state,
        accrual_balances={"accrued_expenses": accrual_total},
        prepaid_rollforward=rolls.get("Prepaid Expenses"),
        fixed_asset_rollforward=rolls.get("Fixed Assets"),
        accumulated_depreciation_rollforward=rolls.get("Accumulated Depreciation"),
        account_reconciliations=recs,
        unresolved_items=list(state.human_review_items),
        journal_entry_ids=[item["entry_id"] for item in load_entries() if item.get("period") == state.period.period],
        reviewer_approvals=approvals,
        audit_trace_refs=[state.trace_path] if state.trace_path else [],
        resolutions=load_resolutions(state.period.period),
        tasks=list(state.tasks),
        reopen_of=reopen_of,
    )
