"""Deterministic cross-domain validators. Generation fails loudly; no silent repair."""

from __future__ import annotations

from collections import Counter

from cash_recon.mathutil import cents
from integrations.cash import reconcile_payout
from prepaid.schedule import generate_schedule

from sample_data.context import CompanyScenarioContext, dollars
from sample_data.pnl import (
    ACTIVE_VENDORS,
    ANNUAL_REVENUE_RUN_RATE,
    AP_INVOICES_TRAILING,
    AP_OPEN,
    AR_OPEN,
    AUGUST_REVENUE,
    BIWEEKLY_PAYROLL_GROSS,
    COGS_ACCOUNTS,
    INTENDED_COGS_MINOR,
    INTENDED_REVENUE_MINOR,
    OPERATIONAL_AP_IDS,
    OPERATING_CASH_2026_09_30,
    REVENUE_ACCOUNTS,
    SEPTEMBER_REVENUE,
    W2_HEADCOUNT,
    cogs_invoice_ids,
    quantity_rate_amount,
    validate_fact_arithmetic,
)
from sample_data.registry import required_ids


class SampleDataValidationError(ValueError):
    """One or more sample-data invariants failed."""


def _collect(ctx: CompanyScenarioContext) -> dict[str, object]:
    return {
        "ap": ctx.ap_invoices,
        "po": ctx.purchase_orders,
        "gr": ctx.goods_receipts,
        "ar": ctx.ar_invoices,
        "pay": ctx.ar_payments,
        "vend_pay": ctx.vendor_payments,
        "bank": ctx.bank_transactions,
        "ledger": ctx.ledger_cash,
        "je": ctx.journal_entries,
        "cust": ctx.customers,
        "vend": ctx.vendors,
    }


def validate_unique_ids(ctx: CompanyScenarioContext) -> list[str]:
    bags = [
        list(ctx.ap_invoices),
        list(ctx.purchase_orders),
        list(ctx.goods_receipts),
        list(ctx.ar_invoices),
        list(ctx.ar_payments),
        list(ctx.vendor_payments),
        list(ctx.bank_transactions),
        list(ctx.ledger_cash),
        list(ctx.journal_entries),
        list(ctx.customers),
        list(ctx.vendors),
        [item.prepaid_id for item in ctx.prepaids],
        [item.asset_id for item in ctx.fixed_assets],
        [item.accrual_id for item in ctx.accruals],
        [item.task_id for item in ctx.close_tasks],
        [item.scenario_id for item in ctx.scenarios.values()],
    ]
    errors = []
    for group in bags:
        counts = Counter(group)
        dupes = [key for key, count in counts.items() if count > 1]
        if dupes:
            errors.append(f"duplicate ids: {dupes}")
    return errors


