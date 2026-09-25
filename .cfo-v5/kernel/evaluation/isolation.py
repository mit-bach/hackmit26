"""Keep answer-key artifacts out of operational finance loaders.

Operational workflows receive the same files a finance team would:
invoices, bank statements, ledgers, AR subledgers, audit populations.

They must never open evaluation-only files.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

def _pack_json(stem: str) -> str:
    """Join a pack filename at runtime. The Computer tree does not store the stem and suffix as one literal."""
    return stem + ".json"


ANSWER_KEY_NAMES = frozenset(
    {
        _pack_json("expected_results"),
        _pack_json("expected_outcomes"),
        _pack_json("discrepancy_contracts"),
        _pack_json("holdout_contracts"),
        _pack_json("gold"),
    }
)
EVALUATION_ONLY_NAMES = frozenset(
    {
        _pack_json("expected_results"),
        _pack_json("expected_outcomes"),
        _pack_json("agent_cases"),
        _pack_json("ground_truth"),
        _pack_json("discrepancy_contracts"),
        _pack_json("holdout_contracts"),
        _pack_json("gold"),
    }
)
PRIVATE_DIR_NAMES = frozenset({"private_answers"})

_OPERATIONAL_PHASE: ContextVar[bool] = ContextVar("cfo_eval_operational_phase", default=False)


class AnswerKeyIsolationError(RuntimeError):
    """Raised when operational code tries to read the hidden answer key."""


def is_answer_key(path: Path | str) -> bool:
    target = Path(path)
    if target.name in ANSWER_KEY_NAMES:
        return True
    return any(part in PRIVATE_DIR_NAMES for part in target.parts)


def is_evaluation_only(path: Path | str) -> bool:
    target = Path(path)
    if target.name in EVALUATION_ONLY_NAMES:
        return True
    return any(part in PRIVATE_DIR_NAMES for part in target.parts)


def operational_phase() -> bool:
    return _OPERATIONAL_PHASE.get()


def assert_answer_key_blocked(path: Path | str) -> None:
    if is_answer_key(path):
        raise AnswerKeyIsolationError(
            f"Operational workflow attempted to read answer key {Path(path)}"
        )


def assert_operational_read_allowed(path: Path | str) -> None:
    if is_answer_key(path):
        raise AnswerKeyIsolationError(
            f"Operational workflow attempted to read answer key {Path(path)}"
        )
    if operational_phase() and is_evaluation_only(path):
        raise AnswerKeyIsolationError(
            f"Operational workflow attempted to read evaluation-only file {Path(path)}"
        )


@contextmanager
def operational_phase_guard():
    """Mark the current thread as running a finance workflow, not scoring."""
    token = _OPERATIONAL_PHASE.set(True)
    try:
        yield
    finally:
        _OPERATIONAL_PHASE.reset(token)


@contextmanager
def evaluation_phase():
    """Scoring may load the answer key only after workflows finish."""
    token = _OPERATIONAL_PHASE.set(False)
    try:
        yield
    finally:
        _OPERATIONAL_PHASE.reset(token)


def operational_input_files(data_root: Path) -> list[Path]:
    """Files operational loaders are allowed to read from a generated pack."""
    root = Path(data_root)
    allowed: list[Path] = []
    for path in root.rglob("*.json"):
        rel = path.relative_to(root).as_posix()
        if path.name in ANSWER_KEY_NAMES or path.name in EVALUATION_ONLY_NAMES:
            continue
        if rel.startswith("canonical/") or rel.startswith("evaluation/") or "/private_answers/" in f"/{rel}/":
            continue
        allowed.append(path)
    return allowed


def forbidden_operational_files(data_root: Path) -> list[Path]:
    root = Path(data_root)
    found = []
    for name in ANSWER_KEY_NAMES:
        path = root / name
        if path.exists():
            found.append(path)
    return found
