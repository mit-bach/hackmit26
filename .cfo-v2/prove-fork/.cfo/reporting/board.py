"""Board pack assembled from deterministic reporting outputs."""

from __future__ import annotations

from reporting.models import (
    BoardPack,
    BoardPackSection,
    CashForecastSnapshot,
    FinancialMetric,
    ForecastVarianceExplanation,
    IncomeStatement,
    VarianceExplanation,
)
from reporting.statements import ratio


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _pct(value: float) -> str:
    return f"{ratio(value) * 100:.1f}%"


def render_markdown(pack: BoardPack) -> str:
    lines = [f"# Board Pack — {pack.period}", "", f"As of {pack.as_of_date}", ""]
    for section in pack.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        if section.narrative:
            lines.append(section.narrative)
            lines.append("")
        for metric in section.metrics:
            current = _pct(metric.current_value) if metric.unit == "ratio" else _money(metric.current_value)
            extra = ""
            if metric.comparison_value is not None:
                other = _pct(metric.comparison_value) if metric.unit == "ratio" else _money(metric.comparison_value)
                extra = f" vs {other}"
                if metric.absolute_variance is not None:
                    delta = (
                        f"{metric.absolute_variance * 100:+.1f} pts"
                        if metric.unit == "ratio"
                        else f"{metric.absolute_variance:+,.2f}"
                    )
                    extra += f" ({delta})"
            lines.append(f"- {metric.metric}: {current}{extra}")
        for item in section.items:
            lines.append(f"- {item}")
        if section.evidence_refs:
            lines.append("")
            lines.append("Evidence: " + ", ".join(section.evidence_refs[:8]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_board_pack(
    *,
    period: str,
    as_of_date: str,
    current: IncomeStatement,
    prior: IncomeStatement | None,
    metrics: list[FinancialMetric],
    variances: list[VarianceExplanation],
    forecast: CashForecastSnapshot | None,
    forecast_variance: ForecastVarianceExplanation | None,
    pack_id: str = "",
) -> BoardPack:
    by_name = {item.metric: item for item in metrics if item.comparison_kind in {None, "prior_period"}}
    gm = by_name.get("gross_margin_pct")
    revenue = by_name.get("revenue")
    opex = by_name.get("operating_expenses")
    cash = by_name.get("cash")
    material = [item for item in variances if item.material]
    gm_var = next((item for item in variances if item.metric in {"gross_margin_pct", "gross_profit"}), None)

    exec_items = [
        f"Revenue { _money(current.revenue) }",
        f"Gross margin {_pct(current.gross_margin_pct)}"
        + (f" vs prior {_pct(prior.gross_margin_pct)}" if prior else ""),
        f"Operating income {_money(current.operating_income)}",
        f"Cash {_money(current.cash)}",
    ]
    if gm_var:
        exec_items.append(gm_var.narrative.split(".")[0] + ".")

    sections = [
        BoardPackSection(
            title="Executive Summary",
            metrics=[item for item in (revenue, gm, cash) if item],
            narrative=(
                gm_var.narrative
                if gm_var
                else f"Results for {period} are taken from the canonical ledger."
            ),
            evidence_refs=[
                f"statement:{period}",
                *([gm_var.variance_id] if gm_var else []),
                *([f"forecast:{forecast.forecast_id}"] if forecast else []),
            ],
            items=exec_items,
        ),
        BoardPackSection(
            title="Financial Performance",
            metrics=[item for item in metrics if item.metric in {"revenue", "cogs", "gross_profit", "operating_income"} and item.comparison_kind == "prior_period"],
            narrative=(
                f"Gross profit {_money(current.gross_profit)} on revenue {_money(current.revenue)}."
            ),
            evidence_refs=[f"statement:{period}", f"metric:gross_profit:{period}"],
        ),
        BoardPackSection(
            title="Revenue",
            metrics=[item for item in metrics if item.metric == "revenue"],
            narrative=f"Revenue is {_money(current.revenue)} for {period}.",
            evidence_refs=[f"metric:revenue:{period}", f"statement:{period}"],
        ),
        BoardPackSection(
            title="Gross Margin",
            metrics=[item for item in (gm,) if item],
            narrative=gm_var.narrative if gm_var else f"Gross margin is {_pct(current.gross_margin_pct)}.",
            evidence_refs=[
                f"metric:gross_margin_pct:{period}",
                *([f"variance:{gm_var.variance_id}"] if gm_var else []),
                *([f"txn:{txn}" for item in (gm_var.contributors if gm_var else []) for txn in item.source_transaction_ids[:3]]),
            ],
        ),
        BoardPackSection(
            title="Operating Expenses",
            metrics=[item for item in (opex,) if item],
            narrative=f"Operating expenses {_money(current.operating_expenses)}.",
            evidence_refs=[f"metric:operating_expenses:{period}"],
        ),
        BoardPackSection(
            title="Cash",
            metrics=[item for item in (cash,) if item],
            narrative=f"Period-end cash {_money(current.cash)}; AP {_money(current.ap)}; AR {_money(current.ar)}.",
            evidence_refs=[f"metric:cash:{period}", f"metric:ap:{period}", f"metric:ar:{period}"],
        ),
    ]
    if forecast:
        last = forecast.weeks[-1]
        trough = min(forecast.weeks, key=lambda item: item.ending_cash)
        sections.append(
            BoardPackSection(
                title="13-Week Cash Outlook",
                narrative=(
                    f"Rolling forecast {forecast.forecast_id} starts at {_money(forecast.beginning_cash)} "
                    f"and ends week {last.week_start} at {_money(last.ending_cash)}. "
                    f"Lowest week is {trough.week_start} at {_money(trough.ending_cash)}."
                ),
                evidence_refs=[f"forecast:{forecast.forecast_id}", forecast.trace_id],
                items=[
                    f"{week.week_start}: begin {_money(week.beginning_cash)} → end {_money(week.ending_cash)}"
                    for week in forecast.weeks[:4]
                ],
            )
        )
    if material:
        sections.append(
            BoardPackSection(
                title="Major Variances",
                narrative=" ".join(item.narrative for item in material),
                evidence_refs=[f"variance:{item.variance_id}" for item in material],
                items=[
                    f"{item.label} {item.amount:+,.2f}"
                    for variance in material
                    for item in variance.contributors[:4]
                ],
            )
        )
    risks = []
    if forecast:
        risks.extend(
            f"Low-confidence AR {line_id}"
            for line_id in forecast.low_confidence_lines[:5]
        )
        risks.extend(f"Held AP {invoice_id}" for invoice_id in forecast.held_ap_ids)
    if forecast_variance:
        for item in forecast_variance.contributors:
            if item.kind in {"timing", "new_unforecast", "unexplained"}:
                risks.append(f"{item.label} {item.amount:+,.2f}")
    if gm_var and abs(gm_var.unexplained_amount) > 0.02:
        risks.append(f"Unexplained GM residual {gm_var.unexplained_amount:+,.2f}")
    sections.append(
        BoardPackSection(
            title="Risks / Items Requiring Attention",
            narrative="Items below are unresolved or low-confidence. No additional business story is inferred.",
            evidence_refs=[
                f"statement:{period}",
                *([f"forecast:{forecast.forecast_id}"] if forecast else []),
                *([f"fva:{forecast_variance.analysis_id}"] if forecast_variance else []),
            ],
            items=risks or ["None flagged by Python controls."],
        )
    )
    pack = BoardPack(
        pack_id=pack_id or f"BP-{period}",
        period=period,
        as_of_date=as_of_date,
        sections=sections,
        forecast_id=forecast.forecast_id if forecast else "",
        variance_ids=[item.variance_id for item in variances],
        evidence_refs=sorted({ref for section in sections for ref in section.evidence_refs}),
        trace_id=f"TRACE-BP-{period}",
    )
    pack.markdown = render_markdown(pack)
    return pack
