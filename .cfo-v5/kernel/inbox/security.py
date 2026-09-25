"""Treat every message body and attachment as untrusted data."""

from __future__ import annotations

import re

from inbox.models import MessageEnvelope

INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?(?:your|previous|prior|the)\s+(?:rules|instructions|policy)", re.I),
    re.compile(r"disregard\s+(?:your|previous|all)\s+(?:rules|instructions)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"override\s+(?:your\s+)?(?:rules|policy|instructions|permissions)", re.I),
    re.compile(r"mark\s+(?:this|the)?\s*(?:invoice\s+)?(?:as\s+)?(?:approved|paid|matched)", re.I),
    re.compile(r"(?:self-?approve|auto-?approve|force\s+approve)", re.I),
    re.compile(r"change\s+(?:the\s+)?bank\s+account", re.I),
    re.compile(r"update\s+(?:the\s+)?(?:wire|ach|bank)\s+(?:instructions|details|account)", re.I),
    re.compile(r"bypass\s+(?:controls|matching|policy|approval)", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"jailbreak", re.I),
)

UNSAFE_MUTATION_PATTERNS = (
    re.compile(r"mark\s+(?:this|the)?\s*(?:invoice\s+)?(?:as\s+)?(?:approved|paid)", re.I),
    re.compile(r"change\s+(?:the\s+)?bank\s+account", re.I),
    re.compile(r"update\s+(?:the\s+)?(?:wire|ach|bank)\s+(?:instructions|details|account)", re.I),
    re.compile(r"bypass\s+(?:controls|matching|policy|approval)", re.I),
    re.compile(r"(?:self-?approve|force\s+approve)", re.I),
)

UNSAFE_MIME = {
    "application/octet-stream",
    "application/x-msdownload",
    "application/x-executable",
    "application/x-dosexec",
    "application/javascript",
}

UNSAFE_SUFFIXES = {".exe", ".bin", ".dll", ".bat", ".cmd", ".sh", ".js"}


def message_blob(message: MessageEnvelope) -> str:
    parts = [message.subject, message.body_text, message.body_html or ""]
    for attachment in message.attachments:
        parts.append(attachment.filename)
        if attachment.content:
            parts.append(attachment.content)
    return "\n".join(part for part in parts if part)


def injection_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text or ""):
            hits.append(pattern.pattern)
    return hits


def has_prompt_injection(message: MessageEnvelope) -> bool:
    return bool(injection_hits(message_blob(message)))


def has_unsafe_mutation_request(message: MessageEnvelope) -> bool:
    blob = message_blob(message)
    return any(pattern.search(blob) for pattern in UNSAFE_MUTATION_PATTERNS)


def attachment_is_unsupported(filename: str, mime_type: str) -> bool:
    name = (filename or "").lower()
    mime = (mime_type or "").lower()
    if mime in UNSAFE_MIME:
        return True
    return any(name.endswith(suffix) for suffix in UNSAFE_SUFFIXES)


def security_reason_codes(message: MessageEnvelope) -> list[str]:
    codes: list[str] = []
    if has_prompt_injection(message):
        codes.append("PROMPT_INJECTION")
    if has_unsafe_mutation_request(message):
        codes.append("UNSAFE_INSTRUCTION_IGNORED")
    for attachment in message.attachments:
        if attachment_is_unsupported(attachment.filename, attachment.mime_type):
            codes.append("UNSUPPORTED_ATTACHMENT")
            break
    return list(dict.fromkeys(codes))
