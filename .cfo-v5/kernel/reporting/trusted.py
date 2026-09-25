"""Trusted cash is the forecast starting balance. Unreconciled GL cash is not."""

from __future__ import annotations

import json
import os
from pathlib import Path

from harness_handles import default_computer_root

UNLOCKED = "UNLOCKED"


def computer_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("HARNESS_COMPUTER")
    if env:
        return Path(env)
    return default_computer_root()


def trusted_cash_path(period: str, computer: Path | None = None) -> Path:
    return computer_root(computer) / "runs" / "cash" / "trusted" / f"{period}.json"


def load_trusted_cash(period: str, computer: Path | None = None) -> dict:
    path = trusted_cash_path(period, computer)
    if not path.is_file():
        return {
            "found": False,
            "period": period,
            "trusted": False,
            "forecast_may_start": False,
            "kernel_allow": False,
            "ctl_cash": "MISSING",
            "reasons": ["no trusted cash packet; 04 has not handed trusted cash"],
            "packet_path": str(path),
            "beginning_cash": None,
            "source": "missing",
        }
    raw = json.loads(path.read_text())
    trusted = bool(raw.get("trusted")) and bool(raw.get("forecast_may_start", raw.get("trusted")))
    reasons = list(raw.get("reasons") or [])
    if not trusted and not reasons:
        reasons.append("trusted cash packet is not trusted")
    amount = raw.get("beginning_cash")
    if amount is None:
        amount = raw.get("trusted_balance")
    if amount is None:
        amount = raw.get("ending_cash")
    return {
        "found": True,
        "period": period,
        "trusted": trusted,
        "forecast_may_start": trusted,
        "kernel_allow": bool(raw.get("kernel_allow")),
        "ctl_cash": raw.get("ctl_cash") or "",
        "reasons": reasons,
        "packet_path": str(path),
        "beginning_cash": amount if trusted else None,
        "unexplained_difference": raw.get("unexplained_difference"),
        "unexplained_difference_minor": raw.get("unexplained_difference_minor"),
        "period_status": raw.get("period_status") or "",
        "source": "trusted_cash" if trusted else "untrusted_packet",
        "label": None if trusted else UNLOCKED,
    }


def forecast_starting_balance(period: str, computer: Path | None = None) -> dict:
    """Refuse unreconciled GL cash. Trusted cash from cash Bot only."""
    packet = load_trusted_cash(period, computer)
    if packet["forecast_may_start"] and packet["beginning_cash"] is not None:
        return packet
    packet["forecast_may_start"] = False
    packet["beginning_cash"] = None
    packet["refused"] = True
    packet["label"] = UNLOCKED
    if "unreconciled GL cash is not trusted cash" not in packet["reasons"]:
        packet["reasons"].append("unreconciled GL cash is not trusted cash")
    return packet
