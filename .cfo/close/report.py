"""Human-readable combined close packet."""

from __future__ import annotations

from accrual.report import _month_name, money_text
from close.models import CloseRun


def _accrual_precedent_lines(report) -> list[str]:
    lines: list[str] = []
    for card in report.traces:
        lookup = getattr(card, "memory_lookup", None)
        if lookup is None:
            continue
        amount = money_text(card.final_amount) if card.final_decision == "accrual_required" else card.final_decision
        method = card.final_method or "—"
        if lookup.precedent_used and lookup.retrieved:
            lines.append(
                f"{card.vendor}: {method} {amount} (prior decision {lookup.retrieved[0]})"
            )
        elif lookup.deviation:
            lines.append(f"{card.vendor}: {method} {amount} — {lookup.deviation}")
    return lines


def format_close_run(state: CloseRun) -> str:
    accrual = state.accrual
    discovery = state.discovery
    payment = state.payment
    month = f"{_month_name(state.period).upper()} {state.period[:4]} CFO CLOSE"
    lines = [
        month,
        "",
        "INVOICES",
        "",
        f"Received: {state.invoices_received}",
        f"Approved: {len(state.approved_ids)}",
        f"Held: {len(state.held_ids)}",
        f"Ingested canonical (session): {state.ingestion_canonical}",
        f"Cross-source duplicates removed: {state.ingestion_duplicates}",
        "",
        "MISSING BILLS",
        "",
    ]
    if discovery and accrual:
        lines.extend(
            [
                f"Expected expenses: {discovery.expected_count}",
                f"Bills already received: {discovery.invoices_received_count}",
                f"Missing-bill candidates: {discovery.missing_count}",
                f"Accruals booked: {len(accrual.accruals_created)}",
                f"Accrued expense: {money_text(accrual.total_accrued_expense)}",
            ]
        )
        precedents = _accrual_precedent_lines(accrual)
        if precedents:
            lines.extend(["", "PRIOR-PERIOD ACCRUAL DECISIONS", ""])
            lines.extend(precedents)
    else:
        lines.append("Accrual workflow did not run.")
    lines.extend(["", "PAYMENTS", ""])
    if payment:
        lines.extend(
            [
                f"Spendable cash: {money_text(state.spendable_cash)}",
                f"Approved invoices considered: {len(payment.candidates)}",
                f"Payments scheduled: {len(payment.plan.pay_this_week)}",
                f"Deferred: {len(payment.plan.defer)}",
                f"Total payout: {money_text(payment.plan.total_payout)}",
                f"Reserve OK: {'yes' if payment.plan.reserve_ok else 'NO'}",
            ]
        )
    else:
        lines.append("Payment scheduler did not run.")

    payouts = [item for item in state.integrations if item.payout_id]
    if payouts:
        lines.extend(
            [
                "",
                "CASH EVENTS",
                "",
                f"Provider payouts recorded: {len({item.payout_id for item in payouts})}",
                "Payouts are cash movements, not new AP invoices.",
            ]
        )

    if state.ar:
        lines.extend(
            [
                "",
                "ACCOUNTS RECEIVABLE",
                "",
                f"Total AR: {money_text(state.ar.total_ar)}",
                f"Past due: {money_text(state.ar.past_due_ar)}",
                f"Disputed: {money_text(state.ar.disputed_ar)}",
                f"Unapplied cash: {money_text(state.ar.unapplied_cash)}",
                f"Expected collections (7d): {money_text(state.ar.expected_collections_7d)}",
            ]
        )

    lines.extend(["", "EXCEPTIONS", ""])
    if state.exceptions:
        for item in state.exceptions[:12]:
            lines.append(f"- {item.detail}")
        if len(state.exceptions) > 12:
            lines.append(f"- … {len(state.exceptions) - 12} more")
    else:
        lines.append("- none")

    if state.reconciliations:
        lines.extend(["", "RECONCILIATION", ""])
        for item in state.reconciliations:
            lines.append(
                f"- {item.vendor}: accrued {money_text(item.estimated_amount)} → "
                f"actual {money_text(item.actual_amount)} "
                f"({item.actual_invoice_id})"
            )

    lines.extend(
        [
            "",
            "AUDIT",
            "",
            f"Close ID: {state.close_id}",
            f"AP traces: {len(state.audit.ap_traces)}",
            f"Accrual traces: {state.audit.accrual_trace_dir or '—'}",
            f"Payment-plan trace: {state.audit.payment_plan_trace or '—'}",
        ]
    )
    if state.audit.reconciliation_traces:
        lines.append("Reconciliation: " + ", ".join(state.audit.reconciliation_traces))
    if state.audit.ingestion_trace:
        lines.append(f"Ingestion: {state.audit.ingestion_trace}")
    graph = _audit_graph_lines(state)
    if graph:
        lines.extend(["", "AUDIT GRAPH", "", *graph])
    if state.trace_path:
        lines.extend(["", f"Close packet: {state.trace_path}"])
    return "\n".join(lines)


