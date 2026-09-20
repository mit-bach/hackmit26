"""Cross-workflow consistency for one canonical financial event."""

from __future__ import annotations

from typing import Any

from cfo.shared_state import shared_state_enabled
from scheduling.cash import policy_eligible_for_pool
from tools import exception_types_for, load_invoice, paid_invoice_ids


def _held(invoice_id: str) -> bool:
    exceptions = exception_types_for(invoice_id)
    return "duplicate" in exceptions or bool(exceptions) and not _approved(invoice_id)


def _approved(invoice_id: str) -> bool:
    from close.orchestrator import decide_ap

    decision = decide_ap(invoice_id, live=False)
    return str(getattr(decision, "decision", "") or getattr(decision, "final_decision", "") or "").upper() == "APPROVE"


def event_consistency(invoice_id: str) -> dict[str, Any]:
    """Every relevant workflow must agree on whether this bill is a real payable."""
    invoice = load_invoice(invoice_id)
    if invoice is None:
        return {"ok": False, "invoice_id": invoice_id, "error": "missing_invoice", "agreements": [], "disagreements": ["invoice"]}
    exceptions = exception_types_for(invoice_id)
    held = "duplicate" in exceptions or (
        exceptions
        and not ({"vendor_mismatch", "small_amount_discrepancy"} >= set(exceptions) and _approved(invoice_id))
    )
    # Clean vendor_mismatch with prior case can still APPROVE.
    try:
        approved = _approved(invoice_id)
    except Exception:
        approved = False
    payable = approved and "duplicate" not in exceptions
    pay_eligible = bool(policy_eligible_for_pool(invoice_id)) if payable else False
    already_paid = invoice_id in paid_invoice_ids()
    disagreements: list[str] = []
    agreements: list[str] = []

    if "duplicate" in exceptions:
        agreements.append("ap_duplicate_hold")
        if pay_eligible:
            disagreements.append("payment_queue")
        else:
            agreements.append("payment_queue_excluded")
        if already_paid:
            # Original may be paid; the duplicate identity should not create a second payment.
            agreements.append("already_paid_original_ok")
    elif payable:
        agreements.append("ap_approved")
        if already_paid:
            agreements.append("not_rescheduled" if not pay_eligible else "reschedule_risk")
            if pay_eligible:
                disagreements.append("payment_queue")
        elif pay_eligible:
            agreements.append("payment_queue")
    else:
        agreements.append("ap_not_payable")
        if pay_eligible:
            disagreements.append("payment_queue")
        else:
            agreements.append("payment_queue_excluded")

    if not shared_state_enabled():
        # Isolated workflows cannot see AP exceptions, so they may disagree. Record that.
        disagreements.append("shared_state_disabled")

    return {
        "ok": not disagreements,
        "invoice_id": invoice_id,
        "vendor": invoice.vendor,
        "amount": float(invoice.amount),
        "exceptions": exceptions,
        "approved": approved,
        "payable": payable,
        "pay_eligible": pay_eligible,
        "already_paid": already_paid,
        "agreements": agreements,
        "disagreements": disagreements,
        "shared_state": shared_state_enabled(),
    }


def duplicate_invoice_ids() -> list[str]:
    from tools import all_invoices

    return [item.invoice_id for item in all_invoices() if "duplicate" in exception_types_for(item.invoice_id)]


def clean_invoice_ids() -> list[str]:
    from tools import all_invoices

    dups = set(duplicate_invoice_ids())
    return [item.invoice_id for item in all_invoices() if item.invoice_id not in dups and not exception_types_for(item.invoice_id)]


def duplicate_must_not_propagate(invoice_id: str) -> dict[str, Any]:
    row = event_consistency(invoice_id)
    blocked = [
        surface
        for surface in ("payment_queue", "forecast_outflow", "close_payable", "vendor_spend", "unexplained_bank")
        if surface in row["disagreements"]
    ]
    if row["pay_eligible"]:
        blocked.append("payment_queue")
    row["blocked_surfaces"] = list(dict.fromkeys(blocked))
    row["ok"] = "duplicate" in row["exceptions"] and not row["pay_eligible"] and "payment_queue" not in row["disagreements"]
    return row
