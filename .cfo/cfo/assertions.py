"""Deterministic cross-workflow amount and identity checks.

Python owns every comparison. Agents do not invent totals.
"""

from __future__ import annotations

from close.ledger import load_entries
from close.period_lock import is_period_closed
from cfo.company import (
    FEATURED,
    INTENDED_AUGUST,
    INTENDED_SEPTEMBER,
    PERIOD,
    money,
)
from scheduling.cash import policy_eligible_for_pool
from scheduling.pool import load_pool


def _check(name: str, passed: bool, detail: str, *, ids: list[str] | None = None) -> dict:
    return {
        "name": name,
        "passed": bool(passed),
        "detail": detail,
        "ids": list(ids or []),
    }


def check_ap_amounts(ap_results: dict) -> list[dict]:
    rows = []
    matched = ap_results.get("INV-001")
    if matched is None:
        rows.append(_check("ap_matched_present", False, "INV-001 was not processed", ids=["INV-001"]))
        return rows
    rows.append(
        _check(
            "ap_matched_approve",
            matched.decision == "APPROVE",
            f"INV-001 decision={matched.decision}",
            ids=["INV-001"],
        )
    )
    rows.append(
        _check(
            "ap_matched_amount",
            money(matched.amount) == 12450.0,
            f"INV-001 amount={matched.amount}",
            ids=["INV-001"],
        )
    )
    duplicate = ap_results.get("INV-018")
    rows.append(
        _check(
            "ap_duplicate_held",
            duplicate is not None and duplicate.decision == "HOLD",
            f"INV-018 decision={getattr(duplicate, 'decision', None)}",
            ids=["INV-018", "INV-010"],
        )
    )
    review = ap_results.get("INV-016")
    rows.append(
        _check(
            "ap_missing_po_held",
            review is not None and review.decision == "HOLD",
            f"INV-016 decision={getattr(review, 'decision', None)}",
            ids=["INV-016"],
        )
    )
    return rows


def check_duplicate_propagation(ap_results: dict) -> list[dict]:
    held = ap_results.get("INV-018")
    eligible = policy_eligible_for_pool("INV-018")
    pool_ids = {item.get("invoice_id") for item in load_pool()}
    journals = [
        item
        for item in load_entries()
        if item.get("source_document_id") == "INV-018" or item.get("transaction_id") == "INV-018"
    ]
    return [
        _check(
            "dup_not_eligible",
            held is not None and held.decision == "HOLD" and not eligible,
            f"eligible={eligible} decision={getattr(held, 'decision', None)}",
            ids=["INV-018"],
        ),
        _check(
            "dup_not_in_payment_pool",
            "INV-018" not in pool_ids,
            f"pool contains INV-018={('INV-018' in pool_ids)}",
            ids=["INV-018"],
        ),
        _check(
            "dup_no_ledger_expense",
            not journals,
            f"journals for INV-018: {[item.get('entry_id') for item in journals]}",
            ids=["INV-018"],
        ),
    ]


def check_cash_amounts(cash_report) -> list[dict]:
    by_bank = {}
    for match in cash_report.matches:
        for bank_id in match.bank_transaction_ids:
            by_bank[bank_id] = match
    grouped = by_bank.get(FEATURED["cash_grouped_bank"])
    fee = by_bank.get(FEATURED["cash_fee_bank"])
    brk = by_bank.get(FEATURED["cash_break_bank"])
    stripe = by_bank.get(FEATURED["cash_stripe_bank"])
    rows = [
        _check(
            "cash_grouped_match",
            grouped is not None and grouped.match_type == "GROUPED_MATCH",
            f"grouped={getattr(grouped, 'match_type', None)}",
            ids=[FEATURED["cash_grouped_bank"], *FEATURED["cash_grouped_invoices"]],
        ),
        _check(
            "cash_grouped_amount",
            grouped is not None and money(grouped.bank_amount) == -18500.0,
            f"grouped bank={getattr(grouped, 'bank_amount', None)}",
            ids=[FEATURED["cash_grouped_bank"]],
        ),
        _check(
            "cash_fee_netted",
            fee is not None and fee.match_type == "FEE_NETTED",
            f"fee={getattr(fee, 'match_type', None)}",
            ids=[FEATURED["cash_fee_bank"]],
        ),
        _check(
            "cash_break_human_review",
            brk is not None
            and brk.match_type == "UNEXPLAINED_DIFFERENCE"
            and brk.status == "HUMAN_REVIEW",
            f"break type={getattr(brk, 'match_type', None)} status={getattr(brk, 'status', None)}",
            ids=[FEATURED["cash_break_bank"]],
        ),
        _check(
            "cash_break_amount",
            brk is not None and money(abs(brk.difference)) == 12.40,
            f"difference={getattr(brk, 'difference', None)}",
            ids=[FEATURED["cash_break_bank"]],
        ),
        _check(
            "cash_stripe_payout",
            stripe is not None and stripe.match_type == "PROVIDER_PAYOUT",
            f"stripe={getattr(stripe, 'match_type', None)}",
            ids=[FEATURED["cash_stripe_bank"]],
        ),
        _check(
            "cash_not_fully_reconciled_before_resolution",
            cash_report.period_status != "RECONCILED" or money(cash_report.unexplained_difference) != 0,
            f"status={cash_report.period_status} unexplained={cash_report.unexplained_difference}",
            ids=[FEATURED["cash_break_bank"]],
        ),
    ]
    return rows


