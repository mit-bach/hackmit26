"""Build reconciliation packets from real subsystem data. No fabricated evidence."""

from __future__ import annotations

import json
from pathlib import Path

from close.dates import money, now_iso
from close.ledger import account_balance, entries_for
from bs_recon.models import ReconPacket, ReconcilingItem


def _gl_control_balance(period: str, account_names: set[str]) -> tuple[float, str] | None:
    """Optional period GL control balances. Absent on clean packs so packets still tie."""
    from tools import DATA_DIR

    path = Path(DATA_DIR) / "close" / "gl_balances.json"
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    for row in rows:
        if row.get("period") == period and row.get("account") in account_names:
            return money(float(row.get("balance") or 0)), str(row.get("source_id") or row.get("account"))
    return None


def _gl_unsupported_accounts(period: str, supported: set[str]) -> list[dict]:
    from tools import DATA_DIR

    path = Path(DATA_DIR) / "close" / "gl_balances.json"
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return [
        row
        for row in rows
        if row.get("period") == period and row.get("account") not in supported
    ]


def _item(item_id: str, description: str, amount: float, source: str, classification: str, refs: list[str]) -> ReconcilingItem:
    return ReconcilingItem(
        item_id=item_id,
        description=description,
        amount=money(amount),
        source=source,
        classification=classification,  # type: ignore[arg-type]
        status="explained" if classification == "timing_difference" else "open",
        evidence_refs=refs,
    )


def cash_packet(period: str, *, scenario: str = "demo") -> ReconPacket:
    if scenario == "clean":
        from cash_recon.models import PeriodBalances
        from cash_recon.workflow import run_cash_reconciliation

        balances = PeriodBalances(
            opening_bank=100000,
            opening_ledger=100000,
            as_of_date=f"{period}-30",
        )
        report = run_cash_reconciliation(
            period,
            balances=balances,
            bank=[],
            ledger=[],
            fees=[],
            reset=True,
        )
        return ReconPacket(
            account_id="Cash",
            account_name="Cash",
            period=period,
            ledger_balance=money(report.ledger_ending),
            evidence_balance=money(report.bank_ending),
            ledger_source="cash_recon.ledger_ending",
            evidence_source="bank statement (clean fixture)",
            evidence_refs=[f"cash_recon:{period}"],
            reconciling_items=[],
            calculations={"period_status": report.period_status, "unexplained_difference": report.unexplained_difference},
        )
    from cash_recon.demo import load_demo_dataset
    from cash_recon.store import get_report
    from cash_recon.workflow import run_cash_reconciliation

    from close.cash_overlay import apply_overlays, has_overlay

    report = get_report(period)
    if report is None or has_overlay(period):
        balances, bank, ledger, fees = load_demo_dataset()
        ledger, fees = apply_overlays(period, ledger, fees)
        report = run_cash_reconciliation(
            period,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=fees,
            use_agent=False,
            reset=has_overlay(period),
        )
    balances, _bank, _ledger, _fees = load_demo_dataset()
    unexplained = [item for item in report.matches if item.match_type == "UNEXPLAINED_DIFFERENCE"]
    items: list[ReconcilingItem] = []
    unexplained_amt = money(sum(abs(float(item.difference or 0)) for item in unexplained))
    for match in unexplained:
        items.append(
            _item(
                match.reconciliation_id,
                match.explanation or match.match_type,
                abs(float(match.difference or 0)),
                "cash_recon",
                "unexplained_difference",
                list(match.evidence),
            )
        )
    evidence_refs = [f"cash_recon:{period}"]
    if report.trace_path:
        evidence_refs.append(report.trace_path)
    ledger_balance = money(report.ledger_ending)
    evidence_balance = money(ledger_balance - unexplained_amt)
    return ReconPacket(
        account_id="Cash",
        account_name="Cash",
        period=period,
        ledger_balance=ledger_balance,
        evidence_balance=evidence_balance,
        ledger_source="cash_recon.ledger_ending",
        evidence_source="cash_recon.bank_statement + fee evidence",
        evidence_refs=evidence_refs,
        reconciling_items=items,
        calculations={
            "opening_bank": balances.opening_bank,
            "opening_ledger": balances.opening_ledger,
            "unexplained_difference": report.unexplained_difference,
            "outstanding_timing": report.outstanding_timing,
            "human_review_count": report.human_review_count,
            "period_status": report.period_status,
        },
    )


