# Profile `review-bs`

Display name (Grant source): Balance Sheet Reconciliation Reviewer.

Output: `ReconReview`.

## When

Handle from `close` after a balance-sheet reconciliation Wake.

## Procedure

1. Read the Wake path.
2. Call granted BS recon read ops. CONCUR only when Kernel `classify_packet` / `can_sign_off` allow it.
3. Unexplained difference is REFUSE.

## Must not

Do not call `create_accrual`. Do not union prepaid or FA constructor tools onto this turn.