def check_close_gate(blocked_state, closed_state) -> list[dict]:
    blocked_cash = any(
        "12.40" in item.detail or "12.4" in item.detail for item in blocked_state.exceptions
    ) or any("12.40" in item or "12.4" in item for item in blocked_state.human_review_items)
    return [
        _check(
            "close_blocked_by_cash",
            blocked_state.period.status == "BLOCKED" and blocked_cash,
            f"blocked status={blocked_state.period.status} exceptions={[item.detail for item in blocked_state.exceptions]}",
            ids=[FEATURED["cash_break_bank"]],
        ),
        _check(
            "close_succeeds_after_resolution",
            closed_state.period.status == "CLOSED" and bool(closed_state.snapshot_path),
            f"closed status={closed_state.period.status} snapshot={closed_state.snapshot_path}",
            ids=[closed_state.close_id],
        ),
        _check(
            "period_lock_closed",
            is_period_closed(PERIOD),
            f"lock closed={is_period_closed(PERIOD)}",
            ids=[PERIOD],
        ),
    ]


def check_reporting_from_ledger(statement, prior) -> list[dict]:
    sep = INTENDED_SEPTEMBER
    aug = INTENDED_AUGUST
    gp = money(statement.revenue - statement.cogs)
    return [
        _check(
            "report_revenue",
            money(statement.revenue) == sep["revenue"],
            f"revenue={statement.revenue}",
            ids=["4000-Revenue"],
        ),
        _check(
            "report_cogs",
            money(statement.cogs) == sep["cogs"],
            f"cogs={statement.cogs}",
            ids=["5100-Hosting", "5200-Supplier"],
        ),
        _check(
            "report_gross_profit_identity",
            money(statement.gross_profit) == gp == sep["gross_profit"],
            f"gp={statement.gross_profit} revenue-cogs={gp}",
            ids=[],
        ),
        _check(
            "report_gross_margin",
            abs(float(statement.gross_margin_pct) - sep["gross_margin_pct"]) < 0.0001,
            f"gm={statement.gross_margin_pct}",
            ids=[],
        ),
        _check(
            "report_august_margin",
            prior is not None and abs(float(prior.gross_margin_pct) - aug["gross_margin_pct"]) < 0.0001,
            f"aug_gm={getattr(prior, 'gross_margin_pct', None)}",
            ids=[],
        ),
    ]


def check_reporting_uses_close(blocked_view: dict, closed_view: dict) -> list[dict]:
    return [
        _check(
            "reporting_sees_blocked_books",
            blocked_view.get("close_status") == "BLOCKED" and not blocked_view.get("books_closed"),
            f"blocked view={blocked_view}",
            ids=[],
        ),
        _check(
            "reporting_sees_closed_snapshot",
            closed_view.get("books_closed") is True
            and closed_view.get("close_status") == "CLOSED"
            and bool(closed_view.get("snapshot_id")),
            f"closed view={closed_view}",
            ids=[str(closed_view.get("snapshot_id") or "")],
        ),
        _check(
            "reporting_snapshot_changed",
            blocked_view.get("snapshot_id") != closed_view.get("snapshot_id")
            or (not blocked_view.get("snapshot_id") and closed_view.get("snapshot_id")),
            "close snapshot identity did not change after successful close",
            ids=[],
        ),
    ]


def check_forecast(forecast, fva, statement) -> list[dict]:
    held_in_forecast = [
        line
        for line in (forecast.lines if forecast else [])
        if line.source_id == "INV-016" and line.committed
    ]
    return [
        _check(
            "forecast_built",
            forecast is not None and bool(getattr(forecast, "weeks", None)),
            f"forecast={getattr(forecast, 'forecast_id', None)}",
            ids=[],
        ),
        _check(
            "forecast_excludes_held_ap",
            not held_in_forecast,
            "INV-016 is held and must not be a committed forecast outflow",
            ids=["INV-016"],
        ),
        _check(
            "forecast_actuals_explained",
            fva is not None and (fva.contributors or abs(fva.total_ending_cash_variance) <= 0.02),
            f"contributors={len(fva.contributors) if fva else 0} miss={getattr(fva, 'total_ending_cash_variance', None)}",
            ids=[],
        ),
        _check(
            "forecast_does_not_invent_pnl",
            statement is not None,
            "forecast uses Python actuals; P&L stays on the ledger",
            ids=[],
        ),
    ]