def validate_foreign_keys(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    vendor_names = {row["name"] for row in ctx.vendors.values()}
    for invoice in ctx.ap_invoices.values():
        if invoice.po_id and invoice.po_id not in ctx.purchase_orders and invoice.invoice_id not in {
            *cogs_invoice_ids(),
            "INV-020",
        }:
            if invoice.po_id:
                errors.append(f"AP {invoice.invoice_id} missing PO {invoice.po_id}")
        if invoice.vendor not in vendor_names:
            errors.append(f"AP {invoice.invoice_id} unknown vendor {invoice.vendor}")
    for receipt in ctx.goods_receipts.values():
        if receipt.po_id not in ctx.purchase_orders:
            errors.append(f"GR {receipt.receipt_id} missing PO {receipt.po_id}")
    for invoice in ctx.ar_invoices.values():
        if invoice.customer_id not in ctx.customers:
            errors.append(f"AR {invoice.invoice_id} missing customer {invoice.customer_id}")
    for payment in ctx.ar_payments.values():
        if payment.customer_id and payment.customer_id not in ctx.customers:
            errors.append(f"payment {payment.payment_id} missing customer {payment.customer_id}")
    for payment in ctx.vendor_payments.values():
        for invoice_id in payment.invoice_ids:
            if invoice_id not in ctx.ap_invoices:
                errors.append(f"vendor payment {payment.payment_id} missing invoice {invoice_id}")
    for entry in ctx.journal_entries.values():
        if entry.source_document_id and not _known(ctx, entry.source_document_id):
            errors.append(f"journal {entry.entry_id} orphan source {entry.source_document_id}")
    return errors


def _known(ctx: CompanyScenarioContext, ref: str) -> bool:
    return (
        ref in ctx.ap_invoices
        or ref in ctx.ar_invoices
        or ref in ctx.ar_payments
        or ref in ctx.vendor_payments
        or ref in ctx.bank_transactions
        or ref in ctx.journal_entries
        or any(item.prepaid_id == ref for item in ctx.prepaids)
        or any(item.asset_id == ref for item in ctx.fixed_assets)
        or any(item.accrual_id == ref for item in ctx.accruals)
        or any(item.contract_id == ref for item in ctx.vendor_contracts)
        or any(item.schedule_id == ref for item in ctx.payroll)
        or any(item["document_id"] == ref for item in ctx.source_documents)
        or ref.startswith("PR-")
        or ref.startswith("CTR-")
        or ref.startswith("DOC-")
        or ref.startswith("OPEX-")
        or ref.startswith("HAP-")
        or ref.startswith("INV-COGS-HIST-")
        or ref.startswith("INV-AR-HIST-")
        or ref.startswith("TXN-VOL-")
        or ref.startswith("TXN-HIST-")
        or ref.startswith("HPO-")
        or ref.startswith("INV-SCALE-")
        or ref.startswith("INV-PIN-")
        or ref.startswith("INV-ATL-")
        or ref.startswith("DIT-")
        or ref.startswith("CC-")
        or ref.startswith("REF-")
        or ref.startswith("tr_")
        or ref.startswith("re_")
        or ref.startswith("dsp_")
        or ref.startswith("FA-")
        or any(row.get("count_id") == ref for row in ctx.cycle_counts)
        or any(row.get("credit_memo_id") == ref for row in ctx.ar_credit_memos)
        or any(row.get("payment_id") == ref for row in ctx.ar_unapplied)
        or ref.startswith("PAY-UNAPP-")
        or ref.startswith("CM-")
        or ref.startswith("BATCH-AR-")
    )


def validate_money_representation(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for txn in ctx.bank_transactions.values():
        if txn.amount_minor != cents(txn.amount):
            errors.append(f"bank {txn.transaction_id} amount/minor mismatch")
    for entry in ctx.ledger_cash.values():
        if entry.amount_minor != cents(entry.amount):
            errors.append(f"ledger {entry.entry_id} amount/minor mismatch")
    for payout in ctx.stripe_payouts:
        if not isinstance(payout.amount, int):
            errors.append(f"stripe {payout.payout_id} amount is not integer cents")
    for entry in ctx.journal_entries.values():
        if entry.amount_minor != cents(entry.amount):
            errors.append(f"journal {entry.entry_id} amount/minor mismatch")
    return errors


def validate_balanced_journal_entries(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for entry in ctx.journal_entries.values():
        if entry.amount_minor <= 0:
            errors.append(f"journal {entry.entry_id} non-positive")
        if not entry.debit_account or not entry.credit_account:
            errors.append(f"journal {entry.entry_id} missing account")
        if entry.debit_account == entry.credit_account:
            errors.append(f"journal {entry.entry_id} debit equals credit account")
    return errors


def validate_ap_to_gl(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for invoice_id in ("INV-001", "INV-002", "INV-017", "INV-018"):
        invoice = ctx.ap_invoices[invoice_id]
        jes = [item for item in ctx.journal_entries.values() if item.source_document_id == invoice_id and item.entry_type in {"ap_invoice", "capital", "prepaid"}]
        if not jes:
            errors.append(f"AP {invoice_id} has no GL posting")
            continue
        if jes[0].amount_minor != cents(invoice.amount):
            errors.append(f"AP {invoice_id} GL amount {jes[0].amount_minor} != {cents(invoice.amount)}")
    return errors


def validate_ar_to_gl(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for invoice_id in ("INV-AR-SEP-001", "INV-AR-AUG-001", "INV-AR-013"):
        invoice = ctx.ar_invoices[invoice_id]
        jes = [item for item in ctx.journal_entries.values() if item.source_document_id == invoice_id]
        if not jes:
            errors.append(f"AR {invoice_id} has no GL posting")
            continue
        if jes[0].amount_minor != cents(invoice.original_amount):
            errors.append(f"AR {invoice_id} GL amount mismatch")
    return errors


def validate_bank_to_cash_events(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    if "TXN-2026-09-018A" not in ctx.bank_transactions:
        errors.append("missing Acme bank payment")
    else:
        if ctx.bank_transactions["TXN-2026-09-018A"].amount_minor != -ctx.vendor_payments["PAY-AP-001"].amount_minor:
            errors.append("Acme bank amount != vendor payment")
    if ctx.ar_payments["PAY-001"].amount != dollars(ctx.bank_transactions["TXN-AR-PAY-001"].amount_minor):
        errors.append("AR receipt bank amount != PAY-001")
    return errors


def validate_stripe_payout_math(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for payout in ctx.stripe_payouts:
        breakdown = reconcile_payout(payout)
        if breakdown.expected_payout_minor != breakdown.actual_payout_minor:
            errors.append(f"stripe {payout.payout_id} expected {breakdown.expected_payout_minor} != actual {breakdown.actual_payout_minor}")
        bank = next((item for item in ctx.bank_transactions.values() if item.raw_metadata.get("payout_id") == payout.payout_id), None)
        if bank is None or bank.amount_minor != int(payout.amount):
            errors.append(f"stripe {payout.payout_id} missing matching bank deposit")
    return errors


def validate_reconciliation_math(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    bank = ctx.bank_transactions["TXN-2026-09-015"]
    ledger = ctx.ledger_cash["GL-AR-NS"]
    if bank.amount_minor - ledger.amount_minor != 1240:
        errors.append(f"Northstar difference is {bank.amount_minor - ledger.amount_minor} cents, expected 1240")
    grouped = sum(ctx.ledger_cash[key].amount_minor for key in ("GL-AP-201", "GL-AP-202", "GL-AP-203"))
    northline_bank = ctx.bank_transactions["TXN-2026-09-008"]
    if grouped != northline_bank.amount_minor:
        errors.append("Northline grouped ACH does not sum")
    from cash_recon.normalize import counterparties_compatible

    if not counterparties_compatible(
        northline_bank.counterparty,
        ctx.ledger_cash["GL-AP-201"].counterparty,
    ):
        errors.append("Northline grouped ACH counterparties are not compatible")
    if ctx.bank_transactions["TXN-2026-09-011"].amount_minor - ctx.ledger_cash["GL-AP-WIRE"].amount_minor != -2500:
        errors.append("Helios fee-netted difference is not $25")
    return errors


def validate_close_tie_outs(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    if not any(item.status == "BLOCKED" and "12.40" in item.blocker_reason for item in ctx.close_tasks):
        errors.append("close is missing the $12.40 blocker")
    if not any(item.status == "COMPLETE" for item in ctx.close_tasks):
        errors.append("close is missing a completed task")
    if not any(item.status == "NEEDS_REVIEW" for item in ctx.close_tasks):
        errors.append("close is missing a review task")
    for link in ctx.identity_links:
        if link.source_document_id and not _known(ctx, link.source_document_id):
            errors.append(f"close link {link.link_id} orphan document {link.source_document_id}")
    return errors


def validate_forecast_math(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    if len(ctx.forecast_weeks) != 13:
        errors.append(f"forecast has {len(ctx.forecast_weeks)} weeks, expected 13")
    for week in ctx.forecast_weeks:
        expected = (
            week.beginning_cash
            + week.ar_collections
            + week.other_inflows
            - week.ap_payments
            - week.payroll
            - week.other_outflows
        )
        if round(expected, 2) != round(week.ending_cash, 2):
            errors.append(f"forecast week {week.week_start} does not roll forward")
    return errors


def _journal_class_totals(ctx: CompanyScenarioContext, accounts: frozenset[str], *, side: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for entry in ctx.journal_entries.values():
        account = entry.debit_account if side == "debit" else entry.credit_account
        if account in accounts:
            totals[entry.period] = totals.get(entry.period, 0) + entry.amount_minor
    return totals


def validate_pnl_integrity(ctx: CompanyScenarioContext) -> list[str]:
    """COGS/revenue must come from dedicated P&L facts, once, and tie to reporting."""
    errors = list(validate_fact_arithmetic())
    journal_cogs = _journal_class_totals(ctx, COGS_ACCOUNTS, side="debit")
    journal_rev = _journal_class_totals(ctx, REVENUE_ACCOUNTS, side="credit")
    for period, expected in INTENDED_COGS_MINOR.items():
        actual = journal_cogs.get(period, 0)
        if actual != expected:
            errors.append(f"journal COGS {period} is {actual} cents, intended {expected}")
    for period, expected in INTENDED_REVENUE_MINOR.items():
        actual = journal_rev.get(period, 0)
        if actual != expected:
            errors.append(f"journal revenue {period} is {actual} cents, intended {expected}")

    seen_txn: dict[str, str] = {}
    seen_source: dict[str, str] = {}
    for entry in ctx.journal_entries.values():
        if entry.debit_account not in COGS_ACCOUNTS:
            continue
        if entry.source_document_id in OPERATIONAL_AP_IDS:
            errors.append(
                f"{entry.entry_id} posts operational AP {entry.source_document_id} to COGS"
            )
        if entry.transaction_id in seen_txn:
            errors.append(
                f"duplicate COGS transaction {entry.transaction_id}: "
                f"{seen_txn[entry.transaction_id]} and {entry.entry_id}"
            )
        seen_txn[entry.transaction_id] = entry.entry_id
        if entry.source_document_id in seen_source:
            errors.append(
                f"duplicate COGS source {entry.source_document_id}: "
                f"{seen_source[entry.source_document_id]} and {entry.entry_id}"
            )
        seen_source[entry.source_document_id] = entry.entry_id
        computed = quantity_rate_amount(entry.quantity, entry.rate)
        if computed is not None and cents(computed) != entry.amount_minor:
            errors.append(
                f"{entry.entry_id}: quantity {entry.quantity} × rate {entry.rate} "
                f"!= line amount {entry.amount}"
            )

    reporting_cogs: dict[str, int] = {}
    reporting_rev: dict[str, int] = {}
    for line in ctx.reporting_lines:
        if line.account_class == "cogs" and line.side == "debit":
            reporting_cogs[line.period] = reporting_cogs.get(line.period, 0) + cents(line.amount)
        if line.account_class == "revenue" and line.side == "credit":
            reporting_rev[line.period] = reporting_rev.get(line.period, 0) + cents(line.amount)
    for period, expected in INTENDED_COGS_MINOR.items():
        if reporting_cogs.get(period, 0) != expected:
            errors.append(f"reporting COGS {period} is {reporting_cogs.get(period, 0)}, intended {expected}")
        if reporting_cogs.get(period, 0) != journal_cogs.get(period, 0):
            errors.append(f"reporting COGS {period} does not match journal COGS")
        if reporting_rev.get(period, 0) != journal_rev.get(period, 0):
            errors.append(f"reporting revenue {period} does not match journal revenue")
        gp = journal_rev.get(period, 0) - journal_cogs.get(period, 0)
        intended_gp = INTENDED_REVENUE_MINOR[period] - expected
        if gp != intended_gp:
            errors.append(f"{period} gross profit {gp} != revenue - COGS {intended_gp}")
    return errors


def validate_reporting_ties_to_gl(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    if not ctx.reporting_lines:
        errors.append("reporting ledger is empty")
    for line in ctx.reporting_lines:
        if line.entry_id not in ctx.journal_entries:
            errors.append(f"reporting line {line.line_id} missing journal {line.entry_id}")
            continue
        entry = ctx.journal_entries[line.entry_id]
        if cents(line.amount) != entry.amount_minor:
            errors.append(f"reporting line {line.line_id} amount != journal")
        if line.source_document_id and line.source_document_id != entry.source_document_id:
            errors.append(f"reporting line {line.line_id} source mismatch")
    rev = {period: 0 for period in (ctx.calendar.comparison_period, ctx.period)}
    cogs = {period: 0 for period in rev}
    for line in ctx.reporting_lines:
        if line.account_class == "revenue" and line.side == "credit":
            rev[line.period] = rev.get(line.period, 0) + cents(line.amount)
        if line.account_class == "cogs" and line.side == "debit":
            cogs[line.period] = cogs.get(line.period, 0) + cents(line.amount)
    if rev.get("2026-08") != INTENDED_REVENUE_MINOR["2026-08"] or rev.get("2026-09") != INTENDED_REVENUE_MINOR["2026-09"]:
        errors.append(f"revenue totals {rev} are not the catalog scale table")
    if cogs.get("2026-08") != INTENDED_COGS_MINOR["2026-08"] or cogs.get("2026-09") != INTENDED_COGS_MINOR["2026-09"]:
        errors.append(f"cogs totals {cogs} are not the catalog scale table")
    return errors


def validate_audit_population_integrity(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    invoice_ids = {item.invoice_id for item in ctx.audit_invoices}
    for invoice_id in ("INV-001", "INV-006", "INV-007", "INV-009"):
        if invoice_id not in invoice_ids:
            errors.append(f"audit population missing {invoice_id}")
    payment_ids = {item.payment_id for item in ctx.audit_payments}
    if "PAY-AP-009" not in payment_ids:
        errors.append("audit population missing round-number payment")
    if not any(item.entry_id == "JE-POST-CLOSE-001" for item in ctx.audit_journals):
        errors.append("audit population missing post-close journal")
    if ctx.expected is None:
        errors.append("expected results missing")
    return errors


def validate_prepaid_amortization(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for item in ctx.prepaids:
        schedule = generate_schedule(item)
        if abs(sum(line.amount for line in schedule) - item.total_amount) > 0.01:
            errors.append(f"prepaid {item.prepaid_id} schedule does not sum")
        posted = [line for line in ctx.prepaid_schedule if line.prepaid_id == item.prepaid_id and line.period == ctx.period]
        if not posted:
            errors.append(f"prepaid {item.prepaid_id} has no {ctx.period} line")
    return errors


def validate_scenarios_planted(ctx: CompanyScenarioContext) -> list[str]:
    missing = [item for item in required_ids() if item not in ctx.scenarios]
    if missing:
        return [f"missing planted scenarios: {missing}"]
    return []


PLOT_AMOUNTS = {
    "INV-001": 12450.0,
    "INV-017": 10000.0,
    "INV-AR-013": 12400.0,
}


def validate_plot_identities(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for invoice_id, amount in PLOT_AMOUNTS.items():
        bag = ctx.ap_invoices if invoice_id.startswith("INV-") and not invoice_id.startswith("INV-AR") else ctx.ar_invoices
        if invoice_id not in bag:
            errors.append(f"missing plot identity {invoice_id}")
            continue
        actual = bag[invoice_id].amount if invoice_id in ctx.ap_invoices else bag[invoice_id].original_amount
        if abs(float(actual) - amount) > 0.009:
            errors.append(f"{invoice_id} amount {actual} != {amount}")
    if "PO-101" not in ctx.purchase_orders or "GR-101" not in ctx.goods_receipts:
        errors.append("clean three-way PO-101 / GR-101 missing")
    if "PAY-006" not in ctx.ar_payments:
        errors.append("missing PAY-006")
    if "TXN-2026-09-015" not in ctx.bank_transactions:
        errors.append("missing TXN-2026-09-015")
    if ctx.company.company_id != "CO-MAXIMOR" or ctx.company.legal_name != "Maximor Demo Corp":
        errors.append("company identity is not Maximor Demo Corp")
    return errors


def validate_scale_floors(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    checks = {
        "ap_invoices": (len(ctx.ap_invoices), 110),
        "vendors": (len(ctx.vendors), ACTIVE_VENDORS),
        "bank_transactions": (len(ctx.bank_transactions), 200),
        "journal_entries": (len(ctx.journal_entries), 2000),
        "historical_ap": (len(ctx.historical_ap_register), AP_INVOICES_TRAILING),
        "processor": (len(ctx.processor_transactions), 2000),
        "payroll_register": (len(ctx.payroll_register), W2_HEADCOUNT),
        "employee_master": (len(ctx.employee_master), W2_HEADCOUNT),
        "documents": (len(ctx.document_texts), 80),
    }
    for name, (actual, floor) in checks.items():
        if actual < floor:
            errors.append(f"{name} count {actual} is below floor {floor}")
    if not any(item.get("status") == "CLOSED" and item.get("period") == "2026-08" for item in ctx.fiscal_periods):
        errors.append("August is not a closed fiscal period")
    if not any(item.get("status") == "OPEN" and item.get("period") == "2026-09" for item in ctx.fiscal_periods):
        errors.append("September is not the open fiscal period")
    return errors


def validate_document_quality(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    for invoice_id in ("INV-001", "INV-017", "INV-018", "INV-021", "INV-KIS-2026-09", "INV-BLS-2026-09", "INV-LEN-ROLL-26"):
        text = ctx.document_texts.get(f"invoices/{invoice_id}.txt", "")
        if len(text) < 400:
            errors.append(f"{invoice_id} document is only {len(text)} characters")
        lower = text.lower()
        if text and "amount due" not in lower:
            errors.append(f"{invoice_id} document missing Amount Due")
        if text and "invoice number" not in lower:
            errors.append(f"{invoice_id} document missing Invoice Number")
        if invoice_id == "INV-001" and "po-101" not in lower:
            errors.append("INV-001 document missing PO-101")
    banned = ("human_review", "this is the fraud", "planted")
    for message in ctx.ingestion_emails:
        blob = f"{message.get('body') or ''} " + " ".join(
            str(item.get("text") or "") for item in message.get("attachments") or []
        )
        lower = blob.lower()
        for token in banned:
            if token in lower:
                errors.append(f"ingestion email {message.get('message_id')} contains {token}")
    for rel, text in ctx.document_texts.items():
        lower = text.lower()
        for token in banned:
            if token in lower:
                errors.append(f"document {rel} contains {token}")
    return errors


HOLD_REASON_CODES = (
    "RELATED_PARTY_VENDOR",
    "RELATED_PARTY_REMITTANCE",
    "BANK_INSTRUMENT_DRIFT",
    "NEAR_DUPLICATE_VENDOR",
    "PO_SPLIT_UNDER_LIMIT",
    "GR_QUANTITY_OVERSTATEMENT",
    "STANDING_PO_OVERCONSUMED",
    "GR_BEFORE_AUTHORIZATION",
    "CROSS_VENDOR_INVOICE_NUMBER",
    "REMITTANCE_RATE_RESIDUAL",
    "RESIDUAL_UNPLUGGED",
    "REC_PLUG_NET_ZERO",
    "UNAPPLIED_CASH_PARK",
    "GHOST_EMPLOYEE",
    "PAYROLL_VENDOR_BANK_COLLISION",
    "CONTRACTOR_W2_DOUBLE_DIP",
    "TERMINATED_EMPLOYEE_PAID",
    "PREPAID_AMORT_MISPOSTED",
    "AMORT_REVERSAL_PAIR",
    "AR_LAPPING",
    "REVENUE_CUTOFF",
    "CHANNEL_STUFFING",
    "BILL_AND_HOLD",
    "PROCESSOR_FEE_OVERSTATEMENT",
    "CONNECTED_ACCOUNT_SKIM",
    "FAKE_INTERCOMPANY",
    "ROUND_TRIP_COUNTERPARTY",
    "CAM_TRUEUP_ORPHAN",
    "NET_ZERO_JE_PAIR",
    "CAPITALIZED_UNRECEIVED",
    "FORECAST_BIAS_FROM_AR",
    "FREIGHT_SURCHARGE_SKIM",
    "SELF_APPROVAL_ALIAS",
    "EFFECTIVE_DATE_MISMATCH",
    "MIXED_SABBATICAL_SURFACE",
    "SL-ADV",
)

MUST_APPROVE_AP = (
    "INV-KIS-2026-09",
    "INV-NLF-02-2026-09",
    "INV-BLS-2026-09",
    "INV-CAM-RENT-2026-09",
    "INV-LEN-ROLL-26",
)


def _blob(value) -> str:
    if isinstance(value, dict):
        return " ".join(_blob(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_blob(item) for item in value)
    return str(value)


def validate_adversarial_holdout(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    if ctx.expected is None:
        return ["expected results missing"]
    holdout = ctx.expected.adversarial_holdout
    ids = [item.id for item in holdout]
    if len(ids) != 109:
        errors.append(f"adversarial_holdout has {len(ids)} rows, expected 109")
    if len(set(ids)) != len(ids):
        errors.append("adversarial_holdout has duplicate ids")
    if ctx.expected.reconciliation_statuses.get("TXN-2026-09-015") not in {"EXCEPTION_OPEN", "CLOSE_BLOCKED", "UNMATCHED"}:
        errors.append("TXN-2026-09-015 expected status is not EXCEPTION_OPEN")
    blockers = set(ctx.expected.close_blockers)
    if not {"TXN-2026-09-015", "TASK-CASH", "TASK-FINAL"} <= blockers:
        errors.append("close blockers missing TXN-2026-09-015 / TASK-CASH / TASK-FINAL")
    if "JE-REC-PLUG-2026-08" not in ctx.journal_entries:
        errors.append("August residual plug JE-REC-PLUG-2026-08 missing")
    if "JE-REC-PLUG-2026-09" in ctx.journal_entries:
        errors.append("September residual plug must be skipped")
    if abs(ctx.company.annual_revenue_run_rate - ANNUAL_REVENUE_RUN_RATE) > 0.009:
        errors.append("company annual revenue is not the catalog table")
    if abs(ctx.company.august_revenue - AUGUST_REVENUE) > 0.009:
        errors.append("company August revenue is not the catalog table")
    if abs(ctx.company.september_revenue - SEPTEMBER_REVENUE) > 0.009:
        errors.append("company September revenue is not the catalog table")
    if abs(ctx.company.operating_cash - OPERATING_CASH_2026_09_30) > 0.009:
        errors.append("operating cash is not the catalog table")
    if abs(ctx.company.biweekly_payroll_gross - BIWEEKLY_PAYROLL_GROSS) > 0.009:
        errors.append("biweekly payroll is not the catalog table")
    if "VEND-MPR-01" in ctx.vendors:
        errors.append("VEND-MPR-01 must not be on the vendor master")
    if any(item.get("legal_name") == "Maximor EU BV" for item in ctx.legal_entity_register):
        errors.append("Maximor EU BV must not be a legal entity")
    if "CUST-IC-EU" not in ctx.customers:
        errors.append("CUST-IC-EU missing")
    if any(row.get("employee_id") == "EMP-8891" for row in ctx.badge_access):
        errors.append("ghost employee has a badge row")
    if any(row.get("employee_id") == "EMP-8891" for row in ctx.it_assets):
        errors.append("ghost employee has an IT asset")
    if any(row.get("emp_id") == "EMP-8891" for row in ctx.okta_export):
        errors.append("ghost employee is in the Okta export")
    for invoice_id in MUST_APPROVE_AP:
        if invoice_id not in ctx.ap_invoices:
            errors.append(f"must-approve invoice {invoice_id} missing")
            continue
        invoice = ctx.ap_invoices[invoice_id]
        po = ctx.purchase_orders.get(invoice.po_id or "")
        if po is None or abs(float(po.authorized_amount) - float(invoice.amount)) > 0.009:
            errors.append(f"{invoice_id} would fail naive three-way on PO amount")
        elif po.approval_limit is not None and float(po.authorized_amount) > float(po.approval_limit) + 0.009:
            errors.append(f"{invoice_id} would HOLD on approval_limit_exceeded")
        receipts = [item for item in ctx.goods_receipts.values() if item.po_id == invoice.po_id]
        if not receipts or receipts[0].amount_received + 0.009 < float(po.authorized_amount if po else 0):
            errors.append(f"{invoice_id} would fail naive three-way on GR amount")
    required_vendors = (
        "VEND-KIS-01",
        "VEND-NLF-02",
        "VEND-NLF-03",
        "VEND-WBT-01",
        "VEND-HAL-01",
        "VEND-CLR-01",
        "VEND-BLS-01",
        "VEND-CPS-01",
        "VEND-HES-01",
        "VEND-OIC-01",
        "VEND-FLE-01",
        "VEND-HBP-01",
    )
    for vendor_id in required_vendors:
        row = ctx.vendors.get(vendor_id)
        if row is None:
            errors.append(f"identity vendor {vendor_id} missing")
            continue
        if not row.get("tax_id") or not row.get("bank_routing"):
            errors.append(f"{vendor_id} missing tax ID or bank")
        if row.get("unusual"):
            errors.append(f"{vendor_id} is tagged unusual")
    required_people = (
        "EMP-4128",
        "EMP-2201",
        "EMP-8891",
        "EMP-3304",
        "EMP-1088",
        "EMP-5510",
        "EMP-6722",
        "EMP-1190",
        "EMP-4402",
        "EMP-0901",
        "EMP-2290",
        "EMP-3310",
    )
    by_emp = {row["employee_id"]: row for row in ctx.employee_master}
    for emp_id in required_people:
        if emp_id not in by_emp:
            errors.append(f"identity employee {emp_id} missing")
    if "6950-Cash-Over-Short" not in {item.account_id for item in ctx.chart}:
        errors.append("chart missing 6950-Cash-Over-Short")
    if "1030-Undeposited-Funds" not in {item.account_id for item in ctx.chart}:
        errors.append("chart missing 1030-Undeposited-Funds")
    if "1300-Due-From-Affiliate" not in {item.account_id for item in ctx.chart}:
        errors.append("chart missing 1300-Due-From-Affiliate")
    if "2100-Due-To-Affiliate" not in {item.account_id for item in ctx.chart}:
        errors.append("chart missing 2100-Due-To-Affiliate")
    stealth5 = [item for item in holdout if item.stealth == 5]
    if len(stealth5) < 15:
        errors.append(f"only {len(stealth5)} stealth-5 holdout rows")
    return errors


def validate_no_holdout_leak(ctx: CompanyScenarioContext) -> list[str]:
    errors = []
    bags = [
        ctx.ap_invoices,
        ctx.ar_invoices,
        ctx.bank_transactions,
        ctx.vendors,
        ctx.journal_entries,
    ]
    blobs = []
    for bag in bags:
        for item in bag.values() if hasattr(bag, "values") else bag:
            blobs.append(_blob(item.model_dump() if hasattr(item, "model_dump") else item))
    for row in ctx.employee_master:
        blobs.append(_blob(row))
    for rel, text in ctx.document_texts.items():
        blobs.append(f"{rel} {text}")
    haystack = "\n".join(blobs)
    for token in HOLD_REASON_CODES + ("fraud",):
        if token in haystack:
            errors.append(f"operational files contain holdout token {token}")
    return errors


VALIDATORS = [
    validate_unique_ids,
    validate_foreign_keys,
    validate_money_representation,
    validate_balanced_journal_entries,
    validate_ap_to_gl,
    validate_ar_to_gl,
    validate_bank_to_cash_events,
    validate_stripe_payout_math,
    validate_reconciliation_math,
    validate_close_tie_outs,
    validate_forecast_math,
    validate_pnl_integrity,
    validate_reporting_ties_to_gl,
    validate_audit_population_integrity,
    validate_prepaid_amortization,
    validate_scenarios_planted,
    validate_plot_identities,
    validate_scale_floors,
    validate_document_quality,
    validate_adversarial_holdout,
    validate_no_holdout_leak,
]


def validate_dataset(ctx: CompanyScenarioContext) -> None:
    errors: list[str] = []
    for validator in VALIDATORS:
        errors.extend(validator(ctx))
    if errors:
        raise SampleDataValidationError("Sample data validation failed:\n- " + "\n- ".join(errors))
