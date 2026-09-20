"""Judge-facing Office-of-the-CFO demo narrative. Numbers come from executed workflows."""

from __future__ import annotations

from cfo.company import COMPANY_NAME, FEATURED, HEADQUARTERS, PERIOD, money
from cfo.eval import format_metrics
from cfo.scenario import invoice_summary


def _usd(value: float | None) -> str:
    return f"${money(value):,.2f}"


def _match_line(report, bank_id: str) -> str:
    if report is None:
        return f"{bank_id}  (no cash report)"
    for match in report.matches:
        if bank_id in match.bank_transaction_ids:
            return (
                f"{bank_id}  {match.match_type}/{match.status}  "
                f"bank={_usd(match.bank_amount)}  diff={_usd(abs(match.difference))}  "
                f"{match.reconciliation_id}"
            )
    return f"{bank_id}  (unmatched in report)"


def _human_block(rows: list[dict]) -> str:
    if not rows:
        return "- (none)"
    lines = []
    for item in rows:
        lines.append(
            f"- {item['status']}  {item['workflow']}  {item['object_id']}\n"
            f"    missing/conflict: {item['missing_or_conflict']}\n"
            f"    required: {item['required_decision']}"
        )
    return "\n".join(lines)


def _handoff_block(rows: list[dict]) -> str:
    if not rows:
        return "- (none)"
    return "\n".join(
        f"- {item['workflow']}  {item['object_id']}  {' → '.join(item['roles'])}  {item['output']}"
        for item in rows
    )


def _chain_block(chain: dict) -> str:
    steps = [
        ("invoice_id", chain.get("invoice_id")),
        ("approval_id", chain.get("approval_id")),
        ("payment_id", chain.get("payment_id")),
        ("bank_transaction_id", chain.get("bank_transaction_id")),
        ("reconciliation_id", chain.get("reconciliation_id")),
        ("journal_entry_id", chain.get("journal_entry_id")),
        ("review_id", chain.get("review_id")),
        ("close_run_id", chain.get("close_run_id")),
        ("snapshot_id", chain.get("snapshot_id")),
        ("report_line", chain.get("report_line")),
        ("variance_driver", chain.get("variance_driver")),
        ("audit_run_id", chain.get("audit_run_id")),
    ]
    filled = [f"{label}={value}" for label, value in steps if value]
    amount = f"  amount={_usd(chain['amount'])}" if chain.get("amount") is not None else ""
    status = f"  {chain['status']}" if chain.get("status") else ""
    return f"{chain['chain_id']}  {chain['label']}{status}{amount}\n    " + " → ".join(filled)


