"""Peer Handle destinations for the grain Bots, including World as the simulated mailbox.

Source of truth: office/computer/cfo/handle-map.json.
A peer Handle is not approval. Accept is not complete.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

GRAIN_SLUGS: tuple[str, ...] = (
    "email",
    "stripe",
    "bank",
    "books",
    "world",
    "ap",
    "pay",
    "apply",
    "collect",
    "cash",
    "close",
    "story",
    "ctl-pay",
    "ctl-cash",
    "ctl-books",
    "audit",
)

SAMPLE_DATA_DISPLAY_NAMES: frozenset[str] = frozenset(
    {
        "AP/AR Sample Data Agent",
        "Audit Controls Sample Data Agent",
        "Cash Recon Sample Data Agent",
        "Close Sample Data Agent",
        "Reporting Forecasting Sample Data Agent",
    }
)

HANDLE_MAP_PATH = (
    Path(__file__).resolve().parent / "computer" / "cfo" / "handle-map.json"
)


@lru_cache(maxsize=1)
def load_handle_map() -> dict[str, Any]:
    raw = json.loads(HANDLE_MAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("edges"), list):
        raise ValueError("handle-map.json must have an edges array")
    return raw


def destination(from_slug: str, when: str) -> tuple[str, str]:
    for edge in load_handle_map()["edges"]:
        if edge.get("from") == from_slug and edge.get("when") == when:
            return str(edge["to"]), str(edge["profile"])
    raise KeyError(f"no Handle edge for {from_slug}/{when}")


def all_destination_slugs() -> set[str]:
    out: set[str] = set()
    for edge in load_handle_map()["edges"]:
        out.add(str(edge["from"]))
        out.add(str(edge["to"]))
    return out


def bot_id_for_slug(slug: str) -> str:
    return f"bot_{slug.replace('-', '_')}"
