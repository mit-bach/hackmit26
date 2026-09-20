# Office prove

This directory is the operation that tests the Office of the CFO on Harness v2.

It is not the repair pack. Repair lives in `docs/Agentic-update/prompts/`.
It is not a demo script. Demo scoping starts after this operation has a verdict.
It is not Kernel pytest. Kernel green is a gate. It is not office-live.

No standing Bot has been tasked, as of the start of this operation, to complete a pipe on a prove instance. These files are the procedures that do that.

Live template after the 2026-09-20 repair: **16 Roster Bots** (grain 15 plus Source Bot `world`), **101 operational Catalog ops**, World bound, `send_office_outbound` granted, Stripe Payout Agent granted, Month-End Close Reviewer granted lock reads, Close Manager and Audit Report Agent honestly empty. `autoRoutines` stays false; fire Routines over HTTP. Disk on the selected instance wins if a later compile moves a count.

---

## What this operation is for

By the end of every procedure in `procedures/`, one of two things is true for every surface that exists in CFO V2:

1. **INTENDED.** The pipe, skill, or Catalog op does the job the corpus named.
2. **RUNS.** The code does not throw. The tool returns. The Handle completes or the Kernel returns a typed object. The miss against intended function is written in a log, not guessed away.

RUNS without INTENDED is the bare minimum the operator asked for. INTENDED is what you need before you scope a judged demo.

A third honest state is allowed:

3. **HONEST-EMPTY / BLOCKED-CORRECT.** The Grant is empty on purpose, or the period is BLOCKED on the planted `$12.40`. That is a pass of law, not a fail of tools.

---

## Read order

1. This file.
2. `00-what-a-procedure-is.md` — what a procedure is, how developed it must be, what it is not.
3. `01-instance-loop.md` — create, select, wipe, restart. Instances are the unit of a run.
4. `02-classification.md` — HARD, SOFT, RUNS, INTENDED. When you stop. When you continue.
5. `03-operator-agent.md` and `prompts/00-OPERATOR.md` — paste the **entire** operator prompt into a new chat. Spawn from `prompts/README.md`.
6. `04-coverage.md` — skills, Catalog ops, Handle edges, Routines, Bots. Tick these. Do not invent a second inventory.
7. `05-gates.md` — compile, import, pytest, boot. Do this before you burn a Pi turn.
8. `procedures/` — P0 through P9, in the order that file names.
9. `logs/` — templates. Write run logs there. Do not write verdicts only in chat.

Corpus for intended function: `docs/Agentic-update/`. Grain: `design-workshop/dominik/cfo-bot-grain.md`. Process: `design-workshop/dominik/cfo-office-processes.md`. Boot: `.cfo-v2/office/RUN.md`.

---

## Order of work

```
Gates (05-gates)
    → P0 Floor          one instance, required
    → P1 Intake         can share an instance with a pipe
    → P2 AP ∥ P3 AR     two instances after P0, or one month instance
    → P4 Cash           after identifiers exist
    → P5 Close          last on that month instance
    → P6 Skill sweep    remaining skills the month did not load
    → P7 Catalog        remaining granted ops the month did not call
    → P8 Cross-pipe     same identity across pipes (needs the month instance, or a fresh month)
    → P9 Kernel eval    honesty caption; never a substitute for P0–P8
```

P2 and P3 may run in parallel on **different** instances. They must not share an instance. Cash and close must see identifiers from apply and pay, so they belong on a month instance that already ran AP and AR, or they HARD as blocked-on-upstream.

One Cursor agent may drive all of this sequentially. Parallel means two prove chats, two instances, two log directories. Never two procedures writing the same instance.

---

## Instance rule, one paragraph

Create a new office instance for a prove run. Select it. Serve that Computer. Do not prove on `live` if you will wipe. Do not reuse `protocol-proof` or `fresh-protocol` as a prove instance. Those are historical desks. Name prove instances `prove-<date>-<proc>-r<n>`. On HARD, patch code, then wipe or create `r<n+1>`. On SOFT, log, finish the procedure, then edit `SKILL.md` / `BOT.md` and re-run that procedure on a new instance.

---

## Done for this operation

The operation is done when:

1. P0 is INTENDED (live Pi, Client attached, sidecar up, BOT.md reachable, one Handle store). `--fake` is not the proof.
2. Every Computer `SKILL.md` (33) has a P6 tick: it loaded on a Bot that is assigned it, or it is logged HONEST-UNASSIGNED.
3. Every operational Catalog op that has a Grant wearer has a P7 tick: one call, no throw. `audit.tools.get_audit_ground_truth` is forbidden in operational phase.
4. Every standing Roster Bot has bound and completed at least one Handle without a tool exception.
5. Pipes AP, AR, cash, close each have a procedure verdict. Bare minimum: RUNS on the happy path and on the fail-closed path. Demo-ready: INTENDED outcomes from `docs/Agentic-update/01-intended-office.md`.
6. P8 has one vendor bill identity and one customer cash identity that survive across pipes, or a log that names the break as T11.
7. Soft-fail logs exist for every skill that RAN and was not INTENDED. Those files were edited. The procedure that owns them was re-run, or a hole is named.
8. The planted `$12.40` on `TXN-2026-09-015` is still unexplained. Close is still BLOCKED on it.

Then, and only then, run the show: `docs/Office-show/`. One golden instance. Not these prove desks. Not these Wakes.

---

## What you must not do in this operation

- Do not complete finance work as the Harness Operator. The prove agent may Wake a Bot. It may not concur for `ctl-*`.
- Do not use `serve --fake` as a prove verdict.
- Do not resolve the planted `$12.40`.
- Do not load holdout catalogs or `get_audit_ground_truth` on operational Grants.
- Do not treat Kernel `evaluate-cfo` 97% as office-live.
- Do not hunt Bot `ar`. Operators are `apply` and `collect`.
- Do not restore `Runner` as the Bot bus.
- Do not add a Bot unless grain Tests A–D fail.
- Do not paste a new numbered Kernel replay into a Skill to make P6 look green.
- Do not demo `INV-S12` / `MSG-S12` as a vendor bill.

---

## Index

| File | Job |
| --- | --- |
| `00-what-a-procedure-is.md` | Law of a procedure |
| `01-instance-loop.md` | Instance create / wipe / restart |
| `02-classification.md` | HARD vs SOFT vs RUNS vs INTENDED |
| `03-operator-agent.md` | Cursor agent that runs the pack |
| `04-coverage.md` | Tick lists |
| `05-gates.md` | Pre-Pi gates |
| `procedures/README.md` | Procedure order and shared step shape |
| `procedures/P0-floor.md` | Bus and bind |
| `procedures/P1-intake.md` | Email, books, bank, stripe, world |
| `procedures/P2-ap.md` | Open bills, match, pay-run |
| `procedures/P3-ar.md` | Apply, collect, send |
| `procedures/P4-cash.md` | Bank vs books, `$12.40` |
| `procedures/P5-close.md` | Period pass, story, audit |
| `procedures/P6-skill-sweep.md` | Every Skill.md |
| `procedures/P7-catalog.md` | Every granted Catalog op |
| `procedures/P8-cross-pipe.md` | One identity across pipes |
| `procedures/P9-kernel-eval-bridge.md` | Existing evals, what they are not |
| `logs/` | Templates and run logs |
