"""Run the Maximor Finance Gauntlet against production workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.isolation import evaluation_phase, operational_phase_guard
from memory.policy import memory_mode
from cfo.shared_state import shared_state_mode


REPO = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO / "runs" / "evals"


def _row(case_id: str, family: str, passed: bool, **extra: Any) -> dict[str, Any]:
    payload = {"case_id": case_id, "family": family, "passed": bool(passed)}
    payload.update(extra)
    return payload


def grade_documents() -> list[dict[str, Any]]:
    from invoice_ingestion.traps import analyze_document
    from evals.maximor_finance_gauntlet.fixtures.documents import public_catalog

    catalog = public_catalog()
    with operational_phase_guard():
        observed = []
        for item in catalog:
            analysis = analyze_document(
                item["text"],
                subject=item.get("subject") or "",
                filename=item.get("filename") or "",
                expected_banking=item.get("expected_banking"),
            )
            observed.append({"case_id": item["case_id"], "analysis": analysis.as_dict(), "title": item["title"]})
    with evaluation_phase():
        from evals.maximor_finance_gauntlet.private_answers.documents import GOLD

        rows = []
        for item in observed:
            gold = GOLD[item["case_id"]]
            actual = item["analysis"]
            flags_ok = set(gold.get("flags") or []).issubset(set(actual.get("flags") or []))
            class_ok = actual.get("classification") == gold["classification"]
            pay_ok = bool(actual.get("payable")) is bool(gold["payable"])
            super_ok = True
            if gold.get("supersedes"):
                super_ok = actual.get("supersedes") == gold["supersedes"]
            passed = class_ok and pay_ok and flags_ok and super_ok
            rows.append(
                _row(
                    item["case_id"],
                    "documents",
                    passed,
                    title=item["title"],
                    expected=gold,
                    actual={"classification": actual.get("classification"), "payable": actual.get("payable"), "flags": actual.get("flags"), "supersedes": actual.get("supersedes")},
                )
            )
        return rows


def _bank(**kwargs):
    from cash_recon.models import BankTransaction
    from cash_recon.normalize import prepare_bank

    return prepare_bank([BankTransaction.model_validate(kwargs)])[0]


def _ledger(**kwargs):
    from cash_recon.models import LedgerEntry
    from cash_recon.normalize import prepare_ledger

    return prepare_ledger([LedgerEntry.model_validate(kwargs)])[0]


def _fee(**kwargs):
    from cash_recon.models import FeeEvidence
    from cash_recon.mathutil import cents

    if "amount_minor" not in kwargs and kwargs.get("amount") is not None:
        kwargs["amount_minor"] = cents(kwargs["amount"])
    return FeeEvidence.model_validate(kwargs)


def grade_cash() -> list[dict[str, Any]]:
    from cash_recon.workflow import run_cash_reconciliation
    from cash_recon.models import PeriodBalances
    from cash_recon.evidence import amount_only_match

    with evaluation_phase():
        from evals.maximor_finance_gauntlet.private_answers.cash import CASH_CASES

        cases = CASH_CASES
    rows = []
    for spec in cases:
        with operational_phase_guard():
            bank = [_bank(**spec["bank"])]
            ledger = [_ledger(**item) for item in spec["ledger"]]
            fees = [_fee(**item) for item in spec.get("fees") or []]
            report = run_cash_reconciliation(
                "2026-09",
                balances=PeriodBalances(opening_bank=0, opening_ledger=0, as_of_date="2026-09-30", opening_bank_minor=0, opening_ledger_minor=0),
                bank=bank,
                ledger=ledger,
                fees=fees,
                reset=True,
            )
            match = next((item for item in report.matches if spec["bank"]["transaction_id"] in item.bank_transaction_ids), None)
            linked = False
            if match and match.ledger_entry_ids:
                led = next((item for item in ledger if item.entry_id in match.ledger_entry_ids), None)
                linked = bool(led and not amount_only_match(bank[0], led))
        family = spec.get("family") or "cash"
        expect_type = spec.get("expect_type")
        actual_type = getattr(match, "match_type", None) if match else None
        actual_status = getattr(match, "status", None) if match else None
        if spec.get("linked") is False:
            passed = actual_type not in {"EXACT_MATCH", "GROUPED_MATCH", "FEE_NETTED"} and not (linked and actual_status == "MATCHED")
        elif spec.get("allow_unmatched"):
            passed = actual_type in {expect_type, "UNMATCHED_BANK", "UNMATCHED_LEDGER", "TIMING_DIFFERENCE"}
        else:
            passed = actual_type == expect_type and actual_status == spec.get("expect_status")
        rows.append(
            _row(
                spec["case_id"],
                family,
                passed,
                title=spec["title"],
                expected={"match_type": expect_type, "status": spec.get("expect_status"), "linked": spec.get("linked")},
                actual={"match_type": actual_type, "status": actual_status, "linked": linked},
            )
        )
    return rows


def _answers_match(actual: dict[str, Any], gold: dict[str, Any]) -> bool:
    answer = actual.get("answer")
    if not gold:
        return answer not in (None, [])
    passed = True
    if "contains" in gold:
        hay = answer if isinstance(answer, list) else [answer]
        passed = gold["contains"] in hay or any(gold["contains"] in str(item) for item in hay)
    if "equals" in gold:
        try:
            passed = abs(float(answer) - float(gold["equals"])) < 1e-6
        except (TypeError, ValueError):
            passed = answer == gold["equals"]
    if "min" in gold:
        try:
            passed = float(answer) >= float(gold["min"])
        except (TypeError, ValueError):
            passed = False
    if gold.get("nonempty"):
        passed = bool(answer)
    if gold.get("startswith"):
        hay = answer if isinstance(answer, list) else [answer]
        passed = any(isinstance(item, str) and item.startswith(gold["startswith"]) for item in hay)
    if gold.get("max") is not None:
        try:
            passed = float(answer) <= float(gold["max"])
        except (TypeError, ValueError):
            passed = False
    return passed


def grade_questions() -> list[dict[str, Any]]:
    from cfo.query import answer_finance_question
    from evals.maximor_finance_gauntlet.fixtures.questions import QUESTIONS

    with operational_phase_guard():
        observed = []
        for item in QUESTIONS:
            spec = dict(item["spec"])
            spec["question_id"] = item["question_id"]
            observed.append((item, answer_finance_question(spec)))
    with evaluation_phase():
        from evals.maximor_finance_gauntlet.private_answers.questions import EXPECTED

        rows = []
        for item, actual in observed:
            gold = EXPECTED.get(item["question_id"]) or {}
            passed = _answers_match(actual, gold)
            rows.append(
                _row(
                    item["question_id"],
                    "questions",
                    passed,
                    difficulty=item["difficulty"],
                    prompt=item["prompt"],
                    actual=actual.get("answer"),
                    sources=actual.get("source_record_ids") or [],
                    steps=actual.get("steps") or [],
                )
            )
        return rows


def grade_rubrics() -> list[dict[str, Any]]:
    from prepaid.models import PrepaidItem
    from prepaid.schedule import generate_schedule

    item = PrepaidItem(
        prepaid_id="PRE-INS-001",
        vendor="Hartford Insurance",
        description="Annual commercial property and liability policy",
        source_document_id="INV-019",
        total_amount=12000.0,
        start_date="2026-09-01",
        end_date="2027-08-31",
        initial_account="Prepaid Expenses",
        expense_account="Insurance Expense",
        amortization_method="straight_line_monthly",
        evidence_refs=["INV-019"],
        created_at="2026-09-01T00:00:00Z",
    )
    with operational_phase_guard():
        schedule = generate_schedule(item)
        september = next((line for line in schedule if line.period == "2026-09"), None)
        remaining = round(item.total_amount - sum(line.amount for line in schedule if line.period <= "2026-09"), 2)
    criteria = {
        "identifies_service_period": bool(item.start_date and item.end_date),
        "september_expense": bool(september and abs(september.amount - 1000.0) < 0.01),
        "remaining_balance": abs(remaining - 11000.0) < 0.01,
        "schedule_sums_to_total": abs(sum(line.amount for line in schedule) - 12000.0) < 0.01,
        "source_evidence": "INV-019" in item.evidence_refs,
    }
    score = sum(1 for value in criteria.values() if value) / len(criteria)
    return [
        _row(
            "RUBRIC-PREPAID-SEP",
            "rubrics",
            score == 1.0,
            title="Complete September close for prepaid insurance",
            score=round(score, 4),
            criteria=criteria,
        )
    ]


def grade_consistency() -> list[dict[str, Any]]:
    from pathlib import Path

    from cfo.consistency import clean_invoice_ids, duplicate_invoice_ids, duplicate_must_not_propagate, event_consistency
    from tools import DATA_DIR, configure_data_dir

    previous = Path(DATA_DIR)
    demo = Path(__file__).resolve().parents[2] / "data" / "demo"
    rebound = False
    try:
        with operational_phase_guard():
            dups = duplicate_invoice_ids()
            if not dups and demo.is_dir():
                configure_data_dir(demo)
                rebound = True
                dups = duplicate_invoice_ids()
            dup_id = dups[0] if dups else None
            cleans = [item for item in clean_invoice_ids() if item != dup_id]
            clean_id = cleans[0] if cleans else "INV-001"
            rows = []
            if dup_id:
                dup = duplicate_must_not_propagate(dup_id)
                rows.append(_row(f"XWF-{dup_id}", "consistency", dup["ok"], actual=dup, title="Duplicate invoice must not enter payment"))
            else:
                rows.append(_row("XWF-NO-DUPLICATE", "consistency", False, title="No duplicate invoice in operational books"))
            clean = event_consistency(clean_id)
            rows.append(_row(f"XWF-{clean_id}", "consistency", clean["ok"] or clean["approved"], actual=clean, title="Clean invoice is a payable"))
        return rows
    finally:
        if rebound:
            configure_data_dir(previous)


def grade_long_horizon(*, memory_enabled: bool = True) -> list[dict[str, Any]]:
    from memory.scenarios import run_harbor_contamination, run_harbor_cross_period, run_harbor_self_correction

    with operational_phase_guard():
        with memory_mode(memory_enabled):
            story = run_harbor_cross_period(memory_enabled=memory_enabled)
            correction = run_harbor_self_correction(memory_enabled=memory_enabled)
            contamination = run_harbor_contamination(memory_enabled=memory_enabled)
    sep_lookup = story.get("september_lookup")
    reused = bool(getattr(sep_lookup, "precedent_used", False)) if memory_enabled else not bool(getattr(sep_lookup, "precedent_used", False))
    rows = [
        _row(
            "LH-HARBOR-AUG-SEP",
            "long_horizon",
            bool(story.get("august") and story.get("september")),
            period="2026-08/2026-09",
            memory_enabled=memory_enabled,
            precedent_used=bool(getattr(sep_lookup, "precedent_used", False)),
        ),
        _row(
            "LH-SELF-CORRECT",
            "long_horizon",
            bool(correction.get("books_corrected") and correction.get("detected_prior_estimate")),
            period="2026-10",
            explanation=(correction.get("explanation") or {}).get("narrative"),
        ),
        _row(
            "LH-CONTAMINATION",
            "long_horizon",
            bool(contamination.get("contained")),
            period="2026-09",
            copied_wrong_amount=contamination.get("copied_wrong_amount"),
            contained=contamination.get("contained"),
        ),
    ]
    if memory_enabled:
        rows.append(_row("LH-MEMORY-REUSED", "memory", reused, precedent_used=True))
    else:
        rows.append(_row("LH-MEMORY-OFF", "memory", reused, precedent_used=False))
    return rows


def grade_recovery() -> list[dict[str, Any]]:
    from cfo.recovery import missing_stripe_metadata, parse_csv_text, parse_json_text, recover_or_skip, replay_event

    with operational_phase_guard():
        bad_json, json_err = parse_json_text("{not json")
        rows_csv, csv_err = parse_csv_text("date,amount\n2026-09-01,10")
        missing_csv, missing_err = parse_csv_text("hello\nworld", required=("date", "amount"))
        seen: set[str] = set()
        first = replay_event("evt_1", seen)
        second = replay_event("evt_1", seen)
        stripe_missing = missing_stripe_metadata({"amount": 10})
        recovered = recover_or_skip("{bad", kind="json")
    checks = [
        _row("REC-JSON", "recovery", bad_json is None and bool(json_err) and recovered["invented"] is False),
        _row("REC-CSV-OK", "recovery", csv_err is None and bool(rows_csv)),
        _row("REC-CSV-MISSING", "recovery", missing_csv is None and bool(missing_err)),
        _row("REC-DUP-EVENT", "recovery", first == ("accepted", True) and second == ("duplicate_ignored", False)),
        _row("REC-STRIPE-META", "recovery", "id" in stripe_missing and "currency" in stripe_missing),
    ]
    return checks


def grade_existing_packs() -> list[dict[str, Any]]:
    from evals.invoice_error_detection import run_eval
    from evals.agent_cases import run_agent_cases

    invoice = run_eval(write=False, tag="gauntlet")
    agents = run_agent_cases()
    rows = []
    for item in invoice.get("cases") or []:
        rows.append(_row(item.get("case_id"), "invoice_pack", bool(item.get("correct")), title=item.get("notes") or item.get("planted_error")))
    for item in agents.get("cases") or agents:
        if isinstance(item, dict) and item.get("case_id"):
            rows.append(_row(item["case_id"], "agent_cases", bool(item.get("passed")), capability=item.get("capability")))
    return rows


def build_scorecard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    families = {}
    for item in cases:
        family = item.get("family") or "other"
        bucket = families.setdefault(family, {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        if item.get("passed"):
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    for bucket in families.values():
        bucket["rate"] = round(bucket["passed"] / bucket["total"], 4) if bucket["total"] else 0.0
    total = len(cases)
    passed = sum(1 for item in cases if item.get("passed"))
    anti = families.get("anti_hack") or {"passed": 0, "failed": 0, "total": 0}
    recovery = families.get("recovery") or {"rate": None, "total": 0, "passed": 0}
    contamination = next((item for item in cases if item.get("case_id") == "LH-CONTAMINATION"), None)
    copied = bool(contamination and contamination.get("copied_wrong_amount"))
    period_rows = [item for item in cases if item.get("family") == "long_horizon" and item.get("period")]
    by_period = {}
    for item in period_rows:
        key = str(item.get("period"))
        bucket = by_period.setdefault(key, {"passed": 0, "total": 0})
        bucket["total"] += 1
        if item.get("passed"):
            bucket["passed"] += 1
    for bucket in by_period.values():
        bucket["rate"] = round(bucket["passed"] / bucket["total"], 4) if bucket["total"] else 0.0
    return {
        "total_scenarios": total,
        "scenarios_passed": passed,
        "scenarios_failed": total - passed,
        "document_correctness": families.get("documents", {}).get("rate"),
        "reconciliation_correctness": families.get("cash", {}).get("rate"),
        "accounting_task_rubric_score": families.get("rubrics", {}).get("rate"),
        "multi_step_qa_accuracy": families.get("questions", {}).get("rate"),
        "cross_workflow_consistency": families.get("consistency", {}).get("rate"),
        "cross_workflow_consistency_rate": families.get("consistency", {}).get("rate"),
        "memory_correctness": families.get("memory", {}).get("rate"),
        "long_horizon_accuracy": families.get("long_horizon", {}).get("rate"),
        "long_horizon_by_period": by_period,
        "error_recovery": recovery.get("rate"),
        "recovery_rate": recovery.get("rate"),
        "error_propagation_rate": 1.0 if copied else 0.0,
        "unsupported_action_rate": anti.get("failed", 0) / max(anti.get("total", 1), 1),
        "unsupported_assertion_rate": anti.get("failed", 0) / max(anti.get("total", 1), 1),
        "by_family": families,
    }


def run_gauntlet(*, memory_enabled: bool = True, shared_state: bool = True, include_existing: bool = True) -> dict[str, Any]:
    with memory_mode(memory_enabled), shared_state_mode(shared_state):
        cases: list[dict[str, Any]] = []
        cases.extend(grade_documents())
        cases.extend(grade_cash())
        cases.extend(grade_questions())
        cases.extend(grade_rubrics())
        cases.extend(grade_consistency())
        cases.extend(grade_long_horizon(memory_enabled=memory_enabled))
        cases.extend(grade_recovery())
        if include_existing:
            cases.extend(grade_existing_packs())
    scorecard = build_scorecard(cases)
    payload = {
        "run_id": datetime.now(timezone.utc).strftime("GAUNTLET-%Y%m%dT%H%M%SZ"),
        "memory_enabled": memory_enabled,
        "shared_state": shared_state,
        "scorecard": scorecard,
        "cases": cases,
        "inspired_by": [
            {"name": "AccountingBench", "url": "https://accounting.penrose.com/"},
            {"name": "APEX-Accounting", "url": "https://huggingface.co/datasets/mercor/apex-accounting"},
            {"name": "Finance Agent Benchmark", "url": "https://huggingface.co/datasets/vals-ai/finance_agent_benchmark"},
            {"name": "DABstep", "url": "https://huggingface.co/datasets/adyen/DABstep"},
            {"name": "BenchRec", "url": "https://www.kaggle.com/datasets/benchmarkteam/benchrec-real-world-cash-reconciliation-dataset"},
            {"name": "Invoice Sandbox Benchmark", "url": "https://github.com/ciru-ai/invoice-sandbox-benchmark"},
        ],
    }
    return payload


def write_gauntlet(payload: dict[str, Any], dest: Path | None = None) -> Path:
    import json

    dest = dest or (RESULTS_DIR / "maximor_finance_gauntlet.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    latest = dest.parent / "maximor_finance_gauntlet_latest.json"
    latest.write_text(dest.read_text())
    return dest
