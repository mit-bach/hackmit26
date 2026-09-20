"""Answer deterministic finance questions from operational Maximor records.

Never loads answer keys. Structured specs are the product API; graders compare
the returned numbers and IDs to hidden gold after the lookup finishes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.isolation import assert_operational_read_allowed
from tools import all_invoices, exception_types_for, paid_invoice_ids


def _roots() -> list[Path]:
    from sample_data.paths import snapshot_loader_paths

    roots = []
    try:
        snap = snapshot_loader_paths()
        tools_data = snap.get("tools_data")
        if tools_data:
            roots.append(Path(tools_data))
            if Path(tools_data).name != "demo":
                roots.append(Path(tools_data) / "demo")
    except Exception:
        pass
    roots.append(Path(__file__).resolve().parent.parent / "data" / "demo")
    seen = []
    for root in roots:
        if root not in seen:
            seen.append(root)
    return seen


def _load(*parts: str):
    import json

    for root in _roots():
        path = root.joinpath(*parts)
        if path.is_file():
            assert_operational_read_allowed(path)
            return json.loads(path.read_text())
    return []


def vendor_spend(vendor: str, period: str) -> dict[str, Any]:
    total_minor = 0
    sources: list[str] = []
    needle = vendor.lower()
    for row in _load("canonical", "vendor_payments.json"):
        if needle not in str(row.get("vendor") or "").lower():
            continue
        date_value = str(row.get("payment_date") or row.get("date") or "")
        if period and not date_value.startswith(period):
            continue
        total_minor += int(row.get("amount_minor") or round(float(row.get("amount") or 0) * 100))
        sources.append(row.get("payment_id"))
    return {
        "answer": round(total_minor / 100.0, 2),
        "unit": "usd",
        "source_record_ids": [item for item in sources if item],
        "steps": [f"Sum canonical vendor payments to {vendor} dated in {period}"],
    }


def unpaid_invoices_older_than(days: int, as_of: str = "2026-09-30") -> dict[str, Any]:
    from ar.aging import days_past_due
    from ar.store import all_invoices as ar_invoices

    found = []
    for invoice in ar_invoices():
        if float(invoice.outstanding_amount) <= 0:
            continue
        if invoice.status == "PAID":
            continue
        age = days_past_due(invoice.due_date, as_of)
        if age > days:
            found.append(invoice.invoice_id)
    found.sort()
    return {
        "answer": found,
        "source_record_ids": found,
        "steps": [f"Age open AR invoices as of {as_of} and keep those more than {days} days past due"],
    }


def stripe_payouts_with_chargebacks() -> dict[str, Any]:
    ids = []
    for row in _load("integrations", "stripe", "payouts.json"):
        lines = row.get("lines") or []
        if any(str(line.get("line_type") or "").lower() in {"dispute", "chargeback"} for line in lines):
            ids.append(row.get("payout_id"))
    ids = [item for item in ids if item]
    return {
        "answer": ids,
        "source_record_ids": ids,
        "steps": ["Read Stripe payout line types and keep payouts that include a dispute or chargeback"],
    }


def stripe_fee_expense(period: str) -> dict[str, Any]:
    total = 0.0
    sources = []
    for row in _load("integrations", "stripe", "payouts.json"):
        arrival = str(row.get("arrival_date") or "")
        if period and not arrival.startswith(period):
            continue
        for line in row.get("lines") or []:
            if str(line.get("line_type") or "") != "stripe_fee":
                continue
            total += abs(float(line.get("amount") or 0))
            sources.append(row.get("payout_id"))
    return {
        "answer": round(total, 2),
        "unit": "usd",
        "source_record_ids": list(dict.fromkeys(item for item in sources if item)),
        "steps": [f"Sum Stripe fee lines on payouts that arrived in {period}"],
    }


def cash_effect_if_pay_due(days: int, as_of: str = "2026-09-30") -> dict[str, Any]:
    from scheduling.cash import policy_eligible_for_pool

    as_of_dt = datetime.strptime(as_of, "%Y-%m-%d")
    total = 0.0
    sources = []
    paid = paid_invoice_ids()
    for invoice in all_invoices():
        if invoice.invoice_id in paid:
            continue
        if not policy_eligible_for_pool(invoice.invoice_id):
            continue
        due = str(getattr(invoice, "due_date", "") or "")[:10]
        if not due:
            continue
        try:
            due_dt = datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            continue
        if 0 <= (due_dt - as_of_dt).days <= days:
            total += float(invoice.amount)
            sources.append(invoice.invoice_id)
    return {
        "answer": round(total, 2),
        "unit": "usd",
        "source_record_ids": sources,
        "steps": [f"Sum payment-eligible invoices due within {days} days of {as_of}"],
    }


def _attachment_text(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item)
    if item.get("text"):
        return str(item.get("text"))
    rel = item.get("path") or item.get("filename")
    if not rel:
        return str(item.get("filename") or "")
    for root in _roots():
        path = root / "ingestion" / str(rel)
        if not path.is_file():
            path = root / "ingestion" / "files" / Path(str(rel)).name
        if path.is_file():
            assert_operational_read_allowed(path)
            return path.read_text()
    return str(item.get("filename") or "")


def revised_invoices() -> dict[str, Any]:
    from invoice_ingestion.traps import extract_supersedes

    found = []
    for row in _load("ingestion", "emails.json"):
        attachments = row.get("attachments") or []
        chunks = [str(row.get("subject") or ""), str(row.get("body") or "")]
        for item in attachments:
            chunks.append(_attachment_text(item))
        text = "\n".join(chunks)
        if extract_supersedes(str(text)) or extract_supersedes(str(row.get("subject") or "")):
            found.append(row.get("message_id"))
    return {
        "answer": found,
        "source_record_ids": [item for item in found if item],
        "steps": ["Inspect ingested email attachments for revision/supersession language"],
    }


def largest_vendor_discrepancy() -> dict[str, Any]:
    worst = None
    amount = -1.0
    for invoice in all_invoices():
        exceptions = exception_types_for(invoice.invoice_id)
        if not exceptions:
            continue
        if float(invoice.amount) > amount:
            amount = float(invoice.amount)
            worst = invoice.invoice_id
    return {
        "answer": worst,
        "source_record_ids": [worst] if worst else [],
        "steps": ["Select the highest-dollar AP invoice that still has an exception"],
    }


def bank_deposit_for_payout(payout_id: str) -> dict[str, Any]:
    for row in _load("integrations", "stripe", "bank_deposits.json"):
        if row.get("payout_id") == payout_id:
            return {
                "answer": row.get("deposit_id"),
                "source_record_ids": [row.get("deposit_id"), payout_id],
                "steps": ["Map the Stripe payout id to the matching bank deposit record"],
            }
    return {
        "answer": None,
        "source_record_ids": [payout_id],
        "steps": ["No bank deposit carried that payout id"],
    }


def outflow_from_prior_approvals(pay_period: str, approve_period: str) -> dict[str, Any]:
    """Portion of pay_period vendor cash that settled invoices dated in approve_period."""
    invoices = {item.invoice_id: item for item in all_invoices()}
    attributed_minor = 0
    period_minor = 0
    sources = []
    for row in _load("canonical", "vendor_payments.json"):
        date_value = str(row.get("payment_date") or "")
        if not date_value.startswith(pay_period):
            continue
        paid = int(row.get("amount_minor") or round(float(row.get("amount") or 0) * 100))
        period_minor += paid
        for invoice_id in row.get("invoice_ids") or []:
            invoice = invoices.get(invoice_id)
            if invoice is None:
                continue
            inv_date = str(getattr(invoice, "invoice_date", "") or "")
            if inv_date.startswith(approve_period):
                if len(row.get("invoice_ids") or []) == 1:
                    attributed_minor += paid
                else:
                    attributed_minor += int(round(float(invoice.amount) * 100))
                sources.append(invoice_id)
    portion = round(attributed_minor / period_minor, 4) if period_minor else 0.0
    return {
        "answer": portion,
        "unit": "portion",
        "amount": round(attributed_minor / 100.0, 2),
        "period_outflow": round(period_minor / 100.0, 2),
        "source_record_ids": list(dict.fromkeys(sources)),
        "steps": [
            f"Sum {pay_period} vendor payments",
            f"Keep the share that settled invoices dated {approve_period}",
            "Divide attributed cash by that month's vendor outflow",
        ],
    }


HANDLERS = {
    "vendor_spend": lambda spec: vendor_spend(spec["vendor"], spec["period"]),
    "unpaid_over_days": lambda spec: unpaid_invoices_older_than(int(spec.get("days") or 60), spec.get("as_of") or "2026-09-30"),
    "stripe_chargeback_payouts": lambda spec: stripe_payouts_with_chargebacks(),
    "stripe_fee_expense": lambda spec: stripe_fee_expense(spec.get("period") or "2026-09"),
    "pay_due_cash_effect": lambda spec: cash_effect_if_pay_due(int(spec.get("days") or 7), spec.get("as_of") or "2026-09-30"),
    "revised_invoices": lambda spec: revised_invoices(),
    "largest_vendor_discrepancy": lambda spec: largest_vendor_discrepancy(),
    "bank_deposit_for_payout": lambda spec: bank_deposit_for_payout(spec["payout_id"]),
    "outflow_from_prior_approvals": lambda spec: outflow_from_prior_approvals(
        spec.get("pay_period") or "2026-09",
        spec.get("approve_period") or "2026-08",
    ),
}


def answer_finance_question(spec: dict[str, Any]) -> dict[str, Any]:
    kind = spec.get("type")
    handler = HANDLERS.get(kind)
    if handler is None:
        return {"answer": None, "error": f"unsupported question type {kind}", "source_record_ids": [], "steps": []}
    result = handler(spec)
    result["question_id"] = spec.get("question_id")
    result["type"] = kind
    return result
