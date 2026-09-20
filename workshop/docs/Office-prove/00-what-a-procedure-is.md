# What a procedure is

A procedure in this directory is a restartable test of the live office. It is not a prompt for a specialist Bot. It is not a Skill. It is not a demo walkthrough. It is not a Kernel unit test.

The operator (a Cursor agent, or Billy driving that agent) executes the procedure against a Harness **office instance**. The instance is a Computer. The Bots on that Computer do the finance work. The procedure watches them.

---

## Why procedures exist

Repair agents in `docs/Agentic-update/prompts/` change Floor, Grants, send, BOT.md, Handle store, and pipe wiring. Those chats can be green in the repair agent’s notes and still leave a Bot that throws, a Skill that steers the wrong way, or a Catalog op that never ran.

This operation is the first time standing Bots are tasked, on purpose, to move open items on a prove instance.

You cannot scope a demo until you know:

- which tools throw
- which tools return and the specialist still does the wrong job
- which skills never load
- which pipes never produce a Handle
- which fail-closed paths are the product (HOLD, BLOCKED, unexplained `$12.40`) and which are accidental breakage

A procedure is how you learn those facts in a way you can restart.

---

## The unit is an instance, not a chat

Harness clones a Computer into `.cfo-v2/office/instances/<id>/`. `office.json` records the desk. `POST /api/office-instances` creates. `POST /api/office-instances/<id>/select` selects. Serve then binds that Computer.

Runtime on that Computer is inboxes, Handles, transcripts, Pi sessions, protocol log, Kernel log, optional `runs/`. Wipe clears runtime. Roster, skills, Catalog, Grants, intercept, and workspace files stay.

That is why a procedure looks like a loop:

1. Create or select an instance.
2. Confirm gates and P0 still hold on that Computer.
3. Apply one stimulus (a Wake, a Routine, an injected message, a Handle from a peer).
4. Wait for the Bot turn to end.
5. Observe traces.
6. Classify the step: HARD, SOFT, RUNS, INTENDED, SKIP, HONEST-EMPTY, BLOCKED-CORRECT.
7. If HARD: stop this instance. Patch code, Grants, compiler, or Harness. Create a new instance or wipe this one. Resume at the last clean checkpoint, usually the start of the procedure, not the middle of a dirty Handle graph.
8. If SOFT: write a log row. Continue the procedure to the end. Do not edit `SKILL.md` in the middle of the instance. After the procedure, edit skills and BOT.md, then re-run that procedure on a new instance.
9. If RUNS or INTENDED: tick coverage. Next step.
10. When the procedure’s done-when is met, write the run log. Do not leave the verdict only in chat.

The loop is the procedure. The Markdown file is the script of that loop.

---

## What a procedure must consist of

Every procedure file in `procedures/` has the same parts, in this order. If a part is missing, the file is not developed enough to run.

### 1. Identity

- Procedure id (`P0` … `P9`)
- One sentence job
- Pipe or surface it owns
- Bots it may Wake
- Bots it must not Wake (SoD)
- Coverage it claims (skills, Catalog ops, Handle edges, Routines)

### 2. Preconditions

What must already be true. P1–P8 require P0 INTENDED, or they HARD at the first bind. Cash requires identifiers or it HARD as blocked-on-upstream. Close requires the other three to have run, or it may only prove BLOCKED on missing work plus `$12.40`.

Preconditions are checks, not hopes. Each one names a file, an HTTP GET, or a command.

### 3. Instance recipe

- Suggested instance name pattern
- Whether this procedure may share a month instance
- Whether parallel is allowed
- What wipe does to this procedure’s checkpoints
- What the live template must contain (skills, roster, Grants) because clone copies those and not Kernel source

### 4. Stimulus catalog

The exact ways work starts in this procedure. Allowed stimuli:

