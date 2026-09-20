---
name: month-end-close-coordination
description: Coordinates month-end close tasks, blockers, and reviewer routing without inventing balances.
status: new
---

# Month-End Close Coordination

## Purpose

Select the next valid close task, explain blockers, and summarize unresolved fail-closed Kernel statuses. Arithmetic and close eligibility stay in Python.

## When to Use

Apply when Bot close wears Profile coordinate, inspects the checklist, decides the next Profile Wake, or prepares the close-status narrative.

## Inputs / Evidence

Use the structured close tasks, dependency graph, reconciliation statuses, journal IDs, and exception list already produced by Python.

## Procedure

1. Read task status. A child task cannot complete before its dependencies.
2. Independent workflows may continue while an unrelated task is blocked.
3. Route preparer work as a new Wake of Bot close with that Profile. Do not union Grants.
4. List fail-closed Kernel statuses exactly as Python recorded them. Do not relabel them as cleared. Queue owner is ctl-books.
5. Prepare a narrative only after Python has computed period status. Do not mark CLOSED.

## Decision Criteria

- READY tasks with satisfied dependencies may start as a new Profile Wake.
- NEEDS_REVIEW and BLOCKED tasks stay fail-closed. Handle ctl-books. Do not ask a human.
- The period may close only when Python evaluate_close_gates passes and ctl-books / lock concurs. Coordinate does not mark CLOSED.

## Output Expectations

Return next tasks, blocked tasks, waiting-on-human items, and a coordination narrative. Do not return invented balances.

## Boundaries

- Do not invent ledger amounts or evidence.
- Do not override Python validation.
- Do not force-close a failed reconciliation.
- Do not ignore fail-closed Kernel statuses named HUMAN_REVIEW.
- Do not ask a human. Do not mark CLOSED.
- Do not alter journal entries.
