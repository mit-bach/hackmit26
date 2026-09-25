---
name: month-end-close-review
description: Reads close gates and refuses lock when evaluate_close_gates failed. Cannot mark CLOSED.
status: new
---

# Month-End Close Review

## Purpose

Bot `ctl-books` Profile `lock` reads `evaluate_close_gates` and the period pack. It looks for reasons to refuse. It cannot mark CLOSED.

## When to Use

Final close review for a period. Call the finance record and the finance record.

## Remainder

CONCUR (`APPROVE_CLOSE`) only when `gate_passed` is true and the packet is complete. If gates failed, `REJECT_CLOSE`. Python ignores `APPROVE_CLOSE` when gates fail.

Planted `$12.40` is unexplained. Do not relabel it as timing. Do not force-match it.

## Output

`FinalCloseVerdict`: `APPROVE_CLOSE`, `REJECT_CLOSE`, or `REQUEST_REVIEW`. None of these mark CLOSED. Kernel `close.month_end` is the only door that can later mark CLOSED.

## Boundaries

- Do not recalculate account balances or journal totals.
- Do not mark the period closed to hide an exception.
- Do not treat NEEDS_REVIEW as complete.
- Do not invent a cleared status.
- Do not the finance record.
- Do not ask a human.
