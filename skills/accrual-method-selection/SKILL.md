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

Typical method choice:

- Stable recurring amounts → last_invoice, simple_average, or contract_commitment.
- Growing usage-based spend → usage_run_rate if usage exists, else weighted_recent_average. Do not blindly use last month when usage or a rate change says otherwise. recent_average is the last three invoices.
- Seasonal spend → seasonal_prior_year when a same-month prior-year invoice exists and naive_recent_average_is_misleading is true.
- Fixed retainer / subscription → contract_commitment.
- Goods received, invoice missing → goods_receipt.
- Invoice already received → no_accrual_needed.
- No reliable signal that work was incurred → insufficient_evidence.

Do not invent a new method name. Do not blend two candidate amounts.

## Output Expectations

Return the selected estimation_method, the copied Python amount, confidence, and a short explanation of why that candidate fit the evidence better than the alternatives.

## Boundaries

- Do not recalculate averages, trends, usage × rate, or receipt totals.
- Do not override Python applicability flags.
- Do not book from a non-applicable candidate.
- Debit the expense_account from the tool output and credit Accrued Expenses; do not invent accounts.
