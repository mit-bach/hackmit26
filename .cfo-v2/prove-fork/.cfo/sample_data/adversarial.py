"""Catalog plants for Maximor Demo Corp.

Called only from ``generate_sample_data``. Operational Bots never import this
module. Reason codes live on the private holdout, not on invoices or vendors.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from ar.models import Customer, CustomerInvoice, CustomerPayment
from models import CompanyPolicy, GoodsReceipt, Invoice, PurchaseOrder
from prepaid.models import PrepaidItem, PrepaidScheduleLine
from reporting.models import ForecastLine
from cash_recon.models import FeeEvidence

from sample_data.adapters import cash_bank, cash_ledger
from sample_data.context import CompanyScenarioContext, cents, dollars
from sample_data.documents import invoice_document_for, render_vendor_invoice
from sample_data.models import (
    AdversarialHoldoutItem,
    JournalEntryRecord,
    VendorPayment,
)
from sample_data.pnl import (
    AP_OPEN,
    AR_OPEN,
    BIWEEKLY_PAYROLL_GROSS,
    COGS_ACCOUNTS,
    CONTRACTOR_1099_COUNT,
    ACTIVE_VENDORS,
    INTENDED_COGS_MINOR,
    INTENDED_REVENUE_MINOR,
    OPERATING_CASH_2026_09_30,
    REVENUE_ACCOUNTS,
)
from sample_data.world import add_documents, _safe_named


INDEX_PATH = (
    Path(__file__).resolve().parents[2]
    / ".cfo-v2"
    / "office"
    / "sessions"
    / "adversarial-scenarios.index.json"
)

KESTREL_HOME = "18 Ware Street, Cambridge, MA 02138"
FAYETTE = "14 Fayette Street, Somerville, MA 02143"
HALYARD_ROUTING = "211370545"
HALYARD_ACCOUNT = "10009022"
KESTREL_ROUTING = "011000138"
KESTREL_OLD_ACCOUNT = "10004401"
KESTREL_NEW_ACCOUNT = "10004419"

# VEND-KIS-01 monthly invoices. Jul–Sep (after 2026-06-12) = 62,118.90.
# All eleven months = 187,412.18.
KIS_MONTHLY: dict[str, float] = {
    "2025-11": 14206.18,
    "2025-12": 14880.40,
    "2026-01": 15220.22,
    "2026-02": 15880.18,
    "2026-03": 16240.44,
    "2026-04": 16820.62,
    "2026-05": 17420.18,
    "2026-06": 14625.06,
    "2026-07": 17831.96,
    "2026-08": 19406.50,
    "2026-09": 24880.44,
}

# 10 plugs 2025-11..2026-08. August is the named $7,206.18.
REC_PLUGS: dict[str, float] = {
    "2025-11": 6842.18,
    "2025-12": 7120.40,
    "2026-01": 7455.22,
    "2026-02": 7688.90,
    "2026-03": 7912.44,
    "2026-04": 8214.66,
    "2026-05": 8420.18,
    "2026-06": 8544.22,
    "2026-07": 17014.22,
    "2026-08": 7206.18,
}


def plant_adversarial(ctx: CompanyScenarioContext) -> None:
    _assert_amount_tables()
    plant_identity_bible(ctx)
    plant_residual(ctx)
    plant_kestrel(ctx)
    plant_halyard(ctx)
    plant_orbit(ctx)
    plant_lapping(ctx)
    plant_pinnacle(ctx)
    plant_processor(ctx)
    plant_merrimack(ctx)
    plant_brightline(ctx)
    plant_cambridge(ctx)
    plant_closecosmetic(ctx)
    plant_freight(ctx)
    densify_open_subledgers(ctx)
    add_documents(ctx)


def finish_adversarial(ctx: CompanyScenarioContext) -> None:
    overlay_forecast(ctx)
    overlay_policies_and_workpapers(ctx)
    set_cash_and_company(ctx)
    attach_holdout(ctx)
    if ctx.audit_invoices and not any(item.invoice_id == "AUD-SAMP-KIS-08" for item in ctx.audit_invoices):
        ctx.audit_invoices.append(
            ctx.audit_invoices[0].model_copy(
                update={
                    "invoice_id": "AUD-SAMP-KIS-08",
                    "vendor": "Kestrel Industrial Supply LLC",
                    "vendor_id": "VEND-KIS-01",
                    "amount": KIS_MONTHLY["2026-02"],
                    "invoice_date": "2026-02-08",
                }
            )
        )


def fill_scale_pnl(ctx: CompanyScenarioContext) -> None:
    """Top up 4000 / COGS so board totals match the catalog table."""
    for period, intended in INTENDED_REVENUE_MINOR.items():
        actual = sum(
            item.amount_minor
            for item in ctx.journal_entries.values()
            if item.period == period and item.credit_account in REVENUE_ACCOUNTS
        )
        gap = intended - actual
        if gap < 0:
            raise ValueError(f"revenue {period} {actual} exceeds intended {intended}")
        if gap == 0:
            continue
        end = f"{period}-{30 if period.endswith('09') else 31}"
        if period.endswith("02"):
            end = f"{period}-28"
        _je(
            ctx,
            f"JE-SCALE-REV-{period}",
            period=period,
            date=end,
            debit="1100-AR",
            credit="4000-Revenue",
            amount_minor=gap,
            memo=f"{period} platform and services billings",
            customer="Northwind Labs",
            product="Platform",
            source=f"INV-SCALE-REV-{period}",
            txn=f"TXN-SCALE-REV-{period}",
            category="revenue",
            entry_type="ar_invoice",
        )
        _je(
            ctx,
            f"JE-SCALE-REV-CASH-{period}",
            period=period,
            date=end,
            debit="1000-Cash",
            credit="1100-AR",
            amount_minor=gap,
            memo=f"{period} collections on scale billings",
            customer="Northwind Labs",
            source=f"INV-SCALE-REV-{period}",
            txn=f"TXN-SCALE-REV-CASH-{period}",
            category="volume_cash",
            entry_type="ar_receipt",
        )
    for period, intended in INTENDED_COGS_MINOR.items():
        actual = sum(
            item.amount_minor
            for item in ctx.journal_entries.values()
            if item.period == period and item.debit_account in COGS_ACCOUNTS
        )
        gap = intended - actual
        if gap < 0:
            raise ValueError(f"COGS {period} {actual} exceeds intended {intended}")
        if gap == 0:
            continue
        end = f"{period}-{30 if period.endswith('09') else 31}"
        _je(
            ctx,
            f"JE-SCALE-COGS-{period}",
            period=period,
            date=end,
            debit="5200-Supplier",
            credit="2000-AP",
            amount_minor=gap,
            memo=f"{period} contracted hardware and licenses",
            vendor="Acme Supplies",
            source=f"INV-SCALE-COGS-{period}",
            txn=f"TXN-SCALE-COGS-{period}",
            category="supplier",
            entry_type="ap_invoice",
        )
        _je(
            ctx,
            f"JE-SCALE-COGS-PAY-{period}",
            period=period,
            date=end,
            debit="2000-AP",
            credit="1000-Cash",
            amount_minor=gap,
            memo=f"Settle INV-SCALE-COGS-{period}",
            vendor="Acme Supplies",
            source=f"INV-SCALE-COGS-{period}",
            txn=f"TXN-SCALE-COGS-PAY-{period}",
            category="volume_cash",
            entry_type="ap_payment",
        )


def _assert_amount_tables() -> None:
    kis = round(sum(KIS_MONTHLY.values()), 2)
    if kis != 187412.18:
        raise ValueError(f"Kestrel monthly sum {kis} != 187412.18")
    after = round(KIS_MONTHLY["2026-07"] + KIS_MONTHLY["2026-08"] + KIS_MONTHLY["2026-09"], 2)
    if after != 62118.90:
        raise ValueError(f"Kestrel after-swap {after} != 62118.90")
    plugs = round(sum(REC_PLUGS.values()), 2)
    if plugs != 86418.60:
        raise ValueError(f"residual plugs {plugs} != 86418.60")
    if REC_PLUGS["2026-08"] != 7206.18:
        raise ValueError("August plug must be 7206.18")


def plant_identity_bible(ctx: CompanyScenarioContext) -> None:
    overlays = {
        "EMP-4128": {
            "home_address": KESTREL_HOME,
            "emergency_contact": "Evan Kestrel, 18 Ware Street, Cambridge MA 02138",
            "okta_user": "USR-VM-04",
            "okta_aliases": ["USR-VM-04", "USR-PREP-04"],
            "hire_date": "2022-08-15",
        },
        "EMP-1088": {
            "home_address": "9 Sacramento Street, Cambridge, MA 02138",
            "okta_user": "USR-JE-04",
            "okta_aliases": ["USR-JE-04", "USR-NA-VOSS"],
            "hire_date": "2019-02-08",
        },
        "EMP-8891": {
            "home_address": "PO Box 12, Reno, NV 89501",
            "okta_user": "",
            "hire_date": "2025-04-14",
        },
        "EMP-2290": {
            "last_day": "2026-03-31",
            "status": "terminated",
            "hire_date": "2020-01-06",
        },
        "EMP-2201": {
            "home_address": "40 Irving Street, Cambridge, MA 02138",
            "okta_user": "USR-FAC-01",
        },
        "EMP-3304": {
            "home_address": "88 Prospect Street, Cambridge, MA 02139",
            "okta_user": "USR-APPLY-02",
        },
        "EMP-3310": {
            "emergency_contact": f"Cara Bright, {FAYETTE}",
            "home_address": "21 Concord Avenue, Cambridge, MA 02138",
        },
        "EMP-6722": {"okta_user": "USR-GR-01", "hire_date": "2018-11-02"},
        "EMP-4402": {"okta_user": "USR-STRIPE-01"},
        "EMP-5510": {"okta_user": "USR-PR-01"},
        "EMP-1190": {"okta_user": "USR-REV-05"},
        "EMP-0901": {"po_approval_limit": 25000.0, "okta_user": "USR-APPR-HALE"},
    }
    by_id = {row["employee_id"]: row for row in ctx.employee_master}
    for emp_id, fields in overlays.items():
        row = by_id.get(emp_id)
        if row is not None:
            row.update(fields)
    ctx.user_map = [
        {"user_id": "USR-VM-04", "emp_id": "EMP-4128", "role": "ap_vendor_master"},
        {"user_id": "USR-PREP-04", "emp_id": "EMP-4128", "role": "ap_preparer"},
        {"user_id": "USR-JE-04", "emp_id": "EMP-1088", "role": "assistant_controller"},
        {"user_id": "USR-NA-VOSS", "emp_id": "EMP-1088", "role": "assistant_controller"},
        {"user_id": "USR-REV-04", "emp_id": "", "role": "distribution_list", "display": "rev-approvals@maximor.example"},
        {"user_id": "USR-REV-05", "emp_id": "EMP-1190", "role": "revenue"},
        {"user_id": "USR-APPLY-02", "emp_id": "EMP-3304", "role": "cash_apply"},
        {"user_id": "USR-FAC-01", "emp_id": "EMP-2201", "role": "facilities"},
        {"user_id": "USR-WH-2290", "emp_id": "EMP-2290", "role": "warehouse"},
        {"user_id": "USR-GR-01", "emp_id": "EMP-6722", "role": "receiving"},
        {"user_id": "USR-STRIPE-01", "emp_id": "EMP-4402", "role": "processor"},
        {"user_id": "USR-PR-01", "emp_id": "EMP-5510", "role": "payroll"},
        {"user_id": "USR-APPR-HALE", "emp_id": "EMP-0901", "role": "po_approver", "limit": 25000.0},
        {"user_id": "USR-APPR-NAIR", "emp_id": "EMP-0902", "role": "po_approver"},
        {"user_id": "USR-APPR-CHEN", "emp_id": "EMP-0903", "role": "po_approver"},
        {"user_id": "USR-APPR-VASQ", "emp_id": "EMP-0904", "role": "po_approver"},
        {"user_id": "USR-MKT-01", "emp_id": "EMP-3310", "role": "marketing"},
        {"user_id": "USR-JE-02", "emp_id": "EMP-1088", "role": "journal_approver_stamp"},
    ]
    ctx.payroll_direct_deposit = [
        {
            "employee_id": "EMP-4128",
            "routing": KESTREL_ROUTING,
            "account": KESTREL_NEW_ACCOUNT,
            "account_last4": "4419",
            "account_hash": "dd-kestrel-4419",
        },
        {
            "employee_id": "EMP-8891",
            "routing": HALYARD_ROUTING,
            "account": HALYARD_ACCOUNT,
            "account_last4": "9022",
            "account_hash": "dd-halyard-9022",
        },
        {
            "employee_id": "EMP-2201",
            "routing": "011000390",
            "account": "10002201",
            "account_last4": "2201",
            "account_hash": "dd-cho-2201",
        },
    ]
    ctx.badge_access = [
        {"employee_id": "EMP-4128", "badge_id": "BDG-4128", "last_seen": "2026-09-19T17:02:00Z", "door": "CAM-4"},
        {"employee_id": "EMP-6722", "badge_id": "BDG-6722", "last_seen": "2026-09-19T16:04:00Z", "door": "CAM-WH-01"},
        {"employee_id": "EMP-2290", "badge_id": "BDG-2290", "last_seen": "2026-03-30T16:40:00Z", "door": "CAM-WH-01"},
        {"employee_id": "EMP-3304", "badge_id": "BDG-3304", "last_seen": "2026-09-18T17:10:00Z", "door": "CAM-4"},
        {"employee_id": "EMP-2201", "badge_id": "BDG-2201", "last_seen": "2026-09-19T18:11:00Z", "door": "CAM-HQ"},
    ]
    ctx.okta_export = [
        {
            "emp_id": emp_id,
            "last_login": "2026-09-19T12:00:00Z",
            "active": emp_id != "EMP-2290",
        }
        for emp_id in overlays
        if emp_id != "EMP-8891"
    ]
    ctx.it_assets = [
        {"asset_tag": "MX-LPT-4128", "employee_id": "EMP-4128", "serial": "LN-4128", "issued": "2024-01-08"},
        {"asset_tag": "MX-LPT-1088", "employee_id": "EMP-1088", "serial": "LN-1088", "issued": "2023-04-01"},
        {"asset_tag": "MX-LPT-3304", "employee_id": "EMP-3304", "serial": "LN-3304", "issued": "2024-06-12"},
    ]
    for index in range(1, 108):
        ctx.it_assets.append(
            {
                "asset_tag": f"MX-LPT-{3000 + index}",
                "employee_id": f"EMP-{1000 + index:04d}",
                "serial": f"LN-ROLL-{index:03d}",
                "issued": "2026-03-18",
                "rollout": "LEN-ROLL-26",
            }
        )
    _add_vendor(
        ctx,
        "VEND-KIS-01",
        "Kestrel Industrial Supply LLC",
        first_seen="2025-11-03",
        tax_id="87-2144091",
        address=KESTREL_HOME,
        routing=KESTREL_ROUTING,
        account=KESTREL_NEW_ACCOUNT,
        organizer="Evan Kestrel",
        created_by="USR-VM-04",
        last_modified_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-NLF-02",
        "North Line Fab Inc",
        first_seen="2026-01-14",
        tax_id="04-7712091",
        address="440 D Street\nBoston, MA 02210",
        created_by="USR-VM-04",
        last_modified_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-NLF-03",
        "NLF Industrial Components",
        first_seen="2026-02-02",
        tax_id="04-7712288",
        address="440 D Street, Suite B\nBoston, MA 02210",
        created_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-WBT-01",
        "Westbrook Tooling",
        first_seen="2026-03-20",
        tax_id="04-6621180",
        address="90 Westbrook Street\nWestbrook, ME 04092",
        created_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-HAL-01",
        "Halyard Facilities LLC",
        first_seen="2025-04-20",
        tax_id="88-2204419",
        address="12 Industrial Park, Reno, NV 89502",
        routing=HALYARD_ROUTING,
        account=HALYARD_ACCOUNT,
        created_by="USR-PR-01",
        insurance_cert="",
        w9="",
    )
    _add_vendor(
        ctx,
        "VEND-CLR-01",
        "Clearing Solutions LLC",
        first_seen="2025-11-20",
        tax_id="85-2201988",
        address="1209 Orange Street\nWilmington, DE 19801",
        created_by="USR-JE-04",
        organizer="Corporation Service Company",
    )
    _add_vendor(
        ctx,
        "VEND-BLS-01",
        "Brightline Studio LLC",
        first_seen="2025-09-04",
        tax_id="27-9081144",
        address=FAYETTE,
        created_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-CPS-01",
        "Cambridge Property Services",
        first_seen="2025-07-08",
        tax_id="04-5518821",
        address="1 Kendall Square\nCambridge, MA 02139",
        routing="011000390",
        account="44552190",
        created_by="USR-FAC-01",
    )
    _add_vendor(
        ctx,
        "VEND-HES-01",
        "Harbor Electric Services",
        first_seen="2026-02-03",
        tax_id="04-2287719",
        address="200 Utility Drive\nSomerville, MA 02143",
        created_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-OIC-01",
        "Orbit Insights Corp",
        first_seen="2025-01-06",
        tax_id="04-8824410",
        address="Workbar Boston, 50 Milk Street\nBoston, MA 02109",
        created_by="USR-JE-04",
    )
    _add_vendor(
        ctx,
        "VEND-FLE-01",
        "Freightline Expedite",
        first_seen="2025-11-10",
        tax_id="04-6612290",
        address="400 Port Road\nNewark, NJ 07114",
        created_by="USR-VM-04",
    )
    _add_vendor(
        ctx,
        "VEND-HBP-01",
        "Hartford Brokerage Partners",
        first_seen="2026-01-08",
        tax_id="06-2291188",
        address="1 Hartford Plaza\nHartford, CT 06103",
        created_by="USR-VM-04",
    )
    if "VEND-003" in ctx.vendors:
        ctx.vendors["VEND-003"]["address"] = "438 D Street\nBoston, MA 02210"
    if "VEND-013" in ctx.vendors:
        ctx.vendors["VEND-013"]["bank_account"] = "44552190"
        ctx.vendors["VEND-013"]["bank_account_last4"] = "2190"
        ctx.vendors["VEND-013"]["bank_changed_on"] = "2026-05-22"
        ctx.vendors["VEND-013"]["change_memo"] = "normalize ACH formatting / strip spaces"
    ctx.vendor_bank_history = [
        {
            "vendor_id": "VEND-KIS-01",
            "effective_date": "2025-11-03",
            "routing": KESTREL_ROUTING,
            "account": KESTREL_OLD_ACCOUNT,
            "account_last4": "4401",
            "memo": "initial setup",
            "changed_by": "USR-VM-04",
        },
        {
            "vendor_id": "VEND-KIS-01",
            "effective_date": "2026-06-12",
            "routing": KESTREL_ROUTING,
            "account": KESTREL_NEW_ACCOUNT,
            "account_last4": "4419",
            "memo": "normalize ACH formatting / strip spaces",
            "changed_by": "USR-VM-04",
        },
        {
            "vendor_id": "VEND-013",
            "effective_date": "2021-08-01",
            "routing": "011000390",
            "account": "44552109",
            "account_last4": "2109",
            "memo": "lease lockbox",
            "changed_by": "USR-APPR-01",
        },
        {
            "vendor_id": "VEND-013",
            "effective_date": "2026-05-22",
            "routing": "011000390",
            "account": "44552190",
            "account_last4": "2190",
            "memo": "normalize ACH formatting / strip spaces",
            "changed_by": "USR-FAC-01",
        },
    ]
    northstar = ctx.customers.get("CUST-009")
    if northstar is not None:
        ctx.customers["CUST-009"] = northstar.model_copy(update={"customer_name": "Northstar LLC"})
    if "CUST-004" in ctx.customers:
        ctx.customers["CUST-004"] = ctx.customers["CUST-004"].model_copy(
            update={
                "billing_address": "14 Fayette Street",
                "city": "Somerville",
                "state": "MA",
                "postal_code": "02143",
                "tax_id": "27-9081101",
            }
        )
    if "CUST-NSC-01" not in ctx.customers:
        ctx.customers["CUST-NSC-01"] = Customer(
            customer_id="CUST-NSC-01",
            customer_name="Northstar Settlement Co",
            legal_name="Northstar Settlement Co",
            billing_email="treasury@northstarsettlement.example",
            billing_address="100 Federal Street",
            city="Boston",
            state="MA",
            postal_code="02110",
            tax_id="04-1102299",
            payment_behavior="on_time",
            on_time_rate=0.99,
        )
        _safe_named(ctx, "CUST-NSC-01")
    if "CUST-IC-EU" not in ctx.customers:
        ctx.customers["CUST-IC-EU"] = Customer(
            customer_id="CUST-IC-EU",
            customer_name="Maximor EU BV",
            legal_name="Maximor EU BV",
            billing_email="ap@maximor-eu.example",
            billing_address="Herengracht 100",
            city="Amsterdam",
            state="",
            postal_code="1015 BS",
            tax_id="NL-000000000",
            payment_behavior="mixed",
            notes="Billed as a customer. Not on the legal entity register.",
        )
        _safe_named(ctx, "CUST-IC-EU")
    seq = 900
    while len(ctx.vendors) < ACTIVE_VENDORS:
        vendor_id = f"VEND-Z{seq:03d}"
        seq += 1
        if vendor_id in ctx.vendors:
            continue
        _add_vendor(
            ctx,
            vendor_id,
            f"Northeast Industrial {seq}",
            first_seen="2023-03-01",
            tax_id=f"04-{seq:07d}",
            address=f"{seq} Albany Street\nCambridge, MA 02139",
        )
    ctx.vendors["VEND-KIS-01"]["change_memo"] = "normalize ACH formatting / strip spaces"


def plant_residual(ctx: CompanyScenarioContext) -> None:
    for period, amount in REC_PLUGS.items():
        end = _month_end(period)
        _je(
            ctx,
            f"JE-REC-PLUG-{period}",
            period=period,
            date=end,
            debit="6950-Cash-Over-Short",
            credit="1000-Cash",
            amount_minor=cents(amount),
            memo="rec true-up",
            vendor="Clearing Solutions LLC",
            source=f"JE-REC-PLUG-{period}",
            txn=f"TXN-REC-PLUG-{period}",
            category="operating",
            entry_type="manual",
            poster="USR-JE-04",
            approver="USR-REV-04",
        )
        inv_period = _next_month(period) if period != "2026-08" else "2026-08"
        inv_id = f"INV-CLR-{inv_period}"
        paid = period != "2026-07" and inv_period != "2026-08"
        if period == "2026-07":
            inv_id = "INV-CLR-2026-08"
            paid = False
        if period == "2026-08":
            continue
        _ap_match(
            ctx,
            inv_id,
            "Clearing Solutions LLC",
            amount,
            f"{inv_period}-08",
            f"{inv_period}-28",
            f"CLR-{inv_period}-01",
            "Bank rec consulting true-up",
            po_id=f"PO-CLR-{inv_period}",
            receipt_id=f"GR-CLR-{inv_period}",
            vendor_id="VEND-CLR-01",
            paid=paid,
            pay_id=f"PAY-CLR-{inv_period}",
            bank_id=f"TXN-CLR-{inv_period}",
            initiator="USR-JE-04",
        )
    _ap_match(
        ctx,
        "INV-CLR-2026-08",
        "Clearing Solutions LLC",
        REC_PLUGS["2026-07"],
        "2026-08-08",
        "2026-09-07",
        "CLR-2026-08-01",
        "Bank rec consulting true-up",
        po_id="PO-CLR-2026-08",
        receipt_id="GR-CLR-2026-08",
        vendor_id="VEND-CLR-01",
        paid=False,
    )
    _add_contract(
        ctx,
        "CTR-CLR-001",
        "Clearing Solutions LLC",
        "2025-11-01",
        monthly_minimum=10000.0,
        description="Bank-rec consulting retainer",
    )
    nsc_total = 0.0
    for period, amount in REC_PLUGS.items():
        ns_slice = round(amount * 0.0971, 2)
        nsc_total = round(nsc_total + ns_slice, 2)
        end = _month_end(period)
        _bank(
            ctx,
            f"TXN-NSC-REF-{period}",
            end,
            cents(ns_slice),
            counterparty="NORTHSTAR SETTLEMENT CO",
            description=f"ACH IN NORTHSTAR SETTLEMENT REF {period}",
            matched=True,
        )
        _je(
            ctx,
            f"JE-NSC-REF-{period}",
            period=period,
            date=end,
            debit="6900-Misc-Expense",
            credit="1000-Cash",
            amount_minor=cents(ns_slice),
            memo="Settlement fee refund",
            customer="Northstar Settlement Co",
            source=f"REF-NSC-{period}",
            txn=f"TXN-NSC-REF-{period}",
            category="operating",
            entry_type="operating",
        )
    ctx.source_documents.append(
        {
            "document_id": "DOC-NS-WIRE",
            "title": "Northstar wire instructions",
            "path": "ingestion/customer_instructions/northstar_wire.pdf",
        }
    )
    for name, filename, customer_id in (
        ("northstar_wire.pdf", "ingestion/customer_instructions/northstar_wire.pdf", "CUST-009"),
        ("meridian_wire.pdf", "ingestion/customer_instructions/meridian_wire.pdf", "CUST-010"),
        ("lumen_wire.pdf", "ingestion/customer_instructions/lumen_wire.pdf", "CUST-008"),
    ):
        text = (
            f"Maximor Demo Corp treasury\nWire / ACH instructions for {customer_id}\n\n"
            "Please remit invoice face amount plus 0.10 percent to cover lockbox processing.\n"
            "This cover is listed on the remit advice as a separate residual.\n"
            "Author: Nadia Voss  USR-JE-04\n"
            "Operating bank First National routing 011000390 account ****9107\n"
            "Do not send processor (Stripe/Adyen) settlements to this lockbox.\n"
        )
        ctx.ingestion_files[filename] = text
        ctx.document_texts[filename] = text
    _add_ar(
        ctx,
        "INV-AR-MER-2026-09",
        "CUST-010",
        "Meridian Health",
        "2026-09-04",
        "2026-10-04",
        48620.00,
        "OPEN",
        "Meridian clinic analytics September",
    )
    _add_ar(
        ctx,
        "INV-AR-LUM-2026-09",
        "CUST-008",
        "Lumen Labs",
        "2026-09-06",
        "2026-10-06",
        31100.00,
        "OPEN",
        "Lumen seat block September",
    )
    _pay_ar(
        ctx,
        "PAY-MER-2026-09",
        "2026-09-22",
        48668.62,
        "Meridian Health Systems",
        "CUST-010",
        remittance="INV-AR-MER-2026-09",
        bank_id="TXN-MER-2026-09",
    )
    _pay_ar(
        ctx,
        "PAY-LUM-2026-09",
        "2026-09-23",
        31131.10,
        "Lumen Labs PBC",
        "CUST-008",
        remittance="INV-AR-LUM-2026-09",
        bank_id="TXN-LUM-2026-09",
    )
    _bank(
        ctx,
        "TXN-MER-2026-09",
        "2026-09-22",
        cents(48668.62),
        counterparty="MERIDIAN HEALTH SYSTEMS",
        description="ACH IN MERIDIAN HEALTH INV-AR-MER-2026-09",
        matched=True,
        ledger_amount=cents(48620.00),
    )
    _bank(
        ctx,
        "TXN-LUM-2026-09",
        "2026-09-23",
        cents(31131.10),
        counterparty="LUMEN LABS PBC",
        description="ACH IN LUMEN LABS INV-AR-LUM-2026-09",
        matched=True,
        ledger_amount=cents(31100.00),
    )
    _je(
        ctx,
        "JE-1030-RESIDUAL",
        period="2026-09",
        date="2026-09-30",
        debit="1030-Undeposited-Funds",
        credit="1000-Cash",
        amount_minor=cents(1121.06),
        memo="ACH batch remainder",
        source="DIT-RESIDUAL-0930",
        txn="TXN-1030-RESIDUAL",
        category="operating",
        entry_type="manual",
        poster="USR-JE-04",
        approver="USR-REV-04",
    )
    ctx.planted_recons.append(
        type(ctx.planted_recons[0])(
            **{
                **ctx.planted_recons[0].model_dump(),
                "reconciliation_id": "REC-AUG-PLUG",
                "period": "2026-08",
                "label": "August bank rec after over/short true-up",
            }
        )
        if ctx.planted_recons
        else _recon_stub("REC-AUG-PLUG", "2026-08")
    )


def plant_kestrel(ctx: CompanyScenarioContext) -> None:
    for period, amount in KIS_MONTHLY.items():
        day = "08" if period != "2026-06" else "08"
        if period == "2026-08":
            inv_id = "INV-KIS-4812"
            po_id = "PO-KIS-4812"
            gr_id = "GR-KIS-4812"
            inv_date = "2026-08-14"
            gr_date = "2026-08-11"
            po_date = "2026-08-14"
        elif period == "2026-02":
            inv_id = "INV-KIS-2026-02-08"
            po_id = f"PO-KIS-{period}"
            gr_id = f"GR-KIS-{period}"
            inv_date = f"{period}-{day}"
            gr_date = inv_date
            po_date = inv_date
        elif period == "2026-09":
            inv_id = "INV-KIS-2026-09"
            po_id = f"PO-KIS-{period}"
            gr_id = f"GR-KIS-{period}"
            inv_date = "2026-09-12"
            gr_date = inv_date
            po_date = inv_date
        else:
            inv_id = f"INV-KIS-{period}"
            po_id = f"PO-KIS-{period}"
            gr_id = f"GR-KIS-{period}"
            inv_date = f"{period}-{day}"
            gr_date = inv_date
            po_date = inv_date
        qty = 20 + (int(period[-2:]) % 9)
        unit = round(amount / qty, 2)
        _ap_match(
            ctx,
            inv_id,
            "Kestrel Industrial Supply LLC",
            amount,
            inv_date,
            _add_days(inv_date, 30),
            f"KIS-{period}-01",
            "MRO overflow KIS-MRO-7",
            po_id=po_id,
            receipt_id=gr_id,
            vendor_id="VEND-KIS-01",
            paid=period < "2026-09",
            pay_id=f"PAY-KIS-{period}",
            bank_id=f"TXN-KIS-{period}",
            approver="Jordan Hale",
            approval_limit=25000.0,
            requested_by="EMP-4128",
            qty=qty,
            unit=unit,
            sku="KIS-MRO-7",
            po_date=po_date,
            gr_date=gr_date,
            dock="CAM-DOCK-4",
            gr_timestamp="16:03:00",
        )
        shrink = round(amount * 0.1527, 2)
        _je(
            ctx,
            f"JE-SHRINK-{period}",
            period=period,
            date=_month_end(period),
            debit="6900-Misc-Expense",
            credit="1400-Inventory",
            amount_minor=max(cents(shrink), 1),
            memo="cycle variance",
            vendor="Kestrel Industrial Supply LLC",
            source=f"CC-CAM-A14-{period}",
            txn=f"TXN-SHRINK-{period}",
            category="operating",
            entry_type="manual",
        )
        ctx.cycle_counts.append(
            {
                "count_id": f"CC-CAM-A14-{period}",
                "bin": "CAM-BIN-A14",
                "sku": "KIS-MRO-7",
                "period": period,
                "book_qty": qty,
                "floor_qty": max(qty - 3, 0),
                "counter": "EMP-6722",
            }
        )
    _ap_match(
        ctx,
        "INV-KIS-10442",
        "Kestrel Industrial Supply LLC",
        18406.22,
        "2026-03-18",
        "2026-04-17",
        "KIS-10442",
        "MRO lot KIS-10442",
        po_id="PO-KIS-10442",
        receipt_id="GR-KIS-10442",
        vendor_id="VEND-KIS-01",
        paid=True,
        pay_id="PAY-KIS-10442",
        bank_id="TXN-KIS-10442",
        qty=14,
        unit=1314.73,
        sku="KIS-MRO-7",
        creator_asset="MX-LPT-4128",
    )
    _ap_match(
        ctx,
        "INV-NLF-10442",
        "North Line Fab Inc",
        18424.62,
        "2026-03-18",
        "2026-04-17",
        "NLF-10442",
        "Fab lot NLF-10442",
        po_id="PO-NLF-10442",
        receipt_id="GR-NLF-10442",
        vendor_id="VEND-NLF-02",
        paid=True,
        pay_id="PAY-NLF-10442",
        bank_id="TXN-NLF-10442",
        qty=14,
        unit=1316.044,
        sku="NLF-FAB-4",
        creator_asset="MX-LPT-4128",
        dock="CAM-DOCK-4",
    )
    nlf_amounts = {
        "2026-01": 9840.18,
        "2026-02": 10120.40,
        "2026-03": 10440.22,
        "2026-04": 10880.18,
        "2026-05": 11220.44,
        "2026-06": 10805.22,
        "2026-07": 10406.18,
        "2026-08": 10440.40,
        "2026-09": 10465.18,
    }
    for period, amount in nlf_amounts.items():
        _ap_match(
            ctx,
            f"INV-NLF-02-{period}",
            "North Line Fab Inc",
            amount,
            f"{period}-16",
            _add_days(f"{period}-16", 30),
            f"NLF2-{period}",
            "Secondary fab cell",
            po_id=f"PO-NLF-02-{period}",
            receipt_id=f"GR-NLF-02-{period}",
            vendor_id="VEND-NLF-02",
            paid=period < "2026-09",
            pay_id=f"PAY-NLF-02-{period}",
            bank_id=f"TXN-NLF-02-{period}",
            dock="CAM-DOCK-4",
        )
    nlf3 = {
        "2026-02": 4480.22,
        "2026-03": 4620.18,
        "2026-04": 4710.44,
        "2026-05": 4880.18,
        "2026-06": 5010.22,
        "2026-07": 5120.40,
        "2026-08": 5184.18,
        "2026-09": 6201.06,
    }
    for period, amount in nlf3.items():
        _ap_match(
            ctx,
            f"INV-NLF-03-{period}",
            "NLF Industrial Components",
            amount,
            f"{period}-17",
            _add_days(f"{period}-17", 30),
            f"NLF3-{period}",
            "Dock 4 components",
            po_id=f"PO-NLF-03-{period}",
            receipt_id=f"GR-NLF-03-{period}",
            vendor_id="VEND-NLF-03",
            paid=period < "2026-09",
            dock="CAM-DOCK-4",
        )
    _ap_match(
        ctx,
        "INV-KIS-4601",
        "Kestrel Industrial Supply LLC",
        24880.44,
        "2026-04-08",
        "2026-05-08",
        "KIS-4601",
        "KIS-MRO-7 April cell A",
        po_id="PO-KIS-4601",
        receipt_id="GR-KIS-4601",
        vendor_id="VEND-KIS-01",
        paid=True,
        approver="Jordan Hale",
        approval_limit=25000.0,
        requested_by="EMP-4128",
        qty=18,
        unit=1382.2466,
        sku="KIS-MRO-7",
    )
    _ap_match(
        ctx,
        "INV-WBT-4602",
        "Westbrook Tooling",
        24106.18,
        "2026-04-09",
        "2026-05-09",
        "WBT-4602",
        "KIS-MRO-7 April cell B",
        po_id="PO-WBT-4602",
        receipt_id="GR-WBT-4602",
        vendor_id="VEND-WBT-01",
        paid=True,
        approver="Jordan Hale",
        approval_limit=25000.0,
        requested_by="EMP-4128",
        sku="KIS-MRO-7",
    )
    _ap_match(
        ctx,
        "INV-KIS-4603",
        "Kestrel Industrial Supply LLC",
        23413.56,
        "2026-04-10",
        "2026-05-10",
        "KIS-4603",
        "KIS-MRO-7 April cell C",
        po_id="PO-KIS-4603",
        receipt_id="GR-KIS-4603",
        vendor_id="VEND-KIS-01",
        paid=True,
        approver="Jordan Hale",
        approval_limit=25000.0,
        requested_by="EMP-4128",
        sku="KIS-MRO-7",
    )
    _ap_match(
        ctx,
        "INV-WBT-2026-07",
        "Westbrook Tooling",
        24106.18,
        "2026-07-12",
        "2026-08-11",
        "WBT-2026-07",
        "Tooling lot July",
        po_id="PO-WBT-2026-07",
        receipt_id="GR-WBT-2026-07",
        vendor_id="VEND-WBT-01",
        paid=True,
        pay_id="PAY-WBT-2026-07",
        bank_id="TXN-WBT-2026-07",
        remit_street=KESTREL_HOME,
    )
    _ap_match(
        ctx,
        "INV-WBT-2026-08",
        "Westbrook Tooling",
        23940.00,
        "2026-08-12",
        "2026-09-11",
        "WBT-2026-08",
        "Tooling lot August",
        po_id="PO-WBT-2026-08",
        receipt_id="GR-WBT-2026-08",
        vendor_id="VEND-WBT-01",
        paid=True,
        remit_street=KESTREL_HOME,
    )
    freight_months = {
        "2025-11": 220.18,
        "2025-12": 228.40,
        "2026-01": 232.22,
        "2026-02": 238.18,
        "2026-03": 240.44,
        "2026-04": 242.18,
        "2026-05": 244.22,
        "2026-06": 246.18,
        "2026-07": 248.40,
        "2026-08": 248.18,
        "2026-09": 229.89,
    }
    _po_only(ctx, "PO-KIS-FRT-STANDING", "Kestrel Industrial Supply LLC", 300.0, "2025-11-01", "Freight add-on standing")
    for period, amount in freight_months.items():
        _ap_match(
            ctx,
            f"INV-KIS-FRT-{period}",
            "Kestrel Industrial Supply LLC",
            amount,
            f"{period}-22",
            _add_days(f"{period}-22", 15),
            f"KIS-FRT-{period}",
            "Freight add-on under standing PO",
            po_id="PO-KIS-FRT-STANDING",
            receipt_id=f"GR-KIS-FRT-{period}",
            vendor_id="VEND-KIS-01",
            paid=period < "2026-09",
            reuse_po=True,
        )
    _ap_match(
        ctx,
        "INV-KIS-0618",
        "Kestrel Industrial Supply LLC",
        24106.18,
        "2026-06-18",
        "2026-07-18",
        "KIS-0618",
        "June MRO with 2/10",
        po_id="PO-KIS-0618",
        receipt_id="GR-KIS-0618",
        vendor_id="VEND-KIS-01",
        paid=True,
        discount=True,
    )
    hes = {
        "2026-02": 3218.40,
        "2026-03": 3440.22,
        "2026-04": 3610.18,
        "2026-05": 3820.44,
        "2026-06": 3688.18,
        "2026-07": 3910.22,
        "2026-08": 3840.18,
        "2026-09": 3890.84,
    }
    for period, amount in hes.items():
        extra = {"remit_street": KESTREL_HOME} if period in {"2026-05", "2026-08"} else {}
        _ap_match(
            ctx,
            f"INV-HES-{period}",
            "Harbor Electric Services",
            amount,
            f"{period}-19",
            _add_days(f"{period}-19", 30),
            f"HES-{period}-P",
            "Sub-meter project -P",
            po_id=f"PO-HES-{period}",
            receipt_id=f"GR-HES-{period}",
            vendor_id="VEND-HES-01",
            paid=period < "2026-09",
            **extra,
        )
    grouped = 24880.44 + 14206.18 + 8207.00
    _bank(
        ctx,
        "TXN-KIS-2026-09-16",
        "2026-09-16",
        -cents(47293.62),
        counterparty="KESTREL INDUSTRIAL SUPPLY LLC",
        description="ACH OUT KESTREL INDUSTRIAL GROUPED",
        matched=True,
    )
    if ctx.audit_invoices:
        ctx.audit_invoices.append(
            ctx.audit_invoices[0].model_copy(
                update={
                    "invoice_id": "AUD-SAMP-KIS-08",
                    "vendor": "Kestrel Industrial Supply LLC",
                    "vendor_id": "VEND-KIS-01",
                    "amount": KIS_MONTHLY["2026-02"],
                    "invoice_date": "2026-02-08",
                }
            )
        )
    _ = grouped


def plant_halyard(ctx: CompanyScenarioContext) -> None:
    cursor = date(2025, 4, 14)
    end = date(2026, 9, 25)
    ghost_gross = 0.0
    while cursor <= end:
        if cursor < date(2025, 10, 3):
            gross = 4180.27
            ctx.payroll_register.append(
                {
                    "pay_date": cursor.isoformat(),
                    "period_start": (cursor - timedelta(days=13)).isoformat(),
                    "period_end": cursor.isoformat(),
                    "employee_id": "EMP-8891",
                    "full_name": "Tomas Halyard",
                    "department": "Warehouse",
                    "annual_salary": 108800,
                    "gross_pay": gross,
                    "employee_taxes": round(gross * 0.0765, 2),
                    "benefits": 95.0,
                    "net_pay": round(gross - round(gross * 0.0765, 2) - 95.0, 2),
                    "employer_cost": round(gross * 1.0765 + 95.0, 2),
                    "location": "Remote",
                    "bank_account": "BANK-PAYROLL",
                    "direct_deposit_last4": "9022",
                }
            )
            ghost_gross = round(ghost_gross + gross, 2)
        cursor += timedelta(days=14)
    for row in ctx.payroll_register:
        if row["employee_id"] == "EMP-8891":
            row["gross_pay"] = 4180.27
            row["direct_deposit_last4"] = "9022"
            row["employee_taxes"] = round(4180.27 * 0.0765, 2)
    ava_from = date(2026, 4, 11)
    for row in ctx.payroll_register:
        if row["employee_id"] == "EMP-2290":
            row["gross_pay"] = 1842.10
            row["include_flag"] = "USR-PR-01"
    for month_n in range(12):
        year = 2025 if month_n < 8 else 2026
        month = month_n + 5 if month_n < 8 else month_n - 7
        if month_n >= 8:
            month = month_n - 7
        # May 2025 (n=0) through April 2026, then continue? catalog 12 months $2400.
        pass
    months = [
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
        "2026-08",
        "2026-09",
    ]
    _po_only(ctx, "PO-HAL-STANDING", "Halyard Facilities LLC", 28800.0, "2025-04-20", "West campus janitorial")
    for period in months:
        _ap_match(
            ctx,
            f"INV-HAL-{period}",
            "Halyard Facilities LLC",
            2400.00,
            f"{period}-05",
            f"{period}-20",
            f"HAL-{period}",
            "West campus janitorial",
            po_id=f"PO-HAL-{period}",
            receipt_id=f"GR-HAL-{period}",
            vendor_id="VEND-HAL-01",
            paid=period < "2026-09",
            pay_id=f"PAY-HAL-{period}",
            bank_id=f"TXN-HAL-{period}",
            approval_limit=25000.0,
        )
    weekend = {
        "2026-01": 2300.00,
        "2026-02": 2300.00,
        "2026-03": 2300.00,
        "2026-04": 2300.00,
        "2026-05": 2300.00,
        "2026-06": 2300.00,
        "2026-07": 2300.00,
        "2026-08": 2300.00,
        "2026-09": 2300.00,
    }
    for period, amount in weekend.items():
        _ap_match(
            ctx,
            f"INV-HAL-WKND-{period}",
            "Halyard Facilities LLC",
            amount,
            f"{period}-28",
            _add_days(f"{period}-28", 15),
            f"HAL-WKND-{period}",
            "Weekend coverage 1099",
            po_id=f"PO-HAL-WKND-{period}",
            receipt_id=f"GR-HAL-WKND-{period}",
            vendor_id="VEND-HAL-01",
            paid=period < "2026-09",
            account="5400-Contractors",
        )
    ctx.contractors.append(
        {
            "contractor_id": "CTR-HALYARD-1099",
            "legal_name": "Tomas Halyard",
            "tin_last4": "9022",
            "emp_id_match": "EMP-8891",
        }
    )
    _add_contract(ctx, "CTR-HAL-01", "Halyard Facilities LLC", "2025-04-20", monthly_minimum=2400.0, description="West campus janitorial")
    ctx.payroll_tax_941 = [
        {
            "form_id": f"941-{period}",
            "period": period,
            "includes_emp_id": "EMP-8891",
            "employer_fica_extra": round(4180.27 * 0.0765, 2),
        }
        for period in ("2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3")
    ]
    _ = ghost_gross
    _ = ava_from


def plant_orbit(ctx: CompanyScenarioContext) -> None:
    _ap_match(
        ctx,
        "INV-OIC-2025-01",
        "Orbit Insights Corp",
        276000.00,
        "2025-01-06",
        "2025-02-05",
        "OIC-2025-01",
        "36-month platform plus implementation",
        po_id="PO-OIC-001",
        receipt_id="GR-OIC-001",
        vendor_id="VEND-OIC-01",
        paid=True,
        pay_id="PAY-OIC-2025-01",
        bank_id="TXN-OIC-2025-01",
        account="1200-Prepaid-Software",
    )
    software = PrepaidItem(
        prepaid_id="PRE-SFT-002",
        vendor="Orbit Insights Corp",
        description="Orbit Insights platform 36 months",
        source_document_id="INV-OIC-2025-01",
        total_amount=180000.0,
        start_date="2025-01-06",
        end_date="2028-01-06",
        initial_account="1200-Prepaid-Software",
        expense_account="1220-Prepaid-Other",
        amortization_method="straight_line_monthly",
        status="active",
        created_at="2025-01-06T00:00:00Z",
        evidence_refs=["INV-OIC-2025-01", "CTR-OIC-001"],
        transaction_id="TXN-PRE-SFT-002",
    )
    ctx.prepaids.append(software)
    ctx.prepaid_schedule.append(
        PrepaidScheduleLine(
            prepaid_id="PRE-SFT-002",
            period="2026-09",
            amount=5000.0,
            status="posted",
            journal_entry_id="JE-PRE-OIC-2026-09",
            method="straight_line_monthly",
        )
    )
    cursor = date(2025, 1, 31)
    month_n = 0
    while cursor <= date(2026, 8, 31):
        period = cursor.strftime("%Y-%m")
        _je(
            ctx,
            f"JE-PRE-OIC-{period}",
            period=period,
            date=cursor.isoformat(),
            debit="1220-Prepaid-Other",
            credit="1200-Prepaid-Software",
            amount_minor=500_000,
            memo="Orbit Insights amortization",
            vendor="Orbit Insights Corp",
            source="PRE-SFT-002",
            txn=f"TXN-PRE-OIC-{period}",
            category="operating",
            entry_type="prepaid",
            poster="USR-JE-04",
            approver="USR-NA-VOSS",
        )
        month_n += 1
        if cursor.month == 12:
            nxt = date(cursor.year + 1, 1, 1)
        else:
            nxt = date(cursor.year, cursor.month + 1, 1)
        import calendar as cal

        cursor = date(nxt.year, nxt.month, cal.monthrange(nxt.year, nxt.month)[1])
    _je(
        ctx,
        "JE-PRE-OIC-2026-09",
        period="2026-09",
        date="2026-09-30",
        debit="1220-Prepaid-Other",
        credit="1200-Prepaid-Software",
        amount_minor=500_000,
        memo="Orbit Insights amortization",
        vendor="Orbit Insights Corp",
        source="PRE-SFT-002",
        txn="TXN-PRE-OIC-2026-09",
        category="operating",
        entry_type="prepaid",
        poster="USR-JE-04",
        approver="USR-NA-VOSS",
    )
    for period in ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"):
        end = _month_end(period)
        nxt = _add_days(end, 1)
        _je(
            ctx,
            f"JE-PRE-OIC-EXP-{period}",
            period=period,
            date=end,
            debit="Software Subscription Expense",
            credit="1220-Prepaid-Other",
            amount_minor=500_000,
            memo="Orbit Insights expense",
            vendor="Orbit Insights Corp",
            source="PRE-SFT-002",
            txn=f"TXN-PRE-OIC-EXP-{period}",
            category="operating",
            entry_type="prepaid",
            poster="USR-JE-04",
            approver="USR-NA-VOSS",
        )
        _je(
            ctx,
            f"JE-PRE-OIC-REV-{period}",
            period=nxt[:7],
            date=nxt,
            debit="1350-Other-Receivable",
            credit="Software Subscription Expense",
            amount_minor=500_000,
            memo="Orbit implementation recoveries",
            vendor="Orbit Insights Corp",
            source="PRE-SFT-002",
            txn=f"TXN-PRE-OIC-REV-{period}",
            category="operating",
            entry_type="manual",
            poster="USR-JE-04",
            approver="USR-NA-VOSS",
        )
    rider = PrepaidItem(
        prepaid_id="PRE-INS-RIDER",
        vendor="Hartford Brokerage Partners",
        description="Cyber rider",
        source_document_id="INV-HBP-2026-01",
        total_amount=18600.0,
        start_date="2026-01-01",
        end_date="2026-03-31",
        initial_account="1210-Prepaid-Insurance",
        expense_account="Insurance Expense",
        amortization_method="straight_line_monthly",
        status="active",
        created_at="2026-01-08T00:00:00Z",
        evidence_refs=["INV-HBP-2026-01"],
        transaction_id="TXN-PRE-INS-RIDER",
    )
    ctx.prepaids.append(rider)
    ctx.prepaid_schedule.append(
        PrepaidScheduleLine(
            prepaid_id="PRE-INS-RIDER",
            period="2026-09",
            amount=0.0,
            status="skipped",
            method="straight_line_monthly",
        )
    )
    _ap_match(
        ctx,
        "INV-HBP-2026-01",
        "Hartford Brokerage Partners",
        18600.00,
        "2026-01-08",
        "2026-02-07",
        "HBP-2026-01",
        "Cyber rider",
        po_id="PO-HBP-2026-01",
        receipt_id="GR-HBP-2026-01",
        vendor_id="VEND-HBP-01",
        paid=True,
        pay_id="PAY-HBP-2026-01",
        bank_id="TXN-HBP-2026-01",
        account="1210-Prepaid-Insurance",
    )
    from fixed_assets.models import FixedAsset

    ctx.fixed_assets.append(
        FixedAsset(
            asset_id="FA-OIC-IMPL",
            description="Orbit Insights implementation",
            vendor="Orbit Insights Corp",
            acquisition_date="2025-01-06",
            placed_in_service_date="2025-01-06",
            cost=96000.0,
            useful_life_months=36,
            asset_account="1500-PPE",
            accumulated_depreciation_account="1510-Accum-Dep",
            depreciation_expense_account="Depreciation Expense",
            source_document_id="INV-OIC-2025-01",
            transaction_id="TXN-FA-OIC-IMPL",
        )
    )
    _je(
        ctx,
        "JE-FA-OIC-2026-09",
        period="2026-09",
        date="2026-09-30",
        debit="Depreciation Expense",
        credit="1510-Accum-Dep",
        amount_minor=266667,
        memo="Orbit implementation depreciation",
        vendor="Orbit Insights Corp",
        source="FA-OIC-IMPL",
        txn="TXN-FA-OIC-2026-09",
        category="operating",
        entry_type="depreciation",
    )
    _ap_match(
        ctx,
        "INV-OIC-PREBILL",
        "Orbit Insights Corp",
        15000.00,
        "2026-09-30",
        "2026-10-30",
        "OIC-PREBILL-Q4",
        "Q4 2026 platform service billed in September",
        po_id="PO-OIC-PREBILL",
        receipt_id="GR-OIC-PREBILL",
        vendor_id="VEND-OIC-01",
        paid=False,
        account="6000-Operating",
        service_period="2026-10-01 to 2026-12-31",
    )
    _add_contract(
        ctx,
        "CTR-OIC-001",
        "Orbit Insights Corp",
        "2025-01-06",
        monthly_minimum=5000.0,
        description="36-month platform plus implementation",
    )


def plant_lapping(ctx: CompanyScenarioContext) -> None:
    chain = [
        ("PAY-LAP-2026-09-12", "2026-09-12", 88400.00, "Helios Analytics Corporation", "CUST-002", "INV-AR-HE-4412", "INV-AR-PIN-2208", "18:22:00"),
        ("PAY-LAP-QH-SEP-PRE", "2026-09-22", 25000.00, "Quiet Harbor Holdings", "CUST-005", "INV-AR-014", "INV-AR-PIN-2210", "18:40:00"),
    ]
    stock = 0.0
    for pay_id, pay_date, amount, payer, cust, named, applied, hhmm in chain:
        _pay_ar(
            ctx,
            pay_id,
            pay_date,
            amount,
            payer,
            cust,
            remittance=f"named {named} apply {applied}",
            bank_id=f"TXN-{pay_id}",
            applied_at=f"{pay_date}T{hhmm}Z",
            applied_invoice=applied,
            named_invoice=named,
        )
        _bank(
            ctx,
            f"TXN-{pay_id}",
            pay_date,
            cents(amount),
            counterparty=payer.upper(),
            description=f"ACH IN {payer.upper()} {named}",
            matched=True,
        )
        stock = round(stock + amount, 2)
        ctx.ar_invoices[applied] = ctx.ar_invoices.get(applied) or CustomerInvoice(
            invoice_id=applied,
            customer_id="CUST-006" if "PIN" in applied else cust,
            customer_name="Pinnacle Retail" if "PIN" in applied else payer,
            invoice_date=pay_date,
            due_date=_add_days(pay_date, 30),
            original_amount=amount,
            outstanding_amount=0.0,
            status="PAID",
            description="Applied via weekend posting",
        )
        _safe_named(ctx, applied)
    _add_ar(ctx, "INV-AR-HE-4412", "CUST-002", "Helios Analytics", "2026-08-15", "2026-09-14", 91200.00, "OPEN", "Helios usage August")
    _add_ar(ctx, "INV-AR-PIN-2208", "CUST-006", "Pinnacle Retail", "2026-07-20", "2026-08-19", 88400.00, "PAID", "Pinnacle store licenses")
    _add_ar(ctx, "INV-AR-PIN-2210", "CUST-006", "Pinnacle Retail", "2026-08-20", "2026-09-19", 25000.00, "PAID", "Pinnacle addendum")
    remaining = round(412880.00 - stock, 2)
    _pay_ar(
        ctx,
        "PAY-LAP-STOCK",
        "2026-08-14",
        remaining,
        "Quiet Harbor Holdings",
        "CUST-005",
        remittance="chain cover",
        bank_id="BATCH-AR-2026-08-14",
        applied_at="2026-08-14T18:30:00Z",
        applied_invoice="INV-AR-HE-4390",
        named_invoice="INV-AR-QH-9001",
    )
    _bank(
        ctx,
        "BATCH-AR-2026-08-14",
        "2026-08-14",
        cents(remaining),
        counterparty="LOCKBOX AR BATCH",
        description="ACH IN AR LOCKBOX BATCH",
        matched=True,
    )
    _bank(
        ctx,
        "BATCH-AR-2026-09-12",
        "2026-09-12",
        cents(88400.00),
        counterparty="LOCKBOX AR BATCH",
        description="ACH IN AR LOCKBOX 2026-09-12",
        matched=True,
    )
    ctx.ar_unapplied.append(
        {
            "customer_id": "CUST-005",
            "account": "1110-AR-Unapplied",
            "in_amount": 62000.00,
            "out_amount": 25791.60,
            "ending": 36208.40,
        }
    )
    _je(
        ctx,
        "JE-UNAPP-QH",
        period="2026-09",
        date="2026-09-20",
        debit="1000-Cash",
        credit="1110-AR-Unapplied",
        amount_minor=cents(36208.40),
        memo="Quiet Harbor unapplied",
        customer="Quiet Harbor Holdings",
        source="PAY-UNAPP-QH",
        txn="TXN-UNAPP-QH",
        category="volume_cash",
        entry_type="ar_receipt",
    )
    ctx.ar_credit_memos.append(
        {
            "credit_memo_id": "CM-HE-088",
            "invoice_id": "INV-AR-HE-4390",
            "amount": 12640.00,
            "date": "2026-08-21",
            "approver_id": "USR-APPLY-02",
            "return_ticket": "",
        }
    )
    _je(
        ctx,
        "JE-CM-HE-088",
        period="2026-08",
        date="2026-08-21",
        debit="4100-Contra-Revenue-Returns",
        credit="1100-AR",
        amount_minor=cents(12640.00),
        memo="Helios credit memo",
        customer="Helios Analytics",
        source="CM-HE-088",
        txn="TXN-CM-HE-088",
        category="revenue",
        entry_type="ar_adjustment",
        poster="USR-APPLY-02",
        approver="USR-APPLY-02",
    )
    remittance = (
        "Helios Analytics Corporation\nRemittance advice\n"
        "Please apply this ACH to INV-AR-HE-4412 $88,400.00.\n"
        "Payer: Helios Analytics  Date: 2026-09-12\n"
        "This file names INV-AR-HE-4412. It does not name INV-AR-PIN-2208.\n"
    )
    ctx.ingestion_files["ingestion/remittance/PAY-LAP-2026-09-12.txt"] = remittance
    ctx.document_texts["ingestion/remittance/PAY-LAP-2026-09-12.txt"] = remittance


def plant_pinnacle(ctx: CompanyScenarioContext) -> None:
    _add_ar(
        ctx,
        "INV-AR-PIN-BH-01",
        "CUST-006",
        "Pinnacle Retail",
        "2026-09-29",
        "2026-12-28",
        2400000.00,
        "OPEN",
        "Pinnacle bill-and-hold CAM-WH-01",
        ship_to="CAM-WH-01",
        extra={"ship_to": "CAM-WH-01", "fob": "destination"},
    )
    _add_ar(
        ctx,
        "INV-AR-ATL-PF-01",
        "CUST-007",
        "Atlas Robotics",
        "2026-09-30",
        "2026-10-30",
        1180000.00,
        "OPEN",
        "Atlas pull-forward",
        extra={"customer_po": "PO-ATL-8841", "customer_po_date": "2026-10-02"},
    )
    _je(
        ctx,
        "JE-REV-CUTOFF-01",
        period="2026-09",
        date="2026-09-30",
        debit="1100-AR",
        credit="4000-Revenue",
        amount_minor=cents(2400000.00),
        memo="Pinnacle September delivery",
        customer="Pinnacle Retail",
        source="INV-AR-PIN-BH-01",
        txn="TXN-PIN-BH-01",
        category="revenue",
        entry_type="ar_invoice",
        poster="USR-REV-05",
        approver="USR-JE-02",
        timestamp="2026-09-30T23:47:00Z",
    )
    _je(
        ctx,
        "JE-REV-CUTOFF-02",
        period="2026-09",
        date="2026-09-30",
        debit="1100-AR",
        credit="4000-Revenue",
        amount_minor=cents(1180000.00),
        memo="Atlas September delivery",
        customer="Atlas Robotics",
        source="INV-AR-ATL-PF-01",
        txn="TXN-ATL-PF-01",
        category="revenue",
        entry_type="ar_invoice",
        poster="USR-REV-05",
        approver="USR-JE-02",
        timestamp="2026-09-30T23:47:00Z",
    )
    _je(
        ctx,
        "JE-COGS-PIN-BH",
        period="2026-09",
        date="2026-09-29",
        debit="5200-Supplier",
        credit="1400-Inventory",
        amount_minor=cents(1104000.00),
        memo="Relieve PIN-BH inventory",
        source="INV-PIN-BH-COGS",
        txn="TXN-PIN-BH-COGS",
        category="supplier",
        entry_type="cogs",
    )
    _je(
        ctx,
        "JE-COGS-ATL-PF",
        period="2026-09",
        date="2026-09-30",
        debit="5200-Supplier",
        credit="1400-Inventory",
        amount_minor=cents(507400.00),
        memo="Relieve ATL-PF inventory",
        source="INV-ATL-PF-COGS",
        txn="TXN-ATL-PF-COGS",
        category="supplier",
        entry_type="cogs",
    )
    ctx.cycle_counts.append(
        {
            "count_id": "CC-CAM-WH-01-2026-09-30",
            "bin": "CAM-WH-01",
            "sku": "PIN-BH",
            "period": "2026-09",
            "book_qty": 0,
            "floor_qty": 400,
            "floor_cost": 1611400.00,
        }
    )
    ctx.inventory_bins.append({"sku": "PIN-BH", "location": "CAM-WH-01-CAGE-B", "qty": 400, "cost": 1104000.00})
    ctx.source_documents.append(
        {
            "document_id": "DOC-SL-PIN-2026-09-28",
            "title": "Pinnacle side letter",
            "body": (
                "Side letter dated 2026-09-28. Paragraph 4 grants Pinnacle a 90-day "
                "right of return on INV-AR-PIN-BH-01. Goods remain at CAM-WH-01."
            ),
        }
    )
    ctx.later_ar.append(
        {
            "invoice_id": "CM-PIN-OCT-01",
            "customer_id": "CUST-006",
            "amount": 2400000.00,
            "date": "2026-10-18",
            "description": "Reserved October return window",
        }
    )
    from inbox.fixtures import spec_pinnacle_hold

    ctx.inbox_extra.append(spec_pinnacle_hold().model_dump(mode="json"))


def plant_processor(ctx: CompanyScenarioContext) -> None:
    _add_contract(
        ctx,
        "CTR-STRIPE-001",
        "Stripe",
        "2025-01-01",
        monthly_minimum=0.0,
        description="2.9 percent plus $0.30 per successful charge",
    )
    _add_contract(
        ctx,
        "CTR-ADYEN-001",
        "Adyen NV",
        "2024-03-01",
        monthly_minimum=0.0,
        description="blended 3.1 percent Adyen",
    )
    ctx.stripe_connected_accounts.append(
        {
            "account_id": "acct_1MaximorProc",
            "legal_name": "Maximor Processing LLC",
            "ein": "88-4412109",
            "dashboard_user": "USR-STRIPE-01",
            "emp_id": "EMP-4402",
            "vendor_id": "",
        }
    )
    skim_months = {
        "2025-10": 16440.18,
        "2025-11": 16880.22,
        "2025-12": 17220.40,
        "2026-01": 17640.18,
        "2026-02": 17880.44,
        "2026-03": 18120.18,
        "2026-04": 18440.22,
        "2026-05": 18680.18,
        "2026-06": 18820.40,
        "2026-07": 19120.18,
        "2026-08": 17211.20,
        "2026-09": 18206.40,
    }
    if round(sum(skim_months.values()), 2) != 214660.18:
        last = 214660.18 - round(sum(list(skim_months.values())[:-1]), 2)
        skim_months["2026-09"] = round(last, 2)
    for period, amount in skim_months.items():
        _je(
            ctx,
            f"JE-FEE-SKIM-{period}",
            period=period,
            date=_month_end(period),
            debit="6600-Processor-Fees",
            credit="1020-Stripe-Clearing",
            amount_minor=cents(amount),
            memo="Processor fees booked",
            source=f"tr_mpr_{period}",
            txn=f"tr_mpr_{period}",
            category="operating",
            entry_type="processor",
            poster="USR-STRIPE-01",
            approver="USR-STRIPE-01",
        )
        ctx.stripe_transfers.append(
            {
                "transfer_id": f"tr_mpr_{period}",
                "destination": "acct_1MaximorProc",
                "amount": amount,
                "date": _month_end(period),
            }
        )
        ctx.stripe_charges.append(
            {
                "charge_id": f"ch_mpr_{period}",
                "gross": round(amount / 0.005, 2),
                "fee_booked_rate": 0.0341,
                "fee_contract_rate": 0.029,
                "period": period,
            }
        )
    ctx.stripe_transfers.append(
        {
            "transfer_id": "tr_mpr_win_4419",
            "destination": "acct_1MaximorProc",
            "amount": 18440.00,
            "date": "2026-08-22",
            "dispute_id": "dsp_win_4419",
        }
    )
    ctx.stripe_disputes.append(
        {
            "dispute_id": "dsp_win_4419",
            "status": "won",
            "amount": 18440.00,
            "gl_reinstated": False,
        }
    )
    ctx.stripe_refunds.append({"refund_id": "re_mpr_span", "extra_fee_gl": 6208.00})
    _je(
        ctx,
        "JE-FEE-BLEND-2026-09",
        period="2026-09",
        date="2026-09-30",
        debit="6600-Processor-Fees",
        credit="1020-Stripe-Clearing",
        amount_minor=cents(800.00),
        memo="Adyen blended rate true-up",
        source="JE-FEE-BLEND-2026-09",
        txn="TXN-FEE-BLEND-2026-09",
        category="operating",
        entry_type="processor",
        poster="USR-STRIPE-01",
        approver="USR-STRIPE-01",
    )
    ctx.adyen_sim.append({"period": "2026-09", "gl_matches_contract": True})
    _bank(
        ctx,
        "TXN-STRIPE-RESERVE-REL",
        "2026-09-27",
        cents(22400.00),
        counterparty="STRIPE RESERVE RELEASE",
        description="ACH IN STRIPE RESERVE RELEASE",
        matched=True,
    )
    ctx.planted_recons.append(_recon_stub("REC-STRIPE-2026-09", "2026-09"))


def plant_merrimack(ctx: CompanyScenarioContext) -> None:
    wires = {
        "2025-12": 180000.00,
        "2026-01": 220000.00,
        "2026-02": 240000.00,
        "2026-03": 250000.00,
        "2026-04": 260000.00,
        "2026-05": 270000.00,
        "2026-06": 280000.00,
        "2026-07": 227600.00,
        "2026-08": 472400.00,
    }
    if round(sum(wires.values()), 2) != 2200000.00:
        wires["2026-07"] = round(2200000.00 - sum(v for k, v in wires.items() if k != "2026-07"), 2)
    running_1300 = 0.0
    for period, cash_out in wires.items():
        tu = 512400.00 if period == "2026-08" else round(cash_out + 40000.00, 2)
        if period == "2026-08":
            tu = 512400.00
            cash_out = 472400.00
        running_1300 = round(running_1300 + (tu - cash_out), 2)
        end = _month_end(period)
        nxt = _add_days(end, 1)
        _je(
            ctx,
            f"JE-IC-TU-{period}",
            period=period,
            date=end,
            debit="1300-Due-From-Affiliate",
            credit="2100-Due-To-Affiliate",
            amount_minor=cents(tu),
            memo="IC true-up EU",
            customer="Maximor EU BV",
            source=f"JE-IC-TU-{period}",
            txn=f"TXN-IC-TU-{period}",
            category="operating",
            entry_type="manual",
            poster="USR-JE-04",
            approver="USR-REV-04",
        )
        _je(
            ctx,
            f"JE-IC-CLR-{period}",
            period=nxt[:7] if nxt[:7] != period else period,
            date=nxt if period != "2026-08" else "2026-08-31",
            debit="2100-Due-To-Affiliate",
            credit="1000-Cash",
            amount_minor=cents(cash_out),
            memo="IC sweep EU",
            source=f"JE-IC-CLR-{period}",
            txn=f"TXN-MRH-{period}",
            category="volume_cash",
            entry_type="manual",
            poster="USR-JE-04",
            approver="USR-REV-04",
        )
        _bank(
            ctx,
            f"TXN-MRH-{period}",
            end if period != "2026-08" else "2026-08-31",
            -cents(cash_out),
            counterparty="MERRIMACK HOLDINGS LLC",
            description="WIRE OUT IC SWEEP EU EIN 83-6612045 100 LOW STREET NEWBURYPORT",
            matched=True,
        )
    # Grow 1300 to 4,851,220 via remaining monthly residual postings.
    residual = round(4851220.00 - 40000.00 * 9, 2)
    _je(
        ctx,
        "JE-IC-BAL-SEED",
        period="2025-12",
        date="2025-12-15",
        debit="1300-Due-From-Affiliate",
        credit="4000-Revenue",
        amount_minor=cents(max(residual, 0.01)),
        memo="EU affiliate billings",
        customer="Maximor EU BV",
        source="INV-AR-IC-EU-SEED",
        txn="TXN-IC-BAL-SEED",
        category="revenue",
        entry_type="ar_invoice",
        poster="USR-JE-04",
        approver="USR-REV-04",
    )
    _add_ar(
        ctx,
        "INV-AR-IC-EU-SEED",
        "CUST-IC-EU",
        "Maximor EU BV",
        "2025-12-15",
        "2026-12-15",
        max(residual, 0.01),
        "OPEN",
        "EU affiliate support",
    )
    if ctx.audit_journals:
        sample = ctx.audit_journals[0].model_copy(
            update={"entry_id": "AUD-SAMP-IC-08", "memo": "IC true-up August"}
        )
        ctx.audit_journals.append(sample)


def plant_brightline(ctx: CompanyScenarioContext) -> None:
    ar_months = {}
    remaining_ar = 419800.00
    for index, period in enumerate(
        [
            "2025-09",
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
            "2026-08",
        ]
    ):
        amount = 34983.33 if index < 11 else round(remaining_ar - 34983.33 * 11, 2)
        ar_months[period] = amount
        _add_ar(
            ctx,
            f"INV-AR-BLM-{period}",
            "CUST-004",
            "Brightline Media",
            f"{period}-12",
            _add_days(f"{period}-12", 30),
            amount,
            "PAID" if period < "2026-09" else "OPEN",
            "Platform invoice",
        )
        _pay_ar(
            ctx,
            f"PAY-BLM-{period}",
            _month_end(period),
            amount,
            "Brightline Media Group",
            "CUST-004",
            remittance=f"INV-AR-BLM-{period}",
            bank_id=f"TXN-BLM-IN-{period}",
        )
        _bank(
            ctx,
            f"TXN-BLM-IN-{period}",
            _month_end(period),
            cents(amount),
            counterparty="BRIGHTLINE MEDIA",
            description=f"ACH IN BRIGHTLINE MEDIA {period}",
            matched=True,
        )
        _je(
            ctx,
            f"JE-AR-BLM-{period}",
            period=period,
            date=f"{period}-12",
            debit="1100-AR",
            credit="4000-Revenue",
            amount_minor=cents(amount),
            memo="Brightline Media platform",
            customer="Brightline Media",
            source=f"INV-AR-BLM-{period}",
            txn=f"TXN-AR-BLM-{period}",
            category="revenue",
            entry_type="ar_invoice",
        )
    _add_ar(
        ctx,
        "INV-AR-BLM-2026-09",
        "CUST-004",
        "Brightline Media",
        "2026-09-12",
        "2026-10-12",
        38200.00,
        "OPEN",
        "Platform invoice September",
    )
    _je(
        ctx,
        "JE-AR-BLM-2026-09",
        period="2026-09",
        date="2026-09-12",
        debit="1100-AR",
        credit="4000-Revenue",
        amount_minor=cents(38200.00),
        memo="Brightline Media platform",
        customer="Brightline Media",
        source="INV-AR-BLM-2026-09",
        txn="TXN-AR-BLM-2026-09",
        category="revenue",
        entry_type="ar_invoice",
    )
    remaining_ap = 444400.00
    _po_only(ctx, "PO-BLS-STANDING", "Brightline Studio LLC", 600000.0, "2025-09-04", "Demand-gen retainer")
    for index, period in enumerate(
        [
            "2025-09",
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
            "2026-08",
        ]
    ):
        amount = 37033.33 if index < 11 else round(remaining_ap - 37033.33 * 11, 2)
        _ap_match(
            ctx,
            f"INV-BLS-{period}",
            "Brightline Studio LLC",
            amount,
            f"{period}-14",
            _add_days(f"{period}-14", 15),
            f"BLS-{period}",
            "Demand-gen retainer",
            po_id=f"PO-BLS-{period}",
            receipt_id=f"GR-BLS-{period}",
            vendor_id="VEND-BLS-01",
            paid=True,
            pay_id=f"PAY-BLS-{period}",
            bank_id=f"TXN-BLS-OUT-{period}",
            requested_by="EMP-3310",
        )
    _ap_match(
        ctx,
        "INV-BLS-2026-09",
        "Brightline Studio LLC",
        40400.00,
        "2026-09-14",
        "2026-09-29",
        "BLS-2026-09",
        "Demand-gen retainer",
        po_id="PO-BLS-2026-09",
        receipt_id="GR-BLS-2026-09",
        vendor_id="VEND-BLS-01",
        paid=False,
        requested_by="EMP-3310",
    )


def plant_cambridge(ctx: CompanyScenarioContext) -> None:
    _add_contract(
        ctx,
        "CTR-CAM-001",
        "Cambridge Properties",
        "2021-08-01",
        monthly_minimum=48000.0,
        description="Cambridge HQ lease. CAM true-up annual.",
        extra={"cam_true_up_cadence": "annual", "lockbox": "44552109"},
    )
    for period in ("2026-06", "2026-07", "2026-08", "2026-09"):
        _ap_match(
            ctx,
            f"INV-CAM-RENT-{period}",
            "Cambridge Properties",
            48000.00,
            f"{period}-01",
            f"{period}-05",
            f"CAM-RENT-{period}",
            "Cambridge HQ rent",
            po_id=f"PO-CAM-RENT-{period}",
            receipt_id=f"GR-CAM-RENT-{period}",
            vendor_id="VEND-013",
            paid=period < "2026-09",
            pay_id=f"PAY-CAM-RENT-{period}",
            bank_id=f"TXN-CAM-RENT-{period}",
            account="6300-Occupancy",
        )
        if period >= "2026-06":
            ctx.bank_transactions[f"TXN-CAM-RENT-{period}"] = cash_bank(
                f"TXN-CAM-RENT-{period}",
                f"{period}-03",
                -cents(48000.00),
                description="ACH OUT CAMBRIDGE PROPERTY SVC",
                reference=f"RENT-{period}",
                counterparty="CAMBRIDGE PROPERTY SVC",
                transaction_type="ach_debit",
                metadata={"receiving_account_last4": "2190", "vendor_id": "VEND-013"},
            )
            ctx.recon_labels[f"TXN-CAM-RENT-{period}"] = {
                "match_type": "EXACT_MATCH",
                "disposition": "MATCHED",
                "ledger_ids": [f"GL-CAM-RENT-{period}"],
            }
    cps_amounts = [
        8427.18,
        8410.22,
        8390.44,
        8440.18,
        8460.22,
        8488.18,
        8510.40,
        8520.18,
        8490.22,
        8506.18,
        8518.40,
        8522.18,
        8530.22,
        8544.18,
        8650.84,
    ]
    if round(sum(cps_amounts), 2) != 126408.22:
        cps_amounts[-1] = round(126408.22 - sum(cps_amounts[:-1]), 2)
    start = date(2025, 7, 15)
    _po_only(ctx, "PO-CPS-CAM", "Cambridge Property Services", 150000.0, "2025-07-08", "CAM reconciliation")
    for index, amount in enumerate(cps_amounts):
        period = (start.replace(day=1) + timedelta(days=32 * index)).strftime("%Y-%m")
        _ap_match(
            ctx,
            f"INV-CPS-{period}",
            "Cambridge Property Services",
            amount,
            f"{period}-15",
            _add_days(f"{period}-15", 20),
            f"CPS-CAM-{period}",
            "CAM reconciliation",
            po_id=f"PO-CPS-{period}",
            receipt_id=f"GR-CPS-{period}",
            vendor_id="VEND-CPS-01",
            paid=period < "2026-09",
            account="6300-Occupancy",
        )
    _ap_match(
        ctx,
        "INV-CAM-CAM-2026",
        "Cambridge Properties",
        18200.00,
        "2026-03-31",
        "2026-04-30",
        "CAM-ANNUAL-2026",
        "Annual CAM true-up Q1 2026",
        po_id="PO-CAM-ANNUAL-2026",
        receipt_id="GR-CAM-ANNUAL-2026",
        vendor_id="VEND-013",
        paid=True,
        account="6300-Occupancy",
    )
    _ap_match(
        ctx,
        "INV-CPS-RENT-2026-06",
        "Cambridge Property Services",
        4000.00,
        "2026-06-02",
        "2026-06-16",
        "CPS-RENT-2026-06",
        "Occupancy support June",
        po_id="PO-CPS-RENT-2026-06",
        receipt_id="GR-CPS-RENT-2026-06",
        vendor_id="VEND-CPS-01",
        paid=True,
        account="6300-Occupancy",
    )
    _ap_match(
        ctx,
        "INV-CPS-RENT-2026-08",
        "Cambridge Property Services",
        4000.00,
        "2026-08-02",
        "2026-08-16",
        "CPS-RENT-2026-08",
        "Occupancy support August",
        po_id="PO-CPS-RENT-2026-08",
        receipt_id="GR-CPS-RENT-2026-08",
        vendor_id="VEND-CPS-01",
        paid=True,
        account="6300-Occupancy",
    )
    from accrual.models import OpenAccrual

    ctx.accruals.append(
        OpenAccrual(
            accrual_id="ACC-CAM-2026-09",
            vendor="Cambridge Properties",
            period="2026-09",
            estimated_amount=48000.0,
            expense_account="6300-Occupancy",
            status="open",
            estimation_method="contract_commitment",
            confidence=0.7,
            evidence=["contract:CTR-CAM-001"],
            reasoning_summary="Lease month occupancy.",
            journal_entry_id="JE-ACC-CAM-202609",
            created_at="2026-09-30T00:00:00Z",
        )
    )
    _je(
        ctx,
        "JE-ACC-CAM-202609",
        period="2026-09",
        date="2026-09-30",
        debit="6300-Occupancy",
        credit="Accrued Expenses",
        amount_minor=cents(48000.00),
        memo="Cambridge occupancy accrual",
        vendor="Cambridge Properties",
        source="ACC-CAM-2026-09",
        txn="ACC-CAM-2026-09",
        category="operating",
        entry_type="accrual",
    )
    rider_pre = PrepaidItem(
        prepaid_id="PRE-CAM-Q3",
        vendor="Cambridge Properties",
        description="Q3 occupancy prepaid",
        source_document_id="INV-CAM-RENT-2026-07",
        total_amount=48000.0,
        start_date="2026-07-01",
        end_date="2026-09-30",
        initial_account="1220-Prepaid-Other",
        expense_account="6300-Occupancy",
        amortization_method="straight_line_monthly",
        status="active",
        created_at="2026-07-01T00:00:00Z",
        transaction_id="TXN-PRE-CAM-Q3",
    )
    ctx.prepaids.append(rider_pre)
    ctx.prepaid_schedule.append(
        PrepaidScheduleLine(
            prepaid_id="PRE-CAM-Q3",
            period="2026-09",
            amount=16000.0,
            status="posted",
            method="straight_line_monthly",
        )
    )
    for row in ctx.payroll_register:
        if row["employee_id"] == "EMP-2201" and row["pay_date"] >= "2025-07-01":
            row["allowance"] = 1200.00
            row["allowance_id"] = "ALLW-CHO"


def plant_closecosmetic(ctx: CompanyScenarioContext) -> None:
    for period, park_id, unpark_id, unpark_date in (
        ("2026-03", "JE-CASH-PARK-2026-03", "JE-CASH-UNPARK-2026-04", "2026-04-02"),
        ("2026-05", "JE-CASH-PARK-2026-05", "JE-CASH-UNPARK-2026-06", "2026-06-02"),
        ("2026-08", "JE-CASH-PARK-2026-08", "", ""),
    ):
        end = _month_end(period)
        _je(
            ctx,
            park_id,
            period=period,
            date=end,
            debit="1030-Undeposited-Funds",
            credit="1000-Cash",
            amount_minor=cents(186420.18),
            memo="deposits in transit",
            source="DIT-FAKE-0831" if period == "2026-08" else park_id,
            txn=park_id,
            category="operating",
            entry_type="manual",
            poster="USR-JE-04",
            approver="USR-REV-04",
        )
        if unpark_id:
            _je(
                ctx,
                unpark_id,
                period=unpark_date[:7],
                date=unpark_date,
                debit="1000-Cash",
                credit="1030-Undeposited-Funds",
                amount_minor=cents(186420.18),
                memo="clear deposits in transit",
                source=unpark_id,
                txn=unpark_id,
                category="operating",
                entry_type="manual",
                poster="USR-JE-04",
                approver="USR-REV-04",
            )
    _je(
        ctx,
        "JE-PR-ACC-2026-08",
        period="2026-08",
        date="2026-08-31",
        debit="6100-Payroll",
        credit="2200-Payroll-Accrual",
        amount_minor=cents(84000.00),
        memo="Payroll accrual August",
        source="JE-PR-ACC-2026-08",
        txn="TXN-PR-ACC-2026-08",
        category="payroll",
        entry_type="accrual",
        poster="USR-JE-04",
        approver="USR-REV-04",
    )
    _je(
        ctx,
        "JE-PR-SHIFT-2026-08",
        period="2026-08",
        date="2026-08-31",
        debit="2200-Payroll-Accrual",
        credit="6100-Payroll",
        amount_minor=cents(84000.00),
        memo="Reverse payroll accrual",
        source="JE-PR-SHIFT-2026-08",
        txn="TXN-PR-SHIFT-2026-08",
        category="payroll",
        entry_type="manual",
        poster="USR-JE-04",
        approver="USR-REV-04",
    )
    _je(
        ctx,
        "JE-PR-AR-2026-08",
        period="2026-08",
        date="2026-08-31",
        debit="1350-Other-Receivable",
        credit="2200-Payroll-Accrual",
        amount_minor=cents(84000.00),
        memo="Payroll reclass",
        source="JE-PR-AR-2026-08",
        txn="TXN-PR-AR-2026-08",
        category="operating",
        entry_type="manual",
        poster="USR-JE-04",
        approver="USR-REV-04",
    )
    _je(
        ctx,
        "JE-AUG-LATE-01",
        period="2026-08",
        date="2026-08-31",
        debit="6000-Operating",
        credit="2000-AP",
        amount_minor=cents(41206.18),
        memo="Westbrook August receipt",
        vendor="Westbrook Tooling",
        source="INV-WBT-2026-08",
        txn="TXN-AUG-LATE-01",
        category="operating",
        entry_type="manual",
        poster="USR-JE-04",
        approver="USR-REV-04",
        timestamp="2026-09-04T08:12:00Z",
        posting_date="2026-09-04",
        post_close=False,
    )
    from fixed_assets.models import FixedAsset

    ctx.fixed_assets.append(
        FixedAsset(
            asset_id="FA-LEN-ROLL-26",
            description="Lenovo laptop rollout",
            vendor="Lenovo",
            acquisition_date="2026-03-18",
            placed_in_service_date="2026-03-18",
            cost=round(168 * 2528.10, 2),
            useful_life_months=36,
            asset_account="1500-PPE",
            accumulated_depreciation_account="1510-Accum-Dep",
            depreciation_expense_account="Depreciation Expense",
            source_document_id="INV-LEN-ROLL-26",
            transaction_id="TXN-FA-LEN-ROLL",
        )
    )
    _ap_match(
        ctx,
        "INV-LEN-ROLL-26",
        "Lenovo",
        round(168 * 2528.10, 2),
        "2026-03-18",
        "2026-04-17",
        "LEN-ROLL-26",
        "Laptop rollout 168 units",
        po_id="PO-LEN-ROLL-26",
        receipt_id="GR-LEN-ROLL",
        vendor_id="VEND-020",
        paid=True,
        qty=168,
        unit=2528.10,
        account="1500-PPE",
        gr_timestamp="11:03:00",
    )
    _je(
        ctx,
        "JE-FA-LEN-2026-09",
        period="2026-09",
        date="2026-09-30",
        debit="Depreciation Expense",
        credit="1510-Accum-Dep",
        amount_minor=cents(4283.58),
        memo="Lenovo rollout depreciation",
        vendor="Lenovo",
        source="FA-LEN-ROLL-26",
        txn="TXN-FA-LEN-2026-09",
        category="operating",
        entry_type="depreciation",
    )


def plant_freight(ctx: CompanyScenarioContext) -> None:
    remaining = 61288.40 - 12440.18
    months = [
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
    ]
    each = round(remaining / 10, 2)
    _po_only(ctx, "PO-FLE-ACC", "Freightline Expedite", 80000.0, "2025-11-10", "Accessorials")
    for index, period in enumerate(months):
        amount = each if index < 9 else round(remaining - each * 9, 2)
        _ap_match(
            ctx,
            f"INV-FLE-{period}",
            "Freightline Expedite",
            amount,
            f"{period}-21",
            _add_days(f"{period}-21", 15),
            f"FLE-{period}-X",
            "Accessorial fuel and liftgate",
            po_id=f"PO-FLE-{period}",
            receipt_id=f"GR-FLE-{period}",
            vendor_id="VEND-FLE-01",
            paid=True,
            pay_id=f"PAY-FLE-{period}",
            bank_id=f"TXN-FLE-{period}",
            account="5300-Freight",
            category="freight",
        )
    _ap_match(
        ctx,
        "INV-FLE-2026-09",
        "Freightline Expedite",
        12440.18,
        "2026-09-21",
        "2026-10-06",
        "FLE-2026-09-X",
        "Accessorial fuel and liftgate",
        po_id="PO-FLE-2026-09",
        receipt_id="GR-FLE-2026-09",
        vendor_id="VEND-FLE-01",
        paid=False,
        account="5300-Freight",
        category="freight",
    )
    _ap_match(
        ctx,
        "INV-FLE-0716",
        "Freightline Expedite",
        1531.96,
        "2026-07-16",
        "2026-07-30",
        "FLE-0716-X",
        "Accessorial mixed ACH",
        po_id="PO-FLE-0716",
        receipt_id="GR-FLE-0716",
        vendor_id="VEND-FLE-01",
        paid=True,
        account="5300-Freight",
        category="freight",
        requested_by="EMP-4128",
    )
    _bank(
        ctx,
        "TXN-MIX-2026-07-16",
        "2026-07-16",
        -cents(26412.40),
        counterparty="KESTREL INDUSTRIAL SUPPLY LLC",
        description="ACH OUT MIXED KESTREL FREIGHTLINE EXPEDITE",
        matched=True,
    )
    _bank(
        ctx,
        "TXN-MIX-2026-08-20",
        "2026-08-20",
        -cents(25118.62),
        counterparty="KESTREL INDUSTRIAL SUPPLY LLC",
        description="ACH OUT MIXED KESTREL FREIGHTLINE EXPEDITE",
        matched=True,
    )
    _add_contract(
        ctx,
        "CTR-FRL-001",
        "Freightline Logistics",
        "2024-01-01",
        monthly_minimum=0.0,
        description="Standard inbound freight. Accessorials not in this contract.",
    )


def densify_open_subledgers(ctx: CompanyScenarioContext) -> None:
    ap_open = sum(
        inv.amount
        for inv in ctx.ap_invoices.values()
        if inv.invoice_id not in {pay_id for pay in ctx.vendor_payments.values() for pay_id in pay.invoice_ids}
    )
    seq = 1
    held_open = {"VEND-001-DUP", "VEND-010", "VEND-018", "VEND-015", "VEND-016"}
    vendors = [row for row in ctx.vendors.values() if not row.get("unusual") and row["vendor_id"] not in held_open]
    while ap_open < AP_OPEN - 5000 and seq < 80:
        vendor = vendors[seq % len(vendors)]
        amount = round(180000.00 + (seq * 137.18) % 90000, 2)
        inv_id = f"INV-OPEN-{seq:03d}"
        _ap_match(
            ctx,
            inv_id,
            vendor["name"],
            amount,
            f"2026-09-{(seq % 27) + 1:02d}",
            f"2026-10-{(seq % 27) + 1:02d}",
            f"OPEN-{seq:04d}",
            "Open operating payable",
            po_id=f"PO-OPEN-{seq:03d}",
            receipt_id=f"GR-OPEN-{seq:03d}",
            vendor_id=vendor["vendor_id"],
            paid=False,
        )
        ap_open = round(ap_open + amount, 2)
        seq += 1
    ar_open = sum(inv.outstanding_amount for inv in ctx.ar_invoices.values())
    seq = 1
    customers = list(ctx.customers.values())
    while ar_open < AR_OPEN - 5000 and seq < 60:
        customer = customers[seq % len(customers)]
        amount = round(420000.00 + (seq * 211.40) % 180000, 2)
        inv_id = f"INV-AR-OPEN-{seq:03d}"
        if inv_id in ctx.ar_invoices:
            seq += 1
            continue
        _add_ar(
            ctx,
            inv_id,
            customer.customer_id,
            customer.customer_name,
            f"2026-0{(seq % 6) + 3}-{(seq % 27) + 1:02d}" if (seq % 6) + 3 <= 9 else f"2026-07-{(seq % 27) + 1:02d}",
            "2026-12-31",
            amount,
            "OPEN",
            "Uncollected platform",
        )
        ar_open = round(ar_open + amount, 2)
        seq += 1


def overlay_forecast(ctx: CompanyScenarioContext) -> None:
    extras = [
        ForecastLine(
            line_id="FC-MRO-KIS",
            source_type="other",
            source_id="INV-KIS-2026-09",
            expected_date="2026-09-21",
            amount=-24880.44,
            confidence=0.9,
            rationale="as planned",
            source_workflow="reporting",
            evidence_refs=["vendor:VEND-KIS-01"],
        ),
        ForecastLine(
            line_id="FC-OTHER-IN",
            source_type="other",
            source_id="6950-Cash-Over-Short",
            expected_date="2026-09-28",
            amount=7187.60,
            confidence=0.4,
            rationale="other income true-up",
            source_workflow="reporting",
            evidence_refs=["gl:6950-Cash-Over-Short"],
        ),
        ForecastLine(
            line_id="FC-PIN-BH",
            source_type="receivable",
            source_id="INV-AR-PIN-BH-01",
            expected_date="2026-10-05",
            amount=2400000.00,
            confidence=0.6,
            rationale="Pinnacle collections week 3",
            source_workflow="reporting",
            evidence_refs=["receivable:INV-AR-PIN-BH-01"],
        ),
        ForecastLine(
            line_id="FC-IC-IN",
            source_type="other",
            source_id="1300-Due-From-Affiliate",
            expected_date="2026-11-02",
            amount=500000.00,
            confidence=0.5,
            rationale="affiliate receivable",
            source_workflow="reporting",
            evidence_refs=["gl:1300-Due-From-Affiliate"],
        ),
    ]
    ctx.forecast_lines.extend(extras)
    if ctx.budget:
        for item in ctx.budget:
            if item.period == "2026-08":
                item.revenue = 30820000.0
                item.cogs = 11095200.0
                item.gross_profit = 19724800.0
                item.gross_margin_pct = 0.64
            if item.period == "2026-09":
                item.revenue = 31140000.0
                item.cogs = 12144600.0
                item.gross_profit = 18995400.0
                item.gross_margin_pct = 0.61


def overlay_policies_and_workpapers(ctx: CompanyScenarioContext) -> None:
    ctx.policies.extend(
        [
            CompanyPolicy(
                policy_id="P-REV-001",
                title="Revenue recognition",
                description="FOB destination. Bill-and-hold requires delivery or lapse of return rights.",
                action="HOLD_REVENUE",
                conditions={"fob": "destination"},
            ),
            CompanyPolicy(
                policy_id="P-INV-001",
                title="Consignment inventory",
                description="Goods in a consignment cage are not sold.",
                action="KEEP_ON_BALANCE_SHEET",
                conditions={"location_type": "consignment"},
            ),
            CompanyPolicy(
                policy_id="P-CASH-UNDEP-AGE",
                title="Undeposited funds aging",
                description="Items in 1030 older than 5 business days are exceptions.",
                action="EXCEPTION_OPEN",
                conditions={"account": "1030-Undeposited-Funds", "max_business_days": 5},
            ),
        ]
    )
    pack = ctx.workpapers.get("close/prior_period/2026-08/cash_rec.txt", "")
    if "over/short true-up" not in pack:
        ctx.workpapers["close/prior_period/2026-08/cash_rec.txt"] = pack.replace(
            "No unexplained difference remained at sign-off.",
            "Over/short true-up $7,206.18 posted as JE-REC-PLUG-2026-08. "
            "No unexplained difference remained at sign-off.",
        )
    sep = ctx.workpapers.get("close/2026-09/cash_rec.txt", "")
    if "true-up" not in sep.lower():
        ctx.workpapers["close/2026-09/cash_rec.txt"] = sep + "\nTrue-up line: \n"


def set_cash_and_company(ctx: CompanyScenarioContext) -> None:
    sep = [item for item in ctx.bank_transactions.values() if str(item.date).startswith("2026-09")]
    movement = sum(item.amount_minor for item in sep)
    target = cents(OPERATING_CASH_2026_09_30)
    ctx.cash_opening_bank_minor = target - movement
    ctx.cash_opening_ledger_minor = ctx.cash_opening_bank_minor
    ctx.opening_cash_forecast_minor = ctx.cash_opening_bank_minor
    ctx.company.operating_cash = OPERATING_CASH_2026_09_30
    ctx.company.active_vendors = len(ctx.vendors)
    ctx.company.w2_headcount = len(ctx.employee_master)
    ctx.company.contractors_1099 = CONTRACTOR_1099_COUNT
    ctx.company.biweekly_payroll_gross = BIWEEKLY_PAYROLL_GROSS
    if ctx.period_balances.get(ctx.period):
        ctx.period_balances[ctx.period].cash = OPERATING_CASH_2026_09_30
        ctx.period_balances[ctx.period].ap = AP_OPEN
        ctx.period_balances[ctx.period].ar = AR_OPEN
    if ctx.cash_position is not None:
        ctx.cash_position.bank_balance = OPERATING_CASH_2026_09_30
    for item in ctx.payroll:
        if item.schedule_id == "PR-2026-10-02" or item.pay_date == "2026-10-02":
            item.expected_amount = BIWEEKLY_PAYROLL_GROSS
        else:
            item.expected_amount = BIWEEKLY_PAYROLL_GROSS
    for item in ctx.forecast_actuals:
        if item.movement_id == "ACT-PAYROLL-HIGH":
            item.amount = -(BIWEEKLY_PAYROLL_GROSS + 17821.40 + 4500.06)
            item.description = "Payroll above schedule after supported OT"


def attach_holdout(ctx: CompanyScenarioContext) -> None:
    if ctx.expected is None:
        return
    ctx.expected.reconciliation_statuses["TXN-2026-09-015"] = "EXCEPTION_OPEN"
    payload = json.loads(INDEX_PATH.read_text()) if INDEX_PATH.is_file() else {"scenarios": []}
    items = []
    for row in payload.get("scenarios", []):
        finding = row.get("expected_finding") or ""
        reason = ""
        magnitude = ""
        record_ids: list[str] = []
        if isinstance(finding, dict):
            reason = str(finding.get("reason_code") or "")
            magnitude = str(finding.get("magnitude") or "")
            raw_ids = finding.get("record_ids") or []
            if isinstance(raw_ids, str):
                record_ids = [part.strip() for part in raw_ids.split(",") if part.strip()]
            else:
                record_ids = [str(item) for item in raw_ids]
        else:
            parts = [part.strip() for part in str(finding).split("|")]
            reason = parts[0] if parts else ""
            magnitude = parts[1] if len(parts) > 1 else ""
            if len(parts) > 2:
                record_ids = [part.strip() for part in parts[2].split(",") if part.strip()]
        must_unmatched = ["TXN-2026-09-015"] if row.get("id") == "ADV-CASH-014" else []
        items.append(
            AdversarialHoldoutItem(
                id=row["id"],
                storyline=row.get("storyline") or "",
                reason_code=reason,
                stealth=int(row.get("stealth") or 0),
                magnitude=magnitude,
                record_ids=list(record_ids),
                plant_objects=list(row.get("plant_objects") or []),
                must_remain_unmatched=must_unmatched,
            )
        )
    ctx.expected.adversarial_holdout = items


def _add_vendor(
    ctx: CompanyScenarioContext,
    vendor_id: str,
    name: str,
    *,
    first_seen: str,
    tax_id: str,
    address: str,
    routing: str = "",
    account: str = "",
    created_by: str = "",
    last_modified_by: str = "",
    organizer: str = "",
    insurance_cert: str | None = None,
    w9: str | None = None,
) -> None:
    if vendor_id in ctx.vendors:
        ctx.vendors[vendor_id].update(
            {
                "name": name,
                "legal_name": name,
                "tax_id": tax_id,
                "address": address,
                "unusual": False,
            }
        )
        return
    last4 = (account or "0000")[-4:]
    ctx.vendors[vendor_id] = {
        "vendor_id": vendor_id,
        "name": name,
        "first_seen": first_seen,
        "unusual": False,
        "legal_name": name,
        "dba": "",
        "tax_id": tax_id,
        "address": address,
        "phone": "+1 617-555-0100",
        "billing_email": f"billing@{vendor_id.lower()}.example",
        "payment_terms": "net 30",
        "bank_name": "First National Bank",
        "bank_routing": routing or "011000390",
        "bank_account": account or f"10{vendor_id[-2:]}0000",
        "bank_account_last4": last4,
        "bank_changed_on": "2026-06-12" if vendor_id == "VEND-KIS-01" else "",
        "change_memo": "normalize ACH formatting / strip spaces" if vendor_id == "VEND-KIS-01" else "",
        "aliases": [],
        "duplicate_risk_key": vendor_id,
        "currency": "USD",
        "country": "US",
        "status": "active",
        "created_by": created_by,
        "last_modified_by": last_modified_by or created_by,
        "organizer_name": organizer,
        "insurance_cert": insurance_cert,
        "w9": w9,
    }
    _safe_named(ctx, vendor_id)


def _po_only(ctx, po_id: str, vendor: str, amount: float, created: str, description: str) -> None:
    if po_id in ctx.purchase_orders:
        return
    ctx.purchase_orders[po_id] = PurchaseOrder(
        po_id=po_id,
        vendor=vendor,
        authorized_amount=amount,
        description=description,
        status="approved",
        created_date=created,
        approval_limit=max(amount, 25000.0),
        approver="Jordan Hale",
    )
    _safe_named(ctx, po_id)


def _ap_match(
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
    vendor_id: str = "",
    paid: bool = False,
    pay_id: str = "",
    bank_id: str = "",
    approver: str = "Priya Nair",
    approval_limit: float | None = None,
    requested_by: str = "",
    qty: int = 1,
    unit: float | None = None,
    sku: str = "",
    po_date: str = "",
    gr_date: str = "",
    dock: str = "",
    gr_timestamp: str = "12:00:00",
    reuse_po: bool = False,
    initiator: str = "USR-PAY-01",
    remit_street: str = "",
    discount: bool = False,
    creator_asset: str = "",
    account: str = "6000-Operating",
    category: str = "volume_opex",
    service_period: str = "",
) -> None:
    amount = round(float(amount), 2)
    unit = round(amount / qty, 2) if unit is None else unit
    limit = approval_limit if approval_limit is not None else max(amount, 25000.0)
    if po_id not in ctx.purchase_orders:
        ctx.purchase_orders[po_id] = PurchaseOrder(
            po_id=po_id,
            vendor=vendor,
            authorized_amount=amount if not reuse_po else ctx.purchase_orders.get(po_id, PurchaseOrder(po_id=po_id, vendor=vendor, authorized_amount=amount, status="approved")).authorized_amount,
            description=description,
            status="approved",
            created_date=po_date or invoice_date,
            approval_limit=limit,
            approver=approver,
        )
        _safe_named(ctx, po_id)
    elif not reuse_po:
        pass
    if receipt_id not in ctx.goods_receipts:
        ctx.goods_receipts[receipt_id] = GoodsReceipt(
            receipt_id=receipt_id,
            po_id=po_id,
            received=True,
            received_date=gr_date or invoice_date,
            amount_received=amount,
            quantity_ordered=qty,
            quantity_received=qty,
        )
        _safe_named(ctx, receipt_id)
    if invoice_id not in ctx.ap_invoices:
        extra = f"{description}. SKU {sku}".strip()
        if service_period:
            extra += f" Service period {service_period}."
        ctx.ap_invoices[invoice_id] = Invoice(
            invoice_id=invoice_id,
            vendor=vendor,
            po_id=po_id,
            amount=amount,
            invoice_date=invoice_date,
            due_date=due_date,
            vendor_invoice_number=vendor_invoice_number,
            description=extra,
            payment_terms="2/10 net 30" if discount else "net 30",
            early_payment_discount_percent=2.0 if discount else 0,
            early_payment_discount_deadline=_add_days(invoice_date, 10) if discount else None,
        )
        _safe_named(ctx, invoice_id)
        lines = [(sku or description, float(qty), float(unit))]
        try:
            text = render_vendor_invoice(
                vendor,
                vendor_invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                po=po_id,
                lines=lines,
                amount=amount,
                extra=(
                    (f"Remit to: {remit_street}\n" if remit_street else "")
                    + (f"PDF creator asset {creator_asset}\n" if creator_asset else "")
                    + (f"Delivery dock {dock}\n" if dock else "")
                    + (f"Requested by {requested_by}\n" if requested_by else "")
                    + "Remit ACH per vendor master. Line items above. Tax $0.00.\n"
                ),
            )
        except ValueError:
            text = invoice_document_for(
                invoice_id,
                vendor,
                vendor_invoice_number,
                amount=amount,
                invoice_date=invoice_date,
                due_date=due_date,
                po_id=po_id,
                description=description,
            )
        ctx.document_texts[f"invoices/{invoice_id}.txt"] = text
        je_id = f"JE-AP-{invoice_id}"
        if je_id not in ctx.journal_entries:
            _je(
                ctx,
                je_id,
                period=invoice_date[:7],
                date=invoice_date,
                debit=account,
                credit="2000-AP",
                amount_minor=cents(amount),
                memo=description,
                vendor=vendor,
                source=invoice_id,
                txn=f"TXN-AP-{invoice_id}",
                category=category if account in COGS_ACCOUNTS else "volume_opex" if account == "6000-Operating" else "operating",
                entry_type="ap_invoice",
            )
    if paid:
        pay_id = pay_id or f"PAY-{invoice_id}"
        bank_id = bank_id or f"TXN-{invoice_id}"
        if pay_id not in ctx.vendor_payments:
            ctx.vendor_payments[pay_id] = VendorPayment(
                payment_id=pay_id,
                invoice_ids=[invoice_id],
                vendor=vendor,
                vendor_id=vendor_id,
                payment_date=_add_days(invoice_date, 12),
                amount_minor=cents(amount),
                method="ach",
                bank_reference=bank_id,
                description=f"ACH {vendor}",
                initiator_id=initiator,
                approver_id="USR-PAY-01",
            )
            _safe_named(ctx, pay_id)
        _bank(
            ctx,
            bank_id,
            _add_days(invoice_date, 12),
            -cents(amount),
            counterparty=vendor.upper(),
            description=f"ACH OUT {vendor.upper()}",
            matched=True,
        )


def _add_ar(
    ctx: CompanyScenarioContext,
    invoice_id: str,
    customer_id: str,
    name: str,
    invoice_date: str,
    due_date: str,
    amount: float,
    status: str,
    description: str,
    ship_to: str = "",
    extra: dict | None = None,
) -> None:
    if invoice_id in ctx.ar_invoices:
        return
    meta = extra or {}
    if ship_to:
        meta["ship_to"] = ship_to
    ctx.ar_invoices[invoice_id] = CustomerInvoice(
        invoice_id=invoice_id,
        customer_id=customer_id,
        customer_name=name,
        invoice_date=invoice_date,
        due_date=due_date,
        original_amount=amount,
        outstanding_amount=0.0 if status == "PAID" else amount,
        status=status,  # type: ignore[arg-type]
        description=description,
        created_at=f"{invoice_date}T09:00:00Z",
        metadata=meta,
    )
    _safe_named(ctx, invoice_id)


def _pay_ar(
    ctx: CompanyScenarioContext,
    payment_id: str,
    payment_date: str,
    amount: float,
    payer: str,
    customer_id: str,
    *,
    remittance: str,
    bank_id: str,
    applied_at: str = "",
    applied_invoice: str = "",
    named_invoice: str = "",
) -> None:
    if payment_id in ctx.ar_payments:
        return
    ctx.ar_payments[payment_id] = CustomerPayment(
        payment_id=payment_id,
        payment_date=payment_date,
        amount=amount,
        payer_name=payer,
        customer_id=customer_id,
        bank_reference=bank_id,
        remittance_text=remittance,
        invoice_reference=named_invoice or remittance,
        unapplied_amount=0.0,
        application_status="APPLIED",
        metadata={
            "applied_at": applied_at or f"{payment_date}T12:00:00Z",
            "applied_invoice_id": applied_invoice,
            "named_invoice_id": named_invoice,
        },
    )
    _safe_named(ctx, payment_id)


def _bank(
    ctx: CompanyScenarioContext,
    txn_id: str,
    txn_date: str,
    amount_minor: int,
    *,
    counterparty: str,
    description: str,
    matched: bool = True,
    ledger_amount: int | None = None,
) -> None:
    if txn_id in ctx.bank_transactions:
        return
    ctx.bank_transactions[txn_id] = cash_bank(
        txn_id,
        txn_date,
        amount_minor,
        description=description,
        reference=txn_id,
        counterparty=counterparty,
        transaction_type="ach_credit" if amount_minor > 0 else "ach_debit",
        metadata={"plant": True},
    )
    _safe_named(ctx, txn_id)
    ledger_id = f"GL-{txn_id}"
    book = ledger_amount if ledger_amount is not None else amount_minor
    if ledger_id not in ctx.ledger_cash:
        ctx.ledger_cash[ledger_id] = cash_ledger(
            ledger_id,
            txn_date,
            book,
            counterparty=counterparty,
            reference=txn_id,
            description=description,
            entry_type="ar_receipt" if amount_minor > 0 else "ap_payment",
            metadata={"bank_id": txn_id},
        )
        _safe_named(ctx, ledger_id)
    ctx.recon_labels[txn_id] = {
        "match_type": "EXACT_MATCH" if matched else "UNMATCHED_BANK",
        "disposition": "MATCHED" if matched else "EXCEPTION_OPEN",
        "ledger_ids": [ledger_id] if matched else [],
    }


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
    vendor: str = "",
    customer: str = "",
    product: str = "",
    source: str = "",
    txn: str = "",
    category: str = "",
    entry_type: str = "operating",
    poster: str = "USR-JE-01",
    approver: str = "USR-JE-02",
    timestamp: str = "",
    posting_date: str = "",
    post_close: bool = False,
) -> None:
    if entry_id in ctx.journal_entries:
        return
    if amount_minor <= 0:
        return
    ctx.add_journal(
        JournalEntryRecord(
            entry_id=entry_id,
            period=period,
            effective_date=date,
            posting_date=posting_date or date,
            posting_timestamp=timestamp or f"{date}T12:00:00Z",
            debit_account=debit,
            credit_account=credit,
            amount_minor=amount_minor,
            memo=memo,
            vendor=vendor,
            customer=customer,
            product=product,
            category=category,
            source_document_id=source,
            transaction_id=txn or entry_id,
            entry_type=entry_type,
            poster_id=poster,
            approver_id=approver,
            post_close=post_close,
        )
    )


def _add_contract(
    ctx: CompanyScenarioContext,
    contract_id: str,
    vendor: str,
    start: str,
    *,
    monthly_minimum: float,
    description: str,
    extra: dict | None = None,
) -> None:
    from accrual.models import VendorContract

    if any(item.contract_id == contract_id for item in ctx.vendor_contracts):
        return
    kwargs = {
        "contract_id": contract_id,
        "vendor": vendor,
        "start_date": start,
        "end_date": "2027-12-31",
        "billing_cadence": "monthly",
        "description": description,
        "monthly_minimum": monthly_minimum,
        "amount": monthly_minimum,
    }
    item = VendorContract.model_validate(kwargs)
    if extra:
        for key, value in extra.items():
            if hasattr(item, key):
                setattr(item, key, value)
    ctx.vendor_contracts.append(item)
    _safe_named(ctx, contract_id)


def _recon_stub(reconciliation_id: str, period: str):
    from audit.models import PlantedReconciliation

    return PlantedReconciliation(
        reconciliation_id=reconciliation_id,
        period=period,
        recon_type="bank",
        original_match_type="EXACT_MATCH",
        original_status="MATCHED",
        bank_transaction_ids=[],
        ledger_entry_ids=[],
    )


def _month_end(period: str) -> str:
    year_i, month_i = (int(part) for part in period.split("-"))
    import calendar as cal

    return date(year_i, month_i, cal.monthrange(year_i, month_i)[1]).isoformat()


def _next_month(period: str) -> str:
    year_i, month_i = (int(part) for part in period.split("-"))
    if month_i == 12:
        return f"{year_i + 1}-01"
    return f"{year_i}-{month_i + 1:02d}"


def _add_days(iso: str, days: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=days)).isoformat()
