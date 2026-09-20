"""Company-scale registers that sit on top of the planted plot IDs.

Plot identities (INV-001, INV-017, INV-AR-013, TXN-2026-09-015, …) are created
by the domain agents. This module densifies Maximor Demo Corp to the catalog
scale table ($372.4M run-rate, 340 vendors, 2,840 W-2). Adversarial plants
are applied afterwards by ``sample_data.adversarial`` at seed 42.
"""

from __future__ import annotations

import calendar
import random
from datetime import date, timedelta
from pathlib import Path

from models import GoodsReceipt, Invoice, PurchaseOrder
from reporting.models import ChartAccount

from sample_data.adapters import cash_bank, cash_ledger
from sample_data.context import CompanyScenarioContext, dollars
from sample_data.documents import (
    PLOT_LINE_ITEMS,
    VENDOR_DIRECTORY,
    invoice_document_for,
    render_goods_receipt,
    render_packing_list,
    render_purchase_order,
    render_workpaper,
)
from sample_data.models import JournalEntryRecord
from sample_data.pnl import cogs_invoice_ids


REFERENCE_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / ".cfo-v2"
    / "office"
    / "reference-datasets"
)

HIST_PERIODS = (
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
)

EXTRA_VENDORS: tuple[tuple[str, str, str], ...] = (
    ("VEND-022", "Twilio", "2022-04-01"),
    ("VEND-023", "Notion Labs", "2023-02-14"),
    ("VEND-024", "Snowflake", "2023-06-01"),
    ("VEND-025", "Okta", "2022-09-12"),
    ("VEND-026", "CrowdStrike", "2023-01-20"),
    ("VEND-027", "Zoom Video", "2021-11-02"),
    ("VEND-028", "Atlassian", "2022-03-08"),
    ("VEND-029", "Cloudflare", "2023-05-19"),
    ("VEND-030", "Northline Fab Group", "2025-11-02"),
    ("VEND-031", "Helios Hardware Supply", "2026-01-15"),
    ("VEND-032", "Harbor Power & Light", "2024-08-01"),
    ("VEND-033", "Staples Business Advantage", "2021-04-01"),
    ("VEND-034", "FedEx", "2021-01-01"),
    ("VEND-035", "ADP", "2020-06-01"),
    ("VEND-036", "WeWork Cambridge", "2022-07-01"),
    ("VEND-037", "Comcast Business", "2021-03-15"),
    ("VEND-038", "Pagaya Coffee Service", "2023-09-01"),
    ("VEND-039", "CleanRoom Janitorial", "2022-01-10"),
    ("VEND-040", "Kendall Square Parking", "2021-08-01"),
    ("VEND-041", "HubSpot", "2022-05-01"),
    ("VEND-042", "Stripe Processing", "2021-02-01"),
    ("VEND-043", "Adyen NV", "2024-03-01"),
    ("VEND-044", "DocuSign", "2022-10-01"),
    ("VEND-045", "Palo Alto Networks", "2023-04-01"),
    ("VEND-046", "Boston Edison Steam", "2021-01-01"),
    ("VEND-047", "Carta", "2023-08-12"),
    ("VEND-048", "Gusto Payroll", "2022-01-01"),
    ("VEND-049", "Vanta", "2024-02-01"),
    ("VEND-050", "Linear App", "2024-06-01"),
)

FILLER_VENDOR_STEMS: tuple[str, ...] = (
    "Alder", "Banyan", "Cedar", "Driftwood", "Elm", "Fir", "Ginkgo", "Hazel",
    "Ironwood", "Juniper", "Larch", "Maple", "Northwood", "Oak", "Pine",
    "Quince", "Redwood", "Spruce", "Teak", "Umber", "Violet", "Walnut",
    "Yarrow", "Zephyr", "Beacon", "Canyon", "Delta", "Echo", "Forge",
    "Granite", "Harbor", "Inlet", "Jetty", "Keel", "Lantern", "Mesa",
    "Nimbus", "Orchard", "Prairie", "Quarry", "Ridge", "Sierra", "Timber",
    "Upland", "Valley", "Wharf", "Yellowstone", "Zenith",
)

CUSTOMER_DIRECTORY: dict[str, dict[str, str]] = {
    "CUST-001": {
        "legal_name": "Northwind Labs, Inc.",
        "billing_email": "ap@northwind.example",
        "billing_address": "500 Technology Square",
        "city": "Cambridge",
        "state": "MA",
        "postal_code": "02139",
        "tax_id": "04-3310021",
    },
    "CUST-002": {
        "legal_name": "Helios Analytics Corporation",
        "billing_email": "ap@heliosanalytics.example",
        "billing_address": "12 Marina Boulevard",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94123",
        "tax_id": "94-2288110",
    },
    "CUST-003": {
        "legal_name": "Acme Industrial LLC",
        "billing_email": "ap@acmeindustrial.example",
        "billing_address": "800 Steel Way",
        "city": "Pittsburgh",
        "state": "PA",
        "postal_code": "15222",
        "tax_id": "25-4410988",
    },
    "CUST-004": {
        "legal_name": "Brightline Media Group",
        "billing_email": "ap@brightline.example",
        "billing_address": "14 Fayette Street",
        "city": "Somerville",
        "state": "MA",
        "postal_code": "02143",
        "tax_id": "27-9081101",
    },
    "CUST-005": {
        "legal_name": "Quiet Harbor Holdings",
        "billing_email": "ap@quietharbor.example",
        "billing_address": "1 Wharf Street",
        "city": "Portland",
        "state": "ME",
        "postal_code": "04101",
        "tax_id": "01-2287710",
    },
    "CUST-006": {
        "legal_name": "Pinnacle Retail Corp.",
        "billing_email": "ap@pinnacle.example",
        "billing_address": "90 Prudential Plaza",
        "city": "Chicago",
        "state": "IL",
        "postal_code": "60601",
        "tax_id": "36-5510299",
    },
    "CUST-007": {
        "legal_name": "Atlas Robotics, Inc.",
        "billing_email": "ap@atlasrobotics.example",
        "billing_address": "350 Third Street",
        "city": "Cambridge",
        "state": "MA",
        "postal_code": "02142",
        "tax_id": "04-8821993",
    },
    "CUST-008": {
        "legal_name": "Lumen Labs PBC",
        "billing_email": "ap@lumenlabs.example",
        "billing_address": "44 East 23rd Street",
        "city": "New York",
        "state": "NY",
        "postal_code": "10010",
        "tax_id": "13-7722104",
    },
    "CUST-009": {
        "legal_name": "Northstar LLC",
        "billing_email": "ap@northstar.example",
        "billing_address": "100 Federal Street",
        "city": "Boston",
        "state": "MA",
        "postal_code": "02110",
        "tax_id": "04-1102288",
    },
    "CUST-010": {
        "legal_name": "Meridian Health Systems",
        "billing_email": "ap@meridianhealth.example",
        "billing_address": "725 Albany Street",
        "city": "Boston",
        "state": "MA",
        "postal_code": "02118",
        "tax_id": "04-6621003",
    },
}

SKU_CATALOG: tuple[tuple[str, str, float], ...] = (
    ("platform seats — monthly", "subscription", 42.0),
    ("usage overage block", "usage", 15.0),
    ("implementation hours", "services", 220.0),
    ("premium support", "services", 1800.0),
    ("SaaS workspace add-on", "subscription", 95.0),
    ("warehouse consumables", "supplies", 38.5),
    ("colo cross-connect", "facilities", 450.0),
    ("security monitoring hosts", "subscription", 12.0),
)

EMPLOYEES: tuple[tuple[str, str, str, int], ...] = (
    ("EMP-001", "Priya Nair", "Finance", 185000),
    ("EMP-002", "Jordan Hale", "Finance", 162000),
    ("EMP-003", "Marcus Chen", "Engineering", 210000),
    ("EMP-004", "Elena Vasquez", "Engineering", 198000),
    ("EMP-005", "Maya Ortiz", "Operations", 98000),
    ("EMP-006", "Chris Lang", "Engineering", 175000),
    ("EMP-007", "Sofia Rahman", "Sales", 140000),
    ("EMP-008", "Noah Patel", "Sales", 128000),
    ("EMP-009", "Hannah Kim", "Customer Success", 110000),
    ("EMP-010", "Luis Romero", "Engineering", 188000),
    ("EMP-011", "Ava Berg", "Engineering", 172000),
    ("EMP-012", "Owen Blake", "G&A", 92000),
    ("EMP-013", "Grace Liu", "Finance", 125000),
    ("EMP-014", "Theo Grant", "Engineering", 205000),
    ("EMP-015", "Nina Volkov", "Sales", 135000),
    ("EMP-016", "Jamal Wright", "Customer Success", 102000),
    ("EMP-017", "Ivy Chen", "Engineering", 168000),
    ("EMP-018", "Peter Holm", "Operations", 88000),
    ("EMP-019", "Sara Quill", "G&A", 76000),
    ("EMP-020", "Benito Cruz", "Engineering", 181000),
    ("EMP-021", "Leah Morse", "Finance", 118000),
    ("EMP-022", "Kenji Sato", "Engineering", 194000),
    ("EMP-023", "Ruth Adler", "Legal ops", 155000),
    ("EMP-024", "Omar Farid", "Engineering", 176000),
    ("EMP-025", "Cora Dane", "Sales", 122000),
    ("EMP-026", "Felix Nguyen", "Engineering", 169000),
    ("EMP-027", "Dana Brooks", "Customer Success", 99000),
    ("EMP-028", "Will Park", "Engineering", 201000),
    ("EMP-029", "Amelia Frost", "G&A", 84000),
    ("EMP-030", "Hugo Stein", "Operations", 91000),
    ("EMP-031", "Yara Haddad", "Engineering", 183000),
    ("EMP-032", "Miles Quinn", "Sales", 131000),
    ("EMP-033", "Piper Shaw", "Finance", 108000),
    ("EMP-034", "Andre Silva", "Engineering", 177000),
    ("EMP-035", "Naomi Ellis", "Customer Success", 104000),
    ("EMP-036", "Rex Calder", "Engineering", 190000),
    ("EMP-037", "Jun Park", "Engineering", 165000),
    ("EMP-038", "Helen Cho", "G&A", 79000),
    ("EMP-039", "Samir Joshi", "Engineering", 186000),
    ("EMP-040", "Tessa Ward", "Sales", 126000),
    ("EMP-041", "Colin Byrne", "Operations", 87000),
    ("EMP-042", "Rita Gomez", "Finance", 112000),
    ("EMP-043", "Evan Cole", "Engineering", 174000),
    ("EMP-044", "Paula Reed", "Customer Success", 97000),
    ("EMP-045", "Dmitri Orlov", "Engineering", 199000),
    ("EMP-046", "Jane Holt", "G&A", 81000),
    ("EMP-047", "Kai Nakamura", "Engineering", 171000),
    ("EMP-048", "Marisol Vega", "Sales", 133000),
)

