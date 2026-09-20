---
name: prior-period-precedent
description: Reuse a prior-period treatment only when current evidence still supports it.
status: new
---

# Prior-Period Precedent

## Purpose

Color a later similar case with last period’s decision. Precedent is not a posted policy.

Harbor Electric is the named thread: same vendor, new period, reuse last method only when current GR / contract / usage still supports it. If evidence changed, do not copy last month.

## When to Use

A month-end accrual, prepaid treatment, or similar vendor case may have happened before for the same entity.

## Remainder

1. Retrieve the prior decision_id. Restate it in one or two sentences.
2. Compare current evidence to prior evidence. Amounts, dates, coverage, documents.
3. Reuse only when current facts support the same treatment. Cite the decision_id.
4. If current evidence disagrees, record a deviation and decide from current facts.
5. October’s actual bill can reverse an accrual. That reversal is Kernel. Do not fake it in Memory.

## Boundaries

- Do not treat precedent as a second close DAG or as `ready_tasks`.
- Do not override Python arithmetic or a hard hold.
- Do not invent a fee, GR, or vendor alias to force a match to last month.
- Do not edit `TXN-2026-09-015` or any bank line in Memory to clear a break.
