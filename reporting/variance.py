"""Transaction-level variance attribution. Agents do not invent residuals."""

from __future__ import annotations

from collections import defaultdict

from accrual.estimation import money
from reporting.ledger import lines_for, signed_pnl
from reporting.models import (
    AttributedTransaction,
    ComparisonKind,
    ContributorConfidence,
    ContributorKind,
    DrilldownNode,
    FinancialMetric,
    QuantityRateMix,
    ReportingLine,
    VarianceContributor,
    VarianceExplanation,
    VarianceTrace,
)
from reporting.statements import build_income_statement, compare_metrics, get_metric, prior_period, ratio

NAMED_CATEGORIES = {
    "hosting": "Cloud hosting",
    "supplier": "Supplier price / materials",
    "freight": "Freight",
    "payroll": "Payroll",
    "revenue": "Revenue",
}

METRIC_CLASSES = {
    "revenue": ("revenue",),
    "cogs": ("cogs",),
    "gross_profit": ("revenue", "cogs"),
    "gross_margin": ("revenue", "cogs"),
    "gross_margin_pct": ("revenue", "cogs"),
    "operating_expenses": ("opex",),
    "operating_income": ("revenue", "cogs", "opex"),
    "cash": ("cash",),
    "ap": ("ap",),
    "ar": ("ar",),
}


def load_assumptions():
    from reporting.sources import load_assumptions as _load

    return _load()


def _normalize_metric(metric: str) -> str:
    aliases = {
        "gross_margin": "gross_margin_pct",
        "gm": "gross_margin_pct",
        "opex": "operating_expenses",
        "op_ex": "operating_expenses",
        "opinc": "operating_income",
    }
    return aliases.get(metric, metric)


def _to_transaction(line: ReportingLine) -> AttributedTransaction:
    return AttributedTransaction(
        transaction_id=line.transaction_id,
        line_id=line.line_id,
        entry_id=line.entry_id,
        source_document_id=line.source_document_id,
        vendor=line.vendor,
        customer=line.customer,
        account=line.account,
        category=line.category,
        amount=signed_pnl(line) if line.account_class in {"revenue", "cogs", "opex"} else money(line.amount),
        posting_date=line.posting_date,
        period=line.period,
        source_workflow=line.source_workflow,
        ledger_entry_id=line.ledger_entry_id or line.entry_id,
        trace_ids=list(line.trace_ids),
        evidence_refs=list(line.evidence_refs),
        quantity=line.quantity,
        rate=line.rate,
    )


def _group_key(line: ReportingLine) -> tuple[str, str, str]:
    category = (line.category or "").strip().lower()
    if category in NAMED_CATEGORIES:
        return category, line.account, ""
    entity = line.vendor or line.customer or ""
    return category, line.account, entity


def _group_label(category: str, account: str, entity: str) -> str:
    if category in NAMED_CATEGORIES:
        return NAMED_CATEGORIES[category]
    if category and category not in {"other", "unclassified", "misc"}:
        return category.replace("_", " ").title()
    if entity:
        return entity
    return account


def _pnl_lines(period: str, classes: tuple[str, ...]) -> list[ReportingLine]:
    rows = []
    for account_class in classes:
        rows.extend(lines_for(period=period, account_class=account_class))
    return [item for item in rows if signed_pnl(item) != 0 or item.account_class not in {"revenue", "cogs", "opex"}]


def _quantity_rate(current: list[ReportingLine], prior: list[ReportingLine]) -> QuantityRateMix | None:
    def _totals(rows: list[ReportingLine]) -> tuple[float | None, float | None, float]:
        qty = sum(item.quantity or 0 for item in rows if item.quantity is not None)
        amount = money(sum(signed_pnl(item) for item in rows))
        with_rate = [item for item in rows if item.quantity and item.rate is not None]
        rate = None
        if with_rate:
            rate = money(sum((item.quantity or 0) * (item.rate or 0) for item in with_rate) / sum(item.quantity or 0 for item in with_rate))
        elif qty:
            rate = money(amount / qty)
        return (qty or None, rate, amount)

    q0, r0, a0 = _totals(prior)
    q1, r1, a1 = _totals(current)
    if q0 is None or q1 is None or r0 is None or r1 is None:
        return None
    quantity_effect = money((q1 - q0) * r0)
    rate_effect = money((r1 - r0) * q1)
    residual = money((a1 - a0) - quantity_effect - rate_effect)
    return QuantityRateMix(
        quantity_effect=quantity_effect,
        rate_effect=rate_effect,
        residual=residual if abs(residual) > 0.02 else 0.0,
    )


