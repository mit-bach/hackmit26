# Surface — Harness protocol

Runtime: `.harness/Harness-v2`.
Client extension: `.cfo-v2/office/computer/cfo/extensions/`.
Computer: `.cfo-v2/office/computer`.

Harness is the bus. It does not know invoices. Finance types stay out of `src/`.

---

## Intended function of this surface

One process per Bot. Disk inbox. Handle accept ≠ complete. Sender never marks complete. Rooms 2–6 with a Host that waits. Memory per BotId. Routines fire onto the owning Bot. Extra Client `-e` loads Grants and Kernel calls. Consequential work can wait on a Bot, not only the human Operator. `/v1` HTTP is control. The Operator overlay is optional.

A child is not a Bot. `examples/cfo-floor` is not this office.

---

## What is good (including what flipped after 2026-09-19)

- Handle protocol types are real. Fake workers and live Pi both can complete.
- Six Handles completed 2026-09-20 on email/ap/ctl-pay. Refuse-on-empty-evidence is good.
- `harness/extensions.json` extraExtensions points at the Client. `client.json` `clientSkills: true`. Attach is no longer only `pi-bot.sh`.
- `cadenceToMs` accepts `weekly` and `monthly`.
- Rooms on the Roster are 3–4 members. In range.
- `approvalLevel: "never"` on all listed Bots.
- `bot_world` directory exists on disk even though bind will not start it from the live Roster.

---

## What is broken

### Documented boot still `--fake` (T5, T12)

`RUN.md` step 3: `npm run serve -- --computer … --fake --no-open`.
Fake workers echo. No model. No Kernel. Not fifteen finance Bots.

`client.json` is a second boot: lazy spawn, sidecar command, grok-4.5. Two runbooks.

### Two Handle stores (T9)

Harness: `harness/bots/<botId>/handles/`.
Client intercept: `workspace/verifier/handles/` with `decision: CONCUR`.
`completedHandleAllowsOp` reads the Client file. A Verifier finishing a Harness Handle does not unlock the Kernel op.

Deploy plan Phase 3 named this. Live Computer still has both.

### Intercept default Operator (T9)

`intercept.json`: `"default": { "kind": "operator" }`. Per-Bot overrides exist for ap/pay/apply/collect/cash/close/books/story. Email, stripe, bank, audit, Verifiers themselves, and World (if bound) follow default. Collect override is `ctl-cash` (wrong for write-off; see `pipes/ar.md`).

### BOT.md outside Computer (T6)

See `surfaces/bot-md.md`.

### Protocol log vs Handle complete (T8)

`protocol.jsonl` on this Computer is dominated by `send.accepted` for MSG-S12. No `turn.end` lines found in a grep of that file. Completion lives on Handle JSON. A demo that tails protocol.jsonl will not see done.

### Rooms empty of Host logs

Roster has Rooms. `computer/harness/rooms/<id>/` had no live Host log in the 09-19 audit. Membership is JSON. It is not a conversation.

### Routines present, auto off

Five Routines. `autoRoutines: false`. Fire is manual. Cadence math no longer drops weekly/monthly. Nothing proves they have been fired to completion with Kernel work.

### Skill dump vs allowlist

Harness still can add whole `<computer>/skills` unless Client skills env is set. Live Computer sets it. Documented fake serve does not spawn Pi, so the fight is latent.

### `ask_user` still on the protocol surface

Client blocks it if the Client extension loaded. Harness still registers it. Models still get taught it in protocol skill text unless rewritten.

### Fake vs live spawnPolicy

Operator config can imply fake even without the flag. README demos still teach `--fake`.

### cfo-floor tests vs office Roster

Harness tests still prove a six-slug fixture. They do not prove `.cfo-v2/office/computer/harness/roster.json`. Sharing names `ap`, `cash`, `close`, `audit` is a trap (T1).

---

## Inadequacies of a working bus

A bus that can complete a stub Handle is necessary and not sufficient. The AP stub proved the protocol and also proved intake did not land a Kernel invoice. Do not treat Handle complete as pipe complete.

OpenMausBot-shaped `ui/` is out of the critical path per deploy plan. It can still distract operators into editing Roster in a Settings panel. Constitution: do not add a sixteenth Bot that way.

---

## Capability this surface must possess

When the bus is adequate for this office:

1. Live Pi workers bind from the office Roster, with Harness `-e` and Client `-e`.
2. Sidecar is up. `call_connected_tool` hits Kernel with Grant re-check.
3. Handle complete is the same object Verifier unlock reads.
4. `blocked` waits on a named Bot when the Client says so, not on the Operator, for pipe concurrence.
5. Identity files are readable from Computer cwd.
6. Fake workers are a demo switch, not the documented office boot.
7. Rooms and Routines can actually run, not only parse.

This file does not specify the intercept JSON schema to use. It requires one Handle store as truth, and Operator as emergency stop.
