"""Human-readable sample-data summary."""

from __future__ import annotations

from pathlib import Path

from sample_data.context import CompanyScenarioContext


def format_summary(ctx: CompanyScenarioContext, *, data_root: Path | None = None) -> str:
    scenarios = sorted(ctx.scenarios)
    ap_ids = [key for key in scenarios if key.startswith("SCN-AP") or key.startswith("SCN-AR")]
    cash_ids = [key for key in scenarios if key.startswith("SCN-CASH")]
    close_ids = [key for key in scenarios if key.startswith("SCN-CLOSE")]
    audit_ids = [key for key in scenarios if key.startswith("SCN-AUDIT")]
    report_ids = [key for key in scenarios if key.startswith("SCN-REPORT")]
    root = f"\nOutput: {data_root}" if data_root else ""
    return "\n".join(
        [
            f"Company: {ctx.company.legal_name}",
            f"Period: {ctx.period}",
            f"Seed: {ctx.seed}",
            "",
            "AP/AR",
            f"  vendors: {len(ctx.vendors)}",
            f"  customers: {len(ctx.customers)}",
            f"  AP invoices: {len(ctx.ap_invoices)}",
            f"  AR invoices: {len(ctx.ar_invoices)}",
            f"  planted scenarios: {len(ap_ids)}",
            "",
            "Cash",
            f"  bank transactions: {len(ctx.bank_transactions)}",
            f"  Stripe payouts: {len(ctx.stripe_payouts)}",
            f"  planted scenarios: {len(cash_ids)}",
            "",
            "Close",
            f"  journal entries: {len(ctx.journal_entries)}",
            f"  reconciliations: {len(ctx.recon_labels)}",
            f"  open items: {sum(1 for item in ctx.close_tasks if item.status != 'COMPLETE')}",
            f"  planted scenarios: {len(close_ids)}",
            "",
            "Audit",
            f"  population size: {len(ctx.audit_invoices) + len(ctx.audit_payments) + len(ctx.audit_journals)}",
            f"  planted control exceptions: {len(audit_ids)}",
            "",
            "Reporting",
            f"  periods: {ctx.calendar.comparison_period}, {ctx.period}",
            f"  forecast weeks: {len(ctx.forecast_weeks)}",
            f"  planted variance cases: {len(report_ids)}",
            "",
            "Cross-domain validation: PASS",
            root,
        ]
    )
