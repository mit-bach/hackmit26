"""Human-readable close and reconciliation reports for the live demo."""

from __future__ import annotations

from accrual.models import (
    AccrualPeriodReport,
    BacktestReport,
    DiscoveryReport,
    ReconciliationResult,
    VendorDecisionTrace,
)
from accrual.validate import status_label

METHOD_LABELS = {
    "last_invoice": "Last invoice",
    "simple_average": "Simple average",
    "recent_average": "Recent average",
    "weighted_recent_average": "Weighted recent average",
    "linear_trend": "Trend projection",
    "seasonal_prior_year": "Prior-year same month",
    "contract_commitment": "Contract commitment",
    "usage_run_rate": "Usage x contract rate",
    "goods_receipt": "Goods receipt",
    "purchase_order": "Purchase order",
    "conservative_minimum": "Conservative minimum",
}

FEATURED_METHODS = {
    "Aether Compute": [
        "last_invoice",
        "recent_average",
        "linear_trend",
        "usage_run_rate",
    ],
    "Harbor Electric": [
        "last_invoice",
        "recent_average",
        "seasonal_prior_year",
    ],
}


def method_label(method: str | None) -> str:
    if not method:
        return "—"
    return METHOD_LABELS.get(method, method.replace("_", " ").title())


def money_text(amount: float | None) -> str:
    if amount is None:
        return "n/a"
    return f"${amount:,.2f}"


def _evidence_lines(trace: VendorDecisionTrace) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    invoices = trace.evidence.historical_invoices
    if invoices:
        last = invoices[-1]
        period = last.get("service_period") or last.get("period") or ""
        lines.append((f"{period} invoice", money_text(last.get("amount"))))
        if trace.vendor == "Harbor Electric":
            prior = next(
                (
                    item
                    for item in invoices
                    if item.get("service_period") == f"{int(trace.period[:4]) - 1}-{trace.period[5:]}"
                ),
                None,
            )
            if prior:
                lines.append((f"{prior['service_period']} invoice", money_text(prior.get("amount"))))
    usage = trace.evidence.usage
    if usage:
        quantity = usage.get("quantity")
        metric = usage.get("metric", "units")
        qty_text = f"{quantity:,.0f} {metric}" if isinstance(quantity, (int, float)) else str(quantity)
        lines.append((f"{usage.get('period', trace.period)} usage", qty_text))
        if usage.get("unit_price") is not None:
            lines.append(("Committed rate", f"${usage['unit_price']} / {metric}"))
    contract = trace.evidence.contract
    if contract and contract.get("amount") is not None:
        cadence = contract.get("billing_cadence", "contract")
        lines.append((f"{cadence.title()} contract", money_text(contract.get("amount"))))
    billed_pos = {item.get("po_id") for item in trace.evidence.current_invoices if item.get("po_id")}
    for receipt in trace.evidence.goods_receipts:
        if receipt.get("po_id") in billed_pos:
            continue
        lines.append(
            (
                f"Goods receipt {receipt.get('receipt_id', '')}".strip(),
                money_text(receipt.get("amount_received")),
            )
        )
    for invoice in trace.evidence.current_invoices:
        lines.append((f"Current invoice {invoice.get('invoice_id', '')}", money_text(invoice.get("amount"))))
    if not lines:
        lines.append(("No reliable period evidence", "—"))
    return lines


def _candidate_rows(trace: VendorDecisionTrace) -> list[tuple[str, str]]:
    featured = FEATURED_METHODS.get(trace.vendor)
    rows = []
    for item in trace.candidate_estimates:
        if featured and item.method not in featured:
            continue
        if not item.applicable and not featured:
            continue
        rows.append((method_label(item.method), money_text(item.amount) if item.applicable else "n/a"))
    if not rows:
        rows = [("No applicable estimate", "—")]
    return rows


def _pad(label: str, value: str, width: int = 28) -> str:
    return f"  {label:<{width}} {value}"


def format_vendor_trace(trace: VendorDecisionTrace) -> str:
    decision = status_label(trace.final_decision)
    amount = money_text(trace.final_amount) if trace.final_decision == "accrual_required" else ""
    decision_line = f"  {decision} {amount}".rstrip()
    lines = [
        trace.vendor.upper(),
        f"Invoice received: {'Yes' if trace.invoice_received else 'No'}",
        "",
        "Evidence:",
    ]
    lines.extend(_pad(label, value) for label, value in _evidence_lines(trace))
    lines.extend(["", "Candidate estimates:"])
    lines.extend(_pad(label, value) for label, value in _candidate_rows(trace))
    lines.extend(
        [
            "",
            "Decision:",
            decision_line,
            f"  Method: {method_label(trace.final_method)}",
            f"  Confidence: {trace.confidence:.0%}",
            f"  {trace.rationale}",
        ]
    )
    if trace.safety_rules_triggered:
        lines.append(f"  Safety: {', '.join(trace.safety_rules_triggered)}")
    if trace.journal_entry:
        lines.extend(
            [
                "",
                "Journal:",
                _pad(f"Dr {trace.journal_entry.debit_account}", money_text(trace.journal_entry.amount), 38),
                _pad(f"Cr {trace.journal_entry.credit_account}", money_text(trace.journal_entry.amount), 38),
            ]
        )
    return "\n".join(lines)


