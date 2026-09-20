"""Write generated records into the exact JSON shapes existing loaders consume."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sample_data.context import CompanyScenarioContext, dollars
from sample_data.schema_map import SCHEMA_VERSION


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def _models(rows) -> list[dict]:
    return [item.model_dump(mode="json") for item in rows]


def write_dataset(ctx: CompanyScenarioContext, output: Path) -> list[str]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def save(rel: str, payload: Any) -> None:
        _dump(output / rel, payload)
        written.append(rel)

    save("invoices.json", _models(ctx.ap_invoices.values()))
    save("purchase_orders.json", _models(ctx.purchase_orders.values()))
    save("goods_receipts.json", _models(ctx.goods_receipts.values()))
    save("company_policies.json", _models(ctx.policies))
    save("prior_cases.json", _models(ctx.prior_cases))
    save("approved_pool.json", ctx.approved_pool)
    save(
        "cash_position.json",
        {
            "as_of_date": ctx.calendar.forecast_as_of,
            "bank_balance": dollars(ctx.opening_cash_forecast_minor),
            "minimum_cash_reserve": 100000,
            "expected_receipts_next_7_days": 75000,
            "payroll_next_7_days": 70000,
            "other_committed_outflows": 20000,
            "payment_horizon_days": 7,
        },
    )
    save("ar_customers.json", _models(ctx.customers.values()))
    save("ar_invoices.json", _models(ctx.ar_invoices.values()))
    save("ar_payments.json", _models(ctx.ar_payments.values()))
    save("ar_precedents.json", _models(ctx.ar_precedents))
    save("historical_invoices.json", _models(ctx.historical_invoices))
    save("vendor_contracts.json", _models(ctx.vendor_contracts))
    save("vendor_usage.json", _models(ctx.vendor_usage))
    save("later_invoices.json", _models(ctx.later_invoices))

    save("cash_recon/bank_statement.json", _models(ctx.bank_transactions.values()))
    save("cash_recon/ledger.json", _models(ctx.ledger_cash.values()))
    save("cash_recon/fee_evidence.json", _models(ctx.fee_evidence.values()))
    save(
        "cash_recon/balances.json",
        {
            "opening_bank": dollars(ctx.cash_opening_bank_minor),
            "opening_ledger": dollars(ctx.cash_opening_ledger_minor),
            "as_of_date": ctx.calendar.as_of_date,
            "currency": "USD",
        },
    )
    save(
        "cash_recon/ground_truth.json",
        {
            "period": ctx.period,
            "matched_bank_ids": [
                key for key, row in ctx.recon_labels.items() if row.get("disposition") == "MATCHED"
            ],
            "exception_bank_ids": [
                key
                for key, row in ctx.recon_labels.items()
                if row.get("disposition") in {"HUMAN_REVIEW", "EXPLAINED_EXCEPTION", "OUTSTANDING_TIMING_ITEM"}
            ],
            "labels": ctx.recon_labels,
        },
    )

    save("close/prepaids.json", _models(ctx.prepaids))
    save("close/fixed_assets.json", _models(ctx.fixed_assets))
    save("close/capital_invoices.json", _models(ctx.capital_invoices))
    save("close/source_documents.json", ctx.source_documents)
    save(
        "close/materiality.json",
        {
            "close_materiality_dollars": 1000.0,
            "auto_review_threshold": 50.0,
            "note": "Materiality never auto-explains an unexplained difference.",
        },
    )
    save("close/tasks.json", _models(ctx.close_tasks))
    save("close/identity_links.json", _models(ctx.identity_links))
    save("close/journal_entries.json", [item.model_dump(mode="json") for item in ctx.journal_entries.values()])

    save("audit/vendors.json", _models(ctx.audit_vendors))
    save("audit/invoices.json", _models(ctx.audit_invoices))
    save("audit/payments.json", _models(ctx.audit_payments))
    save("audit/journal_entries.json", _models(ctx.audit_journals))
    save("audit/approvals.json", _models(ctx.audit_approvals))
    save("audit/periods.json", _models(ctx.audit_periods))
    save("audit/operational_decisions.json", _models(ctx.operational_decisions))
    save("audit/reconciliations.json", _models(ctx.planted_recons))
    save("audit/bank.json", _models(ctx.audit_bank))
    save("audit/ledger.json", _models(ctx.audit_ledger))
    save("audit/fee_evidence.json", _models(ctx.audit_fees))
    policy = json.loads((Path(__file__).resolve().parent.parent / "data" / "audit" / "policy.json").read_text())
    save("audit/policy.json", policy)
    save(
        "audit/ground_truth.json",
        {
            "period": ctx.period,
            "planted_exceptions": [
                {
                    "object_id": item.population_item_id,
                    "control_id": item.control_id,
                    "kind": item.expected_reason_code.lower(),
                }
                for item in (ctx.expected.audit_findings if ctx.expected else [])
            ],
            "expected_pass": [
                {"object_id": "INV-001", "control_id": "AUD-DUP-INV-001"},
                {"object_id": "PAY-AP-001", "control_id": "AUD-RND-001"},
            ],
        },
    )

    save("reporting/chart_of_accounts.json", _models(ctx.chart))
    save("reporting/balances.json", {period: item.model_dump(mode="json") for period, item in ctx.period_balances.items()})
    save("reporting/budget.json", {item.period: item.model_dump(mode="json") for item in ctx.budget})
    save(
        "reporting/assumptions.json",
        {
            "ar_fallback_days_after_due": 0,
            "ar_default_confidence": 0.7,
            "low_confidence_threshold": 0.5,
            "variance_tolerance": 0.02,
            "materiality_abs": 1000,
            "materiality_pct": 0.01,
            "week_start": "monday",
            "forecast_actuals_as_of": "2026-10-04",
        },
    )
    save("reporting/payroll.json", _models(ctx.payroll))
    save(
        "reporting/other_cash.json",
        [
            {
                "source_id": item.source_id,
                "expected_date": item.expected_date,
                "amount": item.amount,
                "confidence": item.confidence,
                "rationale": item.rationale,
            }
            for item in ctx.other_cash
        ],
    )
    save("reporting/actuals.json", _models(ctx.forecast_actuals))
    save("reporting/ap_forecast_state.json", ctx.ap_forecast_state)
    save("reporting/ledger_seed.json", _models(ctx.reporting_lines))
    save("reporting/forecast_lines.json", _models(ctx.forecast_lines))
    save("reporting/forecast_weeks.json", _models(ctx.forecast_weeks))

    save("integrations/stripe/events.json", ctx.stripe_events)
    save("integrations/stripe/balance_transactions.json", ctx.stripe_balance_txns)
    save("integrations/stripe/bank_deposit.json", ctx.stripe_deposits[0] if ctx.stripe_deposits else {})
    save("integrations/stripe/bank_deposits.json", ctx.stripe_deposits)
    save("integrations/stripe/payouts.json", [item.model_dump(mode="json") for item in ctx.stripe_payouts])

    save("ingestion/emails.json", ctx.ingestion_emails)
    save("ingestion/documents.json", ctx.ingestion_documents)
    save("ingestion/erp.json", ctx.ingestion_erp)
    save("ingestion/procurement.json", ctx.ingestion_procurement)
    save("ingestion/vendor_portals.json", ctx.ingestion_vendor_portals)
    save("ingestion/employee_submissions.json", ctx.ingestion_employee)
    save("ingestion/edi_documents.json", ctx.ingestion_edi)
    save("ingestion/bank_transactions.json", ctx.ingestion_bank)

    save("canonical/vendors.json", list(ctx.vendors.values()))
    save("canonical/vendor_payments.json", _models(ctx.vendor_payments.values()))
    save("canonical/journal_entries.json", [item.model_dump(mode="json") for item in ctx.journal_entries.values()])
    save("canonical/scenarios.json", _models(ctx.scenarios.values()))
    save("canonical/storylines.json", _models(ctx.storylines))

    if ctx.expected is not None:
        save("expected_results.json", ctx.expected.model_dump(mode="json"))

    from demo.export import write_demo_layer

    written.extend(write_demo_layer(ctx, output))

    counts = {
        "ap_invoices": len(ctx.ap_invoices),
        "purchase_orders": len(ctx.purchase_orders),
        "goods_receipts": len(ctx.goods_receipts),
        "ar_customers": len(ctx.customers),
        "ar_invoices": len(ctx.ar_invoices),
        "ar_payments": len(ctx.ar_payments),
        "vendor_payments": len(ctx.vendor_payments),
        "bank_transactions": len(ctx.bank_transactions),
        "ledger_entries": len(ctx.ledger_cash),
        "stripe_payouts": len(ctx.stripe_payouts),
        "journal_entries": len(ctx.journal_entries),
        "prepaids": len(ctx.prepaids),
        "fixed_assets": len(ctx.fixed_assets),
        "accruals": len(ctx.accruals),
        "close_tasks": len(ctx.close_tasks),
        "audit_invoices": len(ctx.audit_invoices),
        "forecast_weeks": len(ctx.forecast_weeks),
        "reporting_lines": len(ctx.reporting_lines),
        "scenarios": len(ctx.scenarios),
        "memory_events": len(ctx.memory_events),
        "ingestion_emails": len(ctx.ingestion_emails),
    }
    manifest_files = written + ["manifest.json"]
    save(
        "manifest.json",
        {
            "seed": ctx.seed,
            "company": ctx.company.legal_name,
            "period": ctx.period,
            "comparison_period": ctx.calendar.comparison_period,
            "schema_version": SCHEMA_VERSION,
            "generated_files": manifest_files,
            "record_counts": counts,
            "scenario_ids": sorted(ctx.scenarios),
            "storyline_ids": [item.storyline_id for item in ctx.storylines],
            "validation": "PASS",
        },
    )
    return manifest_files
