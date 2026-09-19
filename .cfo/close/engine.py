"""Single public month-end close engine.

Every close CLI entrypoint must call these functions. The older
``run_cfo_close`` packet in ``close.orchestrator`` is an AP/accrual/schedule
coordinator used by tests; it is not a period-close state machine.
"""

from __future__ import annotations

from close.month_end import (
    finalize_close,
    load_state,
    reopen_period,
    rerun_affected,
    run_month_end,
    save_state,
)

CANONICAL_CLOSE_MODULE = "close.month_end"
CANONICAL_RUN = run_month_end
CANONICAL_STATE_ATTR = "STATE_DIR"

__all__ = [
    "CANONICAL_CLOSE_MODULE",
    "CANONICAL_RUN",
    "CANONICAL_STATE_ATTR",
    "finalize_close",
    "load_state",
    "reopen_period",
    "rerun_affected",
    "run_month_end",
    "save_state",
]
