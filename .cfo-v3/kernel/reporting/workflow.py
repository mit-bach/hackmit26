"""Reporting calculation → variance → reviewer → board; forecast → reviewer."""

from __future__ import annotations

import os

from close.dates import now_iso
from reporting.actuals import compare_forecast_to_actuals, realize_actuals
from reporting.board import build_board_pack
from reporting.forecast import build_forecast
from reporting.models import (
    ProvenanceLink,
    ReportingRun,
    VarianceExplanation,
)
from reporting.reviewer import (
    review_board_pack,
    review_forecast,
    review_forecast_variance,
    review_variance,
)
from reporting.seed import seed_demo_ledger, seed_demo_receivable
from reporting.sources import ap_forecast_lines, set_ap_decision
from reporting.statements import period_report
from reporting.store import latest_snapshot, next_version, save_run, save_snapshot
from reporting.variance import analyze_variance, flag_unsupported_claims
from scheduling.pool import add_approved, load_pool


DEFAULT_PERIOD = "2026-09"
DEFAULT_AS_OF = "2026-09-19"


def _live_requested(live: bool | None) -> bool:
    if live is False:
        return False
    if live is True:
        return True
    return bool(os.environ.get("OPENAI_API_KEY"))


def _maybe_agent(live: bool, runner, fallback):
    if not live:
        return fallback(), False
    try:
        return runner(), True
    except Exception:
        return fallback(), False


def _seed_ap_pool() -> None:
    if load_pool():
        return
    for invoice_id in ("INV-001", "INV-002", "INV-006", "INV-009", "INV-016"):
        try:
            add_approved(invoice_id, source="reporting_demo")
        except Exception:
            continue
    set_ap_decision("INV-016", hold=True, approval_state="hold", reason="Missing PO")
    set_ap_decision("INV-009", scheduled_pay_date="2026-10-09", reason="Deferred past the original due date")
    set_ap_decision("INV-002", scheduled_pay_date="2026-09-22", reason="Approved AP invoice due 2026-09-22")
    set_ap_decision("INV-006", scheduled_pay_date="2026-09-21", reason="Late Google Cloud invoice")
    set_ap_decision("INV-001", scheduled_pay_date="2026-09-30", reason="Approved AP invoice due 2026-09-30")


def _explain_with_agent(explanation: VarianceExplanation, live: bool) -> VarianceExplanation:
    from reporting.agents import variance_analysis_agent
    from reporting.variance import deterministic_narrative

    def fallback():
        return deterministic_narrative(explanation)

    def runner():
        from agent import run_agent

        result = run_agent(
            variance_analysis_agent,
            (
                "Explain this Python variance. Do not recalculate.\n"
                f"metric={explanation.metric} period={explanation.period}"
            ),
        )
        return result.narrative, result.unsupported_claims

    if not live:
        explanation.narrative = fallback()
        return explanation
    try:
        from agent import run_agent
        from reporting.agents import variance_analysis_agent as agent

        result = run_agent(
            agent,
            f"Explain this Python variance. Do not recalculate.\n{explanation.model_dump_json()}",
        )
        explanation.narrative = result.narrative
        explanation.unsupported_claims = list(result.unsupported_claims) + flag_unsupported_claims(
            explanation, result.narrative
        )
        explanation.used_agent = True
    except Exception:
        explanation.narrative = fallback()
    return explanation


