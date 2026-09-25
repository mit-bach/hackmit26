"""Process-wide memory enablement. Default is on; evals can disable retrieval."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

_MEMORY_ENABLED: ContextVar[bool] = ContextVar("cfo_memory_enabled", default=True)


def memory_enabled() -> bool:
    return _MEMORY_ENABLED.get()


def set_memory_enabled(enabled: bool) -> None:
    _MEMORY_ENABLED.set(bool(enabled))


@contextmanager
def memory_mode(enabled: bool):
    token = _MEMORY_ENABLED.set(bool(enabled))
    try:
        yield
    finally:
        _MEMORY_ENABLED.reset(token)
