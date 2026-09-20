# Prompt 01 — Floor (bus and bind)

You are one implementing agent. You own **deployability of the bus**. You do not own a finance pipe. When you are done, a later AR, AP, cash, or close agent can bind a Bot, call Kernel through the Client extension, complete a Handle, and have a Verifier unlock mean the same object.

If you make attach vague, they will each half-fix `RUN.md` and you will have five runbooks.

Read first, in this order:

1. `docs/Agentic-update/prompts/00-SHARED-LAWS.md`
2. This file
3. `docs/Agentic-update/01-intended-office.md`
4. `docs/Agentic-update/02-failure-taxonomy.md`
5. `docs/Agentic-update/03-novelty-boundary.md`
6. `docs/Agentic-update/04-what-is-good.md`
7. `docs/Agentic-update/surfaces/harness-protocol.md`
8. `docs/Agentic-update/surfaces/bot-md.md`
9. `docs/Agentic-update/surfaces/verifiers.md`
10. `docs/Agentic-update/surfaces/wakes-and-routines.md`
11. `docs/Agentic-update/surfaces/other-prompt-layers.md`
12. `docs/Agentic-update/surfaces/grants-and-tools.md`
13. `docs/Agentic-update/evidence/live-computer-2026-09-20.md`
14. `design-workshop/dominik/cfo-bot-grain.md`
15. `design-workshop/dominik/HARNESS-V2-DEPLOY-PLAN.md`
16. `.cfo-v2/office/constitution.md`
17. `.cfo-v2/office/SUPERSEDES.md`
18. `.cfo-v2/office/RUN.md`
19. `.cfo-v2/office/computer/harness/roster.json`
20. `.cfo-v2/office/computer/harness/client.json`
21. `.cfo-v2/office/computer/harness/extensions.json`
22. `.cfo-v2/office/computer/harness/intercept.json`
23. `.cfo-v2/office/computer/cfo/handle-map.json`
24. `.cfo-v2/office/computer/cfo/extensions/intercept.ts`
25. `.cfo-v2/office/computer/cfo/extensions/verifier.ts` if present

Then Read live disk. The 2026-09-20 evidence snapshot can be stale. Disk wins.

Do not read prompts 02, 03, 04, or 05. Do not implement their pipes.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

Replace “documented `--fake` plus a Kernel that scores well” with: **live Pi workers**, Client extension attached on serve/supervisor (not only `pi-bot.sh`), sidecar up, identity files readable from Computer cwd, **one Handle store** as Verifier unlock truth, intercept default **not** the human Operator.

You ship the floor the four pipes stand on. You do not collect cash. You do not match a bill. You do not close September.

---

## Why this is a separate agent

Harness `src/` must stay generic. Finance types stay out. Pipe agents that “just add an extra `-e` in a comment” will fight you. Two Handle stores cannot be fixed from BOT.md. BOT.md cwd cannot be fixed from a Skill. `--fake` in RUN.md will be what a tired operator types the night before the demo.

You specialize in: bind, attach, cwd, unlock, intercept default, extra `-e` persistence, fake vs live as labeled switches.

---

## Categories you close

- **T5** — bus not attached. Kernel pytest is not office-live. Fake workers echo inboxes.
- **T6** — BOT.md cwd miss. `ask_user` taught as Operator unless Client loads.
- **T9** — two Handle stores. Intercept default Operator.
- **T12** — `--fake` as the documented office. `examples/cfo-floor` treated as this Roster.

You do not close T3 send ImportError (02). You do not close T11 INV-S12 (03). You do not bind World (02, Tests A–D). You do not empty-ops close Profiles (05).

---

## Why the current Floor fails

### Documented boot is `--fake` (T5, T12)

`.cfo-v2/office/RUN.md` step 3 still teaches:

```
npm run serve -- --computer … --fake --no-open
```

