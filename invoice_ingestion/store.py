from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from invoice_ingestion import extract as ingestion_extract
from invoice_ingestion.extract import extract_text, resolve_ingestion_path
from tools import DATA_DIR, all_invoices, all_purchase_orders, normalize_vendor


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return raw


def _in_period(row: dict, period: str) -> bool:
    if not period:
        return True
    return (row.get("period") or "") == period


@lru_cache(maxsize=1)
def list_emails_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "emails.json")


@lru_cache(maxsize=1)
def list_erp_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "erp.json")


@lru_cache(maxsize=1)
def list_procurement_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "procurement.json")


@lru_cache(maxsize=1)
def list_vendor_portals_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "vendor_portals.json")


@lru_cache(maxsize=1)
def list_employee_submissions_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "employee_submissions.json")


@lru_cache(maxsize=1)
def list_documents_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "documents.json")


@lru_cache(maxsize=1)
def list_edi_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "edi_documents.json")


@lru_cache(maxsize=1)
def list_bank_raw() -> list[dict]:
    return _read_json(ingestion_extract.INGESTION_DIR / "bank_transactions.json")


def clear_ingestion_cache() -> None:
    list_emails_raw.cache_clear()
    list_erp_raw.cache_clear()
    list_procurement_raw.cache_clear()
    list_vendor_portals_raw.cache_clear()
    list_employee_submissions_raw.cache_clear()
    list_documents_raw.cache_clear()
    list_edi_raw.cache_clear()
    list_bank_raw.cache_clear()
    known_vendor_names.cache_clear()


def list_emails(period: str = "") -> list[dict]:
    return [row for row in list_emails_raw() if _in_period(row, period)]


def get_email(message_id: str) -> dict | None:
    for row in list_emails_raw():
        if row.get("message_id") == message_id:
            return row
    return None


def get_email_attachment(message_id: str, attachment_id: str) -> dict | None:
    email = get_email(message_id)
    if not email:
        return None
    for attachment in email.get("attachments") or []:
        if attachment.get("attachment_id") == attachment_id:
            return {**attachment, "message_id": message_id}
    return None


def list_erp_invoice_records(period: str = "") -> list[dict]:
    return [row for row in list_erp_raw() if _in_period(row, period)]


def get_erp_invoice(record_id: str) -> dict | None:
    for row in list_erp_raw():
        if row.get("record_id") == record_id:
            return row
    return None


def list_procurement_records(period: str = "") -> list[dict]:
    return [row for row in list_procurement_raw() if _in_period(row, period)]


def get_procurement_record(record_id: str) -> dict | None:
    for row in list_procurement_raw():
        if row.get("record_id") == record_id:
            return row
    return None


def list_vendor_portal_documents(period: str = "", vendor: str = "") -> list[dict]:
    rows = [row for row in list_vendor_portals_raw() if _in_period(row, period)]
    if vendor:
        wanted = normalize_vendor(vendor)
        rows = [row for row in rows if normalize_vendor(str(row.get("vendor") or "")) == wanted]
    return rows


def get_vendor_portal_document(document_id: str) -> dict | None:
    for row in list_vendor_portals_raw():
        if row.get("document_id") == document_id:
            return row
    return None


def list_employee_submissions(period: str = "") -> list[dict]:
    return [row for row in list_employee_submissions_raw() if _in_period(row, period)]


def get_employee_submission(submission_id: str) -> dict | None:
    for row in list_employee_submissions_raw():
        if row.get("submission_id") == submission_id:
            return row
    return None


def list_mail_documents(period: str = "") -> list[dict]:
    return [row for row in list_documents_raw() if _in_period(row, period)]


def get_mail_document(document_id: str) -> dict | None:
    for row in list_documents_raw():
        if row.get("document_id") == document_id:
            return row
    return None


def list_edi_documents(period: str = "") -> list[dict]:
    return [row for row in list_edi_raw() if _in_period(row, period)]


def get_edi_document(document_id: str) -> dict | None:
    for row in list_edi_raw():
        if row.get("document_id") == document_id:
            return row
    return None


def list_bank_transactions(period: str = "") -> list[dict]:
    return [row for row in list_bank_raw() if _in_period(row, period)]


def get_bank_transaction(transaction_id: str) -> dict | None:
    for row in list_bank_raw():
        if row.get("transaction_id") == transaction_id:
            return row
    return None


def load_record_text(record: dict) -> str:
    path = record.get("path")
    if path:
        return extract_text(path)
    if record.get("text"):
        return str(record["text"])
    return ""


