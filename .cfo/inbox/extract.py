"""Extract invoice candidates from inbox messages using the existing parser."""

from __future__ import annotations

from invoice_ingestion.extract import UnreadableDocument, UnsupportedFileType, document_hash, extract_text
from invoice_ingestion.interpret import parse_invoice_text_clean
from invoice_ingestion.models import InvoiceCandidate

from inbox.models import MessageAttachment, MessageEnvelope
from inbox.normalize import normalize_currency, normalize_invoice_number, normalize_po, resolve_vendor
from inbox.security import attachment_is_unsupported


class AttachmentParseError(Exception):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def hash_attachment(attachment: MessageAttachment) -> str:
    if attachment.sha256:
        return attachment.sha256
    if attachment.content:
        return document_hash(attachment.content)
    if attachment.path:
        try:
            return document_hash(extract_text(attachment.path))
        except (UnreadableDocument, UnsupportedFileType, OSError):
            return document_hash(f"{attachment.filename}:{attachment.mime_type}")
    return document_hash(f"{attachment.filename}:{attachment.mime_type}")


def attachment_text(attachment: MessageAttachment) -> str:
    if attachment_is_unsupported(attachment.filename, attachment.mime_type):
        raise AttachmentParseError("UNSUPPORTED_ATTACHMENT", f"Unsupported attachment {attachment.filename}")
    if attachment.content is not None:
        return attachment.content
    if attachment.path:
        try:
            return extract_text(attachment.path)
        except UnsupportedFileType as exc:
            raise AttachmentParseError("UNSUPPORTED_ATTACHMENT", str(exc)) from exc
        except UnreadableDocument as exc:
            raise AttachmentParseError("PARSE_FAILURE", str(exc)) from exc
    raise AttachmentParseError("PARSE_FAILURE", f"No content for attachment {attachment.filename}")


def stamp_hashes(message: MessageEnvelope) -> MessageEnvelope:
    attachments = []
    for item in message.attachments:
        attachments.append(item.model_copy(update={"sha256": hash_attachment(item)}))
    return message.model_copy(update={"attachments": attachments})


def _candidate_from_text(
    text: str,
    message: MessageEnvelope,
    *,
    document_path: str | None,
    extra: dict,
) -> InvoiceCandidate:
    vendor_hint = message.sender_name if message.sender_name else None
    parsed = parse_invoice_text_clean(
        text=text,
        source_type="email",
        source_id=message.message_id,
        source_uri=f"inbox://{message.thread_id}/{message.message_id}",
        vendor_hint=vendor_hint,
        document_path=document_path,
        extra_context={
            "from": message.sender_address,
            "sender_name": message.sender_name,
            "subject": message.subject,
            "thread_id": message.thread_id,
            "source": "inbox",
            **extra,
        },
    )
    vendor, known = resolve_vendor(parsed.vendor)
    return parsed.model_copy(
        update={
            "vendor": vendor,
            "vendor_id": vendor if known else parsed.vendor_id,
            "vendor_invoice_number": normalize_invoice_number(parsed.vendor_invoice_number),
            "po_id": normalize_po(parsed.po_id),
            "currency": normalize_currency(parsed.currency, text=text) or parsed.currency,
            "document_hash": parsed.document_hash or (document_hash(text) if text.strip() else None),
        }
    )


def extract_invoice_candidates(message: MessageEnvelope) -> tuple[list[InvoiceCandidate], list[str]]:
    """Return invoice-classified candidates and parse reason codes."""
    errors: list[str] = []
    candidates: list[InvoiceCandidate] = []
    for attachment in message.attachments:
        try:
            text = attachment_text(attachment)
        except AttachmentParseError as exc:
            errors.append(exc.reason_code)
            continue
        parsed = _candidate_from_text(
            text,
            message,
            document_path=attachment.path or attachment.filename,
            extra={"attachment_id": attachment.filename, "filename": attachment.filename},
        )
        if parsed.classification == "invoice":
            candidates.append(parsed)
    if not candidates:
        body = message.body_text or ""
        if body.strip():
            parsed = _candidate_from_text(
                f"{message.subject}\n{body}",
                message,
                document_path=None,
                extra={"origin": "body"},
            )
            if parsed.classification == "invoice":
                candidates.append(parsed)
    return candidates, list(dict.fromkeys(errors))


def combined_thread_text(messages: list[MessageEnvelope]) -> str:
    chunks: list[str] = []
    for item in messages:
        chunks.append(item.subject)
        chunks.append(item.body_text)
        for attachment in item.attachments:
            try:
                chunks.append(attachment_text(attachment))
            except AttachmentParseError:
                continue
    return "\n".join(chunk for chunk in chunks if chunk)
