"""Demo-friendly AR output."""

from __future__ import annotations

from accrual.report import money_text
from ar.models import AgingReport, CashApplyTrace, CashReviewItem, CollectionRun


def format_aging(report: AgingReport) -> str:
    totals = report.totals
    lines = [
        f"RECEIVABLES AGING as of {report.as_of_date}",
        "",
        f"Total AR: {money_text(totals.total_ar)}",
        f"Current:  {money_text(totals.current_ar)}",
        f"Past due: {money_text(totals.past_due_ar)}",
        f"Disputed: {money_text(totals.disputed_ar)}",
        f"Partially paid: {money_text(totals.partially_paid_ar)}",
        "",
        "BUCKETS",
    ]
    for bucket in ("CURRENT", "1-30", "31-60", "61-90", "90+"):
        amount = totals.bucket_amounts.get(bucket, 0)
        pct = totals.bucket_percents.get(bucket, 0)
        lines.append(f"- {bucket:<6} {money_text(amount):>12}  {pct:5.1f}%")
    lines.extend(["", "OPEN INVOICES", ""])
    lines.append(
        f"{'Invoice':<12} {'Customer':<22} {'Due':<12} {'DPD':>4} {'Bucket':<6} {'Outstanding':>12} Status"
    )
    for item in report.lines:
        lines.append(
            f"{item.invoice_id:<12} {item.customer_name:<22} {item.due_date:<12} "
            f"{item.days_past_due:>4} {item.aging_bucket:<6} {money_text(item.outstanding_amount):>12} "
            f"{item.invoice_status}"
            + (" DISPUTE" if item.dispute_status == "OPEN" else "")
        )
    lines.extend(["", "CUSTOMERS", ""])
    for item in report.customers:
        lines.append(
            f"- {item.customer_id} {item.customer_name}: {money_text(item.total_outstanding)} "
            f"outstanding, oldest {item.oldest_unpaid_invoice} ({item.max_days_past_due} dpd), "
            f"{item.open_invoices} open"
        )
    return "\n".join(lines)


def format_collections(run: CollectionRun) -> str:
    lines = [f"COLLECTIONS as of {run.as_of_date}", ""]
    if run.blocked:
        lines.extend(
            [
                "BLOCKED. Apply has not drained new deposits for this as-of.",
                run.block_reason or "Handle apply first.",
                "",
            ]
        )
        if run.apply_handle_path:
            lines.append(f"Handle path: {run.apply_handle_path}")
            lines.append("")
        return "\n".join(lines).rstrip()
    featured = sorted(
        run.decisions,
        key=lambda item: (
            item.action == "NO_ACTION",
            -item.days_past_due,
            -item.outstanding_amount,
        ),
    )
    for item in featured:
        lines.extend(
            [
                f"{item.customer_id} / {item.invoice_id}",
                f"Outstanding: {money_text(item.outstanding_amount)}",
                f"{item.days_past_due} days past due",
                f"Prior reminders: {item.reminder_count}",
                f"Action: {item.action}",
                f"Human approval: {str(item.human_approval_required).lower()}",
                f"Reason: {item.reason}",
            ]
        )
        if item.draft_message:
            lines.append("Draft:")
            lines.append(item.draft_message)
        lines.append("")
    return "\n".join(lines).rstrip()


def format_cash_apply(trace: CashApplyTrace) -> str:
    payment = trace.payment
    lines = [
        f"CASH APPLICATION {payment.payment_id}",
        f"Payer: {payment.payer_name}",
        f"Amount: {money_text(payment.amount)}",
        f"Remittance: {payment.remittance_text or '(none)'}",
        f"Status: {payment.application_status}",
        "",
        "CANDIDATES",
    ]
    if not trace.facts.candidates:
        lines.append("- (none)")
    for item in trace.facts.candidates:
        apps = ", ".join(f"{row.invoice_id} {money_text(row.amount)}" for row in item.applications)
        lines.append(f"- {item.candidate_id} [{item.match_type}] {apps}")
        for note in item.ambiguities:
            lines.append(f"    ambiguity: {note}")
    lines.extend(
        [
            "",
            f"Preparer: {trace.preparer.decision} ({trace.preparer.confidence:.2f})",
            f"  {trace.preparer.reason}",
            f"Validation: {'PASS' if trace.validation.passed else 'FAIL'}",
        ]
    )
    if trace.validation.errors:
        for error in trace.validation.errors:
            lines.append(f"  - {error}")
    if trace.reviewer:
        lines.append(
            f"Reviewer: {trace.reviewer.recommendation} "
            f"(agree={str(trace.reviewer.agree_with_preparer).lower()})"
        )
    lines.extend(
        [
            "",
            f"FINAL: {trace.final.decision}",
            f"Reason: {trace.final.reason}",
        ]
    )
    if trace.already_posted:
        lines.append("Already posted — balances were not changed again.")
    if trace.posted and trace.record:
        lines.append("Posted applications:")
        for row in trace.record.applications:
            lines.append(f"- {row.invoice_id} {money_text(row.amount)}")
        if trace.record.unapplied_amount:
            lines.append(f"Unapplied cash: {money_text(trace.record.unapplied_amount)}")
        lines.append("Invoice state changes:")
        for change in trace.state_changes:
            lines.append(
                f"- {change.invoice_id}: {money_text(change.previous_outstanding)} "
                f"→ {money_text(change.new_outstanding)} ({change.previous_status} → {change.new_status})"
            )
    elif trace.final.review_question:
        lines.append(f"Review question: {trace.final.review_question}")
        for note in trace.final.ambiguities:
            lines.append(f"- {note}")
        lines.append("AR balances were not changed.")
    if trace.trace_path:
        lines.extend(["", f"Trace saved to {trace.trace_path}"])
    return "\n".join(lines)


