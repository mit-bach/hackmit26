"""Deterministic audit sampling. The LLM never chooses the IDs."""

from __future__ import annotations

import random
from datetime import datetime, timezone

from audit.models import PopulationItem, SampleRecord

RISK_SIGNALS = (
    "large_dollar",
    "round_number",
    "duplicate",
    "manual_journal",
    "posted_after_close",
    "self_approval",
    "unusual_vendor",
    "reconciliation_exception",
    "missing_support",
    "late_posting",
    "new_vendor",
    "control_failure",
)

DEFAULT_LARGE_AMOUNT = 10000.0


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_bool(value) -> bool:
    return bool(value)


def score_risk(
    item: PopulationItem,
    criteria: list[str] | None = None,
    *,
    large_amount: float = DEFAULT_LARGE_AMOUNT,
) -> float:
    """Deterministic risk score from structured attributes only."""
    wanted = set(criteria or RISK_SIGNALS)
    attrs = item.attributes
    score = 0.0
    if "large_dollar" in wanted and item.amount >= large_amount:
        score += 3.0 + min(item.amount / large_amount, 10.0)
    if "round_number" in wanted and _as_bool(attrs.get("round_number")):
        score += 2.0
    if "duplicate" in wanted and _as_bool(attrs.get("duplicate")):
        score += 4.0
    if "manual_journal" in wanted and _as_bool(attrs.get("manual_journal")):
        score += 1.5
    if "posted_after_close" in wanted and _as_bool(attrs.get("posted_after_close")):
        score += 4.0
    if "self_approval" in wanted and _as_bool(attrs.get("self_approval")):
        score += 4.0
    if "unusual_vendor" in wanted and _as_bool(attrs.get("unusual_vendor")):
        score += 2.0
    if "reconciliation_exception" in wanted and _as_bool(attrs.get("reconciliation_exception")):
        score += 3.0
    if "missing_support" in wanted and _as_bool(attrs.get("missing_support")):
        score += 2.5
    if "late_posting" in wanted and _as_bool(attrs.get("late_posting")):
        score += 1.5
    if "new_vendor" in wanted and _as_bool(attrs.get("new_vendor")):
        score += 2.0
    if "control_failure" in wanted and _as_bool(attrs.get("control_failure")):
        score += 5.0
    return round(score, 4)


def sample_population(
    population: list[PopulationItem],
    *,
    sample_size: int,
    method: str,
    seed: int,
    audit_run_id: str,
    period: str,
    population_name: str,
    risk_criteria: list[str] | None = None,
    large_amount: float = DEFAULT_LARGE_AMOUNT,
    timestamp: str | None = None,
) -> SampleRecord:
    known = {item.object_id for item in population}
    eligible = [item.object_id for item in population]
    size = max(0, min(int(sample_size), len(eligible)))
    criteria = list(risk_criteria or RISK_SIGNALS)
    scores = {
        item.object_id: score_risk(item, criteria, large_amount=large_amount) for item in population
    }

    if method == "random":
        rng = random.Random(seed)
        chosen = rng.sample(eligible, size) if size else []
    elif method == "risk_based":
        ranked = sorted(population, key=lambda item: (-scores[item.object_id], item.object_id))
        high_risk = [item.object_id for item in ranked if scores[item.object_id] > 0]
        chosen = high_risk[:size]
        if len(chosen) < size:
            remaining = [item.object_id for item in ranked if item.object_id not in chosen]
            rng = random.Random(seed)
            extra = rng.sample(remaining, min(size - len(chosen), len(remaining))) if remaining else []
            chosen.extend(extra)
    else:
        raise ValueError(f"Unknown sampling method {method!r}")

    if any(item not in known for item in chosen):
        raise RuntimeError("Sampler produced an ID that is not in the population")

    return SampleRecord(
        sample_id=f"SMP-{population_name}-{method}-{seed}",
        audit_run_id=audit_run_id,
        population_name=population_name,
        population_size=len(population),
        eligible_ids=list(eligible),
        sampling_method=method,  # type: ignore[arg-type]
        seed=seed,
        risk_criteria=criteria if method == "risk_based" else [],
        sample_size=len(chosen),
        sampled_ids=list(chosen),
        timestamp=timestamp or _now(),
        period=period,
        risk_scores={key: scores[key] for key in chosen},
    )
