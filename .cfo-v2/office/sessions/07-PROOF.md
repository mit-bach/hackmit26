# Session 07 proof — Bot `cash`

Handle completion was **not** live-proven (no Pi turn, no live `bot_send_prompt`). Proofs are Kernel / unit / disk.

## Commands

```bash
.cfo/.venv/bin/python -m pytest .cfo/tests/test_cash_bind_case.py .cfo/tests/test_cash_recon.py -q
# 16 passed

.cfo/.venv/bin/python -m pytest .cfo/tests/test_cfo_integration.py .cfo/tests/test_review_loop.py -q
# 20 passed

node --experimental-strip-types --test .cfo-v2/office/computer/cfo/cashCase.test.ts
# 3 passed

.cfo/.venv/bin/python .cfo-v2/office/sessions/07/prove_cash.py
```

## Disk (Computer)

After `prove_cash.py`:

| Path | What |
| --- | --- |
| `office/computer/runs/cash_recon/cases/2026-09.json` | Bound case. Schema `cfo.cash_recon.case.v1`. 12 bank, 13 ledger, 16 candidates. Proposed fee `posted` flags are `false`. |
| `office/computer/runs/cash_recon/handles/cash-REC-010-ctl-cash.json` | Verifier Handle. `toSlug` `ctl-cash`, `profile` `review-rec`, `queueOwner` `ctl-cash`, `humanQueue` false. |
| `office/computer/runs/cash_recon/packets/cash-rec-REC-010.json` | `$12.40` packet. `difference_minor` 1240. `kernel_status` `HUMAN_REVIEW`. Not MATCHED. |
| `office/computer/runs/cash_recon/session-07-summary.json` | Compact summary of the run. |

## Seeded $12.40 still not MATCHED

- `period_status` = `OPEN` (not `RECONCILED`)
- `unexplained_status` = `HUMAN_REVIEW`
- `unexplained_difference_minor` = 1240
- Queue owner is Bot `ctl-cash`, not the human Operator

## Stripe payout still Kernel waterfall

- `po_1HackMIT97420` `provider_status` `MATCH`
- `integrations.cash.reconcile_payout`: expected 9742000 cents = actual 9742000 cents
- Candidate evidence cites `expected_payout` / `actual_payout` from that breakdown

## `cash` cannot `create_accrual` or release a pay-run

Compiler grants for Cash Reconciliation Preparer and Cash Exception Investigator are only the five `cash_recon.tools.*` reads. They omit `accrual.tools.create_accrual` and every `scheduling.tools.*` id. Catalog contains `create_accrual`; cash Profiles are not granted it. There is no `release_pay_run` Catalog op today; cash still cannot call scheduling reads.

Client filter: `office/computer/cfo/cashGrants.ts` (`cashMayCall`).

## Persistence

`bind_case` writes `<computer>/runs/cash_recon/cases/<period>.json` atomically. A second process with `CFO_CASH_CASE_DIR` / `CFO_CASH_CASE_ID` reloads candidates (`test_bound_case_survives_unbind_and_second_process`).