def format_demo(payload: dict) -> str:
    before: AgingReport = payload["before"]
    after: AgingReport = payload["after"]
    collections: CollectionRun = payload["collections"]
    auto: CashApplyTrace = payload["auto_apply"]
    review: CashApplyTrace = payload["human_review"]
    featured = next(
        (item for item in collections.decisions if item.invoice_id == "INV-AR-020"),
        collections.decisions[0] if collections.decisions else None,
    )
    verifier_case = next(
        (item for item in collections.decisions if item.human_approval_required),
        None,
    )
    blocks = [
        "ACCOUNTS RECEIVABLE DEMO",
        f"As of {payload['as_of']}",
        "",
        "1. AGING BEFORE PAYMENT",
        "",
        format_aging(before),
        "",
        "2. STRAIGHTFORWARD PAYMENT (PAY-001)",
        "",
        format_cash_apply(auto),
        "",
        "3. AMBIGUOUS PAYMENT (PAY-AMBIGUOUS / PAY-005) → ctl-cash",
        "",
        format_cash_apply(review),
        "",
        "4. COLLECTIONS AFTER APPLY DRAIN",
        "",
    ]
    if collections.blocked:
        blocks.append(collections.block_reason or "Collections blocked until apply drains.")
        if collections.apply_handle_path:
            blocks.append(f"Handle path: {collections.apply_handle_path}")
    elif featured:
        blocks.append(
            f"{featured.customer_id} / {featured.invoice_id}\n"
            f"Outstanding: {money_text(featured.outstanding_amount)}\n"
            f"{featured.days_past_due} days past due\n"
            f"Prior reminders: {featured.reminder_count}\n"
            f"Action: {featured.action}\n"
            f"Verifier required: {str(featured.human_approval_required).lower()}\n"
            f"Reason: {featured.reason}"
        )
        if featured.draft_message:
            blocks.extend(["", "Draft collection message", "", featured.draft_message])
    if verifier_case and (not featured or verifier_case.invoice_id != featured.invoice_id):
        blocks.extend(
            [
                "",
                f"Verifier collections case: {verifier_case.customer_id} / {verifier_case.invoice_id}",
                f"Action: {verifier_case.action}",
                f"Reason: {verifier_case.reason}",
            ]
        )
    blocks.extend(
        [
            "",
            "5. AGING AFTER APPLICATION",
            "",
            f"Total AR before: {money_text(before.totals.total_ar)}",
            f"Total AR after:  {money_text(after.totals.total_ar)}",
            f"Change: {money_text(after.totals.total_ar - before.totals.total_ar)}",
            "",
            format_aging(after),
            "",
            "6. AUDIT TRACE",
            "",
            f"PAY-001 decision: {auto.final.decision}",
            f"  {auto.final.reason}",
        ]
    )
    for change in auto.state_changes:
        blocks.append(
            f"  {change.invoice_id}: {money_text(change.previous_outstanding)} → "
            f"{money_text(change.new_outstanding)} ({change.new_status})"
        )
    if auto.trace_path:
        blocks.append(f"  Trace: {auto.trace_path}")
    handle_note = review.verifier_handle_path or "(no handle path)"
    blocks.extend(
        [
            "",
            f"PAY-005 decision: {review.final.decision}",
            f"  {review.final.reason}",
            "  Invoice balances were not mutated.",
            f"  Verifier Handle: {handle_note}",
        ]
    )
    if review.trace_path:
        blocks.append(f"  Trace: {review.trace_path}")
    return "\n".join(blocks)


def format_review_list(items: list[CashReviewItem]) -> str:
    lines = ["CTL-CASH VERIFIER QUEUE (not a human queue)", ""]
    if not items:
        lines.append("(empty)")
        return "\n".join(lines)
    for item in items:
        customer = item.customer_name or item.customer_id or "(unknown)"
        lines.append(
            f"{item.review_id}  {item.payment_id}  {customer}  "
            f"{money_text(item.payment_amount)}  {item.status}"
        )
        if item.ambiguities:
            lines.append(f"  {item.ambiguities[0]}")
    return "\n".join(lines)


