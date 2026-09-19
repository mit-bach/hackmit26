"""Human-readable close and reconciliation reports for the live demo."""

from __future__ import annotations

from accrual.models import (
    AccrualPeriodReport,
    BacktestReport,
    ComparisonReport,
    DiscoveryReport,
    LiveEvalReport,
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
    rows = []
    for item in trace.candidate_estimates:
        if not item.applicable:
            continue
        rows.append((method_label(item.method), money_text(item.amount)))
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
    if trace.policy_method:
        agreement = (
            "agree"
            if trace.policy_agreement is True
            else "disagree"
            if trace.policy_agreement is False
            else "n/a"
        )
        lines.append(f"  Policy method: {method_label(trace.policy_method)} ({agreement})")
    if trace.diagnostic_warnings:
        lines.append(f"  Diagnostic: {trace.diagnostic_warnings[0]}")
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
            ids = ", ".join(item.current_invoice_ids)
            if len(item.current_invoice_ids) > 1:
                lines.append(
                    f"  {item.vendor}: {len(item.current_invoice_ids)} invoices ({ids}) "
                    "— expected period obligation is satisfied"
                )
            else:
                lines.append(f"  {item.vendor}: {ids}")
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
    analysis = report.recent_average_analysis or {}
    if analysis:
        lines.extend(["", "RECENT AVERAGE FAILURES", ""])
        lines.append(analysis.get("summary", ""))
        for bucket, count in (analysis.get("counts") or {}).items():
            lines.append(f"  {bucket}: {count}")
        if analysis.get("safe_when"):
            lines.append(f"Safe when: {analysis['safe_when']}")
        if analysis.get("weak_when"):
            lines.append(f"Weak when: {analysis['weak_when']}")
        lines.append("")
    if report.trace_path:
        lines.append(f"Details: {report.trace_path}")
    return "\n".join(lines).rstrip()


def format_compare(report: ComparisonReport) -> str:
    lines = [
        f"POLICY VS AGENT  {report.period}",
        "",
        f"Agreements: {report.agreements}",
        f"Disagreements: {report.disagreements}",
        "",
    ]
    for item in report.comparisons:
        agreement = (
            "Yes" if item.agree is True else "No" if item.agree is False else "n/a"
        )
        lines.extend(
            [
                item.vendor,
                "",
                "Policy selection:",
                f"  {item.policy_method or '—'}",
                f"  {money_text(item.policy_amount)}",
                "",
                "Agent selection:",
                f"  {item.agent_method or item.agent_status}",
                f"  {money_text(item.agent_amount)}",
                "",
                f"Agreement:",
                f"  {agreement}",
                "",
            ]
        )
        if item.diagnostic_warnings:
            lines.append(f"Diagnostic: {item.diagnostic_warnings[0]}")
            lines.append("")
    if report.trace_path:
        lines.append(f"Details: {report.trace_path}")
    return "\n".join(lines).rstrip()


def format_decision_quality(report: AccrualPeriodReport) -> str:
    lines = ["DECISION QUALITY", ""]
    for trace in report.traces:
        agree = (
            "agree"
            if trace.policy_agreement is True
            else "disagree"
            if trace.policy_agreement is False
            else "n/a"
        )
        evidence = "limited"
        if trace.evidence.usage:
            evidence = "direct usage + contract rate"
        elif any(item.method == "goods_receipt" and item.applicable for item in trace.candidate_estimates):
            evidence = "goods received, invoice missing"
        elif trace.evidence.contract and (trace.evidence.contract.get("amount") is not None):
            evidence = "fixed contractual commitment"
        elif any(item.method == "seasonal_prior_year" and item.applicable for item in trace.candidate_estimates):
            evidence = "seasonal history"
        elif trace.invoice_received:
            evidence = f"{len(trace.evidence.current_invoices)} current-period invoice(s) received"
        if trace.final_decision == "insufficient_evidence":
            lines.extend(
                [
                    f"{trace.vendor}:",
                    "  Insufficient evidence",
                    "  No booking",
                    "",
                ]
            )
            continue
        if trace.final_decision == "no_accrual_needed":
            lines.extend(
                [
                    f"{trace.vendor}:",
                    f"  Invoice already received ({len(trace.evidence.current_invoices)} bill(s))",
                    "  No accrual",
                    "",
                ]
            )
            continue
        extra = ""
        if (
            trace.policy_method == "seasonal_prior_year"
            and trace.final_method == "seasonal_prior_year"
        ):
            extra = "\n  Recent-average warning avoided"
        elif any("REVIEW_FLAG" in item for item in trace.diagnostic_warnings):
            extra = "\n  " + next(item for item in trace.diagnostic_warnings if "REVIEW_FLAG" in item)
        hist = "n/a"
        if trace.final_method == "usage_run_rate" or trace.final_method == "contract_commitment":
            hist = "low"
        elif trace.final_method == "goods_receipt":
            hist = "deterministic GRNI rule"
        elif trace.final_method == "seasonal_prior_year":
            hist = "seasonal history preferred"
        lines.extend(
            [
                f"{trace.vendor}:",
                f"  Agent vs policy: {agree}",
                f"  Evidence quality: {evidence}",
                f"  Historical method error: {hist}{extra}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def format_live_eval(report: LiveEvalReport) -> str:
    lines = [
        "LIVE AGENT CONSISTENCY",
        "",
        f"Period: {report.period}",
        f"Runs: {report.runs}",
        "",
    ]
    for item in report.summaries:
        lines.append(f"{item.vendor}:")
        for method, count in sorted(item.method_counts.items(), key=lambda pair: (-pair[1], pair[0])):
            lines.append(f"  {method}: {count}/{item.trials}")
        lines.append("")
    if report.trace_path:
        lines.append(f"Details: {report.trace_path}")
    return "\n".join(lines).rstrip()
