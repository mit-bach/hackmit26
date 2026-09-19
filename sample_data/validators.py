"""Deterministic cross-domain validators. Generation fails loudly; no silent repair."""

from __future__ import annotations

from collections import Counter

from cash_recon.mathutil import cents
from integrations.cash import reconcile_payout
from prepaid.schedule import generate_schedule

from sample_data.context import CompanyScenarioContext, dollars
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
            "INV-HOST-AUG-001",
            "INV-HOST-AUG-002",
            "INV-SUP-AUG-001",
            "INV-SUP-AUG-002",
            "INV-FRT-AUG-001",
            "INV-HOST-SEP-001",
            "INV-HOST-SEP-002",
            "INV-SUP-SEP-001",
            "INV-SUP-SEP-002",
            "INV-FRT-SEP-001",
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
    if grouped != ctx.bank_transactions["TXN-2026-09-008"].amount_minor:
        errors.append("Northline grouped ACH does not sum")
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
    if rev.get("2026-08") != 100_000_000 or rev.get("2026-09") != 100_000_000:
        errors.append(f"revenue totals {rev} are not both $1,000,000")
    if cogs.get("2026-08") != 36_000_000 or cogs.get("2026-09") != 39_000_000:
        errors.append(f"cogs totals {cogs} are not 360k/390k")
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
    validate_reporting_ties_to_gl,
    validate_audit_population_integrity,
    validate_prepaid_amortization,
    validate_scenarios_planted,
]


def validate_dataset(ctx: CompanyScenarioContext) -> None:
    errors: list[str] = []
    for validator in VALIDATORS:
        errors.extend(validator(ctx))
    if errors:
        raise SampleDataValidationError("Sample data validation failed:\n- " + "\n- ".join(errors))
