"""Demo P&L and cash scenario. Variances are derived from these lines, not stored."""

from __future__ import annotations

import json

from reporting import ledger as reporting_ledger
from reporting.ledger import post_line, reset_ledger
from reporting.models import ReportingLine


def _line(**kwargs) -> ReportingLine:
    kwargs.setdefault("line_id", kwargs["transaction_id"] + "-" + kwargs["account"][:4])
    kwargs.setdefault("entry_id", kwargs["transaction_id"])
    kwargs.setdefault("ledger_entry_id", kwargs["transaction_id"])
    kwargs.setdefault("idempotency_key", kwargs["line_id"])
    kwargs.setdefault("source_workflow", "reporting")
    kwargs.setdefault("evidence_refs", [f"txn:{kwargs['transaction_id']}"])
    return ReportingLine.model_validate(kwargs)


def seed_demo_ledger() -> list[ReportingLine]:
    """August 64% GM / September 61% GM with identifiable COGS transactions."""
    reset_ledger()
    generated = reporting_ledger.DATA_REPORTING / "ledger_seed.json"
    if generated.exists():
        rows = [ReportingLine.model_validate(item) for item in json.loads(generated.read_text())]
        posted = []
        for row in rows:
            posted.append(post_line(row))
        return posted
    rows = [
        # August revenue $1,000,000
        _line(
            transaction_id="TXN-REV-AUG-001",
            period="2026-08",
            posting_date="2026-08-15",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=400000,
            memo="August platform subscriptions",
            customer="Northwind Labs",
            product="Platform",
            category="revenue",
            source_document_id="INV-AR-AUG-001",
        ),
        _line(
            transaction_id="TXN-REV-AUG-002",
            period="2026-08",
            posting_date="2026-08-20",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=350000,
            memo="August usage",
            customer="Helios Analytics",
            product="Usage",
            category="revenue",
            source_document_id="INV-AR-AUG-002",
        ),
        _line(
            transaction_id="TXN-REV-AUG-003",
            period="2026-08",
            posting_date="2026-08-28",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=250000,
            memo="August professional services",
            customer="Acme Industrial",
            product="Services",
            category="revenue",
            source_document_id="INV-AR-AUG-003",
        ),
        # August COGS $360,000
        _line(
            transaction_id="TXN-HOST-AUG-001",
            period="2026-08",
            posting_date="2026-08-31",
            account="5100-Hosting",
            account_class="cogs",
            side="debit",
            amount=50000,
            memo="AWS August compute",
            vendor="Amazon Web Services",
            category="hosting",
            quantity=5000,
            rate=10,
            source_document_id="INV-002-AUG",
        ),
        _line(
            transaction_id="TXN-HOST-AUG-002",
            period="2026-08",
            posting_date="2026-08-31",
            account="5100-Hosting",
            account_class="cogs",
            side="debit",
            amount=30000,
            memo="GCP August compute",
            vendor="Google Cloud",
            category="hosting",
            quantity=3000,
            rate=10,
            source_document_id="INV-006-AUG",
        ),
        _line(
            transaction_id="TXN-SUP-AUG-001",
            period="2026-08",
            posting_date="2026-08-18",
            account="5200-Supplier",
            account_class="cogs",
            side="debit",
            amount=180000,
            memo="Acme components",
            vendor="Acme Supplies",
            category="supplier",
            quantity=1800,
            rate=100,
            source_document_id="INV-001-AUG",
        ),
        _line(
            transaction_id="TXN-SUP-AUG-002",
            period="2026-08",
            posting_date="2026-08-22",
            account="5200-Supplier",
            account_class="cogs",
            side="debit",
            amount=70000,
            memo="Helios hardware",
            vendor="Helios Hardware",
            category="supplier",
            quantity=700,
            rate=100,
            source_document_id="INV-HEL-AUG",
        ),
        _line(
            transaction_id="TXN-FRT-AUG-001",
            period="2026-08",
            posting_date="2026-08-25",
            account="5300-Freight",
            account_class="cogs",
            side="debit",
            amount=20000,
            memo="Standard inbound freight",
            vendor="FastFreight",
            category="freight",
            source_document_id="INV-FRT-AUG",
        ),
        _line(
            transaction_id="TXN-COGS-AUG-MSC",
            period="2026-08",
            posting_date="2026-08-30",
            account="5400-Other-COGS",
            account_class="cogs",
            side="debit",
            amount=10000,
            memo="Unclassified August COGS",
            vendor="Misc Supplies",
            category="unclassified",
            source_document_id="INV-MSC-AUG",
        ),
        # August opex $200,000
        _line(
            transaction_id="TXN-PAY-AUG-001",
            period="2026-08",
            posting_date="2026-08-28",
            account="6100-Payroll",
            account_class="opex",
            side="debit",
            amount=140000,
            memo="August payroll",
            category="payroll",
            source_document_id="PR-2026-08",
        ),
        _line(
            transaction_id="TXN-OPEX-AUG-001",
            period="2026-08",
            posting_date="2026-08-31",
            account="6000-Operating",
            account_class="opex",
            side="debit",
            amount=60000,
            memo="August operating expenses",
            category="operating",
            source_document_id="OPEX-AUG",
        ),
        # September revenue $1,000,000
        _line(
            transaction_id="TXN-REV-SEP-001",
            period="2026-09",
            posting_date="2026-09-15",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=400000,
            memo="September platform subscriptions",
            customer="Northwind Labs",
            product="Platform",
            category="revenue",
            source_document_id="INV-AR-001",
        ),
        _line(
            transaction_id="TXN-REV-SEP-002",
            period="2026-09",
            posting_date="2026-09-20",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=350000,
            memo="September usage",
            customer="Helios Analytics",
            product="Usage",
            category="revenue",
            source_document_id="INV-AR-003",
        ),
        _line(
            transaction_id="TXN-REV-SEP-003",
            period="2026-09",
            posting_date="2026-09-28",
            account="4000-Revenue",
            account_class="revenue",
            side="credit",
            amount=250000,
            memo="September professional services",
            customer="Acme Industrial",
            product="Services",
            category="revenue",
            source_document_id="INV-AR-SEP-003",
        ),
        # September COGS $390,000 — +$30,000 vs August
        _line(
            transaction_id="TXN-HOST-SEP-001",
            period="2026-09",
            posting_date="2026-09-22",
            account="5100-Hosting",
            account_class="cogs",
            side="debit",
            amount=50000,
            memo="AWS September compute",
            vendor="Amazon Web Services",
            category="hosting",
            quantity=5000,
            rate=10,
            source_document_id="INV-002",
        ),
        _line(
            transaction_id="TXN-HOST-SEP-002",
            period="2026-09",
            posting_date="2026-09-22",
            account="5100-Hosting",
            account_class="cogs",
            side="debit",
            amount=30000,
            memo="GCP September compute",
            vendor="Google Cloud",
            category="hosting",
            quantity=3000,
            rate=10,
            source_document_id="INV-006",
        ),
        _line(
            transaction_id="TXN-HOST-SEP-OVERAGE",
            period="2026-09",
            posting_date="2026-09-28",
            account="5100-Hosting",
            account_class="cogs",
            side="debit",
            amount=15000,
            memo="AWS unplanned hosting overage",
            vendor="Amazon Web Services",
            category="hosting",
            quantity=1500,
            rate=10,
            source_document_id="INV-016",
            source_workflow="ap",
        ),
        _line(
            transaction_id="TXN-SUP-SEP-001",
            period="2026-09",
            posting_date="2026-09-18",
            account="5200-Supplier",
            account_class="cogs",
            side="debit",
            amount=187200,
            memo="Acme components at the new contract rate",
            vendor="Acme Supplies",
            category="supplier",
            quantity=1800,
            rate=104,
            source_document_id="INV-001",
        ),
        _line(
            transaction_id="TXN-SUP-SEP-002",
            period="2026-09",
            posting_date="2026-09-20",
            account="5200-Supplier",
            account_class="cogs",
            side="debit",
            amount=72800,
            memo="Helios hardware at the new contract rate",
            vendor="Helios Hardware",
            category="supplier",
            quantity=700,
            rate=104,
            source_document_id="INV-HEL-SEP",
        ),
        _line(
            transaction_id="TXN-FRT-SEP-001",
            period="2026-09",
            posting_date="2026-09-24",
            account="5300-Freight",
            account_class="cogs",
            side="debit",
            amount=20000,
            memo="Standard inbound freight",
            vendor="FastFreight",
            category="freight",
            source_document_id="INV-FRT-SEP",
        ),
        _line(
            transaction_id="TXN-FRT-SEP-EXPEDITE",
            period="2026-09",
            posting_date="2026-09-26",
            account="5300-Freight",
            account_class="cogs",
            side="debit",
            amount=4000,
            memo="Expedited freight on late materials",
            vendor="FastFreight",
            category="freight",
            source_document_id="INV-FRT-EXP",
        ),
        _line(
            transaction_id="TXN-COGS-SEP-RESIDUAL",
            period="2026-09",
            posting_date="2026-09-29",
            account="5400-Other-COGS",
            account_class="cogs",
            side="debit",
            amount=11000,
            memo="Unclassified September COGS",
            vendor="Misc Supplies",
            category="unclassified",
            source_document_id="INV-MSC-SEP",
        ),
        # September opex $200,000
        _line(
            transaction_id="TXN-PAY-SEP-001",
            period="2026-09",
            posting_date="2026-09-25",
            account="6100-Payroll",
            account_class="opex",
            side="debit",
            amount=140000,
            memo="September payroll",
            category="payroll",
            source_document_id="PR-2026-09",
        ),
        _line(
            transaction_id="TXN-OPEX-SEP-001",
            period="2026-09",
            posting_date="2026-09-30",
            account="6000-Operating",
            account_class="opex",
            side="debit",
            amount=60000,
            memo="September operating expenses",
            category="operating",
            source_document_id="OPEX-SEP",
        ),
    ]
    return [post_line(item) for item in rows]


def seed_demo_receivable() -> None:
    """Add the delayed $25,000 collection used by forecast-vs-actual."""
    from ar.models import CustomerInvoice
    from ar.store import get_invoice, save_invoice

    if get_invoice("INV-AR-FC-001") is not None:
        return
    save_invoice(
        CustomerInvoice.model_validate(
            {
                "invoice_id": "INV-AR-FC-001",
                "customer_id": "CUST-010",
                "customer_name": "Quiet Harbor",
                "invoice_date": "2026-08-26",
                "due_date": "2026-09-25",
                "original_amount": 25000.0,
                "outstanding_amount": 25000.0,
                "status": "OPEN",
                "payment_terms": "net 30",
                "description": "Forecast demo — delayed customer payment",
                "created_at": "2026-08-26T12:00:00Z",
            }
        )
    )
