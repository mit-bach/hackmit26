from __future__ import annotations

from agents import function_tool

from invoice_ingestion import store as source_data
from invoice_ingestion.edi import parse_edi_document
from invoice_ingestion.extract import document_hash, page_refs_from_text


def _not_found(kind: str, ident: str) -> dict:
    return {
        "found": False,
        "error": f"{kind} {ident} was not found. Do not invent {kind.lower()} data.",
    }


@function_tool
def list_email_candidates(period: str = "2026-09") -> dict:
    """List AP-inbox emails for a period. Returns ids, senders, and subjects only."""
    rows = source_data.list_emails(period)
    return {
        "found": True,
        "period": period,
        "count": len(rows),
        "emails": [
            {
                "message_id": row.get("message_id"),
                "from": row.get("from"),
                "subject": row.get("subject"),
                "sent_at": row.get("sent_at"),
                "attachment_count": len(row.get("attachments") or []),
            }
            for row in rows
        ],
    }


@function_tool
def get_email(message_id: str) -> dict:
    """Load one email: headers, body, and attachment metadata. Not the attachment bytes."""
    row = source_data.get_email(message_id)
    if row is None:
        return _not_found("Email", message_id)
    attachments = [
        {
            "attachment_id": item.get("attachment_id"),
            "filename": item.get("filename"),
            "content_type": item.get("content_type"),
        }
        for item in row.get("attachments") or []
    ]
    return {
        "found": True,
        "email": {
            "message_id": row.get("message_id"),
            "from": row.get("from"),
            "to": row.get("to"),
            "subject": row.get("subject"),
            "sent_at": row.get("sent_at"),
            "body": row.get("body"),
            "thread_uri": row.get("thread_uri"),
            "attachments": attachments,
        },
    }


@function_tool
def get_email_attachment(message_id: str, attachment_id: str) -> dict:
    """Extract text from one email attachment. Use this instead of guessing PDF contents."""
    attachment = source_data.get_email_attachment(message_id, attachment_id)
    if attachment is None:
        return _not_found("Attachment", attachment_id)
    text = source_data.attachment_text(attachment)
    return {
        "found": True,
        "message_id": message_id,
        "attachment_id": attachment_id,
        "filename": attachment.get("filename"),
        "text": text,
        "document_hash": document_hash(text) if text.strip() else None,
        "page_refs": page_refs_from_text(text) if text.strip() else [],
    }


@function_tool
def list_erp_invoice_records(period: str = "2026-09") -> dict:
    """List ERP/AP invoice records (NetSuite, SAP, Oracle, Workday mocks)."""
    rows = source_data.list_erp_invoice_records(period)
    return {
        "found": True,
        "count": len(rows),
        "records": [
            {
                "record_id": row.get("record_id"),
                "system": row.get("system"),
                "vendor_name": row.get("vendor_name"),
                "invoice_number": row.get("invoice_number"),
            }
            for row in rows
        ],
    }


@function_tool
def get_erp_invoice(record_id: str) -> dict:
    """Load one ERP invoice record. Map fields; do not approve payment."""
    row = source_data.get_erp_invoice(record_id)
    if row is None:
        return _not_found("ERP record", record_id)
    return {"found": True, "record": row}


@function_tool
def list_procurement_records(period: str = "2026-09") -> dict:
    """List Coupa/Ariba/Zip-style procurement documents."""
    rows = source_data.list_procurement_records(period)
    return {
        "found": True,
        "count": len(rows),
        "records": [
            {
                "record_id": row.get("record_id"),
                "system": row.get("system"),
                "document_type": row.get("document_type"),
                "vendor_name": row.get("vendor_name"),
            }
            for row in rows
        ],
    }


@function_tool
def get_procurement_record(record_id: str) -> dict:
    """Load one procurement document, including PO and receiving context if present."""
    row = source_data.get_procurement_record(record_id)
    if row is None:
        return _not_found("Procurement record", record_id)
    return {"found": True, "record": row}


@function_tool
def list_vendor_portal_documents(period: str = "2026-09", vendor: str = "") -> dict:
    """List documents available on mocked vendor billing portals."""
    rows = source_data.list_vendor_portal_documents(period, vendor=vendor)
    return {
        "found": True,
        "count": len(rows),
        "documents": [
            {
                "document_id": row.get("document_id"),
                "portal": row.get("portal"),
                "vendor": row.get("vendor"),
                "document_type": row.get("document_type"),
                "filename": row.get("filename"),
            }
            for row in rows
        ],
    }


