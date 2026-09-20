# Floor bus — 2026-09-20

Floor agent notes. Categories closed here: **T5** (bus attach), **T6** (BOT.md cwd; ask_user as Operator), **T9** (two Handle stores; intercept default Operator), **T12** (`--fake` as the documented office). Disk wins over `live-computer-2026-09-20.md`.

This is the bus. It is not AP/AR/cash/close office-live. World bind is the AR agent’s grain Tests A–D problem. `autoRoutines` stays false; Close owns whether Routines fire.

No sixteenth Bot. Runner is not the Bot bus. Roster slugs are not children.

---

## 1. Documented boot without `--fake` (T5, T12)

Command (git repo root):

```bash
export HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer"
export HARNESS_V2_ROOT="$PWD/.harness/Harness-v2"
export HARNESS_CLIENT_SKILLS=1
cd .harness/Harness-v2
npm run serve -- --computer ../../.cfo-v2/office/computer --no-open
```

`harness/client.json` spawnPolicy is `lazy` (live Pi when a Handle lands). Pass `--eager` to bind every grain slug at boot. Sidecar is `./cfo/bin/sidecar.sh`. `--fake` remains in `RUN.md` as a labeled protocol demo only.

---

## 2. BOT.md reachable from Computer cwd (T6)

Roster instructions still name `office/bots/<slug>/BOT.md` and `office/constitution.md`. Those paths exist under `$HARNESS_COMPUTER`:

```text
.cfo-v2/office/computer/office/bots          → ../../bots
.cfo-v2/office/computer/office/constitution.md → ../../constitution.md
```

Proof:

```bash
cd .cfo-v2/office/computer
test -f office/bots/collect/BOT.md && test -f office/constitution.md && echo ok
```

---

## 3. Handle complete path equals Verifier unlock path (T9)

Harness `completeTurn` writes:

```text
$HARNESS_COMPUTER/harness/bots/<botId>/handles/<handleId>.json
```

Client `completedHandleAllowsOp` reads that same path (`harnessHandlePath` / `findHarnessHandlePath`). A completed Handle whose result first line is `CONCUR` unlocks the consequential Kernel op. `workspace/verifier/handles/` with `decision: CONCUR` does **not** unlock. `workspace/verifier/pending/` is an index only (`handleStore: "harness"`), not concurrence.

---

## 4. intercept collect → ctl-pay for write-off (T9)

Grain: ctl-pay owns money-out and write-off; ctl-cash owns apply and rec; ctl-books owns treatments and lock. Collect write-off is ctl-pay, not ctl-cash.

`harness/intercept.json` on this Computer:

- `default.kind` is `bot` (not Operator)
- `bots.collect.bot` is `ctl-pay`
- `bots.apply` / `bots.cash` → `ctl-cash`
- `bots.close` → `ctl-books`

`cfo/handle-map.json` collect write-off edge already named ctl-pay. Harness `src/` has no ctl-* finance enum; intercept kind is `operator|bot` only.

---

## 5. ask_user cannot complete pay-run / lock / write-off (T6)

Client `tool_call` still blocks `ask_user`. Harness protocol card and `skills/harness/SKILL.md` no longer teach `blocked` = Operator as office law. When intercept kind is `bot`, Harness `ask_user` returns `allowed: false` (`intercept_bot`).

---

## 6. Extra Client `-e` on serve/supervisor (T5)

On disk:

- `harness/client.json` → `extraExtensions: ["./cfo/extensions/index.ts"]`, `clientSkills: true`
- `harness/extensions.json` → absolute Client `cfo/extensions/index.ts`, `clientSkills: true`

Supervisor `envFor` runs `applyAttachEnv` then `extraExtensionArgs(env)`. Spawn argv is `-e <Harness extensions/index.ts> -e <Client cfo/extensions/index.ts>`. Env includes `HARNESS_CLIENT_SKILLS=1` and `HARNESS_V2_ROOT`. Not only `pi-bot.sh`.

---

## Holes left for other agents

| Hole | Owner | Category |
| --- | --- | --- |
| World not on live Roster | AR (Tests A–D) | T1 |
| Send / mailbox last mile | AR | T3, T4 |
| Live vendor bill in Kernel | AP | T11, T12 |
| Identifier handoff + Stripe Grants | Cash | T3, T11 |
| `autoRoutines: false`; close writes `.cfo/runs` | Close | T5 |
| Kernel `Runner` hosts | not Floor | T13 |