def _audit_graph_lines(state: CloseRun) -> list[str]:
    """Point at existing IDs. Does not invent a second trace format."""
    lines: list[str] = []
    featured = [item for item in state.ap_results if item.invoice_id in {"INV-001", "INV-016"}]
    for item in featured:
        dest = "payment pool" if item.decision == "APPROVE" else "not scheduled"
        lines.append(
            f"{item.invoice_id} → {item.ap_decision_id or item.source} → {dest}"
        )
    if state.accrual:
        for card in state.accrual.traces:
            if card.final_decision != "accrual_required":
                continue
            if card.vendor not in {"Aether Compute", "Harbor Electric"}:
                continue
            disc = card.discovery_trace_id or "discovery"
            acc = card.trace_id or "accrual"
            lines.append(f"{card.vendor}: {disc} → {acc}")
    for item in state.reconciliations:
        lines.append(
            f"{item.vendor}: {item.discovery_trace_id} → "
            f"{item.accrual_trace_id} → {item.reconciliation_trace_id}"
        )
    overlay = [
        number
        for item in state.integrations
        for number in item.invoice_numbers
        if number not in state.invoice_ids
    ]
    if overlay:
        unique = list(dict.fromkeys(overlay))
        lines.append(
            "Provider documents "
            + ", ".join(unique[:4])
            + " linked in overlay; not added to the AP inbox."
        )
    return lines


def format_demo_close(state: CloseRun) -> str:
    """Narrate the same CloseRun. No invented numbers."""
    by_id = {item.invoice_id: item for item in state.ap_results}
    lines = [
        "OFFICE OF THE CFO — CONNECTED CLOSE",
        "",
        "1. Invoices received",
        f"   {state.invoices_received} AP inbox invoices for {state.period}.",
        f"   Ingestion added {state.ingestion_canonical} canonical records "
        f"and removed {state.ingestion_duplicates} cross-source duplicates.",
        "",
        "2. AP exception",
    ]
    missing_po = by_id.get("INV-016")
    if missing_po:
        lines.append(
            f"   {missing_po.invoice_id} {missing_po.vendor} is {missing_po.decision} "
            f"({', '.join(missing_po.exceptions) or 'held'})."
        )
    clean = by_id.get("INV-001")
    if clean:
        lines.append(f"   {clean.invoice_id} {clean.vendor} is {clean.decision} and can enter the pay pool.")
    lines.extend(["", "3. Accrual discovery"])
    if state.discovery:
        lines.append(
            f"   Expected {state.discovery.expected_count}; "
            f"{state.discovery.invoices_received_count} already billed; "
            f"{state.discovery.missing_count} missing."
        )
    helios_docs = [
        item.provider
        for item in state.integrations
        if "HEL-INV-6200" in item.invoice_numbers
    ]
    if helios_docs:
        lines.append(
            f"   Helios HEL-INV-6200 arrived via {helios_docs[0]} — "
            "goods-receipt accrual is not needed."
        )
    if state.accrual:
        for vendor in ("Aether Compute", "Harbor Electric", "Helios Hardware", "NewForge Consulting"):
            card = next((item for item in state.accrual.traces if item.vendor == vendor), None)
            if not card:
                continue
            if card.final_decision == "accrual_required":
                lookup = getattr(card, "memory_lookup", None)
                prior = ""
                if lookup is not None and lookup.precedent_used and lookup.retrieved:
                    prior = f" (prior decision {lookup.retrieved[0]})"
                elif lookup is not None and lookup.deviation:
                    prior = f" (deviation from {lookup.retrieved[0]})" if lookup.retrieved else " (prior-period deviation)"
                lines.append(
                    f"   {vendor}: {card.final_method} {money_text(card.final_amount)}{prior}"
                )
            else:
                lines.append(f"   {vendor}: {card.final_decision}")
        lines.append(
            f"   Booked {len(state.accrual.accruals_created)} accruals totaling "
            f"{money_text(state.accrual.total_accrued_expense)}."
        )
    if state.payment:
        lines.extend(
            [
                "",
                "4. Payment scheduling",
                f"   Spendable cash {money_text(state.spendable_cash)}. "
                f"{len(state.payment.plan.pay_this_week)} paid this week, "
                f"{len(state.payment.plan.defer)} deferred.",
            ]
        )
        held_in_plan = [
            row.invoice_id
            for row in state.payment.plan.pay_this_week
            if row.invoice_id in set(state.held_ids)
        ]
        if not held_in_plan:
            lines.append("   HOLD invoices are not in this week's payouts.")
    if state.reconciliations:
        item = state.reconciliations[0]
        lines.extend(
            [
                "",
                "5. Later invoice",
                f"   {item.vendor} accrual {money_text(item.estimated_amount)} "
                f"vs invoice {item.actual_invoice_id} {money_text(item.actual_amount)}.",
                f"   {item.discovery_trace_id} → {item.accrual_trace_id} → {item.reconciliation_trace_id}",
            ]
        )
    lines.extend(["", format_close_run(state)])
    return "\n".join(lines)


