"""Post-decision diagnostics. Warnings never overwrite the agent method."""

from __future__ import annotations

from functools import lru_cache

from accrual.estimation import EstimateContext, candidates_for, naive_recent_average_is_misleading
from accrual.models import EstimateCandidate
from accrual.policy import preferred_candidate


@lru_cache(maxsize=1)
def historical_method_mapes() -> dict[str, float]:
    from accrual.backtest import compute_backtest_metrics, run_backtest_case, select_backtest_invoices
    from accrual.cutoff import without_cutoff

    with without_cutoff():
        records = [run_backtest_case(item) for item in select_backtest_invoices()]
    metrics = compute_backtest_metrics(records)
    return {
        item.method: item.mean_absolute_percentage_error
        for item in metrics.by_method
        if item.mean_absolute_percentage_error is not None
    }


def method_diagnostics(
    *,
    agent_method: str | None,
    agent_status: str,
    context: EstimateContext,
    policy: EstimateCandidate | None = None,
) -> list[str]:
    """Return audit warnings. Empty when there is nothing to flag."""
    policy = policy if policy is not None else preferred_candidate(context)
    warnings: list[str] = []
    applicable = {item.method for item in candidates_for(context) if item.applicable}
    mapes = historical_method_mapes()

    if agent_status == "accrual_required" and agent_method and policy and policy.method:
        if agent_method != policy.method:
            warnings.append(
                f"DISAGREE: agent selected {agent_method}; evidence-type policy prefers {policy.method}."
            )
            agent_mape = mapes.get(agent_method)
            policy_mape = mapes.get(policy.method)
            if (
                agent_mape is not None
                and policy_mape is not None
                and agent_mape >= max(10.0, policy_mape * 2)
            ):
                warnings.append(
                    f"REVIEW_FLAG: selected method has historically weak performance "
                    f"({agent_method} MAPE {agent_mape:.1f}% vs {policy.method} {policy_mape:.1f}%)."
                )
        if (
            agent_method == "recent_average"
            and "seasonal_prior_year" in applicable
            and naive_recent_average_is_misleading(context)
        ):
            seasonal_mape = mapes.get("seasonal_prior_year")
            recent_mape = mapes.get("recent_average")
            extra = ""
            if recent_mape is not None and seasonal_mape is not None:
                extra = f" recent_average MAPE {recent_mape:.1f}% vs seasonal {seasonal_mape:.1f}%."
            warnings.append(
                "REVIEW_FLAG: selected method has historically weak performance "
                f"for this seasonal evidence pattern.{extra}"
            )
    return warnings