| Stimulus | How | Use |
| --- | --- | --- |
| Routine fire | `POST /api/routines/<name>/run` or `npx harness routine <name> --computer <instance>` | Cadence work: pay-run, aging, month-end, story, audit |
| Prove Wake | `POST /api/bots/<id>/messages` with a prompt that names `profile: <profile>` | Force a Profile. This is a test Wake. It is not Harness Operator concurrence |
| Peer Handle | A Bot already in motion sends `bot_send_prompt` | The real office path. Prefer this once a pipe is moving |
| Source inject | Kernel inbox/demo inject, World pack already on `data/` | Land an object Email/Bank/Books/Stripe can see |
| Spawn | `POST /api/bots/<id>/spawn` | Bind a lazy worker before the first Handle |

Forbidden stimuli:

- Completing a Verifier Handle as the Harness Operator
- `ask_user` as the completion path
- `--fake` workers
- Editing Kernel holdout into operational data to make close look CLOSED
- Calling `get_audit_ground_truth` on an operational Bot

### 5. Steps

A step is the smallest unit you classify. A step has:

- **Name** and number
- **Stimulus** (one of the allowed kinds)
- **Actor** — Bot slug and Profile (Display name)
- **Must call** — Catalog op ids that must appear in `pi-rpc.jsonl` or Kernel log without throw
- **May call** — ops that are allowed
- **Must not** — ops, Handles, or human paths that fail the step even if nothing threw
- **Observe** — exact paths and HTTP
- **RUNS when** — no throw, typed return, Handle reached a terminal status
- **INTENDED when** — the open item’s next state matches the corpus
- **HARD if** — stop, patch, new instance
- **SOFT if** — log, continue
- **Coverage ticks** — rows in `04-coverage.md`

A procedure that says “exercise AP” with no steps is not developed. A procedure that freezes the specialist’s reasoning as a numbered Kernel replay is a Skill crime (T7). The procedure names outcomes and tools. It does not tell `ap` how to feel about a price variance.

### 6. Observation pack

Every step that claims office-live must read, at least:

```
$COMPUTER/harness/protocol.jsonl
$COMPUTER/harness/bots/<bot_id>/transcript.jsonl
$COMPUTER/harness/bots/<bot_id>/pi-rpc.jsonl
$COMPUTER/harness/bots/<bot_id>/pi-runtime.jsonl
$COMPUTER/harness/bots/<bot_id>/handles/
$COMPUTER/cfo/kernel.log.jsonl
GET {serve}/api/bots/<id>
GET {serve}/api/handles
```

If the Client Grant door ran, Kernel log has the op. If only Pi text claims a send, that is not a tick.

### 7. Classification and restart

The step must point at `02-classification.md`. It must not invent a fourth failure kind. HARD vs SOFT is the whole split the operator asked for:

- Tool, code, Grant, bind, crash → HARD → instance dies
- Skill or judgment miss, tools returned → SOFT → instance lives, log lives, skill edit after the procedure

### 8. Coverage close-out

A table: claimed ticks vs observed ticks vs holes. Holes become either a later procedure (P6, P7) or a named SKIP with a reason.

### 9. Done-when

Two lines:

- Bare minimum (RUNS)
- Demo-ready (INTENDED)

The procedure is not done because the chat got long. It is done when those lines are true or a hole is named in `logs/runs/<instance>/VERDICT.md`.

### 10. Forbidden

A short list. Always includes: no `--fake` proof, no Operator concurrence, no clearing `$12.40`, no Bot `ar`, no holdout.

---

## How developed is developed enough

A procedure is developed enough to run when a second person (or a second Cursor agent) can execute it without asking the author what “check AP” meant.

That requires:

- Named Bot and Profile
- Named stimulus, including the HTTP path or CLI
- Named Catalog ops
- Named observe files
- Named Maximor objects where the World pack already has them (`INV-001` class match, `TXN-2026-09-015` for `$12.40`). If the id is missing on disk, the step says “a Kernel id that `tools.get_invoice` finds” and the run log records the id used
- HARD/SOFT/RUNS/INTENDED for every step
- A restart rule that says whether you resume the step, the procedure, or the month instance

