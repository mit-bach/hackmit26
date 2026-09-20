"""Strict validation of a written demo pack, including visualization files."""

from __future__ import annotations

import json
from pathlib import Path

from sample_data.orchestrator import generate_sample_data
from sample_data.validators import SampleDataValidationError, validate_dataset


REQUIRED_EXPORTS = (
    "system_capabilities.json",
    "agent_cases.json",
    "lineage.json",
    "timeline.json",
    "demo_queries.json",
    "demo_snapshot.json",
    "memory_events.json",
    "expected_outcomes.json",
    "company.json",
    "vendors.json",
    "customers.json",
    "manifest.json",
    "invoices.json",
    "expected_results.json",
)


def validate_demo_pack(data_root: Path | str) -> list[str]:
    root = Path(data_root)
    errors: list[str] = []
    for name in REQUIRED_EXPORTS:
        if not (root / name).exists():
            errors.append(f"missing {name}")
    if errors:
        return errors

    manifest = json.loads((root / "manifest.json").read_text())
    ctx = generate_sample_data(seed=int(manifest["seed"]), period=manifest["period"], output=None)
    try:
        validate_dataset(ctx)
    except SampleDataValidationError as exc:
        errors.append(str(exc))

    known = (
        set(ctx.ap_invoices)
        | set(ctx.purchase_orders)
        | set(ctx.goods_receipts)
        | set(ctx.ar_invoices)
        | set(ctx.ar_payments)
        | set(ctx.vendor_payments)
        | set(ctx.bank_transactions)
        | set(ctx.journal_entries)
        | set(ctx.customers)
        | set(ctx.vendors)
        | {item.prepaid_id for item in ctx.prepaids}
        | {item.asset_id for item in ctx.fixed_assets}
        | {item.accrual_id for item in ctx.accruals}
        | {item.invoice_id for item in ctx.later_invoices}
        | {item.invoice_id for item in ctx.historical_invoices}
        | {item.contract_id for item in ctx.vendor_contracts}
        | {item.transaction_id for item in ctx.journal_entries.values() if item.transaction_id}
        | {item.approval_id for item in ctx.audit_approvals}
        | {item.task_id for item in ctx.close_tasks}
        | {item.precedent_id for item in ctx.ar_precedents}
        | {item.case_id for item in ctx.prior_cases}
        | {item.get("message_id") for item in ctx.ingestion_emails}
        | {item.payout_id for item in ctx.stripe_payouts}
        | set(ctx.fee_evidence)
        | {
            "CASE-001",
            "CLOSE-2026-08",
            "CLOSE-2026-09",
            "TASK-AP",
            "TASK-CASH",
            "TASK-BS",
            "REC-NS-1240",
            "4000-Revenue",
            "5200-Supplier",
            "GL-AR-NS",
            "HIST-ACME-4410",
        }
    )

    lineage = json.loads((root / "lineage.json").read_text())
    for row in lineage:
        for node in row.get("nodes") or []:
            node_id = node.get("id")
            if node_id and node_id not in known and not str(node_id).startswith("PAYOUT"):
                errors.append(f"lineage {row.get('lineage_id')} unknown node {node_id}")

    timeline = json.loads((root / "timeline.json").read_text())
    for event in timeline:
        for record_id in event.get("record_ids") or []:
            if record_id not in known and not str(record_id).startswith(("PAYOUT", "FA-", "EVT")):
                errors.append(f"timeline {event.get('event_id')} unknown record {record_id}")

    snapshot = json.loads((root / "demo_snapshot.json").read_text())
    if snapshot.get("company", {}).get("company_id") != "CO-MAXIMOR":
        errors.append("demo_snapshot company_id is not CO-MAXIMOR")

    capabilities = json.loads((root / "system_capabilities.json").read_text())
    if not capabilities.get("agents"):
        errors.append("system_capabilities missing agents")
    if not capabilities.get("skills"):
        errors.append("system_capabilities missing skills")

    cases = json.loads((root / "agent_cases.json").read_text())
    agents = {item["agent"] for item in capabilities.get("agents") or []}
    covered = {item["agent"] for item in cases}
    operational = {
        name
        for name in agents
        if "Sample Data" not in name
        and name
        not in {
            "ERP Invoice Agent",
            "EDI / Electronic Invoicing Agent",
            "Bank/Card Discovery Agent",
            "Procurement Invoice Agent",
            "Vendor Portal Agent",
            "Employee Submission Agent",
            "Physical Mail / Document Agent",
            "AP Approver",
            "AP Audit",
            "Payment Audit",
            "Prepaid Reviewer",
            "Fixed Asset Reviewer",
            "Balance Sheet Reconciliation Reviewer",
            "Reporting Reviewer Agent",
            "Forecast Reviewer Agent",
            "Audit Report Agent",
        }
    }
    missing_agents = sorted(operational - covered)
    if missing_agents:
        errors.append(f"agent_cases missing operational agents: {missing_agents}")

    expected = json.loads((root / "expected_outcomes.json").read_text())
    if "SCN-CASH-005" not in expected.get("scenarios", {}):
        errors.append("expected_outcomes missing SCN-CASH-005")
    return errors
