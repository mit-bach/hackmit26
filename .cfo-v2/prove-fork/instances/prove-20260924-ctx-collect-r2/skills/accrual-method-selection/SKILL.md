---
name: accrual-method-selection
description: Selects the most defensible accrual estimation method from Python-computed candidates. Use after evidence shows an unbilled expense should be accrued.
status: extracted
---

# Accrual Method Selection

## Purpose

Choose which Python estimate candidate to book when an accrual is required. The model selects a method; Python owns the amount.

## When to Use

Apply after accrual-evidence-evaluation has found that an expense was probably incurred this period and no invoice exists.

## Inputs / Evidence

Use get_estimate_candidates / compute_accrual_estimate. Each candidate includes method, applicable flag, amount, rationale, and inputs. Also consider contract cadence, usage, receipts, and whether naive_recent_average_is_misleading is true.

## Procedure

1. Ignore methods Python marked not applicable.
2. Choose the method that best fits the evidence — not a single naive rule and not automatically last month.
3. If accruing, call create_accrual with that method so the ledger can be updated from the Python amount.
4. Copy estimated_amount from the Python candidate exactly, including cents.

## Decision Criteria

Prefer stronger evidence types over weaker proxies. Do not key off vendor names.

1. Current-period usage × contracted rate → usage_run_rate.
2. Goods received, invoice missing → goods_receipt.
3. Fixed retainer / subscription due this period → contract_commitment.
4. Same-month prior-year amount when naive_recent_average_is_misleading is true → seasonal_prior_year.
5. Stable recurring history → last_invoice or simple_average.
6. Recent average or trend only when no stronger evidence exists.

Recent average is a fallback, not a default. Do not prefer it merely because it is simple.
Direct and current-period evidence outranks stale or smoothed history.
Invoice already received → no_accrual_needed.
No reliable incurred signal → insufficient_evidence.

Do not invent a new method name. Do not blend two candidate amounts.

## Output Expectations

Return the selected estimation_method, the copied Python amount, confidence, and a short explanation of why that candidate fit the evidence better than the alternatives.

## Boundaries

- Do not recalculate averages, trends, usage × rate, or receipt totals.
- Do not override Python applicability flags.
- Do not book from a non-applicable candidate.
- Debit the expense_account from the tool output and credit Accrued Expenses; do not invent accounts.