IDENTITY_EMPLOYEES: tuple[tuple[str, str, str, int, str], ...] = (
    ("EMP-0901", "Jordan Hale", "Procurement", 162000, "USR-APPR-HALE"),
    ("EMP-0902", "Priya Nair", "Finance", 185000, "USR-APPR-NAIR"),
    ("EMP-0903", "Marcus Chen", "Engineering operations", 210000, "USR-APPR-CHEN"),
    ("EMP-0904", "Elena Vasquez", "IT", 198000, "USR-APPR-VASQ"),
    ("EMP-1088", "Nadia Voss", "Controller", 176000, "USR-JE-04"),
    ("EMP-1190", "Mei Stratton", "Revenue", 148000, "USR-REV-05"),
    ("EMP-2201", "Riley Cho", "Facilities", 92000, "USR-FAC-01"),
    ("EMP-2290", "Ava Pell", "Warehouse", 48000, "USR-WH-2290"),
    ("EMP-3304", "Samir Okonkwo", "AR", 118000, "USR-APPLY-02"),
    ("EMP-3310", "Nia Bright", "Marketing", 132000, "USR-MKT-01"),
    ("EMP-4128", "Dana Kestrel", "AP", 94000, "USR-VM-04"),
    ("EMP-4402", "Luis Redmond", "Processor operations", 141000, "USR-STRIPE-01"),
    ("EMP-5510", "Chris Pell", "Payroll", 128000, "USR-PR-01"),
    ("EMP-6722", "Glen Park", "Warehouse receiving", 64000, "USR-GR-01"),
    ("EMP-8891", "Tomas Halyard", "Warehouse", 108800, "USR-WH-8891"),
)


def _period_end(period: str) -> str:
    year_i, month_i = (int(part) for part in period.split("-"))
    return date(year_i, month_i, calendar.monthrange(year_i, month_i)[1]).isoformat()


def _period_start(period: str) -> str:
    return f"{period}-01"


def _safe_named(ctx: CompanyScenarioContext, value: str) -> str:
    if ctx.ids.contains(value):
        return value
    return ctx.ids.named(value)


def _routing(vendor_id: str) -> str:
    digits = "".join(ch for ch in vendor_id if ch.isdigit()) or "221"
    return f"01100{int(digits) % 900 + 100:03d}"


def _account(vendor_id: str) -> str:
    n = int("".join(ch for ch in vendor_id if ch.isdigit()) or "1")
    return f"{10000000 + n * 417:09d}"


def enrich_vendor_master(ctx: CompanyScenarioContext) -> None:
    alias_overrides = {
        "VEND-001": ["Acme Supply Co.", "ACME SUPPLIES"],
        "VEND-001-ALIAS": ["Acme Supplies"],
        "VEND-001-DUP": ["Acme Supplies L.L.C."],
        "VEND-003": ["Northline Fab", "NORTHLINE FABRICATION CORP"],
        "VEND-005": ["Helios Hardware Inc", "HELIOS HARDWARE"],
        "VEND-015": ["Harbor Electric Co"],
        "VEND-030": ["Northline Fabrication Group"],
        "VEND-031": ["Helios Hardware Supply Co."],
        "VEND-032": ["Harbor P&L"],
    }
    bank_changed = {
        "VEND-005": "2026-04-18",
        "VEND-015": "2025-11-02",
        "VEND-022": "2026-02-09",
    }
    for vendor_id, row in ctx.vendors.items():
        name = row["name"]
        directory = VENDOR_DIRECTORY.get(name, {})
        row.update(
            {
                "legal_name": directory.get("legal_name", name),
                "dba": name if directory.get("legal_name", name) != name else "",
                "tax_id": directory.get("tax_id", f"04-{int(vendor_id[-3:]) * 137 % 9000000:07d}")
                if vendor_id[-3:].isdigit()
                else directory.get("tax_id", "04-0000000"),
                "address": directory.get("address", "1 Vendor Row\nBoston, MA 02110"),
                "phone": directory.get("phone", "+1 617-555-0000"),
                "billing_email": directory.get("email", f"billing@{vendor_id.lower()}.example"),
                "payment_terms": directory.get("terms", "net 30"),
                "bank_name": (directory.get("bank") or "First National Bank").split("  ")[0],
                "bank_routing": _routing(vendor_id),
                "bank_account": _account(vendor_id),
                "bank_account_last4": _account(vendor_id)[-4:],
                "bank_changed_on": bank_changed.get(vendor_id, ""),
                "aliases": alias_overrides.get(vendor_id, []),
                "duplicate_risk_key": "acme-supplies" if vendor_id.startswith("VEND-001") else vendor_id,
                "currency": "USD",
                "country": "US",
                "status": "active",
            }
        )
        if vendor_id == "VEND-001-DUP":
            row["duplicate_risk_key"] = "acme-supplies"


def add_extra_vendors(ctx: CompanyScenarioContext) -> None:
    for vendor_id, name, first_seen in EXTRA_VENDORS:
        if vendor_id in ctx.vendors:
            continue
        ctx.vendors[vendor_id] = {
            "vendor_id": vendor_id,
            "name": name,
            "first_seen": first_seen,
            "unusual": False,
            "legal_name": name,
            "dba": "",
            "tax_id": f"04-{int(vendor_id[-3:]) * 271 % 9000000:07d}",
            "address": f"{100 + int(vendor_id[-3:])} Atlantic Avenue\nBoston, MA 02110",
            "phone": f"+1 617-555-{int(vendor_id[-3:]) % 9000:04d}",
            "billing_email": f"billing@{name.split()[0].lower()}.example",
            "payment_terms": "net 30",
            "bank_name": "First National Bank",
            "bank_routing": _routing(vendor_id),
            "bank_account": _account(vendor_id),
            "bank_account_last4": _account(vendor_id)[-4:],
            "bank_changed_on": "",
            "aliases": [],
            "duplicate_risk_key": vendor_id,
            "currency": "USD",
            "country": "US",
            "status": "active",
        }
        _safe_named(ctx, vendor_id)
    add_scale_vendors(ctx)
    enrich_vendor_master(ctx)


def add_scale_vendors(ctx: CompanyScenarioContext) -> None:
    """Fill the vendor master to 340 active rows. Identity-bible vendors come later."""
    suffixes = (
        "Systems", "Services", "Supply", "Labs", "Partners", "Works",
        "Components", "Network", "Studio", "Group",
    )
    next_n = 51
    while len(ctx.vendors) < 325:
        vendor_id = f"VEND-{next_n:03d}"
        next_n += 1
        if vendor_id in ctx.vendors:
            continue
        stem = FILLER_VENDOR_STEMS[(next_n * 3) % len(FILLER_VENDOR_STEMS)]
        suffix = suffixes[next_n % len(suffixes)]
        name = f"{stem} {suffix}"
        first_seen = f"{2020 + (next_n % 6)}-{(next_n % 12) + 1:02d}-01"
        ctx.vendors[vendor_id] = {
            "vendor_id": vendor_id,
            "name": name,
            "first_seen": first_seen,
            "unusual": False,
            "legal_name": f"{name} LLC",
            "dba": "",
            "tax_id": f"04-{(next_n * 409) % 90_00000:07d}",
            "address": f"{100 + next_n} Massachusetts Avenue\nCambridge, MA 02139",
            "phone": f"+1 617-555-{next_n % 9000:04d}",
            "billing_email": f"billing@{stem.lower()}.example",
            "payment_terms": "net 30",
            "bank_name": "First National Bank",
            "bank_routing": _routing(vendor_id),
            "bank_account": _account(vendor_id),
            "bank_account_last4": _account(vendor_id)[-4:],
            "bank_changed_on": "",
            "aliases": [],
            "duplicate_risk_key": vendor_id,
            "currency": "USD",
            "country": "US",
            "status": "active",
        }
        _safe_named(ctx, vendor_id)


