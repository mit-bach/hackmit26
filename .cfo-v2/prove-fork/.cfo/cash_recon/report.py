"""Human-readable monthly cash reconciliation report and traces."""

from __future__ import annotations

from accrual.report import _month_name
from cash_recon.eval import format_metrics
from cash_recon.mathutil import money_text
from cash_recon.models import CashReconciliationReport, MatchTrace

MATCHED_STATUSES = {"MATCHED"}


def format_cash_report(report: CashReconciliationReport) -> str:
    month = f"{_month_name(report.period)} {report.period[:4]} Cash Reconciliation"
    lines = [
        month,
        "",
        f"Bank ending balance: {money_text(report.bank_ending)}",
        f"Ledger cash balance: {money_text(report.ledger_ending)}",
        f"Reconciled amount: {money_text(report.reconciled_amount)}",
        f"Outstanding timing items: {money_text(report.outstanding_timing)}",
        f"Unexplained difference: {money_text(report.unexplained_difference)}",
        f"Items requiring human review: {report.human_review_count}",
        f"Period status: {report.period_status}",
        f"Arithmetic tie-out: {'PASS' if report.arithmetic_tied else 'FAIL'}",
        "",
        "Matched:",
    ]
    matched = [item for item in report.matches if item.status in MATCHED_STATUSES]
    if not matched:
        lines.append("- (none)")
    for item in matched:
        lines.append(
            f"- {item.reconciliation_id} {item.match_type} {item.status}: {item.explanation}"
        )
    lines.extend(["", "Exceptions:"])
    exceptions = [item for item in report.matches if item.status not in MATCHED_STATUSES]
    if not exceptions:
        lines.append("- (none)")
    for item in exceptions:
        lines.append(
            f"- {item.reconciliation_id} {item.match_type} {item.status}: {item.explanation}"
        )
    lines.extend(["", "Controls:"])
    if report.control_findings:
        for finding in report.control_findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- (none)")
    if report.tie_out.items:
        lines.extend(["", "Tie-out:"])
        lines.append(
            f"Bank {money_text(report.tie_out.bank_ending)} − ledger {money_text(report.tie_out.ledger_ending)} "
            f"= break {money_text(report.tie_out.break_amount)}"
        )
        lines.append(f"Reconciling items {money_text(report.tie_out.reconciling_sum)}")
        for row in report.tie_out.items:
            lines.append(
                f"- {row['reconciliation_id']} {row['match_type']}: {money_text(row['impact'])}"
            )
    if report.metrics:
        lines.extend(["", format_metrics(report.metrics)])
    if report.trace_path:
        lines.extend(["", f"Trace packet: {report.trace_path}"])
    return "\n".join(lines)


def format_match_trace(trace: MatchTrace) -> str:
    lines = [
        f"Reconciliation {trace.reconciliation_id}",
        f"Period: {trace.period}",
        f"Match type: {trace.match_type}",
        f"Final status: {trace.status}",
        f"Human review: {'yes' if trace.human_review else 'no'}",
        "",
        "Bank transactions:",
    ]
    for item in trace.bank_transactions:
        lines.append(f"- {item.transaction_id} {item.date} {money_text(item.amount)} {item.description}")
    if not trace.bank_transactions:
        lines.append("- (none)")
    lines.extend(["", "Ledger entries:"])
    for item in trace.ledger_entries:
        lines.append(f"- {item.entry_id} {item.date} {money_text(item.amount)} {item.counterparty} {item.reference}")
    if not trace.ledger_entries:
        lines.append("- (none)")
    lines.extend(["", "Candidates:"])
    for item in trace.candidates:
        lines.append(
            f"- {item.candidate_id} {item.match_type} bank={money_text(item.bank_amount)} "
            f"ledger={money_text(item.ledger_amount)} diff={money_text(item.difference)}"
        )
    calc = trace.calculations or {}
    lines.extend(
        [
            "",
            "Calculations:",
            f"- bank_amount_minor: {calc.get('bank_amount_minor')}",
            f"- ledger_amount_minor: {calc.get('ledger_amount_minor')}",
            f"- difference_minor: {calc.get('difference_minor')}",
        ]
    )
    if trace.preparer:
        lines.extend(
            [
                "",
                "Preparer:",
                f"- disposition: {trace.preparer.disposition}",
                f"- candidate: {trace.preparer.selected_candidate_id}",
                f"- {trace.preparer.reasons[0] if trace.preparer.reasons else ''}",
            ]
        )
    if trace.investigation:
        lines.extend(["", "Investigator:"])
        for finding in trace.investigation.findings:
            lines.append(f"- {finding}")
        if trace.investigation.unsupported_hypotheses:
            lines.append("Unsupported: " + ", ".join(trace.investigation.unsupported_hypotheses))
    if trace.validation:
        lines.extend(
            [
                "",
                "Validator:",
                f"- passed: {'yes' if trace.validation.passed else 'no'}",
                f"- human_review_required: {'yes' if trace.validation.human_review_required else 'no'}",
            ]
        )
        lines.extend(f"- {error}" for error in trace.validation.errors)
    if trace.reviewer:
        lines.extend(
            [
                "",
                "Reviewer:",
                f"- {trace.reviewer.reviewer_status} / {trace.reviewer.disposition}",
                f"- arithmetic_ok: {'yes' if trace.reviewer.arithmetic_ok else 'no'}",
            ]
        )
    lines.extend(["", f"Evidence: {', '.join(trace.evidence) or '(none)'}"])
    if trace.control_findings:
        lines.append("Controls: " + ", ".join(trace.control_findings))
    if trace.proposed_journal_entries:
        lines.extend(["", "Proposed journal entries (not posted):"])
        for entry in trace.proposed_journal_entries:
            lines.append(f"- {entry.memo}")
            for line in entry.lines:
                lines.append(f"  {line.side} {line.account} {money_text(line.amount)}")
    if trace.trace_path:
        lines.extend(["", f"Trace file: {trace.trace_path}"])
    return "\n".join(lines)
