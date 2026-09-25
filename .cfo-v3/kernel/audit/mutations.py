"""Runtime mutations. Expected answers live only in the caller, never on the dataset."""

from __future__ import annotations

from dataclasses import dataclass, field

from audit.dataset import AuditDataset
from audit.models import AuditInvoice, AuditVendor, OperationalDecision


@dataclass
class Mutation:
    mutation_id: str
    description: str
    object_id: str
    control_id: str
    kind: str
    expected_detect: bool = True


def _payment(dataset: AuditDataset, payment_id: str):
    for item in dataset.payments:
        if item.payment_id == payment_id:
            return item
    raise KeyError(payment_id)


def _journal(dataset: AuditDataset, entry_id: str):
    for item in dataset.journals:
        if item.entry_id == entry_id:
            return item
    raise KeyError(entry_id)


def _approval(dataset: AuditDataset, approval_id: str):
    for item in dataset.approvals:
        if item.approval_id == approval_id:
            return item
    raise KeyError(approval_id)


def _recon(dataset: AuditDataset, reconciliation_id: str):
    for item in dataset.reconciliations:
        if item.reconciliation_id == reconciliation_id:
            return item
    raise KeyError(reconciliation_id)


def _vendor(dataset: AuditDataset, vendor_id: str):
    for item in dataset.vendors:
        if item.vendor_id == vendor_id:
            return item
    raise KeyError(vendor_id)


def apply_mutations(dataset: AuditDataset, names: list[str] | None = None) -> tuple[AuditDataset, list[Mutation]]:
    """Copy the dataset, apply named mutations, return (mutated, mutation metadata)."""
    copy = dataset.copy()
    applied: list[Mutation] = []
    catalog = [
        ("corrupt_recon_status", mutate_recon_status),
        ("corrupt_recon_amount", mutate_recon_amount),
        ("self_approve", mutate_self_approve),
        ("post_close_unauthorized", mutate_post_close),
        ("duplicate_invoice_format", mutate_duplicate_invoice),
        ("near_duplicate_vendor", mutate_near_duplicate_vendor),
        ("round_manual_wire", mutate_round_manual_wire),
        ("stripe_fee_arithmetic", mutate_stripe_fee),
        ("ar_cash_assignment", mutate_ar_assignment),
    ]
    wanted = set(names) if names is not None else {name for name, _fn in catalog}
    for name, fn in catalog:
        if name in wanted:
            applied.append(fn(copy))
    return copy, applied


def mutate_recon_status(dataset: AuditDataset) -> Mutation:
    item = _recon(dataset, "REC-AUD-AGREE")
    item.original_status = "UNMATCHED"
    item.original_match_type = "UNMATCHED_BANK"
    return Mutation(
        "corrupt_recon_status",
        "Changed original bank reconciliation from MATCHED to UNMATCHED",
        "REC-AUD-AGREE",
        "AUD-REPERF-001",
        "recon_status",
    )


def mutate_recon_amount(dataset: AuditDataset) -> Mutation:
    item = _recon(dataset, "REC-AUD-AGREE")
    item.original_difference = 12.40
    item.original_ledger_amount = item.original_bank_amount + 12.40
    return Mutation(
        "corrupt_recon_amount",
        "Altered original reconciled difference by $12.40",
        "REC-AUD-AGREE",
        "AUD-REPERF-001",
        "recon_amount",
    )


def mutate_self_approve(dataset: AuditDataset) -> Mutation:
    item = _approval(dataset, "APR-AUD-001")
    item.approver_id = item.requester_id
    return Mutation(
        "self_approve",
        "Changed approver ID so requester == approver",
        "APR-AUD-001",
        "AUD-SOD-001",
        "self_approval",
    )


def mutate_post_close(dataset: AuditDataset) -> Mutation:
    item = _journal(dataset, "JE-AUD-001")
    close = dataset.period.close_timestamp or "2026-10-03T18:00:00Z"
    item.posting_timestamp = "2026-10-06T09:00:00Z"
    item.posting_date = "2026-10-06"
    item.authorized = False
    item.authorization_id = None
    item.authorization_policy = None
    return Mutation(
        "post_close_unauthorized",
        f"Moved JE-AUD-001 posting after close {close} and removed authorization",
        "JE-AUD-001",
        "AUD-PCE-001",
        "post_close",
    )


