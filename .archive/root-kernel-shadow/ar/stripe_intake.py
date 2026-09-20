"""Turn Stripe payment objects into AR records. Does not implement payout math."""

from __future__ import annotations

from datetime import datetime, timezone

from integrations.cash import major_units
from ar.ledger import learn_stripe_precedent, open_dispute, post_processor_fee, post_refund
from ar.models import CustomerPayment
from ar.store import all_payments, get_customer, get_invoice, get_payment, save_payment
from ar.workflow import run_cash_apply


def _iso_date(value) -> str:
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
    text = str(value or "")
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    return datetime.now(timezone.utc).date().isoformat()


def _metadata(obj: dict) -> dict:
    raw = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    return {str(key): str(value) for key, value in raw.items() if value not in (None, "")}


def _invoice_hint(obj: dict) -> str | None:
    meta = _metadata(obj)
    for key in ("invoice_id", "order_id", "internal_invoice_id"):
        value = meta.get(key)
        if value:
            return value
    invoice = obj.get("invoice")
    if isinstance(invoice, str) and invoice.upper().startswith("INV"):
        return invoice
    return None


def _payer_name(obj: dict) -> str:
    billing = obj.get("billing_details") if isinstance(obj.get("billing_details"), dict) else {}
    if billing.get("name"):
        return str(billing["name"])
    customer = obj.get("customer")
    if isinstance(customer, dict) and customer.get("name"):
        return str(customer["name"])
    meta = _metadata(obj)
    if meta.get("customer_name"):
        return meta["customer_name"]
    if obj.get("description"):
        return str(obj["description"])
    return ""


def _customer_id(obj: dict) -> str | None:
    meta = _metadata(obj)
    if meta.get("customer_id"):
        return meta["customer_id"]
    customer = obj.get("customer")
    if isinstance(customer, str) and customer.startswith("CUST-"):
        return customer
    if isinstance(customer, dict) and str(customer.get("id") or "").startswith("CUST-"):
        return str(customer["id"])
    return None


def find_payment_for_stripe(*, charge_id: str = "", payment_intent_id: str = "", payment_id: str = "") -> CustomerPayment | None:
    if payment_id:
        found = get_payment(payment_id)
        if found:
            return found
    for item in all_payments():
        meta = item.metadata or {}
        if charge_id and meta.get("stripe_charge_id") == charge_id:
            return item
        if payment_intent_id and meta.get("stripe_payment_intent_id") == payment_intent_id:
            return item
        if charge_id and item.payment_id == charge_id:
            return item
    return None


def payment_from_stripe_object(obj: dict, *, event_type: str) -> CustomerPayment:
    charge_id = str(obj.get("id") or "") if obj.get("object") == "charge" else str(obj.get("latest_charge") or "")
    if obj.get("object") == "payment_intent":
        pi_id = str(obj.get("id") or "")
        charges = obj.get("charges", {})
        data = charges.get("data") if isinstance(charges, dict) else None
        if isinstance(data, list) and data:
            charge_id = str(data[0].get("id") or charge_id)
    else:
        pi_id = str(obj.get("payment_intent") or "")
    existing = find_payment_for_stripe(charge_id=charge_id, payment_intent_id=pi_id)
    if existing:
        return existing
    amount_minor = int(obj.get("amount_received") or obj.get("amount") or 0)
    invoice_hint = _invoice_hint(obj)
    description = str(obj.get("description") or "")
    customer_id = _customer_id(obj)
    if customer_id and get_customer(customer_id) is None:
        customer_id = None
    raw_id = str(charge_id or pi_id or obj.get("id") or "UNKNOWN")
    payment_id = f"PAY-STR-{raw_id}".upper()
    return CustomerPayment(
        payment_id=payment_id,
        payment_date=_iso_date(obj.get("created")),
        amount=major_units(amount_minor),
        currency=str(obj.get("currency") or "usd").upper(),
        payer_name=_payer_name(obj),
        customer_id=customer_id,
        bank_reference=charge_id or pi_id,
        remittance_text=" ".join(part for part in [description, invoice_hint or ""] if part),
        invoice_reference=invoice_hint,
        source="stripe",
        unapplied_amount=major_units(amount_minor),
        application_status="UNMATCHED",
        metadata={
            "stripe_charge_id": charge_id,
            "stripe_payment_intent_id": pi_id,
            "stripe_balance_transaction_id": str(obj.get("balance_transaction") or ""),
            "stripe_event_type": event_type,
            **_metadata(obj),
        },
    )


