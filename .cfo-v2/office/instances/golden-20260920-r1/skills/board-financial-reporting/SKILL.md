---
name: board-financial-reporting
description: Write a compact board narrative from Kernel facts. Unlocked drafts label every number UNLOCKED.
status: new
---

# Board Financial Reporting

## Purpose

Select Kernel facts a board should see. Stay tied to evidence IDs. Do not own the books.

## When to Use

Bot `story` Profile `board`. `audit` samples the pack. There is no reporting Verifier.

## Remainder

Lead with revenue, gross margin, operating income, and cash **as Python computed them**. Choose which verified Kernel contributor belongs in the lead sentence. Do not add a second story. Do not fill a residual.

If `lock_status` is not `CLOSED`, label every number `UNLOCKED`. Forecast starting balance is trusted cash. Unreconciled GL cash is not trusted cash. If trusted cash is missing, the 13-week start is refused.

## Boundaries

- Do not recalculate financial results.
- Do not invent market, competitive, or macroeconomic explanations.
- Do not add metrics that Python did not produce.
- Do not drop evidence IDs from material claims.
- Do not treat an unlocked draft as a closed pack.
