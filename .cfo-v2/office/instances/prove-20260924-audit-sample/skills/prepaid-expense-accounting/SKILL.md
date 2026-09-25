---
name: prepaid-expense-accounting
description: Chooses among Python prepaid treatments (immediate expense, straight-line monthly, daily proration) using service-period evidence. Use when a payment covers future months.
status: new
---

# Prepaid Expense Accounting

## Purpose

Decide whether a payment is a prepaid asset and which Python amortization method fits the service period.

## When to Use

Apply when preparing or reviewing insurance, software, rent, or other amounts paid before the related service is consumed.

## Inputs / Evidence

Use get_prepaid_treatment_candidates and get_prepaid_schedule. Each candidate includes applicability, amount, and rationale. Also inspect source_document_id and evidence_refs.

## Procedure

1. If the source document is missing, do not amortize. Request evidence.
2. Ignore methods Python marked not applicable.
3. Prefer daily_prorate when the first or last month is a partial service period.
4. Prefer straight_line_monthly when the contract covers full calendar months.
5. Prefer immediate_expense only when Python marks that candidate applicable (one calendar month).
6. Copy schedule amounts from Python. Do not invent catch-up math for late discovery.

## Decision Criteria

- Multi-month remaining service → prepaid, not period expense.
- Same-month start and end → immediate expense is allowed.
- Partial first or last month → daily proration is stronger than equal months.
- Missing policy or contract → insufficient_evidence.

## Output Expectations

Return the selected method, copied Python amounts, evidence used, and a short explanation of why that candidate fit better than the alternatives.

## Boundaries

- Do not recalculate monthly or daily amounts.
- Do not post a period Python already marked posted.
- Do not amortize before the service start or after the service end.
- Do not treat a capital asset purchase as a prepaid.
