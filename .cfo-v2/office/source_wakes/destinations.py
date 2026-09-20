"""Handle destinations for Source Bots. Topology, not Kernel math."""

from __future__ import annotations

EMAIL_DESTINATION: dict[str, tuple[str, str]] = {
    "invoice": ("ap", "prepare"),
    "vendor_invoice": ("ap", "prepare"),
    "payment_confirmation": ("apply", "apply"),
    "remittance": ("apply", "apply"),
    "customer_remittance": ("apply", "apply"),
}

STRIPE_DEPOSIT = ("cash", "match")
STRIPE_CHARGES = ("apply", "apply")
BANK_LINE = ("cash", "match")
BOOKS_BILL = ("ap", "prepare")
BOOKS_AR = ("collect", "chase")
BOOKS_LOCK_STATE = ("close", "coordinate")


def email_destination(classification: str) -> tuple[str, str] | None:
    return EMAIL_DESTINATION.get(classification)


def books_destination(*, record_kind: str) -> tuple[str, str] | None:
    if record_kind in {"erp-invoice", "procurement-invoice", "edi", "xero-accpay", "netsuite-vendorbill", "coupa-invoice"}:
        return BOOKS_BILL
    if record_kind in {"xero-accrec", "open-invoice"}:
        return BOOKS_AR
    if record_kind in {"period-lock-state", "gl-row"}:
        return BOOKS_LOCK_STATE
    return None