def attribute_account_movements(
    period: str,
    comparison_period: str,
    *,
    classes: tuple[str, ...] = ("cogs",),
    materiality_abs: float | None = None,
) -> tuple[list[VarianceContributor], float]:
    assumptions = load_assumptions()
    threshold = assumptions.materiality_abs if materiality_abs is None else materiality_abs
    current = _pnl_lines(period, classes)
    prior = _pnl_lines(comparison_period, classes)

    grouped: dict[tuple[str, str, str], dict[str, list[ReportingLine]]] = defaultdict(lambda: {"current": [], "prior": []})
    for item in current:
        grouped[_group_key(item)]["current"].append(item)
    for item in prior:
        grouped[_group_key(item)]["prior"].append(item)

    contributors: list[VarianceContributor] = []
    residual = 0.0
    current_total = money(sum(signed_pnl(item) for item in current))
    prior_total = money(sum(signed_pnl(item) for item in prior))
    total_delta = money(current_total - prior_total)

    for (category, account, entity), buckets in grouped.items():
        cur_amt = money(sum(signed_pnl(item) for item in buckets["current"]))
        prior_amt = money(sum(signed_pnl(item) for item in buckets["prior"]))
        delta = money(cur_amt - prior_amt)
        if abs(delta) <= 0.005:
            continue
        named = category in NAMED_CATEGORIES
        unclassified = category in {"", "other", "unclassified", "misc"}
        if unclassified and not named and abs(delta) <= threshold:
            residual = money(residual + delta)
            continue
        txns = [_to_transaction(item) for item in buckets["current"] + buckets["prior"]]
        # For dollar contribution to a decrease in profit, COGS increases are negative to GP.
        if classes == ("cogs",) or "cogs" in classes and "revenue" in classes:
            signed = money(-delta) if set(classes) == {"cogs"} else money(
                sum(signed_pnl(item) * (1 if item.account_class == "revenue" else -1) for item in buckets["current"])
                - sum(signed_pnl(item) * (1 if item.account_class == "revenue" else -1) for item in buckets["prior"])
            )
            if set(classes) == {"cogs"}:
                signed = money(-delta)
        else:
            signed = delta
        qrm = _quantity_rate(buckets["current"], buckets["prior"])
        kind: ContributorKind = "verified" if named or buckets["current"] and buckets["prior"] else "likely"
        confidence: ContributorConfidence = "high" if kind == "verified" else "medium"
        contributors.append(
            VarianceContributor(
                label=_group_label(category, account, entity),
                amount=signed if set(classes) != {"cogs"} and "cogs" not in classes else (
                    money(-delta) if set(classes) == {"cogs"} else signed
                ),
                source_transaction_ids=sorted({item.transaction_id for item in txns}),
                ledger_entry_ids=sorted({item.ledger_entry_id or item.entry_id for item in txns}),
                source_document_ids=sorted({item.source_document_id for item in txns if item.source_document_id}),
                vendor=entity if any(item.vendor == entity for item in buckets["current"] + buckets["prior"]) else "",
                customer=entity if any(item.customer == entity for item in buckets["current"] + buckets["prior"]) else "",
                account=account,
                category=category,
                confidence=confidence,
                kind=kind,
                quantity_rate_mix=qrm,
                transactions=txns,
                evidence_refs=[
                    *[f"txn:{item.transaction_id}" for item in txns],
                    *[f"je:{item.ledger_entry_id or item.entry_id}" for item in txns],
                ],
            )
        )

    if set(classes) == {"cogs"}:
        # Contributors explain the change in gross profit from COGS (inverse of COGS delta).
        pass
    elif set(classes) == {"revenue"}:
        pass

    contributors.sort(key=lambda item: abs(item.amount), reverse=True)
    if set(classes) == {"cogs"}:
        residual = money(-residual)
        total_for_share = money(-total_delta)
    elif set(classes) == {"revenue", "cogs"}:
        residual = money(-residual) if residual else 0.0
        total_for_share = money(
            (money(sum(signed_pnl(item) for item in current if item.account_class == "revenue"))
             - money(sum(signed_pnl(item) for item in current if item.account_class == "cogs")))
            - (
                money(sum(signed_pnl(item) for item in prior if item.account_class == "revenue"))
                - money(sum(signed_pnl(item) for item in prior if item.account_class == "cogs"))
            )
        )
    else:
        total_for_share = total_delta

    for item in contributors:
        share = ratio(item.amount / total_for_share) if total_for_share else 0.0
        item.share_of_variance = share
    return contributors, money(residual)