def run_reporting_workflow(
    period: str = DEFAULT_PERIOD,
    *,
    as_of: str = DEFAULT_AS_OF,
    comparison_period: str | None = None,
    live: bool | None = None,
    seed: bool = True,
    persist: bool = True,
) -> ReportingRun:
    live = _live_requested(live)
    if seed:
        seed_demo_ledger()
        seed_demo_receivable()
        _seed_ap_pool()

    current, prior, metrics = period_report(period, comparison_period=comparison_period)
    compare_to = comparison_period or (prior.period if prior else "2026-08")
    explanation = analyze_variance("gross_margin_pct", period, compare_to)
    explanation = _explain_with_agent(explanation, live)
    variance_review = review_variance(explanation)

    prior_snapshot = latest_snapshot(as_of)
    version = next_version(as_of)
    snapshot = build_forecast(as_of, prior=prior_snapshot, version=version)
    if live:
        try:
            from agent import run_agent
            from reporting.agents import cash_forecast_agent

            result = run_agent(
                cash_forecast_agent,
                f"Interpret this Python forecast. Do not recalculate.\n{snapshot.forecast_id}",
            )
            snapshot = snapshot.model_copy(
                update={
                    "agent_judgments": list(result.judgments) or list(result.risks),
                    "used_agent": True,
                }
            )
        except Exception:
            pass
    else:
        snapshot = snapshot.model_copy(
            update={
                "agent_judgments": [
                    "Held AP invoices are excluded from committed outflows.",
                    "Low-confidence AR collections remain on the forecast with reduced confidence.",
                ],
            }
        )
    if persist:
        snapshot = save_snapshot(snapshot)

    forecast_review = review_forecast(snapshot)
    actuals = realize_actuals(snapshot)
    fva = compare_forecast_to_actuals(snapshot, actuals)
    if live:
        try:
            from agent import run_agent
            from reporting.agents import forecast_variance_agent

            result = run_agent(
                forecast_variance_agent,
                f"Explain this Python forecast miss. Do not recalculate.\n{fva.model_dump_json()}",
            )
            fva = fva.model_copy(update={"narrative": result.narrative, "used_agent": True})
        except Exception:
            pass
    fva_review = review_forecast_variance(fva)

    pack = build_board_pack(
        period=period,
        as_of_date=as_of,
        current=current,
        prior=prior,
        metrics=metrics,
        variances=[explanation],
        forecast=snapshot,
        forecast_variance=fva,
    )
    if live:
        try:
            from agent import run_agent
            from reporting.agents import board_reporting_agent

            result = run_agent(
                board_reporting_agent,
                f"Write the executive narrative from these Python facts.\n{pack.pack_id}",
            )
            if pack.sections:
                pack.sections[0].narrative = result.executive_narrative or pack.sections[0].narrative
            pack.unsupported_claims = list(result.unsupported_claims)
            pack.used_agent = True
        except Exception:
            pass
    board_review = review_board_pack(pack, {current.period: current, **({prior.period: prior} if prior else {})})

    provenance = _build_provenance(explanation, snapshot, pack)
    reviews = [variance_review, forecast_review, fva_review, board_review]
    escalations = [
        item.reasons[0] if item.reasons else item.decision
        for item in reviews
        if item.escalation == "human"
    ]
    run = ReportingRun(
        run_id=f"RPT-{period}-{now_iso().replace(':', '').replace('-', '')}",
        period=period,
        comparison_period=compare_to,
        as_of_date=as_of,
        statement=current,
        comparison_statement=prior,
        metrics=metrics,
        variances=[explanation],
        forecast=snapshot,
        forecast_variance=fva,
        board_pack=pack,
        reviews=reviews,
        provenance=provenance,
        used_agent=any([explanation.used_agent, snapshot.used_agent, fva.used_agent, pack.used_agent]),
        escalations=escalations,
    )
    if persist:
        run.trace_path = str(save_run(run))
    return run


def _build_provenance(
    explanation: VarianceExplanation,
    snapshot,
    pack,
) -> list[ProvenanceLink]:
    links: list[ProvenanceLink] = []
    by_source = {item.source_id: item for item in snapshot.lines}
    for invoice_id in ("INV-002", "INV-009", "INV-016", "INV-AR-FC-001"):
        line = by_source.get(invoice_id)
        from close.context import remember_link

        close_link = remember_link(
            source_document_id=invoice_id,
            transaction_id=invoice_id,
            extra={
                "forecast_id": snapshot.forecast_id,
                "forecast_line_id": line.line_id if line else "",
                "variance_id": explanation.variance_id,
                "board_pack_id": pack.pack_id,
            },
        )
        links.append(
            ProvenanceLink(
                source_document_id=invoice_id,
                ap_decision="HOLD" if line and line.hold else ("APPROVE" if line and line.source_type == "invoice" else ""),
                scheduled_payment="" if line is None or line.hold else line.expected_date,
                forecast_line_id=line.line_id if line else "",
                forecast_id=snapshot.forecast_id,
                variance_id=explanation.variance_id,
                board_pack_id=pack.pack_id,
                close_link_id=close_link.link_id,
                trace_ids=[snapshot.trace_id, explanation.trace_id or explanation.variance_id, pack.trace_id],
            )
        )
    # Hosting overage used in GM attribution
    overage = next((item for item in explanation.contributors if "hosting" in item.category), None)
    if overage:
        from close.context import remember_link

        remember_link(
            source_document_id="INV-016",
            transaction_id="TXN-HOST-SEP-OVERAGE",
            journal_entry_id="TXN-HOST-SEP-OVERAGE",
            extra={"variance_id": explanation.variance_id, "board_pack_id": pack.pack_id},
        )
    _ = ap_forecast_lines
    return links