def format_month_end_status(state) -> str:
    from close.dates import month_name

    title = f"{month_name(state.period.period).upper()} {state.period.period[:4]} CLOSE"
    lines = [title, "-" * len(title), ""]
    display = {
        "ap": "AP processing",
        "ar": "AR processing",
        "cash": "Cash reconciliation",
        "accruals": "Accruals",
        "prepaid": "Prepaid amortization",
        "depreciation": "Depreciation",
        "bs_recon": "Balance-sheet reconciliations",
        "final_review": "Final review",
    }
    width = max(len(label) for label in display.values())
    for task in state.tasks:
        label = display.get(task.task_id)
        if not label:
            continue
        lines.append(f"{label.ljust(width)} {task.status}")
    attention = list(
        dict.fromkeys(
            item.detail
            for item in state.exceptions
            if item.kind in {"cash_unexplained", "prepaid_evidence", "bs_recon"}
        )
    )
    from close.reviews import load_reviews

    review = list(dict.fromkeys(state.human_review_items))
    queued = [item for item in load_reviews(state.period.period) if item.status != "RESOLVED"]
    if queued:
        lines.extend(["", "Open review items:"])
        for item in queued:
            lines.append(f"- {item.description} [{item.review_id}]")
    elif review or attention:
        lines.extend(["", "Blocking items:"])
        for item in review:
            lines.append(f"- {item}")
        for item in attention:
            if item not in review:
                lines.append(f"- {item}")
    lines.extend(["", f"Close status: {state.period.status}"])
    lines.append(f"Period status: {state.period.status}")
    lines.append(f"Completion: {state.completion_pct:.0f}%")
    if getattr(state, "snapshot_path", None):
        lines.append(f"Snapshot: {state.snapshot_path}")
    if state.trace_path:
        lines.append(f"Packet: {state.trace_path}")
    if getattr(state, "manager", None) and state.manager:
        lines.extend(["", "Close manager:", state.manager.narrative])
    return "\n".join(lines)


