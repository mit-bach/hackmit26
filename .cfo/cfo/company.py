"""Canonical September 2026 company: inventory and shared identities.

Workflows already exist. This module names the one company they share
and the IDs that must survive AP → cash → close → reporting → audit.
"""

from __future__ import annotations

PERIOD = "2026-09"
AS_OF = "2026-09-30"
REPORTING_AS_OF = "2026-09-19"
COMPANY_ID = "CO-MAXIMOR"
COMPANY_NAME = "Maximor Demo Corp"
TRADE_NAME = "Maximor"
HEADQUARTERS = "Cambridge, MA"
CURRENCY = "USD"

# Existing operational fixtures already model this company. Do not invent
# a second set of amounts or IDs for the integration demo.
WORKFLOW_INVENTORY = {
    "ap": [
        "invoice ingestion",
        "duplicate detection",
        "three-way matching",
        "approval routing",
        "payment scheduling",
    ],
    "ar": ["aging", "collections", "cash application"],
    "cash": [
        "bank reconciliation",
        "grouped invoice payments",
        "bank fees",
        "refunds",
        "unexplained differences",
        "Stripe reconciliation",
        "Adyen settlement",
    ],
    "close": [
        "accruals",
        "prepaids",
        "fixed-asset depreciation",
        "balance-sheet reconciliation",
        "close gating",
        "post-close protection",
        "prior-period accrual methodology",
    ],
    "reporting": [
        "actuals",
        "variance analysis",
        "board reporting",
        "13-week cash forecast",
        "forecast-vs-actual explanation",
    ],
    "audit": [
        "sampling",
        "control testing",
        "duplicate controls",
        "round-number payments",
        "self-approval",
        "post-close entries",
        "independent re-performance",
        "findings",
        "corrections / recurring findings",
    ],
    "memory": [
        "August Stripe payout precedent",
        "Harbor Electric seasonal accrual methodology",
    ],
}

# Representative cases already planted in operational fixtures.
FEATURED = {
    "ap_matched": "INV-001",
    "ap_duplicate": "INV-018",
    "ap_duplicate_original": "INV-010",
    "ap_human_review": "INV-016",
    "ar_auto_apply": "PAY-001",
    "ar_ambiguous": "PAY-AMBIGUOUS",
    "cash_grouped_bank": "TXN-2026-09-008",
    "cash_grouped_invoices": ("INV-201", "INV-202", "INV-203"),
    "cash_fee_bank": "TXN-2026-09-011",
    "cash_refund_bank": "TXN-2026-09-012B",
    "cash_stripe_bank": "TXN-2026-09-019A",
    "cash_adyen_bank": "TXN-2026-09-019B",
    "cash_break_bank": "TXN-2026-09-015",
    "cash_correction_journal": "GL-CASH-CORR-1240",
    "close_unmatched_ar": "PAY-CLOSE-4500",
    "close_prepaid_gap": "PRE-INS-MISSING",
    "reporting_hosting_overage": "TXN-HOST-SEP-OVERAGE",
    "reporting_supplier": "TXN-SUP-SEP-001",
    "reporting_freight": "TXN-FRT-SEP-EXPEDITE",
    "harbor_vendor": "Harbor Electric",
    "harbor_method": "seasonal_prior_year",
    "harbor_september_amount": 4650.0,
    "harbor_august_amount": 7800.0,
}

INTENDED_SEPTEMBER = {
    "revenue": 1_000_000.0,
    "cogs": 390_000.0,
    "gross_profit": 610_000.0,
    "gross_margin_pct": 0.61,
}

INTENDED_AUGUST = {
    "revenue": 1_000_000.0,
    "cogs": 360_000.0,
    "gross_profit": 640_000.0,
    "gross_margin_pct": 0.64,
}

CHAIN_SPECS = (
    {
        "chain_id": "CHAIN-AP-CLEAN",
        "label": "Matched AP invoice through close and reporting",
        "invoice_id": "INV-001",
        "expected_ap": "APPROVE",
    },
    {
        "chain_id": "CHAIN-AP-DUP",
        "label": "Duplicate invoice held — never paid",
        "invoice_id": "INV-018",
        "duplicate_of": "INV-010",
        "expected_ap": "HOLD",
    },
    {
        "chain_id": "CHAIN-AP-REVIEW",
        "label": "Missing-PO invoice requires human review",
        "invoice_id": "INV-016",
        "expected_ap": "HOLD",
    },
    {
        "chain_id": "CHAIN-CASH-GROUPED",
        "label": "One wire covering three vendor invoices",
        "bank_transaction_id": "TXN-2026-09-008",
        "invoice_ids": ["INV-201", "INV-202", "INV-203"],
        "expected_match": "GROUPED_MATCH",
    },
    {
        "chain_id": "CHAIN-CASH-FEE",
        "label": "International wire net of bank fee",
        "bank_transaction_id": "TXN-2026-09-011",
        "expected_match": "FEE_NETTED",
    },
    {
        "chain_id": "CHAIN-CASH-BREAK",
        "label": "$12.40 unexplained difference blocks close",
        "bank_transaction_id": "TXN-2026-09-015",
        "expected_match": "UNEXPLAINED_DIFFERENCE",
        "expected_status": "HUMAN_REVIEW",
    },
    {
        "chain_id": "CHAIN-CASH-STRIPE",
        "label": "Stripe payout to operating account",
        "bank_transaction_id": "TXN-2026-09-019A",
        "expected_match": "PROVIDER_PAYOUT",
    },
    {
        "chain_id": "CHAIN-AR-APPLY",
        "label": "Customer remittance auto-applied",
        "payment_id": "PAY-001",
        "expected_ar": "AUTO_APPLY",
    },
    {
        "chain_id": "CHAIN-AR-REVIEW",
        "label": "Ambiguous remittance sent to human review",
        "payment_id": "PAY-AMBIGUOUS",
        "expected_ar": "HUMAN_REVIEW",
    },
    {
        "chain_id": "CHAIN-CLOSE-HARBOR",
        "label": "Harbor Electric September accrual cites August methodology",
        "vendor": "Harbor Electric",
        "expected_method": "seasonal_prior_year",
        "expected_amount": 4650.0,
    },
)


def money(value: float | None) -> float:
    return round(float(value or 0), 2)
