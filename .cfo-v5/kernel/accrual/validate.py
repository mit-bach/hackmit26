"""Reject inconsistent Accrual Agent output instead of silently rewriting it."""

from __future__ import annotations

from accrual.estimation import money
from accrual.models import AccrualDecision, EstimateCandidate, EstimationMethod

AMOUNT_TOLERANCE = 0.01

STATUS_LABELS = {
    "accrual_required": "ACCRUE",
    "no_accrual_needed": "SKIP",
    "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.upper())


def candidate_for(method: str | None, candidates: list[EstimateCandidate]) -> EstimateCandidate | None:
    if not method:
        return None
    for item in candidates:
        if item.method == method:
            return item
    return None


def amounts_match(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return False
    return abs(money(left) - money(right)) <= AMOUNT_TOLERANCE


def validate_agent_decision(
    decision: AccrualDecision,
    candidates: list[EstimateCandidate],
) -> list[str]:
    """Return validation errors. An empty list means the structured output is consistent."""
    errors: list[str] = []
    known_methods = set(EstimationMethod.__args__)  # type: ignore[attr-defined]

    if decision.status == "accrual_required":
        if not decision.estimation_method:
            errors.append("ACCRUE requires a selected estimation method.")
        elif decision.estimation_method not in known_methods:
            errors.append(f"Unknown estimation method {decision.estimation_method!r}.")
        if decision.estimated_amount is None:
            errors.append("ACCRUE requires a numeric estimated_amount.")
        elif decision.estimated_amount <= 0:
            errors.append("Negative or zero accruals are rejected.")
        match = candidate_for(decision.estimation_method, candidates)
        if decision.estimation_method:
            if match is None:
                errors.append(
                    f"Method {decision.estimation_method} is not a candidate for this vendor."
                )
            elif not match.applicable or match.amount is None:
                errors.append(
                    f"Method {decision.estimation_method} is not an applicable deterministic candidate."
                )
            elif decision.estimated_amount is not None and not amounts_match(
                decision.estimated_amount, match.amount
            ):
                errors.append(
                    f"Amount {decision.estimated_amount} does not match Python "
                    f"{decision.estimation_method} candidate {match.amount}."
                )
    else:
        if decision.journal_entry is not None:
            errors.append(f"{status_label(decision.status)} cannot include a journal entry.")
        if decision.estimated_amount is not None:
            errors.append(f"{status_label(decision.status)} cannot include an estimated amount.")
        if decision.accrual_id:
            errors.append(f"{status_label(decision.status)} cannot book an accrual.")
    return errors


def failed_safe_decision(decision: AccrualDecision, errors: list[str]) -> AccrualDecision:
    """Keep the vendor in the close, but do not book from a malformed decision."""
    return decision.model_copy(
        update={
            "status": "insufficient_evidence",
            "estimated_amount": None,
            "estimation_method": None,
            "journal_entry": None,
            "accrual_id": None,
            "reasoning_summary": (
                f"{decision.reasoning_summary} Rejected malformed agent output: "
                + "; ".join(errors)
            ).strip(),
        }
    )