def format_cfo_demo(payload: dict) -> str:
    opening = payload["opening"]
    ap = payload["ap_results"]
    ar = payload["ar_demo"]
    blocked_cash = payload["blocked_cash"]
    closed_cash = payload["closed_cash"]
    blocked = payload["blocked_close"]
    closed = payload["closed_close"]
    statement = payload["statement"]
    prior = payload["prior_statement"]
    reporting = payload["reporting_run"]
    fva = payload["forecast_variance"]
    audit = payload["audit_run"]
    independence = payload["independence"]
    inventory = payload["inventory"]

    inv_lines = [f"- {name}: {', '.join(items)}" for name, items in inventory.items()]
    ap_lines = []
    for invoice_id, result in ap.items():
        extra = f"  exceptions={', '.join(result.exceptions)}" if result.exceptions else ""
        ap_lines.append(
            f"- {invoice_summary(invoice_id)}  {result.decision}  {result.ap_decision_id}{extra}"
        )
    collections = ar["collections"]
    collection_lines = [
        f"- {item.customer_name}  {item.action}  {item.invoice_id}"
        for item in collections.decisions[:6]
    ] or ["- (none)"]
    auto = ar["auto_apply"]
    amb = ar["human_review"]

    cash_cases = [
        _match_line(blocked_cash, FEATURED["cash_grouped_bank"]),
        _match_line(blocked_cash, FEATURED["cash_fee_bank"]),
        _match_line(blocked_cash, FEATURED["cash_refund_bank"]),
        _match_line(blocked_cash, FEATURED["cash_stripe_bank"]),
        _match_line(blocked_cash, FEATURED["cash_adyen_bank"]),
        _match_line(blocked_cash, FEATURED["cash_break_bank"]),
    ]
    blockers = blocked.human_review_items or [item.detail for item in blocked.exceptions]
    resolved = payload["resolved_reviews"]
    resolve_lines = [
        f"- {item.source_workflow}  {item.review_id}  {item.status}  {item.resolution_action}"
        for item in resolved.values()
    ] or ["- (none)"]

    gm_now = f"{statement.gross_margin_pct:.0%}" if statement else "n/a"
    gm_prior = f"{prior.gross_margin_pct:.0%}" if prior else "n/a"
    variance_lines = []
    for item in reporting.variances:
        variance_lines.append(
            f"- {item.metric}: {item.variance:+.4f}  {item.narrative}"
        )
        for contrib in item.contributors[:5]:
            variance_lines.append(f"    {contrib.label}  {contrib.amount:+,.2f}")
    fva_lines = []
    if fva is not None:
        fva_lines.append(fva.narrative)
        for item in fva.contributors[:5]:
            fva_lines.append(f"- {item.kind}: {item.label}  {item.amount:+,.2f}")

    sample_lines = [
        f"- {item.population_name}: {', '.join(item.sampled_ids[:6])}"
        for item in audit.samples
    ] or ["- (none)"]
    control_lines = [
        f"- {item.control_id}  {item.result}  tested={len(item.tested_ids)}"
        for item in audit.controls
    ] or ["- (none)"]
    reperf_lines = [
        f"- {item.reconciliation_id}  {'AGREE' if item.agreed else 'DISAGREE'}  {item.recon_type}"
        for item in audit.reperformance[:6]
    ] or ["- (none)"]
    finding_lines = [
        f"- {item.finding_id}  {item.result}  {item.control_id}  {', '.join(item.affected_object_ids[:3])}  evidence={', '.join(item.evidence_ids[:3])}"
        for item in audit.findings[:8]
    ] or ["- (none)"]

    chain_lines = [_chain_block(item) for item in payload["chains"]]
    failed = [item for item in payload["checks"] if not item["passed"]]
    failed_lines = [f"- {item['name']}: {item['detail']}" for item in failed] or ["- (none)"]

    remaining = list(closed.human_review_items)
    harbor = payload.get("harbor_trace")
    august = payload.get("august_memory") or {}
    harbor_lookup = getattr(harbor, "memory_lookup", None) if harbor is not None else None
    harbor_prior = ""
    if harbor_lookup is not None and harbor_lookup.retrieved:
        harbor_prior = harbor_lookup.retrieved[0]
    harbor_line = (
        f"Harbor Electric booked {getattr(harbor, 'final_method', 'n/a')} "
        f"{_usd(getattr(harbor, 'final_amount', 0))} citing {harbor_prior or 'no prior decision'}."
        if harbor is not None
        else "Harbor Electric accrual was not on the close packet."
    )
    company = payload.get("company") or {}
    return "\n".join(
        [
            f"{company.get('legal_name', COMPANY_NAME).upper()} — SEPTEMBER 2026",
            f"Office of the CFO  ·  {company.get('headquarters', HEADQUARTERS)}  ·  {company.get('company_id', 'CO-MAXIMOR')}",
            "",
            "One company. One set of books. Every ID below is the same economic event",
            "as it moves from AP or the bank through close, reporting, and audit.",
            "",
            "THE MONTH IN ONE PAGE",
            f"- Close started {blocked.period.status} because the bank was $12.40 over the ledger.",
            f"- A reviewer posted the correcting receipt; September is now {closed.period.status}.",
            f"- Duplicate {FEATURED['ap_duplicate']} stayed HOLD and never entered the payment pool.",
            f"- {harbor_line}",
            f"- Gross margin moved {gm_prior} → {gm_now} from ledger transactions, not a new estimate.",
            f"- August memory on file: Harbor {august.get('harbor_memory_id') or '(none)'}; "
            f"Stripe {august.get('stripe_memory_id') or '(none)'}.",
            "",
            "Implemented workflows (not rebuilt):",
            *inv_lines,
            "",
            "1. OPENING STATE",
            f"Period {PERIOD}",
            f"- AP invoices on file: {opening['invoice_count']}",
            f"- Opening bank: {_usd(opening['opening_bank'])}",
            f"- Opening ledger cash: {_usd(opening['opening_ledger'])}",
            f"- AR outstanding: {_usd(opening['ar_outstanding'])} across {opening['ar_invoices']} invoices",
            "",
            "2. AP / AR",
            "Accounts payable",
            *ap_lines,
            "",
            "Accounts receivable — collections",
            *collection_lines,
            "",
            f"Applied cash: {auto.payment_id}  {auto.final.decision}  {_usd(auto.payment.amount)}",
            f"  {auto.final.reason}",
            f"Ambiguous cash: {amb.payment_id}  {amb.final.decision}",
            f"  {amb.final.reason}",
            "",
            "3. CASH RECONCILIATION",
            f"Period status: {blocked_cash.period_status}  unexplained={_usd(blocked_cash.unexplained_difference)}",
            *cash_cases,
            "Cash is not fully reconciled while the $12.40 difference remains open.",
            "",
            "4. MONTH-END CLOSE ATTEMPT",
            f"Close status: {blocked.period.status}",
            f"Cash task: {next((item.status for item in blocked.tasks if item.task_id == 'cash'), 'n/a')}",
            "Blocking reasons:",
            *([f"- {item}" for item in blockers] or ["- (none)"]),
            "",
            "5. HUMAN RESOLUTION",
            "Existing reviewer actions (not a status overwrite):",
            *resolve_lines,
            "",
            "6. CLOSE",
            f"Close status: {closed.period.status}",
            f"Snapshot: {closed.snapshot_path or '(none)'}",
            f"Cash after resolution: {getattr(closed_cash, 'period_status', 'n/a')}  "
            f"unexplained={_usd(getattr(closed_cash, 'unexplained_difference', 0))}",
            f"Post-close unauthorized journal: {payload['post_close_detail'] or 'not rejected'}",
            "",
            "7. REPORTING",
            f"Source: ledger period_report / close snapshot {payload['closed_reporting'].get('snapshot_id') or '(none)'}",
            f"- Revenue: {_usd(statement.revenue)}",
            f"- COGS: {_usd(statement.cogs)}",
            f"- Gross profit: {_usd(statement.gross_profit)}",
            f"- Gross margin: {gm_now}  (August {gm_prior})",
            *variance_lines,
            "",
            "8. FORECAST UPDATE",
            f"Forecast: {getattr(reporting.forecast, 'forecast_id', 'n/a')}",
            *fva_lines,
            "",
            "9. AUDIT",
            f"Audit run: {audit.audit_run_id}  findings={len(audit.findings)}",
            "Sample selected",
            *sample_lines,
            "Controls tested",
            *control_lines,
            "Re-performance",
            *reperf_lines,
            f"Independence on operational cash {independence.get('reconciliation_id')}: "
            f"{'PASS' if independence.get('passed') else 'FAIL'}",
            "Findings",
            *finding_lines,
            "",
            "10. PRIOR-PERIOD MEMORY",
            f"August Harbor methodology: {august.get('harbor_memory_id') or '(none)'}",
            f"August Stripe payout treatment: {august.get('stripe_memory_id') or '(none)'}",
            harbor_line,
            "Current September evidence was checked before reuse. A method shift would appear as a deviation.",
            "",
            "11. TRACE",
            *chain_lines,
            "",
            "Agent handoffs (structured workflow outputs)",
            _handoff_block(payload["handoffs"]),
            "",
            "Human-review points",
            _human_block(payload["human_reviews"]),
            "",
            "12. FINAL CFO STATE",
            f"- AP: matched {FEATURED['ap_matched']} APPROVE; "
            f"duplicate {FEATURED['ap_duplicate']} HOLD; "
            f"review {FEATURED['ap_human_review']} HOLD",
            f"- AR: {auto.final.decision} on {auto.payment_id}; {amb.final.decision} on {amb.payment_id}",
            f"- Cash recon: {getattr(closed_cash, 'period_status', 'n/a')}",
            f"- Close: {closed.period.status}",
            f"- Reporting: {statement.period} GM {gm_now}",
            f"- Forecast: {getattr(reporting.forecast, 'forecast_id', 'n/a')}",
            f"- Audit: {audit.audit_run_id} / {len(audit.findings)} findings",
            f"- Memory: Harbor {harbor_prior or '(none)'} → "
            f"{getattr(harbor, 'written_memory_id', None) or '(none)'}",
            f"- Unresolved human-review items: {', '.join(remaining) if remaining else '(none)'}",
            "",
            format_metrics(payload["metrics"]),
            "",
            "Failed integration assertions",
            *failed_lines,
        ]
    )
