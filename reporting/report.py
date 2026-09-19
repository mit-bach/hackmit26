"""Terminal rendering for the reporting demo."""

from __future__ import annotations

from reporting.forecast import lines_for_week
from reporting.models import CashForecastSnapshot, ReportingRun


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_reporting_run(run: ReportingRun) -> str:
    current = run.statement
    prior = run.comparison_statement
    gm = next((item for item in run.variances if item.metric == "gross_margin_pct"), None)
    forecast = run.forecast
    fva = run.forecast_variance
    pack = run.board_pack
    lines = [
        "OFFICE OF THE CFO — REPORTING AND FORECASTING",
        "",
        "1. Financial results",
        "",
    ]
    if current:
        lines.extend(
            [
                f"   Period {current.period}",
                f"   Revenue            {_money(current.revenue)}",
                f"   COGS               {_money(current.cogs)}",
                f"   Gross profit       {_money(current.gross_profit)}",
                f"   Gross margin       {_pct(current.gross_margin_pct)}",
                f"   Operating expenses {_money(current.operating_expenses)}",
                f"   Operating income   {_money(current.operating_income)}",
                f"   Cash               {_money(current.cash)}",
                f"   AP                 {_money(current.ap)}",
                f"   AR                 {_money(current.ar)}",
            ]
        )
    if prior:
        lines.extend(["", f"   Prior {prior.period} gross margin {_pct(prior.gross_margin_pct)}"])
    lines.extend(["", "2. Detected material variance", ""])
    if gm:
        lines.append(f"   {gm.metric}: {gm.comparison_value} → {gm.current_value} ({gm.variance:+})")
        lines.append(f"   Dollar impact: {gm.dollar_variance:+,.2f}")
        lines.append(f"   Reconciled: {'yes' if gm.reconciled else 'NO'}")
        lines.append(f"   {gm.narrative}")
    lines.extend(["", "3. Transaction-level explanation", ""])
    if gm:
        for item in gm.contributors:
            txns = ", ".join(item.source_transaction_ids[:4]) or "(none)"
            lines.append(
                f"   {item.kind.upper():9} {item.label:28} {item.amount:+12,.2f}  "
                f"share {item.share_of_variance:.0%}  txns {txns}"
            )
        lines.append(f"   UNEXPLAINED residual {gm.unexplained_amount:+,.2f}")
    lines.extend(["", "4. Current 13-week cash forecast", ""])
    if forecast:
        lines.append(f"   {forecast.forecast_id} as of {forecast.as_of_date}")
        lines.append(f"   Beginning cash {_money(forecast.beginning_cash)}")
        lines.append(f"   Held AP excluded: {', '.join(forecast.held_ap_ids) or '(none)'}")
        for week in forecast.weeks[:6]:
            lines.append(
                f"   {week.week_start}  begin {_money(week.beginning_cash):>12}  "
                f"AR {_money(week.ar_collections):>10}  AP {_money(week.ap_payments):>10}  "
                f"PR {_money(week.payroll):>10}  end {_money(week.ending_cash):>12}"
            )
        if len(forecast.weeks) > 6:
            last = forecast.weeks[-1]
            lines.append(f"   … {len(forecast.weeks) - 6} more weeks … end {_money(last.ending_cash)}")
        sample = next((item for item in forecast.lines if item.source_type == "invoice"), None)
        if sample:
            lines.append(
                f"   Example AP line {sample.source_id} {sample.expected_date} "
                f"{sample.amount:+,.2f} — {sample.rationale}"
            )
    lines.extend(["", "5. Forecast-vs-actual analysis", ""])
    if fva:
        lines.append(f"   Miss vs {fva.forecast_id}: {fva.total_ending_cash_variance:+,.2f}")
        lines.append(f"   Reconciled: {'yes' if fva.reconciled else 'NO'}")
        for item in fva.contributors:
            lines.append(f"   {item.kind:18} {item.label:48} {item.amount:+,.2f}")
        lines.append(f"   {fva.narrative}")
    lines.extend(["", "6. Generated board-pack excerpt", ""])
    if pack:
        excerpt = "\n".join(pack.markdown.splitlines()[:28])
        lines.append(excerpt)
    lines.extend(["", "7. Evidence / provenance trail", ""])
    for item in run.provenance:
        chain = " → ".join(
            part
            for part in [
                item.source_document_id,
                item.ap_decision,
                item.scheduled_payment and f"pay {item.scheduled_payment}",
                item.forecast_line_id,
                item.forecast_id,
                item.variance_id,
                item.board_pack_id,
            ]
            if part
        )
        lines.append(f"   {chain}")
    if run.trace_path:
        lines.extend(["", f"Trace: {run.trace_path}"])
    reviews = ", ".join(f"{item.role.split()[0]} {item.decision}" for item in run.reviews)
    if reviews:
        lines.extend(["", f"Reviews: {reviews}"])
    if run.escalations:
        lines.append("Escalations: " + "; ".join(run.escalations))
    return "\n".join(lines)


