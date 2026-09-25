# plover: facade.test.ts on .cfo-v3

Command: `node --test extensions/facade.test.ts` from `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo`.

- Before: 16 tests, 13 pass, 3 fail.
- After: 16 tests, 16 pass, 0 fail.

Files changed:

- `.cfo-v3/harness/intercept.json` (new)
- `.cfo-v3/cfo/extensions/facade.test.ts` (two tests)

No other extension source was edited. No banned file was added.

## 1. `intercept collect write-off owner is ctl-pay`

Failure: `ENOENT` on `.cfo-v3/harness/intercept.json`.

Decision: runtime input. Create the file.

Change: added `.cfo-v3/harness/intercept.json` with the same shape and routes as `.cfo-v2/office/computer/harness/intercept.json`. `default` is `{kind: bot, bot: ctl-pay}`. `collect`, `ap`, and `pay` route to `ctl-pay`. `apply`, `cash`, and `stripe` route to `ctl-cash`. `close` routes to `ctl-books`. The test is unchanged.

Why:
- `.cfo-v2/office/computer/harness/PROTOCOL.md` line 39 says the Harness decides between `ask_user` and waiting on a Verifier Bot Handle from `harness/intercept.json` `kind`. That makes the file a Harness runtime input, not old-layout proof.
- One v2 comment was dropped: `Align with cfo/handle-map.json`. `.cfo-v3/cfo/handle-map.json` does not exist.

Observed: no `.ts`, `.py`, or `.sh` file under `.cfo-v3` or `.cfo-v2` (instances excluded) reads `intercept.json`. The only matches were the `facade.test.ts` copies. The mission said `intercept.ts` loads this file. The current `.cfo-v3/cfo/extensions/intercept.ts` does not read it. It routes through `verifier.ts` `routeVerifier`. The Harness itself is outside this tree, so I did not verify how it reads the file.

## 2. `BOT.md and constitution are readable from Computer cwd`

Failure: `office/constitution.md` does not exist in `.cfo-v3`. The `office/bots/collect/BOT.md` assertion passed.

Decision: ban list or old-layout proof. Do not restore `constitution.md`.

Change: renamed the test to `BOT.md and system.md are readable from Computer cwd`. The constitution assertion now checks `office/system.md`, which exists in `.cfo-v3/office/`. The `BOT.md` assertion is unchanged.

## 3. `stripe payout has no Connectors until a constructor exists`

Failure: `bind.connectors` was `true`, but the test expected `false`.

Decision: neither case in the mission. No file is missing. The test's premise is out of date.

Evidence:
- `.cfo-v3/cfo/slug-map.json` maps `stripe/payout` to `Stripe Payout Agent`.
- `.cfo-v3/cfo/grants.json` has a `Stripe Payout Agent` grant with `source: integrations/agent.py`.
- `.cfo-v3/kernel/integrations/agent.py` builds `Agent(name="Stripe Payout Agent", ...)`.

The constructor exists, so the old condition "until a constructor exists" has been met. This test also fails on `.cfo-v2/office/computer`: 15 pass, 1 fail, same test.

Change: renamed the test to `stripe payout binds to Stripe Payout Agent and sees only payout reads`. It now asserts:
- `connectors` is `true` and there is no `refuseReason`.
- `displayName` is `Stripe Payout Agent`.
- The visible ops are exactly `integrations.tools.list_processor_payouts`, `integrations.tools.get_processor_payout`, and `integrations.tools.get_payout_waterfall`.
- Every visible op has mutability `read`.

The test still checks the grant boundary. Stripe cannot see ops outside its grant.

Not proved: whether the parent wants stripe unbound in v3 on purpose, with the grant removed instead. If so, the fix is in `grants.json` or `slug-map.json`, which is outside plover's write scope, and this test should be reverted.
