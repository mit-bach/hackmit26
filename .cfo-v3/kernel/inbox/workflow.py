"""Counterparty → transport → Finance Inbox → dispatch → AP/trace."""

from __future__ import annotations

from datetime import datetime, timezone

from invoice_ingestion.extract import document_hash

from inbox.agents import run_counterparty_agent, run_counterparty_reply, run_inbox_agent
from inbox.extract import combined_thread_text
from inbox.models import (
    COUNTERPARTY_AGENT,
    FINANCE_INBOX_AGENT,
    CounterpartyAgentOutput,
    InboxAttempt,
    InboxHandoffResult,
    InboxTrace,
    MessageEnvelope,
    MessageSpec,
    ToolCallTrace,
)
from inbox.store import persist_state, remember_trace
from inbox.transport import (
    all_outcomes,
    deliver,
    get_message,
    list_thread,
    message_lock,
    prior_outcome,
    remember_outcome,
    replace_message,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trace_id(message_id: str) -> str:
    return f"INBOX-{message_id}"


def _attachment_hashes(message: MessageEnvelope) -> list[str]:
    return [item.sha256 or document_hash(item.filename) for item in message.attachments]


def _build_trace(
    sender,
    receiver,
    message: MessageEnvelope,
    *,
    replayed: bool,
    prior_attempts: list[InboxAttempt] | None = None,
) -> InboxTrace:
    dispatch = receiver.dispatch
    classification = receiver.classification
    attempt = InboxAttempt(
        attempt=len(prior_attempts or []) + 1,
        message_id=message.message_id,
        classification=classification,
        dispatch=dispatch,
        status=dispatch.status,
        reason_codes=list(dispatch.reason_codes),
        timestamp=_now(),
    )
    attempts = list(prior_attempts or []) + [attempt]
    extracted = {
        "vendor": classification.counterparty_name,
        "invoice_number": classification.invoice_number,
        "po_number": classification.po_number,
        "amount_cents": classification.amount_cents,
        "currency": classification.currency,
        "invoice_date": classification.invoice_date,
        "due_date": classification.due_date,
    }
    duplicate = None
    if dispatch.status == "DUPLICATE_DELIVERY":
        duplicate = "transport"
    elif dispatch.status == "BUSINESS_DUPLICATE":
        duplicate = "business"
    elif dispatch.duplicate_of:
        duplicate = f"linked:{dispatch.duplicate_of}"
    return InboxTrace(
        trace_id=_trace_id(message.message_id),
        sender_agent=COUNTERPARTY_AGENT,
        receiver_agent=FINANCE_INBOX_AGENT,
        sender_run_id=sender.run_id if sender else None,
        receiver_run_id=receiver.run_id,
        message_id=message.message_id,
        thread_id=message.thread_id,
        attachment_hashes=_attachment_hashes(message),
        classification=classification,
        selected_action=classification.selected_action,
        extracted_fields=extracted,
        validation_errors=dispatch.validation_errors,
        validation_warnings=dispatch.validation_warnings,
        duplicate_check=duplicate,
        called_workflow=dispatch.called_workflow,
        record_ids=dispatch.record_ids,
        invoice_id=dispatch.invoice_id,
        match_status=dispatch.match_status,
        final_status=dispatch.status,
        reason_codes=list(dict.fromkeys(list(dispatch.reason_codes) + list(classification.reason_codes))),
        decision_summary=classification.rationale,
        attempts=attempts,
        tool_calls=[
            ToolCallTrace(
                agent=COUNTERPARTY_AGENT,
                tool="send_inbox_message",
                input_summary=message.message_id,
                output_summary="delivered",
                timestamp=message.sent_at,
            ),
            ToolCallTrace(
                agent=FINANCE_INBOX_AGENT,
                tool="classify_inbox_message",
                input_summary=message.message_id,
                output_summary=classification.classification,
                timestamp=_now(),
            ),
            ToolCallTrace(
                agent=FINANCE_INBOX_AGENT,
                tool="dispatch_inbox_action",
                input_summary=classification.selected_action,
                output_summary=dispatch.status,
                timestamp=_now(),
            ),
        ],
        timestamps={"received_at": message.received_at, "processed_at": _now()},
    )


def _thread_attempts(thread_id: str) -> list[InboxAttempt]:
    attempts: list[InboxAttempt] = []
    for result in all_outcomes().values():
        if result.trace.thread_id == thread_id:
            attempts.extend(result.trace.attempts)
    return attempts


def process_message(
    message_id: str,
    *,
    sender=None,
    persist: bool = True,
) -> InboxHandoffResult:
    with message_lock(message_id):
        prior = prior_outcome(message_id)
        if prior is not None:
            replayed = prior.model_copy(deep=True)
            replayed.replayed = True
            replayed.final_status = "DUPLICATE_DELIVERY"
            replayed.receiver = replayed.receiver.model_copy(
                update={
                    "replayed": True,
                    "dispatch": replayed.receiver.dispatch.model_copy(
                        update={
                            "status": "DUPLICATE_DELIVERY",
                            "reason_codes": list(
                                dict.fromkeys(
                                    [*replayed.receiver.dispatch.reason_codes, "TRANSPORT_IDEMPOTENT"]
                                )
                            ),
                            "mutation": False,
                        }
                    ),
                }
            )
            replayed.trace = replayed.trace.model_copy(
                update={
                    "final_status": "DUPLICATE_DELIVERY",
                    "duplicate_check": "transport",
                    "reason_codes": list(dict.fromkeys([*replayed.trace.reason_codes, "TRANSPORT_IDEMPOTENT"])),
                }
            )
            return replayed

        message = get_message(message_id)
        if message is None:
            raise KeyError(f"Inbox message {message_id} was not found")

        thread = list_thread(message.thread_id)
        if len(thread) > 1:
            combined = combined_thread_text(thread)
            message = replace_message(
                message.model_copy(update={"body_text": combined, "subject": thread[0].subject})
            )

        receiver = run_inbox_agent(message_id)
        sender_output = sender or CounterpartyAgentOutput(
            run_id=f"RUN-CP-{message_id}",
            message_id=message_id,
            thread_id=message.thread_id,
            sent=True,
            status="ALREADY_DELIVERED",
        )
        prior_attempts = _thread_attempts(message.thread_id)
        trace = _build_trace(
            sender_output, receiver, message, replayed=False, prior_attempts=prior_attempts
        )
        if persist:
            remember_trace(trace)
        result = InboxHandoffResult(
            sender=sender_output,
            receiver=receiver,
            trace=trace,
            invoice_id=receiver.dispatch.invoice_id,
            final_status=receiver.dispatch.status,
        )
        remember_outcome(message_id, result)
        if persist:
            persist_state()
        return result


def handoff(spec: MessageSpec, *, persist: bool = True) -> InboxHandoffResult:
    """Real two-agent handoff: sender delivers, receiver classifies and dispatches."""
    sender = run_counterparty_agent(spec)
    return process_message(sender.message_id, sender=sender, persist=persist)


def handoff_reply(
    thread_id: str,
    in_reply_to: str,
    message_id: str,
    body_text: str,
    *,
    persist: bool = True,
) -> InboxHandoffResult:
    sender = run_counterparty_reply(thread_id, in_reply_to, message_id, body_text)
    return process_message(sender.message_id, sender=sender, persist=persist)


def receive_raw(message: MessageEnvelope, *, persist: bool = True) -> InboxHandoffResult:
    stored = deliver(message)
    return process_message(stored.message_id, persist=persist)
