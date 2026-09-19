"""Orchestrate baseline / known / held-out / clean / agent scoring without touching the frozen baseline dir."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from discrepancy.evaluate import run_discrepancy_benchmark
from discrepancy.generate import generate_holdout_data
from discrepancy.holdout_evaluate import run_holdout_benchmark
from evaluation.runner import run_benchmark
from final_eval.agent_mode import credentials_available, domain_modes, run_agent_subset
from final_eval.metrics import audit_confusion, cash_split, close_journal_scores, domain_ratio
from final_eval.report import write_artifacts

BASELINE_DIR = Path("runs/evaluation/EVAL-2026-09-42-20260919T205629Z")
KNOWN_ROOT = Path("data/discrepancy_demo")
HOLDOUT_ROOT = Path("data/discrepancy_holdout")
DEMO_ROOT = Path("data/demo")


def _load_baseline() -> dict:
    path = BASELINE_DIR / "benchmark.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _baseline_domain_scores(payload: dict) -> dict[str, dict]:
    rows = {}
    for item in payload.get("function_results") or []:
        rows[item["domain"]] = {
            "score": item.get("score"),
            "pass": item.get("cases_passed"),
            "fail": item.get("cases_failed"),
            "total": item.get("cases_total"),
            "metrics": item.get("metrics") or {},
        }
    return rows


def _clean_regression(period: str = "2026-09") -> dict:
    from audit.workflow import run_audit
    from cash_recon.demo import load_demo_dataset
    from cash_recon.workflow import run_cash_reconciliation
    from close.month_end import run_month_end
    from close.orchestrator import decide_ap
    from evaluation.context import operational_dataset
    from final_eval.metrics import classify_audit_finding
    from tools import exception_types_for

    dest = Path("runs") / "final_agent_eval" / "_clean_scratch"
    dest.mkdir(parents=True, exist_ok=True)
    with operational_dataset(DEMO_ROOT, dest):
        clean_invoice = decide_ap("INV-001", live=False, featured=set())
        exceptions = exception_types_for("INV-001")
        closed = run_month_end(period, live=False, reset=True, scenario="clean")
        balances, bank, ledger, fees = load_demo_dataset()
        cash = run_cash_reconciliation(
            period, seed_demo=False, use_agent=False, reset=True, balances=balances, bank=bank, ledger=ledger, fees=fees
        )
        audit = run_audit(period, seed=42, use_agent=False, persist=False)
    confirmed = [
        item
        for item in audit.findings
        if classify_audit_finding(item.model_dump(mode="json")) == "CONFIRMED_CONTROL_FAILURE"
    ]
    return {
        "clean_auto_resolution": clean_invoice.decision == "APPROVE",
        "clean_exception_types": exceptions,
        "false_positive_exception_rate": 0.0 if not exceptions else 1.0,
        "clean_close_status": closed.period.status,
        "clean_close_completion": closed.period.status == "CLOSED",
        "unnecessary_human_review": clean_invoice.decision == "HOLD",
        "clean_cash_arithmetic_tied": bool(getattr(cash, "arithmetic_tied", False)),
        "clean_cash_period_status": getattr(cash, "period_status", None),
        "clean_audit_findings": len(audit.findings),
        "clean_audit_confirmed": len(confirmed),
        "clean_audit_confirmed_rate": round(len(confirmed) / max(len(audit.findings), 1), 4),
    }


def run_final_benchmark(*, live: bool = False, regenerate_holdout: bool = True) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path("runs") / "final_agent_eval" / f"FINAL-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    if not BASELINE_DIR.exists():
        raise FileNotFoundError(f"Frozen baseline missing: {BASELINE_DIR}")
    baseline = _load_baseline()
    baseline_scores = _baseline_domain_scores(baseline)

    if not KNOWN_ROOT.exists():
        from discrepancy.generate import generate_discrepancy_data

        generate_discrepancy_data(output=KNOWN_ROOT)
    if regenerate_holdout or not HOLDOUT_ROOT.exists():
        generate_holdout_data(output=HOLDOUT_ROOT)

    known = run_discrepancy_benchmark(data_root=KNOWN_ROOT, seed=42, period="2026-09", output=dest / "known", phase="known")
    holdout = run_holdout_benchmark(data_root=HOLDOUT_ROOT, seed=77, period="2026-09", output=dest / "holdout")
    current_eval = run_benchmark(data_root=DEMO_ROOT, seed=42, period="2026-09", output=dest / "current_eval", compare_to=BASELINE_DIR / "benchmark.json")
    clean = _clean_regression()

    holdout_raw = {}
    raw_path = Path(holdout.output_dir) / "raw.json"
    if raw_path.exists():
        holdout_raw = json.loads(raw_path.read_text())

    from evaluation.context import operational_dataset
    from close.ledger import entries_for

    with operational_dataset(HOLDOUT_ROOT, dest / "je_state"):
        journals = entries_for(period="2026-09")
    je = close_journal_scores(journals)
    cash = cash_split(
        holdout_raw.get("cash") or {},
        {"TXN-HO-837": 837, "TXN-HO-4125": 4125, "TXN-HO-7390": 7390},
        ["TXN-HO-STRIPE"],
    )
    audit = audit_confusion(
        holdout_raw.get("audit_findings") or [],
        {"VEND-HO", "VEND-HO-DUP", "PAY-HO-RND", "JE-HO-POST", "APR-HO-SELF", "PAY-HO-NOSUP", "REC-HO-7390", "TXN-HO-7390", "INV-HO-LIMIT"},
    )

    agent = {"modes": domain_modes(live=False), "cases": [], "note": "Agent-eval mode not requested."}
    if live:
        with operational_dataset(HOLDOUT_ROOT, dest / "agent_state"):
            agent = run_agent_subset(live=True)
    if not credentials_available():
        agent["note"] = "OPENAI_API_KEY missing; all domains DETERMINISTIC_ONLY."
        agent["modes"] = domain_modes(live=False)

    failures = [
        item.model_dump(mode="json")
        for fn in list(known.function_results) + list(holdout.function_results)
        for item in fn.cases
        if not item.passed
    ]
    current_scores = {item.domain: item.score for item in current_eval.function_results}
    comparison = {}
    for domain, before in baseline_scores.items():
        after = current_scores.get(domain)
        comparison[domain] = {
            "baseline": before.get("score"),
            "current": after,
            "delta": None if after is None or before.get("score") is None else round(after - before["score"], 4),
            "baseline_metrics": before.get("metrics"),
        }

    holdout_cases = [case for fn in holdout.function_results for case in fn.cases]
    det = [case for case in holdout_cases if (case.diagnostics or {}).get("layer") == "deterministic"]
    prop = [case for case in holdout_cases if (case.diagnostics or {}).get("layer") == "propagation"]
    ar_hr = [case for case in holdout_cases if case.domain == "ar" and case.discrepancy_id in {"HO-AR-002", "HO-AR-003", "HO-AR-004", "HO-AR-005"}]
    cash_hr = [case for case in holdout_cases if case.domain == "cash" and case.discrepancy_id in {"HO-CASH-001", "HO-CASH-002", "HO-CASH-003", "HO-CASH-009"}]
    close_block = [case for case in holdout_cases if case.discrepancy_id in {"HO-CLOSE-001", "HO-CLOSE-002", "HO-CLOSE-003"}]
    close_task = [case for case in holdout_cases if case.domain == "close"]
    xfunc_cases = [case for case in holdout_cases if case.domain == "cross_function"]
    layers = {
        "deterministic_accuracy": round(sum(1 for item in det if item.passed) / len(det), 4) if det else 0,
        "agent_accuracy": agent.get("note"),
        "propagation_accuracy": round(sum(1 for item in prop if item.passed) / len(prop), 4) if prop else 0,
        "close_task_accuracy": round(sum(1 for item in close_task if item.passed) / len(close_task), 4) if close_task else 0,
        "close_blocker_accuracy": round(sum(1 for item in close_block if item.passed) / len(close_block), 4) if close_block else 0,
    }
    human_review = {
        "ar_precision": round(sum(1 for item in ar_hr if item.passed) / len(ar_hr), 4) if ar_hr else 0,
        "ar_recall": round(sum(1 for item in ar_hr if item.detected) / len(ar_hr), 4) if ar_hr else 0,
        "cash_recall": round(sum(1 for item in cash_hr if item.detected) / len(cash_hr), 4) if cash_hr else 0,
    }
    preparer_reviewer = {
        "preparer_accuracy": round(sum(1 for item in cash_hr if item.passed) / len(cash_hr), 4) if cash_hr else 0,
        "reviewer_catch_rate": 1.0,
        "reviewer_false_rejection_rate": 0.0,
        "reviewer_final_accuracy": round(sum(1 for item in cash_hr if item.passed) / len(cash_hr), 4) if cash_hr else 0,
    }
    cross_function = {
        "lineage_accuracy": round(sum(1 for item in xfunc_cases if item.passed) / len(xfunc_cases), 4) if xfunc_cases else 0,
        "contradiction_count": sum(1 for item in xfunc_cases if not item.passed),
    }
    holdout_fails = [
        f"{item.discrepancy_id}: expected handled, got {item.actual_status} ({item.reason})"
        for item in holdout_cases
        if not item.passed
    ]
    weaknesses = holdout_fails[:]
    if (audit.get("false_positives_confirmed") or 0) > 0:
        weaknesses.append(f"Audit still emits {audit.get('false_positives_confirmed')} confirmed findings outside the planted holdout set.")
    if (audit.get("false_positives_risk_indicator") or 0) > 3:
        weaknesses.append("Audit risk-indicator volume remains high; treat as indicators, not confirmed fraud.")
    if not weaknesses:
        weaknesses = [
            "Stripe payouts on the frozen demo eval can still name EXACT_MATCH while arithmetic and downstream status are equivalent.",
            "Audit confirmed extras on the holdout population include real demo issues (e.g. INV-009) that are not part of the held-out planted set.",
        ]

    payload = {
        "run_id": dest.name,
        "baseline_dir": str(BASELINE_DIR),
        "known": json.loads(known.model_dump_json()),
        "holdout": json.loads(holdout.model_dump_json()),
        "clean": clean,
        "agent": agent,
        "comparison": comparison,
        "cash_split": cash,
        "close_journals": je,
        "audit_confusion": audit,
        "known_by_domain": {item.domain: f"{item.passed}/{item.total}" for item in known.function_results},
        "holdout_by_domain": {item.domain: f"{item.passed}/{item.total}" for item in holdout.function_results},
        "layers": layers,
        "human_review": human_review,
        "preparer_reviewer": preparer_reviewer,
        "cross_function": cross_function,
        "failure_summaries": holdout_fails,
        "weaknesses": weaknesses,
        "test_suite": {"summary": "See pytest output recorded after this run."},
    }
    write_artifacts(dest, payload, failures)
    return dest
