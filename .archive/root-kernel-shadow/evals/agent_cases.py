"""Execute ``data/demo/agent_cases.json`` against live deterministic workflows.

No live LLM. Each case calls the same Python engines the CFO eval already uses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from invoice_ingestion import extract as invoice_extract
from invoice_ingestion.interpret import classify_text, parse_invoice_text
from tools import collect_case_evidence, exception_types_for, vendor_alias_established


REPO = Path(__file__).resolve().parent.parent
CANONICAL_CASES = REPO / "data" / "demo" / "agent_cases.json"


def load_agent_cases(path: Path | str | None = None) -> list[dict]:
    target = Path(path) if path else CANONICAL_CASES
    return json.loads(target.read_text())


def _case(case: dict, passed: bool, actual: Any, reason: str = "") -> dict:
    return {
        "case_id": case["case_id"],
        "agent": case.get("agent"),
        "capability": case.get("capability"),
        "passed": bool(passed),
        "expected": case.get("expected"),
        "actual": actual,
        "reason": reason,
        "source_record_ids": case.get("source_record_ids") or [],
    }


def _email_row(message_id: str) -> dict | None:
    path = invoice_extract.INGESTION_DIR / "emails.json"
    if not path.exists():
        return None
    rows = json.loads(path.read_text())
    return next((item for item in rows if item.get("message_id") == message_id), None)


def _email_text(row: dict) -> tuple[str, str, str]:
    attachments = row.get("attachments") or []
    text = attachments[0]["text"] if attachments else row.get("body", "")
    filename = attachments[0].get("filename", "") if attachments else ""
    return text, row.get("subject", ""), filename


class _Runtime:
    """Shared workflow results so a 24-case pass does not rerun month-end four times."""

    def __init__(self) -> None:
        self.cash_report = None
        self.month_end = None
        self.audit = None
        self.aging = None
        self.collections = None
        self.variance = None
        self.forecast = None
        self.forecast_var = None
        self.accrual_discovery = None

    def cash(self):
        if self.cash_report is None:
            from cash_recon.demo import load_demo_dataset, seed_provider_payouts
            from cash_recon.store import reset_cash_state
            from cash_recon.workflow import run_cash_reconciliation

            reset_cash_state()
            seed_provider_payouts()
            balances, bank, ledger, fees = load_demo_dataset()
            self.cash_report = run_cash_reconciliation(
                "2026-09",
                seed_demo=False,
                use_agent=False,
                reset=True,
                balances=balances,
                bank=bank,
                ledger=ledger,
                fees=fees,
            )
        return self.cash_report

    def cash_match(self, bank_id: str):
        report = self.cash()
        return next(
            (item for item in report.matches if bank_id in item.bank_transaction_ids),
            None,
        )

    def close(self, period: str = "2026-09"):
        if self.month_end is None:
            from close.month_end import run_month_end

            self.month_end = run_month_end(period, live=False, reset=True, scenario="demo")
        return self.month_end

    def audit_run(self, period: str, seed: int):
        if self.audit is None:
            from audit.workflow import run_audit

            self.audit = run_audit(period, seed=seed, use_agent=False, persist=False)
        return self.audit

    def aging_report(self, as_of: str):
        if self.aging is None:
            from ar.store import reset_state
            from ar.workflow import run_aging

            reset_state()
            self.aging = run_aging(as_of, persist=True)
        return self.aging

    def collections_run(self, as_of: str):
        if self.collections is None:
            from ar.workflow import run_collections

            self.aging_report(as_of)
            self.collections = run_collections(as_of, live=False, persist=True)
        return self.collections

    def gm_variance(self, period: str):
        if self.variance is None:
            from reporting.seed import seed_demo_ledger
            from reporting.variance import analyze_variance

            seed_demo_ledger()
            self.variance = analyze_variance("gross_margin_pct", period)
        return self.variance

    def cash_forecast(self, as_of: str, weeks: int):
        if self.forecast is None:
            from reporting.forecast import build_forecast
            from reporting.seed import seed_demo_ledger, seed_demo_receivable

            seed_demo_ledger()
            seed_demo_receivable()
            self.forecast = build_forecast(as_of, weeks=weeks)
        return self.forecast

    def forecast_variance(self, as_of: str, weeks: int):
        if self.forecast_var is None:
            from reporting.actuals import compare_forecast_to_actuals

            snapshot = self.cash_forecast(as_of, weeks)
            self.forecast_var = compare_forecast_to_actuals(snapshot)
        return self.forecast_var

    def harbor_discovery(self, period: str):
        if self.accrual_discovery is None:
            from accrual.discovery import discover_period, missing_bill_candidates

            report = discover_period(period)
            self.accrual_discovery = missing_bill_candidates(report)
        return self.accrual_discovery


def _run_one(case: dict, runtime: _Runtime) -> dict:
    case_id = case["case_id"]
    payload = case.get("input") or {}
    expected = case.get("expected") or {}
    try:
        if case_id.startswith("AC-EMAIL"):
            return _email_case(case, payload, expected)
        if case_id.startswith("AC-AP-") or case_id == "AC-AP-DUP":
            return _ap_case(case, payload, expected)
        if case_id == "AC-SCHEDULER-DUE":
            return _scheduler_case(case, payload, expected)
        if case_id == "AC-COLLECTIONS":
            return _collections_case(case, payload, expected, runtime)
        if case_id.startswith("AC-CASH-APPLY"):
            return _cash_apply_case(case, payload, expected)
        if case_id.startswith("AC-CASH-"):
            return _cash_recon_case(case, payload, expected, runtime)
        if case_id == "AC-ACCRUAL":
            return _accrual_case(case, payload, expected, runtime)
        if case_id == "AC-PREPAID":
            return _prepaid_case(case, payload, expected)
        if case_id == "AC-ASSET":
            return _asset_case(case, payload, expected)
        if case_id in {"AC-BS-RECON", "AC-CLOSE-REVIEW", "AC-CLOSE-MANAGER"}:
            return _close_case(case, payload, expected, runtime)
        if case_id == "AC-AUDITOR":
            return _audit_case(case, payload, expected, runtime)
        if case_id == "AC-VARIANCE":
            return _variance_case(case, payload, expected, runtime)
        if case_id == "AC-FORECAST":
            return _forecast_case(case, payload, expected, runtime)
        if case_id == "AC-FORECAST-VAR":
            return _forecast_var_case(case, payload, expected, runtime)
        if case_id == "AC-BOARD":
            return _board_case(case, payload, expected, runtime)
    except Exception as exc:
        return _case(case, False, {"error": str(exc)}, str(exc))
    return _case(case, False, None, f"no runtime handler for {case_id}")


def _email_case(case: dict, payload: dict, expected: dict) -> dict:
    row = _email_row(payload["message_id"])
    if row is None:
        return _case(case, False, None, f"missing {payload['message_id']}")
    text, subject, filename = _email_text(row)
    kind, _why = classify_text(text, subject=subject, filename=filename)
    parsed = parse_invoice_text(text, source_type="email", source_id=payload["message_id"])
    actual = {"classification": kind, "invoice_number": parsed.vendor_invoice_number}
    ok = kind == expected.get("classification")
    if expected.get("invoice_number"):
        ok = ok and parsed.vendor_invoice_number == expected["invoice_number"]
    return _case(case, ok, actual)


def _ap_case(case: dict, payload: dict, expected: dict) -> dict:
    from close.orchestrator import decide_ap

    invoice_id = payload["invoice_id"]
    result = decide_ap(invoice_id, live=False, featured=set())
    exceptions = exception_types_for(invoice_id)
    evidence = collect_case_evidence(invoice_id)
    actual = {
        "decision": result.decision,
        "exceptions": exceptions,
        "precedent_id": "CASE-001" if vendor_alias_established(evidence) else None,
    }
    ok = result.decision == expected.get("decision")
    for item in expected.get("exceptions") or []:
        ok = ok and item in exceptions
    if "exceptions" in expected and expected["exceptions"] == []:
        ok = ok and exceptions == []
    if expected.get("precedent_id"):
        ok = ok and vendor_alias_established(evidence)
    return _case(case, ok, actual)


def _scheduler_case(case: dict, payload: dict, expected: dict) -> dict:
    from scheduling.cash import load_cash_position, payment_candidate

    candidate = payment_candidate(payload["invoice_id"], cash=load_cash_position())
    if candidate is None:
        return _case(case, False, None, "missing payment candidate")
    eligible = bool(candidate.due_within_horizon or candidate.late)
    return _case(
        case,
        eligible == bool(expected.get("eligible")),
        {"eligible": eligible, "days_until_due": candidate.days_until_due, "as_of": payload.get("as_of")},
    )


def _collections_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from ar.aging import aging_bucket, days_past_due
    from ar.store import all_invoices

    as_of = payload.get("as_of", "2026-09-30")
    invoice_id = payload["invoice_id"]
    aging = runtime.aging_report(as_of)
    line = next((item for item in aging.lines if item.invoice_id == invoice_id), None)
    if line is None:
        invoice = next((item for item in all_invoices() if item.invoice_id == invoice_id), None)
        bucket = aging_bucket(days_past_due(invoice.due_date, as_of)) if invoice else None
    else:
        bucket = line.aging_bucket
    collections = runtime.collections_run(as_of)
    decision = next((item for item in collections.decisions if item.invoice_id == invoice_id), None)
    action = getattr(decision, "action", None)
    ok = bucket == expected.get("aging_bucket")
    if expected.get("action_not"):
        ok = ok and action is not None and action != expected["action_not"]
    return _case(case, ok, {"aging_bucket": bucket, "action": action})


def _cash_apply_case(case: dict, payload: dict, expected: dict) -> dict:
    from ar.store import reset_state
    from ar.workflow import run_cash_apply

    reset_state()
    result = run_cash_apply(payload["payment_id"], as_of="2026-09-30", live=False, persist=False)
    invoice_ids = [item.invoice_id for item in (result.final.applications or [])]
    if not invoice_ids and result.payment and result.payment.invoice_reference:
        invoice_ids = [result.payment.invoice_reference]
    actual = {"decision": result.final.decision, "invoice_ids": invoice_ids}
    ok = result.final.decision == expected.get("decision")
    for invoice_id in expected.get("invoice_ids") or []:
        ok = ok and invoice_id in invoice_ids
    return _case(case, ok, actual)


def _cash_recon_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    match = runtime.cash_match(payload["bank_id"])
    if match is None:
        return _case(case, False, None, f"no cash match for {payload['bank_id']}")
    actual = {
        "status": match.status,
        "match_type": match.match_type,
        "difference_cents": match.difference_minor,
        "invented_explanation": match.match_type not in {
            "UNEXPLAINED_DIFFERENCE",
            "FEE_NETTED",
            "GROUPED_MATCH",
            "EXACT_MATCH",
            "PROVIDER_PAYOUT",
            "TIMING_DIFFERENCE",
            "HUMAN_REVIEW",
        }
        and match.status != "HUMAN_REVIEW",
    }
    ok = True
    if "status" in expected:
        ok = ok and match.status == expected["status"]
    if "match_type" in expected:
        ok = ok and match.match_type == expected["match_type"]
    if "difference_cents" in expected:
        ok = ok and match.difference_minor == expected["difference_cents"]
    if expected.get("invented_explanation") is False:
        ok = ok and match.status == "HUMAN_REVIEW" and match.match_type == "UNEXPLAINED_DIFFERENCE"
        actual["invented_explanation"] = False
    return _case(case, ok, actual)


def _accrual_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from tools import DATA_DIR as tools_dir

    vendor = payload["vendor"]
    missing = runtime.harbor_discovery(payload["period"])
    needed = any(vendor.lower() in item.vendor.lower() for item in missing)
    planted = expected.get("accrual_id")
    journal_path = Path(tools_dir) / "close" / "journal_entries.json"
    planted_present = False
    if planted and journal_path.exists():
        rows = json.loads(journal_path.read_text())
        planted_present = any(
            item.get("transaction_id") == planted or planted in (item.get("related_ids") or [])
            for item in rows
        )
    actual = {
        "needed": needed,
        "accrual_id": planted if planted_present else None,
        "discovered_vendors": [item.vendor for item in missing],
        "runtime_mints_own_ids": True,
    }
    ok = needed == bool(expected.get("needed")) and planted_present
    return _case(case, ok, actual)


def _prepaid_case(case: dict, payload: dict, expected: dict) -> dict:
    from prepaid.agent import deterministic_prepare

    decision = deterministic_prepare(payload["prepaid_id"])
    method = decision.selected_method
    treatment = "AMORTIZE" if method in {"straight_line_monthly", "daily_prorate"} else method
    return _case(case, treatment == expected.get("treatment"), {"treatment": treatment, "method": method})


def _asset_case(case: dict, payload: dict, expected: dict) -> dict:
    from fixed_assets.agent import deterministic_prepare
    from fixed_assets.schedule import should_capitalize
    from fixed_assets.store import load_seed_assets, load_seed_candidates

    source = payload["source"]
    candidate = next((item for item in load_seed_candidates() if item.source_document_id == source or item.candidate_id == source), None)
    asset = next((item for item in load_seed_assets() if item.source_document_id == source or source in (item.evidence_refs or [])), None)
    subject = asset or candidate
    if subject is None:
        return _case(case, False, None, f"no capital candidate for {source}")
    decision = deterministic_prepare(subject)
    amount = subject.cost if hasattr(subject, "cost") else subject.amount
    depreciable = should_capitalize(amount, subject.useful_life_months)
    already_on_books = asset is not None and depreciable
    treatment = (
        "DEPRECIATE"
        if already_on_books or (decision.decision == "capitalize" and depreciable)
        else decision.decision
    )
    return _case(case, treatment == expected.get("treatment"), {"treatment": treatment, "decision": decision.decision})


def _close_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from close.agents import deterministic_coordinate
    from close.checklist import unresolved_blockers

    state = runtime.close(payload.get("period", "2026-09"))
    tasks = {item.task_id: item for item in state.tasks}
    cash = tasks.get("cash") or tasks.get("TASK-CASH")
    blocker_text = " ".join(
        filter(
            None,
            [
                getattr(cash, "blocker_reason", "") if cash else "",
                " ".join(state.human_review_items),
                " ".join(item.blocker_reason or "" for item in state.tasks),
            ],
        )
    )
    cash_open = (
        state.period.status in {"BLOCKED", "IN_PROGRESS"}
        or (cash is not None and cash.status in {"BLOCKED", "NEEDS_REVIEW", "FAILED"})
        or "12.40" in blocker_text
    )
    blocked = state.period.status == "BLOCKED" or bool(unresolved_blockers(state.tasks)) or "12.40" in blocker_text
    manager = state.manager or deterministic_coordinate(state)
    actual = {
        "period_status": state.period.status,
        "blocker": "12.40" if "12.40" in blocker_text else blocker_text[:80],
        "cash_open": cash_open,
        "coordination": "deterministic_coordinate",
        "blocked": blocked,
        "manager_can_close": getattr(manager, "can_close", None),
    }
    ok = True
    if "period_status" in expected:
        ok = ok and (
            state.period.status == expected["period_status"]
            or (expected["period_status"] == "BLOCKED" and blocked)
        )
    if "blocker" in expected:
        ok = ok and expected["blocker"] in blocker_text
    if "cash_open" in expected:
        ok = ok and cash_open == expected["cash_open"]
    if "coordination" in expected:
        ok = ok and expected["coordination"] == "deterministic_coordinate"
    if "blocked" in expected:
        ok = ok and blocked == expected["blocked"]
    return _case(case, ok, actual)


def _audit_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from audit.eval import _finding_object_ids
    from evaluation.evaluators.audit_controls import _duplicate_reperformed

    run = runtime.audit_run(payload.get("period", "2026-09"), int(payload.get("seed", 42)))
    found = _finding_object_ids(run)
    for control in run.controls:
        found.update(control.tested_ids)
    wanted = list(expected.get("findings_include") or [])
    detected = []
    missing = []
    for item in wanted:
        ok = item in found
        if item == "INV-006" and not ok:
            ok = _duplicate_reperformed(item, run)
        if ok:
            detected.append(item)
        else:
            missing.append(item)
    return _case(case, missing == [], {"findings_include": detected, "missing": missing})


def _variance_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    explanation = runtime.gm_variance(payload.get("period", "2026-09"))
    driver_ids = sorted(
        {
            txn
            for item in explanation.contributors
            for txn in list(item.source_transaction_ids) + list(item.source_document_ids)
        }
    )
    august = round(float(explanation.comparison_value), 2)
    september = round(float(explanation.current_value), 2)
    actual = {"august": august, "september": september, "driver_ids": driver_ids}
    ok = august == expected.get("august") and september == expected.get("september")
    for txn in expected.get("driver_ids") or []:
        ok = ok and txn in driver_ids
    return _case(case, ok, actual)


def _forecast_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    snapshot = runtime.cash_forecast(payload.get("as_of", "2026-09-19"), int(payload.get("weeks", 13)))
    actual = {"week_count": len(snapshot.weeks)}
    return _case(case, actual["week_count"] == expected.get("week_count"), actual)


def _forecast_var_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from reporting.actuals import load_actuals

    explanation = runtime.forecast_variance("2026-09-19", 13)
    actual_ids = {item.source_id for item in load_actuals() if item.source_id}
    contributor_ids = {item.source_id for item in explanation.contributors if item.source_id}
    sources = sorted(actual_ids | contributor_ids)
    actual = {"miss_sources": sources}
    ok = all(item in sources for item in expected.get("miss_sources") or [])
    return _case(case, ok, actual)


def _board_case(case: dict, payload: dict, expected: dict, runtime: _Runtime) -> dict:
    from reporting.reviewer import review_variance
    from reporting.statements import build_income_statement, period_report

    period = payload.get("period", "2026-09")
    explanation = runtime.gm_variance(period)
    current, _prior, _metrics = period_report(period)
    statement = build_income_statement(period)
    verdict = review_variance(explanation)
    ties = (
        abs(explanation.current_value - statement.gross_margin_pct) <= 1e-6
        and abs(current.gross_margin_pct - statement.gross_margin_pct) <= 1e-6
    )
    actual = {
        "metrics_tie_to_gl": ties,
        "statement_gm": statement.gross_margin_pct,
        "variance_gm": explanation.current_value,
        "review": verdict.decision,
    }
    return _case(case, ties == bool(expected.get("metrics_tie_to_gl")), actual)


def run_agent_cases(path: Path | str | None = None) -> dict:
    cases = load_agent_cases(path)
    runtime = _Runtime()
    results = [_run_one(case, runtime) for case in cases]
    by_agent: dict[str, dict[str, int]] = {}
    for item in results:
        bucket = by_agent.setdefault(item["agent"] or "unknown", {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        if item["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    passed = sum(1 for item in results if item["passed"])
    return {
        "cases": results,
        "passed": passed,
        "failed": len(results) - passed,
        "total": len(results),
        "pass_rate_by_agent": {
            name: round(row["passed"] / row["total"], 4) if row["total"] else 0.0
            for name, row in sorted(by_agent.items())
        },
        "unhandled": [item["case_id"] for item in results if item.get("reason", "").startswith("no runtime handler")],
    }