def _dollar_target(metric: FinancialMetric) -> float:
    if metric.dollar_variance is not None:
        return money(metric.dollar_variance)
    if metric.absolute_variance is not None and metric.unit == "usd":
        return money(metric.absolute_variance)
    return 0.0


def reconcile_contributors(
    contributors: list[VarianceContributor],
    unexplained: float,
    total: float,
    tolerance: float,
) -> bool:
    summed = money(sum(item.amount for item in contributors) + unexplained)
    return abs(money(summed - total)) <= tolerance


def _drilldown(
    metric: str,
    period: str,
    contributors: list[VarianceContributor],
    dollar_variance: float,
) -> list[DrilldownNode]:
    root = DrilldownNode(level="metric", key=metric, label=metric, amount=dollar_variance)
    by_account: dict[str, list[VarianceContributor]] = defaultdict(list)
    for item in contributors:
        by_account[item.account or item.category or item.label].append(item)
    for account, group in by_account.items():
        account_node = DrilldownNode(
            level="account",
            key=account,
            label=account,
            amount=money(sum(item.amount for item in group)),
        )
        for item in group:
            category_node = DrilldownNode(
                level="category",
                key=item.category or item.label,
                label=item.label,
                amount=item.amount,
                transaction_ids=list(item.source_transaction_ids),
                evidence_refs=list(item.evidence_refs),
            )
            entities: dict[str, list[AttributedTransaction]] = defaultdict(list)
            for txn in item.transactions:
                entities[txn.vendor or txn.customer or txn.account].append(txn)
            for entity, txns in entities.items():
                entity_node = DrilldownNode(
                    level="entity",
                    key=entity,
                    label=entity,
                    amount=money(sum(txn.amount for txn in txns if txn.period == period) or sum(txn.amount for txn in txns)),
                    transaction_ids=[txn.transaction_id for txn in txns],
                )
                for txn in txns:
                    entity_node.children.append(
                        DrilldownNode(
                            level="transaction",
                            key=txn.transaction_id,
                            label=f"{txn.transaction_id} {txn.posting_date}",
                            amount=txn.amount,
                            transaction_ids=[txn.transaction_id],
                            evidence_refs=txn.evidence_refs
                            + ([f"doc:{txn.source_document_id}"] if txn.source_document_id else []),
                            children=[
                                DrilldownNode(
                                    level="evidence",
                                    key=ref,
                                    label=ref,
                                    amount=txn.amount,
                                    evidence_refs=[ref],
                                )
                                for ref in (txn.evidence_refs or [f"txn:{txn.transaction_id}"])
                            ],
                        )
                    )
                category_node.children.append(entity_node)
            account_node.children.append(category_node)
        root.children.append(account_node)
    return [root]


def analyze_variance(
    metric: str,
    period: str,
    comparison_period: str | None = None,
    *,
    comparison_kind: ComparisonKind = "prior_period",
    materiality_threshold: float | None = None,
    variance_id: str = "",
) -> VarianceExplanation:
    metric = _normalize_metric(metric)
    compare_to = comparison_period or prior_period(period)
    current = build_income_statement(period)
    previous = build_income_statement(compare_to)
    metrics = compare_metrics(current, previous, kind=comparison_kind, comparison_period=compare_to)
    fact = get_metric(metrics, metric, kind=comparison_kind)
    assumptions = load_assumptions()
    tolerance = assumptions.variance_tolerance
    materiality = materiality_threshold if materiality_threshold is not None else assumptions.materiality_abs
    classes = METRIC_CLASSES.get(metric, ("cogs",))
    if metric in {"gross_margin_pct", "gross_margin", "gross_profit"}:
        classes = ("cogs",)
    contributors, unexplained = attribute_account_movements(
        period,
        compare_to,
        classes=classes,
        materiality_abs=materiality,
    )
    dollar = _dollar_target(fact)
    if metric in {"gross_margin_pct", "gross_profit"} and fact.dollar_variance is not None:
        dollar = money(fact.dollar_variance)
    # If we attributed only COGS, contributor amounts already invert to GP impact.
    if not reconcile_contributors(contributors, unexplained, dollar, tolerance):
        gap = money(dollar - money(sum(item.amount for item in contributors) + unexplained))
        unexplained = money(unexplained + gap)
    reconciled = reconcile_contributors(contributors, unexplained, dollar, tolerance)
    variance_value = fact.absolute_variance if fact.absolute_variance is not None else dollar
    material = abs(dollar) >= materiality or (
        fact.relative_variance is not None and abs(fact.relative_variance) >= assumptions.materiality_pct
    )
    explanation = VarianceExplanation(
        variance_id=variance_id or f"VAR-{period}-{metric}",
        metric=metric,
        period=period,
        comparison_period=compare_to,
        comparison_kind=comparison_kind,
        current_value=fact.current_value,
        comparison_value=fact.comparison_value if fact.comparison_value is not None else 0,
        variance=variance_value if variance_value is not None else 0,
        dollar_variance=dollar,
        contributors=contributors,
        unexplained_amount=unexplained,
        reconciled=reconciled,
        residual_tolerance=tolerance,
        material=material,
        drilldown=_drilldown(metric, period, contributors, dollar),
        evidence_refs=[
            fact.metric_id,
            f"variance:{variance_id or f'VAR-{period}-{metric}'}",
            *[ref for item in contributors for ref in item.evidence_refs],
        ],
    )
    if not reconciled:
        explanation.unsupported_claims.append(
            "Contributor amounts plus residual do not reconcile to the dollar variance."
        )
    explanation.narrative = deterministic_narrative(explanation)
    return explanation


