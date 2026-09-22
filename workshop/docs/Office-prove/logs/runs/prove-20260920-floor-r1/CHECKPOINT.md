# Checkpoint — prove-20260920-floor-r1

| Time | Step | Class | Kernel ids | Note |
| --- | --- | --- | --- | --- |
| 2026-09-20T14:30Z | P0-S01 | RUNS | | currentId prove-20260920-floor-r1; catalog 101 |
| 2026-09-20T14:30Z | P0-S02 | RUNS | | sidecar 64042 |
| 2026-09-20T14:30Z | P0-S03 | RUNS | | not fake; Client attached |
| 2026-09-20T14:31Z | P0-S04 | RUNS | | ap pid 83626 cwd this Computer |
| 2026-09-20T14:31Z | P0-S04b | RUNS | | all 16 idle with pids |
| 2026-09-20T14:32Z | P0-S05 | RUNS | INV-001 | tools.get_invoice ok k_0240b3e7a405 Handle h_c197153e-03d4-4509-a3a6-3856f01822d3 completed |
| 2026-09-20T14:33Z | P0-S06 | INTENDED | | BOT.md + constitution on Computer |
| 2026-09-20T14:33Z | P0-S07 | INTENDED | | collect create_accrual forbidden; kernel did not write |
| 2026-09-20T14:33Z | P0-S08 | INTENDED | | intercept default ctl-pay |
| 2026-09-20T14:33Z | P0-S09 | RUNS | | one Handle store; P2 owns unlock |
| 2026-09-20T14:33Z | P0-S10 | RUNS | | bind table = S04b |
| 2026-09-20T14:33Z | P0-S11 | SKIP | | ask_user not called; model refused |

## Frozen ids

- VENDOR_ID: INV-001 (Acme Supplies, PO-101, amount 12450, vendor_invoice_number ACM-2026-4410). Not INV-S12.
- CASH_ID / payment_id:
- BANK_TXN $12.40: TXN-2026-09-015
- Other:

## Replay rule if HARD

Replay from: P0-S04 bind, then S05. Do not continue a dirty Handle graph on this floor instance for pipes — use prove-20260920-month-r1.
