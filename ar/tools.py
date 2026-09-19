"""Structured facts for AR agents. Agents do not browse the raw store."""

from __future__ import annotations

from agents import function_tool

from ar.cash import generate_cash_candidates
from ar.collections import collection_candidates
from ar.context import ar_close_snapshot
from ar.store import get_invoice, get_payment, get_customer, precedents


@function_tool
def get_collection_candidates(as_of: str) -> list[dict]:
    """Return overdue collection facts already computed by Python."""
    return [item.model_dump(mode="json") for item in collection_candidates(as_of)]


@function_tool
def get_collection_invoice_facts(invoice_id: str, as_of: str) -> dict:
    """Return Python collection facts for one invoice."""
    from ar.collections import build_collection_facts

    invoice = get_invoice(invoice_id)
    if invoice is None:
        return {"error": f"Unknown invoice {invoice_id}"}
    return build_collection_facts(invoice, as_of).model_dump(mode="json")


@function_tool
def get_cash_application_facts(payment_id: str) -> dict:
    """Return payment, open invoices, and deterministic match candidates."""
    payment = get_payment(payment_id)
    if payment is None:
        return {"error": f"Unknown payment {payment_id}"}
    return generate_cash_candidates(payment).model_dump(mode="json")


@function_tool
def get_ar_precedents(customer_id: str = "") -> list[dict]:
    """Return customer remittance / payment-pattern precedent. Precedent is evidence, not a rule."""
    return [item.model_dump(mode="json") for item in precedents(customer_id)]


@function_tool
def get_ar_customer(customer_id: str) -> dict:
    """Return the customer profile used for collections and cash application."""
    customer = get_customer(customer_id)
    if customer is None:
        return {"error": f"Unknown customer {customer_id}"}
    return customer.model_dump(mode="json")


@function_tool
def get_ar_close_snapshot(as_of: str) -> dict:
    """Return the shared AR snapshot consumed by close, forecast, and audit."""
    return ar_close_snapshot(as_of).model_dump(mode="json")
