# Instance loop

Every prove run happens on a Harness office instance. The live Computer is the template. A prove instance is a clone of template files plus empty runtime.

Code: `.harness/Harness-v2/src/server/office-instances.ts`. Wipe: `.harness/Harness-v2/src/wipe.ts`. Registry: `.cfo-v2/office/office.json`.

---

## Live vs instance

| Id | Computer | Prove use |
| --- | --- | --- |
| `live` | `.cfo-v2/office/computer` | Template. Compile here. Edit skills here after a procedure. Do not wipe `live` as a prove cleanup. |
| `protocol-proof`, `fresh-protocol` | `.cfo-v2/office/instances/<id>` | Historical desks. Dirty. Do not select them as prove instances. |
| `prove-…` | `.cfo-v2/office/instances/<id>` | The only desks these procedures run on. |

`office.json` `currentId` is whichever desk serve last selected. On 2026-09-20 it was `protocol-proof`. That does not make `protocol-proof` the prove instance. Create a new one.

Serve honors `currentId`. If you `npm run serve -- --computer .cfo-v2/office/computer` and `currentId` is another instance, you are not on the live tree. P0 checks `GET /api/office-instances` (or `/api/office`) and confirms the Computer path.

---

## What create copies

`createOfficeInstance` clones from live:

- `harness/roster.json`
- `harness/client.json`
- `harness/intercept.json`
- `harness/extensions.json`
- `skills/` (entire tree)
- `cfo/` Catalog, Grants, Client extension (not Kernel `.cfo/` source; skips `kernel.port`, `kernel.log.jsonl`, pyc)
- `workspace/`
- `data` as a symlink to the same World pack the live Computer used

Then `initComputer` and `wipeRuntime`.

It does **not** copy:

- Pi sessions
- protocol log
- inboxes, transcripts, Handles, lanes
- threads, receipts, approvals
- Kernel sidecar port

Kernel Python is always `.cfo/` via sidecar `PYTHONPATH`. A Kernel patch is global. A skill patch is live-template (and the next clone) unless you also edit the instance copy.

BOT.md standing identity files live under `.cfo-v2/office/bots/` in the repo. P0 requires they are readable from Computer cwd (`office/bots/<slug>/BOT.md` under `$HARNESS_COMPUTER`). If Floor repair added a symlink or copy into the Computer, clone must preserve it. If P0 finds BOT.md missing on a new instance, that is HARD: the clone filter dropped identity, or Floor never landed.

---

## Create, select, serve

From repo root. Replace names as you go. Serve URL is whatever `npm run serve` prints. RUN.md default is `http://127.0.0.1:8787/`.

Create:

```bash
# serve must already be up against the office parent, or use the UI Offices page.
curl -sS -X POST http://127.0.0.1:8787/api/office-instances \
  -H 'content-type: application/json' \
  -d '{"name":"prove-20260920-floor-r1"}'
```