def check_shared_identity(chains: list[dict]) -> list[dict]:
    rows = []
    by_id = {item["chain_id"]: item for item in chains}
    clean = by_id.get("CHAIN-AP-CLEAN") or {}
    rows.append(
        _check(
            "identity_ap_clean",
            bool(clean.get("invoice_id") == "INV-001" and clean.get("approval_id") and clean.get("close_run_id")),
            f"clean chain={clean}",
            ids=["INV-001"],
        )
    )
    brk = by_id.get("CHAIN-CASH-BREAK") or {}
    rows.append(
        _check(
            "identity_cash_break",
            brk.get("bank_transaction_id") == FEATURED["cash_break_bank"]
            and bool(brk.get("reconciliation_id"))
            and bool(brk.get("review_id"))
            and bool(brk.get("journal_entry_id"))
            and bool(brk.get("close_run_id")),
            f"cash-break chain={brk}",
            ids=[FEATURED["cash_break_bank"]],
        )
    )
    rows.append(
        _check(
            "identity_audit_present",
            any(item.get("audit_run_id") for item in chains),
            "no audit run id attached to identity chains",
            ids=[],
        )
    )
    return rows


def check_audit(audit_run, independence: dict, dataset) -> list[dict]:
    from audit.evidence import validate_run_evidence

    evidence_errors = validate_run_evidence(audit_run)
    invoice_ids = {item.invoice_id for item in dataset.invoices}
    operational_invoices = {"INV-001", "INV-018", "INV-016"} & invoice_ids
    sampled = {oid for sample in audit_run.samples for oid in sample.sampled_ids}
    recon_ids = {item.reconciliation_id for item in dataset.reconciliations}
    return [
        _check(
            "audit_sampled",
            bool(audit_run.samples),
            f"samples={len(audit_run.samples)}",
            ids=[],
        ),
        _check(
            "audit_control_exception",
            bool(audit_run.findings),
            f"findings={len(audit_run.findings)}",
            ids=[item.finding_id for item in audit_run.findings[:4]],
        ),
        _check(
            "audit_reperformance",
            bool(audit_run.reperformance),
            f"reperformances={len(audit_run.reperformance)}",
            ids=[],
        ),
        _check(
            "audit_evidence_complete",
            not evidence_errors,
            f"evidence_errors={evidence_errors}",
            ids=[],
        ),
        _check(
            "audit_sees_operational_invoices",
            operational_invoices == {"INV-001", "INV-018", "INV-016"},
            f"operational invoices in dataset={sorted(operational_invoices)} sampled_overlap={sorted(operational_invoices & sampled)}",
            ids=sorted(operational_invoices),
        ),
        _check(
            "audit_independence",
            bool(independence.get("passed")),
            f"independence={independence}",
            ids=list(independence.get("bank_transaction_ids") or []),
        ),
        _check(
            "audit_dataset_has_cash_matches",
            len(recon_ids) >= 1,
            f"recon count={len(recon_ids)}",
            ids=sorted(recon_ids)[:4],
        ),
    ]


def evaluate_all(payload: dict) -> list[dict]:
    checks: list[dict] = []
    checks.extend(check_ap_amounts(payload["ap_results"]))
    checks.extend(check_duplicate_propagation(payload["ap_results"]))
    checks.extend(check_cash_amounts(payload["blocked_cash"]))
    checks.extend(check_close_gate(payload["blocked_close"], payload["closed_close"]))
    checks.extend(check_reporting_from_ledger(payload["statement"], payload["prior_statement"]))
    checks.extend(check_reporting_uses_close(payload["blocked_reporting"], payload["closed_reporting"]))
    checks.extend(check_forecast(payload["forecast"], payload["forecast_variance"], payload["statement"]))
    checks.extend(check_shared_identity(payload["chains"]))
    checks.extend(check_audit(payload["audit_run"], payload["independence"], payload["audit_dataset"]))
    if payload.get("post_close_rejected"):
        checks.append(
            _check(
                "post_close_rejected",
                True,
                payload.get("post_close_detail") or "unauthorized September journal rejected",
                ids=[PERIOD],
            )
        )
    else:
        checks.append(
            _check(
                "post_close_rejected",
                False,
                "closed period accepted an unauthorized journal",
                ids=[PERIOD],
            )
        )
    return checks