def format_cash_forecast(snapshot: CashForecastSnapshot) -> str:
    assumptions = snapshot.assumptions or {}
    reserve = float(assumptions.get("minimum_cash_reserve") or 100000)
    lines = [
        f"13-WEEK CASH FORECAST as of {snapshot.as_of_date}",
        f"Opening cash: {_money(snapshot.beginning_cash)}",
        f"Source of expected receipts: {assumptions.get('source_of_truth', 'live_ar')}",
        (
            f"Live AR expected collections (7d): "
            f"{_money(float(assumptions.get('live_ar_expected_collections') or 0))}"
        ),
        (
            f"Legacy expected_receipts_next_7_days: "
            f"{_money(float(assumptions.get('legacy_expected_receipts_next_7_days') or 0))} "
            "(fallback only)"
        ),
        f"Posted AR cash since bank snapshot: {_money(float(assumptions.get('posted_ar_cash') or 0))}",
        f"Unapplied customer cash: {_money(float(assumptions.get('unapplied_customer_cash') or 0))}",
        "",
        f"{'Week':<12} {'Opening Cash':>14} {'AR Inflows':>12} {'AP Outflows':>12} "
        f"{'Payroll':>10} {'Other':>10} {'Ending Cash':>14}",
    ]
    for week in snapshot.weeks:
        other = week.other_outflows - week.other_inflows
        lines.append(
            f"{week.week_start:<12} {_money(week.beginning_cash):>14} "
            f"{_money(week.ar_collections):>12} {_money(week.ap_payments):>12} "
            f"{_money(week.payroll):>10} {_money(other):>10} {_money(week.ending_cash):>14}"
        )
    lines.extend(["", "AR collections:"])
    ar_lines = [item for item in snapshot.lines if item.source_type == "receivable"]
    if not ar_lines:
        lines.append("- (none)")
    for item in ar_lines:
        tag = "" if item.committed else " [excluded from base case]"
        lines.append(
            f"- {item.customer} {item.source_id} {_money(item.amount)} "
            f"on {item.expected_date} ({item.rationale}){tag}"
        )
    lines.extend(["", "AP payments:"])
    ap_lines = [item for item in snapshot.lines if item.source_type == "invoice"]
    if not ap_lines:
        lines.append("- (none)")
    for item in ap_lines:
        hold = " [HOLD — not committed]" if item.hold else ""
        lines.append(
            f"- {item.vendor} {item.source_id} {_money(abs(item.amount))} "
            f"on {item.expected_date} ({item.rationale}){hold}"
        )
    low_cash = [week for week in snapshot.weeks if week.ending_cash < reserve]
    lines.extend(["", "Low-cash weeks:"])
    if not low_cash:
        lines.append("- (none)")
    for week in low_cash:
        lines.append(f"- {week.week_start} ending {_money(week.ending_cash)}")
    uncertain = [
        item
        for item in snapshot.lines
        if item.source_type == "receivable" and item.line_id in snapshot.low_confidence_lines
    ]
    lines.extend(["", "Uncertain collections:"])
    if not uncertain:
        lines.append("- (none)")
    for item in uncertain:
        lines.append(f"- {item.source_id} {_money(item.amount)} {item.rationale}")
    disputed = [
        item
        for item in snapshot.lines
        if item.source_type == "receivable" and not item.committed and "disputed:true" in item.evidence_refs
    ]
    lines.extend(["", "Disputed AR excluded from base case:"])
    if not disputed:
        lines.append("- (none)")
    for item in disputed:
        lines.append(f"- {item.source_id} {_money(item.amount)} {item.customer}")
    lines.extend(
        [
            "",
            f"Unapplied customer cash: {_money(float(assumptions.get('unapplied_customer_cash') or 0))}",
        ]
    )
    if snapshot.weeks:
        first = snapshot.weeks[0]
        detail = lines_for_week(snapshot, first.week_start, source_type="receivable")
        lines.extend(
            [
                "",
                f"Why week {first.week_start} AR inflows are {_money(first.ar_collections)}:",
            ]
        )
        if not detail:
            lines.append("- (no committed receivable lines)")
        for item in detail:
            lines.append(f"- {item.source_id} {_money(item.amount)} — {item.rationale}")
    if snapshot.trace_id:
        lines.extend(["", f"Forecast id: {snapshot.forecast_id}", f"Trace: {snapshot.trace_id}"])
    return "\n".join(lines)