Fake workers complete Handles with `` `[${slug}] ${prompt}` ``. No model. No Kernel. Not fifteen finance Bots.

`client.json` is a second boot: lazy spawn, sidecar command, grok-4.5. Two runbooks. Operators will pick the short one.

`--fake` may remain a **labeled protocol demo**. It must not be the happy path.

### Extra `-e` used to be only `pi-bot.sh`

As of the 2026-09-20 snapshot, `harness/extensions.json` extraExtensions already points at the Client, and `client.json` has `clientSkills: true`. Attach is no longer only a shell script. **Prove it is persisted on `serve` / supervisor argv or config**, not only on a helper script that a documented fake serve never calls. If disk has already flipped this, keep it and document the live command. If serve still drops `-e`, that is your bug.

### Two Handle stores (T9)

Harness writes `harness/bots/<botId>/handles/`.
Client intercept unlocks from `workspace/verifier/handles/` with `decision: CONCUR`.
`completedHandleAllowsOp` reads the Client file. A Verifier finishing a Harness Handle does not unlock the Kernel op.

Deploy plan Phase 3 named this. Live Computer still has both. Pipe agents cannot Grant their way out of this.

### Intercept default Operator (T9)

`intercept.json`: `"default": { "kind": "operator" }`. Per-Bot overrides exist for ap/pay/apply/collect/cash/close/books/story. Email, stripe, bank, audit, Verifiers themselves, and World (if 02 binds it) follow default.

Collect override is `ctl-cash`. Grain write-off is `ctl-pay`. `handle-map.json` already says collect write-off → `ctl-pay`. **Align intercept with handle-map and grain.** Collect write-off is your intercept row even though 02 owns collect send. If you leave collect → ctl-cash, 02’s send-as-consequential will also route wrong.

Grain owners you must encode:

| Stake | Verifier |
| --- | --- |
| Money out, pay-run, write-off | `ctl-pay` |
| Material apply, bank-rec sign-off | `ctl-cash` |
| Treatments, period lock | `ctl-books` |

### BOT.md outside Computer (T6)

Roster `instructions`: `Read office/bots/<slug>/BOT.md and obey office/constitution.md`.
Computer cwd: `office/computer`.
Resolved path: `office/computer/office/bots/...` — missing.
Actual file: `.cfo-v2/office/bots/<slug>/BOT.md`.

Pi file tools that stay inside the Computer never see identity. The Bot then runs on a two-sentence Roster line plus dumped skills.

You own the **layout** (symlink, copy, or Roster path that exists under `HARNESS_COMPUTER`). Pipe agents own the **wording** of their slugs’ BOT.md.

### `ask_user` still on the protocol surface (T6, T9)

Client blocks it if the Client extension loaded. Harness still registers it. Protocol skill text still teaches `blocked` means Operator unless rewritten. `approvalLevel: "never"` is Roster text. It does not strip Pi tools by itself.

`ask_user` cannot complete pay-run, lock, or write-off. You may rewrite Harness protocol skill text **generically** (blocked waits on a named approver kind `operator|bot`). You may not hard-code `ctl-pay` in Harness `src/`.

### Routines present, auto off

Five Routines. `client.json` `autoRoutines: false`. Cadence `weekly` / `monthly` now parse. Nothing proves they have been fired to completion with Kernel work.

You may turn autoRoutines on **only if** live Pi + Client `-e` + sidecar are the documented boot and a Routine firing into `--fake` cannot be the story. If turning them on is unsafe until pipes exist, leave them false and say so in NOTES. 05 must not assume month-end auto-fires if you left it false.

### Protocol log vs Handle complete (T8)

`protocol.jsonl` on this Computer is dominated by `send.accepted` for MSG-S12. Completion lives on Handle JSON. A demo that tails protocol.jsonl will not see done. You do not have to make protocol.jsonl pretty. You do have to make Handle complete the object Verifier unlock reads.

### Rooms empty of Host logs

