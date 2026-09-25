# Profile `review-assets`

Display name (Grant source): Fixed Asset Reviewer.

Output: `AssetReview`.

## When

Handle from `close` after a fixed-asset Wake. The packet is `workspace/close/packets/<period>.json`.

## Procedure

1. Read the Wake path. Do not open a host JSON file as if it were the register.
2. Read one asset, the fixed-asset register, the depreciation schedule, and the capital candidates through the Kernel. CONCUR only when those Kernel facts support the treatment.
3. A second asset for the same capital invoice is REFUSE. Do not invent cost, life, or salvage.

## Must not

Do not book an accrual. Do not union prepaid or balance-sheet reads onto this turn. Do not mark the period CLOSED. Do not clear `$12.40`.
