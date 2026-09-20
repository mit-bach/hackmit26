# Surface — Verifiers and SoD

Slugs: `ctl-pay`, `ctl-cash`, `ctl-books`.
Law: SUPERSEDES, constitution, grain §8.
Code: Client `verifier.ts`, `intercept.ts`, `catalog.overrides.json` denylist, Kernel `sod_forbid`.

---

## Intended function of this surface

Uncertain or high-stakes work gets a second standing identity that looks for reasons to refuse. The proposing Bot does not approve itself. A human is not in the completion path.

Partition by stake, not by twin count:

| Verifier | Stake |
| --- | --- |
| `ctl-pay` | Money out or off the books: match concurrence, pay-run release, write-off |
| `ctl-cash` | Cash identification: material apply, rec sign-off |
| `ctl-books` | Books: treatments, period lock |

Kernel still vetoes. A Verifier that concurs on a planted trap Kernel marked illegal is a bug in the Verifier. Kernel still refuses the post.

Peer Handle is not approval. `ap` sending to `pay` is not concurrence.

`audit` is not a Verifier.

---

## What is good

Three Verifiers instead of twelve reviewer Display names.

Denylist so Payment Audit cannot rebuild the run, so AP Reviewer cannot hold RECORD_TOOLS, so accrual writes are not on lock-only Profiles (overrides exist; lock Grant is still `ops: []`).

Live ctl-pay REFUSE on incomplete INV-S12 packet. “Look for reasons to refuse” happened once on the bus.

BOT.md voice on Verifiers is sharper than Operator BOT.md files: not a rubber stamp, packet must be complete, Kernel must already allow.

---

## What is broken

### HUMAN_REVIEW string vs human queue (T9)

Kernel statuses keep the name. SUPERSEDES remaps the owner. Fixtures still expect the string. CLI review commands still exist. Docs and README in `.cfo/` still talk like a person. Models will call the wrong owner if BOT.md and Kernel comments disagree.

### Two unlock paths (T9)

See `surfaces/harness-protocol.md`. Client CONCUR file vs Harness Handle.

### intercept.json mismatches grain (T2)

Collect → ctl-cash in intercept. Write-off → ctl-pay in grain and handle-map.
Default → operator.

### Verifier Grants too thin or too twin-like (T9, T7)

Too thin: cannot re-perform source (RECORD_TOOLS stripped).
Too twin-like: same skills as the doer (`cash-application` on apply and ctl-cash review-apply).

ctl-pay review-pay may only read cash position and treasury policies. It cannot see the candidate list it was denylisted from rebuilding. Refuse-for-incompleteness is easy. Refuse-for-wrong-rank is hard without facts.

### ask_user still taught (T6)

Harness protocol skill. Client blocks the tool if loaded. Without Client `-e`, a Harness-only worker still has it. approvalLevel never is not a tool filter.

### No reporting Verifier (intentional)

Story has no ctl-*. Material doubt is INSUFFICIENT. Audit samples later. Fluent wrong causal story is the residual risk. Named in `pipes/close-story-audit.md`. Do not add ctl-story without failing Tests A–D.

---

## Capability this surface must possess

When Verifiers are adequate:

1. Every fail-closed Kernel status that used to mean “ask a person” has a Verifier owner.
2. That owner is bound, has read facts enough to refuse for a reason, and cannot post the Operator Bot’s write.
3. Unlock of a consequential Kernel op waits on that Verifier’s done Handle, one store.
4. Operator can stop a Bot. Operator cannot complete pay-run or lock by clicking approve.
5. Write-off is ctl-pay. Apply review is ctl-cash. Lock is ctl-books. No intercept table silently swaps those.

This file does not design Verifier Memory. Refuse-reason habits are specialist novelty on the Verifier side.