def format_close_summary(report: AccrualPeriodReport) -> str:
    lines = [
        f"Period: {report.period}",
        f"Vendors reviewed: {report.vendors_reviewed}",
        f"Accruals created: {len(report.accruals_created)}",
        f"Skipped because invoice received: {len(report.no_accrual_needed)}",
        f"Insufficient evidence: {len(report.uncertain_items)}",
        f"Total accrued expense: {money_text(report.total_accrued_expense)}",
    ]
    if report.ranked_missing:
        lines.append("")
        lines.append(f"Potential unrecorded expense: {money_text(report.total_accrued_expense)}")
        lines.append("Largest missing bills:")
        for index, item in enumerate(report.ranked_missing, start=1):
            lines.append(
                f"  {index}. {item.vendor:<22} {money_text(item.estimated_amount)}"
            )
    return "\n".join(lines)


def format_period_report(report: AccrualPeriodReport) -> str:
    cards = [format_vendor_trace(trace) for trace in report.traces]
    body = "\n\n".join(cards)
    footer = format_close_summary(report)
    extra = f"\nTraces: {report.trace_dir}" if report.trace_dir else ""
    return f"{body}\n\n{footer}{extra}"


def format_reconciliation(result: ReconciliationResult) -> str:
    abs_error = result.absolute_error if result.absolute_error else abs(result.estimation_error)
    percent = f"{result.percentage_error:.2f}%" if result.percentage_error is not None else "n/a"
    expense = result.expense_account or "Expense"
    signed = f"{'+' if result.estimation_error >= 0 else '-'}${abs_error:,.2f}"
    lines = [
        f"Vendor: {result.vendor}",
        f"Original accrual: {money_text(result.estimated_amount)}",
        f"Actual invoice: {money_text(result.actual_amount)}",
        f"Difference: {signed}",
        f"Absolute error: {money_text(abs_error)}",
        f"Percentage error: {percent}",
        "",
        "Reverse accrual:",
        f"  Dr Accrued Expenses                 {money_text(result.estimated_amount)}",
        f"  Cr {expense:<32} {money_text(result.estimated_amount)}",
        "",
        "Book actual invoice:",
        f"  Dr {expense:<32} {money_text(result.actual_amount)}",
        f"  Cr Accounts Payable                 {money_text(result.actual_amount)}",
    ]
    if result.accrual_id or result.trace_id:
        lines.extend(
            [
                "",
                f"Accrual ID: {result.accrual_id}",
            ]
        )
        if result.trace_id:
            lines.append(f"Accrual trace: {result.trace_id}")
        if result.discovery_trace_id:
            lines.append(f"Discovery trace: {result.discovery_trace_id}")
        if result.reconciliation_trace_id:
            lines.append(f"Reconciliation trace: {result.reconciliation_trace_id}")
        if result.actual_invoice_id:
            lines.append(f"Invoice ID: {result.actual_invoice_id}")
    return "\n".join(lines)


def format_discovery(report: DiscoveryReport) -> str:
    lines = [
        f"{_month_name(report.period).upper()} {report.period[:4]} CLOSE DISCOVERY",
        "",
        f"Expected expenses: {report.expected_count}",
        f"Invoices already received: {report.invoices_received_count}",
        f"Potential missing bills: {report.missing_count}",
        "",
        "MISSING BILL CANDIDATES",
        "",
    ]
    missing = [item for item in report.results if item.missing_bill_candidate]
    if not missing:
        lines.append("None")
    for item in missing:
        evidence = (
            max(item.signals, key=lambda signal: signal.confidence).detail
            if item.signals
            else item.reason
        )
        confidence = (
            f"{item.expectation_confidence:.0%}"
            if item.expectation_confidence >= 0.5
            else "Low"
        )
        lines.extend(
            [
                item.vendor,
                f"  Evidence: {evidence}",
                f"  Invoice received: {'Yes' if item.invoice_received else 'No'}",
                f"  Expectation confidence: {confidence}",
                "",
            ]
        )
    received = [item for item in report.results if item.invoice_received]
    if received:
        lines.append("ALREADY RECEIVED")
        for item in received:
            lines.append(f"  {item.vendor}: {', '.join(item.current_invoice_ids)}")
    return "\n".join(lines).rstrip()


def _month_name(period: str) -> str:
    names = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    return names.get(period[5:], period)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0f}%" if value == int(value) else f"{value}%"


def format_backtest(report: BacktestReport) -> str:
    metrics = report.metrics
    mape = (
        f"{metrics.mean_absolute_percentage_error:.1f}%"
        if metrics.mean_absolute_percentage_error is not None
        else "n/a"
    )
    lines = [
        "ACCRUAL BACKTEST",
        "",
        f"Historical invoices tested: {metrics.invoices_tested}",
        f"Periods: {', '.join(report.periods)}",
        "",
        f"Mean absolute error:       {money_text(metrics.mean_absolute_error)}",
        f"Median absolute error:     {money_text(metrics.median_absolute_error)}",
        f"Mean absolute % error:     {mape}",
        f"Average signed error:      {money_text(metrics.mean_signed_error)}",
        "",
        f"Within 5%:                 {_pct(metrics.within_5_percent)}",
        f"Within 10%:                {_pct(metrics.within_10_percent)}",
        "",
        "METHOD PERFORMANCE",
        "",
    ]
    for item in metrics.by_method:
        pct = (
            f"{item.mean_absolute_percentage_error:.1f}%"
            if item.mean_absolute_percentage_error is not None
            else "n/a"
        )
        lines.extend(
            [
                method_label(item.method),
                f"  observations: {item.observations}",
                f"  mean absolute % error: {pct}",
                "",
            ]
        )
    if report.trace_path:
        lines.append(f"Details: {report.trace_path}")
    return "\n".join(lines).rstrip()
