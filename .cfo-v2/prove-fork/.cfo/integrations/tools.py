"""Read-only Stripe/Adyen payout tools. Never mint InvoiceCandidate."""

from __future__ import annotations

from agents import function_tool

from integrations.cash import reconcile_payout
from integrations.store import all_payouts, get_payout, get_reconciliation


def _empty_invoice_guard(payload: dict) -> dict:
    payload["invoice_candidates"] = 0
    payload.pop("invoice_candidate", None)
    payload.pop("InvoiceCandidate", None)
    return payload


def read_processor_payout(payout_id: str) -> dict:
    payout = get_payout(payout_id)
    if payout is None:
        return _empty_invoice_guard(
            {"error": f"unknown payout {payout_id}", "invoice_candidates": 0}
        )
    row = payout.model_dump(mode="json")
    return _empty_invoice_guard(
        {
            "payout_id": payout.payout_id,
            "provider": payout.provider,
            "status": payout.status,
            "amount_minor": payout.amount,
            "currency": payout.currency,
            "arrival_date": payout.arrival_date,
            "bank_deposit_id": payout.bank_deposit_id,
            "line_count": len(payout.lines),
            "invoice_candidates": 0,
            "payout": row,
        }
    )


def read_payout_waterfall(payout_id: str) -> dict:
    payout = get_payout(payout_id)
    if payout is None:
        return _empty_invoice_guard(
            {"error": f"unknown payout {payout_id}", "invoice_candidates": 0}
        )
    breakdown = get_reconciliation(payout_id) or reconcile_payout(payout)
    payload = breakdown.model_dump(mode="json")
    payload["invoice_candidates"] = 0
    payload["next_owner_deposit"] = "cash"
    payload["next_owner_charges"] = "apply"
    payload["never_ap_invoice"] = True
    return _empty_invoice_guard(payload)


def read_processor_payouts() -> list[dict]:
    rows = []
    for payout in all_payouts():
        rows.append(
            _empty_invoice_guard(
                {
                    "payout_id": payout.payout_id,
                    "provider": payout.provider,
                    "status": payout.status,
                    "amount_minor": payout.amount,
                    "bank_deposit_id": payout.bank_deposit_id,
                    "invoice_candidates": 0,
                }
            )
        )
    return rows


@function_tool
def get_processor_payout(payout_id: str) -> dict:
    return read_processor_payout(payout_id)


@function_tool
def get_payout_waterfall(payout_id: str) -> dict:
    return read_payout_waterfall(payout_id)


@function_tool
def list_processor_payouts() -> list[dict]:
    return read_processor_payouts()
