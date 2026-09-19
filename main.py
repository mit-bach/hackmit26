#!/usr/bin/env python3
"""Run the autonomous Office-of-the-CFO workflows.

Usage:
    python main.py INV-001
    python main.py schedule
    python main.py schedule --seed-demo
    python main.py accrue 2026-09
    python main.py ingest 2026-09
    python main.py skills
    python main.py skills --agent accrual
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
    print("       python main.py ingest [period] [--no-ap] [--llm] [--replay-check]")
    print("       python main.py skills [--agent NAME]")
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
    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "skills":
        return run_skills_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in {"accrue", "accrual"}:
        from accrue import main as accrue_main

        return accrue_main(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "schedule":
        return run_schedule_cli(sys.argv[2:])

    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() == "ingest":
        from invoice_ingestion.demo import run_demo

        return run_demo(sys.argv[2:])

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
