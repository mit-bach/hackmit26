"""Visualization, lineage, timeline, queries, and agent-case exports.

Operational finance files stay in the schemas existing loaders already consume.
These extra files are a frontend-friendly layer derived from the same records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from demo.inventory import build_system_capabilities
from demo.queries import build_demo_queries
from sample_data.context import CompanyScenarioContext, dollars


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def _tags(ctx: CompanyScenarioContext, record_id: str, *extra: str) -> list[str]:
    values = list(ctx.visualization_tags.get(record_id, []))
    values.extend(extra)
    return sorted(set(values))


def build_lineage(ctx: CompanyScenarioContext) -> list[dict]:
    stripe_ids = [item.payout_id for item in ctx.stripe_payouts]
    return [
        {
            "lineage_id": "LIN-INV-001",
            "kind": "ap_through_close",
            "record_id": "INV-001",
            "nodes": [
                {"role": "document", "id": "MSG-E-INV-001"},
                {"role": "ap_invoice", "id": "INV-001", "amount_cents": 1_245_000, "vendor": "Acme Supplies"},
                {"role": "purchase_order", "id": "PO-101"},
                {"role": "goods_receipt", "id": "GR-101"},
                {"role": "journal", "id": "JE-AP-INV-001"},
                {"role": "vendor_payment", "id": "PAY-AP-001"},
                {"role": "bank", "id": "TXN-2026-09-018A"},
                {"role": "close_evidence", "id": "TASK-AP"},
                {"role": "audit", "id": "INV-001"},
            ],
            "scenario_ids": ["SCN-AP-001", "SCN-CASH-001", "SCN-HAND-001"],
            "tags": _tags(ctx, "INV-001", "lineage"),
        },
        {
            "lineage_id": "LIN-INV-017",
            "kind": "ap_fee_netted_wire",
            "record_id": "INV-017",
            "nodes": [
                {"role": "ap_invoice", "id": "INV-017", "amount_cents": 1_000_000, "vendor": "Helios Hardware"},
                {"role": "journal", "id": "JE-AP-INV-017"},
                {"role": "vendor_payment", "id": "PAY-AP-017"},
                {"role": "bank", "id": "TXN-2026-09-011"},
                {"role": "fee_evidence", "id": "FEE-729103"},
            ],
            "scenario_ids": ["SCN-CASH-003", "SCN-HAND-001"],
            "tags": _tags(ctx, "INV-017", "lineage"),
        },
        {
            "lineage_id": "LIN-INV-AR-007",
            "kind": "ar_through_forecast",
            "record_id": "INV-AR-007",
            "nodes": [
                {"role": "ar_invoice", "id": "INV-AR-007", "amount_cents": 1_200_000, "customer": "Northwind Labs"},
                {"role": "payment", "id": "PAY-001"},
                {"role": "bank", "id": "TXN-AR-PAY-001"},
                {"role": "forecast", "id": "INV-AR-007"},
                {"role": "reporting", "id": "4000-Revenue"},
            ],
            "scenario_ids": ["SCN-AR-007", "SCN-HAND-002"],
            "tags": _tags(ctx, "INV-AR-007", "lineage"),
        },
        {
            "lineage_id": "LIN-INV-AR-013",
            "kind": "unexplained_cash_block",
            "record_id": "INV-AR-013",
            "nodes": [
                {"role": "ar_invoice", "id": "INV-AR-013", "amount_cents": 1_240_000},
                {"role": "payment", "id": "PAY-006", "amount_cents": 1_241_240},
                {"role": "bank", "id": "TXN-2026-09-015"},
                {"role": "ledger", "id": "GL-AR-NS"},
                {"role": "close_blocker", "id": "TASK-CASH"},
                {"role": "audit", "id": "REC-NS-1240"},
            ],
            "scenario_ids": ["SCN-CASH-005", "SCN-CLOSE-015", "SCN-CFO-001"],
            "tags": _tags(ctx, "INV-AR-013", "lineage"),
        },
        {
            "lineage_id": "LIN-STRIPE",
            "kind": "stripe_payout",
            "record_id": stripe_ids[0] if stripe_ids else "PAYOUT-001",
            "nodes": [{"role": "stripe_payout", "id": item} for item in stripe_ids],
            "scenario_ids": ["SCN-CASH-009", "SCN-CASH-010", "SCN-CASH-011", "SCN-MEM-003"],
            "tags": ["stripe", "cash", "cross_workflow"],
        },
        {
            "lineage_id": "LIN-DELL-ASSET",
            "kind": "capital_to_depreciation",
            "record_id": "INV-018",
            "nodes": [
                {"role": "ap_invoice", "id": "INV-018", "amount_cents": 6_000_000},
                {"role": "journal", "id": "JE-AP-INV-018"},
                {"role": "fixed_asset", "id": next((item.asset_id for item in ctx.fixed_assets), "FA-001")},
            ],
            "scenario_ids": ["SCN-CLOSE-005"],
            "tags": ["close", "ap", "cross_workflow"],
        },
    ]


def build_timeline(ctx: CompanyScenarioContext) -> list[dict]:
    events = [
        {"event_id": "EVT-001", "sequence": 1, "period": "2026-08", "event_type": "PERIOD_CLOSED", "agent": "Close Manager", "title": "August 2026 closed", "record_ids": ["CLOSE-2026-08"], "status": "CLOSED", "related_workflows": ["month_end_close"]},
        {"event_id": "EVT-002", "sequence": 2, "period": "2026-08", "event_type": "MEMORY", "agent": "AP Reviewer", "title": "Approved Acme vendor-alias precedent", "record_ids": ["CASE-001"], "status": "RECORDED", "related_workflows": ["ap"]},
        {"event_id": "EVT-003", "sequence": 3, "period": "2026-08", "event_type": "MEMORY", "agent": "Cash Application Reviewer", "title": "Corrected Meridian unlabeled ACH", "record_ids": ["AR-PREC-003", "PAY-005"], "status": "RECORDED", "related_workflows": ["ar"]},
        {"event_id": "EVT-010", "sequence": 10, "period": "2026-09", "event_type": "DOCUMENT", "agent": "Email Invoice Agent", "title": "Ingested clean Acme invoice", "record_ids": ["MSG-E-INV-001", "INV-001"], "amount_cents": 1_245_000, "status": "CLASSIFIED", "related_workflows": ["invoice_ingestion", "ap"]},
        {"event_id": "EVT-011", "sequence": 11, "period": "2026-09", "event_type": "AGENT_DECISION", "agent": "AP Preparer", "title": "Clean three-way match on INV-001", "record_ids": ["INV-001", "PO-101", "GR-101"], "amount_cents": 1_245_000, "status": "APPROVE", "related_workflows": ["ap"]},
        {"event_id": "EVT-012", "sequence": 12, "period": "2026-09", "event_type": "AGENT_DECISION", "agent": "Exception Investigator", "title": "Recognized Acme alias via CASE-001", "record_ids": ["INV-021", "CASE-001"], "amount_cents": 1_245_000, "status": "APPROVE", "related_workflows": ["ap", "memory"]},
        {"event_id": "EVT-020", "sequence": 20, "period": "2026-09", "event_type": "PAYMENT", "agent": "Payment Scheduler", "title": "Scheduled Acme and grouped Northline payments", "record_ids": ["PAY-AP-001", "INV-014", "INV-015", "INV-016"], "status": "PLANNED", "related_workflows": ["payment_scheduling", "cash"]},
        {"event_id": "EVT-030", "sequence": 30, "period": "2026-09", "event_type": "CASH_APPLICATION", "agent": "Cash Application Agent", "title": "Applied Northwind exact remittance", "record_ids": ["PAY-001", "INV-AR-007"], "amount_cents": 1_200_000, "status": "AUTO_APPLY", "related_workflows": ["ar"]},
        {"event_id": "EVT-031", "sequence": 31, "period": "2026-09", "event_type": "AGENT_DECISION", "agent": "Cash Application Agent", "title": "Escalated ambiguous Lumen remittance", "record_ids": ["PAY-004", "INV-AR-010", "INV-AR-011"], "amount_cents": 500_000, "status": "HUMAN_REVIEW", "related_workflows": ["ar"]},
        {"event_id": "EVT-040", "sequence": 40, "period": "2026-09", "event_type": "RECONCILIATION", "agent": "Cash Reconciliation Preparer", "title": "Matched one ACH to three Northline invoices", "record_ids": ["TXN-2026-09-008", "INV-014", "INV-015", "INV-016"], "status": "MATCHED", "related_workflows": ["cash_reconciliation"]},
        {"event_id": "EVT-041", "sequence": 41, "period": "2026-09", "event_type": "RECONCILIATION", "agent": "Cash Exception Investigator", "title": "Explained Helios wire net of $25 fee", "record_ids": ["TXN-2026-09-011", "INV-017"], "amount_cents": -1_002_500, "status": "EXPLAINED_EXCEPTION", "related_workflows": ["cash_reconciliation"]},
        {"event_id": "EVT-042", "sequence": 42, "period": "2026-09", "event_type": "AGENT_DECISION", "agent": "Cash Reconciliation Preparer", "title": "Detected unexplained cash difference", "record_ids": ["TXN-2026-09-015", "GL-AR-NS", "INV-AR-013"], "amount_cents": 1240, "status": "BLOCKED", "related_workflows": ["cash_reconciliation", "month_end_close"]},
        {"event_id": "EVT-050", "sequence": 50, "period": "2026-09", "event_type": "CLOSE", "agent": "Close Manager", "title": "September close blocked on $12.40", "record_ids": ["TASK-CASH", "TXN-2026-09-015"], "amount_cents": 1240, "status": "BLOCKED", "related_workflows": ["month_end_close"]},
        {"event_id": "EVT-051", "sequence": 51, "period": "2026-09", "event_type": "ACCRUAL", "agent": "Accrual Agent", "title": "Accrued Harbor Electric from prior methodology", "record_ids": ["ACC-HE-2026-09", "JE-ACC-HE-202609"], "amount_cents": 478_000, "status": "ACCRUED", "related_workflows": ["accrual", "close"]},
        {"event_id": "EVT-060", "sequence": 60, "period": "2026-09", "event_type": "REPORTING", "agent": "Variance Analysis Agent", "title": "Gross margin fell three points vs August", "record_ids": ["TXN-SUP-SEP-001", "TXN-HOST-SEP-001", "TXN-FRT-SEP-001"], "status": "EXPLAINED", "related_workflows": ["reporting"]},
        {"event_id": "EVT-061", "sequence": 61, "period": "2026-09", "event_type": "FORECAST", "agent": "Forecast Variance Agent", "title": "Cash forecast miss from late collection and unexpected items", "record_ids": ["INV-AR-014", "INV-012"], "status": "FORECAST_MISS", "related_workflows": ["forecasting"]},
        {"event_id": "EVT-070", "sequence": 70, "period": "2026-09", "event_type": "AUDIT", "agent": "Auditor Agent", "title": "Planted control exceptions independently rediscovered", "record_ids": ["VEND-001-DUP", "INV-006", "PAY-AP-009", "JE-POST-CLOSE-001", "APR-INV-SELF"], "status": "FINDING", "related_workflows": ["audit"]},
        {"event_id": "EVT-080", "sequence": 80, "period": "2026-10", "event_type": "ACCRUAL", "agent": "Accrual Agent", "title": "October Harbor Electric invoice arrives for September service", "record_ids": ["INV-HE-2026-09", "ACC-HE-2026-09"], "amount_cents": 478_000, "status": "REVERSAL_CANDIDATE", "related_workflows": ["accrual"]},
    ]
    return events


def build_agent_cases(ctx: CompanyScenarioContext) -> list[dict]:
    return [
        {"case_id": "AC-INBOX-SEND", "agent": "Counterparty Message Agent", "capability": "inbox.counterparty_to_ap", "input": {"message_id": "MSG-INBOX-001"}, "expected": {"sent": True, "wrote_ap": False}, "source_record_ids": ["MSG-INBOX-001"], "downstream_record_ids": [], "visualization_tags": ["happy_path", "ap", "inbox"]},
        {"case_id": "AC-INBOX-RECEIVE", "agent": "Finance Inbox Agent", "capability": "inbox.counterparty_to_ap", "input": {"message_id": "MSG-INBOX-001"}, "expected": {"classification": "VENDOR_INVOICE", "action": "CREATE_AP_INVOICE"}, "source_record_ids": ["MSG-INBOX-001"], "downstream_record_ids": ["INV-001"], "visualization_tags": ["happy_path", "ap", "inbox"]},
        {"case_id": "AC-EMAIL-CLEAN", "agent": "Email Invoice Agent", "capability": "ingestion.classify_document", "input": {"message_id": "MSG-E-INV-001"}, "expected": {"classification": "invoice", "invoice_number": "ACM-2026-4410"}, "source_record_ids": ["MSG-E-INV-001"], "downstream_record_ids": ["INV-001"], "visualization_tags": ["happy_path", "ap"]},
        {"case_id": "AC-EMAIL-QUOTE", "agent": "Email Invoice Agent", "capability": "ingestion.classify_document", "input": {"message_id": "MSG-E-QUOTE"}, "expected": {"classification": "quote"}, "source_record_ids": ["MSG-E-QUOTE"], "downstream_record_ids": [], "visualization_tags": ["exception", "ap"]},
        {"case_id": "AC-AP-PREPARER-CLEAN", "agent": "AP Preparer", "capability": "ap.three_way_match", "input": {"invoice_id": "INV-001"}, "expected": {"decision": "APPROVE", "exceptions": []}, "source_record_ids": ["INV-001", "PO-101", "GR-101"], "downstream_record_ids": ["PAY-AP-001"], "visualization_tags": ["happy_path", "ap"]},
        {"case_id": "AC-AP-INVESTIGATOR-ALIAS", "agent": "Exception Investigator", "capability": "memory.cross_period", "input": {"invoice_id": "INV-021"}, "expected": {"decision": "APPROVE", "exceptions": ["vendor_mismatch"], "precedent_id": "CASE-001"}, "source_record_ids": ["INV-021", "CASE-001"], "downstream_record_ids": ["JE-AP-INV-021"], "visualization_tags": ["memory", "ap"]},
        {"case_id": "AC-AP-DUP", "agent": "AP Reviewer", "capability": "ap.three_way_match", "input": {"invoice_id": "INV-006"}, "expected": {"decision": "HOLD", "exceptions": ["duplicate"]}, "source_record_ids": ["INV-006", "INV-007"], "downstream_record_ids": [], "visualization_tags": ["exception", "ap", "audit"]},
        {"case_id": "AC-SCHEDULER-DUE", "agent": "Payment Scheduler", "capability": "ap.payment_scheduling", "input": {"invoice_id": "INV-002", "as_of": "2026-09-19"}, "expected": {"eligible": True}, "source_record_ids": ["INV-002"], "downstream_record_ids": [], "visualization_tags": ["ap"]},
        {"case_id": "AC-COLLECTIONS", "agent": "Collections Agent", "capability": "ar.aging_collections", "input": {"invoice_id": "INV-AR-005", "as_of": "2026-09-30"}, "expected": {"aging_bucket": "90+", "action_not": "NO_ACTION"}, "source_record_ids": ["INV-AR-005", "CUST-005"], "downstream_record_ids": [], "visualization_tags": ["ar", "exception"]},
        {"case_id": "AC-CASH-APPLY-EXACT", "agent": "Cash Application Agent", "capability": "ar.cash_application", "input": {"payment_id": "PAY-001"}, "expected": {"decision": "AUTO_APPLY", "invoice_ids": ["INV-AR-007"]}, "source_record_ids": ["PAY-001", "INV-AR-007"], "downstream_record_ids": ["TXN-AR-PAY-001"], "visualization_tags": ["happy_path", "ar"]},
        {"case_id": "AC-CASH-APPLY-AMBIGUOUS", "agent": "Cash Application Reviewer", "capability": "ar.cash_application", "input": {"payment_id": "PAY-004"}, "expected": {"decision": "HUMAN_REVIEW"}, "source_record_ids": ["PAY-004", "INV-AR-010", "INV-AR-011"], "downstream_record_ids": [], "visualization_tags": ["exception", "ar"]},
        {"case_id": "AC-CASH-RECON-1240", "agent": "Cash Reconciliation Preparer", "capability": "cash.bank_reconciliation", "input": {"bank_id": "TXN-2026-09-015"}, "expected": {"status": "HUMAN_REVIEW", "difference_cents": 1240}, "source_record_ids": ["TXN-2026-09-015", "GL-AR-NS"], "downstream_record_ids": ["TASK-CASH"], "visualization_tags": ["cash", "close", "demo_highlight"]},
        {"case_id": "AC-CASH-RECON-GROUPED", "agent": "Cash Reconciliation Preparer", "capability": "cash.bank_reconciliation", "input": {"bank_id": "TXN-2026-09-008"}, "expected": {"match_type": "GROUPED_MATCH"}, "source_record_ids": ["TXN-2026-09-008", "INV-014", "INV-015", "INV-016"], "downstream_record_ids": [], "visualization_tags": ["cash", "ap"]},
        {"case_id": "AC-CASH-INVESTIGATOR", "agent": "Cash Exception Investigator", "capability": "cash.bank_reconciliation", "input": {"bank_id": "TXN-2026-09-015"}, "expected": {"status": "HUMAN_REVIEW", "invented_explanation": False}, "source_record_ids": ["TXN-2026-09-015"], "downstream_record_ids": ["TASK-CASH"], "visualization_tags": ["cash", "exception"]},
        {"case_id": "AC-CASH-REVIEWER", "agent": "Cash Reconciliation Reviewer", "capability": "cash.bank_reconciliation", "input": {"bank_id": "TXN-2026-09-011"}, "expected": {"match_type": "FEE_NETTED"}, "source_record_ids": ["TXN-2026-09-011", "FEE-729103"], "downstream_record_ids": [], "visualization_tags": ["cash", "exception"]},
        {"case_id": "AC-ACCRUAL", "agent": "Accrual Agent", "capability": "close.accruals", "input": {"vendor": "Harbor Electric", "period": "2026-09"}, "expected": {"needed": True, "accrual_id": "ACC-HE-2026-09"}, "source_record_ids": ["CTR-HE-001", "HI-HE-2026-08"], "downstream_record_ids": ["JE-ACC-HE-202609"], "visualization_tags": ["close", "memory"]},
        {"case_id": "AC-PREPAID", "agent": "Prepaid Preparer", "capability": "close.prepaids", "input": {"prepaid_id": "PRE-INS-001"}, "expected": {"treatment": "AMORTIZE"}, "source_record_ids": ["PRE-INS-001", "INV-019"], "downstream_record_ids": [], "visualization_tags": ["close"]},
        {"case_id": "AC-ASSET", "agent": "Fixed Asset Preparer", "capability": "close.fixed_assets", "input": {"source": "INV-018"}, "expected": {"treatment": "DEPRECIATE"}, "source_record_ids": ["INV-018"], "downstream_record_ids": [], "visualization_tags": ["close"]},
        {"case_id": "AC-BS-RECON", "agent": "Balance Sheet Reconciliation Preparer", "capability": "close.balance_sheet_recs", "input": {"period": "2026-09"}, "expected": {"cash_open": True}, "source_record_ids": ["TXN-2026-09-015"], "downstream_record_ids": ["TASK-BS"], "visualization_tags": ["close", "cash"]},
        {"case_id": "AC-CLOSE-REVIEW", "agent": "Month-End Close Reviewer", "capability": "close.month_end", "input": {"period": "2026-09"}, "expected": {"period_status": "BLOCKED", "blocker": "12.40"}, "source_record_ids": ["TXN-2026-09-015", "TASK-CASH"], "downstream_record_ids": ["CLOSE-2026-09"], "visualization_tags": ["close", "demo_highlight"]},
        {"case_id": "AC-CLOSE-MANAGER", "agent": "Close Manager", "capability": "close.month_end", "input": {"period": "2026-09"}, "expected": {"coordination": "deterministic_coordinate", "blocked": True}, "source_record_ids": ["TASK-CASH"], "downstream_record_ids": [], "visualization_tags": ["close"]},
        {"case_id": "AC-AUDITOR", "agent": "Auditor Agent", "capability": "audit.controls", "input": {"period": "2026-09", "seed": 42}, "expected": {"findings_include": ["VEND-001", "INV-006", "PAY-AP-009", "JE-POST-CLOSE-001", "APR-INV-SELF"]}, "source_record_ids": ["VEND-001-DUP", "INV-006", "PAY-AP-009"], "downstream_record_ids": [], "visualization_tags": ["audit"]},
        {"case_id": "AC-VARIANCE", "agent": "Variance Analysis Agent", "capability": "reporting.variance_board", "input": {"metric": "gross_margin_pct", "period": "2026-09"}, "expected": {"august": 0.64, "september": 0.61, "driver_ids": ["TXN-SUP-SEP-001", "TXN-HOST-SEP-001"]}, "source_record_ids": ["TXN-SUP-SEP-001", "TXN-HOST-SEP-001", "TXN-FRT-SEP-001"], "downstream_record_ids": [], "visualization_tags": ["forecast", "demo_highlight"]},
        {"case_id": "AC-FORECAST", "agent": "Cash Forecast Agent", "capability": "forecast.thirteen_week", "input": {"as_of": "2026-09-19", "weeks": 13}, "expected": {"week_count": 13}, "source_record_ids": ["INV-AR-014", "INV-012"], "downstream_record_ids": [], "visualization_tags": ["forecast"]},
        {"case_id": "AC-FORECAST-VAR", "agent": "Forecast Variance Agent", "capability": "forecast.thirteen_week", "input": {"period": "2026-09"}, "expected": {"miss_sources": ["INV-AR-014", "INV-012"]}, "source_record_ids": ["INV-AR-014", "INV-012"], "downstream_record_ids": [], "visualization_tags": ["forecast"]},
        {"case_id": "AC-BOARD", "agent": "Board Reporting Agent", "capability": "reporting.variance_board", "input": {"period": "2026-09"}, "expected": {"metrics_tie_to_gl": True}, "source_record_ids": ["4000-Revenue", "5200-Supplier"], "downstream_record_ids": [], "visualization_tags": ["forecast"]},
    ]


def build_expected_outcomes(ctx: CompanyScenarioContext) -> dict:
    return {
        "period": ctx.period,
        "seed": ctx.seed,
        "note": "Structured facts only. Operational agents must not load this file.",
        "scenarios": {
            item.scenario_id: {
                "expected_behavior": item.expected_behavior,
                "source_ids": item.source_ids,
                "severity": item.severity,
            }
            for item in ctx.scenarios.values()
        },
        "ap_exceptions": ctx.expected.ap_exceptions if ctx.expected else {},
        "reconciliation_statuses": ctx.expected.reconciliation_statuses if ctx.expected else {},
        "close_blockers": ctx.expected.close_blockers if ctx.expected else [],
        "gross_margin": {"2026-08": 0.64, "2026-09": 0.61, "drivers": ctx.expected.gross_margin_drivers if ctx.expected else []},
        "forecast_miss_drivers": ctx.expected.forecast_miss_drivers if ctx.expected else [],
        "audit_findings": [item.model_dump(mode="json") for item in (ctx.expected.audit_findings if ctx.expected else [])],
    }


def build_snapshot(ctx: CompanyScenarioContext, lineage: list[dict], timeline: list[dict], queries: list[dict]) -> dict:
    return {
        "company": ctx.company.model_dump(mode="json"),
        "calendar": ctx.calendar.model_dump(mode="json"),
        "highlights": [
            "INV-001 clean three-way match paid and bank-matched",
            "INV-017 Helios wire explained net of a $25 fee",
            "TXN-2026-09-015 unexplained $12.40 blocks September close",
            "INV-021 uses August CASE-001 vendor-alias precedent",
            "Gross margin 64% -> 61% from supplier/hosting/freight transactions",
        ],
        "counts": {
            "vendors": len(ctx.vendors),
            "customers": len(ctx.customers),
            "ap_invoices": len(ctx.ap_invoices),
            "ar_invoices": len(ctx.ar_invoices),
            "bank_transactions": len(ctx.bank_transactions),
            "journal_entries": len(ctx.journal_entries),
            "scenarios": len(ctx.scenarios),
        },
        "cash": {
            "opening_bank_cents": ctx.cash_opening_bank_minor,
            "unexplained_difference_cents": 1240,
        },
        "entities": {
            "vendors": list(ctx.vendors.values()),
            "customers": [item.model_dump(mode="json") for item in ctx.customers.values()],
            "ap_invoices": [
                {**item.model_dump(mode="json"), "tags": _tags(ctx, item.invoice_id)}
                for item in ctx.ap_invoices.values()
            ],
            "ar_invoices": [
                {**item.model_dump(mode="json"), "tags": _tags(ctx, item.invoice_id)}
                for item in ctx.ar_invoices.values()
            ],
            "exceptions": [
                {"id": "TXN-2026-09-015", "kind": "unexplained_difference", "amount_cents": 1240},
                {"id": "INV-006", "kind": "duplicate_invoice"},
                {"id": "PAY-004", "kind": "ambiguous_remittance"},
            ],
        },
        "relationships": lineage,
        "timeline": timeline,
        "memory_events": ctx.memory_events,
        "demo_queries": [item["query_id"] for item in queries],
        "opening_cash_forecast_dollars": dollars(ctx.opening_cash_forecast_minor),
    }


def write_demo_layer(ctx: CompanyScenarioContext, output: Path) -> list[str]:
    output = Path(output)
    written: list[str] = []
    lineage = build_lineage(ctx)
    timeline = build_timeline(ctx)
    queries = build_demo_queries()
    agent_cases = build_agent_cases(ctx)
    capabilities = build_system_capabilities()
    snapshot = build_snapshot(ctx, lineage, timeline, queries)

    artifacts = {
        "company.json": ctx.company.model_dump(mode="json"),
        "vendors.json": list(ctx.vendors.values()),
        "customers.json": [item.model_dump(mode="json") for item in ctx.customers.values()],
        "memory_events.json": ctx.memory_events,
        "lineage.json": lineage,
        "timeline.json": timeline,
        "demo_queries.json": queries,
        "agent_cases.json": agent_cases,
        "expected_outcomes.json": build_expected_outcomes(ctx),
        "system_capabilities.json": capabilities,
        "demo_snapshot.json": snapshot,
    }
    for rel, payload in artifacts.items():
        _dump(output / rel, payload)
        written.append(rel)
    return written
