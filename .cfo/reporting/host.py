"""Bot story host. Writes flux / forecast / board packets. Does not own the books.

If lock_status is not CLOSED, every number is labeled UNLOCKED.
Forecast starting balance is trusted cash from cash Bot. Unreconciled GL
cash is not trusted cash. Kernel forecast snapshots stay create-only.
"""

from __future__ import annotations

import json
from pathlib import Path

from close.period_lock import period_status
from harness_handles import default_computer_root, write_peer_handle
from reporting.store import configure_paths as configure_reporting_store
from reporting.trusted import forecast_starting_balance
from reporting.unlocked import UNLOCKED, lock_is_closed, prefix_unlocked, stamp_amounts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n")


def _choose_flux_sentence(explanation) -> str:
    """Pick the lead sentence among Kernel contributors. Do not invent a number."""
    verified = [item for item in explanation.contributors if item.kind == "verified"]
    likely = [item for item in explanation.contributors if item.kind == "likely"]
    lead = verified[0] if verified else (likely[0] if likely else None)
    if lead is None:
        if abs(explanation.unexplained_amount) > explanation.residual_tolerance:
            return (
                f"Unexplained residual {explanation.unexplained_amount:+,.2f} "
                "has no supported transaction explanation."
            )
        return explanation.narrative
    evidence = ""
    if lead.source_transaction_ids:
        evidence = lead.source_transaction_ids[0]
    elif lead.evidence_refs:
        evidence = lead.evidence_refs[0]
    return (
        f"{lead.label} {lead.amount:+,.2f} is the lead Kernel contributor "
        f"(evidence {evidence or lead.label})."
    )


