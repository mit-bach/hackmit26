# PROVED — wren 0001

Part: fix two Verifier defects from `workshop/docs/Office-show/DESIGN-REVIEW.md` section 3 in `.cfo-v3/cfo/extensions/`.

## Test command

Run from `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo` (Node v26.9.0, native TypeScript):

```
node --test extensions/verifier-wiring.test.ts
```

## Output on the new code (exit 0)

Full log: `engineers/wren/new-run.txt`.

```
▶ Verifier concurrence parse
  ✔ prose that mentions CONCUR is not CONCUR
  ✔ accepts only a structured decision
  ✔ a completed Handle whose result says 'I do not concur' does not unlock
▶ call_connected_tool through the Pi registration path
  ✔ unlocks a consequential op after CONCUR when the model retries with the same idempotency_key
  ✔ honors an explicit handle_id the model passes
ℹ tests 5  pass 5  fail 0
```

## Output on the old code (exit 1)

The same test file ran before the fix. Full log: `engineers/wren/old-run.txt`. The old sources are in `engineers/wren/old/`. Each test fails on the defect, not on setup:

| Test | Old-code failure |
| --- | --- |
| prose that mentions CONCUR is not CONCUR | `handleConcurrence("I do not concur")` returned `CONCUR` |
| accepts only a structured decision | `{"decision": "I do not CONCUR"}` returned `CONCUR`, expected `none` |
| 'I do not concur' does not unlock | `completedHandleAllowsOp` returned `true` |
| unlocks after CONCUR, same idempotency_key | after a CONCUR Handle, the retry still returned `verifier_required` |
| honors an explicit handle_id | `call_connected_tool` schema has no `handle_id` |

## Diff summary

Full diff: `engineers/wren/fix.diff`.

1. `intercept.ts` `handleConcurrence`: accepts only a trimmed first line exactly `CONCUR` or `REFUSE`, or a whole-text JSON object whose `decision` is exactly `"CONCUR"` or `"REFUSE"`. All other text returns `none`. The prefix match and the word scan are gone.
2. `intercept.ts` new `pendingHandleIdsForKey` and `resolvePendingHandleId`. They scan `workspace/verifier/pending/*.json` for rows with the same `fromSlug`, `op`, and idempotency key, newest first. They return the Handle that already allows the op, else the newest, else `null`. Rows written before this change have no `idempotencyKey`. For those rows, the key comes from the packet file name `<key>.json`.
3. `intercept.ts` `persistPendingHandle` and `call.ts` `interceptVerifier`: the pending index row now records `idempotencyKey`.
4. `index.ts` `call_connected_tool`: new optional `handle_id` parameter. If the model passes it, that id goes to `callConnectedTool`. If not, the id comes from `resolvePendingHandleId` by idempotency key. The literal `null` is gone. There is one new prompt guideline, and the intercept `instruction` in `call.ts` now tells the model to call again with the same `idempotency_key` after CONCUR.
5. New `extensions/verifier-wiring.test.ts`, beside `facade.test.ts`. The Pi-path tests load `index.ts` default export with a fake `PiExtensionApi` and call the registered `call_connected_tool.execute`. They do not call `callConnectedTool` directly. The tests use a scratch Computer (copies of `cfo/catalog.json`, `grants.json`, `slug-map.json`) and a fake `HARNESS_V2_ROOT/src/send.ts`. The fake returns Handle ids `h-wren-N`, so the test proves the lookup finds a Handle id that is not the idempotency key.

## What is proved

- A completed Harness Handle with first line `CONCUR` now unlocks the op on a model retry through the Pi tool, with no `handle_id` argument.
- A prose refusal ("I do not concur") on the first Handle stays locked. The retry opens a second Handle, and a CONCUR on that second Handle unlocks the op. The lookup picks the allowing Handle among several.
- A CONCUR for one idempotency key does not unlock a call with a different key.
- Each consequential intercept went to `ctl-books` (3 sends recorded).
- "Unlocked" means the call reached the sidecar step: `sidecar_unavailable`, because the scratch Computer has no `cfo/kernel.port`.

## What is not proved

- Typecheck: `.cfo-v3/cfo` has no `node_modules`. `tsc` and `typebox` are not installed, so `npm test` (tsc) did not run. Node type stripping ran the files. It does not check types.
- `typebox` itself: the test resolves the real package if installed. Here it is not installed, so a schema-shaped stub loaded instead. The `handle_id` schema assertion runs against that stub.
- Live Pi and live Harness `sendPrompt` were not exercised.
- Not fixed (outside this part): a CONCUR binds to Bot + op + idempotency key, not to `args`. A model that reuses a concurred key with different args still passes the gate. The Kernel sidecar idempotency check is the only guard there.

## Regression check

`node --test extensions/facade.test.ts` gives the same result before and after the change: 13 pass and 3 fail. The 3 failures come from the `.cfo-v3` layout, not from this change. The stripe payout binding test fails. `office/bots/collect/BOT.md` and `office/constitution.md` do not exist. `harness/intercept.json` does not exist.
