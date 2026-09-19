"""Deterministic evaluation against optional ground-truth labels."""

from __future__ import annotations

from cash_recon.demo import load_ground_truth
from cash_recon.models import BankTransaction, CashReconciliationReport, EvaluationMetrics


def evaluate_report(
    report: CashReconciliationReport,
    *,
    period_bank: list[BankTransaction] | None = None,
    ground_truth: dict | None = None,
) -> EvaluationMetrics:
    try:
        truth = ground_truth if ground_truth is not None else load_ground_truth()
    except FileNotFoundError:
        truth = {}
    labels = (truth or {}).get("labels") or {}
    expected_matched = set((truth or {}).get("matched_bank_ids") or [])
    expected_exceptions = set((truth or {}).get("exception_bank_ids") or [])

    by_bank: dict[str, list] = {}
    for match in report.matches:
        for bank_id in match.bank_transaction_ids:
            by_bank.setdefault(bank_id, []).append(match)

    period_bank_ids = [item.transaction_id for item in period_bank] if period_bank is not None else [
        bank_id for match in report.matches for bank_id in match.bank_transaction_ids
    ]

    exact = grouped = provider = 0
    unexplained = 0
    true_exceptions = 0
    false_matches = 0
    false_exception_flags = 0
    true_positives = 0

    for match in report.matches:
        if match.match_type == "EXACT_MATCH" and match.status == "MATCHED":
            exact += 1
        if match.match_type == "GROUPED_MATCH" and match.status == "MATCHED":
            grouped += 1
        if match.match_type == "PROVIDER_PAYOUT" and match.status == "MATCHED":
            provider += 1
        if match.match_type == "UNEXPLAINED_DIFFERENCE":
            unexplained += 1

    for bank_id in period_bank_ids:
        matches = by_bank.get(bank_id) or []
        primary = matches[0] if matches else None
        expected = labels.get(bank_id) or {}
        expected_type = expected.get("match_type")
        expected_disposition = expected.get("disposition")
        actual_type = primary.match_type if primary else None
        actual_status = primary.status if primary else None
        is_matched = actual_status in {"MATCHED", "EXPLAINED_EXCEPTION"}
        if bank_id in expected_matched:
            if is_matched and (not expected_type or actual_type == expected_type or actual_type in {"EXACT_MATCH", "GROUPED_MATCH", "PROVIDER_PAYOUT", "FEE_NETTED"}):
                true_positives += 1
            elif not is_matched:
                false_exception_flags += 1
        if bank_id in expected_exceptions:
            if actual_status == "HUMAN_REVIEW" or actual_type in {
                "UNEXPLAINED_DIFFERENCE",
                "POSSIBLE_DUPLICATE_REFUND",
                "POSSIBLE_DUPLICATE_BANK_TXN",
                "UNMATCHED_BANK",
            }:
                true_exceptions += 1
        if is_matched and expected_matched and bank_id not in expected_matched:
            false_matches += 1
        if expected_type and actual_type == expected_type and expected_disposition and actual_status == expected_disposition:
            pass

    predicted_matched = {
        bank_id
        for bank_id, rows in by_bank.items()
        if any(item.status in {"MATCHED", "EXPLAINED_EXCEPTION"} for item in rows)
    }
    if expected_matched:
        true_positives = len(predicted_matched & expected_matched)
        false_matches = len(predicted_matched - expected_matched)
        false_exception_flags = len(expected_matched - predicted_matched)
        true_exceptions = len(
            {
                bank_id
                for bank_id in expected_exceptions
                if any(item.status == "HUMAN_REVIEW" or item.match_type in {
                    "UNEXPLAINED_DIFFERENCE",
                    "POSSIBLE_DUPLICATE_REFUND",
                    "POSSIBLE_DUPLICATE_BANK_TXN",
                    "UNMATCHED_BANK",
                } for item in by_bank.get(bank_id, []))
            }
        )
        precision = true_positives / len(predicted_matched) if predicted_matched else 0.0
        recall = true_positives / len(expected_matched) if expected_matched else 0.0
        used_truth = True
    else:
        precision = 1.0 if not false_matches else 0.0
        recall = 1.0
        used_truth = False

    return EvaluationMetrics(
        period=report.period,
        total_bank_transactions=len(period_bank_ids),
        exact_matches=exact,
        grouped_matches=grouped,
        provider_matches=provider,
        true_exceptions=true_exceptions,
        false_matches=false_matches,
        false_exception_flags=false_exception_flags,
        unexplained_items=unexplained,
        human_review_count=report.human_review_count,
        precision=round(precision, 4),
        recall=round(recall, 4),
        arithmetic_tied=report.arithmetic_tied,
        ground_truth_used=used_truth,
    )


def format_metrics(metrics: EvaluationMetrics) -> str:
    tied = "PASS" if metrics.arithmetic_tied else "FAIL"
    return "\n".join(
        [
            f"Cash reconciliation evaluation — {metrics.period}",
            f"Total bank transactions: {metrics.total_bank_transactions}",
            f"Exact matches: {metrics.exact_matches}",
            f"Grouped matches: {metrics.grouped_matches}",
            f"Provider matches: {metrics.provider_matches}",
            f"True exceptions detected: {metrics.true_exceptions}",
            f"False matches: {metrics.false_matches}",
            f"False exception flags: {metrics.false_exception_flags}",
            f"Unexplained items: {metrics.unexplained_items}",
            f"Human-review count: {metrics.human_review_count}",
            f"Precision: {metrics.precision:.2%}",
            f"Recall: {metrics.recall:.2%}",
            f"Arithmetic tie-out: {tied}",
        ]
    )
