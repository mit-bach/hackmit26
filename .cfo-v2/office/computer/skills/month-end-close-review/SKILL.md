---
name: month-end-close-review
description: Decides whether a month can close from the checklist, blockers, and unsigned reconciliations. Use at final close review.
status: new
---

# Month-End Close Review

## Purpose

Independently decide whether remaining close tasks, exceptions, and reconciliations allow the period to be marked closed.

## When to Use

Apply when reviewing unresolved exceptions or performing final close review for a period.

## Inputs / Evidence

Use the close checklist statuses, exception list, reconciliation statuses, journal/evidence references already produced by upstream tasks, and any prior-period accrual decision_id cited on the packet.

## Procedure

1. A task is complete only when its dependencies are complete and its own status is COMPLETE.
2. NEEDS_REVIEW, BLOCKED, and FAILED upstream work are unresolved blockers.
3. Unsigned HUMAN_REVIEW or missing-evidence reconciliations block close.
4. Approve close only when every required task is COMPLETE and no material exception remains.
5. When an accrual cites a prior-period decision_id, confirm current evidence was checked and that a material methodology deviation is visible if the treatment changed.

## Decision Criteria

- All checklist items COMPLETE and recs signed off → the period may close.
- Any unexplained difference, missing evidence, or failed task → do not close.
- Corrected failed tasks may be retried; do not repost completed journals.

## Output Expectations

Return only one structured decision:

- `APPROVE_CLOSE`
- `REJECT_CLOSE`
- `REQUEST_REVIEW`

Python enforces the hard gates. An `APPROVE_CLOSE` decision is ignored when deterministic checks still show a blocker.

## Boundaries

- Do not recalculate account balances or journal totals.
- Do not mark the period closed to hide an exception.
- Do not treat NEEDS_REVIEW as complete.
- Do not invent a cleared status for an account the packet still flags.
- Do not override a failed Python gate.