def enrich_customers(ctx: CompanyScenarioContext) -> None:
    extras = {
        "CUST-011": ("Beacon Biotech", "on_time", 0.94, 1, False, "invoice_number"),
        "CUST-012": ("Copperline Logistics", "mixed", 0.7, 7, False, "purchase_order"),
        "CUST-013": ("Summit Civic", "chronic_late", 0.4, 16, False, "none"),
        "CUST-014": ("Redwood Clinics", "batch_payer", 0.78, 4, True, "batch"),
        "CUST-015": ("Ironclad Software", "on_time", 0.91, 0, True, "invoice_number"),
    }
    from ar.models import Customer

    for customer_id, (name, behavior, rate, late, strategic, remit) in extras.items():
        if customer_id in ctx.customers:
            continue
        item = Customer(
            customer_id=customer_id,
            customer_name=name,
            payment_behavior=behavior,
            on_time_rate=rate,
            average_days_late=late,
            strategic=strategic,
            typical_remittance=remit,
            legal_name=f"{name}, Inc.",
            billing_email=f"ap@{name.split()[0].lower()}.example",
            billing_address="1 Customer Plaza",
            city="Boston",
            state="MA",
            postal_code="02110",
            tax_id=f"04-{int(customer_id[-3:]) * 193 % 9000000:07d}",
        )
        ctx.customers[customer_id] = item
        _safe_named(ctx, customer_id)
    for customer_id, profile in CUSTOMER_DIRECTORY.items():
        item = ctx.customers.get(customer_id)
        if item is None:
            continue
        ctx.customers[customer_id] = item.model_copy(update=profile | {"legal_name": profile["legal_name"]})


def _add_ap(
    ctx: CompanyScenarioContext,
    invoice_id: str,
    vendor: str,
    amount: float,
    invoice_date: str,
    due_date: str,
    vendor_invoice_number: str,
    description: str,
    *,
    po_id: str,
    receipt_id: str,
) -> None:
    if invoice_id in ctx.ap_invoices:
        return
    po = PurchaseOrder(
        po_id=po_id,
        vendor=vendor,
        authorized_amount=amount,
        description=description,
        status="approved",
        created_date=invoice_date,
        approval_limit=max(amount, 25000.0),
        approver="Jordan Hale",
    )
    ctx.purchase_orders[po_id] = po
    _safe_named(ctx, po_id)
    gr = GoodsReceipt(
        receipt_id=receipt_id,
        po_id=po_id,
        received=True,
        received_date=invoice_date,
        amount_received=amount,
        quantity_ordered=1,
        quantity_received=1,
    )
    ctx.goods_receipts[receipt_id] = gr
    _safe_named(ctx, receipt_id)
    invoice = Invoice(
        invoice_id=invoice_id,
        vendor=vendor,
        po_id=po_id,
        amount=amount,
        invoice_date=invoice_date,
        due_date=due_date,
        vendor_invoice_number=vendor_invoice_number,
        description=description,
        payment_terms="net 30",
    )
    ctx.ap_invoices[invoice_id] = invoice
    _safe_named(ctx, invoice_id)
    je_id = f"JE-AP-{invoice_id}"
    if je_id not in ctx.journal_entries:
        ctx.add_journal(
            JournalEntryRecord(
                entry_id=je_id,
                period=invoice_date[:7],
                effective_date=invoice_date,
                posting_date=invoice_date,
                posting_timestamp=f"{invoice_date}T12:30:00Z",
                debit_account="6000-Operating",
                credit_account="2000-AP",
                amount_minor=int(round(amount * 100)),
                memo=description,
                vendor=vendor,
                source_document_id=invoice_id,
                transaction_id=f"TXN-AP-{invoice_id}",
                entry_type="ap_invoice",
                category="volume_opex",
                related_ids=[invoice_id, po_id],
                evidence_refs=[f"doc:{invoice_id}"],
            )
        )


def add_live_ap_volume(ctx: CompanyScenarioContext, rng: random.Random) -> None:
    vendors = [row["name"] for row in ctx.vendors.values() if not row.get("unusual")]
    target = 110
    next_n = 22
    while len(ctx.ap_invoices) < target:
        invoice_id = f"INV-{next_n:03d}"
        next_n += 1
        if invoice_id in ctx.ap_invoices or invoice_id in cogs_invoice_ids():
            continue
        vendor = vendors[(next_n * 7) % len(vendors)]
        sku, _kind, unit = SKU_CATALOG[next_n % len(SKU_CATALOG)]
        qty = 1 + (next_n % 9)
        amount_minor = qty * int(round(unit * 100)) + (next_n % 17) * 13
        if amount_minor % 100 == 0 and amount_minor >= 1_000_000:
            amount_minor += 17
        amount = dollars(amount_minor)
        day = 1 + (next_n % 27)
        invoice_date = f"2026-09-{day:02d}"
        due = date(2026, 9, day) + timedelta(days=30)
        due_date = due.isoformat()
        _add_ap(
            ctx,
            invoice_id,
            vendor,
            amount,
            invoice_date,
            due_date,
            f"{vendor[:3].upper()}-2026-09-{next_n:04d}",
            f"{sku} billed {invoice_date}",
            po_id=f"PO-{300 + next_n}",
            receipt_id=f"GR-{300 + next_n}",
        )


def add_extra_ar(ctx: CompanyScenarioContext) -> None:
    from ar.models import CustomerInvoice

    extras = [
        ("INV-AR-017", "CUST-011", "Beacon Biotech", "2026-09-12", "2026-10-12", 18400.0, "OPEN", "September seats"),
        ("INV-AR-018", "CUST-012", "Copperline Logistics", "2026-08-20", "2026-09-19", 9600.0, "PAST_DUE", "Dock scanners 1-30"),
        ("INV-AR-019", "CUST-013", "Summit Civic", "2026-07-15", "2026-08-14", 7200.0, "PAST_DUE", "Civic portal 31-60"),
        ("INV-AR-020", "CUST-014", "Redwood Clinics", "2026-06-10", "2026-07-10", 15800.0, "PAST_DUE", "Clinic rollout 61-90"),
        ("INV-AR-021", "CUST-015", "Ironclad Software", "2026-09-05", "2026-10-05", 22100.0, "OPEN", "Ironclad platform"),
        ("INV-AR-022", "CUST-001", "Northwind Labs", "2026-09-22", "2026-10-22", 6400.0, "OPEN", "Add-on usage"),
        ("INV-AR-023", "CUST-006", "Pinnacle Retail", "2026-09-08", "2026-10-08", 4100.0, "OPEN", "Store 14 license"),
        ("INV-AR-024", "CUST-007", "Atlas Robotics", "2026-08-28", "2026-09-27", 8900.0, "PAST_DUE", "Spare parts kit"),
        ("INV-AR-025", "CUST-004", "Brightline Media", "2026-05-02", "2026-06-01", 27500.0, "PAST_DUE", "Retainer 90+"),
        ("INV-AR-026", "CUST-005", "Quiet Harbor", "2026-09-25", "2026-10-25", 3800.0, "OPEN", "Quiet Harbor addendum"),
        ("INV-AR-027", "CUST-010", "Meridian Health", "2026-09-18", "2026-10-18", 5100.0, "OPEN", "Clinic analytics"),
        ("INV-AR-028", "CUST-002", "Helios Analytics", "2026-09-14", "2026-10-14", 13300.0, "OPEN", "Usage true-up"),
        ("INV-AR-029", "CUST-008", "Lumen Labs", "2026-09-16", "2026-10-16", 2700.0, "OPEN", "Seat block C"),
        ("INV-AR-030", "CUST-009", "Northstar LLC", "2026-09-21", "2026-10-21", 4500.0, "OPEN", "Northstar add-on"),
    ]
    for invoice_id, customer_id, name, invoice_date, due_date, amount, status, description in extras:
        if invoice_id in ctx.ar_invoices:
            continue
        ctx.ar_invoices[invoice_id] = CustomerInvoice(
            invoice_id=invoice_id,
            customer_id=customer_id,
            customer_name=name,
            invoice_date=invoice_date,
            due_date=due_date,
            original_amount=amount,
            outstanding_amount=amount,
            status=status,  # type: ignore[arg-type]
            description=description,
            created_at=f"{invoice_date}T09:00:00Z",
            currency="USD",
        )
        _safe_named(ctx, invoice_id)


def add_historical_ap_register(ctx: CompanyScenarioContext, rng: random.Random) -> None:
    vendors = [row for row in ctx.vendors.values() if not row.get("unusual")]
    seq = 0
    for period in HIST_PERIODS + ("2026-08",):
        year_i, month_i = (int(part) for part in period.split("-"))
        last = calendar.monthrange(year_i, month_i)[1]
        for day_n in range(1, 21):
            for slot in range(22):
                seq += 1
                vendor = vendors[(seq * 3 + slot) % len(vendors)]
                sku, _kind, unit = SKU_CATALOG[(seq + slot) % len(SKU_CATALOG)]
                qty = 1 + ((seq + slot) % 11)
                amount = round(qty * unit + ((seq % 23) * 0.11), 2)
                day = min(last, 1 + (day_n * 1) % last)
                invoice_date = f"{period}-{day:02d}"
                invoice_id = f"HAP-{period}-{seq:04d}"
                po_id = f"HPO-{period}-{seq:04d}"
                je_id = f"JE-{invoice_id}"
                row = {
                    "invoice_id": invoice_id,
                    "vendor_id": vendor["vendor_id"],
                    "vendor": vendor["name"],
                    "vendor_invoice_number": f"{vendor['name'][:3].upper()}-{period}-{seq:04d}",
                    "invoice_date": invoice_date,
                    "due_date": (date(year_i, month_i, day) + timedelta(days=30)).isoformat(),
                    "amount": amount,
                    "currency": "USD",
                    "po_id": po_id,
                    "status": "PAID",
                    "paid_date": min(_period_end(period), (date(year_i, month_i, day) + timedelta(days=18)).isoformat()),
                    "period": period,
                    "description": f"{sku} {period}",
                    "journal_id": je_id,
                }
                ctx.historical_ap_register.append(row)
                if je_id in ctx.journal_entries:
                    continue
                ctx.add_journal(
                    JournalEntryRecord(
                        entry_id=je_id,
                        period=period,
                        effective_date=row["paid_date"],
                        posting_date=row["paid_date"],
                        posting_timestamp=f"{row['paid_date']}T15:00:00Z",
                        debit_account="6000-Operating",
                        credit_account="1000-Cash",
                        amount_minor=int(round(amount * 100)),
                        memo=row["description"],
                        vendor=vendor["name"],
                        source_document_id=invoice_id,
                        transaction_id=invoice_id,
                        entry_type="historical_ap",
                        category="volume_opex",
                        related_ids=[invoice_id, po_id],
                        evidence_refs=[f"register:{invoice_id}"],
                    )
                )
                _safe_named(ctx, invoice_id)
                _safe_named(ctx, je_id)


