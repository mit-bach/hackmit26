"""In-process inbox transport with message-id idempotency and locks."""

from __future__ import annotations

import threading
from collections import defaultdict

from inbox.extract import stamp_hashes
from inbox.models import InboxHandoffResult, MessageEnvelope

_mailbox: dict[str, MessageEnvelope] = {}
_threads: dict[str, list[str]] = defaultdict(list)
_outcomes: dict[str, InboxHandoffResult] = {}
_message_locks: dict[str, threading.Lock] = {}
_invoice_locks: dict[str, threading.Lock] = {}
_registry_lock = threading.RLock()


def reset_transport() -> None:
    with _registry_lock:
        _mailbox.clear()
        _threads.clear()
        _outcomes.clear()
        _message_locks.clear()
        _invoice_locks.clear()


def message_lock(message_id: str) -> threading.Lock:
    with _registry_lock:
        lock = _message_locks.get(message_id)
        if lock is None:
            lock = threading.Lock()
            _message_locks[message_id] = lock
        return lock


def invoice_lock(key: str) -> threading.Lock:
    with _registry_lock:
        lock = _invoice_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _invoice_locks[key] = lock
        return lock


def deliver(message: MessageEnvelope) -> MessageEnvelope:
    """Accept a message into the mailbox. Same message_id is a no-op."""
    stamped = stamp_hashes(message)
    with message_lock(stamped.message_id):
        existing = _mailbox.get(stamped.message_id)
        if existing is not None:
            return existing
        _mailbox[stamped.message_id] = stamped
        thread = _threads[stamped.thread_id]
        if stamped.message_id not in thread:
            thread.append(stamped.message_id)
        return stamped


def replace_message(message: MessageEnvelope) -> MessageEnvelope:
    stamped = stamp_hashes(message)
    _mailbox[stamped.message_id] = stamped
    thread = _threads[stamped.thread_id]
    if stamped.message_id not in thread:
        thread.append(stamped.message_id)
    return stamped


def get_message(message_id: str) -> MessageEnvelope | None:
    return _mailbox.get(message_id)


def list_thread(thread_id: str) -> list[MessageEnvelope]:
    return [_mailbox[mid] for mid in _threads.get(thread_id, []) if mid in _mailbox]


def all_messages() -> list[MessageEnvelope]:
    return list(_mailbox.values())


def all_thread_ids() -> list[str]:
    return list(_threads.keys())


def remember_outcome(message_id: str, result: InboxHandoffResult) -> InboxHandoffResult:
    _outcomes[message_id] = result
    return result


def prior_outcome(message_id: str) -> InboxHandoffResult | None:
    return _outcomes.get(message_id)


def all_outcomes() -> dict[str, InboxHandoffResult]:
    return dict(_outcomes)


def restore_mailbox(messages: list[MessageEnvelope], outcomes: dict[str, InboxHandoffResult] | None = None) -> None:
    reset_transport()
    for message in messages:
        deliver(message)
    if outcomes:
        _outcomes.update(outcomes)