def deterministic_narrative(explanation: VarianceExplanation) -> str:
    parts = [
        (
            f"{explanation.metric} moved from {explanation.comparison_value} "
            f"to {explanation.current_value} ({explanation.variance:+})."
        )
    ]
    if explanation.dollar_variance:
        parts.append(f"Dollar impact is {explanation.dollar_variance:+,.2f}.")
    verified = [item for item in explanation.contributors if item.kind == "verified"]
    likely = [item for item in explanation.contributors if item.kind == "likely"]
    for item in verified:
        extra = ""
        mix = item.quantity_rate_mix
        if mix and mix.rate_effect:
            extra = f" COGS rate effect {mix.rate_effect:+,.2f}."
        if mix and mix.quantity_effect:
            extra += f" COGS quantity effect {mix.quantity_effect:+,.2f}."
        parts.append(
            f"Verified: {item.label} {item.amount:+,.2f} "
            f"({len(item.source_transaction_ids)} transactions).{extra}"
        )
    for item in likely:
        parts.append(f"Likely: {item.label} {item.amount:+,.2f}.")
    if abs(explanation.unexplained_amount) > explanation.residual_tolerance:
        parts.append(
            f"Unexplained residual {explanation.unexplained_amount:+,.2f} "
            "has no supported transaction explanation."
        )
    else:
        parts.append("No material unexplained residual.")
    return " ".join(parts)


def trace_variance(
    metric: str,
    period: str,
    comparison_period: str | None = None,
) -> VarianceTrace:
    explanation = analyze_variance(metric, period, comparison_period)
    transactions = [txn for item in explanation.contributors for txn in item.transactions]
    return VarianceTrace(
        metric=explanation.metric,
        period=explanation.period,
        comparison_period=explanation.comparison_period,
        dollar_variance=explanation.dollar_variance,
        contributors=explanation.contributors,
        transactions=transactions,
        drilldown=explanation.drilldown,
        unexplained_amount=explanation.unexplained_amount,
        reconciled=explanation.reconciled,
    )


def flag_unsupported_claims(explanation: VarianceExplanation, narrative: str) -> list[str]:
    """Reject invented causes that are not in the computed contributor set."""
    flags: list[str] = []
    allowed = {item.label.lower() for item in explanation.contributors}
    allowed.update(NAMED_CATEGORIES.values())
    allowed.update(NAMED_CATEGORIES)
    allowed.update({"unexplained", "residual", "unexplained residual"})
    suspects = (
        "market share",
        "recession",
        "competitor pricing",
        "fx loss",
        "currency",
        "headcount freeze",
        "macro",
    )
    lowered = narrative.lower()
    for phrase in suspects:
        if phrase in lowered:
            flags.append(f"Unsupported explanation: {phrase}")
    if "because" in lowered:
        for item in explanation.contributors:
            if item.label.lower() in lowered:
                break
        else:
            if abs(explanation.unexplained_amount) > explanation.residual_tolerance and "unexplained" not in lowered:
                flags.append("Narrative assigns a cause without a verified contributor.")
    return flags
