"""Demo scenario catalog. Planted answers stay hidden until a workflow runs."""

from __future__ import annotations

from demo_web import workflows
from demo_web import artifacts

SCENARIOS = [
    {
        "id": "messy-invoice",
        "title": "Messy Invoice",
        "setup": "A poorly scanned Northline invoice lands in the AP inbox.",
        "workflows": ["ingestion", "ap"],
        "bots": ["email", "ap"],
        "record_ids": ["MSG-E-MESSY"],
        "href": "/inbox",
    },
    {
        "id": "duplicate-invoice",
        "title": "Duplicate Invoice",
        "setup": "A second copy of a vendor invoice is presented for payment.",
        "workflows": ["ap"],
        "bots": ["ap", "ctl-pay"],
        "record_ids": ["INV-006"],
        "href": "/ap",
    },
    {
        "id": "three-way-match",
        "title": "Three-Way Match Exception",
        "setup": "An invoice does not agree with the purchase order or receipt.",
        "workflows": ["ap"],
        "bots": ["ap", "ctl-pay"],
        "record_ids": ["INV-003"],
        "href": "/ap",
    },
    {
        "id": "payment-decision",
        "title": "Autonomous Payment Decision",
        "setup": "The weekly pay-run chooses what to pay from the approved pool.",
        "workflows": ["schedule"],
        "bots": ["pay", "ctl-pay"],
        "record_ids": ["INV-002", "INV-012"],
        "href": "/ap",
    },
    {
        "id": "stripe-payout",
        "title": "Stripe Payout Reconciliation",
        "setup": "A Stripe payout includes charges, fees, refunds, and disputes.",
        "workflows": ["stripe"],
        "bots": ["stripe", "cash"],
        "record_ids": ["po_1MaximorFees", "po_1MaximorRefunds", "po_1MaximorDisputes"],
        "href": "/stripe",
    },
    {
        "id": "bank-exception",
        "title": "Bank Reconciliation Exception",
        "setup": "Operating-account activity includes grouped payments, fee-netted wires, and an unexplained difference.",
        "workflows": ["cash"],
        "bots": ["cash", "ctl-cash"],
        "record_ids": ["TXN-2026-09-015", "TXN-2026-09-008", "TXN-2026-09-011"],
        "href": "/cash",
    },
    {
        "id": "month-end-accrual",
        "title": "Month-End Accrual",
        "setup": "Harbor Electric service was consumed; the September invoice has not arrived.",
        "workflows": ["accrual"],
        "bots": ["close", "ctl-books"],
        "record_ids": ["Harbor Electric"],
        "href": "/close",
    },
    {
        "id": "cross-period-memory",
        "title": "Cross-Period Memory",
        "setup": "September work retrieves August methodology and can deviate when evidence changes.",
        "workflows": ["memory"],
        "bots": ["close", "cash"],
        "record_ids": ["MEM-004", "CASE-001"],
        "href": "/memory",
    },
    {
        "id": "audit-controls",
        "title": "Audit / Control Detection",
        "setup": "Independent assurance samples the books after operations have recorded them.",
        "workflows": ["audit"],
        "bots": ["audit"],
        "record_ids": [],
        "href": "/audit",
    },
    {
        "id": "forecast-miss",
        "title": "Forecast Miss Explanation",
        "setup": "Cash and gross margin moved. The system traces the variance to source transactions.",
        "workflows": ["forecast"],
        "bots": ["story"],
        "record_ids": ["INV-AR-014", "INV-012"],
        "href": "/forecast",
    },
    {
        "id": "cfo-cycle",
        "title": "Full CFO Cycle",
        "setup": "Run the connected September office: AP, AR, cash, close, reporting, audit, memory.",
        "workflows": ["cfo-cycle"],
        "bots": ["email", "ap", "pay", "apply", "cash", "close", "story", "audit"],
        "record_ids": ["INV-001", "TXN-2026-09-015"],
        "href": "/",
    },
    {
        "id": "document-trap",
        "title": "Planted Document Trap",
        "setup": "A voided invoice and a duplicate Harbor-style bill try to enter accounts payable.",
        "workflows": ["ingestion", "ap"],
        "bots": ["email", "ap", "ctl-pay"],
        "record_ids": ["INV-006"],
        "href": "/evaluations",
    },
    {
        "id": "self-correction",
        "title": "Later Evidence Corrects an Estimate",
        "setup": "August estimated Harbor Electric. October's actual bill arrives and the books are corrected.",
        "workflows": ["memory"],
        "bots": ["close", "ctl-books"],
        "record_ids": ["Harbor Electric"],
        "href": "/memory",
    },
    {
        "id": "stripe-to-books",
        "title": "Stripe Charges to the General Ledger",
        "setup": "Charges, refunds, fees, and chargebacks become one payout, one bank deposit, and one cash interpretation.",
        "workflows": ["stripe"],
        "bots": ["stripe", "cash", "close"],
        "record_ids": ["po_1MaximorFees"],
        "href": "/stripe",
    },
]