@function_tool
def get_vendor_portal_document(document_id: str) -> dict:
    """Load one vendor-portal document and its extracted text."""
    row = source_data.get_vendor_portal_document(document_id)
    if row is None:
        return _not_found("Vendor portal document", document_id)
    text = source_data.load_record_text(row)
    return {
        "found": True,
        "document": {
            **{key: value for key, value in row.items() if key != "path"},
            "text": text,
            "document_hash": document_hash(text) if text.strip() else None,
        },
    }


@function_tool
def list_employee_submissions(period: str = "2026-09") -> dict:
    """List employee-submitted files and notes."""
    rows = source_data.list_employee_submissions(period)
    return {
        "found": True,
        "count": len(rows),
        "submissions": [
            {
                "submission_id": row.get("submission_id"),
                "submitted_by": row.get("submitted_by"),
                "channel": row.get("channel"),
                "filename": row.get("filename"),
                "note": row.get("note"),
            }
            for row in rows
        ],
    }


@function_tool
def get_employee_submission(submission_id: str) -> dict:
    """Load one employee submission and extracted document text."""
    row = source_data.get_employee_submission(submission_id)
    if row is None:
        return _not_found("Employee submission", submission_id)
    text = source_data.load_record_text(row)
    return {
        "found": True,
        "submission": {
            **{key: value for key, value in row.items() if key != "path"},
            "text": text,
            "document_hash": document_hash(text) if text.strip() else None,
        },
    }


@function_tool
def list_mail_documents(period: str = "2026-09") -> dict:
    """List scanned mailroom / physical documents."""
    rows = source_data.list_mail_documents(period)
    return {
        "found": True,
        "count": len(rows),
        "documents": [
            {
                "document_id": row.get("document_id"),
                "filename": row.get("filename"),
                "origin": row.get("origin"),
            }
            for row in rows
        ],
    }


@function_tool
def get_mail_document(document_id: str) -> dict:
    """Load extracted text for one scanned document, including page markers."""
    row = source_data.get_mail_document(document_id)
    if row is None:
        return _not_found("Document", document_id)
    text = source_data.load_record_text(row)
    return {
        "found": True,
        "document": {
            **{key: value for key, value in row.items() if key != "path"},
            "text": text,
            "document_hash": document_hash(text) if text.strip() else None,
            "page_refs": page_refs_from_text(text) if text.strip() else [],
        },
    }


@function_tool
def list_edi_documents(period: str = "2026-09") -> dict:
    """List structured EDI/XML/JSON invoice documents."""
    rows = source_data.list_edi_documents(period)
    return {
        "found": True,
        "count": len(rows),
        "documents": [
            {
                "document_id": row.get("document_id"),
                "format": row.get("format"),
            }
            for row in rows
        ],
    }


@function_tool
def get_edi_document(document_id: str) -> dict:
    """Load one EDI document. Prefer the Python parse; only remap if a field is ambiguous."""
    row = source_data.get_edi_document(document_id)
    if row is None:
        return _not_found("EDI document", document_id)
    try:
        parsed = parse_edi_document(row)
        parsed_dump = parsed.model_dump(mode="json")
        parse_error = None
    except Exception as exc:
        parsed_dump = None
        parse_error = str(exc)
    return {
        "found": True,
        "document": row,
        "python_parse": parsed_dump,
        "python_parse_error": parse_error,
    }


@function_tool
def list_bank_transactions(period: str = "2026-09") -> dict:
    """List corporate-card / bank transactions. A charge is not an invoice."""
    rows = source_data.list_bank_transactions(period)
    return {
        "found": True,
        "count": len(rows),
        "transactions": [
            {
                "transaction_id": row.get("transaction_id"),
                "posted_date": row.get("posted_date"),
                "vendor_descriptor": row.get("vendor_descriptor"),
                "amount": row.get("amount"),
                "memo": row.get("memo"),
            }
            for row in rows
        ],
    }


@function_tool
def get_bank_transaction(transaction_id: str) -> dict:
    """Load one bank or card transaction."""
    row = source_data.get_bank_transaction(transaction_id)
    if row is None:
        return _not_found("Transaction", transaction_id)
    return {"found": True, "transaction": row}


@function_tool
def find_related_invoice(transaction_id: str) -> dict:
    """Search other simulated sources for invoice documentation matching this charge."""
    row = source_data.get_bank_transaction(transaction_id)
    if row is None:
        return _not_found("Transaction", transaction_id)
    matches = source_data.find_related_invoice_records(row)
    return {
        "found": True,
        "transaction_id": transaction_id,
        "match_count": len(matches),
        "matches": [
            {
                "source_type": item.get("source_type"),
                "source_id": item.get("source_id"),
                "source_uri": item.get("source_uri"),
                "vendor": item.get("vendor"),
                "vendor_invoice_number": item.get("vendor_invoice_number"),
                "amount": item.get("amount"),
                "excerpt": (item.get("text") or "")[:800],
            }
            for item in matches
        ],
    }
