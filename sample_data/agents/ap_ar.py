"""AP/AR sample-data agent. Owns vendors, customers, invoices, POs, receipts, payments."""

from __future__ import annotations

import json

from ar.models import ARPrecedent, Customer, CustomerInvoice, CustomerPayment
from models import GoodsReceipt, Invoice, PriorCase, PurchaseOrder, CompanyPolicy

from sample_data.agents.base import SampleDataAgent
from sample_data.context import (
    FIXED_GENERATED_AT,
    REPO_DATA,
    CompanyScenarioContext,
    cents,
    dollars,
)
from sample_data.models import JournalEntryRecord, Product, ScenarioPlan


def _vendor(ctx: CompanyScenarioContext, vendor_id: str, name: str, first_seen: str, *, unusual: bool = False) -> dict:
    row = {"vendor_id": vendor_id, "name": name, "first_seen": first_seen, "unusual": unusual}
    ctx.vendors[vendor_id] = row
    ctx.ids.named(vendor_id)
    return row


def _customer(**kwargs) -> Customer:
    return Customer.model_validate(kwargs)


def _po(ctx, **kwargs) -> PurchaseOrder:
    item = PurchaseOrder.model_validate(kwargs)
    ctx.purchase_orders[item.po_id] = item
    ctx.ids.named(item.po_id)
    return item


def _gr(ctx, **kwargs) -> GoodsReceipt:
    item = GoodsReceipt.model_validate(kwargs)
    ctx.goods_receipts[item.receipt_id] = item
    ctx.ids.named(item.receipt_id)
    return item


def _ap(ctx, **kwargs) -> Invoice:
    item = Invoice.model_validate(kwargs)
    ctx.ap_invoices[item.invoice_id] = item
    ctx.ids.named(item.invoice_id)
    return item


def _ar_inv(ctx, **kwargs) -> CustomerInvoice:
    kwargs.setdefault("created_at", f"{kwargs['invoice_date']}T09:00:00Z")
    kwargs.setdefault("currency", "USD")
    item = CustomerInvoice.model_validate(kwargs)
    ctx.ar_invoices[item.invoice_id] = item
    ctx.ids.named(item.invoice_id)
    return item


def _pay(ctx, **kwargs) -> CustomerPayment:
    kwargs.setdefault("unapplied_amount", kwargs["amount"])
    kwargs.setdefault("application_status", "UNMATCHED")
    kwargs.setdefault("currency", "USD")
    item = CustomerPayment.model_validate(kwargs)
    ctx.ar_payments[item.payment_id] = item
    ctx.ids.named(item.payment_id)
    return item


def _je(
    ctx: CompanyScenarioContext,
    entry_id: str,
    *,
    period: str,
    date: str,
    debit: str,
    credit: str,
    amount_minor: int,
    memo: str,
    source_document_id: str,
    transaction_id: str,
    vendor: str = "",
    customer: str = "",
    product: str = "",
    category: str = "",
    quantity: float | None = None,
    rate: float | None = None,
    entry_type: str = "operating",
    related: list[str] | None = None,
) -> JournalEntryRecord:
    return ctx.add_journal(
        JournalEntryRecord(
            entry_id=entry_id,
            period=period,
            effective_date=date,
            posting_date=date,
            posting_timestamp=f"{date}T12:00:00Z",
            debit_account=debit,
            credit_account=credit,
            amount_minor=amount_minor,
            memo=memo,
            vendor=vendor,
            customer=customer,
            product=product,
            category=category,
            quantity=quantity,
            rate=rate,
            source_document_id=source_document_id,
            transaction_id=transaction_id,
            entry_type=entry_type,
            related_ids=list(related or [source_document_id]),
            evidence_refs=[f"doc:{source_document_id}"],
        )
    )