def add_trailing_pnl(ctx: CompanyScenarioContext) -> None:
    """Prior months at the catalog monthly run-rate, not the $1,000,000 toy."""
    customers = [
        ("CUST-001", "Northwind Labs", "Platform"),
        ("CUST-002", "Helios Analytics", "Usage"),
        ("CUST-003", "Acme Industrial", "Services"),
    ]
    splits = (1_220_000_000, 1_067_500_000, 762_500_000)
    cogs_rows = (
        ("Amazon Web Services", "5100-Hosting", "hosting", 152_500_000),
        ("Google Cloud", "5100-Hosting", "hosting", 91_500_000),
        ("Acme Supplies", "5200-Supplier", "supplier", 549_000_000),
        ("Helios Hardware", "5200-Supplier", "supplier", 213_500_000),
        ("Freightline Logistics", "5300-Freight", "freight", 61_000_000),
        ("Misc Supplies", "5400-Other-COGS", "unclassified", 30_500_000),
    )
    for period in HIST_PERIODS:
        end = _period_end(period)
        for index, ((customer_id, name, product), amount_minor) in enumerate(zip(customers, splits), start=1):
            invoice_id = f"INV-AR-HIST-{period}-{index:02d}"
            if invoice_id in ctx.ar_invoices:
                continue
            from ar.models import CustomerInvoice

            ctx.ar_invoices[invoice_id] = CustomerInvoice(
                invoice_id=invoice_id,
                customer_id=customer_id,
                customer_name=name,
                invoice_date=end,
                due_date=end,
                original_amount=dollars(amount_minor),
                outstanding_amount=0.0,
                status="PAID",
                description=f"{period} {product} subscription",
                last_payment_date=end,
                created_at=f"{end}T09:00:00Z",
            )
            _safe_named(ctx, invoice_id)
            txn = f"TXN-REV-HIST-{period}-{index:02d}"
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=f"JE-{txn}",
                    period=period,
                    effective_date=end,
                    posting_date=end,
                    posting_timestamp=f"{end}T18:00:00Z",
                    debit_account="1100-AR",
                    credit_account="4000-Revenue",
                    amount_minor=amount_minor,
                    memo=f"{period} {product}",
                    customer=name,
                    product=product,
                    source_document_id=invoice_id,
                    transaction_id=txn,
                    entry_type="ar_invoice",
                    category="volume_revenue",
                )
            )
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=f"JE-CASH-{txn}",
                    period=period,
                    effective_date=end,
                    posting_date=end,
                    posting_timestamp=f"{end}T18:30:00Z",
                    debit_account="1000-Cash",
                    credit_account="1100-AR",
                    amount_minor=amount_minor,
                    memo=f"Collection {invoice_id}",
                    customer=name,
                    source_document_id=invoice_id,
                    transaction_id=f"PAY-HIST-{period}-{index:02d}",
                    entry_type="ar_receipt",
                    category="volume_cash",
                )
            )
        for index, (vendor, account, category, amount_minor) in enumerate(cogs_rows, start=1):
            invoice_id = f"INV-COGS-HIST-{period}-{index:02d}"
            txn = f"TXN-COGS-HIST-{period}-{index:02d}"
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=f"JE-{txn}",
                    period=period,
                    effective_date=end,
                    posting_date=end,
                    posting_timestamp=f"{end}T19:00:00Z",
                    debit_account=account,
                    credit_account="2000-AP",
                    amount_minor=amount_minor,
                    memo=f"{period} {category}",
                    vendor=vendor,
                    source_document_id=invoice_id,
                    transaction_id=txn,
                    entry_type="ap_invoice",
                    category="volume_cogs",
                )
            )
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=f"JE-PAY-{txn}",
                    period=period,
                    effective_date=end,
                    posting_date=end,
                    posting_timestamp=f"{end}T19:20:00Z",
                    debit_account="2000-AP",
                    credit_account="1000-Cash",
                    amount_minor=amount_minor,
                    memo=f"Settle {invoice_id}",
                    vendor=vendor,
                    source_document_id=invoice_id,
                    transaction_id=f"PAY-{txn}",
                    entry_type="ap_payment",
                    category="volume_cash",
                )
            )
            _safe_named(ctx, invoice_id)


def add_documents(ctx: CompanyScenarioContext) -> None:
    for invoice in ctx.ap_invoices.values():
        key = f"invoices/{invoice.invoice_id}.txt"
        if invoice.invoice_id in PLOT_LINE_ITEMS or invoice.invoice_id.startswith("INV-"):
            text = invoice_document_for(
                invoice.invoice_id,
                invoice.vendor,
                invoice.vendor_invoice_number,
                amount=invoice.amount,
                invoice_date=invoice.invoice_date,
                due_date=invoice.due_date,
                po_id=invoice.po_id,
                description=invoice.description,
            )
            ctx.document_texts[key] = text
            ctx.ingestion_files[key] = text
        if invoice.po_id and invoice.po_id in ctx.purchase_orders:
            po = ctx.purchase_orders[invoice.po_id]
            ctx.document_texts[f"purchase_orders/{po.po_id}.txt"] = render_purchase_order(
                po.po_id,
                po.vendor,
                authorized_amount=po.authorized_amount,
                created_date=po.created_date or invoice.invoice_date,
                description=po.description,
                approver=po.approver or "Jordan Hale",
            )
    for receipt in ctx.goods_receipts.values():
        vendor = ctx.purchase_orders[receipt.po_id].vendor if receipt.po_id in ctx.purchase_orders else ""
        ctx.document_texts[f"goods_receipts/{receipt.receipt_id}.txt"] = render_goods_receipt(
            receipt.receipt_id,
            receipt.po_id,
            vendor,
            received_date=receipt.received_date or "",
            quantity_ordered=receipt.quantity_ordered,
            quantity_received=receipt.quantity_received,
            amount_received=receipt.amount_received,
            packing_list=f"PL-{receipt.receipt_id}",
        )
        ctx.document_texts[f"packing_lists/PL-{receipt.receipt_id}.txt"] = render_packing_list(
            receipt.po_id,
            vendor,
            items=[f"Line {receipt.receipt_id} — qty {receipt.quantity_received}"],
            ship_date=receipt.received_date or "",
        )


