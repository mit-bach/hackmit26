"""Deterministic financial statements and period comparisons."""

from __future__ import annotations

import json

from accrual.estimation import money
from reporting import ledger as reporting_ledger
from reporting.ledger import lines_for, load_balances, period_balance, signed_pnl
from reporting.models import (
    BudgetPeriod,
    ComparisonKind,
    FinancialMetric,
    IncomeStatement,
    ReportingLine,
)
from tools import DataFileError


STATEMENT_METRICS = (
    "revenue",
    "cogs",
    "gross_profit",
    "gross_margin_pct",
    "operating_expenses",
    "operating_income",
    "cash",
    "ap",
    "ar",
)


def ratio(value: float) -> float:
    return round(float(value), 8)


def load_budget() -> dict[str, BudgetPeriod]:
    path = reporting_ledger.DATA_REPORTING / "budget.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DataFileError(f"Invalid JSON in budget.json: {exc.msg}") from exc
    if isinstance(raw, dict):
        return {key: BudgetPeriod.model_validate({"period": key, **value}) for key, value in raw.items()}
    rows = {}
    for item in raw:
        parsed = BudgetPeriod.model_validate(item)
        rows[parsed.period] = parsed
    return rows


def _class_total(rows: list[ReportingLine], account_class: str) -> float:
    return money(sum(signed_pnl(item) for item in rows if item.account_class == account_class))


def build_income_statement(period: str) -> IncomeStatement:
    rows = lines_for(period=period)
    revenue = _class_total(rows, "revenue")
    cogs = _class_total(rows, "cogs")
    opex = _class_total(rows, "opex")
    gross_profit = money(revenue - cogs)
    margin = ratio(gross_profit / revenue) if revenue else 0.0
    operating_income = money(gross_profit - opex)
    balances = load_balances()
    balance = balances.get(period)
    cash = money(balance.cash) if balance else period_balance(period, "cash")
    ap = money(balance.ap) if balance else period_balance(period, "ap")
    ar = money(balance.ar) if balance else period_balance(period, "ar")
    statement = IncomeStatement(
        period=period,
        revenue=revenue,
        cogs=cogs,
        gross_profit=gross_profit,
        gross_margin_pct=margin,
        operating_expenses=opex,
        operating_income=operating_income,
        cash=cash,
        ap=ap,
        ar=ar,
        line_ids=[item.line_id for item in rows],
    )
    statement.metrics = [
        _metric(name, period, getattr(statement, name), unit="ratio" if name.endswith("_pct") else "usd")
        for name in STATEMENT_METRICS
    ]
    return statement


def _metric(name: str, period: str, value: float, unit: str) -> FinancialMetric:
    return FinancialMetric(
        metric=name,
        period=period,
        current_value=value if unit == "usd" else ratio(value),
        unit=unit,  # type: ignore[arg-type]
        evidence_refs=[f"metric:{name}:{period}", f"statement:{period}"],
    )


def _value(statement: IncomeStatement, metric: str) -> float:
    if not hasattr(statement, metric):
        raise KeyError(f"Unknown reporting metric {metric!r}")
    return getattr(statement, metric)


def compare_metrics(
    current: IncomeStatement,
    comparison: IncomeStatement | BudgetPeriod | None,
    *,
    kind: ComparisonKind,
    comparison_period: str = "",
    metrics: tuple[str, ...] = STATEMENT_METRICS,
) -> list[FinancialMetric]:
    rows: list[FinancialMetric] = []
    if comparison is None:
        return list(current.metrics)
    for name in metrics:
        current_value = _value(current, name)
        if isinstance(comparison, BudgetPeriod):
            other = getattr(comparison, name)
            if other is None:
                continue
            label = comparison.period
        else:
            other = _value(comparison, name)
            label = comparison.period
        absolute = (
            ratio(current_value - other)
            if name.endswith("_pct")
            else money(current_value - other)
        )
        relative = ratio(absolute / other) if other else None
        dollar = None
        if name == "gross_margin_pct":
            current_gp = current.gross_profit
            if isinstance(comparison, BudgetPeriod):
                other_gp = comparison.gross_profit
                if other_gp is None and comparison.revenue is not None and comparison.cogs is not None:
                    other_gp = money(comparison.revenue - comparison.cogs)
            else:
                other_gp = comparison.gross_profit
            if other_gp is not None:
                dollar = money(current_gp - other_gp)
        elif name in {"revenue", "cogs", "gross_profit", "operating_expenses", "operating_income", "cash", "ap", "ar"}:
            dollar = money(current_value - other) if not name.endswith("_pct") else None
        rows.append(
            FinancialMetric(
                metric=name,
                period=current.period,
                current_value=current_value,
                comparison_value=other,
                comparison_kind=kind,
                comparison_period=comparison_period or label,
                absolute_variance=absolute,
                relative_variance=relative,
                dollar_variance=dollar,
                unit="ratio" if name.endswith("_pct") else "usd",
                evidence_refs=[
                    f"metric:{name}:{current.period}",
                    f"metric:{name}:{comparison_period or label}",
                    f"statement:{current.period}",
                ],
            )
        )
    return rows


def prior_period(period: str) -> str:
    year, month = period.split("-")
    month_i = int(month) - 1
    year_i = int(year)
    if month_i == 0:
        return f"{year_i - 1}-12"
    return f"{year_i}-{month_i:02d}"


def period_report(
    period: str,
    *,
    comparison_period: str | None = None,
    include_budget: bool = True,
) -> tuple[IncomeStatement, IncomeStatement | None, list[FinancialMetric]]:
    current = build_income_statement(period)
    compare_to = comparison_period or prior_period(period)
    previous = None
    metrics = list(current.metrics)
    try:
        previous = build_income_statement(compare_to)
        if previous.revenue or previous.cogs or previous.operating_expenses:
            metrics = compare_metrics(current, previous, kind="prior_period", comparison_period=compare_to)
    except Exception:
        previous = None
    if include_budget:
        budget = load_budget().get(period)
        if budget:
            metrics.extend(compare_metrics(current, budget, kind="budget", comparison_period=f"budget:{period}"))
    return current, previous, metrics


def get_metric(metrics: list[FinancialMetric], name: str, kind: ComparisonKind | None = None) -> FinancialMetric:
    for item in metrics:
        if item.metric == name and (kind is None or item.comparison_kind == kind):
            return item
    raise KeyError(f"Metric {name} not found")
