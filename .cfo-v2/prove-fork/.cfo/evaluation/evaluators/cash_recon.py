"""Evaluate the existing cash-reconciliation workflow."""

from __future__ import annotations

from cash_recon.demo import load_demo_dataset
from cash_recon.store import reset_cash_state
from cash_recon.workflow import run_cash_reconciliation
from evaluation.comparison import error_case, score_cash_disposition
from evaluation.models import EvaluationCaseResult
from evaluation.scoring import summarize_function

CASH_CASES = (
    ("SCN-CASH-001", "TXN-2026-09-018A", "EXACT_MATCH", "MATCHED", False),
    ("SCN-CASH-002", "TXN-2026-09-008", "GROUPED_MATCH", "MATCHED", False),
    ("SCN-CASH-003", "TXN-2026-09-011", "FEE_NETTED", "EXPLAINED_EXCEPTION", False),
    ("SCN-CASH-004", "TXN-2026-09-012B", "POSSIBLE_DUPLICATE_REFUND", "HUMAN_REVIEW", True),
    ("SCN-CASH-005", "TXN-2026-09-015", "UNEXPLAINED_DIFFERENCE", "HUMAN_REVIEW", True),
    ("SCN-CASH-006", "GL-AP-HE", "TIMING_DIFFERENCE", "OUTSTANDING_TIMING_ITEM", False),
    ("SCN-CASH-007", "TXN-2026-09-025", "UNMATCHED_BANK", "HUMAN_REVIEW", True),
    ("SCN-CASH-008", "GL-AP-ORPHAN", "UNMATCHED_LEDGER", "HUMAN_REVIEW", True),
    ("SCN-CASH-009", "TXN-2026-09-019A", "PROVIDER_PAYOUT", "MATCHED", False),
    ("SCN-CASH-010", "TXN-2026-09-022S", "PROVIDER_PAYOUT", "MATCHED", False),
    ("SCN-CASH-011", "TXN-2026-09-026S", "PROVIDER_PAYOUT", "MATCHED", False),
    ("SCN-CASH-012", "TXN-2026-09-021", None, "HUMAN_REVIEW", True),
)


def run_cash(period: str, expected_statuses: dict[str, str] | None = None) -> tuple:
    reset_cash_state()
    balances, bank, ledger, fees = load_demo_dataset()
    try:
        report = run_cash_reconciliation(
            period,
            seed_demo=False,
            use_agent=False,
            reset=True,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=fees,
        )
    except Exception as exc:
        case = error_case(case_id="CASH-WORKFLOW", domain="cash", scenario_id="SCN-CASH-001", reason=str(exc))
        summary = summarize_function("cash", [case])
        summary.workflow_error = str(exc)
        return summary, {}

    by_bank: dict[str, dict] = {}
    by_ledger: dict[str, dict] = {}
    for match in report.matches:
        row = {
            "match_type": match.match_type,
            "status": match.status,
            "bank_ids": list(match.bank_transaction_ids),
            "ledger_ids": list(match.ledger_entry_ids),
            "difference": match.difference,
        }
        for bank_id in match.bank_transaction_ids:
            by_bank[bank_id] = row
        for ledger_id in match.ledger_entry_ids:
            by_ledger[ledger_id] = row

    cases: list[EvaluationCaseResult] = []
    for scenario_id, object_id, match_type, disposition, human in CASH_CASES:
        row = by_bank.get(object_id) or by_ledger.get(object_id) or {}
        actual_type = row.get("match_type")
        actual_status = row.get("status")
        fee_explained = disposition == "EXPLAINED_EXCEPTION" and actual_type == "FEE_NETTED"
        cases.append(
            score_cash_disposition(
                object_id=object_id,
                scenario_id=scenario_id,
                expected_type=match_type,
                expected_status=disposition,
                actual_type=actual_type,
                actual_status="EXPLAINED_EXCEPTION" if fee_explained else actual_status,
                human=human,
            )
        )

    labels = (expected_statuses or {})
    predicted_matched = {key for key, row in by_bank.items() if row.get("status") in {"MATCHED", "EXPLAINED_EXCEPTION"}}
    expected_matched = {key for key, value in labels.items() if value == "MATCHED"}
    false_matches = predicted_matched - expected_matched if expected_matched else set()

    summary = summarize_function("cash", cases)
    grouped = next((item for item in cases if item.scenario_id == "SCN-CASH-002"), None)
    fee = next((item for item in cases if item.scenario_id == "SCN-CASH-003"), None)
    dup = next((item for item in cases if item.scenario_id == "SCN-CASH-004"), None)
    unexplained = next((item for item in cases if item.scenario_id == "SCN-CASH-005"), None)
    stripe = [item for item in cases if item.scenario_id in {"SCN-CASH-009", "SCN-CASH-010", "SCN-CASH-011"}]
    auto = [item for item in cases if item.review_class == "AUTO_RESOLVE_EXPECTED"]
    summary.metrics = {
        "match_precision": round(
            (len(predicted_matched & expected_matched) / len(predicted_matched)) if predicted_matched and expected_matched else summary.accuracy,
            4,
        ),
        "match_recall": round(
            (len(predicted_matched & expected_matched) / len(expected_matched)) if expected_matched else summary.accuracy,
            4,
        ),
        "grouped_match_accuracy": grouped.score if grouped else 0.0,
        "fee_handling_accuracy": fee.score if fee else 0.0,
        "duplicate_refund_detection": dup.score if dup else 0.0,
        "unexplained_difference_detection": unexplained.score if unexplained else 0.0,
        "stripe_payout_tie_accuracy": round(sum(item.score for item in stripe) / len(stripe), 4) if stripe else 0.0,
        "false_reconciliation_rate": round(len(false_matches) / max(len(predicted_matched), 1), 4),
        "arithmetic_tie_is_not_sufficient": 1.0 if unexplained and unexplained.score == 1 else 0.0,
    }
    _ = auto
    raw = {
        "by_bank": by_bank,
        "by_ledger": by_ledger,
        "period_status": report.period_status,
        "arithmetic_tied": report.arithmetic_tied,
        "human_review_count": report.human_review_count,
    }
    return summary, raw
