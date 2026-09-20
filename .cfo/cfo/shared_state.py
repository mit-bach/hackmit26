"""Process-wide shared canonical-state enablement. Default is on."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

_SHARED_STATE: ContextVar[bool] = ContextVar("cfo_shared_state", default=True)


def shared_state_enabled() -> bool:
    return _SHARED_STATE.get()


def set_shared_state(enabled: bool) -> None:
    _SHARED_STATE.set(bool(enabled))


@contextmanager
def shared_state_mode(enabled: bool):
    token = _SHARED_STATE.set(bool(enabled))
    try:
        yield
    finally:
        _SHARED_STATE.reset(token)