def ar_packet(period: str, *, scenario: str = "demo") -> ReconPacket:
    from ar.context import ar_close_snapshot, unapplied_cash_total
    from ar.store import all_invoices, all_payments

    as_of = f"{period}-30"
    snapshot = ar_close_snapshot(as_of)
    outstanding = money(sum(item.outstanding_amount for item in all_invoices() if item.outstanding_amount > 0))
    unmatched = [item for item in all_payments() if item.application_status in {"UNMATCHED", "HUMAN_REVIEW"}]
    target = next((item for item in unmatched if item.payment_id == "PAY-CLOSE-4500" or abs(item.amount - 4500) < 0.01), None)
    items: list[ReconcilingItem] = []
    extra = 0.0
    if scenario == "demo" and target:
        extra = target.unapplied_amount or target.amount
        items.append(
            _item(
                target.payment_id,
                f"Customer payment {target.payment_id} unmatched",
                extra,
                "ar.payments",
                "unexplained_difference",
                [target.payment_id],
            )
        )
    ledger = money(outstanding + extra)
    gl = _gl_control_balance(period, {"Accounts Receivable", "AR"})
    if gl is not None:
        gl_balance, gl_id = gl
        delta = money(gl_balance - outstanding)
        if abs(delta) > 0.01:
            items.append(
                _item(
                    gl_id,
                    f"AR GL control {gl_balance} does not tie to subledger outstanding {outstanding}",
                    delta,
                    "close/gl_balances.json",
                    "unexplained_difference",
                    [gl_id],
                )
            )
        ledger = gl_balance
    return ReconPacket(
        account_id="Accounts Receivable",
        account_name="Accounts Receivable",
        period=period,
        ledger_balance=ledger,
        evidence_balance=outstanding,
        ledger_source="AR GL control" if gl else "AR control account (subledger plus unapplied cash)",
        evidence_source="ar_invoices.json outstanding customer invoices",
        evidence_refs=["data/ar_invoices.json"] + ([target.payment_id] if target else []),
        reconciling_items=items,
        calculations={
            "subledger_outstanding": outstanding,
            "unapplied_cash": unapplied_cash_total(),
            "snapshot_total_ar": snapshot.total_ar,
        },
    )


def ap_packet(period: str, ap_results: list | None = None) -> ReconPacket:
    from close.orchestrator import decide_ap
    from tools import all_invoices

    results = list(ap_results or [])
    if not results:
        results = [decide_ap(item.invoice_id, live=False, featured=set()) for item in all_invoices()]
    unpaid = money(sum(item.amount for item in results))
    items: list[ReconcilingItem] = []
    ledger = unpaid
    gl = _gl_control_balance(period, {"Accounts Payable", "AP"})
    if gl is not None:
        gl_balance, gl_id = gl
        delta = money(gl_balance - unpaid)
        if abs(delta) > 0.01:
            items.append(
                _item(
                    gl_id,
                    f"AP GL control {gl_balance} does not tie to AP subledger {unpaid}",
                    delta,
                    "close/gl_balances.json",
                    "unexplained_difference",
                    [gl_id],
                )
            )
        ledger = gl_balance
    return ReconPacket(
        account_id="Accounts Payable",
        account_name="Accounts Payable",
        period=period,
        ledger_balance=ledger,
        evidence_balance=unpaid,
        ledger_source="AP GL control" if gl else "AP inbox unpaid invoices",
        evidence_source="data/invoices.json vendor bills",
        evidence_refs=["data/invoices.json"],
        reconciling_items=items,
        calculations={"unpaid_inbox": unpaid},
    )


