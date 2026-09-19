"""Small mutation harness for individual audit controls.

Each helper starts from a known passing record and changes one field.
"""

from __future__ import annotations

from audit.models import AuditApproval, AuditInvoice, AuditJournalEntry, AuditPayment, AuditVendor


def passing_round_payment() -> tuple[AuditPayment, AuditVendor]:
    vendor = AuditVendor(
        vendor_id="VEND-ACME",
        vendor_name="Acme Supplies",
        first_seen="2024-01-15",
    )
    payment = AuditPayment(
        payment_id="PAY-CLEAN-49873",
        amount=49873,
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.vendor_name,
        payment_date="2026-09-18",
        payment_method="ach",
        source="automated",
        period="2026-09",
        description="Large non-round automated payment",
    )
    return payment, vendor


def mutate_round_to_50000(payment: AuditPayment) -> AuditPayment:
    return payment.model_copy(update={"amount": 50000})


def mutate_round_to_manual(payment: AuditPayment) -> AuditPayment:
    return payment.model_copy(update={"source": "manual", "payment_method": "wire"})


def mutate_round_vendor_new(vendor: AuditVendor) -> AuditVendor:
    return vendor.model_copy(update={"first_seen": "2026-09-15", "unusual": True})


def passing_post_close_entry() -> AuditJournalEntry:
    return AuditJournalEntry(
        entry_id="JE-AUD-001",
        period="2026-09",
        effective_date="2026-09-28",
        posting_date="2026-09-28",
        posting_timestamp="2026-09-28T10:00:00Z",
        amount=3200,
        authorized=False,
        authorization_id=None,
    )


def mutate_post_close_timestamp(entry: AuditJournalEntry) -> AuditJournalEntry:
    return entry.model_copy(
        update={"posting_timestamp": "2026-10-06T09:00:00Z", "posting_date": "2026-10-06"}
    )


def mutate_add_authorization(entry: AuditJournalEntry) -> AuditJournalEntry:
    return entry.model_copy(
        update={"authorized": True, "authorization_id": "AUTH-PCE-001", "authorization_policy": "PCE-AUTH-001"}
    )


def mutate_remove_authorization(entry: AuditJournalEntry) -> AuditJournalEntry:
    return entry.model_copy(
        update={"authorized": False, "authorization_id": None, "authorization_policy": None}
    )


def passing_sod_approval() -> AuditApproval:
    return AuditApproval(
        approval_id="APR-CLEAN-SOD",
        object_type="invoice",
        object_id="INV-CLEAN-UNIQUE",
        requester_id="USR-JANE-01",
        preparer_id="USR-JANE-01",
        reviewer_id="USR-REV-07",
        approver_id="USR-JANE-02",
        amount=49873,
        period="2026-09",
    )


def mutate_self_approve(record: AuditApproval) -> AuditApproval:
    return record.model_copy(update={"approver_id": record.requester_id})


def passing_unique_invoice() -> AuditInvoice:
    return AuditInvoice(
        invoice_id="INV-CLEAN-UNIQUE",
        vendor_id="VEND-ACME",
        vendor="Acme Supplies",
        vendor_invoice_number="ACM-CLEAN-100",
        amount=49873,
        invoice_date="2026-09-18",
        period="2026-09",
        operational_decision="APPROVE",
        operational_duplicate_detected=False,
    )


def mutate_formatted_duplicate(invoice: AuditInvoice) -> AuditInvoice:
    return invoice.model_copy(
        update={
            "invoice_id": "INV-CLEAN-DUP-FMT",
            "vendor": "Acme Supply Co.",
            "vendor_invoice_number": "acm clean-100",
            "operational_duplicate_detected": False,
        }
    )
