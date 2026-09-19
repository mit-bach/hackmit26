"""Accrual Agent: estimate and book expenses incurred but not yet invoiced."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accrual.workflow import run_accrual_workflow, run_demo, run_reconcile_workflow

__all__ = ["run_accrual_workflow", "run_demo", "run_reconcile_workflow"]


def __getattr__(name: str):
    if name in __all__:
        from accrual import workflow

        return getattr(workflow, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
