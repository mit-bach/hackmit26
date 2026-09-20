# NOTES — Cash pipe (prompt 04)

Date: 2026-09-20. Disk wins.

Standing Bots: `cash` (unmatched bank line), `ctl-cash` (rec sign-off), `stripe` (payout waterfall, granted). Bank stays a Bot with no webhook in `WEBHOOK_PROVIDERS`.

## Honest state

| Claim | State |
| --- | --- |
| Integer-cent tie-out | Kernel-live. Kept. |
| `$12.40` / `TXN-2026-09-015` | Unexplained. ctl-cash cannot MATCHED. Period not RECONCILED. |
| Helios `TXN-2026-09-011` | FEE_NETTED only with Kernel fee evidence. Operational id is `ADV-729103`. Isolated cousin still matches only with `FEE-729103`. |
| Stripe | Constructor **Stripe Payout Agent**. Grants compiled. `invoice_candidates == 0`. Simulated. Not RecBench office-live. |
| Identifier trust | Kernel function + test. Office fails closed if apply/pay have not written identifiers. |
| Harness Handle cash → ctl-cash | Kernel host writes `harness/bots/bot_ctl_cash/handles/`. Trusted cash packet at `workspace/cash/trusted/<period>.json`. Close Handle only when Kernel allows. |
| bind_case | Sidecar/host. Not a Catalog op. |
| RecBench grouped ACH office-live | Not claimed. |

## Floor hole

`autoRoutines: false` remains. Intercept default is `ctl-pay`. Cash override is `ctl-cash`. Do not park unnamed cash ops on the Operator.

## Stop

Do not load holdout ADV residual into operational books. Do not give `ctl-cash` posting tools. Do not start the 13-week forecast here.
