---
name: month-end-close-coordination
description: Coordinates month-end close tasks, blockers, and reviewer routing without inventing balances.
status: new
---

# Month-End Close Coordination

## Purpose

Select the next valid close task, explain blockers, and summarize unresolved HUMAN_REVIEW items. Arithmetic and close eligibility stay in Python.

## When to Use

Apply when the Close Manager inspects the checklist, decides what can start, or prepares the close-status narrative.

## Inputs / Evidence

Use the structured close tasks, dependency graph, reconciliation statuses, journal IDs, and exception list already produced by Python.

## Procedure

1. Read task status. A child task cannot complete before its dependencies.
2. Independent workflows may continue while an unrelated task is blocked.
3. Route preparer work to the owning function. Route unsigned reconciliations to the reviewer.
4. List HUMAN_REVIEW items exactly as Python recorded them. Do not relabel them as cleared.
5. Prepare a narrative only after Python has computed period status.

## Decision Criteria

- READY tasks with satisfied dependencies may start.
- NEEDS_REVIEW and BLOCKED tasks wait on humans or failed validation.
- The period may close only when Python marks every required task COMPLETE and no unresolved HUMAN_REVIEW remains.

## Output Expectations

Return next tasks, blocked tasks, waiting-on-human items, and a coordination narrative. Do not return invented balances.

## Boundaries

- Do not invent ledger amounts or evidence.
- Do not override Python validation.
- Do not force-close a failed reconciliation.
- Do not ignore HUMAN_REVIEW.
- Do not alter journal entries.
