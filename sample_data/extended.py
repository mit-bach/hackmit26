"""Plant derived demo scenarios that reuse already-created records.

These stories do not invent a second company. They attach memory, handoff,
and CFO orchestration labels to identities the domain agents already wrote.
"""

from __future__ import annotations

from sample_data.context import CompanyScenarioContext


def plant_extended_scenarios(ctx: CompanyScenarioContext) -> None:
    ctx.plant(
        "SCN-MEM-001",
        ["CASE-001", "INV-021", "VEND-001", "VEND-001-ALIAS"],
        storyline="STORY-CLEAN",
        notes="August CASE-001 makes the September Acme alias retrievable.",
    )
    ctx.plant(
        "SCN-MEM-002",
        ["AR-PREC-001", "AR-PREC-004", "CUST-007", "PAY-003", "INV-AR-008", "INV-AR-009"],
        notes="Atlas batch-payment precedent is live AR memory.",
    )
    stripe_ids = [item.payout_id for item in ctx.stripe_payouts]
    ctx.plant(
        "SCN-MEM-003",
        stripe_ids or ["PAYOUT-001"],
        notes="Stripe settlement math is the same payout identity used by cash recon.",
    )
    ctx.plant(
        "SCN-MEM-004",
        ["ACC-HE-2026-09", "CTR-HE-001", "HI-HE-2026-08", "JE-ACC-HE-202609"],
        notes="Harbor Electric accrual reuses the prior-period evidence set.",
    )
    ctx.plant(
        "SCN-LEARN-001",
        ["AR-PREC-003", "PAY-005", "PAY-008", "INV-AR-012", "INV-AR-016"],
        notes="Human correction is persisted; later Meridian remittance can retrieve it.",
    )
    ctx.plant(
        "SCN-HAND-001",
        ["INV-001", "PO-101", "GR-101", "JE-AP-INV-001", "PAY-AP-001", "TXN-2026-09-018A"],
        storyline="STORY-CLEAN",
    )
    ctx.plant(
        "SCN-HAND-002",
        ["INV-AR-007", "PAY-001", "TXN-AR-PAY-001", "CUST-001"],
        storyline="STORY-CLEAN",
    )
    ctx.plant(
        "SCN-CFO-001",
        ["TXN-2026-09-015", "TASK-CASH", "CLOSE-2026-09"],
        storyline="STORY-UNRESOLVED",
        notes="September close remains BLOCKED on the $12.40 cash difference.",
    )
    ctx.plant(
        "SCN-CFO-002",
        ["INV-AR-014", "INV-012", "TXN-2026-09-015"],
        notes="Forecast miss is explained from actual records, not a hardcoded narrative.",
    )
    _seed_memory_events(ctx)
    _seed_tags(ctx)


def _seed_memory_events(ctx: CompanyScenarioContext) -> None:
    ctx.memory_events = [
        {
            "event_id": "MEM-001",
            "period": "2026-08",
            "kind": "ap_precedent",
            "title": "Acme Supply Co. confirmed as Acme Supplies",
            "record_ids": ["CASE-001", "HIST-ACME-4410"],
            "retrievable_via": ["get_prior_cases", "vendor_alias_established"],
            "used_by_september": ["INV-021"],
            "agent": "AP Reviewer",
        },
        {
            "event_id": "MEM-002",
            "period": "2026-08",
            "kind": "ar_precedent",
            "title": "Atlas pays multiple invoices in one wire",
            "record_ids": ["AR-PREC-001", "AR-PREC-004", "CUST-007"],
            "retrievable_via": ["get_ar_precedents"],
            "used_by_september": ["PAY-003"],
            "agent": "Cash Application Agent",
        },
        {
            "event_id": "MEM-003",
            "period": "2026-08",
            "kind": "stripe_pattern",
            "title": "Stripe payout nets charges, fees, refunds, and disputes",
            "record_ids": [item.payout_id for item in ctx.stripe_payouts],
            "retrievable_via": ["cash_recon.providers", "integrations.cash.reconcile_payout"],
            "used_by_september": [item.payout_id for item in ctx.stripe_payouts],
            "agent": "Cash Reconciliation Preparer",
        },
        {
            "event_id": "MEM-004",
            "period": "2026-08",
            "kind": "accrual_methodology",
            "title": "Harbor Electric accrued from contract plus recent average",
            "record_ids": ["CTR-HE-001", "HI-HE-2026-08", "ACC-HE-2026-09"],
            "retrievable_via": ["get_vendor_invoice_history", "get_vendor_contract"],
            "used_by_september": ["ACC-HE-2026-09"],
            "agent": "Accrual Agent",
        },
        {
            "event_id": "MEM-005",
            "period": "2026-08",
            "kind": "human_correction",
            "title": "Meridian unlabeled ACH applied to INV-AR-012",
            "record_ids": ["AR-PREC-003", "PAY-005", "INV-AR-012"],
            "retrievable_via": ["get_ar_precedents"],
            "used_by_september": ["PAY-008"],
            "agent": "Cash Application Reviewer",
        },
    ]


def _seed_tags(ctx: CompanyScenarioContext) -> None:
    tags = {
        "INV-001": ["happy_path", "ap", "cross_workflow", "demo_highlight"],
        "INV-017": ["exception", "ap", "cash", "demo_highlight"],
        "INV-021": ["memory", "ap", "demo_highlight"],
        "INV-006": ["exception", "ap", "audit"],
        "INV-009": ["exception", "ap", "audit"],
        "INV-010": ["exception", "ap", "audit"],
        "INV-AR-005": ["ar", "exception", "demo_highlight"],
        "INV-AR-007": ["happy_path", "ar", "cross_workflow"],
        "INV-AR-013": ["exception", "ar", "cash", "close", "demo_highlight"],
        "PAY-001": ["happy_path", "ar", "cash"],
        "PAY-003": ["ar", "memory", "cross_workflow"],
        "PAY-004": ["exception", "ar"],
        "PAY-007": ["exception", "ar"],
        "TXN-2026-09-015": ["exception", "cash", "close", "demo_highlight"],
        "TXN-2026-09-008": ["cash", "ap", "cross_workflow", "demo_highlight"],
        "TXN-2026-09-011": ["cash", "exception", "demo_highlight"],
        "JE-POST-CLOSE-001": ["audit", "close", "exception"],
        "ACC-HE-2026-09": ["close", "memory"],
        "PRE-INS-001": ["close"],
    }
    for payout in ctx.stripe_payouts:
        tags[payout.payout_id] = ["stripe", "cash", "cross_workflow"]
    ctx.visualization_tags = tags
