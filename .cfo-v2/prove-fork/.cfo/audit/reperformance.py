"""Independent reconciliation re-performance.

Independent compute functions accept source evidence only. They do not take
an original operational conclusion. Comparison happens after compute.
"""

from __future__ import annotations

from ar.cash import generate_cash_candidates, policy_cash_decision
from ar.models import Customer, CustomerInvoice, CustomerPayment
from audit.models import PlantedReconciliation, ReperformanceRecord
from cash_recon.engine import propose_matches
from cash_recon.models import BankTransaction, FeeEvidence, LedgerEntry
from cash_recon.validate import expected_disposition

DEFAULT_TOLERANCE = 0.01


def _money(value: float | None) -> float:
    return round(float(value or 0), 2)


def _within(left: float, right: float, tolerance: float) -> bool:
    return abs(_money(left) - _money(right)) <= tolerance


def independent_cash_result(
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
    period: str,
    bank_ids: list[str],
    ledger_ids: list[str],
) -> dict:
    """Recompute a cash/Stripe match from source records only."""
    independent = propose_matches(bank, ledger, fees, period)
    wanted_bank = set(bank_ids)
    wanted_ledger = set(ledger_ids)
    match = next(
        (
            item
            for item in independent
            if wanted_bank & set(item.bank_transaction_ids) or wanted_ledger & set(item.ledger_entry_ids)
        ),
        None,
    )
    if match is None:
        return {
            "match_type": "UNMATCHED",
            "status": "HUMAN_REVIEW",
            "bank_amount": 0.0,
            "ledger_amount": 0.0,
            "difference": 0.0,
            "bank_transaction_ids": [],
            "ledger_entry_ids": [],
            "source_inputs": {
                "period": period,
                "bank_ids": list(bank_ids),
                "ledger_ids": list(ledger_ids),
            },
        }
    return {
        "match_type": match.match_type,
        "status": expected_disposition(match.match_type, provider_status=match.provider_status),
        "bank_amount": match.bank_amount,
        "ledger_amount": match.ledger_amount,
        "difference": match.difference,
        "bank_transaction_ids": list(match.bank_transaction_ids),
        "ledger_entry_ids": list(match.ledger_entry_ids),
        "candidate_id": match.candidate_id,
        "source_inputs": {
            "period": period,
            "bank_ids": list(match.bank_transaction_ids),
            "ledger_ids": list(match.ledger_entry_ids),
            "bank_amount": match.bank_amount,
            "ledger_amount": match.ledger_amount,
        },
    }


def independent_accrual_error(estimated_amount: float, actual_amount: float) -> dict:
    """Recompute accrual estimation error from source amounts only."""
    estimated = _money(estimated_amount)
    actual = _money(actual_amount)
    error = _money(actual - estimated)
    return {
        "estimated_amount": estimated,
        "actual_amount": actual,
        "estimation_error": error,
        "difference": error,
        "source_inputs": {"estimated_amount": estimated, "actual_amount": actual},
    }


def independent_ar_application(
    payment: CustomerPayment,
    invoices: list[CustomerInvoice],
    customers: list[Customer],
) -> dict:
    """Recompute AR cash application from remittance and open invoices only."""
    facts = generate_cash_candidates(payment, invoices=invoices, customers=customers)
    proposal = policy_cash_decision(facts)
    invoice_ids = [item.invoice_id for item in proposal.applications]
    return {
        "decision": proposal.decision,
        "invoice_ids": invoice_ids,
        "difference": 0,
        "confidence": proposal.confidence,
        "source_inputs": {
            "payment_id": payment.payment_id,
            "payment_amount": payment.amount,
            "remittance_text": payment.remittance_text,
            "candidate_count": len(facts.candidates),
        },
    }


def _compare_cash(original: dict, independent: dict, tolerance: float) -> list[str]:
    differences: list[str] = []
    if original.get("match_type") != independent.get("match_type"):
        differences.append(f"match_type {original.get('match_type')} vs {independent.get('match_type')}")
    if original.get("status") != independent.get("status"):
        differences.append(f"status {original.get('status')} vs {independent.get('status')}")
    if not _within(float(original.get("difference") or 0), float(independent.get("difference") or 0), tolerance):
        differences.append(f"difference {original.get('difference')} vs {independent.get('difference')}")
    return differences


