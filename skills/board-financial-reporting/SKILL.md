---
name: board-financial-reporting
description: Write a compact board narrative from Python statements, variances, and the 13-week cash forecast. Use when assembling or reviewing a board pack.
status: new
---

# Board Financial Reporting

## Purpose

Select the material, already-computed facts a board should see and write a short narrative that stays tied to evidence IDs.

## When to Use

Apply when the Board Reporting Agent drafts section narratives or the Reporting Reviewer Agent checks a board pack.

## Inputs / Evidence

Use get_period_metrics, get_variance_facts, and get_cash_forecast. Authoritative numbers are:

- income-statement metrics and comparisons
- variance IDs and contributor transaction IDs
- forecast IDs and weekly cash totals
- reviewer findings and escalation flags

Do not introduce a metric that is not in the Python pack.

## Procedure

1. Lead with revenue, gross margin, operating income, and cash.
2. Use the verified variance narrative for material moves. Do not add a second story.
3. Summarize the 13-week outlook from weekly totals and named risks (holds, late collections).
4. Put unresolved residuals and low-confidence AR in items requiring attention.
5. Attach metric, variance, forecast, or transaction IDs to every material sentence.

## Decision Criteria

- If Python has no contributor, the board pack may not claim a cause.
- A number that does not match the statement is a defect, not a rounding story.
- Attention items are for unresolved, held, or low-confidence items — not strategy advice.

## Output Expectations

Return a short executive narrative and attention list. Every material claim keeps an evidence reference already present in the facts.

## Boundaries

- Do not recalculate financial results.
- Do not invent market, competitive, or macroeconomic explanations.
- Do not add metrics that Python did not produce.
- Do not drop evidence IDs from material claims.