Roster has Rooms 3–4 members (legal range). Membership is JSON. It is not a conversation. You do not have to fill Host logs for every Room. You do have to not invent a Host that is a sixteenth Bot.

### Skill dump vs allowlist

Harness can add whole `<computer>/skills` unless Client skills env is set. Live Computer sets `HARNESS_CLIENT_SKILLS` via extensions. Documented fake serve does not spawn Pi, so the fight is latent. Live boot must keep the allowlist.

### `cfo-floor` tests vs office Roster (T1)

Harness tests still prove a six-slug fixture. They do not prove `.cfo-v2/office/computer/harness/roster.json`. Sharing names `ap`, `cash`, `close`, `audit` is a trap. Do not “fix” tests by replacing the fixture with this office inside Harness `src`. Do not “fix” this office by copying `cfo-floor`.

### OpenMausBot-shaped `ui/`

Out of the critical path per deploy plan. Do not add a sixteenth Bot from a Settings panel. Do not restyle Harness UI as this ticket.

---

## Files you may create

- Symlinks or copies under `office/computer/` so BOT.md and constitution resolve. Prefer a layout a later agent can grep.
- A live boot section in RUN.md (you edit RUN.md; creating a second runbook is worse).
- Harness tests for generic primitives you add: extra `-e` persistence, approver kind `operator|bot`, Handle complete → unlock if that lives in generic code.
- `docs/Agentic-update/evidence/NOTES-floor.md` if you leave autoRoutines off or a Handle-store hole.

## Files you may edit

- `.cfo-v2/office/RUN.md`
- `.cfo-v2/office/computer/harness/client.json`
- `.cfo-v2/office/computer/harness/extensions.json`
- `.cfo-v2/office/computer/harness/intercept.json` (default + collect write-off owner; do not invent AR send edges — 02 owns those)
- `.cfo-v2/office/computer/cfo/extensions/intercept.ts`
- `.cfo-v2/office/computer/cfo/extensions/verifier.ts`
- `.cfo-v2/office/computer/harness/roster.json` **instructions paths only** and any bind-required Computer layout. Do not add `world`. Do not change collect connectors (02). Do not fill Stripe Display name (04).
- `.harness/Harness-v2/src/**` generic bus only: extra `-e` on serve/supervisor, skill path filter, approver kind, Handle complete as unlock source if that is generic.
- `.harness/Harness-v2/skills/harness/SKILL.md` if it still teaches blocked = Operator as law.
- `.harness/Harness-v2/tests/**` for those generic changes (`office-instances.test.ts`, `session-desk.test.ts` if that is where attach lives — grep, do not shotgun).
- Computer-side copies/symlinks of `office/bots/*/BOT.md` and `office/constitution.md` **without rewriting their specialist prose**.

## Files you must not edit

- `.cfo/inbox/`, `.cfo/ar/`, `.cfo/workflow.py`, `.cfo/agent.py`, `.cfo/cash_recon/`, `.cfo/close/`, `.cfo/reporting/`, `.cfo/audit/`
- Pipe BOT.md **wording** (object, must-not, done-when). You may make the file reachable.
- `grants.json` ops lists. You do not recompile finance Catalog.
- `.cfo-v2/office/instances/**` (read-only evidence)
- `examples/cfo-floor`
- `web/`
- Skills `ar-collections-policy`, `three-way-match-analysis`, close skills
- Prompt files 02–05

---

## Outcomes (not a design)