class APARSampleDataAgent(SampleDataAgent):
    name = "AP/AR Sample Data Agent"
    domain = "ap_ar"

    TEMPLATES = [
        "SCN-AP-001",
        "SCN-AP-002",
        "SCN-AP-003",
        "SCN-AP-004",
        "SCN-AP-005",
        "SCN-AP-006",
        "SCN-AP-007",
        "SCN-AP-008",
        "SCN-AP-009",
        "SCN-AP-010",
        "SCN-AP-011",
        "SCN-AP-012",
        "SCN-AR-001",
        "SCN-AR-002",
        "SCN-AR-003",
        "SCN-AR-004",
        "SCN-AR-005",
        "SCN-AR-006",
        "SCN-AR-007",
        "SCN-AR-008",
        "SCN-AR-009",
        "SCN-AR-010",
        "SCN-AR-011",
        "SCN-AR-012",
    ]

    def plan(self, ctx: CompanyScenarioContext) -> ScenarioPlan:
        return ScenarioPlan(
            agent=self.name,
            selected_templates=list(self.TEMPLATES),
            narrative=(
                "Maximor Demo Corp September books: a clean Acme three-way match "
                "paid this week, a Northline grouped disbursement, and AR that "
                "ages across every bucket including an ambiguous Lumen remittance."
            ),
        )

    def apply(self, ctx: CompanyScenarioContext, plan: ScenarioPlan) -> None:
        self._load_static(ctx)
        self._masters(ctx)
        self._ap_cases(ctx)
        self._cogs_and_revenue(ctx)
        self._ar_cases(ctx)
        self._ingestion(ctx)
        self._accrual_history(ctx)

    def _load_static(self, ctx: CompanyScenarioContext) -> None:
        ctx.policies = [
            CompanyPolicy.model_validate(item)
            for item in json.loads((REPO_DATA / "company_policies.json").read_text())
        ]
        ctx.prior_cases = [
            PriorCase.model_validate(item)
            for item in json.loads((REPO_DATA / "prior_cases.json").read_text())
        ]
        ctx.products = [
            Product(product_id="SKU-PLATFORM", name="Platform", category="subscription"),
            Product(product_id="SKU-USAGE", name="Usage", category="usage"),
            Product(product_id="SKU-SERVICES", name="Services", category="services"),
            Product(product_id="SKU-COMPONENT", name="Components", category="hardware"),
        ]

    def _masters(self, ctx: CompanyScenarioContext) -> None:
        _vendor(ctx, "VEND-001", "Acme Supplies", "2024-01-15")
        _vendor(ctx, "VEND-001-DUP", "Acme Supplies LLC", "2026-09-01")
        _vendor(ctx, "VEND-002", "Amazon Web Services", "2022-01-01")
        _vendor(ctx, "VEND-003", "Northline Fabrication", "2023-04-12")
        _vendor(ctx, "VEND-004", "Office Depot", "2023-02-01")
        _vendor(ctx, "VEND-005", "Helios Hardware", "2023-06-01")
        _vendor(ctx, "VEND-006", "Datadog", "2023-01-01")
        _vendor(ctx, "VEND-007", "Slack Technologies", "2023-01-01")
        _vendor(ctx, "VEND-008", "Figma", "2023-03-01")
        _vendor(ctx, "VEND-009", "Google Cloud", "2022-06-01")
        _vendor(ctx, "VEND-010", "Northwind Phantom LLC", "2026-09-15", unusual=True)
        _vendor(ctx, "VEND-011", "Hartford Insurance", "2022-09-01")
        _vendor(ctx, "VEND-012", "Orbit Analytics", "2024-10-01")
        _vendor(ctx, "VEND-013", "Cambridge Properties", "2021-01-01")
        _vendor(ctx, "VEND-014", "Dell Technologies", "2022-03-01")
        _vendor(ctx, "VEND-015", "Harbor Electric", "2023-01-01")
        _vendor(ctx, "VEND-016", "Lindholm & Ruiz LLP", "2024-04-01")
        _vendor(ctx, "VEND-017", "GitHub", "2022-01-01")
        _vendor(ctx, "VEND-018", "Shadow Vendor LLC", "2025-06-01")
        _vendor(ctx, "VEND-019", "Freightline Logistics", "2023-08-01")
        _vendor(ctx, "VEND-020", "Lenovo", "2024-01-01")
        _vendor(ctx, "VEND-021", "Misc Supplies", "2023-01-01")

        customers = [
            _customer(
                customer_id="CUST-001",
                customer_name="Northwind Labs",
                payment_behavior="on_time",
                on_time_rate=0.98,
                average_days_late=0,
                strategic=True,
                typical_remittance="invoice_number",
                notes="Pays cleanly and names invoice numbers.",
                aliases=["Northwnd Labs", "Northwind Laboratory"],
            ),
            _customer(
                customer_id="CUST-002",
                customer_name="Helios Analytics",
                payment_behavior="chronic_late",
                on_time_rate=0.31,
                average_days_late=24,
                risk_flag="late_payer",
                typical_remittance="purchase_order",
                notes="Late payer; often cites PO numbers.",
                aliases=["Helios Analytic", "Helios Analytics Inc"],
            ),
            _customer(
                customer_id="CUST-003",
                customer_name="Acme Industrial",
                payment_behavior="batch_payer",
                on_time_rate=0.72,
                average_days_late=8,
                strategic=True,
                typical_remittance="batch",
                aliases=["Acme Inc.", "Acme Industrial LLC"],
            ),
            _customer(
                customer_id="CUST-004",
                customer_name="Brightline Media",
                payment_behavior="mixed",
                on_time_rate=0.6,
                average_days_late=12,
                typical_remittance="invoice_number",
            ),
            _customer(
                customer_id="CUST-005",
                customer_name="Quiet Harbor",
                payment_behavior="chronic_late",
                on_time_rate=0.22,
                average_days_late=18,
                risk_flag="collections",
                typical_remittance="none",
            ),
            _customer(
                customer_id="CUST-006",
                customer_name="Pinnacle Retail",
                payment_behavior="partial",
                on_time_rate=0.7,
                average_days_late=5,
                typical_remittance="invoice_number",
            ),
            _customer(
                customer_id="CUST-007",
                customer_name="Atlas Robotics",
                payment_behavior="batch_payer",
                on_time_rate=0.8,
                average_days_late=3,
                typical_remittance="batch",
            ),
            _customer(
                customer_id="CUST-008",
                customer_name="Lumen Labs",
                payment_behavior="mixed",
                on_time_rate=0.65,
                average_days_late=6,
                typical_remittance="none",
                notes="Two open invoices share the same outstanding amount.",
            ),
            _customer(
                customer_id="CUST-009",
                customer_name="Northstar LLC",
                payment_behavior="on_time",
                on_time_rate=0.9,
                average_days_late=0,
                typical_remittance="invoice_number",
            ),
            _customer(
                customer_id="CUST-010",
                customer_name="Meridian Health",
                payment_behavior="mixed",
                on_time_rate=0.55,
                average_days_late=9,
                typical_remittance="none",
            ),
        ]
        for item in customers:
            ctx.customers[item.customer_id] = item
            ctx.ids.named(item.customer_id)

    def _ap_cases(self, ctx: CompanyScenarioContext) -> None:
        # A. Clean three-way match — demo thread 1.
        _po(ctx, po_id="PO-101", vendor="Acme Supplies", authorized_amount=12450.0, description="Office equipment", status="approved", created_date="2026-09-02", approval_limit=25000.0, approver="Jordan Hale")
        _gr(ctx, receipt_id="GR-101", po_id="PO-101", received=True, received_date="2026-09-05", amount_received=12450.0, quantity_ordered=15, quantity_received=15)
        _ap(ctx, invoice_id="INV-001", vendor="Acme Supplies", po_id="PO-101", amount=12450.0, invoice_date="2026-09-08", due_date="2026-09-22", vendor_invoice_number="ACM-2026-4410", description="Standing desks and monitors", payment_terms="2/10 net 30", early_payment_discount_percent=2, early_payment_discount_deadline="2026-09-18", late_fee_percent=1.5, vendor_priority="normal")
        _je(ctx, "JE-AP-INV-001", period="2026-09", date="2026-09-08", debit="6000-Operating", credit="2000-AP", amount_minor=1_245_000, memo="Acme supplies invoice", source_document_id="INV-001", transaction_id="TXN-AP-INV-001", vendor="Acme Supplies", category="opex", entry_type="ap_invoice")
        ctx.plant("SCN-AP-001", ["INV-001", "PO-101", "GR-101", "JE-AP-INV-001"], storyline="STORY-CLEAN")

        # Eligible this week (AWS).
        _po(ctx, po_id="PO-102", vendor="Amazon Web Services", authorized_amount=8320.0, description="September AWS usage", status="approved", created_date="2026-09-01", approval_limit=20000.0, approver="Priya Nair")
        _gr(ctx, receipt_id="GR-102", po_id="PO-102", received=True, received_date="2026-09-01", amount_received=8320.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-002", vendor="Amazon Web Services", po_id="PO-102", amount=8320.0, invoice_date="2026-09-05", due_date="2026-09-22", vendor_invoice_number="AWS-3844-2910", description="September compute", payment_terms="net 30", vendor_priority="high")
        _je(ctx, "JE-AP-INV-002", period="2026-09", date="2026-09-05", debit="6000-Operating", credit="2000-AP", amount_minor=832_000, memo="AWS September invoice", source_document_id="INV-002", transaction_id="TXN-AP-INV-002", vendor="Amazon Web Services", category="opex", entry_type="ap_invoice")
        ctx.plant("SCN-AP-009", ["INV-002", "PO-102"], storyline="STORY-CLEAN")

        # B. Quantity mismatch — Datadog billed 50 hosts, 40 received.
        _po(ctx, po_id="PO-103", vendor="Datadog", authorized_amount=15000.0, description="Monitoring 50 hosts", status="approved", created_date="2026-09-01", approval_limit=25000.0, approver="Marcus Chen")
        _gr(ctx, receipt_id="GR-103", po_id="PO-103", received=True, received_date="2026-09-02", amount_received=12000.0, quantity_ordered=50, quantity_received=40)
        _ap(ctx, invoice_id="INV-003", vendor="Datadog", po_id="PO-103", amount=15000.0, invoice_date="2026-09-03", due_date="2026-10-03", vendor_invoice_number="DD-INV-90211", description="Pro monitoring 50 hosts", payment_terms="net 30", vendor_priority="high")
        _je(ctx, "JE-AP-INV-003", period="2026-09", date="2026-09-03", debit="6000-Operating", credit="2000-AP", amount_minor=1_500_000, memo="Datadog invoice pending receipt", source_document_id="INV-003", transaction_id="TXN-AP-INV-003", vendor="Datadog", category="opex")
        ctx.plant("SCN-AP-002", ["INV-003", "PO-103", "GR-103"])

        # C. Price mismatch — Slack billed above PO.
        _po(ctx, po_id="PO-105", vendor="Slack Technologies", authorized_amount=4375.0, description="Business+ 50 users", status="approved", created_date="2026-09-01", approval_limit=10000.0, approver="Elena Vasquez")
        _gr(ctx, receipt_id="GR-105", po_id="PO-105", received=True, received_date="2026-09-02", amount_received=4375.0, quantity_ordered=50, quantity_received=50)
        _ap(ctx, invoice_id="INV-004", vendor="Slack Technologies", po_id="PO-105", amount=5000.0, invoice_date="2026-09-04", due_date="2026-10-04", vendor_invoice_number="SLK-BUS-50-0926", description="Business+ billed above PO", payment_terms="net 30")
        _je(ctx, "JE-AP-INV-004", period="2026-09", date="2026-09-04", debit="6000-Operating", credit="2000-AP", amount_minor=500_000, memo="Slack price exception", source_document_id="INV-004", transaction_id="TXN-AP-INV-004", vendor="Slack Technologies", category="opex")
        ctx.plant("SCN-AP-003", ["INV-004", "PO-105", "GR-105"])

        # D. Missing goods receipt.
        _po(ctx, po_id="PO-108", vendor="Figma", authorized_amount=4375.0, description="Organization seats", status="approved", created_date="2026-09-01", approval_limit=10000.0, approver="Priya Nair")
        _ap(ctx, invoice_id="INV-005", vendor="Figma", po_id="PO-108", amount=4375.0, invoice_date="2026-09-06", due_date="2026-10-06", vendor_invoice_number="FIG-ORG-0926", description="Figma org seats — receipt missing")
        _je(ctx, "JE-AP-INV-005", period="2026-09", date="2026-09-06", debit="6000-Operating", credit="2000-AP", amount_minor=437_500, memo="Figma invoice without receipt", source_document_id="INV-005", transaction_id="TXN-AP-INV-005", vendor="Figma", category="opex")
        ctx.plant("SCN-AP-004", ["INV-005", "PO-108"])

        # E. Duplicate invoice number.
        _po(ctx, po_id="PO-118", vendor="Shadow Vendor LLC", authorized_amount=8750.0, description="Shadow consulting", status="approved", created_date="2026-09-10", approval_limit=20000.0, approver="Jordan Hale")
        _gr(ctx, receipt_id="GR-118", po_id="PO-118", received=True, received_date="2026-09-12", amount_received=8750.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-006", vendor="Shadow Vendor LLC", po_id="PO-118", amount=8750.0, invoice_date="2026-09-16", due_date="2026-10-16", vendor_invoice_number="SV-999001", description="Shadow consulting original")
        _ap(ctx, invoice_id="INV-007", vendor="Shadow Vendor LLC", po_id="PO-118", amount=8750.0, invoice_date="2026-09-16", due_date="2026-10-16", vendor_invoice_number="SV-999001", description="Shadow consulting duplicate submission")
        _je(ctx, "JE-AP-INV-006", period="2026-09", date="2026-09-16", debit="6000-Operating", credit="2000-AP", amount_minor=875_000, memo="Shadow vendor original", source_document_id="INV-006", transaction_id="TXN-AP-INV-006", vendor="Shadow Vendor LLC", category="opex")
        ctx.plant("SCN-AP-005", ["INV-006", "INV-007"], storyline="STORY-RESOLVED")

        # F. Invoice requiring approval (PO pending).
        _po(ctx, po_id="PO-116", vendor="GitHub", authorized_amount=21000.0, description="Enterprise seats", status="pending", created_date="2026-09-12", approval_limit=25000.0, approver="Marcus Chen")
        _ap(ctx, invoice_id="INV-008", vendor="GitHub", po_id="PO-116", amount=21000.0, invoice_date="2026-09-14", due_date="2026-10-14", vendor_invoice_number="GH-ENT-0926", description="GitHub enterprise — PO pending")
        ctx.plant("SCN-AP-006", ["INV-008", "PO-116"])

        # G. Exceeds approval threshold.
        _po(ctx, po_id="PO-109", vendor="Northwind Phantom LLC", authorized_amount=50000.0, description="Manual new-vendor engagement", status="approved", created_date="2026-09-18", approval_limit=10000.0, approver="USR-PREP-02")
        _gr(ctx, receipt_id="GR-109", po_id="PO-109", received=True, received_date="2026-09-18", amount_received=50000.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-009", vendor="Northwind Phantom LLC", po_id="PO-109", amount=50000.0, invoice_date="2026-09-19", due_date="2026-09-20", vendor_invoice_number="NWP-50000", description="Round-number new vendor invoice")
        _je(ctx, "JE-AP-INV-009", period="2026-09", date="2026-09-19", debit="6000-Operating", credit="2000-AP", amount_minor=5_000_000, memo="Phantom vendor invoice", source_document_id="INV-009", transaction_id="TXN-AP-INV-009", vendor="Northwind Phantom LLC", category="opex")
        ctx.plant("SCN-AP-007", ["INV-009", "PO-109"])

        # H. On hold (goods not received) — later paid anyway for audit.
        _po(ctx, po_id="PO-110", vendor="Office Depot", authorized_amount=3280.0, description="Task chairs not received", status="approved", created_date="2026-09-04", approval_limit=10000.0, approver="Elena Vasquez")
        _gr(ctx, receipt_id="GR-110", po_id="PO-110", received=False, received_date=None, amount_received=0.0, quantity_ordered=8, quantity_received=0)
        _ap(ctx, invoice_id="INV-010", vendor="Office Depot", po_id="PO-110", amount=3280.0, invoice_date="2026-09-10", due_date="2026-09-24", vendor_invoice_number="OD-HOLD-9912", description="Chairs not received — must hold")
        ctx.plant("SCN-AP-008", ["INV-010", "PO-110", "GR-110"], storyline="STORY-UNRESOLVED")

        # J. Not yet due.
        _po(ctx, po_id="PO-112", vendor="GitHub", authorized_amount=21000.0, description="Actions minutes", status="approved", created_date="2026-09-01", approval_limit=25000.0, approver="Marcus Chen")
        _gr(ctx, receipt_id="GR-112", po_id="PO-112", received=True, received_date="2026-09-01", amount_received=21000.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-012", vendor="GitHub", po_id="PO-112", amount=21000.0, invoice_date="2026-09-02", due_date="2026-10-02", vendor_invoice_number="GH-ACT-1002", description="GitHub actions — not yet due", vendor_priority="high")
        _je(ctx, "JE-AP-INV-012", period="2026-09", date="2026-09-02", debit="6000-Operating", credit="2000-AP", amount_minor=2_100_000, memo="GitHub not yet due", source_document_id="INV-012", transaction_id="TXN-AP-INV-012", vendor="GitHub", category="opex")
        ctx.plant("SCN-AP-010", ["INV-012"])

        # K. Early-payment discount still open as of 2026-09-19.
        _po(ctx, po_id="PO-104", vendor="Office Depot", authorized_amount=2100.0, description="Toner and paper", status="approved", created_date="2026-09-12", approval_limit=10000.0, approver="Elena Vasquez")
        _gr(ctx, receipt_id="GR-104", po_id="PO-104", received=True, received_date="2026-09-13", amount_received=2100.0, quantity_ordered=10, quantity_received=10)
        _ap(ctx, invoice_id="INV-013", vendor="Office Depot", po_id="PO-104", amount=2100.0, invoice_date="2026-09-14", due_date="2026-10-14", vendor_invoice_number="OD-DISC-2100", description="Supplies with 2/10 discount", payment_terms="2/10 net 30", early_payment_discount_percent=2, early_payment_discount_deadline="2026-09-24")
        _je(ctx, "JE-AP-INV-013", period="2026-09", date="2026-09-14", debit="6000-Operating", credit="2000-AP", amount_minor=210_000, memo="Office Depot discount window", source_document_id="INV-013", transaction_id="TXN-AP-INV-013", vendor="Office Depot", category="opex")
        ctx.plant("SCN-AP-011", ["INV-013"])

        # Northline three invoices — grouped ACH in cash agent.
        for po_id, inv_id, gr_id, amount, vin, day in [
            ("PO-201", "INV-014", "GR-201", 5000.0, "NF-201", "2026-09-04"),
            ("PO-202", "INV-015", "GR-202", 7500.0, "NF-202", "2026-09-05"),
            ("PO-203", "INV-016", "GR-203", 6000.0, "NF-203", "2026-09-06"),
        ]:
            _po(ctx, po_id=po_id, vendor="Northline Fabrication", authorized_amount=amount, description=f"Fabrication {vin}", status="approved", created_date="2026-09-01", approval_limit=20000.0, approver="Jordan Hale")
            _gr(ctx, receipt_id=gr_id, po_id=po_id, received=True, received_date=day, amount_received=amount, quantity_ordered=1, quantity_received=1)
            _ap(ctx, invoice_id=inv_id, vendor="Northline Fabrication", po_id=po_id, amount=amount, invoice_date=day, due_date="2026-09-20", vendor_invoice_number=vin, description=f"Northline {vin}")
            _je(ctx, f"JE-AP-{inv_id}", period="2026-09", date=day, debit="6000-Operating", credit="2000-AP", amount_minor=cents(amount), memo=f"Northline {inv_id}", source_document_id=inv_id, transaction_id=f"TXN-AP-{inv_id}", vendor="Northline Fabrication", category="opex")

        # Helios hardware wire (fee-netted AP payment).
        _po(ctx, po_id="PO-205", vendor="Helios Hardware", authorized_amount=10000.0, description="Lab controllers", status="approved", created_date="2026-09-01", approval_limit=20000.0, approver="Priya Nair")
        _gr(ctx, receipt_id="GR-205", po_id="PO-205", received=True, received_date="2026-09-08", amount_received=10000.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-017", vendor="Helios Hardware", po_id="PO-205", amount=10000.0, invoice_date="2026-09-08", due_date="2026-09-18", vendor_invoice_number="HEL-WIRE-10000", description="Lab controllers")
        _je(ctx, "JE-AP-INV-017", period="2026-09", date="2026-09-08", debit="6000-Operating", credit="2000-AP", amount_minor=1_000_000, memo="Helios hardware", source_document_id="INV-017", transaction_id="TXN-AP-INV-017", vendor="Helios Hardware", category="opex", entry_type="ap_invoice")

        # Dell capital invoice.
        _po(ctx, po_id="PO-221", vendor="Dell Technologies", authorized_amount=60000.0, description="PowerEdge R760 cluster", status="approved", created_date="2026-09-01", approval_limit=100000.0, approver="Marcus Chen")
        _gr(ctx, receipt_id="GR-221", po_id="PO-221", received=True, received_date="2026-09-04", amount_received=60000.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-018", vendor="Dell Technologies", po_id="PO-221", amount=60000.0, invoice_date="2026-09-05", due_date="2026-10-05", vendor_invoice_number="DELL-R760-60K", description="PowerEdge R760 server cluster")
        _je(ctx, "JE-AP-INV-018", period="2026-09", date="2026-09-05", debit="Computer Equipment", credit="2000-AP", amount_minor=6_000_000, memo="Dell server cluster", source_document_id="INV-018", transaction_id="TXN-AP-INV-018", vendor="Dell Technologies", category="capex", entry_type="capital")

        # Hartford prepaid insurance invoice.
        _po(ctx, po_id="PO-INS", vendor="Hartford Insurance", authorized_amount=12000.0, description="Annual policy", status="approved", created_date="2026-08-20", approval_limit=25000.0, approver="Jordan Hale")
        _gr(ctx, receipt_id="GR-INS", po_id="PO-INS", received=True, received_date="2026-09-01", amount_received=12000.0, quantity_ordered=1, quantity_received=1)
        _ap(ctx, invoice_id="INV-019", vendor="Hartford Insurance", po_id="PO-INS", amount=12000.0, invoice_date="2026-09-01", due_date="2026-09-15", vendor_invoice_number="HART-ANN-2026", description="Annual commercial policy")
        _je(ctx, "JE-AP-INV-019", period="2026-09", date="2026-09-01", debit="Prepaid Insurance", credit="2000-AP", amount_minor=1_200_000, memo="Prepaid insurance", source_document_id="INV-019", transaction_id="TXN-AP-INV-019", vendor="Hartford Insurance", category="prepaid")

        # Orbit prepaid software (already paid last year conceptually — still a source doc).
        _ap(ctx, invoice_id="INV-020", vendor="Orbit Analytics", po_id=None, amount=24000.0, invoice_date="2025-10-01", due_date="2025-10-15", vendor_invoice_number="OA-ANN-2025", description="Analytics platform annual")

        ctx.approved_pool = [
            {"invoice_id": "INV-001", "vendor": "Acme Supplies", "amount": 12450.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-002", "vendor": "Amazon Web Services", "amount": 8320.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-012", "vendor": "GitHub", "amount": 21000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-013", "vendor": "Office Depot", "amount": 2100.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-014", "vendor": "Northline Fabrication", "amount": 5000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-015", "vendor": "Northline Fabrication", "amount": 7500.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-016", "vendor": "Northline Fabrication", "amount": 6000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-017", "vendor": "Helios Hardware", "amount": 10000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-018", "vendor": "Dell Technologies", "amount": 60000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
            {"invoice_id": "INV-019", "vendor": "Hartford Insurance", "amount": 12000.0, "approval_source": "ap_policy", "added_at": FIXED_GENERATED_AT},
        ]

    def _cogs_and_revenue(self, ctx: CompanyScenarioContext) -> None:
        """Transaction-level P&L causes. August GM 64%, September GM 61%."""
        # August revenue $1,000,000 and COGS $360,000.
        revenue_aug = [
            ("INV-AR-AUG-001", "CUST-001", "Northwind Labs", "TXN-REV-AUG-001", 40_000_000, "2026-08-15", "Platform", "August platform subscriptions"),
            ("INV-AR-AUG-002", "CUST-002", "Helios Analytics", "TXN-REV-AUG-002", 35_000_000, "2026-08-20", "Usage", "August usage"),
            ("INV-AR-AUG-003", "CUST-003", "Acme Industrial", "TXN-REV-AUG-003", 25_000_000, "2026-08-28", "Services", "August professional services"),
        ]
        for invoice_id, cust_id, name, txn, amount_minor, day, product, memo in revenue_aug:
            _ar_inv(
                ctx,
                invoice_id=invoice_id,
                customer_id=cust_id,
                customer_name=name,
                invoice_date=day,
                due_date="2026-09-15" if cust_id != "CUST-001" else "2026-08-31",
                original_amount=dollars(amount_minor),
                outstanding_amount=0.0,
                status="PAID",
                description=memo,
                last_payment_date=day,
            )
            _je(ctx, f"JE-{txn}", period="2026-08", date=day, debit="1100-AR", credit="4000-Revenue", amount_minor=amount_minor, memo=memo, source_document_id=invoice_id, transaction_id=txn, customer=name, product=product, category="revenue", entry_type="ar_invoice")

        from sample_data.pnl import COGS_FACTS

        for fact in COGS_FACTS:
            invoice_date = "2026-08-28" if fact.period == "2026-08" else "2026-09-28"
            due_date = "2026-09-15" if fact.period == "2026-08" else "2026-10-15"
            _ap(
                ctx,
                invoice_id=fact.invoice_id,
                vendor=fact.vendor,
                po_id=None,
                amount=dollars(fact.amount_minor),
                invoice_date=invoice_date,
                due_date=due_date,
                vendor_invoice_number=f"{fact.invoice_id}-VIN",
                description=fact.memo,
            )
            _je(
                ctx,
                f"JE-{fact.transaction_id}",
                period=fact.period,
                date=fact.date,
                debit=fact.account,
                credit="2000-AP",
                amount_minor=fact.amount_minor,
                memo=fact.memo,
                source_document_id=fact.invoice_id,
                transaction_id=fact.transaction_id,
                vendor=fact.vendor,
                category=fact.category,
                quantity=fact.quantity,
                rate=fact.rate,
                product="Components" if fact.category == "supplier" else "",
                entry_type="ap_invoice",
            )

        # September revenue $1,000,000. Platform discounted $20k vs August; mix shifts to usage.
        revenue_sep = [
            ("INV-AR-SEP-001", "CUST-001", "Northwind Labs", "TXN-REV-SEP-001", 36_760_000, "2026-09-15", "Platform", "September platform after discount"),
            ("INV-AR-SEP-002", "CUST-002", "Helios Analytics", "TXN-REV-SEP-002", 37_000_000, "2026-09-20", "Usage", "September usage (mix shift)"),
            ("INV-AR-SEP-003", "CUST-003", "Acme Industrial", "TXN-REV-SEP-003", 25_000_000, "2026-09-28", "Services", "September professional services"),
        ]
        for invoice_id, cust_id, name, txn, amount_minor, day, product, memo in revenue_sep:
            outstanding = dollars(amount_minor) if invoice_id != "INV-AR-SEP-001" else dollars(amount_minor)
            _ar_inv(
                ctx,
                invoice_id=invoice_id,
                customer_id=cust_id,
                customer_name=name,
                invoice_date=day,
                due_date="2026-10-15",
                original_amount=dollars(amount_minor),
                outstanding_amount=outstanding,
                status="OPEN",
                description=memo,
            )
            _je(ctx, f"JE-{txn}", period="2026-09", date=day, debit="1100-AR", credit="4000-Revenue", amount_minor=amount_minor, memo=memo, source_document_id=invoice_id, transaction_id=txn, customer=name, product=product, category="revenue", entry_type="ar_invoice")

        # Operating expenses (do not change GM).
        _je(ctx, "JE-OPEX-AUG-PAY", period="2026-08", date="2026-08-28", debit="6100-Payroll", credit="1000-Cash", amount_minor=14_000_000, memo="August payroll", source_document_id="PR-2026-08-28", transaction_id="TXN-PAY-AUG", category="payroll", entry_type="payroll")
        _je(ctx, "JE-OPEX-SEP-PAY", period="2026-09", date="2026-09-25", debit="6100-Payroll", credit="1000-Cash", amount_minor=14_000_000, memo="September payroll", source_document_id="PR-2026-09-25", transaction_id="TXN-PAY-SEP", category="payroll", entry_type="payroll")

    def _ar_cases(self, ctx: CompanyScenarioContext) -> None:
        _ar_inv(ctx, invoice_id="INV-AR-001", customer_id="CUST-001", customer_name="Northwind Labs", invoice_date="2026-09-15", due_date="2026-10-15", original_amount=12000.0, outstanding_amount=12000.0, status="OPEN", purchase_order="PO-NW-4401", description="September add-on seats")
        ctx.plant("SCN-AR-001", ["INV-AR-001"])

        _ar_inv(ctx, invoice_id="INV-AR-002", customer_id="CUST-003", customer_name="Acme Industrial", invoice_date="2026-08-11", due_date="2026-09-10", original_amount=8500.0, outstanding_amount=8500.0, status="PAST_DUE", description="August hardware — 1-30 overdue")
        ctx.plant("SCN-AR-002", ["INV-AR-002"])

        _ar_inv(ctx, invoice_id="INV-AR-003", customer_id="CUST-002", customer_name="Helios Analytics", invoice_date="2026-07-21", due_date="2026-08-20", original_amount=24000.0, outstanding_amount=24000.0, status="PAST_DUE", purchase_order="PO-HEL-8821", description="Implementation — 31-60 overdue")
        ctx.plant("SCN-AR-003", ["INV-AR-003"])

        _ar_inv(ctx, invoice_id="INV-AR-004", customer_id="CUST-004", customer_name="Brightline Media", invoice_date="2026-06-15", due_date="2026-07-15", original_amount=31000.0, outstanding_amount=31000.0, status="PAST_DUE", description="Campaign fees — 61-90 overdue")
        ctx.plant("SCN-AR-004", ["INV-AR-004"])

        _ar_inv(ctx, invoice_id="INV-AR-005", customer_id="CUST-005", customer_name="Quiet Harbor", invoice_date="2026-04-01", due_date="2026-05-01", original_amount=45000.0, outstanding_amount=45000.0, status="PAST_DUE", description="Platform arrears — 90+ overdue", reminder_count=3, collection_status="REMINDED", last_collection_contact="2026-09-01")
        ctx.plant("SCN-AR-005", ["INV-AR-005"])
        ctx.plant("SCN-AR-012", ["INV-AR-005", "CUST-005"])

        _ar_inv(ctx, invoice_id="INV-AR-006", customer_id="CUST-006", customer_name="Pinnacle Retail", invoice_date="2026-09-01", due_date="2026-10-01", original_amount=10000.0, outstanding_amount=10000.0, status="OPEN", description="Store rollout")
        _pay(ctx, payment_id="PAY-002", payment_date="2026-09-27", amount=4000.0, payer_name="Pinnacle Retail", customer_id="CUST-006", bank_reference="ACH-PIN-4K", remittance_text="Partial INV-AR-006 store rollout", invoice_reference="INV-AR-006", source="ach")
        ctx.plant("SCN-AR-006", ["INV-AR-006", "PAY-002"])

        _ar_inv(ctx, invoice_id="INV-AR-007", customer_id="CUST-001", customer_name="Northwind Labs", invoice_date="2026-09-01", due_date="2026-09-30", original_amount=12000.0, outstanding_amount=12000.0, status="OPEN", description="Named exact-pay invoice")
        _pay(ctx, payment_id="PAY-001", payment_date="2026-09-29", amount=12000.0, payer_name="Northwind Labs", customer_id="CUST-001", bank_reference="WIRE-NW-9921", remittance_text="Payment for INV-AR-007 September platform", invoice_reference="INV-AR-007", source="wire")
        ctx.plant("SCN-AR-007", ["INV-AR-007", "PAY-001"], storyline="STORY-CLEAN")

        _ar_inv(ctx, invoice_id="INV-AR-008", customer_id="CUST-007", customer_name="Atlas Robotics", invoice_date="2026-09-05", due_date="2026-10-05", original_amount=15000.0, outstanding_amount=15000.0, status="OPEN", description="Atlas license")
        _ar_inv(ctx, invoice_id="INV-AR-009", customer_id="CUST-007", customer_name="Atlas Robotics", invoice_date="2026-09-08", due_date="2026-10-08", original_amount=22400.0, outstanding_amount=22400.0, status="OPEN", description="Atlas implementation")
        _pay(ctx, payment_id="PAY-003", payment_date="2026-09-28", amount=37400.0, payer_name="Atlas Robotics", customer_id="CUST-007", bank_reference="WIRE-ATL-374", remittance_text="INV-AR-008 and INV-AR-009", invoice_reference="INV-AR-008,INV-AR-009", source="wire")
        ctx.plant("SCN-AR-008", ["INV-AR-008", "INV-AR-009", "PAY-003"])

        _ar_inv(ctx, invoice_id="INV-AR-010", customer_id="CUST-008", customer_name="Lumen Labs", invoice_date="2026-09-01", due_date="2026-10-01", original_amount=5000.0, outstanding_amount=5000.0, status="OPEN", description="Seat block A")
        _ar_inv(ctx, invoice_id="INV-AR-011", customer_id="CUST-008", customer_name="Lumen Labs", invoice_date="2026-09-03", due_date="2026-10-03", original_amount=5000.0, outstanding_amount=5000.0, status="OPEN", description="Seat block B")
        _pay(ctx, payment_id="PAY-004", payment_date="2026-09-26", amount=5000.0, payer_name="Lumen Labs", customer_id="CUST-008", bank_reference="ACH-LUMEN-5K", remittance_text="September billing", source="ach")
        ctx.plant("SCN-AR-009", ["INV-AR-010", "INV-AR-011", "PAY-004"], storyline="STORY-UNRESOLVED")
        ctx.plant("SCN-AR-011", ["INV-AR-010", "INV-AR-011", "PAY-004"])

        _ar_inv(ctx, invoice_id="INV-AR-012", customer_id="CUST-010", customer_name="Meridian Health", invoice_date="2026-09-10", due_date="2026-10-10", original_amount=3200.0, outstanding_amount=3200.0, status="OPEN", description="Quiet ops invoice")
        _pay(ctx, payment_id="PAY-005", payment_date="2026-09-29", amount=3200.0, payer_name="Quiet Harbor", bank_reference="ACH-QH-3200", remittance_text="September ops", source="ach")
        ctx.plant("SCN-AR-010", ["PAY-005", "INV-AR-012"])

        _ar_inv(ctx, invoice_id="INV-AR-013", customer_id="CUST-009", customer_name="Northstar LLC", invoice_date="2026-09-01", due_date="2026-09-30", original_amount=12400.0, outstanding_amount=12400.0, status="OPEN", description="Northstar platform")
        _pay(ctx, payment_id="PAY-006", payment_date="2026-09-15", amount=12412.4, payer_name="Northstar LLC", customer_id="CUST-009", bank_reference="WIRE-NS-12412", remittance_text="Northstar platform", invoice_reference="INV-AR-013", source="wire")

        _ar_inv(ctx, invoice_id="INV-AR-014", customer_id="CUST-005", customer_name="Quiet Harbor", invoice_date="2026-09-18", due_date="2026-10-02", original_amount=25000.0, outstanding_amount=25000.0, status="OPEN", description="Forecasted collection that will arrive late")

        _je(ctx, "JE-AR-INV-AR-013", period="2026-09", date="2026-09-01", debit="1100-AR", credit="4000-Revenue", amount_minor=1_240_000, memo="Northstar platform", source_document_id="INV-AR-013", transaction_id="TXN-AR-013", customer="Northstar LLC", product="Platform", category="revenue", entry_type="ar_invoice")
        ctx.ar_precedents = [
            ARPrecedent(precedent_id="AR-PREC-001", customer_id="CUST-007", kind="batch_payment", summary="Atlas commonly pays several invoices in one wire.", facts={"typical_remittance": "batch"}),
            ARPrecedent(precedent_id="AR-PREC-002", customer_id="CUST-008", kind="ambiguous_amount", summary="Lumen often has two invoices with the same outstanding.", facts={"same_amount": True}),
        ]

    def _ingestion(self, ctx: CompanyScenarioContext) -> None:
        ctx.ingestion_emails = [
            {
                "message_id": "MSG-E-INV-001",
                "period": ctx.period,
                "from": "billing@acmesupplies.example",
                "to": "ap@maximor.example",
                "subject": "Invoice ACM-2026-4410 from Acme Supplies",
                "sent_at": "2026-09-08T10:00:00Z",
                "body": "Please find invoice ACM-2026-4410 for $12,450.00. PO-101.",
                "attachments": [{"attachment_id": "ATT-E-001", "filename": "ACM-2026-4410.pdf", "content_type": "application/pdf", "text": "INVOICE ACM-2026-4410\nVendor: Acme Supplies\nAmount: 12450.00\nPO: PO-101"}],
            },
            {
                "message_id": "MSG-E-QUOTE",
                "period": ctx.period,
                "from": "sales@acmesupplies.example",
                "to": "ap@maximor.example",
                "subject": "Quote Q-8891 for additional standing desks",
                "sent_at": "2026-09-09T11:40:00Z",
                "body": "This is a quotation, not a request for payment until you issue a PO.",
                "attachments": [{"attachment_id": "ATT-E-QUOTE", "filename": "Q-8891-quote.pdf", "content_type": "application/pdf", "text": "QUOTATION Q-8891\nNot an invoice."}],
            },
            {
                "message_id": "MSG-E-STMT",
                "period": ctx.period,
                "from": "ar@office.example",
                "to": "ap@maximor.example",
                "subject": "Account statement September 2026",
                "sent_at": "2026-09-30T08:00:00Z",
                "body": "Attached is your monthly statement of open items. This is not an invoice.",
                "attachments": [{"attachment_id": "ATT-E-STMT", "filename": "statement-sep.pdf", "content_type": "application/pdf", "text": "STATEMENT of account. Balance brought forward. Not an invoice."}],
            },
            {
                "message_id": "MSG-E-RCPT",
                "period": ctx.period,
                "from": "expenses@maximor.example",
                "to": "ap@maximor.example",
                "subject": "Uber receipt for campus visit",
                "sent_at": "2026-09-12T18:00:00Z",
                "body": "Receipt for $42.10. This is a payment confirmation / receipt, not a vendor invoice.",
                "attachments": [{"attachment_id": "ATT-E-RCPT", "filename": "uber-receipt.pdf", "content_type": "application/pdf", "text": "RECEIPT. Paid. Thank you. Not an invoice."}],
            },
            {
                "message_id": "MSG-E-MKT",
                "period": ctx.period,
                "from": "news@slack.com",
                "to": "ap@maximor.example",
                "subject": "New Slack AI features — limited time",
                "sent_at": "2026-09-08T16:02:00Z",
                "body": "Upgrade your workspace with Slack AI. Unsubscribe anytime. This newsletter is not an invoice.",
                "attachments": [],
            },
            {
                "message_id": "MSG-E-PO",
                "period": ctx.period,
                "from": "procurement@maximor.example",
                "to": "ap@maximor.example",
                "subject": "PO-101 issued to Acme Supplies",
                "sent_at": "2026-09-02T09:00:00Z",
                "body": "Purchase order PO-101 has been issued. This is a PO, not a vendor invoice.",
                "attachments": [{"attachment_id": "ATT-E-PO", "filename": "PO-101.pdf", "content_type": "application/pdf", "text": "PURCHASE ORDER PO-101\nAcme Supplies\nAuthorized 12450.00"}],
            },
        ]
        ctx.ingestion_documents = [
            {
                "document_id": "DOC-SCAN-QUOTE",
                "period": ctx.period,
                "origin": "mailroom_scan",
                "filename": "quote-q8891.pdf",
                "content_type": "application/pdf",
                "text": "QUOTATION Q-8891. This is not an invoice.",
                "received_date": "2026-09-09",
            }
        ]
        ctx.plant("SCN-AP-012", ["MSG-E-QUOTE", "MSG-E-STMT", "MSG-E-RCPT", "MSG-E-MKT", "MSG-E-PO"])

    def _accrual_history(self, ctx: CompanyScenarioContext) -> None:
        from accrual.models import AccrualInvoice, VendorContract

        for month, amount in [("2026-04", 4700.0), ("2026-05", 4750.0), ("2026-06", 4780.0), ("2026-07", 4720.0), ("2026-08", 4800.0)]:
            ctx.historical_invoices.append(
                AccrualInvoice(
                    invoice_id=f"HI-HE-{month}",
                    vendor="Harbor Electric",
                    amount=amount,
                    invoice_date=f"{month}-28" if month != "2026-04" else "2026-05-02",
                    service_period=month,
                    expense_account="Utilities Expense",
                    vendor_invoice_number=f"HE-{month}",
                    description=f"Electricity {month}",
                )
            )
        for month, amount in [("2026-04", 8500.0), ("2026-05", 8500.0), ("2026-06", 8500.0), ("2026-07", 8600.0), ("2026-08", 8550.0)]:
            ctx.historical_invoices.append(
                AccrualInvoice(
                    invoice_id=f"HI-LR-{month}",
                    vendor="Lindholm & Ruiz LLP",
                    amount=amount,
                    invoice_date=f"{month[:7]}-05".replace("2026-04", "2026-05") if False else f"{int(month[5:7]) + 1:02d}",
                    service_period=month,
                    expense_account="Legal Expense",
                    vendor_invoice_number=f"LR-{month}",
                    description=f"Retainer {month}",
                )
            )
        # Fix legal invoice dates properly.
        ctx.historical_invoices = [item for item in ctx.historical_invoices if not item.invoice_id.startswith("HI-LR-")]
        follow = {"2026-04": "2026-05-05", "2026-05": "2026-06-05", "2026-06": "2026-07-05", "2026-07": "2026-08-05", "2026-08": "2026-09-05"}
        amounts = {"2026-04": 8500.0, "2026-05": 8500.0, "2026-06": 8500.0, "2026-07": 8600.0, "2026-08": 8550.0}
        for month, amount in amounts.items():
            ctx.historical_invoices.append(
                AccrualInvoice(
                    invoice_id=f"HI-LR-{month}",
                    vendor="Lindholm & Ruiz LLP",
                    amount=amount,
                    invoice_date=follow[month],
                    service_period=month,
                    expense_account="Legal Expense",
                    vendor_invoice_number=f"LR-{month}",
                    description=f"Retainer {month}",
                )
            )
        ctx.vendor_contracts = [
            VendorContract(
                contract_id="CTR-HE-001",
                vendor="Harbor Electric",
                start_date="2026-01-01",
                end_date="2026-12-31",
                billing_cadence="monthly",
                amount=4750.0,
                expense_account="Utilities Expense",
                billed_in_arrears=True,
                monthly_minimum=4500.0,
                description="Cambridge campus electricity billed in arrears.",
            ),
            VendorContract(
                contract_id="CTR-LR-001",
                vendor="Lindholm & Ruiz LLP",
                start_date="2026-04-01",
                end_date="2027-03-31",
                billing_cadence="monthly",
                amount=8500.0,
                expense_account="Legal Expense",
                billed_in_arrears=True,
                monthly_minimum=8500.0,
                description="General-counsel retainer billed in arrears.",
            ),
        ]
        ctx.later_invoices = [
            AccrualInvoice(
                invoice_id="INV-HE-2026-09",
                vendor="Harbor Electric",
                amount=4780.0,
                invoice_date="2026-10-04",
                service_period="2026-09",
                expense_account="Utilities Expense",
                vendor_invoice_number="HE-2026-09",
                description="September electricity — arrived in October",
            ),
            AccrualInvoice(
                invoice_id="INV-LR-2026-09",
                vendor="Lindholm & Ruiz LLP",
                amount=8500.0,
                invoice_date="2026-10-05",
                service_period="2026-09",
                expense_account="Legal Expense",
                vendor_invoice_number="LR-2026-09",
                description="September retainer — arrived in October",
            ),
        ]
