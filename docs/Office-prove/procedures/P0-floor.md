# P0 — Floor (bus and bind)

**Job.** Prove the office can bind live Pi workers, attach the Client Grant door, talk to the Kernel sidecar, and complete a Handle whose unlock the Verifier path can see. No finance pipe is claimed here except that a Bot can call one granted read op without throw.

**Owns.** Bus, bind, cwd, intercept, extra `-e`, sidecar, Handle store.

**May Wake.** Any one Roster Bot that has a non-empty Grant. Prefer `ap` / Profile `prepare` with `tools.get_company_policies` or `tools.get_invoice` as a smoke read.

**Must not Wake.** Do not run weekly-pay-run as the P0 proof. Do not lock. Do not send mail.

**Coverage claimed.** All 15 (or 16) Bots bind. Client skills intersect on. `--fake` off. Intercept default not Operator.

**Preconditions.** `../05-gates.md` G1–G9 recorded. Live template is the clone source.

**Instance.** `prove-<date>-floor-rN`. Do not use `live`. Do not use `protocol-proof`.

---

## S01 — Create and select

- Stimulus: `POST {URL}/api/office-instances` with name `prove-<date>-floor-r1`. Then `POST .../<id>/select`.
- Actor: none (Harness)
- Must call: none
- Must not: select `protocol-proof`; prove on `live`
- Observe: `GET {URL}/api/office-instances`; `office.json`; snapshot Computer path
- RUNS when: instance exists; `currentId` is the new id; Computer path is `instances/<id>`
- INTENDED when: clone has `harness/roster.json`, `skills/`, `cfo/catalog.json`, `data` symlink, empty inboxes
- HARD if: create 500; select leaves serve on the old Computer; clone missing Catalog
- SOFT if: never (this is plumbing)
- Ticks: instance loop works

---

## S02 — Sidecar on this Computer

- Stimulus: serve already running; after select, wait for `{COMPUTER}/cfo/kernel.port`
- Actor: Kernel sidecar (not a Bot)
- Must call: none yet
- Must not: point sidecar at `.cfo/runs` as the Computer
- Observe: `kernel.port`; first lines of `kernel.log.jsonl`; process list if needed
- RUNS when: port file is fresh after select; log accepts connections
- INTENDED when: `HARNESS_COMPUTER` for that sidecar is this instance
- HARD if: stale port from previous desk; sidecar crash; log ImportError at import
- SOFT if: never
- Ticks: G7 on instance

If port does not appear, spawn any Bot (S04) and recheck. Still missing → HARD.

---

## S03 — Live Pi argv, not fake

- Stimulus: none. Read serve command line and `{COMPUTER}/harness/extensions.json` plus `client.json`
- Actor: supervisor
- Must call: none
- Must not: `--fake` in argv
- Observe: `extensions.json` extraExtensions includes Client `cfo/extensions/index.ts`; `clientSkills` true
- RUNS when: Client `-e` persisted on this Computer
- INTENDED when: `HARNESS_CLIENT_SKILLS=1` will be on worker env (see a spawned worker or supervisor notes)
- HARD if: fake workers; missing Client extension; skills dump whole tree because clientSkills false
- SOFT if: never
- Ticks: T5/T12 fake not used

---

## S04 — Bind one Bot

- Stimulus: `POST {URL}/api/bots/ap/spawn` (or `email` if ap Grant empty — it is not)
- Actor: Bot `ap`
- Must call: none yet (bind only)
- Must not: unbound Pi with no `HARNESS_BOT`
- Observe: `GET {URL}/api/bots/ap`; `harness/bots/bot_ap/lane.json`; `pi-runtime.jsonl`
- RUNS when: worker alive; slug `ap`; Client loaded
- INTENDED when: instructions can resolve `office/bots/ap/BOT.md` from Computer cwd (read the worker cwd or try listing that path on `{COMPUTER}`)
- HARD if: bind refuse; missing Display name; BOT.md path missing (T6 cwd); worker exit
- SOFT if: BOT.md exists but is stale vs constructor — log, continue P0, Floor/05 later if P2 SOFT
- Ticks: Bot ap bind

Repeat spawn for every Roster slug (S04b). You do not need a finance prompt for each. Bind without crash is RUNS for P0 Bot rows. Lazy spawn may wait until first Handle. Then S05 is the Handle.

World: if not on Roster, SKIP with T1. Do not add it in P0.

Stripe: if Display name `""`, bind may HARD. Then HONEST “stripe not office-live” for P1/P4, or 05 Cash repair. Do not skip silently.

---

## S05 — Smoke Grant read on ap

