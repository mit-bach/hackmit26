from __future__ import annotations

from pathlib import Path

from models import ScheduleTrace
from scheduling.host import run_schedule_host
from scheduling.pool import candidates_from_pool

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"

__all__ = ["RUNS_DIR", "candidates_from_pool", "run_schedule_workflow"]


def run_schedule_workflow(
    *,
    chooser=None,
    computer_root: Path | None = None,
    runs_dir: Path | None = None,
    idempotency_key: str | None = None,
) -> ScheduleTrace:
    """Weekly pay-run host. Concurrence is a Handle to ctl-pay, not Payment Audit."""
    return run_schedule_host(
        chooser=chooser,
        computer_root=computer_root,
        runs_dir=runs_dir or RUNS_DIR,
        idempotency_key=idempotency_key,
    )
