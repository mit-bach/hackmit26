"""Canonical P&L facts for the shared sample company.

Board P&L is the $372.4M run-rate table. The named COGS facts remain the
loud 64% → 61% mix-shift decoy (quantity × rate). Additional GL lines carry
the rest of August $30.82M / September $31.14M revenue.
Operational AP invoices (INV-001, INV-002, …) stay on operating expense.
"""

from __future__ import annotations

from typing import NamedTuple

from sample_data.context import cents, dollars


COGS_ACCOUNTS = frozenset(
    {"5100-Hosting", "5200-Supplier", "5300-Freight", "5400-Other-COGS", "5000-COGS"}
)
REVENUE_ACCOUNTS = frozenset({"4000-Revenue"})

# Operational AP invoices that must never be reused as P&L COGS source documents.
OPERATIONAL_AP_IDS = frozenset(
    {
        "INV-001",
        "INV-002",
        "INV-003",
        "INV-004",
        "INV-005",
        "INV-006",
        "INV-007",
        "INV-008",
        "INV-009",
        "INV-010",
        "INV-011",
        "INV-012",
        "INV-013",
        "INV-014",
        "INV-015",
        "INV-016",
        "INV-017",
        "INV-018",
        "INV-019",
        "INV-020",
    }
)

# Loud decoy slice (quantity × rate on named hosting/supplier/freight IDs).
DECOY_COGS_MINOR = {"2026-08": 36_000_000, "2026-09": 39_000_000}

# Catalog scale table. 36% / 39% COGS → GM 64% → 61% on the full books.
INTENDED_REVENUE_MINOR = {"2026-08": 3_082_000_000, "2026-09": 3_114_000_000}
INTENDED_COGS_MINOR = {"2026-08": 1_109_520_000, "2026-09": 1_214_460_000}

ANNUAL_REVENUE_RUN_RATE = 372_400_000.00
AUGUST_REVENUE = 30_820_000.00
SEPTEMBER_REVENUE = 31_140_000.00
W2_HEADCOUNT = 2_840
CONTRACTOR_1099_COUNT = 412
BIWEEKLY_PAYROLL_GROSS = 8_437_291.44
AP_OPEN = 18_420_000.00
AR_OPEN = 41_260_000.00
OPERATING_CASH_2026_09_30 = 14_882_410.18
ACTIVE_VENDORS = 340
AP_INVOICES_TRAILING = 4_800
BANK_LINES_PER_MONTH = 210


class CogsFact(NamedTuple):
    invoice_id: str
    vendor: str
    transaction_id: str
    amount_minor: int
    account: str
    category: str
    quantity: float | None
    rate: float | None
    memo: str
    period: str
    date: str


