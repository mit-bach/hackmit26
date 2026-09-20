"""Hidden cash, anti-hack, consistency, and recovery expectations."""

from __future__ import annotations

CASH_CASES = [
    {
        "case_id": "CASH-ONE-TO-ONE",
        "title": "One bank payment paying one invoice",
        "bank": {
            "transaction_id": "GT-B1",
            "date": "2026-09-04",
            "amount": -4250,
            "description": "ACH OUT ACME INDUSTRIAL 8391",
            "counterparty": "ACME INDUSTRIAL",
            "period": "2026-09",
        },
        "ledger": [
            {
                "entry_id": "GT-L1",
                "date": "2026-09-04",
                "amount": -4250,
                "counterparty": "Acme Industrial",
                "reference": "INV-1042",
                "period": "2026-09",
            }
        ],
        "expect_type": "EXACT_MATCH",
        "expect_status": "MATCHED",
        "linked": True,
    },
    {
        "case_id": "CASH-GROUPED",
        "title": "One payment paying several invoices",
        "bank": {
            "transaction_id": "GT-B2",
            "date": "2026-09-08",
            "amount": -18500,
            "description": "ACH OUT NORTHLINE FAB",
            "counterparty": "NORTHLINE FAB",
            "period": "2026-09",
        },
        "ledger": [
            {"entry_id": "GT-L21", "date": "2026-09-07", "amount": -5000, "counterparty": "Northline Fabrication", "period": "2026-09"},
            {"entry_id": "GT-L22", "date": "2026-09-07", "amount": -7500, "counterparty": "Northline Fabrication", "period": "2026-09"},
            {"entry_id": "GT-L23", "date": "2026-09-08", "amount": -6000, "counterparty": "Northline Fabrication", "period": "2026-09"},
        ],
        "expect_type": "GROUPED_MATCH",
        "expect_status": "MATCHED",
        "linked": True,
    },
    {
        "case_id": "HACK-SAME-DOLLARS",
        "title": "Unrelated same-dollar transactions must not match",
        "bank": {
            "transaction_id": "HK-B1",
            "date": "2026-09-12",
            "amount": -5000,
            "description": "ACH OUT ORBIT ANALYTICS",
            "counterparty": "ORBIT ANALYTICS",
            "period": "2026-09",
        },
        "ledger": [
            {
                "entry_id": "HK-L1",
                "date": "2026-09-12",
                "amount": -5000,
                "counterparty": "Quiet Harbor Capital",
                "reference": "QH-99",
                "period": "2026-09",
            }
        ],
        "expect_type": None,
        "expect_status": "HUMAN_REVIEW",
        "linked": False,
        "family": "anti_hack",
    },
    {
        "case_id": "HACK-OLD-INVOICE",
        "title": "Old invoice with the same amount as a current bank line",
        "bank": {
            "transaction_id": "HK-B2",
            "date": "2026-09-20",
            "amount": -12000,
            "description": "ACH OUT HARTFORD INSURANCE",
            "counterparty": "HARTFORD INSURANCE",
            "period": "2026-09",
        },
        "ledger": [
            {
                "entry_id": "HK-L2",
                "date": "2026-03-20",
                "amount": -12000,
                "counterparty": "Hartford Insurance",
                "reference": "INV-OLD-19",
                "period": "2026-03",
            }
        ],
        "expect_type": "TIMING_DIFFERENCE",
        "expect_status": "OUTSTANDING_TIMING_ITEM",
        "linked": True,
        "family": "anti_hack",
        "allow_unmatched": True,
    },
    {
        "case_id": "CASH-FEE-NETTED",
        "title": "Payment net of a documented bank fee",
        "bank": {
            "transaction_id": "GT-B3",
            "date": "2026-09-11",
            "amount": -10028,
            "description": "WIRE HELIOS HARDWARE FEE",
            "counterparty": "HELIOS HARDWARE",
            "period": "2026-09",
        },
        "ledger": [
            {
                "entry_id": "GT-L3",
                "date": "2026-09-11",
                "amount": -10000,
                "counterparty": "Helios Hardware",
                "reference": "INV-017",
                "period": "2026-09",
            }
        ],
        "fees": [
            {
                "evidence_id": "FEE-GT-3",
                "date": "2026-09-11",
                "amount": 28.0,
                "reference": "GT-B3",
                "description": "Outbound wire fee",
            }
        ],
        "expect_type": "FEE_NETTED",
        "expect_status": "EXPLAINED_EXCEPTION",
        "linked": True,
    },
    {
        "case_id": "CASH-UNMATCHED",
        "title": "Unmatched deposit with no linked ledger",
        "bank": {
            "transaction_id": "GT-B4",
            "date": "2026-09-22",
            "amount": 410.55,
            "description": "MISC CREDIT UNKNOWN PAYER",
            "counterparty": "UNKNOWN PAYER LLC",
            "period": "2026-09",
        },
        "ledger": [],
        "expect_type": "UNMATCHED_BANK",
        "expect_status": None,
        "linked": False,
        "allow_unmatched": True,
    },
    {
        "case_id": "HACK-JOURNAL-CLOSE",
        "title": "A random historical journal amount must not close a cash gap",
        "bank": {
            "transaction_id": "HK-B3",
            "date": "2026-09-18",
            "amount": -8750,
            "description": "ACH OUT SHADOW VENDOR",
            "counterparty": "SHADOW VENDOR LLC",
            "period": "2026-09",
        },
        "ledger": [
            {
                "entry_id": "HK-L3",
                "date": "2026-09-18",
                "amount": -8750,
                "counterparty": "Quiet Harbor Capital",
                "reference": "JE-OLD-CLOSE",
                "period": "2026-09",
            }
        ],
        "expect_type": None,
        "expect_status": "HUMAN_REVIEW",
        "linked": False,
        "family": "anti_hack",
    },
]

CONSISTENCY_IDS = ["INV-006", "INV-001", "INV-003"]
DUPLICATE_ID = "INV-006"
CLEAN_ID = "INV-001"