def format_month_end_demo(state) -> str:
    from close.ledger import load_entries

    steps = [
        ("ap", "AP"),
        ("ar", "AR"),
        ("cash", "Cash reconciliation"),
        ("accruals", "Accruals"),
        ("prepaid", "Prepaid amortization"),
        ("depreciation", "Depreciation"),
        ("bs_recon", "Balance-sheet reconciliations"),
        ("final_review", "Final review"),
    ]
    by_id = {item.task_id: item for item in state.tasks}
    lines = ["OFFICE OF THE CFO — MONTH-END CLOSE", ""]
    for index, (task_id, label) in enumerate(steps, start=1):
        task = by_id.get(task_id)
        status = task.status if task else "NOT_STARTED"
        if status == "NOT_STARTED" and task and (
            task.blocker_reason or (by_id.get("bs_recon") and by_id["bs_recon"].status == "BLOCKED")
        ):
            status = "WAITING"
        lines.append(f"[{index}/{len(steps)}] {label} {status}")
    if state.accrual:
        citations = _accrual_precedent_lines(state.accrual)
        if citations:
            lines.extend(["", "ACCRUAL METHODOLOGY", *citations])
    journals = load_entries()
    journal_lines = [
        f"- {item['entry_id']}  Dr {item['debit_account']}  Cr {item['credit_account']}  "
        f"${item['debit']:,.2f}  [{item['entry_type']}]"
        for item in journals
    ] or ["- (none)"]
    recon_lines = [f"- {item}" for item in state.reconciliation_ids] or ["- (none)"]
    exception_lines = [f"- {item.detail}" for item in state.exceptions] or ["- (none)"]
    review_lines = [f"- {item}" for item in state.human_review_items] or ["- (none)"]
    lines.extend(
        [
            "",
            "JOURNAL ENTRIES",
            *journal_lines,
            "",
            "RECONCILIATIONS",
            *recon_lines,
            "",
            "UNRESOLVED EXCEPTIONS",
            *exception_lines,
            "",
            "HUMAN REVIEW",
            *review_lines,
            "",
            f"Close completion: {state.completion_pct:.0f}%",
            f"Evidence / traces: {state.trace_path or '—'}",
            "",
            format_month_end_status(state),
        ]
    )
    return "\n".join(lines)


def format_close_trace(state) -> str:
    from close.period_lock import load_events
    from close.snapshot import list_snapshots
    from close.resolve import load_resolutions

    lines = [
        f"CLOSE TRACE — {state.period.period}",
        f"Status: {state.period.status}",
        f"Close ID: {state.close_id}",
        "",
        "DEPENDENCY GRAPH",
    ]
    for task in state.tasks:
        deps = ", ".join(task.dependencies) or "—"
        lines.append(f"- {task.task_id}: {task.status}  depends_on=[{deps}]  owner={task.owner_agent}")
        if task.blocker_reason:
            lines.append(f"    blocker: {task.blocker_reason}")
        if task.output_refs:
            lines.append(f"    outputs: {', '.join(task.output_refs[:6])}")
    lines.extend(["", "RECONCILIATIONS"])
    for item in state.reconciliation_ids or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "JOURNAL ENTRIES"])
    for item in state.journal_entry_ids[:20] or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "HUMAN REVIEW"])
    for item in state.human_review_items or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "RESOLUTIONS"])
    resolutions = load_resolutions(state.period.period)
    if not resolutions:
        lines.append("- (none)")
    for item in resolutions:
        lines.append(f"- {item.item_id}: {item.resolution} ({item.created_at})")
    lines.extend(["", "CONTROL EVENTS"])
    events = load_events(state.period.period)
    if not events:
        lines.append("- (none)")
    for item in events:
        lines.append(f"- {item.event_type} {item.decision} {item.reason}")
    lines.extend(["", "SNAPSHOTS"])
    snapshots = list_snapshots(state.period.period)
    if not snapshots:
        lines.append("- (none)")
    for item in snapshots:
        lines.append(f"- {item.snapshot_id} {item.close_status} {item.close_timestamp}")
    if state.trace_path:
        lines.extend(["", f"Working packet: {state.trace_path}"])
    return "\n".join(lines)


def format_review_queue(items, *, period: str) -> str:
    lines = [f"REVIEW QUEUE — {period}", ""]
    if not items:
        lines.append("No review items.")
        return "\n".join(lines)
    width = max(len(item.review_id) for item in items)
    for item in items:
        amount = f"${item.amount:,.2f}" if item.amount is not None else "—"
        lines.append(
            f"{item.review_id.ljust(width)}  {item.status.ljust(18)}  {item.source_workflow.ljust(8)}  {amount}  {item.description}"
        )
    return "\n".join(lines)