def format_review_item(item: CashReviewItem) -> str:
    customer = item.customer_name or item.customer_id or "(unknown)"
    lines = [
        f"REVIEW {item.review_id}",
        f"Payment: {item.payment_id}",
        f"Customer: {customer}",
        f"Amount: {money_text(item.payment_amount)}",
        f"Date: {item.payment_date}",
        f"Remittance: {item.remittance_text or '(none)'}",
        f"Reference: {item.invoice_reference or item.bank_reference or '(none)'}",
        f"Status: {item.status}",
        f"Confidence: {item.confidence:.2f}",
        "",
        "CANDIDATES",
    ]
    if not item.candidates:
        lines.append("- (none)")
    for candidate in item.candidates:
        apps = ", ".join(f"{row.invoice_id} {money_text(row.amount)}" for row in candidate.applications)
        lines.append(f"- {candidate.candidate_id} [{candidate.match_type}] {apps}")
    lines.append("")
    if item.agent_recommendation:
        lines.append(
            f"Agent: {item.agent_recommendation.decision} — {item.agent_recommendation.reason}"
        )
    if item.reviewer_recommendation:
        lines.append(
            f"Reviewer agent: {item.reviewer_recommendation.recommendation} — "
            + "; ".join(item.reviewer_recommendation.reasons)
        )
    if item.proposed_applications:
        lines.append("Proposed allocation:")
        for row in item.proposed_applications:
            lines.append(f"- {row.invoice_id} {money_text(row.amount)}")
    else:
        lines.append("Proposed allocation: (none — human must specify invoices)")
    if item.ambiguities:
        lines.append("Ambiguities:")
        for note in item.ambiguities:
            lines.append(f"- {note}")
    if item.trace_path:
        lines.append(f"Trace: {item.trace_path}")
    if item.resolved_at:
        lines.extend(
            [
                "",
                f"Resolved: {item.status} by {item.resolved_by} at {item.resolved_at}",
                f"Reason: {item.resolution_reason}",
            ]
        )
        for row in item.final_applications:
            lines.append(f"- {row.invoice_id} {money_text(row.amount)}")
        if item.differed_from_agent:
            lines.append("Final allocation differed from the agent proposal.")
    return "\n".join(lines)


def format_review_resolution(item: CashReviewItem) -> str:
    return format_review_item(item)


def format_forecast_demo(payload: dict) -> str:
    from reporting.report import format_cash_forecast

    blocks = [
        "AR + 13-WEEK CASH FORECAST DEMO",
        f"As of {payload['as_of']}",
        "",
        "A. INITIAL 13-WEEK FORECAST",
        "",
        format_cash_forecast(payload["forecast_before"]),
        "",
        "B. AMBIGUOUS PAY-005 → HUMAN_REVIEW (ctl-cash packet)",
        "",
        format_cash_apply(payload["human_review"]),
        "",
        "C. REVIEW QUEUE",
        "",
        format_review_list(payload["queue_before"]),
        "",
        "D. VERIFIER CORRECTION (ctl-cash Kernel door; ar-review-correct is emergency)",
        "",
        format_review_item(payload["resolved"]),
        "",
        "E. INVOICE / PAYMENT / JOURNAL MUTATION",
        "",
    ]
    for change in payload.get("invoice_changes") or []:
        blocks.append(
            f"- {change.invoice_id}: {money_text(change.previous_outstanding)} → "
            f"{money_text(change.new_outstanding)} ({change.previous_status} → {change.new_status})"
        )
    payment = payload["payment_after"]
    blocks.append(
        f"- {payment.payment_id} status {payment.application_status} "
        f"unapplied {money_text(payment.unapplied_amount)}"
    )
    for journal in payload.get("journals") or []:
        blocks.append(
            f"- {journal.entry_id} Dr {journal.debit.account} "
            f"{money_text(journal.debit.amount)} / Cr {journal.credit.account} "
            f"{money_text(journal.credit.amount)}"
        )
    blocks.extend(
        [
            "",
            "F. UPDATED AGING",
            "",
            format_aging(payload["aging_after"]),
            "",
            "G. UPDATED 13-WEEK FORECAST",
            "",
            format_cash_forecast(payload["forecast_after"]),
            "",
            "H. AUDIT TRACE",
            "",
        ]
    )
    for event in payload.get("audit") or []:
        blocks.append(f"- {event['event_type']}: {event['summary']}")
    blocks.extend(["", "I. PRECEDENT CREATED FROM CORRECTION", ""])
    for item in payload.get("precedents") or []:
        blocks.append(f"- {item.precedent_id} [{item.kind}] support={item.support_count}")
        blocks.append(f"  {item.summary}")
    return "\n".join(blocks)
