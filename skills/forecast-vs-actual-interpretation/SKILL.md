---
name: forecast-vs-actual-interpretation
description: Explain a cash forecast miss using Python timing, amount, new, removed, and residual contributors. Use after actual bank or ledger cash is known.
status: new
---

# Forecast Versus Actual Interpretation

## Purpose

Explain why ending cash missed a stored forecast snapshot once actual cash movements are known.

## When to Use

Apply when the Forecast Variance Agent or Forecast Reviewer Agent receives a `ForecastVarianceExplanation`. Python has already compared the immutable snapshot with later actuals.

## Inputs / Evidence

Authoritative Python outputs include:

- forecast versus actual inflows, outflows, and ending cash by week
- contributors classified as timing, amount, new/unforecast, removed/cancelled, or unexplained
- source IDs that match AP invoices, receivables, or payroll schedules

Do not reconstruct the snapshot and do not recalculate the miss.

## Procedure

1. Start from the total ending-cash miss.
2. Keep the Python classification. A late customer receipt is timing, not a new customer.
3. An amount miss is the same source ID with a different dollar amount.
4. New/unforecast activity has no forecast line.
5. Removed/cancelled activity was forecast and did not occur in the actuals window.
6. Residual stays unexplained.

## Decision Criteria

- Contributors plus residual must reconcile to the miss. If Python says they do not, escalate.
- Timing inside the horizon is not a reason to invent extra revenue or expense.
- Do not restate a timing item as an amount item.

## Output Expectations

Narrate each classified miss with its source ID and amount. State the residual separately. Do not merge categories.

## Boundaries

- Do not recalculate weekly cash or the miss.
- Do not invent counterparties for unexplained amounts.
- Do not rewrite the historical forecast snapshot.
- Do not treat a late receipt as cancelled if Python classified it as timing.