def apply_stripe_payment(obj: dict, *, event_type: str, live: bool = False) -> dict:
    payment = payment_from_stripe_object(obj, event_type=event_type)
    existing = get_payment(payment.payment_id)
    if existing and existing.application_status in {"APPLIED", "PARTIALLY_APPLIED", "HUMAN_REVIEW"}:
        bt_id = str(obj.get("balance_transaction") or "")
        if bt_id and not (existing.metadata or {}).get("stripe_balance_transaction_id"):
            meta = dict(existing.metadata or {})
            meta["stripe_balance_transaction_id"] = bt_id
            if obj.get("id") and obj.get("object") == "charge":
                meta["stripe_charge_id"] = str(obj["id"])
            save_payment(existing.model_copy(update={"metadata": meta}))
        return {
            "status": "already_processed",
            "payment_id": existing.payment_id,
            "decision": existing.application_status,
            "invoice_ids": [],
            "duplicate": True,
        }
    save_payment(payment)
    trace = run_cash_apply(payment.payment_id, live=live, persist=True)
    invoice_ids = [item.invoice_id for item in (trace.final.applications if trace.final else [])]
    if trace.final and trace.final.decision == "AUTO_APPLY" and (payment.invoice_reference or invoice_ids):
        learn_stripe_precedent(get_payment(payment.payment_id) or payment, invoice_ids or [payment.invoice_reference or ""])
    return {
        "status": "processed",
        "payment_id": payment.payment_id,
        "decision": trace.final.decision if trace.final else None,
        "invoice_ids": invoice_ids,
        "posted": trace.posted,
        "already_posted": trace.already_posted,
        "trace_path": trace.trace_path,
        "reason": trace.final.reason if trace.final else "",
        "precedent_used": list(trace.final.precedent_used) if trace.final else [],
        "precedent_affected": bool(trace.final.precedent_affected) if trace.final else False,
        "ambiguities": list(trace.final.ambiguities) if trace.final else [],
        "duplicate": False,
    }


def apply_stripe_refund(obj: dict, *, event_type: str) -> dict:
    refund_id = str(obj.get("id") or "")
    charge_id = str(obj.get("charge") or "")
    if obj.get("object") == "charge":
        charge_id = str(obj.get("id") or charge_id)
        refunds = obj.get("refunds", {})
        data = refunds.get("data") if isinstance(refunds, dict) else None
        if isinstance(data, list) and data:
            refund_id = str(data[0].get("id") or refund_id)
            obj = data[0]
    payment = find_payment_for_stripe(charge_id=charge_id, payment_intent_id=str(obj.get("payment_intent") or ""))
    amount_minor = abs(int(obj.get("amount") or 0))
    invoice_ids = []
    if payment and payment.invoice_reference and get_invoice(payment.invoice_reference):
        invoice_ids = [payment.invoice_reference]
    elif payment:
        from ar.store import applications_for_payment

        posted = applications_for_payment(payment.payment_id)
        if posted:
            invoice_ids = [item.invoice_id for item in posted[-1].applications]
    result = post_refund(
        refund_id=refund_id or charge_id,
        amount=major_units(amount_minor),
        payment=payment,
        invoice_ids=invoice_ids,
        refund_date=_iso_date(obj.get("created")),
        memo=f"{event_type} {refund_id or charge_id}",
        stripe_refund_id=refund_id or charge_id,
    )
    result["payment_id"] = payment.payment_id if payment else None
    result["invoice_ids"] = invoice_ids
    result["amount"] = major_units(amount_minor)
    return result


def apply_stripe_dispute(obj: dict, *, event_type: str) -> dict:
    dispute_id = str(obj.get("id") or "")
    charge_id = str(obj.get("charge") or "")
    payment = find_payment_for_stripe(charge_id=charge_id, payment_intent_id=str(obj.get("payment_intent") or ""))
    amount_minor = abs(int(obj.get("amount") or 0))
    fee_minor = 0
    for item in obj.get("balance_transactions") or []:
        if str(item.get("type") or "") in {"adjustment", "stripe_fee", "dispute"} and int(item.get("fee") or 0):
            fee_minor += abs(int(item.get("fee") or 0))
    if obj.get("fee"):
        fee_minor = abs(int(obj.get("fee") or 0))
    invoice_ids = []
    if payment and payment.invoice_reference and get_invoice(payment.invoice_reference):
        invoice_ids = [payment.invoice_reference]
    elif payment:
        from ar.store import applications_for_payment

        posted = applications_for_payment(payment.payment_id)
        if posted:
            invoice_ids = [item.invoice_id for item in posted[-1].applications]
    result = open_dispute(
        dispute_id=dispute_id,
        amount=major_units(amount_minor),
        fee_amount=major_units(fee_minor),
        invoice_ids=invoice_ids,
        payment=payment,
        dispute_date=_iso_date(obj.get("created")),
        reason=str(obj.get("reason") or event_type),
        stripe_dispute_id=dispute_id,
    )
    result["payment_id"] = payment.payment_id if payment else None
    result["invoice_ids"] = invoice_ids
    result["amount"] = major_units(amount_minor)
    result["fee_amount"] = major_units(fee_minor)
    return result


def apply_payout_fee(payout_id: str, fee_amount: float, fee_date: str) -> dict:
    return post_processor_fee(payout_id=payout_id, fee_amount=fee_amount, fee_date=fee_date)
