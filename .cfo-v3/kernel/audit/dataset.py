"""In-memory audit dataset. Mutations operate on copies; disk fixtures stay unchanged."""

from __future__ import annotations

from copy import deepcopy

from ar.models import Customer, CustomerInvoice, CustomerPayment
from audit.models import (
    AccountingPeriod,
    AuditApproval,
    AuditCorrection,
    AuditInvoice,
    AuditJournalEntry,
    AuditPayment,
    AuditVendor,
    OperationalDecision,
    PlantedReconciliation,
)
from audit.store import (
    load_approvals,
    load_invoices,
    load_journals,
    load_operational_decisions,
    load_payments,
    load_period,
    load_planted_reconciliations,
    load_recon_source,
    load_vendors,
)
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry
from pydantic import BaseModel, Field


def default_ar_objects() -> tuple[list[Customer], list[CustomerInvoice], dict[str, CustomerPayment]]:
    customers = [
        Customer(customer_id="CUST-AUD-1", customer_name="Helios Labs", aliases=["Helios"]),
    ]
    invoices = [
        CustomerInvoice(
            invoice_id="INV-AR-AUD-001",
            customer_id="CUST-AUD-1",
            customer_name="Helios Labs",
            invoice_date="2026-09-01",
            due_date="2026-09-30",
            original_amount=1800,
            outstanding_amount=1800,
        ),
        CustomerInvoice(
            invoice_id="INV-AR-AUD-002",
            customer_id="CUST-AUD-1",
            customer_name="Helios Labs",
            invoice_date="2026-09-05",
            due_date="2026-10-05",
            original_amount=900,
            outstanding_amount=900,
        ),
    ]
    payments = {
        "PAY-AR-AUD-001": CustomerPayment(
            payment_id="PAY-AR-AUD-001",
            customer_id="CUST-AUD-1",
            payer_name="Helios Labs",
            payment_date="2026-09-18",
            amount=1800,
            unapplied_amount=1800,
            remittance_text="INV-AR-AUD-001",
            invoice_reference="INV-AR-AUD-001",
        ),
        "PAY-AR-AUD-002": CustomerPayment(
            payment_id="PAY-AR-AUD-002",
            customer_id="CUST-AUD-1",
            payer_name="Helios Labs",
            payment_date="2026-09-19",
            amount=900,
            unapplied_amount=900,
            remittance_text="no invoice mentioned",
        ),
    }
    return customers, invoices, payments


FALSE_POSITIVE_GUARD_IDS = {
    "PAY-AUD-001",
    "PAY-AUD-003",
    "JE-AUD-002",
    "APR-AUD-001",
    "APR-AUD-004",
    "APR-CLEAN-SOD",
    "VEND-NORTHSTAR",
    "VEND-HELIOS",
    "PAY-CLEAN-REPEAT-A",
    "PAY-CLEAN-REPEAT-B",
    "INV-CLEAN-SAMEAMT-A",
    "INV-CLEAN-SAMEAMT-B",
    "REC-AUD-ACCRUAL-AGREE",
}


PLANTED_FAILURE_IDS = {
    "PAY-AUD-002",
    "JE-AUD-003",
    "JE-AUD-004",
    "APR-AUD-002",
    "APR-AUD-003",
    "APR-AUD-005",
    "AUD-INV-MISS-1",
    "AUD-INV-MISS-2",
    "VEND-ACME-DUP",
    "REC-AUD-DISAGREE",
    "REC-AUD-ACCRUAL-DISAGREE",
    "REC-AUD-AR-DISAGREE",
}


class AuditDataset(BaseModel):
    period: AccountingPeriod
    vendors: list[AuditVendor] = Field(default_factory=list)
    payments: list[AuditPayment] = Field(default_factory=list)
    journals: list[AuditJournalEntry] = Field(default_factory=list)
    approvals: list[AuditApproval] = Field(default_factory=list)
    invoices: list[AuditInvoice] = Field(default_factory=list)
    decisions: list[OperationalDecision] = Field(default_factory=list)
    reconciliations: list[PlantedReconciliation] = Field(default_factory=list)
    bank: list[BankTransaction] = Field(default_factory=list)
    ledger: list[LedgerEntry] = Field(default_factory=list)
    fees: list[FeeEvidence] = Field(default_factory=list)
    ar_customers: list[Customer] = Field(default_factory=list)
    ar_invoices: list[CustomerInvoice] = Field(default_factory=list)
    ar_payments: dict[str, CustomerPayment] = Field(default_factory=dict)
    corrections: list[AuditCorrection] = Field(default_factory=list)

    def copy(self) -> "AuditDataset":
        return AuditDataset.model_validate(deepcopy(self.model_dump(mode="json")))


def load_dataset(period: str = "2026-09") -> AuditDataset:
    bank, ledger, fees = load_recon_source()
    planted = load_planted_reconciliations()
    customers, invoices, payments = default_ar_objects()
    return AuditDataset(
        period=load_period(period),
        vendors=load_vendors(),
        payments=load_payments(),
        journals=[item for item in load_journals() if item.period == period],
        approvals=load_approvals(),
        invoices=load_invoices(),
        decisions=load_operational_decisions(),
        reconciliations=[item for item in planted if item.period == period or not item.period],
        bank=bank,
        ledger=ledger,
        fees=fees,
        ar_customers=customers,
        ar_invoices=invoices,
        ar_payments=payments,
    )


