"""Run the canonical Maximor demo pack against the live finance workflows.

Never mutates ``data/demo``. Runtime state lands under ``runs/demo_eval``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from demo.reset import reset_demo_runtime
from demo.validate import REQUIRED_EXPORTS, validate_demo_pack
from evals.agent_cases import run_agent_cases
from evaluation.context import operational_dataset
from evaluation.runner import run_benchmark
from sample_data.orchestrator import generate_sample_data
from sample_data.validators import (
    SampleDataValidationError,
    validate_ap_to_gl,
    validate_ar_to_gl,
    validate_balanced_journal_entries,
    validate_bank_to_cash_events,
    validate_dataset,
    validate_reconciliation_math,
    validate_stripe_payout_math,
)
from tools import collect_case_evidence, exception_types_for, load_prior_cases, vendor_alias_established


REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "data" / "demo"


def _latest_payload(result, extra: dict) -> dict:
    overall = result.overall_metrics
    by_domain: dict[str, float] = {}
    for fn in result.function_results:
        by_domain[fn.domain] = fn.accuracy
    agent_pass = extra.get("pass_rate_by_agent") or {}
    return {
        "run_id": result.run_id,
        "data_root": result.data_root,
        "period": result.period,
        "seed": result.seed,
        "cases_passed": overall.cases_passed + extra.get("extra_passed", 0) + extra.get("agent_passed", 0),
        "cases_failed": overall.cases_failed + extra.get("extra_failed", 0) + extra.get("agent_failed", 0),
        "cases_error": overall.cases_error,
        "benchmark_passed": overall.cases_passed,
        "benchmark_failed": overall.cases_failed,
        "agent_cases_passed": extra.get("agent_passed", 0),
        "agent_cases_failed": extra.get("agent_failed", 0),
        "agent_cases_total": extra.get("agent_total", 0),
        "extra_cases_passed": extra.get("extra_passed", 0),
        "extra_cases_total": extra.get("extra_total", 0),
        "pass_rate": overall.overall_score,
        "pass_rate_by_domain": by_domain,
        "pass_rate_by_agent": agent_pass,
        "close_success_or_blocker_correct": extra.get("close_blocker_ok"),
        "memory_dependent_case_success": extra.get("memory_ok"),
        "handoff_success": extra.get("handoff_ok"),
        "ledger_tie_out": extra.get("ledger_ok"),
        "stripe_tie_out": extra.get("stripe_ok"),
        "cross_workflow_consistency": extra.get("lineage_ok"),
        "repeatability": extra.get("repeat_ok"),
        "reset_ok": extra.get("reset_ok"),
        "visualization_exports_ok": extra.get("exports_ok"),
        "post_close_controls": extra.get("post_close_ok"),
        "output_dir": result.output_dir,
        "extra_cases": extra.get("cases", []),
        "agent_cases": extra.get("agent_cases", []),
    }


def _integrity_checks(period: str) -> dict:
    cases = []
    ctx = generate_sample_data(seed=42, period=period, output=None)
    ledger_errors = validate_balanced_journal_entries(ctx)
    stripe_errors = validate_stripe_payout_math(ctx)
    consistency_errors = (
        validate_ap_to_gl(ctx)
        + validate_ar_to_gl(ctx)
        + validate_bank_to_cash_events(ctx)
        + validate_reconciliation_math(ctx)
    )
    dataset_errors: list[str] = []
    try:
        validate_dataset(ctx)
    except SampleDataValidationError as exc:
        dataset_errors = [str(exc)]

    pack_errors = validate_demo_pack(CANONICAL)
    left = generate_sample_data(seed=42, period=period, output=None)
    right = generate_sample_data(seed=42, period=period, output=None)
    repeat_ok = (
        sorted(left.scenarios) == sorted(right.scenarios)
        and left.journal_entries["JE-AP-INV-001"].amount_minor == right.journal_entries["JE-AP-INV-001"].amount_minor
        and left.bank_transactions["TXN-2026-09-015"].amount_minor == right.bank_transactions["TXN-2026-09-015"].amount_minor
        and [item.payout_id for item in left.stripe_payouts] == [item.payout_id for item in right.stripe_payouts]
    )

    dest_a = REPO / "runs" / "demo_eval" / "_reset_probe_a"
    dest_b = REPO / "runs" / "demo_eval" / "_reset_probe_b"
    reset_demo_runtime(dest_a, source=CANONICAL, include_answer_keys=False)
    first_hash = hashlib.sha256((dest_a / "invoices.json").read_bytes()).hexdigest()
    reset_demo_runtime(dest_b, source=CANONICAL, include_answer_keys=False)
    second_hash = hashlib.sha256((dest_b / "invoices.json").read_bytes()).hexdigest()
    canonical_invoices = hashlib.sha256((CANONICAL / "invoices.json").read_bytes()).hexdigest()
    reset_ok = first_hash == second_hash == canonical_invoices and not (dest_a / "expected_results.json").exists()

    missing_exports = [name for name in REQUIRED_EXPORTS if not (CANONICAL / name).exists()]
    exports_ok = missing_exports == [] and pack_errors == []

    cases.append({"case_id": "DEMO-LEDGER-TIE", "passed": ledger_errors == [], "actual": ledger_errors})
    cases.append({"case_id": "DEMO-STRIPE-TIE", "passed": stripe_errors == [], "actual": stripe_errors})
    cases.append(
        {
            "case_id": "DEMO-CROSS-WORKFLOW",
            "passed": consistency_errors == [] and dataset_errors == [],
            "actual": consistency_errors + dataset_errors,
        }
    )
    cases.append({"case_id": "DEMO-LINEAGE-EXPORT", "passed": pack_errors == [], "actual": pack_errors})
    cases.append({"case_id": "DEMO-REPEAT", "passed": repeat_ok, "actual": {"repeatable": repeat_ok}})
    cases.append({"case_id": "DEMO-RESET", "passed": reset_ok, "actual": {"reset_ok": reset_ok}})
    cases.append(
        {
            "case_id": "DEMO-EXPORTS",
            "passed": exports_ok,
            "actual": {"missing": missing_exports, "pack_errors": pack_errors},
        }
    )
    return {
        "cases": cases,
        "ledger_ok": ledger_errors == [],
        "stripe_ok": stripe_errors == [],
        "lineage_ok": consistency_errors == [] and pack_errors == [] and dataset_errors == [],
        "repeat_ok": repeat_ok,
        "reset_ok": reset_ok,
        "exports_ok": exports_ok,
    }


def _run_structured_demo_cases(period: str) -> dict:
    cases = []

    evidence = collect_case_evidence("INV-021")
    alias_ok = vendor_alias_established(evidence)
    cases.append(
        {
            "case_id": "DEMO-MEM-ALIAS",
            "passed": alias_ok and "vendor_mismatch" in evidence.exception_types,
            "expected": {"precedent": "CASE-001", "exception": "vendor_mismatch"},
            "actual": {"alias": alias_ok, "exceptions": evidence.exception_types},
        }
    )
    priors = {item.case_id for item in load_prior_cases()}
    cases.append(
        {
            "case_id": "DEMO-MEM-PRIOR",
            "passed": "CASE-001" in priors,
            "expected": "CASE-001",
            "actual": sorted(priors),
        }
    )

    from ar.store import precedents as store_precedents
    from ar.store import reset_state
    from ar.workflow import run_cash_apply

    reset_state()
    ids = {item.precedent_id for item in store_precedents("CUST-010")}
    cases.append(
        {
            "case_id": "DEMO-LEARN-PRECEDENT",
            "passed": "AR-PREC-003" in ids,
            "expected": "AR-PREC-003",
            "actual": sorted(ids),
        }
    )
    overpay = run_cash_apply("PAY-007", as_of="2026-09-30", live=False, persist=False)
    cases.append(
        {
            "case_id": "DEMO-AR-OVERPAY",
            "passed": overpay.final.decision == "HUMAN_REVIEW",
            "expected": "HUMAN_REVIEW",
            "actual": overpay.final.decision,
        }
    )

    from close.month_end import run_month_end

    state = run_month_end(period, live=False, reset=True, scenario="demo")
    blocked = state.period.status in {"BLOCKED", "IN_PROGRESS"} or bool(state.human_review_items)
    cases.append(
        {
            "case_id": "DEMO-CLOSE-BLOCKED",
            "passed": blocked,
            "expected": "BLOCKED",
            "actual": state.period.status,
        }
    )

    from audit.workflow import run_audit

    audit = run_audit(period, seed=42, use_agent=False, persist=False)
    found: set[str] = set()
    for finding in audit.findings:
        found.update(finding.affected_object_ids + finding.journal_entry_ids)
    post_close_ok = "JE-POST-CLOSE-001" in found
    cases.append(
        {
            "case_id": "DEMO-POST-CLOSE",
            "passed": post_close_ok,
            "expected": "JE-POST-CLOSE-001",
            "actual": sorted(item for item in found if "POST-CLOSE" in item or item == "JE-POST-CLOSE-001"),
        }
    )

    from close.orchestrator import decide_ap

    clean = decide_ap("INV-001", live=False, featured=set())
    cases.append(
        {
            "case_id": "DEMO-HANDOFF-AP",
            "passed": clean.decision == "APPROVE" and exception_types_for("INV-001") == [],
            "expected": "APPROVE",
            "actual": clean.decision,
        }
    )

    agent = run_agent_cases()
    cases.extend(agent["cases"])

    integrity = _integrity_checks(period)
    cases.extend(integrity["cases"])

    extra_ids = {item["case_id"] for item in integrity["cases"]} | {
        "DEMO-MEM-ALIAS",
        "DEMO-MEM-PRIOR",
        "DEMO-LEARN-PRECEDENT",
        "DEMO-AR-OVERPAY",
        "DEMO-CLOSE-BLOCKED",
        "DEMO-POST-CLOSE",
        "DEMO-HANDOFF-AP",
    }
    structured = [item for item in cases if item["case_id"] in extra_ids]
    passed = sum(1 for item in structured if item["passed"])
    return {
        "cases": cases,
        "agent_cases": agent["cases"],
        "memory_ok": all(item["passed"] for item in cases if item["case_id"].startswith("DEMO-MEM") or item["case_id"].startswith("DEMO-LEARN")),
        "close_blocker_ok": all(item["passed"] for item in cases if item["case_id"].startswith("DEMO-CLOSE")),
        "handoff_ok": all(item["passed"] for item in cases if "HANDOFF" in item["case_id"]),
        "ledger_ok": integrity["ledger_ok"],
        "stripe_ok": integrity["stripe_ok"],
        "lineage_ok": integrity["lineage_ok"],
        "repeat_ok": integrity["repeat_ok"],
        "reset_ok": integrity["reset_ok"],
        "exports_ok": integrity["exports_ok"],
        "post_close_ok": post_close_ok,
        "pass_rate_by_agent": agent["pass_rate_by_agent"],
        "agent_passed": agent["passed"],
        "agent_failed": agent["failed"],
        "agent_total": agent["total"],
        "extra_passed": passed,
        "extra_failed": len(structured) - passed,
        "extra_total": len(structured),
    }


def run_demo_company_eval(
    *,
    data_root_path: Path = CANONICAL,
    seed: int = 42,
    period: str = "2026-09",
    reset: bool = True,
    live: bool = False,
) -> dict:
    data_root_path = Path(data_root_path)
    errors = validate_demo_pack(data_root_path if (data_root_path / "manifest.json").exists() else CANONICAL)
    if errors:
        raise SystemExit("Demo pack validation failed:\n- " + "\n- ".join(errors))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = REPO / "runs" / "demo_eval" / f"DEMO-{period}-{seed}-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    runtime = dest / "runtime"
    if reset:
        reset_demo_runtime(runtime, source=CANONICAL, include_answer_keys=False)

    result = run_benchmark(
        data_root=data_root_path,
        seed=seed,
        period=period,
        output=dest / "benchmark",
        live=live,
    )
    with operational_dataset(data_root_path, dest / "extra_state"):
        extra = _run_structured_demo_cases(period)

    payload = _latest_payload(result, extra)
    payload["validation"] = "PASS"
    payload["canonical_data_root"] = str(CANONICAL)
    payload["runtime_copy"] = str(runtime) if reset else None
    (dest / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
    latest = REPO / "runs" / "demo_eval" / "latest.json"
    shutil.copy2(dest / "result.json", latest)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.demo_company")
    parser.add_argument("--data-root", default=str(CANONICAL))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--month", default="2026-09")
    parser.add_argument("--no-reset", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    payload = run_demo_company_eval(
        data_root_path=Path(args.data_root),
        seed=args.seed,
        period=args.month,
        reset=not args.no_reset,
        live=args.live,
    )
    summary = {
        k: payload[k]
        for k in (
            "run_id",
            "pass_rate",
            "cases_passed",
            "cases_failed",
            "agent_cases_passed",
            "agent_cases_failed",
            "close_success_or_blocker_correct",
            "memory_dependent_case_success",
            "ledger_tie_out",
            "cross_workflow_consistency",
        )
    }
    print(json.dumps(summary, indent=2))
    failed_agents = [item["case_id"] for item in payload.get("agent_cases") or [] if not item.get("passed")]
    if failed_agents:
        print("Failed agent cases:", ", ".join(failed_agents))
    print(f"\nWrote {payload['output_dir']}")
    print(f"Latest: {REPO / 'runs' / 'demo_eval' / 'latest.json'}")
    return 0 if payload.get("cases_error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
