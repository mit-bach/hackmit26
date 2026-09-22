"""Local multi-run live-agent evaluation. Not part of the normal pytest suite."""

from __future__ import annotations

from collections import Counter

from accrual.ledger import isolated_ledger
from accrual.models import LiveEvalReport, LiveEvalTrial, LiveEvalVendorSummary
from accrual.trace import TRACES_ROOT, new_run_id
from accrual.workflow import _run_vendor

DEFAULT_VENDORS = [
    "Aether Compute",
    "Harbor Electric",
    "Helios Hardware",
    "NewForge Consulting",
]


def run_live_eval(period: str, runs: int = 5, vendors: list[str] | None = None) -> LiveEvalReport:
    vendors = vendors or list(DEFAULT_VENDORS)
    runs = max(1, int(runs))
    run_id = new_run_id()
    directory = TRACES_ROOT / "eval-live" / run_id
    trials: list[LiveEvalTrial] = []
    with isolated_ledger(directory / "ledger"):
        for index in range(1, runs + 1):
            for vendor in vendors:
                print(f"Eval run {index}/{runs}: {vendor}...", flush=True)
                decision, _trace = _run_vendor(vendor, period, run_id=f"{run_id}-r{index}")
                trials.append(
                    LiveEvalTrial(
                        vendor=vendor,
                        run=index,
                        status=decision.status,
                        method=decision.estimation_method,
                        amount=decision.estimated_amount,
                    )
                )
    summaries = []
    for vendor in vendors:
        rows = [item for item in trials if item.vendor == vendor]
        method_counts = Counter(item.method or item.status for item in rows)
        status_counts = Counter(item.status for item in rows)
        summaries.append(
            LiveEvalVendorSummary(
                vendor=vendor,
                trials=len(rows),
                method_counts=dict(method_counts),
                status_counts=dict(status_counts),
            )
        )
    report = LiveEvalReport(
        period=period,
        runs=runs,
        vendors=vendors,
        trials=trials,
        summaries=summaries,
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "results.json"
    path.write_text(report.model_dump_json(indent=2) + "\n")
    report.trace_path = str(path)
    return report
