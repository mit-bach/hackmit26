"""Print a concise inbox handoff sequence."""

from __future__ import annotations

from inbox.fixtures import demo_specs, full_inbox_specs, spec_incomplete_reply
from inbox.models import InboxHandoffResult
from inbox.store import configure_runs_dir, created_invoice_ids, load_state, persist_state
from inbox.workflow import handoff, handoff_reply


def format_handoff(result: InboxHandoffResult) -> str:
    classification = result.receiver.classification
    dispatch = result.receiver.dispatch
    extracted = []
    if classification.invoice_number:
        extracted.append(f"invoice={classification.invoice_number}")
    if classification.counterparty_name:
        extracted.append(f"vendor={classification.counterparty_name}")
    if classification.amount_cents is not None:
        extracted.append(f"amount_cents={classification.amount_cents}")
    if classification.po_number:
        extracted.append(f"po={classification.po_number}")
    lines = [
        f"Sender: {result.sender.agent}  run={result.sender.run_id}  sent {result.sender.message_id}",
        f"Receiver: {result.receiver.agent}  run={result.receiver.run_id}",
        f"Classification: {classification.classification}  action={classification.selected_action}",
        f"Extracted: {', '.join(extracted) or '(none)'}",
        f"Duplicate/validation: {result.trace.duplicate_check or 'none'}  "
        f"errors={dispatch.validation_errors or []}",
        f"Canonical invoice: {dispatch.invoice_id or '(none)'}",
        f"Three-way match: {dispatch.match_status or 'n/a'}  exceptions={dispatch.match_exceptions or []}",
        f"Final status: {result.final_status}  reasons={dispatch.reason_codes}",
        f"Trace: {result.trace.trace_path or result.trace.trace_id}",
    ]
    if result.replayed:
        lines.append("Idempotent replay: yes — no second payable created")
    return "\n".join(lines)


def run_demo_inbox(
    *,
    full: bool = False,
    reset: bool = False,
    persist: bool = True,
) -> list[InboxHandoffResult]:
    if reset:
        from invoice_ingestion.adapter import reset_ingested_invoices
        from inbox.store import reset_inbox_state
        from tools import reset_runtime_invoices

        reset_inbox_state()
        reset_ingested_invoices()
        reset_runtime_invoices()
    elif persist:
        load_state()

    specs = full_inbox_specs() if full else demo_specs()
    results: list[InboxHandoffResult] = []
    for spec in specs:
        results.append(handoff(spec, persist=persist))
        if spec.case_id == "incomplete":
            results.append(
                handoff_reply(
                    spec.thread_id,
                    spec.message_id,
                    spec_incomplete_reply().message_id,
                    spec_incomplete_reply().body_text,
                    persist=persist,
                )
            )
    if persist:
        persist_state()
    return results


def format_demo(results: list[InboxHandoffResult]) -> str:
    blocks = ["Finance Inbox Demo", ""]
    for index, result in enumerate(results, start=1):
        blocks.append(f"[{index}] {result.sender.message_id}")
        blocks.append(format_handoff(result))
        blocks.append("")
    blocks.append(f"Inbox-created AP invoices: {', '.join(created_invoice_ids()) or '(none)'}")
    replayed = sum(1 for item in results if item.replayed)
    if replayed:
        blocks.append(f"Replayed deliveries: {replayed}")
    return "\n".join(blocks).rstrip() + "\n"