def _row_id(item) -> str | None:
    if isinstance(item, PlantedReconciliation):
        return item.reconciliation_id
    if isinstance(item, AuditPayment):
        return item.payment_id
    if isinstance(item, AuditJournalEntry):
        return item.entry_id
    if isinstance(item, AuditApproval):
        return item.approval_id
    if isinstance(item, AuditInvoice):
        return item.invoice_id
    if isinstance(item, AuditVendor):
        return item.vendor_id
    if isinstance(item, OperationalDecision):
        return item.object_id
    if isinstance(item, BankTransaction):
        return item.transaction_id
    if isinstance(item, LedgerEntry):
        return item.entry_id
    return getattr(item, "object_id", None)


def _keep(rows, attr: str = "object_id"):
    return [item for item in rows if _row_id(item) not in PLANTED_FAILURE_IDS]


def extra_clean_records() -> dict:
    """Passing records used for mutation and false-positive tests. Not planted failures."""
    return {
        "vendors": [
            AuditVendor(vendor_id="VEND-NORTHSTAR", vendor_name="Helios Labrador Supply", first_seen="2023-02-01"),
            AuditVendor(vendor_id="VEND-HELIOS", vendor_name="Helios Labs", first_seen="2023-02-01"),
        ],
        "payments": [
            AuditPayment(
                payment_id="PAY-CLEAN-49873",
                amount=49873,
                vendor_id="VEND-ACME",
                vendor_name="Acme Supplies",
                payment_date="2026-09-18",
                payment_method="ach",
                source="automated",
                invoice_ids=["INV-CLEAN-UNIQUE"],
                approval_ids=["APR-CLEAN-SOD"],
                initiator_id="USR-PAY-07",
                approver_id="USR-APPR-07",
                period="2026-09",
                description="Large non-round automated payment",
            ),
            AuditPayment(
                payment_id="PAY-CLEAN-REPEAT-A",
                amount=1920,
                vendor_id="VEND-ACME",
                vendor_name="Acme Supplies",
                payment_date="2026-09-11",
                source="automated",
                invoice_ids=["INV-CLEAN-SAMEAMT-A"],
                approval_ids=["APR-CLEAN-SOD"],
                initiator_id="USR-PAY-07",
                approver_id="USR-APPR-07",
                period="2026-09",
                description="Valid invoice A, same amount as B",
            ),
            AuditPayment(
                payment_id="PAY-CLEAN-REPEAT-B",
                amount=1920,
                vendor_id="VEND-ACME",
                vendor_name="Acme Supplies",
                payment_date="2026-09-21",
                source="automated",
                invoice_ids=["INV-CLEAN-SAMEAMT-B"],
                approval_ids=["APR-CLEAN-SOD"],
                initiator_id="USR-PAY-07",
                approver_id="USR-APPR-07",
                period="2026-09",
                description="Valid invoice B, same amount as A, different number",
            ),
        ],
        "invoices": [
            AuditInvoice(
                invoice_id="INV-CLEAN-UNIQUE",
                vendor_id="VEND-ACME",
                vendor="Acme Supplies",
                vendor_invoice_number="ACM-CLEAN-100",
                amount=49873,
                invoice_date="2026-09-18",
                period="2026-09",
                operational_decision="APPROVE",
                operational_duplicate_detected=False,
            ),
            AuditInvoice(
                invoice_id="INV-CLEAN-SAMEAMT-A",
                vendor_id="VEND-ACME",
                vendor="Acme Supplies",
                vendor_invoice_number="ACM-4410-A",
                amount=1920,
                invoice_date="2026-09-11",
                period="2026-09",
                operational_decision="APPROVE",
                operational_duplicate_detected=False,
            ),
            AuditInvoice(
                invoice_id="INV-CLEAN-SAMEAMT-B",
                vendor_id="VEND-ACME",
                vendor="Acme Supplies",
                vendor_invoice_number="ACM-4410-B",
                amount=1920,
                invoice_date="2026-09-21",
                period="2026-09",
                operational_decision="APPROVE",
                operational_duplicate_detected=False,
            ),
        ],
        "approvals": [
            AuditApproval(
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
        ],
    }


def clean_dataset(period: str = "2026-09") -> AuditDataset:
    """Passing September records only. No planted ground-truth failures."""
    raw = load_dataset(period)
    extra = extra_clean_records()
    vendors = _keep(raw.vendors) + extra["vendors"]
    seen_vendors = {item.vendor_id for item in vendors}
    for item in extra["vendors"]:
        if item.vendor_id not in seen_vendors:
            vendors.append(item)
    invoices = _keep(raw.invoices) + extra["invoices"]
    payments = _keep(raw.payments) + extra["payments"]
    approvals = _keep(raw.approvals) + extra["approvals"]
    return AuditDataset(
        period=raw.period,
        vendors=vendors,
        payments=payments,
        journals=_keep(raw.journals),
        approvals=approvals,
        invoices=invoices,
        decisions=[item for item in raw.decisions if item.object_id not in PLANTED_FAILURE_IDS],
        reconciliations=_keep(raw.reconciliations),
        bank=raw.bank,
        ledger=raw.ledger,
        fees=raw.fees,
        ar_customers=raw.ar_customers,
        ar_invoices=raw.ar_invoices,
        ar_payments=raw.ar_payments,
    )
