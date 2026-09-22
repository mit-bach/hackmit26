"""Per-run Stripe evaluation control. Default preserves current policy behavior."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunControl:
    decision_mode: str = "policy"
    memory_enabled: bool = True
    use_llm: bool = False
    records: list[dict[str, Any]] = field(default_factory=list)

    def record(self, payload: dict[str, Any]) -> None:
        self.records.append(payload)


_CONTROL: ContextVar[RunControl] = ContextVar("stripe_run_control", default=RunControl())


def get_control() -> RunControl:
    return _CONTROL.get()


@contextmanager
def run_control(*, decision_mode: str = "policy", memory_enabled: bool = True, use_llm: bool = False):
    from memory.policy import memory_mode

    control = RunControl(decision_mode=decision_mode, memory_enabled=memory_enabled, use_llm=use_llm)
    token = _CONTROL.set(control)
    try:
        with memory_mode(memory_enabled):
            yield control
    finally:
        _CONTROL.reset(token)