def upgrade_ingestion_emails(ctx: CompanyScenarioContext) -> None:
    by_id = {row["message_id"]: row for row in ctx.ingestion_emails}
    mapping = {
        "MSG-E-INV-001": "INV-001",
        "MSG-E-DUP-001": "INV-001",
        "MSG-E-INFER": "INV-021",
        "MSG-E-MESSY": "INV-014",
    }
    for message_id, invoice_id in mapping.items():
        row = by_id.get(message_id)
        invoice = ctx.ap_invoices.get(invoice_id)
        if row is None or invoice is None:
            continue
        text = invoice_document_for(
            invoice.invoice_id,
            invoice.vendor,
            invoice.vendor_invoice_number,
            amount=invoice.amount,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            po_id=invoice.po_id,
            description=invoice.description,
        )
        if message_id == "MSG-E-MESSY":
            text = text.replace("INVOICE", "1NVOICE").replace("Northline Fabrication Corp.", "Northline Fabrication")
            row["body"] = (
                "Hi AP — scanned copy attached, sorry for the quality. "
                "Northline Fabrication lot NF-201 against PO-201. "
                "Please process when you can read the header.\n\n"
                "Regards,\nWarehouse billing\nNorthline Fabrication Corp.\n55 Industrial Way, Somerville, MA 02143"
            )
        elif message_id == "MSG-E-DUP-001":
            row["body"] = (
                "Resending in case the first copy of ACM-2026-4410 was missed. "
                "Same invoice, same PO-101, same $12,450.00. "
                "Please do not pay twice.\n\n"
                "Billing\nAcme Supplies, Inc.\n180 Northern Avenue, Boston, MA 02210"
            )
        elif message_id == "MSG-E-INFER":
            row["body"] = (
                "Attached is the second Cambridge shipment billed as ACM-2026-4411. "
                "The header omitted our legal name; Acme Supplies is the vendor on PO-101 "
                "and CASE-001 already confirmed the Acme Supply Co. alias.\n\n"
                "Accounts receivable\nAcme Supplies, Inc."
            )
        else:
            row["body"] = (
                "Hello Maximor AP,\n\n"
                "Please find invoice ACM-2026-4410 for standing desks and monitors. "
                "The order is PO-101. Goods were received at Dock B on 2026-09-05 (GR-101). "
                "Terms are 2/10 net 30; a 2% discount is available through 2026-09-18.\n\n"
                "Remit ACH to First National Bank routing 011000390 account ****4410 and "
                "include ACM-2026-4410 on the payment advice.\n\n"
                "Thank you,\nAcme Supplies billing desk\n"
                "180 Northern Avenue, Suite 400, Boston, MA 02210\n"
                "billing@acmesupplies.example"
            )
        if row.get("attachments"):
            row["attachments"][0]["text"] = text
    quote = by_id.get("MSG-E-QUOTE")
    if quote is not None:
        from sample_data.documents import render_quote

        quote_text = render_quote(
            "Acme Supplies",
            "Q-8891",
            amount=12450.0,
            valid_until="2026-10-01",
            lines=PLOT_LINE_ITEMS["INV-001"],
        )
        quote["body"] = (
            "This is a quotation, not a request for payment until you issue a PO. "
            "Quote Number Q-8891 covers additional standing desks if you want a second lot.\n\n"
            "Sales\nAcme Supplies, Inc."
        )
        if quote.get("attachments"):
            quote["attachments"][0]["text"] = quote_text
    stmt = by_id.get("MSG-E-STMT")
    if stmt is not None:
        from sample_data.documents import render_statement

        text = render_statement(
            "Office Depot",
            period="September 2026",
            open_items=[("OD-DISC-2100", 2100.0), ("OD-HOLD-9912", 3280.0)],
        )
        stmt["body"] = (
            "Attached is your monthly statement of open items. This is not an invoice. "
            "Please match the listed Office Depot invoices to your AP subledger.\n\n"
            "Statements desk\nOffice Depot, LLC"
        )
        if stmt.get("attachments"):
            stmt["attachments"][0]["text"] = text
    po_mail = by_id.get("MSG-E-PO")
    if po_mail is not None and "PO-101" in ctx.purchase_orders:
        po = ctx.purchase_orders["PO-101"]
        text = render_purchase_order(
            po.po_id,
            po.vendor,
            authorized_amount=po.authorized_amount,
            created_date=po.created_date,
            description=po.description,
            approver=po.approver,
        )
        po_mail["body"] = (
            "Purchase order PO-101 has been issued to Acme Supplies for office equipment "
            "authorized at $12,450.00. This is a PO, not a vendor invoice.\n\n"
            "Procurement\nMaximor Demo Corp"
        )
        if po_mail.get("attachments"):
            po_mail["attachments"][0]["text"] = text
    rcpt = by_id.get("MSG-E-RCPT")
    if rcpt is not None:
        rcpt["body"] = (
            "Uber trip receipt for a campus visit on 2026-09-12. Fare $42.10 charged to "
            "the corporate card ending 4410. This is a payment confirmation / receipt, "
            "not a vendor invoice.\n\n"
            "Rider: Maya Ortiz\nPickup: Kendall Square  Dropoff: 245 Main Street"
        )
        if rcpt.get("attachments"):
            rcpt["attachments"][0]["text"] = (
                "UBER\nTrip receipt\nFare 42.10 USD\nDate 2026-09-12\n"
                "This is a payment confirmation / receipt, not a vendor invoice.\n"
                "Card ••••4410  Rider Maya Ortiz\n"
                "Pickup Kendall T  Dropoff Maximor HQ Dock B\n"
            )
    mkt = by_id.get("MSG-E-MKT")
    if mkt is not None:
        mkt["body"] = (
            "Upgrade your workspace with Slack AI. Limited time for Business+ customers. "
            "Unsubscribe anytime. This newsletter is not an invoice.\n\n"
            "Slack marketing  ·  500 Howard Street, San Francisco, CA 94105"
        )
    missing = by_id.get("MSG-E-MISSING")
    if missing is not None:
        missing["body"] = (
            "Please process the attached invoice for last week's delivery.\n\n"
            "We will send a complete bill if this scan is unreadable.\n"
        )
        if missing.get("attachments"):
            missing["attachments"][0]["text"] = (
                "Please process the attached invoice.\n"
                "No amount, vendor, or invoice number is printed.\n"
                "Scan quality is too poor to recover the header.\n"
                "Contact unknown@vendor.example if you can identify the shipment.\n"
            )
    scan = next((item for item in ctx.ingestion_documents if item["document_id"] == "DOC-SCAN-INV-001"), None)
    if scan is not None and "INV-001" in ctx.ap_invoices:
        invoice = ctx.ap_invoices["INV-001"]
        scan["text"] = invoice_document_for(
            invoice.invoice_id,
            invoice.vendor,
            invoice.vendor_invoice_number,
            amount=invoice.amount,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            po_id=invoice.po_id,
            description=invoice.description,
        )


VOLUME_CASH_EXCLUDE = {
    "VEND-030",  # Northline near-duplicate; would join the grouped ACH pool
    "VEND-031",  # Helios near-duplicate; would join the fee-netted wire pool
    "VEND-032",  # Harbor near-duplicate
    "VEND-042",  # Stripe Processing; would collide with provider payout matching
    "VEND-043",  # Adyen NV; same
    "VEND-KIS-01",
    "VEND-NLF-02",
    "VEND-NLF-03",
    "VEND-WBT-01",
    "VEND-HAL-01",
    "VEND-CLR-01",
    "VEND-BLS-01",
    "VEND-CPS-01",
    "VEND-HES-01",
    "VEND-OIC-01",
    "VEND-FLE-01",
    "VEND-HBP-01",
}


def _volume_cash_vendors(ctx: CompanyScenarioContext) -> list[dict]:
    allowed = {vendor_id for vendor_id, _name, _seen in EXTRA_VENDORS} - VOLUME_CASH_EXCLUDE
    rows = [row for row in ctx.vendors.values() if row["vendor_id"] in allowed]
    if not rows:
        raise ValueError("no safe counterparties for September volume bank lines")
    return rows


def expand_september_bank(ctx: CompanyScenarioContext, rng: random.Random) -> None:
    vendors = _volume_cash_vendors(ctx)
    needed = 210 - len(ctx.bank_transactions)
    if needed <= 0:
        return
    for index in range(1, needed + 1):
        vendor = vendors[index % len(vendors)]
        day = 1 + (index % 28)
        txn_date = f"2026-09-{day:02d}"
        amount_minor = -(100_000 + index * 17)
        if index % 7 == 0:
            amount_minor = abs(amount_minor)
        txn_id = f"TXN-VOL-2026-09-{index:03d}"
        ledger_id = f"GL-VOL-2026-09-{index:03d}"
        if txn_id in ctx.bank_transactions:
            continue
        difficulty = "exact"
        reference = f"ACH-{index:04d}"
        description = f"ACH {'IN' if amount_minor > 0 else 'OUT'} {vendor['name'].upper()}"
        if index % 11 == 0:
            difficulty = "degraded_ref"
            reference = f"{vendor['name'][:6].upper()} {day:02d}"
            description = f"{vendor['name'].split()[0].upper()} 09{day:02d} SETTLEMENT"
        elif index % 19 == 0:
            difficulty = "unbundle_leg"
            description = f"ACH OUT {vendor['name'].upper()} BATCH LEG {index % 3 + 1}"
        elif index % 23 == 0:
            difficulty = "fee_inclusive"
            description = f"WIRE {vendor['name'].upper()} INCL WIRE CHG"
        ctx.bank_transactions[txn_id] = cash_bank(
            txn_id,
            txn_date,
            amount_minor,
            description=description,
            reference=reference,
            counterparty=vendor["name"].upper(),
            transaction_type="ach_credit" if amount_minor > 0 else "ach_debit",
            metadata={"volume": True, "difficulty": difficulty, "vendor_id": vendor["vendor_id"]},
        )
        _safe_named(ctx, txn_id)
        ctx.ledger_cash[ledger_id] = cash_ledger(
            ledger_id,
            txn_date,
            amount_minor,
            counterparty=vendor["name"],
            reference=reference if difficulty != "degraded_ref" else txn_id,
            description=f"Books {vendor['name']} {txn_date}",
            entry_type="ar_receipt" if amount_minor > 0 else "ap_payment",
            metadata={"volume": True, "bank_id": txn_id},
        )
        _safe_named(ctx, ledger_id)
        ctx.recon_labels[txn_id] = {
            "match_type": "EXACT_MATCH",
            "disposition": "MATCHED",
            "ledger_ids": [ledger_id],
        }
        je_id = f"JE-{ledger_id}"
        if je_id not in ctx.journal_entries:
            if amount_minor < 0:
                debit, credit = "6000-Operating", "1000-Cash"
            else:
                debit, credit = "1000-Cash", "1100-AR"
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=je_id,
                    period="2026-09",
                    effective_date=txn_date,
                    posting_date=txn_date,
                    posting_timestamp=f"{txn_date}T14:00:00Z",
                    debit_account=debit,
                    credit_account=credit,
                    amount_minor=abs(amount_minor),
                    memo=description,
                    vendor=vendor["name"] if amount_minor < 0 else "",
                    source_document_id=txn_id,
                    transaction_id=txn_id,
                    entry_type="volume_cash",
                    category="volume_opex" if amount_minor < 0 else "volume_cash",
                )
            )


def add_bank_history(ctx: CompanyScenarioContext, rng: random.Random) -> None:
    vendors = [row for row in ctx.vendors.values() if not row.get("unusual")]
    seq = 0
    for period in HIST_PERIODS + ("2026-08", "2026-10"):
        year_i, month_i = (int(part) for part in period.split("-"))
        last = calendar.monthrange(year_i, month_i)[1]
        account = "BANK-OPERATING" if period != "2026-10" else "BANK-OPERATING"
        for day in range(1, last + 1):
            for slot in range(7):
                seq += 1
                vendor = vendors[(seq + slot) % len(vendors)]
                amount_minor = -((900 + (seq * 41) % 6200) * 100)
                if slot == 0:
                    amount_minor = abs(amount_minor)
                txn_date = f"{period}-{day:02d}"
                ctx.bank_history.append(
                    {
                        "transaction_id": f"TXN-HIST-{period}-{seq:04d}",
                        "bank_account": account if slot != 3 else "BANK-PAYROLL",
                        "date": txn_date,
                        "amount_minor": amount_minor,
                        "amount": dollars(amount_minor),
                        "currency": "USD",
                        "counterparty": vendor["name"],
                        "reference": f"HIST-{seq:04d}",
                        "description": f"{'IN' if amount_minor > 0 else 'OUT'} {vendor['name']}",
                        "period": period,
                    }
                )