COGS_FACTS: tuple[CogsFact, ...] = (
    CogsFact("INV-HOST-AUG-001", "Amazon Web Services", "TXN-HOST-AUG-001", 5_000_000, "5100-Hosting", "hosting", 5000.0, 10.0, "AWS August compute", "2026-08", "2026-08-31"),
    CogsFact("INV-HOST-AUG-002", "Google Cloud", "TXN-HOST-AUG-002", 3_000_000, "5100-Hosting", "hosting", 3000.0, 10.0, "GCP August compute", "2026-08", "2026-08-31"),
    CogsFact("INV-SUP-AUG-001", "Acme Supplies", "TXN-SUP-AUG-001", 18_000_000, "5200-Supplier", "supplier", 1800.0, 100.0, "Acme components", "2026-08", "2026-08-31"),
    CogsFact("INV-SUP-AUG-002", "Helios Hardware", "TXN-SUP-AUG-002", 7_000_000, "5200-Supplier", "supplier", 700.0, 100.0, "Helios hardware", "2026-08", "2026-08-31"),
    CogsFact("INV-FRT-AUG-001", "Freightline Logistics", "TXN-FRT-AUG-001", 2_000_000, "5300-Freight", "freight", 200.0, 100.0, "Standard inbound freight", "2026-08", "2026-08-31"),
    CogsFact("INV-MSC-AUG-001", "Misc Supplies", "TXN-COGS-AUG-MSC", 1_000_000, "5400-Other-COGS", "unclassified", None, None, "Unclassified August COGS", "2026-08", "2026-08-31"),
    CogsFact("INV-HOST-SEP-001", "Amazon Web Services", "TXN-HOST-SEP-001", 5_000_000, "5100-Hosting", "hosting", 5000.0, 10.0, "AWS September compute", "2026-09", "2026-09-30"),
    CogsFact("INV-HOST-SEP-002", "Google Cloud", "TXN-HOST-SEP-002", 3_000_000, "5100-Hosting", "hosting", 3000.0, 10.0, "GCP September compute", "2026-09", "2026-09-30"),
    CogsFact("INV-HOST-SEP-003", "Amazon Web Services", "TXN-HOST-SEP-OVERAGE", 1_500_000, "5100-Hosting", "hosting", 1500.0, 10.0, "AWS unplanned hosting overage", "2026-09", "2026-09-30"),
    CogsFact("INV-SUP-SEP-001", "Acme Supplies", "TXN-SUP-SEP-001", 18_720_000, "5200-Supplier", "supplier", 1800.0, 104.0, "Acme components at the new contract rate", "2026-09", "2026-09-30"),
    CogsFact("INV-SUP-SEP-002", "Helios Hardware", "TXN-SUP-SEP-002", 7_280_000, "5200-Supplier", "supplier", 700.0, 104.0, "Helios hardware at the new contract rate", "2026-09", "2026-09-30"),
    CogsFact("INV-FRT-SEP-001", "Freightline Logistics", "TXN-FRT-SEP-001", 2_000_000, "5300-Freight", "freight", 200.0, 100.0, "Standard inbound freight", "2026-09", "2026-09-30"),
    CogsFact("INV-FRT-SEP-002", "Freightline Logistics", "TXN-FRT-SEP-EXPEDITE", 400_000, "5300-Freight", "freight", 40.0, 100.0, "Expedited freight on late materials", "2026-09", "2026-09-30"),
    CogsFact("INV-MSC-SEP-001", "Misc Supplies", "TXN-COGS-SEP-RESIDUAL", 1_100_000, "5400-Other-COGS", "unclassified", None, None, "Unclassified September COGS", "2026-09", "2026-09-30"),
)


def line_amount_dollars(fact: CogsFact) -> float:
    return dollars(fact.amount_minor)


def quantity_rate_amount(quantity: float | None, rate: float | None) -> float | None:
    if quantity is None or rate is None:
        return None
    return round(float(quantity) * float(rate), 2)


def cogs_facts_for(period: str) -> tuple[CogsFact, ...]:
    return tuple(item for item in COGS_FACTS if item.period == period)


def intended_cogs_minor(period: str) -> int:
    return sum(item.amount_minor for item in cogs_facts_for(period))


def cogs_invoice_ids() -> frozenset[str]:
    return frozenset(item.invoice_id for item in COGS_FACTS)


def cogs_transaction_ids() -> frozenset[str]:
    return frozenset(item.transaction_id for item in COGS_FACTS)


def validate_fact_arithmetic() -> list[str]:
    errors = []
    for fact in COGS_FACTS:
        computed = quantity_rate_amount(fact.quantity, fact.rate)
        if computed is not None and cents(computed) != fact.amount_minor:
            errors.append(
                f"{fact.transaction_id}: quantity {fact.quantity} × rate {fact.rate} "
                f"= {computed} != {line_amount_dollars(fact)}"
            )
        if fact.invoice_id in OPERATIONAL_AP_IDS:
            errors.append(f"{fact.transaction_id} reuses operational AP id {fact.invoice_id}")
    for period, expected in DECOY_COGS_MINOR.items():
        actual = intended_cogs_minor(period)
        if actual != expected:
            errors.append(f"{period} decoy COGS facts sum {actual} != {expected}")
    return errors