1. **Documented boot** for this office is live Pi workers with Harness `-e` and Client `-e`, `HARNESS_CLIENT_SKILLS=1`, `HARNESS_V2_ROOT` set, sidecar up. RUN.md must not teach `--fake` as the happy path. `--fake` may remain a labeled protocol demo in a clearly marked subsection.
2. **Identity files** BOT.md and constitution are readable from Computer cwd, or Roster instructions name a path that exists under `HARNESS_COMPUTER`.
3. **Verifier unlock** reads the same Handle store Harness `completeTurn` writes. A completed Harness Handle can unlock a consequential Kernel op when the Verifier concured. A second Client-only CONCUR file is not the source of truth.
4. **Intercept default** is not the human Operator for this Client. Collect write-off → `ctl-pay`, not `ctl-cash`. Align `intercept.json` with `handle-map.json` and grain.
5. **`ask_user` cannot complete** pay-run, lock, or write-off. Client still blocks it. Harness protocol text must not teach blocked = Operator as the office law.
6. **Extra Client extension** is persisted on serve/supervisor, not only `pi-bot.sh`. Prove argv or config on disk.
7. **Do not put invoice types**, `ctl-*` constants as finance enums, or close DAGs in Harness `src`. Generic primitives only (extra `-e`, skill path filter, approver kind `operator|bot`).
8. **Do not restore `Runner`** as the Bot bus. Do not register Roster slugs as children. Do not invent a sixteenth Bot. World bind is prompt 02.

---

## Novelty fence (Floor)

You may choose Computer layout (symlink, copy, intercept file shape) as long as the outcomes hold. You may choose whether autoRoutines start true, if you can defend it without `--fake` firing finance work into echo workers.

You must not freeze a numbered “how Pi thinks about invoices” procedure into Harness protocol skill. Harness does not know invoices.

You must not design Memory schema for apply or collect.

---

## Implementation notes that are still not a design

### Handle store

The corpus does not specify the intercept JSON schema. It requires one store as truth. Prefer: Verifier complete of the Harness Handle is what `completedHandleAllowsOp` (or successor) reads. If you keep a Client-side file, it must be a projection of that Handle, not a parallel decision.

### Operator remains emergency stop

Operator can stop a Bot. Operator cannot complete pay-run or lock by clicking approve. If intercept default cannot be “none,” default may be a Verifier only where grain already named one. Unnamed consequential ops must not silently become a human queue.

### Fake workers

Keep the code path. Relabel the docs. A judge who follows RUN.md must get Pi, not echo.

### Do not “fix” INV-S12

Six completed Handles on 2026-09-20 are protocol proof that refuse-on-empty-evidence works. Leave that history. Do not turn MSG-S12 into the judged AP story. That is 03.

---

## Proof / acceptance

1. Write the exact command that starts this office **without** `--fake`. Put it in RUN.md as the happy path.
2. From Computer cwd, a file tool can Read the Bot identity file Roster names. Show the resolved path.
3. Show Handle complete path equals Verifier unlock path in code (one function, or one directory, not two disagreeing stores).
4. Show `intercept.json` collect → `ctl-pay` for write-off, and default is not `{ "kind": "operator" }` as the office law.
5. Show serve/supervisor config or argv still has Client `-e` after a restart path you document.
6. If you touched `.harness/Harness-v2/src`, existing tests you affected pass. Add a test for the generic primitive.
7. `ask_user` cannot be the completion tool for a consequential op when Client is loaded. Show the block.
8. Do **not** claim office-live for AP, AR, cash, or close.

When you finish, list the files you changed and the live boot command as it appears in RUN.md.

---

## Stop conditions

- If you cannot unify Handle stores without putting invoice types in Harness `src`, stop and write NOTES. Do not smuggle `INV-` into the bus.
- If BOT.md cannot live on Computer without copying 15 files, a symlink from `computer/office/bots` → `../bots` (or equivalent) is enough. Do not rewrite 15 identities.
- If live Pi cannot boot in this environment (no model key, sidecar down), document the command anyway, prove attach with tests, and say the live spawn was not executed. Do not silently fall back to `--fake` as success.
- If World looks easy to add to the Roster, **do not**. That is 02.

## Out of scope

Finance send. Real vendor bills. Stripe Grants. Close `runs` path. Skill rewrites. Website. Commits unless the operator asks.