def add_employee_master(ctx: CompanyScenarioContext) -> None:
    """W-2 register at catalog headcount. Identity-bible rows keep catalog IDs."""
    from sample_data.pnl import BIWEEKLY_PAYROLL_GROSS, W2_HEADCOUNT

    first = (
        "Alex", "Blair", "Casey", "Drew", "Eden", "Finley", "Gray", "Harper",
        "Indigo", "Jules", "Kai", "Logan", "Morgan", "Noel", "Oakley", "Parker",
        "Quinn", "Reese", "Sage", "Taylor", "Uma", "Val", "Winter", "Xen",
    )
    last = (
        "Abbott", "Bennett", "Clarke", "Diaz", "Ellis", "Foster", "Greene",
        "Hayes", "Ingram", "Jones", "Khan", "Lopez", "Meyer", "Ng", "Ortiz",
        "Patel", "Quinn", "Ross", "Shah", "Turner", "Upton", "Vega", "Walsh",
        "Young",
    )
    depts = ("Engineering", "Sales", "Finance", "Operations", "G&A", "Customer Success", "Warehouse")
    seen = {row[0] for row in EMPLOYEES} | {row[0] for row in IDENTITY_EMPLOYEES}
    rows: list[dict] = []
    for emp_id, name, dept, annual in EMPLOYEES:
        rows.append(_employee_row(emp_id, name, dept, annual, "Cambridge, MA", "active"))
    for emp_id, name, dept, annual, _usr in IDENTITY_EMPLOYEES:
        status = "terminated" if emp_id == "EMP-2290" else "active"
        location = "Remote" if emp_id == "EMP-8891" else "Cambridge, MA"
        rows.append(_employee_row(emp_id, name, dept, annual, location, status))
    seq = 1000
    while len(rows) < W2_HEADCOUNT:
        emp_id = f"EMP-{seq:04d}"
        seq += 1
        if emp_id in seen:
            continue
        seen.add(emp_id)
        name = f"{first[seq % len(first)]} {last[(seq * 3) % len(last)]}"
        dept = depts[seq % len(depts)]
        annual = 72000 + (seq * 137) % 90000
        rows.append(_employee_row(emp_id, name, dept, annual, "Cambridge, MA", "active"))
    # Scale filler gross so one pay period equals the catalog biweekly total.
    named_ids = {row[0] for row in IDENTITY_EMPLOYEES}
    named_gross = 0.0
    filler = []
    for row in rows:
        gross = round(row["annual_salary"] / 26.0, 2)
        row["biweekly_gross"] = gross
        if row["employee_id"] in named_ids:
            named_gross = round(named_gross + gross, 2)
        else:
            filler.append(row)
    target_filler = round(BIWEEKLY_PAYROLL_GROSS - named_gross, 2)
    current_filler = round(sum(item["biweekly_gross"] for item in filler), 2)
    if filler and abs(current_filler - target_filler) > 0.009:
        scale = target_filler / current_filler if current_filler else 1.0
        running = 0.0
        for item in filler[:-1]:
            item["biweekly_gross"] = round(item["biweekly_gross"] * scale, 2)
            running = round(running + item["biweekly_gross"], 2)
        filler[-1]["biweekly_gross"] = round(target_filler - running, 2)
    ctx.employee_master = rows
    for row in rows:
        _safe_named(ctx, row["employee_id"])
    ctx.legal_entity_register = [
        {
            "entity_id": "CO-MAXIMOR",
            "legal_name": "Maximor Demo Corp",
            "jurisdiction": "MA",
            "ein": "04-3829107",
            "status": "active",
            "parent_id": "",
        }
    ]
    ctx.facilities_registry = [
        {
            "site_id": "CAM-HQ",
            "name": "Cambridge headquarters",
            "address": "245 Main Street, Cambridge, MA 02142",
            "type": "office",
        },
        {
            "site_id": "CAM-WH-01",
            "name": "Cambridge warehouse",
            "address": "90 Binney Street, Cambridge, MA 02142",
            "type": "warehouse",
        },
        {
            "site_id": "3PL-BOS",
            "name": "Boston 3PL",
            "address": "1 Terminal Road, Boston, MA 02128",
            "type": "3pl",
        },
    ]
    ctx.warehouse_locations = [
        {
            "location_id": "CAM-BIN-A14",
            "site_id": "CAM-WH-01",
            "bin": "A14",
            "sku_prefix": "KIS-MRO-7",
        },
        {
            "location_id": "CAM-WH-01-CAGE-B",
            "site_id": "CAM-WH-01",
            "bin": "CAGE-B",
            "consignment_customer": "CUST-006",
            "label": "consignment hold",
        },
        {
            "location_id": "CAM-DOCK-4",
            "site_id": "CAM-WH-01",
            "bin": "DOCK-4",
            "sku_prefix": "NLF",
        },
    ]
    ctx.org_chart = [
        {"emp_id": "EMP-0901", "title": "Procurement manager", "manager_emp_id": "EMP-0902", "org": "Procurement"},
        {"emp_id": "EMP-0902", "title": "Finance manager", "manager_emp_id": "", "org": "Finance"},
        {"emp_id": "EMP-5510", "title": "Payroll administrator", "manager_emp_id": "EMP-0902", "org": "Finance"},
        {"emp_id": "EMP-4128", "title": "AP vendor-master clerk", "manager_emp_id": "EMP-0902", "org": "Finance"},
        {"emp_id": "EMP-1088", "title": "Assistant controller", "manager_emp_id": "EMP-0902", "org": "Finance"},
        {"emp_id": "EMP-3304", "title": "AR cash applier", "manager_emp_id": "EMP-1088", "org": "Finance"},
        {"emp_id": "EMP-1190", "title": "Revenue accountant", "manager_emp_id": "EMP-1088", "org": "Finance"},
        {"emp_id": "EMP-4402", "title": "Processor operations", "manager_emp_id": "EMP-0902", "org": "Finance"},
        {"emp_id": "EMP-2201", "title": "Facilities coordinator", "manager_emp_id": "EMP-0902", "org": "Facilities"},
        {"emp_id": "EMP-6722", "title": "Warehouse receiving", "manager_emp_id": "", "org": "Cambridge warehouse"},
        {"emp_id": "EMP-8891", "title": "Remote warehouse coordinator — West", "manager_emp_id": "", "org": "West Warehouse"},
        {"emp_id": "EMP-2290", "title": "Warehouse associate", "manager_emp_id": "", "org": "West Warehouse", "last_day": "2026-03-31"},
        {"emp_id": "EMP-3310", "title": "Marketing manager", "manager_emp_id": "EMP-0902", "org": "Marketing"},
        {"seat_id": "WEST-WH-MGR", "org": "West Warehouse", "title": "West Warehouse manager", "emp_id": "", "vacant_since": "2025-03-31"},
    ]
    orphans = ["EMP-1001", "EMP-1002", "EMP-1003", "EMP-1004", "EMP-1005", "EMP-1006"]
    for emp_id in orphans:
        ctx.org_chart.append(
            {"emp_id": emp_id, "title": "Warehouse associate", "manager_emp_id": "", "org": "West Warehouse"}
        )


def _employee_row(emp_id: str, name: str, department: str, annual: int, location: str, status: str) -> dict:
    parts = name.split(" ", 1)
    home = "245 Main Street, Cambridge, MA 02142"
    return {
        "employee_id": emp_id,
        "full_name": name,
        "first_name": parts[0],
        "last_name": parts[1] if len(parts) > 1 else "",
        "department": department,
        "annual_salary": annual,
        "location": location,
        "status": status,
        "hire_date": "2021-04-12",
        "last_day": "2026-03-31" if emp_id == "EMP-2290" else "",
        "home_address": home,
        "emergency_contact": "",
        "okta_user": f"USR-{emp_id[-4:]}",
        "manager_emp_id": "",
    }


def add_payroll_register(ctx: CompanyScenarioContext) -> None:
    if not ctx.employee_master:
        add_employee_master(ctx)
    periods = []
    cursor = date(2025, 10, 3)
    end = date(2026, 9, 25)
    while cursor <= end:
        periods.append(cursor)
        cursor += timedelta(days=14)
    from sample_data.pnl import BIWEEKLY_PAYROLL_GROSS

    for pay_date in periods:
        period_start = (pay_date - timedelta(days=13)).isoformat()
        period_end = pay_date.isoformat()
        period_gross = 0.0
        for emp in ctx.employee_master:
            if emp["status"] == "terminated" and emp.get("last_day") and pay_date.isoformat() > emp["last_day"]:
                # Ava Pell remains on the register after last_day; skip others.
                if emp["employee_id"] != "EMP-2290":
                    continue
            gross = float(emp.get("biweekly_gross") or round(emp["annual_salary"] / 26.0, 2))
            if emp["employee_id"] == "EMP-8891":
                gross = 4180.27
            ee_tax = round(gross * 0.0765, 2)
            net = round(gross - ee_tax - 95.0, 2)
            period_gross = round(period_gross + gross, 2)
            ctx.payroll_register.append(
                {
                    "pay_date": pay_date.isoformat(),
                    "period_start": period_start,
                    "period_end": period_end,
                    "employee_id": emp["employee_id"],
                    "full_name": emp["full_name"],
                    "department": emp["department"],
                    "annual_salary": emp["annual_salary"],
                    "gross_pay": gross,
                    "employee_taxes": ee_tax,
                    "benefits": 95.0,
                    "net_pay": net,
                    "employer_cost": round(gross * 1.0765 + 95.0, 2),
                    "location": emp.get("location") or "Cambridge, MA",
                    "bank_account": "BANK-PAYROLL",
                    "direct_deposit_last4": "",
                }
            )
        je_id = f"JE-PRREG-{pay_date.isoformat()}"
        total = int(round(period_gross * 100))
        if je_id not in ctx.journal_entries and pay_date.isoformat()[:7] not in {"2026-08", "2026-09"}:
            ctx.add_journal(
                JournalEntryRecord(
                    entry_id=je_id,
                    period=pay_date.isoformat()[:7],
                    effective_date=pay_date.isoformat(),
                    posting_date=pay_date.isoformat(),
                    posting_timestamp=f"{pay_date.isoformat()}T16:00:00Z",
                    debit_account="6100-Payroll",
                    credit_account="1000-Cash",
                    amount_minor=max(total, 1),
                    memo=f"Biweekly payroll {pay_date.isoformat()}",
                    source_document_id=f"PR-{pay_date.isoformat()}",
                    transaction_id=f"TXN-PRREG-{pay_date.isoformat()}",
                    entry_type="payroll",
                    category="volume_payroll",
                )
            )
    # Keep the catalog biweekly identity on the last September run.
    if ctx.payroll_register:
        _ = BIWEEKLY_PAYROLL_GROSS


