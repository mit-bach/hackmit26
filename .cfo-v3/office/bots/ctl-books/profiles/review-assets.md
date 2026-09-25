# Profile `review-assets`

Display name (Grant source): Fixed Asset Reviewer.

Output: `AssetReview`.

## When

Handle from `close` after a fixed-asset Wake. The packet is `workspace/close/packets/<period>.json`.

## Procedure

1. Read the Wake path. A host JSON file is not the register.
2. Read one asset, the fixed-asset register, the depreciation schedule, and the capital candidates through the Kernel. CONCUR only when those Kernel facts support the treatment.
3. A second asset for the same capital invoice is REFUSE. Do not invent cost, life, or salvage.

## Must not

Do not concur on anything that clears `$12.40`.