def catalog() -> list[dict]:
    rows = []
    for item in SCENARIOS:
        preview = artifacts.scenario_preview(item["id"])
        rows.append(
            {
                **item,
                "planted_issue": None,
                "challenge": preview.get("challenge"),
                "input_preview": preview.get("inputs") or [],
                "expected": None,
            }
        )
    return rows


def run_scenario(scenario_id: str) -> dict:
    dispatch = {
        "messy-invoice": lambda: workflows.run_logged(
            "ingest",
            lambda: workflows.ingest_sample("MSG-E-MESSY"),
            bots=["email", "ap"],
            record_ids=["MSG-E-MESSY"],
        ),
        "duplicate-invoice": lambda: workflows.run_logged(
            "ap",
            lambda: workflows.run_ap("INV-006"),
            bots=["ap", "ctl-pay"],
            record_ids=["INV-006"],
        ),
        "three-way-match": lambda: workflows.run_logged(
            "ap",
            lambda: workflows.run_ap("INV-003"),
            bots=["ap", "ctl-pay"],
            record_ids=["INV-003"],
        ),
        "payment-decision": lambda: workflows.run_logged(
            "schedule",
            workflows.run_schedule,
            bots=["pay", "ctl-pay"],
            record_ids=["INV-002", "INV-012"],
        ),
        "stripe-payout": lambda: workflows.run_logged(
            "stripe",
            workflows.run_stripe_recon,
            bots=["stripe", "cash"],
            record_ids=["po_1MaximorFees"],
        ),
        "bank-exception": lambda: workflows.run_logged(
            "cash",
            workflows.run_bank_recon,
            bots=["cash", "ctl-cash"],
            record_ids=["TXN-2026-09-015"],
        ),
        "month-end-accrual": lambda: workflows.run_logged(
            "accrual",
            workflows.run_accrual,
            bots=["close"],
            record_ids=["Harbor Electric"],
        ),
        "cross-period-memory": lambda: workflows.run_logged(
            "memory",
            lambda: workflows.run_memory("harbor"),
            bots=["close"],
            record_ids=["Harbor Electric"],
        ),
        "audit-controls": lambda: workflows.run_logged(
            "audit",
            workflows.run_audit,
            bots=["audit"],
        ),
        "forecast-miss": lambda: workflows.run_logged(
            "forecast",
            workflows.run_forecast,
            bots=["story"],
            record_ids=["INV-AR-014", "INV-012"],
        ),
        "cfo-cycle": lambda: workflows.run_logged(
            "cfo-cycle",
            workflows.run_cfo_cycle,
            bots=["ap", "apply", "cash", "close", "story", "audit"],
            record_ids=["INV-001", "TXN-2026-09-015"],
        ),
        "document-trap": lambda: workflows.run_logged(
            "ap",
            lambda: workflows.run_ap("INV-006"),
            bots=["email", "ap", "ctl-pay"],
            record_ids=["INV-006"],
        ),
        "self-correction": lambda: workflows.run_logged(
            "memory",
            lambda: workflows.run_memory("harbor-correct"),
            bots=["close", "ctl-books"],
            record_ids=["Harbor Electric"],
        ),
        "stripe-to-books": lambda: workflows.run_logged(
            "stripe",
            workflows.run_stripe_recon,
            bots=["stripe", "cash"],
            record_ids=["po_1MaximorFees"],
        ),
    }
    fn = dispatch.get(scenario_id)
    if fn is None:
        raise KeyError(scenario_id)
    card = next(item for item in SCENARIOS if item["id"] == scenario_id)
    result = fn()
    result["scenario"] = {**card, "challenge": artifacts.SCENARIO_CHALLENGES.get(scenario_id), "planted_issue": None}
    preview = artifacts.scenario_preview(scenario_id)
    inner = result.get("result") or {}
    io = inner.get("io") or {}
    if not io.get("inputs"):
        io["inputs"] = preview.get("inputs")
        inner["io"] = io
        result["result"] = inner
    record_ids = result.get("record_ids") or (inner.get("record_ids") if isinstance(inner, dict) else None) or card.get("record_ids") or []
    result["expected"] = artifacts.expected_for_records(record_ids)
    return result
