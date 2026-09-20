#!/usr/bin/env python3
"""Run the autonomous Office-of-the-CFO workflows.

Usage:
    python main.py INV-001
    python main.py schedule
    python main.py schedule --seed-demo
    python main.py accrue 2026-09
    python main.py ingest 2026-09
    python main.py close-month --month 2026-09 --seed-demo
    python main.py close 2026-09
    python main.py demo-close
    python main.py skills
    python main.py skills --agent accrual
    python main.py ar-aging --as-of 2026-09-30
    python main.py ar-collections --as-of 2026-09-30
    python main.py ar-cash-apply PAY-001
    python main.py ar-review-list
    python main.py cash-forecast --as-of 2026-09-30 --weeks 13
    python main.py ar-demo
    python main.py ar-forecast-demo
    python main.py audit-demo
    python main.py audit-demo --adversarial
    python main.py month-end 2026-09
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from models import DecisionTrace, ScheduleTrace
from tools import DataFileError, load_invoice

load_dotenv(Path(__file__).resolve().parent / ".env")


def format_trace(trace: DecisionTrace) -> str:
    final = trace.final
    preparer_reason = trace.preparer.reasons[0] if trace.preparer.reasons else ""
    investigator_block = "Investigator:\n(skipped — straightforward case)"
    if trace.investigation:
        finding = (
            trace.investigation.findings[0]
            if trace.investigation.findings
            else trace.investigation.recommendation
        )
        investigator_block = (
            f"Investigator:\n{trace.investigation.recommendation}\n{finding}"
        )
    reviewer_reason = trace.reviewer.reasons[0] if trace.reviewer.reasons else ""
    approver_reason = trace.approver.reasons[0] if trace.approver.reasons else ""
    audit_line = "PASS" if trace.audit.passed else "FAIL"
    if trace.audit.findings:
        audit_line = f"{audit_line} — {trace.audit.findings[0]}"
    evidence = "\n".join(f"- {item}" for item in final.evidence_used) or "- (none)"
    reconsideration = (
        "\nReconsideration: yes\n" if final.reconsideration_performed else "\n"
    )
    skill_lines = []
    for item in trace.agents:
        names = ", ".join(skill.name for skill in item.skills) or "(none)"
        skill_lines.append(f"- {item.role}: {names}")
        skill_lines.extend(f"  ERROR: {error}" for error in item.load_errors)
    skills_block = ""
    if skill_lines:
        skills_block = "\n\nSkills\n" + "\n".join(skill_lines)
    return (
        f"Invoice: {final.invoice_id}\n"
        f"\n"
        f"Preparer:\n"
        f"{trace.preparer.recommendation}\n"
        f"{preparer_reason}\n"
        f"\n"
        f"{investigator_block}\n"
        f"\n"
        f"Reviewer:\n"
        f"{trace.reviewer.recommendation}\n"
        f"Confidence: {trace.reviewer.confidence:.2f}\n"
        f"{reviewer_reason}\n"
        f"\n"
        f"Approver:\n"
        f"{trace.approver.decision}\n"
        f"Confidence: {trace.approver.confidence:.2f}\n"
        f"{approver_reason}\n"
        f"\n"
        f"Audit:\n"
        f"{audit_line}"
        f"{reconsideration}"
        f"FINAL DECISION: {final.decision}\n"
        f"Confidence: {final.confidence:.2f}\n"
        f"\n"
        f"Evidence:\n"
        f"{evidence}"
        f"{skills_block}"
    )


def format_schedule(trace: ScheduleTrace) -> str:
    by_id = {item.invoice_id: item for item in trace.candidates}
    pay_lines = []
    for row in trace.plan.pay_this_week:
        item = by_id.get(row.invoice_id)
        vendor = item.vendor if item else ""
        tag = "discount" if row.capture_discount else "pay"
        pay_lines.append(f"- {row.invoice_id}  {vendor}  ${row.amount:,.2f}  [{tag}]  {row.reason}")
    defer_lines = []
    for row in trace.plan.defer:
        item = by_id.get(row.invoice_id)
        vendor = item.vendor if item else ""
        amount = f"${item.amount:,.2f}" if item else ""
        defer_lines.append(f"- {row.invoice_id}  {vendor}  {amount}  {row.reason}")
    metrics = trace.metrics
    audit_line = "PASS" if trace.audit.passed else "FAIL"
    if trace.audit.findings:
        audit_line = f"{audit_line} — {trace.audit.findings[0]}"
    text = (
        f"Payment plan as of {trace.as_of_date}\n"
        f"Spendable cash: ${trace.spendable_cash:,.2f}\n"
        f"\n"
        f"PAY THIS WEEK (${trace.plan.total_payout:,.2f})\n"
        f"{chr(10).join(pay_lines) or '- (none)'}\n"
        f"\n"
        f"DEFER\n"
        f"{chr(10).join(defer_lines) or '- (none)'}\n"
        f"\n"
        f"Cash after payments: ${trace.plan.cash_after_payments:,.2f}\n"
        f"Reserve OK: {'yes' if trace.plan.reserve_ok else 'NO'}\n"
        f"\n"
        f"Metrics\n"
        f"- On-time: {metrics.due_invoices_paid_on_time}/{metrics.invoices_due_this_horizon} "
        f"({metrics.on_time_percent}%)\n"
        f"- Discounts captured: ${metrics.discounts_captured:,.2f} / "
        f"${metrics.discounts_available:,.2f}\n"
        f"- Late fees avoided: ${metrics.late_fees_avoided:,.2f}\n"
        f"- Unnecessary early payments: {metrics.unnecessary_early_payments}\n"
        f"- Reserve violation: {'yes' if metrics.reserve_violation else 'no'}\n"
        f"- Cash retained: ${metrics.total_cash_retained:,.2f}\n"
        f"\n"
        f"Audit: {audit_line}"
    )
    if trace.agents:
        skill_lines = []
        for item in trace.agents:
            names = ", ".join(skill.name for skill in item.skills) or "(none)"
            skill_lines.append(f"- {item.role}: {names}")
            skill_lines.extend(f"  ERROR: {error}" for error in item.load_errors)
        text += "\n\nSkills\n" + "\n".join(skill_lines)
    return text


def _usage() -> int:
    print("Usage: python main.py INV-001")
    print("       python main.py schedule [--seed-demo]")
    print("       python main.py accrue 2026-09")
    print("       python main.py close [period] [--deterministic]")
    print("       python main.py close run --period 2026-09")
    print("       python main.py close status --period 2026-09")
    print("       python main.py close reviews --period 2026-09")
    print("       python main.py close finalize --period 2026-09")
    print("       python main.py demo-close [period]")
    print("       python main.py ingest [period] [--no-ap] [--llm] [--replay-check]")
    print("       python main.py integration-demo")
    print("       python main.py stripe-demo")
    print("       python main.py integrations status")
    print("       python main.py webhook-demo [stripe|adyen|gmail|outlook|xero]")
    print("       python main.py sync [coupa|netsuite|stripe]")
    print("       python main.py webhook-server")
    print("       python main.py skills [--agent NAME]")
    print("       python main.py ar-aging [--as-of 2026-09-30]")
    print("       python main.py ar-collections [--as-of 2026-09-30]")
    print("       python main.py ar-cash-apply PAY-001")
    print("       python main.py ar-review-list")
    print("       python main.py ar-review-show PAY-005")
    print("       python main.py ar-review-approve PAY-005")
    print("       python main.py ar-review-correct PAY-005 --apply INV-AR-101:10000 --reason TEXT")
    print("       python main.py ar-review-reject PAY-005 --reason TEXT")
    print("       python main.py ar-demo")
    print("       python main.py cash-forecast [--as-of 2026-09-30] [--weeks 13]")
    print("       python main.py ar-forecast-demo")
    print("       python main.py close-month --month 2026-09 --seed-demo")
    print("       python main.py eval-close --month 2026-09")
    print("       python main.py reconcile-cash --month 2026-09 --seed-demo")
    print("       python main.py reconcile-trace REC-001")
    print("       python main.py eval-cash-reconciliation")
    print("       python main.py memory-demo [--story stripe|prepaid|both]")
    print("       python main.py eval-memory")
    print("       python main.py month-end [period]")
    print("       python main.py close-month --month 2026-09 --seed-demo")
    print("       python main.py close-trace --month 2026-09")
    print("       python main.py eval-close --month 2026-09")
    print("       python main.py resolve-review REC-010 --resolution TEXT")
    print("       python main.py reopen-period --month 2026-09 --reason TEXT")
    print("       python main.py post-journal --date 2026-09-29 --debit X --credit Y --amount N")
    print("       python main.py account-recon-trace BSR-001")
    print("       python main.py audit [--period 2026-09] [--seed 26]")
    print("       python main.py audit-demo")
    print("       python main.py audit-demo --adversarial")
    print("       python main.py audit-trace")
    print("       python main.py eval-audit")
    print("       python main.py demo-reporting")
    print("       python main.py reporting [period] [as-of]")
    print("       python main.py generate-sample-data [--seed 42] [--month 2026-09] [--output data/demo]")
    print("       python main.py validate-sample-data [--data-root data/demo]")
    print("       python main.py sample-data-summary [--data-root data/demo]")
    print("       python main.py evaluate-cfo [--data-root data/demo] [--seed 42] [--all]")
    print("       python main.py cfo-demo")
    print("       python main.py generate-discrepancy-data [--seed 42] [--month 2026-09] [--output data/discrepancy_demo]")
    print("       python main.py generate-holdout-data [--seed 77] [--output data/discrepancy_holdout]")
    print("       python main.py evaluate-discrepancies [--data-root data/discrepancy_demo]")
    print("       python main.py final-eval [--live]")
    return 1


def _require_api_key(example: str) -> int | None:
    if os.environ.get("OPENAI_API_KEY"):
        return None
    print(
        "OPENAI_API_KEY is not set.\n"
        "Copy .env.example to .env and add your key, then rerun:\n"
        f"  {example}"
    )
    return 1


def run_schedule_cli(argv: list[str]) -> int:
    seed_demo = "--seed-demo" in argv
    from_traces = "--from-traces" in argv
    unknown = [item for item in argv if item not in {"--seed-demo", "--from-traces"}]
    if unknown:
        print(f"Unknown schedule option: {unknown[0]}")
        return _usage()

    from scheduling.pool import seed_demo_pool, seed_from_traces
    from scheduling.workflow import RUNS_DIR, run_schedule_workflow

    if seed_demo:
        added = seed_demo_pool()
        print(f"Seeded approved pool with {len(added)} policy-eligible invoices.")
    elif from_traces:
        added = seed_from_traces(RUNS_DIR)
        print(f"Loaded {len(added)} APPROVE traces into the approved pool.")

    missing = _require_api_key("python main.py schedule")
    if missing is not None:
        return missing

    try:
        trace = run_schedule_workflow()
    except ValueError as exc:
        print(str(exc))
        return 1
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1
    except Exception as exc:
        print(f"The payment scheduler failed: {exc}")
        return 1

    print(format_schedule(trace))
    if trace.trace_path:
        print(f"\nTrace saved to {trace.trace_path}")
    return 0


def run_close_cli(argv: list[str]) -> int:
    month_end_commands = {
        "run",
        "status",
        "reviews",
        "review",
        "resolve",
        "rerun",
        "finalize",
        "prepaid",
        "depreciate",
        "eval-live",
    }
    if argv and argv[0].strip().lower() in month_end_commands:
        from close.cli import run_month_end_cli

        return run_month_end_cli(argv)

    # Compatibility: `python main.py close 2026-09` is close-month.
    period = "2026-09"
    flags = []
    for item in argv:
        if item[:1].isdigit() and len(item) == 7:
            period = item
        else:
            flags.append(item)
    from close.cli import run_close_month_cli

    return run_close_month_cli(["--month", period, "--reset", *flags])


def run_demo_close_cli(argv: list[str]) -> int:
    period = "2026-09"
    rest = [item for item in argv if not item.startswith("--")]
    if rest:
        period = rest[0]
    try:
        from close.engine import run_month_end
        from close.report import format_month_end_demo

        state = run_month_end(period, scenario="demo", live=False, reset=True, allow_close=False)
        print(format_month_end_demo(state))
        return 0
    except Exception as exc:
        print(f"Month-end close demo failed: {exc}")
        return 1


def run_skills_cli(argv: list[str]) -> int:
    agent_query = None
    index = 0
    while index < len(argv):
        option = argv[index]
        if option in {"--agent", "-a"}:
            if index + 1 >= len(argv):
                print("Usage: python main.py skills --agent <name>")
                return 1
            agent_query = argv[index + 1]
            index += 2
            continue
        print(f"Unknown skills option: {option}")
        return _usage()
    try:
        from skills.validate import validate_skill_system

        validate_skill_system()
        if agent_query:
            from skills.inspect import format_agent_skills

            print(format_agent_skills(agent_query), end="")
        else:
            from skills.inspect import format_skills_index

            print(format_skills_index(), end="")
        return 0
    except KeyError as exc:
        print(exc)
        return 1
    except Exception as exc:
        print(f"Skill inspection failed: {exc}")
        return 1


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "generate-sample-data",
        "generate_sample_data",
    }:
        from sample_data.cli import run_generate

        return run_generate(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "validate-sample-data",
        "validate_sample_data",
    }:
        from sample_data.cli import run_validate

        return run_validate(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "sample-data-summary",
        "sample_data_summary",
    }:
        from sample_data.cli import run_summary

        return run_summary(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "evaluate-cfo",
        "evaluate_cfo",
    }:
        from evaluation.cli import run_evaluate

        return run_evaluate(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"cfo-demo", "cfo_demo"}:
        from cfo.cli import run_cfo_demo_cli

        return run_cfo_demo_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "generate-discrepancy-data",
        "generate_discrepancy_data",
    }:
        from discrepancy.cli import run_generate

        return run_generate(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "generate-holdout-data",
        "generate_holdout_data",
    }:
        from discrepancy.cli import run_generate_holdout

        return run_generate_holdout(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"final-eval", "final_eval"}:
        from final_eval.cli import run_final_eval

        return run_final_eval(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "evaluate-discrepancies",
        "evaluate_discrepancies",
    }:
        from discrepancy.cli import run_evaluate as run_discrepancy_eval

        return run_discrepancy_eval(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "skills":
        return run_skills_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-aging", "ar_aging"}:
        from ar.cli import run_aging_cli

        return run_aging_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-collections", "ar_collections"}:
        from ar.cli import run_collections_cli

        return run_collections_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-cash-apply", "ar_cash_apply"}:
        from ar.cli import run_cash_apply_cli

        return run_cash_apply_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-demo", "ar_demo"}:
        from ar.cli import run_demo_cli

        return run_demo_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-review-list", "ar_review_list"}:
        from ar.cli import run_review_list_cli

        return run_review_list_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-review-show", "ar_review_show"}:
        from ar.cli import run_review_show_cli

        return run_review_show_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-review-approve", "ar_review_approve"}:
        from ar.cli import run_review_approve_cli

        return run_review_approve_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-review-correct", "ar_review_correct"}:
        from ar.cli import run_review_correct_cli

        return run_review_correct_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-review-reject", "ar_review_reject"}:
        from ar.cli import run_review_reject_cli

        return run_review_reject_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"ar-forecast-demo", "ar_forecast_demo"}:
        from ar.cli import run_forecast_demo_cli

        return run_forecast_demo_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"cash-forecast", "cash_forecast"}:
        from reporting.cli import run_cash_forecast_cli

        return run_cash_forecast_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"reconcile-cash", "reconcile_cash", "cash-recon"}:
        from cash_recon.cli import run_reconcile_cash

        return run_reconcile_cash(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"reconcile-trace", "reconcile_trace", "cash-trace"}:
        from cash_recon.cli import run_reconcile_trace

        return run_reconcile_trace(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "eval-cash-reconciliation",
        "eval_cash_reconciliation",
        "eval-cash",
    }:
        from cash_recon.cli import run_eval_cash

        return run_eval_cash(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {
        "demo-reporting",
        "reporting-demo",
        "demo_reporting",
    }:
        from reporting.cli import run_demo_reporting

        return run_demo_reporting(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "reporting":
        from reporting.cli import run_reporting

        return run_reporting(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"audit-demo", "audit_demo"}:
        from audit.cli import run_audit_demo_cli

        return run_audit_demo_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"audit-trace", "audit_trace"}:
        from audit.cli import run_audit_trace_cli

        return run_audit_trace_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"eval-audit", "eval_audit"}:
        from audit.cli import run_eval_audit_cli

        return run_eval_audit_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "audit":
        from audit.cli import run_audit_cli

        return run_audit_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"accrue", "accrual"}:
        from accrue import main as accrue_main

        return accrue_main(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "schedule":
        return run_schedule_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"close-month", "close_month"}:
        from close.cli import run_close_month_cli

        return run_close_month_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"reopen-period", "reopen_period"}:
        from close.cli import run_reopen_period_cli

        return run_reopen_period_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"resolve-review", "resolve_review"}:
        from close.cli import run_resolve_review_cli

        return run_resolve_review_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"close-trace", "close_trace"}:
        from close.cli import run_close_trace_cli

        return run_close_trace_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"account-recon-trace", "account_recon_trace"}:
        from close.cli import run_account_recon_trace_cli

        return run_account_recon_trace_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"eval-close", "eval_close"}:
        from close.cli import run_eval_close_cli

        return run_eval_close_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"post-journal", "post_journal"}:
        from close.cli import run_post_journal_cli

        return run_post_journal_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"month-end", "month_end"}:
        from close.cli import run_month_end_cli

        args = sys.argv[2:]
        commands = {"run", "status", "reviews", "review", "resolve", "rerun", "finalize", "prepaid", "depreciate", "eval-live"}
        if not args or args[0] not in commands:
            period = "2026-09"
            flags = []
            for item in args:
                if item[:1].isdigit():
                    period = item
                else:
                    flags.append(item)
            args = ["run", "--period", period, "--reset", "--deterministic", *flags]
        return run_month_end_cli(args)

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "close":
        return run_close_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"demo-close", "close-demo"}:
        return run_demo_close_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "ingest":
        from invoice_ingestion.demo import run_demo

        return run_demo(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"integration-demo", "integrations-demo"}:
        from integrations.demo import run_integration_demo

        print(run_integration_demo(replay=True))
        return 0

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"stripe-demo", "stripe_demo"}:
        from integrations.cli import run_stripe_demo

        return run_stripe_demo()

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"memory-demo", "memory_demo"}:
        from memory.cli import run_memory_demo

        return run_memory_demo(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"eval-memory", "memory-eval", "eval_memory"}:
        from memory.cli import run_memory_eval

        return run_memory_eval(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "integrations":
        from integrations.cli import run_cli

        return run_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "webhook-demo":
        from integrations.cli import run_webhook_demo

        name = sys.argv[2].strip().lower() if len(sys.argv) >= 3 else "stripe"
        return run_webhook_demo(name)

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"sync", "stripe-sync"}:
        from integrations.cli import run_sync

        if sys.argv[1].strip().lower() == "stripe-sync":
            return run_sync("stripe", sys.argv[2:])
        name = sys.argv[2].strip().lower() if len(sys.argv) >= 3 else ""
        if not name:
            print("Usage: python main.py sync [coupa|netsuite|stripe]")
            return 1
        return run_sync(name, sys.argv[3:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"webhook-server", "webhooks"}:
        from integrations.cli import run_server

        return run_server()

    if len(sys.argv) != 2:
        return _usage()

    invoice_id = sys.argv[1].strip().upper()

    try:
        invoice = load_invoice(invoice_id)
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1

    if invoice is None:
        print(f"Unknown invoice ID: {invoice_id}")
        print("Check data/invoices.json for a valid ID such as INV-001.")
        return 1

    missing = _require_api_key("python main.py INV-001")
    if missing is not None:
        return missing

    try:
        from workflow import run_ap_workflow

        trace = run_ap_workflow(invoice_id)
    except DataFileError as exc:
        print(f"Could not read AP data files: {exc}")
        return 1
    except Exception as exc:
        print(f"The AP workflow failed: {exc}")
        return 1

    print(format_trace(trace))
    if trace.trace_path:
        print(f"\nTrace saved to {trace.trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