def add_processor_volume(ctx: CompanyScenarioContext, rng: random.Random) -> None:
    customers = list(ctx.customers.values())
    schemes = ("Visa", "Mastercard", "NexPay", "GlobalCard", "Amex")
    start = date(2025, 10, 1)
    for index in range(1, 3001):
        customer = customers[index % len(customers)]
        day = start + timedelta(days=index % 350)
        amount = round(18.0 + (index * 7.13) % 420.0, 2)
        ctx.processor_transactions.append(
            {
                "psp_reference": f"MX-{100000000 + index}",
                "merchant": "Maximor Demo Corp",
                "customer_id": customer.customer_id,
                "customer_name": customer.customer_name,
                "card_scheme": schemes[index % len(schemes)],
                "year": day.year,
                "hour_of_day": index % 24,
                "minute_of_hour": (index * 3) % 60,
                "day_of_year": int(day.strftime("%j")),
                "is_credit": index % 17 == 0,
                "usd_amount": amount,
                "amount_minor": int(round(amount * 100)),
                "currency": "USD",
                "ip_country": "US",
                "issuing_country": "US",
                "device_type": ("Windows", "MacOS", "iOS", "Android")[index % 4],
                "shopper_interaction": "Ecommerce",
                "has_fraudulent_dispute": False,
                "is_refused_by_adyen": False,
                "processor": "stripe" if index % 5 else "adyen",
                "settled_date": day.isoformat(),
            }
        )


def add_fiscal_calendar(ctx: CompanyScenarioContext) -> None:
    periods = list(HIST_PERIODS) + ["2026-08", "2026-09", "2026-10"]
    for period in periods:
        if period == "2026-09":
            status = "OPEN"
            note = "September close starts blocked on TXN-2026-09-015."
        elif period == "2026-10":
            status = "FUTURE"
            note = "Thin future tail: Harbor Electric / legal invoices arrive."
        else:
            status = "CLOSED"
            note = "Prior closed period."
        ctx.fiscal_periods.append(
            {
                "period": period,
                "status": status,
                "period_start": _period_start(period),
                "period_end": _period_end(period),
                "currency": "USD",
                "entity": "CO-MAXIMOR",
                "note": note,
            }
        )
    ctx.bank_account_master = [
        {
            "account_id": "BANK-OPERATING",
            "name": "First National operating",
            "gl_account": "1000-Cash",
            "currency": "USD",
            "routing": "011000390",
            "last4": "9107",
        },
        {
            "account_id": "BANK-PAYROLL",
            "name": "First National payroll",
            "gl_account": "1010-Payroll-Imprest",
            "currency": "USD",
            "routing": "011000390",
            "last4": "2281",
        },
        {
            "account_id": "BANK-RESERVE",
            "name": "Cambridge Trust reserve",
            "gl_account": "1020-Reserve-Cash",
            "currency": "USD",
            "routing": "011300135",
            "last4": "4402",
        },
    ]
    ctx.approval_matrix = [
        {"role": "AP preparer", "limit": 25000.0, "objects": ["invoice"]},
        {"role": "AP reviewer", "limit": 100000.0, "objects": ["invoice", "payment"]},
        {"role": "Controller", "limit": 250000.0, "objects": ["invoice", "payment", "journal"]},
        {"role": "CFO", "limit": None, "objects": ["journal", "close"]},
    ]


CATALOG_COA: tuple[tuple[str, str, str], ...] = (
    ("1000-Cash", "Cash", "cash"),
    ("1010-Payroll-Imprest", "Payroll imprest", "cash"),
    ("1020-Stripe-Clearing", "Stripe clearing", "cash"),
    ("1030-Undeposited-Funds", "Undeposited funds", "cash"),
    ("1100-AR", "Accounts receivable", "ar"),
    ("1110-AR-Unapplied", "AR unapplied cash", "ar"),
    ("1200-Prepaid-Software", "Prepaid software", "other"),
    ("1210-Prepaid-Insurance", "Prepaid insurance", "other"),
    ("1220-Prepaid-Other", "Prepaid other", "other"),
    ("1300-Due-From-Affiliate", "Due from affiliate", "other"),
    ("1350-Other-Receivable", "Other receivable", "other"),
    ("1400-Inventory", "Inventory", "other"),
    ("1500-PPE", "Property plant and equipment", "other"),
    ("1510-Accum-Dep", "Accumulated depreciation", "other"),
    ("2000-AP", "Accounts payable", "ap"),
    ("2100-Due-To-Affiliate", "Due to affiliate", "other"),
    ("2200-Payroll-Accrual", "Payroll accrual", "other"),
    ("2300-Deferred-Revenue", "Deferred revenue", "other"),
    ("4000-Revenue", "Revenue", "revenue"),
    ("4100-Contra-Revenue-Returns", "Contra revenue returns", "revenue"),
    ("5100-Hosting", "Cloud hosting", "cogs"),
    ("5200-Supplier", "Supplier COGS", "cogs"),
    ("5300-Freight", "Freight", "cogs"),
    ("5400-Other-COGS", "Other COGS", "cogs"),
    ("5400-Contractors", "Contractors", "opex"),
    ("6000-Operating", "Operating expenses", "opex"),
    ("6100-Payroll", "Payroll", "opex"),
    ("6200-Benefits", "Benefits", "opex"),
    ("6300-Occupancy", "Occupancy", "opex"),
    ("6400-Professional-Fees", "Professional fees", "opex"),
    ("6500-Bank-Fees", "Bank fees", "opex"),
    ("6600-Processor-Fees", "Processor fees", "opex"),
    ("6900-Misc-Expense", "Miscellaneous expense", "opex"),
    ("6950-Cash-Over-Short", "Cash over short", "opex"),
)


def add_chart(ctx: CompanyScenarioContext) -> None:
    extra = [
        ChartAccount(account_id=account_id, name=name, account_class=account_class)  # type: ignore[arg-type]
        for account_id, name, account_class in CATALOG_COA
    ]
    extra.extend(
        [
            ChartAccount(account_id="1010-Payroll-Cash", name="Payroll cash", account_class="cash", aliases=["1010-Payroll-Imprest"]),
            ChartAccount(account_id="1020-Reserve-Cash", name="Reserve cash", account_class="cash"),
            ChartAccount(account_id="1200-Prepaid", name="Prepaid assets", account_class="other"),
            ChartAccount(account_id="1500-FixedAssets", name="Computer equipment", account_class="other"),
            ChartAccount(account_id="2100-Accrued", name="Accrued expenses", account_class="other"),
            ChartAccount(account_id="6200-Facilities", name="Facilities", account_class="opex"),
            ChartAccount(account_id="6300-Software", name="Software subscriptions", account_class="opex"),
            ChartAccount(account_id="Utilities Expense", name="Utilities", account_class="opex"),
            ChartAccount(account_id="Legal Expense", name="Legal", account_class="opex"),
            ChartAccount(account_id="Insurance Expense", name="Insurance", account_class="opex"),
            ChartAccount(account_id="Depreciation Expense", name="Depreciation", account_class="opex"),
            ChartAccount(account_id="Software Subscription Expense", name="Software amortization", account_class="opex"),
            ChartAccount(account_id="Prepaid Insurance", name="Prepaid insurance", account_class="other"),
            ChartAccount(account_id="Prepaid Software", name="Prepaid software", account_class="other"),
            ChartAccount(account_id="Computer Equipment", name="Computer equipment", account_class="other"),
            ChartAccount(account_id="Accumulated Depreciation - Equipment", name="Accumulated depreciation", account_class="other"),
            ChartAccount(account_id="Accrued Expenses", name="Accrued expenses", account_class="other"),
            ChartAccount(account_id="Consulting Expense", name="Consulting", account_class="opex"),
        ]
    )
    known = {item.account_id for item in ctx.chart}
    for item in extra:
        if item.account_id not in known:
            ctx.chart.append(item)
            known.add(item.account_id)


