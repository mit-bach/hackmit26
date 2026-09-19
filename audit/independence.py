"""Prove re-performance does not use the original operational conclusion as input."""

from __future__ import annotations

import inspect

from audit.dataset import AuditDataset, load_dataset
from audit.reperformance import (
    independent_accrual_error,
    independent_ar_application,
    independent_cash_result,
    reperform_accrual,
    reperform_ar_cash,
    reperform_cash_match,
)


INDEPENDENT_FUNCTIONS = (
    independent_cash_result,
    independent_accrual_error,
    independent_ar_application,
)


def independent_signatures_exclude_original() -> list[str]:
    """Return function names that unexpectedly accept an original conclusion."""
    blocked = []
    forbidden = {
        "original",
        "original_result",
        "original_status",
        "original_match_type",
        "original_difference",
        "original_decision",
        "original_error",
        "planted",
    }
    for fn in INDEPENDENT_FUNCTIONS:
        names = set(inspect.signature(fn).parameters)
        if names & forbidden:
            blocked.append(fn.__name__)
    return blocked


def _same_independent(before, after) -> bool:
    return before.independent_result == after.independent_result


def prove_bank_independence(dataset: AuditDataset, audit_run_id: str = "IND-BANK") -> dict:
    planted = next(item for item in dataset.reconciliations if item.reconciliation_id == "REC-AUD-AGREE")
    before = reperform_cash_match(
        planted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    corrupted = planted.model_copy(update={"original_status": "UNMATCHED", "original_match_type": "UNMATCHED_BANK"})
    after = reperform_cash_match(
        corrupted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    return {
        "name": "bank_reconciliation",
        "reconciliation_id": planted.reconciliation_id,
        "used_original_as_input": before.used_original_as_input or after.used_original_as_input,
        "independent_unchanged": _same_independent(before, after),
        "before_agreed": before.agreed,
        "after_agreed": after.agreed,
        "disagreement_detected": before.agreed and not after.agreed,
        "passed": (
            not before.used_original_as_input
            and not after.used_original_as_input
            and _same_independent(before, after)
            and before.agreed
            and not after.agreed
        ),
    }


def prove_stripe_independence(dataset: AuditDataset, audit_run_id: str = "IND-STRIPE") -> dict:
    planted = next(item for item in dataset.reconciliations if item.reconciliation_id == "REC-AUD-STRIPE")
    before = reperform_cash_match(
        planted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    corrupted = planted.model_copy(
        update={
            "original_difference": 12.40,
            "original_ledger_amount": planted.original_bank_amount - 12.40,
            "original_match_type": "FEE_NETTED",
        }
    )
    after = reperform_cash_match(
        corrupted, dataset.bank, dataset.ledger, dataset.fees, audit_run_id=audit_run_id
    )
    return {
        "name": "stripe_reconciliation",
        "reconciliation_id": planted.reconciliation_id,
        "used_original_as_input": before.used_original_as_input or after.used_original_as_input,
        "independent_unchanged": _same_independent(before, after),
        "before_agreed": before.agreed,
        "after_agreed": after.agreed,
        "disagreement_detected": before.agreed and not after.agreed,
        "passed": (
            not before.used_original_as_input
            and not after.used_original_as_input
            and _same_independent(before, after)
            and before.agreed
            and not after.agreed
        ),
    }


def prove_accrual_independence(dataset: AuditDataset, audit_run_id: str = "IND-ACCRUAL") -> dict:
    planted = next(
        item for item in dataset.reconciliations if item.reconciliation_id == "REC-AUD-ACCRUAL-AGREE"
    )
    before = reperform_accrual(planted, audit_run_id=audit_run_id)
    corrupted = planted.model_copy(update={"original_error": 12.40})
    after = reperform_accrual(corrupted, audit_run_id=audit_run_id)
    return {
        "name": "accrual_reperformance",
        "reconciliation_id": planted.reconciliation_id,
        "used_original_as_input": before.used_original_as_input or after.used_original_as_input,
        "independent_unchanged": _same_independent(before, after),
        "before_agreed": before.agreed,
        "after_agreed": after.agreed,
        "disagreement_detected": before.agreed and not after.agreed,
        "passed": (
            not before.used_original_as_input
            and not after.used_original_as_input
            and _same_independent(before, after)
            and before.agreed
            and not after.agreed
        ),
    }


def prove_ar_independence(dataset: AuditDataset, audit_run_id: str = "IND-AR") -> dict:
    planted = next(item for item in dataset.reconciliations if item.reconciliation_id == "REC-AUD-AR-AGREE")
    payment = dataset.ar_payments[planted.payment_id or ""]
    before = reperform_ar_cash(
        planted,
        payment,
        dataset.ar_invoices,
        dataset.ar_customers,
        audit_run_id=audit_run_id,
    )
    corrupted = planted.model_copy(update={"invoice_ids": ["INV-AR-AUD-002"], "original_decision": "AUTO_APPLY"})
    after = reperform_ar_cash(
        corrupted,
        payment,
        dataset.ar_invoices,
        dataset.ar_customers,
        audit_run_id=audit_run_id,
    )
    return {
        "name": "ar_cash_application",
        "reconciliation_id": planted.reconciliation_id,
        "used_original_as_input": before.used_original_as_input or after.used_original_as_input,
        "independent_unchanged": _same_independent(before, after),
        "before_agreed": before.agreed,
        "after_agreed": after.agreed,
        "disagreement_detected": before.agreed and not after.agreed,
        "passed": (
            not before.used_original_as_input
            and not after.used_original_as_input
            and _same_independent(before, after)
            and before.agreed
            and not after.agreed
        ),
    }


def run_independence_suite(dataset: AuditDataset | None = None) -> list[dict]:
    data = dataset or load_dataset("2026-09")
    return [
        prove_bank_independence(data),
        prove_stripe_independence(data),
        prove_ar_independence(data),
        prove_accrual_independence(data),
    ]
