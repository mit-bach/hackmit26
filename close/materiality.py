"""Configurable close materiality. Never used to auto-explain a break."""

from __future__ import annotations

import json
from pathlib import Path

from close.models import MaterialityPolicy

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "data" / "close" / "materiality.json"
REPORTING_PATH = ROOT / "data" / "reporting" / "assumptions.json"


def load_materiality() -> MaterialityPolicy:
    payload: dict = {}
    source = "defaults"
    if REPORTING_PATH.exists():
        reporting = json.loads(REPORTING_PATH.read_text())
        if isinstance(reporting, dict) and "materiality_abs" in reporting:
            payload["close_materiality_dollars"] = float(reporting["materiality_abs"])
            source = "data/reporting/assumptions.json"
    if POLICY_PATH.exists():
        close_policy = json.loads(POLICY_PATH.read_text())
        if isinstance(close_policy, dict):
            payload.update(close_policy)
            source = "data/close/materiality.json"
    payload["source"] = source
    payload.setdefault(
        "note",
        "Materiality never auto-explains an unexplained difference.",
    )
    return MaterialityPolicy.model_validate(payload)


def materiality_explains(amount: float, policy: MaterialityPolicy | None = None) -> bool:
    """Always false. Small unexplained items remain visible."""
    _ = amount, policy
    return False