def mutate_duplicate_invoice(dataset: AuditDataset) -> Mutation:
    source = next(item for item in dataset.invoices if item.invoice_id == "INV-CLEAN-UNIQUE")
    clone = AuditInvoice(
        invoice_id="INV-CLEAN-DUP-FMT",
        vendor_id=source.vendor_id,
        vendor="Acme Supply Co.",
        vendor_invoice_number="acm clean-100",
        amount=source.amount,
        invoice_date=source.invoice_date,
        period=source.period,
        operational_decision="APPROVE",
        operational_duplicate_detected=False,
    )
    dataset.invoices.append(clone)
    dataset.decisions.append(
        OperationalDecision(
            object_id=clone.invoice_id,
            object_type="invoice",
            workflow="ap",
            decision="APPROVE",
            duplicate_detected=False,
        )
    )
    return Mutation(
        "duplicate_invoice_format",
        "Added a duplicate invoice with altered vendor/number formatting",
        "INV-CLEAN-UNIQUE",
        "AUD-DUP-INV-001",
        "duplicate_invoice",
    )


def mutate_near_duplicate_vendor(dataset: AuditDataset) -> Mutation:
    dataset.vendors.append(
        AuditVendor(
            vendor_id="VEND-ACME-RUNTIME",
            vendor_name="Acme Supply Co.",
            first_seen="2026-09-20",
        )
    )
    return Mutation(
        "near_duplicate_vendor",
        "Added a near-duplicate vendor master (Acme Supply Co.)",
        "VEND-ACME",
        "AUD-DUP-VEND-001",
        "duplicate_vendor",
    )


def mutate_round_manual_wire(dataset: AuditDataset) -> Mutation:
    item = _payment(dataset, "PAY-CLEAN-49873")
    vendor = _vendor(dataset, "VEND-NEWCO") if any(v.vendor_id == "VEND-NEWCO" for v in dataset.vendors) else None
    item.amount = 50000
    item.source = "manual"
    item.payment_method = "wire"
    if vendor:
        item.vendor_id = vendor.vendor_id
        item.vendor_name = vendor.vendor_name
        vendor.first_seen = "2026-09-15"
        vendor.unusual = True
    return Mutation(
        "round_manual_wire",
        "Changed $49,873 automated payment into a $50,000 manual wire to a new vendor",
        "PAY-CLEAN-49873",
        "AUD-RND-001",
        "round_number",
    )


def mutate_stripe_fee(dataset: AuditDataset) -> Mutation:
    item = _recon(dataset, "REC-AUD-STRIPE")
    item.original_difference = 12.40
    item.original_ledger_amount = item.original_bank_amount - 12.40
    item.original_match_type = "FEE_NETTED"
    return Mutation(
        "stripe_fee_arithmetic",
        "Altered original Stripe net/fee arithmetic by $12.40",
        "REC-AUD-STRIPE",
        "AUD-REPERF-001",
        "stripe_fee",
    )


def mutate_ar_assignment(dataset: AuditDataset) -> Mutation:
    item = _recon(dataset, "REC-AUD-AR-AGREE")
    item.invoice_ids = ["INV-AR-AUD-002"]
    item.original_decision = "AUTO_APPLY"
    item.original_status = "AUTO_APPLY"
    return Mutation(
        "ar_cash_assignment",
        "Changed original AR cash application to the wrong invoice",
        "REC-AUD-AR-AGREE",
        "AUD-REPERF-001",
        "ar_cash",
    )


def restore_mutation(dataset: AuditDataset, mutation_id: str) -> AuditDataset:
    """Undo one mutation by reloading the clean object from an unmutated copy is the caller's job.

    This helper applies the inverse of selected demo corrections.
    """
    if mutation_id == "self_approve":
        item = _approval(dataset, "APR-AUD-001")
        item.approver_id = "USR-APPR-01"
    elif mutation_id == "round_manual_wire":
        item = _payment(dataset, "PAY-CLEAN-49873")
        item.amount = 49873
        item.source = "automated"
        item.payment_method = "ach"
        item.vendor_id = "VEND-ACME"
        item.vendor_name = "Acme Supplies"
    return dataset