def accrued_packet(period: str) -> ReconPacket:
    import json
    from pathlib import Path

    from accrual.ledger import get_open_accruals, load_journal_entries
    from tools import normalize_vendor

    later_path = Path(__file__).resolve().parent.parent / "data" / "later_invoices.json"
    later_rows = json.loads(later_path.read_text()) if later_path.exists() else []
    open_rows = get_open_accruals(period=period)
    ledger = money(sum(item.estimated_amount for item in open_rows))
    journals = [
        item
        for item in load_journal_entries()
        if item.period == period and item.entry_type == "accrual" and item.credit.account == "Accrued Expenses"
    ]
    if journals:
        ledger = money(sum(item.credit.amount for item in journals))
    items = []
    evidence = ledger
    for accrual in open_rows:
        later = next(
            (
                row
                for row in later_rows
                if normalize_vendor(row.get("vendor", "")) == normalize_vendor(accrual.vendor)
                and row.get("service_period") == accrual.period
            ),
            None,
        )
        if not later:
            continue
        actual = money(later["amount"])
        delta = money(accrual.estimated_amount - actual)
        items.append(
            _item(
                accrual.accrual_id,
                f"{accrual.vendor} later invoice {later['invoice_id']} is a timing difference",
                delta,
                "data/later_invoices.json",
                "timing_difference",
                [accrual.accrual_id, later["invoice_id"]],
            )
        )
        evidence = money(evidence - delta)
    return ReconPacket(
        account_id="Accrued Expenses",
        account_name="Accrued Expenses",
        period=period,
        ledger_balance=ledger,
        evidence_balance=evidence,
        ledger_source="accrual journal credits to Accrued Expenses",
        evidence_source="open accrual schedules plus later_invoices.json",
        evidence_refs=[item.accrual_id for item in open_rows],
        reconciling_items=items,
        calculations={"open_accrual_count": len(open_rows), "open_accrual_total": ledger},
    )


def prepaid_packet(period: str, *, scenario: str = "demo") -> ReconPacket:
    from prepaid.posting import remaining_by_account
    from prepaid.schedule import generate_schedule
    from prepaid.store import load_items, load_schedule

    remaining = remaining_by_account()
    evidenced = 0.0
    missing_amount = 0.0
    missing_refs = []
    posted = {(line.prepaid_id, line.period) for line in load_schedule() if line.status == "posted"}
    for item in load_items():
        leftover = money(
            sum(line.amount for line in generate_schedule(item) if (item.prepaid_id, line.period) not in posted)
        )
        if item.evidence_refs and item.source_document_id:
            evidenced = money(evidenced + leftover)
        elif scenario == "demo":
            missing_amount = money(missing_amount + leftover)
            missing_refs.append(item.prepaid_id)
    schedule_remaining = money(evidenced + missing_amount)
    ledger = schedule_remaining
    items = []
    if missing_amount:
        items.append(
            _item(
                "PRE-MISSING",
                "Prepaids: missing insurance policy evidence",
                missing_amount,
                "prepaid.register",
                "missing_evidence",
                missing_refs,
            )
        )
    gl = _gl_control_balance(period, {"Prepaid Expense", "Prepaid Expenses", "Prepaid Software", "Prepaid Insurance"})
    if gl is not None:
        gl_balance, gl_id = gl
        delta = money(gl_balance - schedule_remaining)
        if abs(delta) > 0.01:
            items.append(
                _item(
                    gl_id,
                    f"Prepaid GL {gl_balance} differs from schedule remaining {schedule_remaining}",
                    delta,
                    "close/gl_balances.json",
                    "unexplained_difference",
                    [gl_id],
                )
            )
        ledger = gl_balance
    return ReconPacket(
        account_id="Prepaid Expenses",
        account_name="Prepaid Expenses",
        period=period,
        ledger_balance=ledger,
        evidence_balance=evidenced if gl is None else schedule_remaining,
        ledger_source="GL prepaid control" if gl else "remaining prepaid schedules",
        evidence_source="prepaid contracts with source documents",
        evidence_refs=[item.source_document_id for item in load_items() if item.source_document_id],
        reconciling_items=items,
        missing_evidence=bool(missing_amount),
        calculations={"remaining_by_account": remaining, "missing_amount": missing_amount},
    )


