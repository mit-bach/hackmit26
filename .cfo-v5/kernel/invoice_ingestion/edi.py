"""Deterministic parsers for EDI 810-like JSON, UBL-style XML, and structured JSON."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from invoice_ingestion.extract import document_hash
from invoice_ingestion.models import InvoiceCandidate, InvoiceEvidence, InvoiceLineItem


class EDIParseError(Exception):
    pass


def _cents_to_amount(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EDIParseError(f"Non-numeric EDI amount: {value!r}") from exc
    return round(number / 100.0, 2)


def _money(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        value = cleaned
    try:
        return round(float(value), 2)
    except (TypeError, ValueError) as exc:
        raise EDIParseError(f"Non-numeric amount: {value!r}") from exc


def _evidence(field: str, source: str, value) -> InvoiceEvidence:
    return InvoiceEvidence(field=field, source=source, value=value, text=None if value is None else str(value))


def parse_edi_810_json(payload: dict, *, source_id: str, source_uri: str | None = None) -> InvoiceCandidate:
    big = payload.get("BIG") or {}
    party = payload.get("N1") or {}
    lines = payload.get("IT1") or []
    totals = payload.get("TDS") or {}
    currency = payload.get("CUR") or payload.get("currency") or "USD"

    line_items: list[InvoiceLineItem] = []
    for row in lines:
        amount = _cents_to_amount(row.get("amount_cents"))
        if amount is None:
            amount = _money(row.get("amount"))
        unit_price = _cents_to_amount(row.get("unit_price_cents"))
        if unit_price is None:
            unit_price = _money(row.get("unit_price"))
        qty = row.get("quantity")
        line_items.append(
            InvoiceLineItem(
                description=str(row.get("description") or ""),
                quantity=float(qty) if qty is not None else None,
                unit_price=unit_price,
                amount=amount,
            )
        )

    total = _cents_to_amount(totals.get("total_cents"))
    if total is None:
        total = _money(totals.get("total") or payload.get("total"))
    subtotal = _cents_to_amount(totals.get("subtotal_cents"))
    if subtotal is None:
        subtotal = _money(totals.get("subtotal"))
    tax = _cents_to_amount(totals.get("tax_cents"))
    if tax is None:
        tax = _money(totals.get("tax"))

    vendor = party.get("name") or payload.get("vendor")
    invoice_number = big.get("invoice_number") or payload.get("invoice_number")
    invoice_date = big.get("invoice_date") or payload.get("invoice_date")
    due_date = big.get("due_date") or payload.get("due_date")
    po_id = big.get("po_number") or payload.get("po_number") or payload.get("po_id")

    evidence = [
        _evidence("vendor", "edi.N1.name", vendor),
        _evidence("vendor_invoice_number", "edi.BIG.invoice_number", invoice_number),
        _evidence("invoice_date", "edi.BIG.invoice_date", invoice_date),
        _evidence("amount", "edi.TDS.total", total),
    ]
    raw = json.dumps(payload, sort_keys=True)
    return InvoiceCandidate(
        source_type="edi",
        source_id=source_id,
        source_uri=source_uri,
        vendor=vendor,
        vendor_id=party.get("id"),
        vendor_invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        currency=currency,
        subtotal=subtotal,
        tax=tax,
        amount=total,
        po_id=po_id,
        line_items=line_items,
        document_hash=document_hash(raw),
        extraction_confidence=0.99,
        evidence=evidence,
        classification="invoice",
        classification_reason="Structured EDI 810-like record parsed in Python",
        source_context={"format": "edi_810_json"},
    )


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_ubl_xml(xml_text: str, *, source_id: str, source_uri: str | None = None) -> InvoiceCandidate:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise EDIParseError(f"Invalid XML: {exc}") from exc

    values: dict[str, str] = {}
    line_items: list[InvoiceLineItem] = []
    for node in root.iter():
        name = _local(node.tag)
        text = (node.text or "").strip()
        if not text:
            continue
        if name in {
            "ID",
            "IssueDate",
            "DueDate",
            "PayableAmount",
            "TaxExclusiveAmount",
            "TaxAmount",
            "DocumentCurrencyCode",
            "RegistrationName",
            "Name",
        }:
            values.setdefault(name, text)

    for node in root.iter():
        if _local(node.tag) != "InvoiceLine":
            continue
        line_desc = ""
        line_amount = None
        qty = None
        for child in node.iter():
            child_name = _local(child.tag)
            child_text = (child.text or "").strip()
            if child_name in {"Description", "Name"} and child_text:
                line_desc = child_text
            if child_name == "LineExtensionAmount" and child_text:
                line_amount = _money(child_text)
            if child_name == "InvoicedQuantity" and child_text:
                qty = _money(child_text)
        line_items.append(InvoiceLineItem(description=line_desc, quantity=qty, amount=line_amount))

    vendor = values.get("RegistrationName") or values.get("Name")
    invoice_number = values.get("ID")
    amount = _money(values.get("PayableAmount"))
    candidate = InvoiceCandidate(
        source_type="edi",
        source_id=source_id,
        source_uri=source_uri,
        vendor=vendor,
        vendor_invoice_number=invoice_number,
        invoice_date=values.get("IssueDate"),
        due_date=values.get("DueDate"),
        currency=values.get("DocumentCurrencyCode") or "USD",
        subtotal=_money(values.get("TaxExclusiveAmount")),
        tax=_money(values.get("TaxAmount")),
        amount=amount,
        line_items=line_items,
        document_hash=document_hash(xml_text),
        extraction_confidence=0.95,
        evidence=[
            _evidence("vendor", "ubl.RegistrationName", vendor),
            _evidence("vendor_invoice_number", "ubl.ID", invoice_number),
            _evidence("amount", "ubl.PayableAmount", amount),
        ],
        classification="invoice",
        classification_reason="UBL-style XML invoice parsed in Python",
        source_context={"format": "ubl_xml"},
    )
    return candidate


def parse_structured_json(payload: dict, *, source_id: str, source_uri: str | None = None) -> InvoiceCandidate:
    lines = []
    for row in payload.get("line_items") or []:
        if isinstance(row, dict):
            lines.append(InvoiceLineItem.model_validate(row))
    vendor = payload.get("vendor") or payload.get("vendor_name")
    amount = _money(payload.get("amount") or payload.get("total"))
    return InvoiceCandidate(
        source_type="edi",
        source_id=source_id,
        source_uri=source_uri,
        vendor=vendor,
        vendor_id=payload.get("vendor_id"),
        vendor_invoice_number=payload.get("invoice_number") or payload.get("vendor_invoice_number"),
        invoice_date=payload.get("invoice_date"),
        due_date=payload.get("due_date"),
        currency=payload.get("currency") or "USD",
        subtotal=_money(payload.get("subtotal")),
        tax=_money(payload.get("tax")),
        amount=amount,
        po_id=payload.get("po_id") or payload.get("po_number"),
        line_items=lines,
        document_hash=document_hash(json.dumps(payload, sort_keys=True)),
        extraction_confidence=0.97,
        evidence=[
            _evidence("vendor", "json.vendor", vendor),
            _evidence("vendor_invoice_number", "json.invoice_number", payload.get("invoice_number")),
            _evidence("amount", "json.total", amount),
        ],
        classification="invoice",
        classification_reason="Structured JSON invoice parsed in Python",
        source_context={"format": "json"},
    )


def parse_edi_document(record: dict) -> InvoiceCandidate:
    source_id = record.get("document_id") or record.get("source_id") or "unknown"
    source_uri = record.get("source_uri")
    fmt = (record.get("format") or "").lower()
    payload = record.get("payload")
    xml_text = record.get("xml") or record.get("text")

    if fmt in {"edi_810_json", "edi810", "json_810"} or isinstance(payload, dict) and "TDS" in payload:
        if not isinstance(payload, dict):
            raise EDIParseError("EDI 810 JSON payload missing")
        return parse_edi_810_json(payload, source_id=source_id, source_uri=source_uri)
    if fmt in {"ubl", "ubl_xml", "xml"} or xml_text:
        if not xml_text:
            raise EDIParseError("UBL XML text missing")
        return parse_ubl_xml(xml_text, source_id=source_id, source_uri=source_uri)
    if isinstance(payload, dict):
        return parse_structured_json(payload, source_id=source_id, source_uri=source_uri)
    raise EDIParseError(f"Unsupported EDI format {fmt!r} for {source_id}")