def reperform_cash_match(
    planted: PlantedReconciliation,
    bank: list[BankTransaction],
    ledger: list[LedgerEntry],
    fees: list[FeeEvidence],
    *,
    audit_run_id: str,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ReperformanceRecord:
    independent_result = independent_cash_result(
        bank,
        ledger,
        fees,
        planted.period,
        planted.bank_transaction_ids,
        planted.ledger_entry_ids,
    )
    original_result = {
        "match_type": planted.original_match_type,
        "status": planted.original_status,
        "bank_amount": planted.original_bank_amount,
        "ledger_amount": planted.original_ledger_amount,
        "difference": planted.original_difference,
        "bank_transaction_ids": list(planted.bank_transaction_ids),
        "ledger_entry_ids": list(planted.ledger_entry_ids),
    }
    differences = _compare_cash(original_result, independent_result, tolerance)
    return ReperformanceRecord(
        record_id=f"RPF-{planted.reconciliation_id}",
        audit_run_id=audit_run_id,
        reconciliation_id=planted.reconciliation_id,
        recon_type=planted.recon_type,
        source_ids=list(dict.fromkeys([*planted.bank_transaction_ids, *planted.ledger_entry_ids])),
        original_result=original_result,
        independent_result=independent_result,
        differences=differences,
        tolerance=tolerance,
        agreed=not differences,
        result="PASS" if not differences else "FAIL",
        evidence_trace=[
            f"source:{item}" for item in [*planted.bank_transaction_ids, *planted.ledger_entry_ids]
        ],
        used_original_as_input=False,
    )


def reperform_accrual(
    planted: PlantedReconciliation,
    *,
    audit_run_id: str,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ReperformanceRecord:
    independent_result = independent_accrual_error(planted.estimated_amount or 0, planted.actual_amount or 0)
    original_error = _money(planted.original_error)
    original_result = {
        "estimated_amount": independent_result["estimated_amount"],
        "actual_amount": independent_result["actual_amount"],
        "estimation_error": original_error,
    }
    agreed = _within(independent_result["estimation_error"], original_error, tolerance)
    return ReperformanceRecord(
        record_id=f"RPF-{planted.reconciliation_id}",
        audit_run_id=audit_run_id,
        reconciliation_id=planted.reconciliation_id,
        recon_type="accrual",
        source_ids=[item for item in [planted.vendor, *planted.invoice_ids] if item],
        original_result=original_result,
        independent_result=independent_result,
        differences=[] if agreed else [f"estimation_error {original_error} vs {independent_result['estimation_error']}"],
        tolerance=tolerance,
        agreed=agreed,
        result="PASS" if agreed else "FAIL",
        evidence_trace=list(planted.invoice_ids),
        used_original_as_input=False,
    )


def reperform_ar_cash(
    planted: PlantedReconciliation,
    payment: CustomerPayment,
    invoices: list[CustomerInvoice],
    customers: list[Customer],
    *,
    audit_run_id: str,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ReperformanceRecord:
    independent_result = independent_ar_application(payment, invoices, customers)
    original_ids = list(planted.invoice_ids)
    original_decision = planted.original_decision or planted.original_status
    original_result = {"decision": original_decision, "invoice_ids": original_ids, "difference": 0}
    differences: list[str] = []
    if original_decision != independent_result["decision"]:
        differences.append(f"decision {original_decision} vs {independent_result['decision']}")
    if set(original_ids) != set(independent_result["invoice_ids"]):
        differences.append(f"invoices {original_ids} vs {independent_result['invoice_ids']}")
    agreed = not differences
    return ReperformanceRecord(
        record_id=f"RPF-{planted.reconciliation_id}",
        audit_run_id=audit_run_id,
        reconciliation_id=planted.reconciliation_id,
        recon_type="ar_cash",
        source_ids=[payment.payment_id, *independent_result["invoice_ids"]],
        original_result=original_result,
        independent_result=independent_result,
        differences=differences,
        tolerance=tolerance,
        agreed=agreed,
        result="PASS" if agreed else "FAIL",
        evidence_trace=[payment.payment_id, *independent_result["invoice_ids"]],
        used_original_as_input=False,
    )