def attachment_text(attachment: dict) -> str:
    if attachment.get("text"):
        return str(attachment["text"])
    if attachment.get("path"):
        return extract_text(attachment["path"])
    return ""


@lru_cache(maxsize=1)
def known_vendor_names() -> list[str]:
    names: list[str] = []
    for invoice in all_invoices():
        names.append(invoice.vendor)
    for purchase_order in all_purchase_orders():
        names.append(purchase_order.vendor)
    for extra_name in ("historical_invoices.json", "vendor_contracts.json"):
        extra_path = DATA_DIR / extra_name
        if extra_path.exists():
            for item in _read_json(extra_path):
                if isinstance(item, dict) and item.get("vendor"):
                    names.append(str(item["vendor"]))
    unique: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = normalize_vendor(name)
        if key and key not in seen:
            seen.add(key)
            unique.append(name)
    return unique


def is_known_vendor(name: str | None) -> bool:
    if not name:
        return False
    wanted = normalize_vendor(name)
    return any(normalize_vendor(item) == wanted for item in known_vendor_names())


INVOICE_ID_RE = re.compile(r"\b[A-Z]{2,10}-?[A-Z0-9\-]*\d[A-Z0-9\-]*\b", re.I)
INVOICE_ID_STOP = {"USD", "SEP26"}


def invoice_ids_in(text: str) -> set[str]:
    found: set[str] = set()
    for item in INVOICE_ID_RE.findall(text.upper()):
        if item in INVOICE_ID_STOP or item.isdigit():
            continue
        if not any(ch.isdigit() for ch in item):
            continue
        found.add(item)
    return found


def find_related_invoice_records(transaction: dict) -> list[dict]:
    """Search simulated sources for documents that could support a card charge."""
    memo = str(transaction.get("memo") or "")
    descriptor = str(transaction.get("vendor_descriptor") or "")
    amount = transaction.get("amount")
    needles = invoice_ids_in(memo + " " + descriptor)

    matches: list[dict] = []

    def vendors_overlap(vendor: str) -> bool:
        if not vendor:
            return False
        left = normalize_vendor(vendor)
        right = normalize_vendor(descriptor)
        if not left or not right:
            return False
        return left == right or left in right or right in left

    def consider(source_type: str, source_id: str, vendor: str, number: str, total, uri: str | None, text: str):
        ids = invoice_ids_in(f"{number} {text}")
        number_ok = bool(needles and needles & ids)
        amount_ok = amount is not None and total is not None and abs(float(amount) - float(total)) <= 0.05
        if number_ok or (vendors_overlap(vendor) and amount_ok):
            matches.append(
                {
                    "source_type": source_type,
                    "source_id": source_id,
                    "source_uri": uri,
                    "vendor": vendor,
                    "vendor_invoice_number": number,
                    "amount": total,
                    "text": text,
                }
            )

    for email in list_emails_raw():
        for attachment in email.get("attachments") or []:
            text = attachment_text(attachment)
            consider(
                "email",
                email.get("message_id"),
                "",
                "",
                None,
                email.get("thread_uri"),
                text,
            )

    for row in list_vendor_portals_raw():
        text = load_record_text(row)
        consider(
            "vendor_portal",
            row.get("document_id"),
            str(row.get("vendor") or ""),
            "",
            None,
            row.get("source_uri"),
            text,
        )

    for row in list_erp_raw():
        consider(
            "erp",
            row.get("record_id"),
            str(row.get("vendor_name") or ""),
            str(row.get("invoice_number") or ""),
            row.get("total"),
            f"erp://{row.get('system')}/{row.get('record_id')}",
            json.dumps(row),
        )

    for row in list_documents_raw():
        text = load_record_text(row)
        consider(
            "document",
            row.get("document_id"),
            "",
            "",
            None,
            None,
            text,
        )

    for row in list_edi_raw():
        payload = json.dumps(row)
        consider(
            "edi",
            row.get("document_id"),
            str(((row.get("payload") or {}).get("N1") or {}).get("name") or ""),
            str(((row.get("payload") or {}).get("BIG") or {}).get("invoice_number") or ""),
            None,
            row.get("source_uri"),
            payload,
        )

    # De-dupe by source_type+source_id while preserving order.
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for item in matches:
        key = (str(item.get("source_type")), str(item.get("source_id")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def file_exists(path: str) -> bool:
    return resolve_ingestion_path(path).exists()
