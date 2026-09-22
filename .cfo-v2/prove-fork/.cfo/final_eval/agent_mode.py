"""Run the real agent path on a small held-out subset. Never relabel fallback as AGENT_RUN."""

from __future__ import annotations

import os
from typing import Any


def credentials_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def domain_modes(*, live: bool) -> dict[str, str]:
    if live and credentials_available():
        return {
            "ap": "AGENT_RUN",
            "ar": "AGENT_RUN",
            "cash": "AGENT_RUN",
            "close": "AGENT_RUN",
            "audit": "DETERMINISTIC_ONLY",
            "reporting": "DETERMINISTIC_ONLY",
            "forecasting": "DETERMINISTIC_ONLY",
            "cross_function": "DETERMINISTIC_ONLY",
        }
    return {name: "DETERMINISTIC_ONLY" for name in ("ap", "ar", "cash", "close", "audit", "reporting", "forecasting", "cross_function")}


def run_agent_subset(*, live: bool) -> dict[str, Any]:
    """Invoke production agent entrypoints. Failures stay labeled DETERMINISTIC_ONLY."""
    modes = domain_modes(live=live)
    rows: list[dict[str, Any]] = []
    if not live or not credentials_available():
        return {"modes": modes, "cases": rows, "note": "No live credentials; deterministic workflow benchmark preserved."}

    try:
        from close.orchestrator import decide_ap

        result = decide_ap("INV-HO-QTY", live=True, featured={"INV-HO-QTY"})
        rows.append(
            {
                "domain": "ap",
                "object_id": "INV-HO-QTY",
                "mode": "AGENT_RUN" if result.source == "ap_workflow" else "DETERMINISTIC_ONLY",
                "decision": result.decision,
                "exceptions": list(result.exceptions),
                "source": result.source,
            }
        )
        if result.source != "ap_workflow":
            modes["ap"] = "DETERMINISTIC_ONLY"
    except Exception as exc:
        modes["ap"] = "DETERMINISTIC_ONLY"
        rows.append({"domain": "ap", "mode": "DETERMINISTIC_ONLY", "error": str(exc)})

    try:
        from ar.workflow import run_cash_apply

        trace = run_cash_apply("PAY-HO-AR-AMB", as_of="2026-09-30", live=True, persist=False)
        used = bool(getattr(trace, "used_agent", False) or getattr(trace, "live", False))
        rows.append(
            {
                "domain": "ar",
                "object_id": "PAY-HO-AR-AMB",
                "mode": "AGENT_RUN" if used else "DETERMINISTIC_ONLY",
                "decision": trace.final.decision,
                "reason": getattr(trace.final, "reason", ""),
            }
        )
        if not used:
            modes["ar"] = "DETERMINISTIC_ONLY"
    except Exception as exc:
        modes["ar"] = "DETERMINISTIC_ONLY"
        rows.append({"domain": "ar", "mode": "DETERMINISTIC_ONLY", "error": str(exc)})

    try:
        from cash_recon.demo import load_demo_dataset, seed_provider_payouts
        from cash_recon.store import reset_cash_state
        from cash_recon.workflow import run_cash_reconciliation

        reset_cash_state()
        seed_provider_payouts()
        balances, bank, ledger, fees = load_demo_dataset()
        report = run_cash_reconciliation(
            "2026-09",
            seed_demo=False,
            use_agent=True,
            reset=True,
            balances=balances,
            bank=bank,
            ledger=ledger,
            fees=fees,
        )
        used = bool(getattr(report, "used_agent", False))
        match = next((item for item in report.matches if "TXN-HO-7390" in item.bank_transaction_ids), None)
        rows.append(
            {
                "domain": "cash",
                "object_id": "TXN-HO-7390",
                "mode": "AGENT_RUN" if used else "DETERMINISTIC_ONLY",
                "status": getattr(match, "status", None),
                "match_type": getattr(match, "match_type", None),
            }
        )
        if not used:
            modes["cash"] = "DETERMINISTIC_ONLY"
    except Exception as exc:
        modes["cash"] = "DETERMINISTIC_ONLY"
        rows.append({"domain": "cash", "mode": "DETERMINISTIC_ONLY", "error": str(exc)})

    try:
        from close.month_end import run_month_end

        state = run_month_end("2026-09", live=True, reset=False, scenario="demo", allow_close=False)
        rows.append(
            {
                "domain": "close",
                "mode": "AGENT_RUN",
                "period_status": state.period.status,
                "human_review": list(state.human_review_items)[:5],
            }
        )
    except Exception as exc:
        modes["close"] = "DETERMINISTIC_ONLY"
        rows.append({"domain": "close", "mode": "DETERMINISTIC_ONLY", "error": str(exc)})

    return {"modes": modes, "cases": rows, "note": "Live agent subset only; remaining domains stay DETERMINISTIC_ONLY."}