def run_story_host(
    computer: Path | None = None,
    period: str = "2026-09",
    *,
    as_of: str = "",
    lock_status: str = "",
    close_pack_path: str = "",
) -> dict:
    computer = Path(computer) if computer is not None else default_computer_root()
    computer.mkdir(parents=True, exist_ok=True)
    configure_reporting_store(computer / "runs" / "reporting")
    as_of = as_of or f"{period}-30"
    if not lock_status:
        lock_status = period_status(period)
        if lock_status == "OPEN" and close_pack_path:
            pack_file = computer / close_pack_path
            if pack_file.is_file():
                pack = json.loads(pack_file.read_text())
                lock_status = pack.get("status") or lock_status
    unlocked = not lock_is_closed(lock_status)
    prefix = f"workspace/story/{period}"
    trusted = forecast_starting_balance(period, computer)

    wake = {
        "period": period,
        "as_of": as_of,
        "lock_status": lock_status,
        "close_pack_path": close_pack_path,
        "unlocked": unlocked,
        "label": UNLOCKED if unlocked else "",
    }
    _write_json(computer / f"{prefix}/wake.json", wake)

    flux_packet: dict = {
        "profile": "flux",
        "outputType": "VarianceAgentResult",
        "period": period,
        "lock_status": lock_status,
        "unlocked": unlocked,
        "status": "INSUFFICIENT",
        "narrative": prefix_unlocked(
            "No Kernel variance facts for this period yet.", lock_status=lock_status
        ),
        "unsupported_claims": [],
        "evidence_ids": [],
        "numbers": {},
    }
    try:
        from reporting.variance import analyze_variance, deterministic_narrative, flag_unsupported_claims

        explanation = analyze_variance("revenue", period)
        kernel_narrative = deterministic_narrative(explanation)
        lead = _choose_flux_sentence(explanation)
        narrative = prefix_unlocked(f"{lead} {kernel_narrative}", lock_status=lock_status)
        unsupported = flag_unsupported_claims(explanation, narrative)
        evidence_ids = [explanation.variance_id] if getattr(explanation, "variance_id", "") else []
        evidence_ids.extend(
            [tid for item in explanation.contributors for tid in item.source_transaction_ids]
        )
        flux_packet = {
            "profile": "flux",
            "outputType": "VarianceAgentResult",
            "period": period,
            "lock_status": lock_status,
            "unlocked": unlocked,
            "status": "OK" if explanation.reconciled else "INSUFFICIENT",
            "narrative": narrative,
            "unsupported_claims": unsupported,
            "evidence_ids": list(dict.fromkeys(evidence_ids)),
            "metric": explanation.metric,
            "numbers": stamp_amounts(
                {
                    "current_value": explanation.current_value,
                    "comparison_value": explanation.comparison_value,
                    "variance": explanation.variance,
                    "dollar_variance": explanation.dollar_variance,
                    "unexplained_amount": explanation.unexplained_amount,
                },
                lock_status=lock_status,
                evidence_id=explanation.metric,
            ),
        }
    except Exception as exc:
        flux_packet["status"] = "INSUFFICIENT"
        flux_packet["narrative"] = prefix_unlocked(
            f"Variance facts unavailable ({type(exc).__name__}).", lock_status=lock_status
        )

    _write_json(computer / f"{prefix}/flux.json", flux_packet)

    forecast_packet = {
        "profile": "forecast",
        "outputType": "ForecastAgentResult",
        "period": period,
        "as_of": as_of,
        "lock_status": lock_status,
        "unlocked": unlocked,
        "status": "REFUSED",
        "trusted_cash": trusted,
        "forecast_id": "",
        "beginning_cash": None,
        "beginning_cash_source": trusted.get("source"),
        "numbers": stamp_amounts({}, lock_status=lock_status),
        "narrative": prefix_unlocked(
            "Forecast refused. Starting balance is not trusted cash. "
            "Unreconciled GL cash is not the 13-week start.",
            lock_status=lock_status,
        ),
        "judgments": [],
        "risks": list(trusted.get("reasons") or []),
    }
    if trusted.get("forecast_may_start") and trusted.get("beginning_cash") is not None:
        from reporting.forecast import build_forecast, persist_forecast_export
        from reporting.store import save_snapshot

        snapshot = build_forecast(as_of, beginning_cash=float(trusted["beginning_cash"]))
        saved = save_snapshot(snapshot)
        persist_forecast_export(saved, directory=computer / "runs" / "forecast")
        forecast_packet.update(
            {
                "status": "OK",
                "forecast_id": saved.forecast_id,
                "beginning_cash": labeled_or_plain(saved.beginning_cash, lock_status),
                "ending_cash": labeled_or_plain(
                    saved.weeks[-1].ending_cash if saved.weeks else None, lock_status
                ),
                "immutable": True,
                "narrative": prefix_unlocked(
                    f"13-week forecast {saved.forecast_id} starts from trusted cash.",
                    lock_status=lock_status,
                ),
            }
        )
    _write_json(computer / f"{prefix}/forecast.json", forecast_packet)

    board_numbers = {
        "lock_status": lock_status,
        "forecast_status": forecast_packet["status"],
    }
    if flux_packet.get("numbers"):
        board_numbers["flux"] = flux_packet["numbers"]
    board_packet = {
        "profile": "board",
        "outputType": "BoardAgentResult",
        "period": period,
        "lock_status": lock_status,
        "unlocked": unlocked,
        "status": "DRAFT",
        "executive_narrative": prefix_unlocked(
            flux_packet.get("narrative") or "Board pack cites Kernel facts only.",
            lock_status=lock_status,
        ),
        "attention_items": list(forecast_packet.get("risks") or []),
        "evidence_ids": list(flux_packet.get("evidence_ids") or []),
        "numbers": stamp_amounts(board_numbers, lock_status=lock_status),
        "unsupported_claims": list(flux_packet.get("unsupported_claims") or []),
    }
    if forecast_packet["status"] == "REFUSED":
        board_packet["attention_items"].append(
            "Forecast starting balance is not trusted cash. Do not treat GL cash as closed cash."
        )
    _write_json(computer / f"{prefix}/board.json", board_packet)
    board_md = [
        f"# Board pack — {period}",
        "",
        f"lock_status: {lock_status}",
        f"label: {UNLOCKED if unlocked else 'locked'}",
        "",
        board_packet["executive_narrative"],
        "",
        "Evidence: " + ", ".join(board_packet["evidence_ids"][:12] or ["(none)"]),
        "",
    ]
    if unlocked:
        board_md.insert(4, "Every number in this draft is UNLOCKED.")
        board_md.insert(5, "")
    _write_text(computer / f"{prefix}/board.md", "\n".join(board_md))

    next_wake = {
        "toSlug": "story",
        "to": "bot_story",
        "from": "bot_story",
        "profile": "forecast",
        "kind": "a2a_handoff",
        "paths": [f"{prefix}/flux.json"],
        "prompt": (
            f"profile: forecast\n"
            f"lock_status={lock_status}. If not CLOSED, label every number UNLOCKED. "
            "Call trusted cash before any 13-week start. Never ask a human."
        ),
        "live_sent": False,
    }
    write_peer_handle(
        computer,
        from_slug="story",
        to_slug="story",
        profile="forecast",
        paths=[f"{prefix}/flux.json"],
        prompt=next_wake["prompt"],
        extra={"lock_status": lock_status, "live_sent": False},
    )
    write_peer_handle(
        computer,
        from_slug="story",
        to_slug="audit",
        profile="interpret",
        paths=[f"{prefix}/board.json"],
        prompt=(
            f"profile: interpret\nSample the story pack at {prefix}/. "
            "Cite Kernel finding IDs only. Do not concur. Never ask a human."
        ),
        extra={"live_sent": False},
    )

    return {
        "period": period,
        "lock_status": lock_status,
        "unlocked": unlocked,
        "flux_path": f"{prefix}/flux.json",
        "forecast_path": f"{prefix}/forecast.json",
        "board_path": f"{prefix}/board.json",
        "forecast_status": forecast_packet["status"],
        "trusted": bool(trusted.get("trusted")),
        "computer_root": str(computer),
    }


def labeled_or_plain(value, lock_status: str):
    from reporting.unlocked import labeled_number

    if value is None:
        return None
    if lock_is_closed(lock_status):
        return value
    return labeled_number(value, lock_status=lock_status)