- Stimulus: prove Wake

```text
profile: prepare
Call tools.get_company_policies or tools.get_invoice for a Kernel id that exists in the World pack.
Do not approve. Do not Handle ctl-pay. Stop after the tool returns.
```

- Actor: `ap` / `prepare` (AP Preparer)
- Must call: at least one of `tools.get_company_policies`, `tools.get_invoice`
- Must not: `ask_user`; invent an amount; Profile union
- Observe: `pi-rpc.jsonl`; `kernel.log.jsonl`; Handle complete; protocol `turn.end`
- RUNS when: op returns JSON; no traceback; Handle terminal
- INTENDED when: Client Grant door enforced (an unganted op would be rejected — optional negative check in S07)
- HARD if: throw; tool unknown; Handle never completes; Operator asked to finish
- SOFT if: model rambling but the op returned — RUNS the op, SOFT the prompt if it then tried to match. For P0, prefer RUNS
- Ticks: tools.get_company_policies or tools.get_invoice; Bot ap Handle

Pick a real id. If you pass `INV-S12` and get not found, that is BLOCKED-CORRECT for get_invoice, still RUNS for the door. Do not use it as a later AP judged bill.

---

## S06 — BOT.md reachable

- Stimulus: none. From `{COMPUTER}` as cwd, `test -f office/bots/ap/BOT.md` and `test -f office/constitution.md`
- Actor: none
- RUNS/INTENDED when: both exist
- HARD if: missing (T6). Floor repair: copy or symlink repo `office/bots` and constitution into Computer. New instance after template fix (clone copies Computer files; a repo-only file is not cloned unless it sits under the Computer)
- Ticks: identity cwd

---

## S07 — Grant door negative (one unganted op)

- Stimulus: prove Wake on `collect` asking it to call `accrual.tools.create_accrual`
- Actor: `collect` / `chase`
- Must call: none. Client should refuse the op
- Must not: the accrual write succeeding
- Observe: pi-rpc error or Client reject; Kernel must not create an accrual
- RUNS when: reject, no throw crash of the worker
- INTENDED when: SoD door holds
- HARD if: collect creates an accrual (Grant union or missing denylist)
- SOFT if: model never attempts the op — RUNS not proved for the door. Retry with a more forceful Wake once. If still no attempt, SKIP door-negative and rely on unit tests; note in VERDICT
- Ticks: SoD

---

## S08 — Intercept default

- Stimulus: read `{COMPUTER}/harness/intercept.json`
- Actor: none
- INTENDED when: `default.kind` is `bot`, not `operator`. collect write-off owner `ctl-pay`
- HARD if: default operator (T9)
- Ticks: T9

---

## S09 — One Handle store

- Stimulus: complete S05. Then see whether Kernel consequential unlock (if any) and Harness `handles/` agree
- Actor: Floor/Client
- INTENDED when: the completed Harness Handle is the object Verifier unlock would read. No required second `workspace/verifier/handles/` CONCUR file
- HARD if: you must write a Client-only CONCUR JSON to unlock, while Harness already completed (T2, T9)
- If S05 was a read-only smoke, this step may only document the paths. Then P2 S-ctl-pay is the real proof. Note “P0 partial; P2 owns unlock”
- Ticks: T9 Handle store

---

## S10 — Remaining Bots bind

- Stimulus: spawn each remaining slug, or land a one-line Wake `profile: <default>\nPing. Do not call tools.` only if spawn is not enough to prove Pi starts
- Actor: each Roster Bot
- RUNS when: each worker starts without bind refuse
- HARD if: any slug missing Display name (stripe) unless you already classified HONEST not office-live
- Ticks: Bot table bind column

A ping Wake that calls no tools is not a P7 tick.

---

## S11 — ask_user cannot complete

- Stimulus: read Client intercept / Harness protocol text the worker sees if easy; otherwise wait for P2. Optional: Wake `ap` to `ask_user` for approval
- Must not: ask_user completing
- HARD if: ask_user runs and is treated as concurrence
- INTENDED: Client blocks it
- Ticks: T6 ask_user

---

## Done-when

- Bare min: S01–S05 RUNS; no fake; sidecar up; ap Handle terminal without throw
- INTENDED (required before other procedures claim office-live): S03, S06, S08, bind of all finance slugs, Client skills on

## Forbidden

`--fake` as proof. Operator concurrence. Adding Bot world here. Finance types in Harness src.

## Restart

HARD in S01–S03: fix serve/clone, new floor instance. HARD in S05: Kernel or Client patch, wipe or new instance, replay S04–S05. Do not continue into P1 on a Computer that cannot complete a read op.