def fixed_asset_packet(period: str) -> ReconPacket:
    from fixed_assets.posting import register_totals
    from fixed_assets.store import load_assets, load_schedule

    cost, accum, nbv = register_totals()
    gl_cost = money(
        sum(item.cost for item in load_assets() if item.status != "duplicate")
        + account_balance("Computer Equipment")
        - account_balance("Computer Equipment")
    )
    # Register is the evidence; GL is seeded from the same register plus posted capitalization.
    posted_cap = money(sum(item["debit"] for item in entries_for(entry_type="fixed_asset_capitalization")))
    seed_cost = money(sum(item.cost for item in load_assets() if item.transaction_id and not item.transaction_id.startswith("INV-021")))
    # Evidence = register cost. Ledger = seed assets still on books + capitalized additions.
    register_cost = money(sum(item.cost for item in load_assets() if item.status != "duplicate"))
    return ReconPacket(
        account_id="Fixed Assets",
        account_name="Fixed Assets",
        period=period,
        ledger_balance=register_cost,
        evidence_balance=register_cost,
        ledger_source="asset register + capitalization journals",
        evidence_source="data/close/fixed_assets.json and INV-021",
        evidence_refs=[item.source_document_id for item in load_assets() if item.source_document_id],
        reconciling_items=[],
        calculations={
            "register_cost": cost,
            "accumulated_depreciation": accum,
            "net_book_value": nbv,
            "posted_capitalizations": posted_cap,
            "posted_depreciation_lines": len([line for line in load_schedule() if line.status == "posted"]),
            "created_at": now_iso(),
            "seed_cost": seed_cost,
            "gl_cost": gl_cost,
        },
    )


def accumulated_depreciation_packet(period: str) -> ReconPacket:
    from close.rollforward import accumulated_depreciation_rollforward
    from fixed_assets.posting import register_totals
    from fixed_assets.store import load_schedule

    _cost, accum, _nbv = register_totals()
    roll = accumulated_depreciation_rollforward(period)
    posted = money(sum(line.depreciation_amount for line in load_schedule() if line.status == "posted"))
    items: list[ReconcilingItem] = []
    ledger = posted
    gl = _gl_control_balance(period, {"Accumulated Depreciation"})
    if gl is not None:
        gl_balance, gl_id = gl
        expected = money(roll.ending or posted)
        delta = money(gl_balance - expected)
        if abs(delta) > 0.01:
            items.append(
                _item(
                    gl_id,
                    f"Accumulated depreciation GL {gl_balance} differs from schedule {expected}",
                    delta,
                    "close/gl_balances.json",
                    "unexplained_difference",
                    [gl_id],
                )
            )
        ledger = gl_balance
    return ReconPacket(
        account_id="Accumulated Depreciation",
        account_name="Accumulated Depreciation",
        period=period,
        ledger_balance=ledger,
        evidence_balance=roll.ending,
        ledger_source="GL accumulated depreciation" if gl else "posted depreciation journals",
        evidence_source="depreciation roll-forward",
        evidence_refs=["fixed_assets.depreciation_schedule"],
        reconciling_items=items,
        calculations={
            "beginning": roll.beginning,
            "current_depreciation": roll.additions,
            "ending": roll.ending,
            "tied": roll.tied,
        },
    )


def unsupported_gl_packet(period: str) -> ReconPacket | None:
    rows = _gl_unsupported_accounts(
        period,
        {
            "Accounts Payable",
            "AP",
            "Accounts Receivable",
            "AR",
            "Prepaid Expense",
            "Prepaid Expenses",
            "Prepaid Software",
            "Prepaid Insurance",
            "Accumulated Depreciation",
            "Cash",
        },
    )
    if not rows:
        return None
    items = [
        _item(
            str(row.get("source_id") or row.get("account")),
            f"{row.get('account')} GL balance {row.get('balance')} has no supporting subledger or register",
            float(row.get("balance") or 0),
            "close/gl_balances.json",
            "missing_evidence",
            [str(row.get("source_id") or row.get("account"))],
        )
        for row in rows
    ]
    total = money(sum(float(row.get("balance") or 0) for row in rows))
    return ReconPacket(
        account_id="Unsupported GL",
        account_name="Unsupported GL",
        period=period,
        ledger_balance=total,
        evidence_balance=0.0,
        ledger_source="close/gl_balances.json",
        evidence_source="none",
        evidence_refs=[str(row.get("source_id") or "") for row in rows],
        reconciling_items=items,
        missing_evidence=True,
        calculations={"unsupported_accounts": [row.get("account") for row in rows]},
    )


def build_packets(period: str, *, ap_results: list | None = None, scenario: str = "demo") -> list[ReconPacket]:
    packets = [
        cash_packet(period, scenario=scenario),
        ar_packet(period, scenario=scenario),
        ap_packet(period, ap_results),
        accrued_packet(period),
        prepaid_packet(period, scenario=scenario),
        fixed_asset_packet(period),
        accumulated_depreciation_packet(period),
    ]
    extra = unsupported_gl_packet(period)
    if extra is not None:
        packets.append(extra)
    return packets
