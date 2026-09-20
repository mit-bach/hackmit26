"""Deterministic ID factory. Same seed + sequence → same identifier."""

from __future__ import annotations

from collections import defaultdict


class IdFactory:
    """Stable prefixed counters. Callers never invent IDs by hand."""

    def __init__(self) -> None:
        self._seq: dict[str, int] = defaultdict(int)
        self._reserved: set[str] = set()

    def reserve(self, value: str) -> str:
        if value in self._reserved:
            raise ValueError(f"Duplicate reserved id {value}")
        self._reserved.add(value)
        return value

    def next(self, prefix: str, width: int = 3) -> str:
        self._seq[prefix] += 1
        value = f"{prefix}{self._seq[prefix]:0{width}d}"
        return self.reserve(value)

    def named(self, value: str) -> str:
        return self.reserve(value)

    def contains(self, value: str) -> bool:
        return value in self._reserved