def add_august_close_pack(ctx: CompanyScenarioContext) -> None:
    aug_jes = [item for item in ctx.journal_entries.values() if item.period == "2026-08"]
    trial = {}
    for entry in aug_jes:
        trial[entry.debit_account] = trial.get(entry.debit_account, 0) + entry.amount_minor
        trial[entry.credit_account] = trial.get(entry.credit_account, 0) - entry.amount_minor
    ctx.august_close_pack = {
        "period": "2026-08",
        "status": "CLOSED",
        "close_id": "CLOSE-2026-08",
        "closed_at": "2026-09-03T18:00:00Z",
        "closed_by": "agent:close-orchestrator",
        "trial_balance": [
            {"account": account, "amount_minor": amount, "amount": dollars(amount)}
            for account, amount in sorted(trial.items())
        ],
        "tasks": [
            {"task_id": "TASK-AUG-CASH", "status": "COMPLETE", "evidence": "August bank rec tied"},
            {"task_id": "TASK-AUG-AP", "status": "COMPLETE", "evidence": "August AP subledger tied"},
            {"task_id": "TASK-AUG-AR", "status": "COMPLETE", "evidence": "August AR subledger tied"},
            {"task_id": "TASK-AUG-FINAL", "status": "COMPLETE", "evidence": "August signed off 2026-09-03"},
        ],
    }
    ctx.workpapers["close/prior_period/2026-08/cash_rec.txt"] = render_workpaper(
        "August 2026 operating bank reconciliation",
        "2026-08",
        preparer="Cash Reconciliation Preparer",
        reviewer="Cash Reconciliation Reviewer",
        status="COMPLETE",
        body=(
            "Opening book cash agreed to July close. August deposits and disbursements "
            "were sampled against the First National operating statement. Outstanding "
            "timing items cleared in the first week of September. No unexplained difference "
            "remained at sign-off. September will compare against this pack.\n"
            "Identities carried: CASE-001 (Acme alias), AR-PREC-003 (Meridian unlabeled ACH), "
            "Harbor Electric methodology CTR-HE-001 / HI-HE-2026-08."
        ),
    )
    ctx.workpapers["close/prior_period/2026-08/ap_tie.txt"] = render_workpaper(
        "August 2026 AP subledger tie",
        "2026-08",
        preparer="AP Preparer",
        reviewer="AP Reviewer",
        status="COMPLETE",
        body=(
            "AP trial balance agrees to account 2000-AP. Sampled invoices include the "
            "Acme Supply Co. alias later reused as INV-021. No held invoices were released."
        ),
    )
    ctx.workpapers["close/prior_period/2026-08/ar_tie.txt"] = render_workpaper(
        "August 2026 AR subledger tie",
        "2026-08",
        preparer="Cash Application Agent",
        reviewer="Cash Application Reviewer",
        status="COMPLETE",
        body=(
            "AR aging at August 31 agreed to 1100-AR. Atlas batch-payer pattern recorded "
            "as AR-PREC-001 / AR-PREC-004. Quiet Harbor remained past due; no cash applied."
        ),
    )
    ctx.workpapers["close/prior_period/2026-08/signoff.txt"] = render_workpaper(
        "August 2026 close sign-off",
        "2026-08",
        preparer="Close Manager",
        reviewer="Month-End Close Reviewer",
        status="COMPLETE",
        body=(
            "Period 2026-08 is closed. CLOSE-2026-08. Materiality $1,000. "
            "September is the next open period and starts blocked until cash rec completes."
        ),
    )
    ctx.workpapers["close/2026-09/cash_rec.txt"] = render_workpaper(
        "September 2026 operating bank reconciliation",
        "2026-09",
        preparer="Cash Reconciliation Preparer",
        reviewer="Cash Reconciliation Reviewer",
        status="BLOCKED",
        body=(
            "Most September items match, including the Acme ACH TXN-2026-09-018A, the "
            "Northline grouped disbursement TXN-2026-09-008, and the Helios wire TXN-2026-09-011 "
            "which is $25 net of FEE-729103.\n"
            "Open item: bank TXN-2026-09-015 posts $12,412.40 from Northstar LLC; ledger "
            "GL-AR-NS / PAY-006 / INV-AR-013 remains $12,400.00. Difference $12.40. "
            "No fee advice supports the gap. TASK-CASH stays blocked. "
            "Do not force a match."
        ),
    )
    ctx.workpapers["close/2026-09/ap_tie.txt"] = render_workpaper(
        "September 2026 AP subledger tie",
        "2026-09",
        preparer="AP Preparer",
        reviewer="AP Reviewer",
        status="COMPLETE",
        body=(
            "INV-001 three-way match to PO-101 / GR-101. Held items remain INV-003 through "
            "INV-010 as listed in the AP exceptions file. Dell INV-018 capitalized. "
            "Hartford INV-019 prepaid."
        ),
    )
    ctx.workpapers["close/2026-09/accruals.txt"] = render_workpaper(
        "September 2026 missing-bill accruals",
        "2026-09",
        preparer="Accrual Agent",
        reviewer="Month-End Close Reviewer",
        status="COMPLETE",
        body=(
            "Harbor Electric ACC-HE-2026-09 $4,780 from CTR-HE-001 and HI-HE-2026-08. "
            "Lindholm & Ruiz ACC-LR-2026-09 $8,500 from CTR-LR-001. "
            "October bills INV-HE-2026-09 and INV-LR-2026-09 are the reversal candidates."
        ),
    )
    ctx.workpapers["close/2026-09/final_review.txt"] = render_workpaper(
        "September 2026 final close review",
        "2026-09",
        preparer="Close Manager",
        reviewer="Month-End Close Reviewer",
        status="BLOCKED",
        body=(
            "Final review cannot complete while TASK-CASH is blocked on the $12.40 "
            "Northstar difference (TXN-2026-09-015). Balance-sheet rec TASK-BS depends "
            "on the same item. Compare every tie to the August pack under close/prior_period/2026-08/."
        ),
    )


def add_round2_hooks(ctx: CompanyScenarioContext) -> None:
    ctx.round2_hooks = {
        "note": (
            "Private holdout. Operational Email/AP/Audit Bots must not load this file. "
            "Round 2 may add rows to these registers without rewriting plot IDs."
        ),
        "seed": ctx.seed,
        "stable_id_prefixes": [
            "INV-",
            "HAP-",
            "TXN-",
            "TXN-VOL-",
            "TXN-HIST-",
            "JE-",
            "VEND-",
            "GL-",
            "GL-VOL-",
            "CUST-",
            "EMP-",
        ],
        "do_not_retarget": [
            "INV-001",
            "PO-101",
            "GR-101",
            "INV-017",
            "INV-AR-013",
            "PAY-006",
            "TXN-2026-09-015",
            "GL-AR-NS",
            "PAY-AP-009",
            "JE-POST-CLOSE-001",
            "VEND-001",
            "VEND-001-DUP",
        ],
        "vendor_near_duplicates": [
            {
                "a": "VEND-001",
                "b": "VEND-001-DUP",
                "relation": "normalize_vendor already collapses this pair",
            },
            {
                "a": "VEND-003",
                "b": "VEND-030",
                "relation": "similar legal name, different tax ID and bank — not labeled",
            },
            {
                "a": "VEND-005",
                "b": "VEND-031",
                "relation": "similar legal name, different tax ID and bank — not labeled",
            },
            {
                "a": "VEND-015",
                "b": "VEND-032",
                "relation": "similar utility name, different tax ID and bank — not labeled",
            },
        ],
        "registers": {
            "ap_history": "registers/ap_history.csv",
            "gl_detail": "registers/gl_detail.csv",
            "bank_history": "registers/bank_history.csv",
            "payroll": "registers/payroll_register.csv",
            "processor": "integrations/processor/card_transactions.csv",
            "vendor_master": "canonical/vendors.json",
            "september_bank": "cash_recon/bank_statement.json",
        },
        "headroom": (
            "Phase B planted. Trailing AP, GL, bank, payroll, and processor files "
            "carry the catalog siphons. Plot IDs in do_not_retarget stay intact. "
            "Hidden answers live in expected_results.json adversarial_holdout."
        ),
        "scenario_registry": "canonical/scenarios.json",
        "reference_sampled": {
            "invoice_sandbox": "document letterhead/line-item bar; gold_master PDFs not copied",
            "apex_accounting": "workpaper density; company remains Maximor Demo Corp",
            "dabstep": "processor column layout and 3,000-tx volume, merchants remapped",
            "recbench": "degraded_ref / unbundle_leg / fee_inclusive description patterns on volume bank lines",
        },
    }


def sampled_reference_note() -> dict:
    dabstep = REFERENCE_ROOT / "dabstep" / "data" / "context" / "payments.csv"
    recbench = REFERENCE_ROOT / "recbench" / "small" / "csv" / "labels_bank.csv"
    invoices = REFERENCE_ROOT / "invoice-sandbox-benchmark" / "gold_master" / "invoices"
    apex = REFERENCE_ROOT / "apex-accounting" / "world"
    return {
        "invoice_sandbox_pdfs_present": invoices.is_dir(),
        "apex_world_present": apex.is_dir(),
        "dabstep_payments_present": dabstep.is_file(),
        "recbench_labels_present": recbench.is_file(),
        "finance_agent_benchmark": "not loaded",
    }


def expand_operating_world(ctx: CompanyScenarioContext) -> None:
    rng = random.Random(ctx.seed)
    add_extra_vendors(ctx)
    enrich_customers(ctx)
    add_live_ap_volume(ctx, rng)
    add_extra_ar(ctx)
    add_documents(ctx)
    upgrade_ingestion_emails(ctx)


def expand_registers(ctx: CompanyScenarioContext) -> None:
    rng = random.Random(ctx.seed + 1)
    add_employee_master(ctx)
    add_historical_ap_register(ctx, rng)
    add_trailing_pnl(ctx)
    expand_september_bank(ctx, rng)
    add_bank_history(ctx, rng)
    add_payroll_register(ctx)
    add_processor_volume(ctx, rng)
    add_fiscal_calendar(ctx)
    add_chart(ctx)
    add_august_close_pack(ctx)
    add_round2_hooks(ctx)
