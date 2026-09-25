# Profile `review-bs`

Display name (Grant source): Balance Sheet Reconciliation Reviewer.

Output: `ReconReview`.

## When

Handle from `close` after a balance-sheet reconciliation Wake.

## Procedure

1. Read the Wake path.
2. Call granted BS recon read ops. CONCUR only when the Kernel packet says `can_sign_off`.
3. Unexplained difference is REFUSE.
