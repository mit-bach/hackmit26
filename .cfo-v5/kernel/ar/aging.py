"""Deterministic receivables aging. The LLM does not calculate days or buckets."""

from __future__ import annotations

from datetime import date, datetime, timezone

from accrual.estimation import money
from ar.models import (
    AgingBucket,
    AgingLine,
    AgingReport,
    AgingTotals,
    CustomerAging,
    CustomerInvoice,
    InvoiceStatus,
)
from ar.store import add_event, all_customers, all_invoices, save_trace

BUCKETS: tuple[AgingBucket, ...] = ("CURRENT", "1-30", "31-60", "61-90", "90+")


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def days_past_due(due_date: str, as_of: str) -> int:
    delta = (parse_date(as_of) - parse_date(due_date)).days
    return max(delta, 0)


def aging_bucket(days: int) -> AgingBucket:
    if days <= 0:
        return "CURRENT"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def derive_status(invoice: CustomerInvoice, as_of: str) -> InvoiceStatus:
    outstanding = money(invoice.outstanding_amount)
    if invoice.dispute_status == "OPEN" and outstanding > 0:
        return "DISPUTED"
    if outstanding <= 0:
        return "PAID"
    if outstanding < money(invoice.original_amount):
        return "PARTIALLY_PAID"
    if days_past_due(invoice.due_date, as_of) > 0:
        return "PAST_DUE"
    return "OPEN"


def _percent(part: float, total: float) -> float:
    if money(total) <= 0:
        return 0.0
    return money(part / total * 100)


def age_invoices(invoices: list[CustomerInvoice], as_of: str) -> list[AgingLine]:
    lines: list[AgingLine] = []
    for invoice in invoices:
        outstanding = money(invoice.outstanding_amount)
        if outstanding <= 0:
            continue
        dpd = days_past_due(invoice.due_date, as_of)
        lines.append(
            AgingLine(
                invoice_id=invoice.invoice_id,
                customer_id=invoice.customer_id,
                customer_name=invoice.customer_name,
                original_amount=money(invoice.original_amount),
                outstanding_amount=outstanding,
                due_date=invoice.due_date,
                days_past_due=dpd,
                aging_bucket=aging_bucket(dpd),
                dispute_status=invoice.dispute_status,
                collection_status=invoice.collection_status,
                invoice_status=derive_status(invoice, as_of),
            )
        )
    lines.sort(key=lambda item: (-item.days_past_due, item.customer_name, item.invoice_id))
    return lines


def summarize(lines: list[AgingLine]) -> AgingTotals:
    bucket_amounts = {bucket: 0.0 for bucket in BUCKETS}
    disputed = 0.0
    partial = 0.0
    for line in lines:
        bucket_amounts[line.aging_bucket] = money(
            bucket_amounts[line.aging_bucket] + line.outstanding_amount
        )
        if line.dispute_status == "OPEN":
            disputed = money(disputed + line.outstanding_amount)
        if line.invoice_status == "PARTIALLY_PAID":
            partial = money(partial + line.outstanding_amount)
    total = money(sum(bucket_amounts.values()))
    current = bucket_amounts["CURRENT"]
    return AgingTotals(
        total_ar=total,
        current_ar=current,
        past_due_ar=money(total - current),
        bucket_amounts=bucket_amounts,
        bucket_percents={bucket: _percent(amount, total) for bucket, amount in bucket_amounts.items()},
        disputed_ar=disputed,
        partially_paid_ar=partial,
        open_invoice_count=len(lines),
    )


def customer_rollup(lines: list[AgingLine]) -> list[CustomerAging]:
    customers = {item.customer_id: item for item in all_customers()}
    grouped: dict[str, list[AgingLine]] = {}
    for line in lines:
        grouped.setdefault(line.customer_id, []).append(line)
    rows: list[CustomerAging] = []
    for customer_id, group in grouped.items():
        oldest = max(group, key=lambda item: item.days_past_due)
        profile = customers.get(customer_id)
        rows.append(
            CustomerAging(
                customer_id=customer_id,
                customer_name=group[0].customer_name,
                total_outstanding=money(sum(item.outstanding_amount for item in group)),
                oldest_unpaid_invoice=oldest.invoice_id,
                oldest_due_date=oldest.due_date,
                max_days_past_due=oldest.days_past_due,
                open_invoices=len(group),
                amount_past_due=money(
                    sum(item.outstanding_amount for item in group if item.days_past_due > 0)
                ),
                dispute_amount=money(
                    sum(item.outstanding_amount for item in group if item.dispute_status == "OPEN")
                ),
                payment_behavior=profile.payment_behavior if profile else "",
            )
        )
    rows.sort(key=lambda item: (-item.max_days_past_due, -item.total_outstanding, item.customer_name))
    return rows


def build_aging_report(
    as_of: str,
    invoices: list[CustomerInvoice] | None = None,
    *,
    persist: bool = True,
) -> AgingReport:
    rows = invoices if invoices is not None else all_invoices()
    lines = age_invoices(rows, as_of)
    report = AgingReport(
        as_of_date=as_of,
        lines=lines,
        totals=summarize(lines),
        customers=customer_rollup(lines),
        calculated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    if persist:
        path = save_trace("aging", report)
        report.trace_path = str(path)
        add_event(
            "aging_run",
            f"Aged {len(lines)} open invoices as of {as_of}",
            invoice_ids=[item.invoice_id for item in lines],
            details={
                "as_of_date": as_of,
                "total_ar": report.totals.total_ar,
                "bucket_amounts": report.totals.bucket_amounts,
            },
        )
    return report
