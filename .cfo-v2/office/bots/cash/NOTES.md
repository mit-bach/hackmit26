# NOTES — Cash (prompt 04)

Date: 2026-09-20. Disk wins.

Unmatched bank lines stay on Bot `cash`. Rec sign-off stays on `ctl-cash`. Cash does not own vendor bills, does not apply AR, and does not move money.

## Identifiers (T11)

Cash copies apply/pay identifiers. It does not re-guess the counterparty from a memo. If those pipes have not written an identifier packet, fail closed and Handle `ctl-cash`. Kernel demo rec still generates candidates without identifiers. Office host `cash_recon.office.run_cash_office` requires them when `require_identifier=True`.

Apply identified-deposit packets may still be Kernel JSON under `runs/ar/packets/` rather than Harness Handles. Cash reads the fields. It does not rewrite AR or AP.

## $12.40 (T12)

`TXN-2026-09-015` stays `UNEXPLAINED_DIFFERENCE`. `ctl-cash` REFUSE MATCHED. Period cannot be RECONCILED. Close stays BLOCKED. Helios `TXN-2026-09-011` is FEE_NETTED only with Kernel fee evidence (`ADV-729103` in operational books; isolated cousin `FEE-729103`). Holdout ADV residual is not loaded.

## Stripe (T3)

Constructor Display name is **Stripe Payout Agent**. Compiler writes Grants. `invoice_candidates` stays 0. Simulated unpack only. Not RecBench office-live. Not live Stripe keys.

## Handles (T5)

Kernel JSON under `runs/cash_recon/handles/` still exists. Office host also writes Harness Handles under `harness/bots/bot_ctl_cash/handles/`. Trusted cash is `workspace/cash/trusted/<period>.json`. Close gets a Harness Handle only when Kernel allows and `ctl-cash` concurs. The judged September pack does not.

## bind_case (T8)

Still Sidecar/host session setup. Not a Catalog op. BOT.md done-when does not tell the Bot to call it.

## Floor

Intercept default is Bot `ctl-pay`. Cash override is `ctl-cash`. `autoRoutines: false` remains Floor-owned. See `docs/Agentic-update/evidence/NOTES-floor-hole.md`. This agent did not rewrite `RUN.md`.

## Proof

```bash
PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest .cfo/tests/test_cash_office.py .cfo/tests/test_cash_recon.py .cfo/tests/test_cash_bind_case.py .cfo/tests/test_integrations.py -q
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

The command that still blocks $12.40: `test_northstar_12_40_stays_unexplained_and_blocks_reconciled`.