A procedure is too developed (wrong kind of long) when it:

- Pastes Kernel `must_hold` into the specialist’s mouth
- Adds Bots
- Specifies Memory schema
- Decides World’s grain status (P1 records the live Roster fact; it does not decree a sixteenth Bot)
- Turns fail-closed HOLD into a fail of the office

Write outcomes. Leave remainder to the Bot.

---

## Two verdicts per step, on purpose

The operator asked for a bare minimum: everything that exists either works as intended or does not throw.

That is two axes.

| | Tools threw or never attached | Tools returned |
| --- | --- | --- |
| Next state matches corpus | should not happen; treat as HARD investigation | **INTENDED** |
| Next state does not match corpus | **HARD** | **SOFT** if the miss is skill/judgment; **HARD** if the miss is a missing Grant, missing send, or identity break the specialist could not have repaired |

Fail-closed that the corpus wants (HOLD on missing GR, BLOCKED on `$12.40`, collect refuses while deposits remain) is INTENDED, not SOFT.

Costume (Bot exists, `ops: []`, model writes English) is not RUNS for that Profile’s Catalog claim. It may be HONEST-EMPTY if the Grant is empty on purpose (Close Manager coordinate). P5 and P7 name which empty Grants are honest.

---

## One prove agent, many Bots

The specialist Bots are `email`, `ap`, `collect`, and the rest. They do not read these procedure files.

The **prove agent** is a Cursor agent with this directory attached. It:

- Creates and selects instances
- Fires stimuli
- Reads traces
- Classifies
- Writes logs
- Patches HARD defects in Kernel, Client, compiler, Harness generic bus, Grants (by fixing constructors and recompiling, not by hand-editing Grant ops)
- After a procedure, edits SKILL.md / BOT.md for SOFT defects
- Re-runs

It may run procedures sequentially in one chat. It may open a second chat for a second instance (P2 ∥ P3). It must not paste P0–P9 into a specialist Bot.

Billy may execute the same files by hand. The files do not require a model to classify a Python traceback.

---

## Sequential vs parallel

| Mode | Rule |
| --- | --- |
| Sequential | One instance. P0 → P1 → P2 → P3 → P4 → P5 → P8 on a month instance. P6 and P7 fill holes after. This is the default. |
| Parallel | Two instances. Typical: `prove-ap` runs P1-subset + P2. `prove-ar` runs P1-subset + P3. P0 must already be INTENDED on the live template, because clone copies the template. |
| Forbidden parallel | Two chats, one instance. Two wipes. Two Handle graphs. |

Kernel source `.cfo/` is shared. A HARD patch to Kernel is seen by every instance after sidecar restart. Skills are copied at instance create. A skill edit on live Computer is seen by the next clone, not by an instance that already exists, unless you also edit that instance’s `skills/` or you create `r<n+1>`.

---

## Relation to other documents

| Document | Job | This directory’s relation |
| --- | --- | --- |
| `workshop/docs/Agentic-update/` | What is broken, what is good, novelty fence | Source of INTENDED |
| `docs/Agentic-update/prompts/` | Repair Floor and pipes | Do that first if P0 or a pipe HARD on a missing tool |
| `.cfo-v2/office/RUN.md` | How to boot | P0 executes it |
| `.cfo-v2/office/DEMO-DESIGN.md` | Future show world | Not the prove stimulus. World pack on disk is. |
| Kernel `evaluate-cfo` | Python score | P9. Caption only. |
| Skills | Specialist remainder | P6 validates load and steer. SOFT edits them. |
| Catalog / Grants | Doors | P7. Skills never grant tools. |

If a procedure HARD on `send_office_outbound` ImportError, that is not a skill edit. That is a 05 AR / Floor repair, then a new prove instance.

---

## What this file refuses to specify

- How a Bot stores vendor habit
- Whether World is a sixteenth Bot (P1 records Roster reality)
- Demo minute-by-minute script
- Website UX
- New Catalog ops

Those wait until this operation has a verdict.
