"""Human-readable transaction lineage across connected finance workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cfo.explain import label_record, money
from cfo.consistency import event_consistency
from tools import (
    DATA_DIR,
    exception_types_for,
    load_goods_receipt,
    load_invoice,
    load_purchase_order,
    paid_invoice_ids,
)


ROLE_TITLES = {
    "document": "Original document",
    "email": "Inbox message",
    "ap_invoice": "Invoice recognized",
    "purchase_order": "Purchase order match",
    "goods_receipt": "Receiving record",
    "vendor_payment": "Payment scheduled or paid",
    "bank": "Bank movement reconciled",
    "journal": "General ledger updated",
    "forecast": "Cash forecast updated",
    "close_evidence": "Month-end close",
    "audit": "Audit evidence retained",
    "memory": "Prior decision remembered",
}


def _json(*parts: str) -> list | dict | None:
    path = Path(DATA_DIR).joinpath(*parts)
    if not path.is_file():
        demo = Path(__file__).resolve().parent.parent / "data" / "demo"
        path = demo.joinpath(*parts)
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _lineage_row(record_id: str) -> dict | None:
    rows = _json("lineage.json") or []
    for row in rows:
        if row.get("record_id") == record_id:
            return row
        for node in row.get("nodes") or []:
            if node.get("id") == record_id:
                return row
    return None


def describe_event(record_id: str) -> dict[str, Any]:
    """What Maximor received, decided, and changed elsewhere for one event."""
    invoice = load_invoice(record_id)
    if invoice is None:
        return {
            "record_id": record_id,
            "title": record_id,
            "received": f"No invoice named {record_id} is on the operational books.",
            "decision": "Nothing to decide.",
            "why": "The identifier does not match a vendor invoice.",
            "changed": [],
            "correct": None,
            "steps": [],
        }
    exceptions = exception_types_for(record_id)
    paid = record_id in paid_invoice_ids()
    po = load_purchase_order(invoice.po_id)
    receipt = load_goods_receipt(invoice.po_id)
    consistency = event_consistency(record_id)
    duplicate = "duplicate" in exceptions
    decision = "Held as a duplicate" if duplicate else ("Approved payable" if not exceptions else "Held for exceptions")
    if paid and not duplicate:
        decision = "Already paid"
    received = (
        f"Maximor received invoice {label_record(record_id, vendor=invoice.vendor)} "
        f"for {money(invoice.amount)}, dated {invoice.invoice_date}."
    )
    why = (
        "The same vendor invoice number is already on the books, so this copy is not a new payable."
        if duplicate
        else (
            "Purchase order, receiving, and invoice amounts agree."
            if not exceptions
            else "The three-way match found " + ", ".join(exceptions) + "."
        )
    )
    changed = []
    if duplicate:
        changed = [
            "Accounts payable did not create a second payable.",
            "The payment queue will not include this copy.",
            "The cash forecast will not treat it as a new outflow.",
            "Close will not add a second vendor balance.",
            "Audit keeps the duplicate hold as evidence.",
        ]
    else:
        if po:
            changed.append(f"Matched to purchase order {po.po_id} for {po.vendor}.")
        if receipt:
            changed.append(f"Checked receiving record {receipt.po_id}.")
        if paid:
            changed.append("A vendor payment is already on the books.")
        else:
            changed.append("Eligible for the weekly payment pool if policy allows.")
        changed.append("Close and audit keep this invoice as payable evidence.")
    packed = _lineage_row(record_id)
    steps = []
    if packed:
        for node in packed.get("nodes") or []:
            role = node.get("role") or ""
            node_id = node.get("id") or ""
            vendor = node.get("vendor") or invoice.vendor
            amount = node.get("amount_cents")
            detail = label_record(node_id, vendor=vendor if role == "ap_invoice" else None)
            if amount:
                detail = f"{detail} for {money(amount / 100.0)}"
            steps.append(
                {
                    "role": role,
                    "title": ROLE_TITLES.get(role, role.replace("_", " ").title()),
                    "record_id": node_id,
                    "detail": detail,
                }
            )
    else:
        steps = [
            {"role": "ap_invoice", "title": "Invoice recognized", "record_id": record_id, "detail": label_record(record_id, vendor=invoice.vendor)},
            {"role": "purchase_order", "title": "Purchase order match", "record_id": invoice.po_id, "detail": invoice.po_id or "No purchase order"},
            {"role": "goods_receipt", "title": "Receiving record", "record_id": invoice.po_id, "detail": "Receiving checked" if receipt else "No receiving record"},
        ]
    return {
        "record_id": record_id,
        "title": f"Invoice {record_id} from {invoice.vendor}",
        "vendor": invoice.vendor,
        "amount": float(invoice.amount),
        "received": received,
        "decision": decision,
        "why": why,
        "changed": changed,
        "correct": bool(consistency.get("ok")) if duplicate else (not duplicate),
        "exceptions": exceptions,
        "paid": paid,
        "consistency": consistency,
        "steps": steps,
        "purchase_order": po.po_id if po else None,
        "purchase_order_label": f"Purchase order {po.po_id} for {po.vendor}" if po else None,
    }