def format_review_item(item) -> str:
    lines = [
        f"REVIEW {item.review_id}",
        f"Period: {item.period}",
        f"Source: {item.source_workflow} / {item.source_case_id}",
        f"Issue: {item.issue_type}",
        f"Status: {item.status}",
        f"Assigned: {item.assigned_role or '—'}",
        f"Amount: {f'${item.amount:,.2f}' if item.amount is not None else '—'}",
        f"Description: {item.description}",
        f"Proposed resolution: {item.proposed_resolution or '—'}",
        f"Decision: {item.decision or '—'}",
        f"Reason: {item.decision_reason or '—'}",
        f"Downstream: {', '.join(item.downstream_tasks_affected) or '—'}",
        f"Evidence: {', '.join(item.evidence_refs) or '—'}",
    ]
    if item.source_object_after:
        lines.append(f"Source object after: {item.source_object_after}")
    return "\n".join(lines)


def format_resolution(item) -> str:
    lines = [
        f"Resolved {item.review_id}" if item.status == "RESOLVED" else f"Updated {item.review_id}",
        f"Status: {item.status}",
        f"Action: {item.resolution_action or item.decision}",
        f"Reason: {item.decision_reason or '—'}",
        "",
        "Underlying source change",
        f"  before: {item.source_object_before or '—'}",
        f"  after:  {item.source_object_after or '—'}",
    ]
    if item.journal_entry_ids:
        lines.append(f"  journals: {', '.join(item.journal_entry_ids)}")
    return "\n".join(lines)


def format_rerun(state) -> str:
    lines = [
        f"TARGETED RERUN — {state.period.period}",
        f"Invalidated: {', '.join(state.invalidated_tasks) or '—'}",
        f"Reran: {', '.join(state.rerun_tasks) or '—'}",
        "",
        format_month_end_status(state),
    ]
    return "\n".join(lines)


def format_finalize(state) -> str:
    gate = state.gate
    verdict = state.final_verdict
    lines = [
        f"FINAL CLOSE REVIEW — {state.period.period}",
        f"Tasks complete: {'PASS' if gate and gate.all_required_tasks_complete else 'FAIL'}",
        f"BS reconciliations SIGNED_OFF: {'PASS' if gate and gate.all_required_bs_recs_signed_off else 'FAIL'}",
        f"Blocking reviews: {'PASS' if gate and gate.no_blocking_reviews else 'FAIL'}",
        f"Evidence completeness: {'PASS' if gate and gate.evidence_complete else 'FAIL'}",
        f"Journal safeguards: {'PASS' if gate and gate.journal_safeguards_pass else 'FAIL'}",
        f"Final reviewer: {verdict.decision if verdict else '—'}",
        f"Approved by: {state.period.approved_by or '—'}",
        "",
        f"Close status: {state.period.status}",
    ]
    if gate and gate.blockers:
        lines.extend(["", "Gate blockers:"] + [f"- {item}" for item in gate.blockers])
    if verdict and verdict.reasons:
        lines.extend(["", "Reviewer reasons:"] + [f"- {item}" for item in verdict.reasons])
    if state.period.status == "CLOSED":
        from close.dates import month_name

        lines.extend(["", f"{month_name(state.period.period).upper()} {state.period.period[:4]}: CLOSED"])
    return "\n".join(lines)


def format_resolve_demo(phase1, resolutions: list, phase3, phase4) -> str:
    from close.dates import month_name

    month = f"{month_name(phase1.period.period).upper()} {phase1.period.period[:4]}"
    lines = [
        "OFFICE OF THE CFO — MONTH-END CLOSE",
        "",
        "PHASE 1 — INITIAL CLOSE",
        "",
        format_month_end_demo(phase1),
        "",
        "PHASE 2 — REVIEW",
        "",
    ]
    for item in resolutions:
        lines.append(format_resolution(item))
        lines.append("")
    lines.extend(
        [
            "PHASE 3 — TARGETED RERUN",
            "",
            format_rerun(phase3),
            "",
            "PHASE 4 — FINAL REVIEW",
            "",
            format_finalize(phase4),
            "",
            f"{month}: {phase4.period.status}",
        ]
    )
    return "\n".join(lines)