Select:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/office-instances/prove-20260920-floor-r1/select
```

Selecting switches the running serve Computer. Confirm:

```bash
curl -sS http://127.0.0.1:8787/api/office-instances
curl -sS http://127.0.0.1:8787/api/snapshot
```

The snapshot Computer root must end with `instances/prove-20260920-floor-r1` (or the id returned). If it still points at `office/computer` or `protocol-proof`, stop. You are on the wrong desk.

Boot itself is P0. This file only says: the procedure does not start until the selected Computer is the prove instance.

---

## Naming

```
prove-<YYYYMMDD>-<proc>-r<n>
```

Examples:

- `prove-20260920-floor-r1`
- `prove-20260920-month-r1` — sequential P1–P5 + P8
- `prove-20260920-ap-r1` — parallel AP
- `prove-20260920-ar-r1` — parallel AR
- `prove-20260920-catalog-r1` — P7 remainder
- `prove-20260920-skills-r1` — P6 remainder

`<proc>` is `floor`, `month`, `ap`, `ar`, `cash`, `close`, `intake`, `catalog`, `skills`, `cross`. Do not name an instance after a Bot slug alone (`prove-ap` is the AP procedure, not Bot `ap`).

Increment `r<n>` on HARD restart. Keep `r1` logs. Do not delete the old instance folder until the verdict is written. You may leave old instances on disk. Do not select them by accident.

---

## Wipe vs new instance

| Action | Command / API | Clears | Keeps | Use when |
| --- | --- | --- | --- | --- |
| Wipe runtime | `POST /api/wipe` on the selected Computer | inboxes, Handles, transcripts, Pi sessions, protocol, Kernel log, optional `runs/` | Roster, skills, Grants, Catalog, intercept, workspace | HARD left dirty Handles, the patch is Kernel/Harness already loaded, and you want the same Computer ids |
| New instance | `POST /api/office-instances` | everything runtime (clone starts wiped) | nothing from the dirty run | Skill/Grant/roster/template changed, or you do not trust the dirty workspace |
| Kill Bot | `POST /api/bots/<id>/kill` | that worker process | disk | Worker wedged. Then wipe that Bot’s session dir if needed |
| Stop serve | process stop | nothing on disk | everything | Sidecar/port confusion. Restart serve after select |

Wipe default in code keeps `runs/` unless `wipeRuns: true`. Prove cash/close need Computer `runs/`. After a HARD in close, wipe with runs cleared if the pack is half-written. After a SOFT in AP, do not wipe until the procedure ends; you still want the Handle graph.

Do not pass `--fake` when you come back.

Keep memory (`keepMemory`) only when the procedure under test is T10 (next-period learning). Default prove wipes memory so a prior SOFT cannot leak into the next HARD retry.

---

## Checkpoints

A checkpoint is a procedure step number plus a short note of Kernel ids that exist (invoice id, payment id, bank txn id). Write it into `logs/runs/<instance>/CHECKPOINT.md` after every INTENDED or RUNS step that later steps depend on.

On HARD:

1. Write `logs/runs/<instance>/HARD.md` with the traceback, op id, Bot, step.
2. Patch. Recompile if constructors changed: `PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational` on the **live** tree, then new instance so Grants copy.
3. If the patch was Kernel-only and Grants did not change, you may wipe the same instance and resume at the last checkpoint **only if** no half-applied money or half-sent mail exists. If apply posted, or a dun sent, do not resume. New instance. Replay from P1.
4. Never resume in the middle of a Verifier turn.

On SOFT:

1. Write `logs/runs/<instance>/SOFT.md` (append a row).
2. Continue.
3. At procedure end, edit skills/BOT.md on live (and Kernel skill registry if that is the source).
4. New instance. Re-run that procedure. Prior SOFT should not recur. If it does, it is still SOFT unless you now see a throw (then HARD).

---

## Shared Kernel, copied skills

```
.patch Kernel .cfo/          → all instances, after sidecar restart
.patch Client extension      → live cfo/ then new instance (clone copies cfo/)
.patch compiler output       → recompile on live, new instance
.patch SKILL.md              → live computer/skills and .cfo/skills; new instance
.patch BOT.md                → office/bots (repo). Instance sees it only if Computer cwd has that tree
.patch roster.json           → live harness/roster.json; new instance
.patch Harness src           → restart serve; instances stay
```

Hand-editing `grants.json` ops is forbidden. Constructors are the Grant source. SUPERSEDES and compiler comments say this. A prove HARD that “fixes” Grants by typing an op into JSON will fail the next compile.

---

## Month instance vs coverage instances

**Month instance** (`prove-…-month-rN`): P1 through P5 and P8. This is the only instance that can prove identifier handoff (T11). Prefer this when you want demo-ready.

**Coverage instances**: P6 remainder skills (EDI, vendor portal, employee, physical mail) and P7 remainder Catalog ops. These may be parallel after P0. They prove RUNS. They do not prove a closed month.

**Pipe-parallel instances**: `prove-…-ap-rN` and `prove-…-ar-rN` after P0 INTENDED on the template. Useful when AP HARD would otherwise block AR learning. Cash/close still need a month instance later.

---

## Serve, sidecar, workers

P0 states the boot. This file states instance consequences:

- Lazy spawn (`client.json` `spawnPolicy: lazy`) starts a Pi worker when a Handle lands. Prove may `POST /api/bots/<id>/spawn` first so bind errors show before the finance prompt.
- Sidecar is per Computer (`cfo/kernel.port` on that instance). Select switches Computer. Sidecar must come up on the new tree. If the port file is stale from a previous desk, wipeRuntime on create already dropped it. After a manual select, wait for a new `kernel.port` or HARD.
- Do not point `HARNESS_COMPUTER` at `.cfo/`. RUN.md: live Bots write `$HARNESS_COMPUTER/runs`.

---

## Operator DM vs peer Handle

`POST /api/bots/<id>/messages` sends `kind: user_dm` from `operator`. That is allowed as a **prove Wake**. It is a test harness for “this Bot, this Profile, this job.”

It is not allowed as:

- Verifier concurrence
- Payment release
- Period lock
- Write-off

Those complete when `ctl-*` Bots complete their Handles. Intercept must not default to the human Operator. P0 checks `intercept.json`. If default is `{ "kind": "operator" }`, P0 is HARD (T9). Live Computer on a later 2026-09-20 pass already points default at `ctl-pay`. Disk wins. Read the selected instance’s file.

---

## Log location

```
docs/Office-prove/logs/runs/<instance-id>/
  README.md          copied from templates, filled
  VERDICT.md
  CHECKPOINT.md
  HARD.md            only if a HARD happened
  SOFT.md            append-only
  coverage.md        ticks for this run
  notes.md           free text, including “blocked on 05 repair”
```

Do not write these under the instance Computer. The next wipe would delete them. The instance Computer holds traces. This directory holds judgments.

---

## Quick checklist before any step

1. `currentId` is the prove instance.
2. Serve URL responds.
3. `cfo/kernel.port` on **that** Computer exists and is fresh.
4. `--fake` is not in the serve argv.
5. Log directory for this instance exists.
6. You know whether this is a month instance or a coverage instance.
