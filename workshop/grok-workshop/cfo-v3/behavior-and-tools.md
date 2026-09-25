# Layer 4 — Bot text

Depends on layer 2, because the files live only under `.cfo-v3/office/bots` and `.cfo-v3/skills`. This file replaces the earlier draft of the same name.

Authority: `DESIGN-REVIEW.md` sections 4 and 5, and `PROFILES-AND-PROPOSAL.md` as a defect list. Do not build the item ledger or `complete_step` in this layer. That redesign is a later layer, after the office runs.

## Job

Rewrite the pasted text so it matches the code.

- Delete the phrase `the finance record`. Say the action in ordinary words. Do not paste Catalog ids into text an operator would send as a wake.
- Delete `## Must not` lines that name an action the Bot has no tool for.
- Delete the sentence that stealth theft is not in the operational books. The rows are in the world pack. The answer key is not, and it must not be in `.cfo-v3`.
- Close and story packets go to `workspace/<slug>/packets/<id>.json`. Kernel traces go to `runs/`.
- `path-leases.json` lists all 16 slugs. A missing slug is deny, not allow.
- Paste skills from the Grant for the work in hand, or paste none and let one skill path exist. Do not paste by roster and also register the same body as a Pi skill.
- `profile:` is not parsed from the middle of a message. Until the profile mechanism is removed, a missing header means the Bot's default, every wake, including after restart. `active-profile.txt` and the Grant bind are the same value.

## Not this layer

Do not add a workflow engine. Do not delete Profiles yet. Do not spawn Pi to record a September tape.

## Done when

`rg -n 'the finance record' .cfo-v3` prints nothing.

`rg -n 'not in operational books' .cfo-v3` prints nothing.

The lease file has 16 slugs. A note under `## Proved` names the files changed.

## Landed

Files written under `.cfo-v3`:

- `office/system.md`
- `office/bots/<slug>/BOT.md` (16) and `office/bots/<slug>/profiles/*.md`
- `office/bots/close/HOST.md`, `office/bots/close/NOTES.md`, `office/bots/story/NOTES.md`, `office/bots/audit/NOTES.md`
- `office/bots/audit/routines/post-close-assurance.md`
- `skills/*/SKILL.md` (33), including `skills/audit-finding-writing/SKILL.md`
- `cfo/path-leases.json` (16 slugs; `emptyWritePrefixes` is `deny`; `audit` also has `runs/audit/`)

`the finance record` is gone from `.cfo-v3/office`. `review-assets.md` is the fixed-asset review, not a copy of `review-bs.md`. Close and story packets are `workspace/<slug>/packets/`. Kernel traces are `runs/`. The person-readable close pack is HTML at `workspace/close/packets/<period>.html` with the gate result, and September stays not CLOSED while `$12.40` is open. That HTML is kernel close-host code. This desk does not claim the file exists here.

Proves not run. No new instance. No tape. Golden was not touched.

1. World replies: not run. No Harness session on a new `.cfo-v3` instance.
2. Collect thread: not run. Same missing session.
3. `INV-001` pay draft: not run. Did not rerun `prove-20260920-fork-month-r3`.
4. Fee-net `TXN-2026-09-011` and leave `$12.40` open: not run. Same missing session.
5. Audit sample: not run. Same missing session.
6. Close treatments and Kernel gate reads: not run. Same missing session.
7. Blocked write outside `workspace/<slug>/`: not run. A Bot that never wrote does not prove the sandbox.
8. Injection mail: `.cfo-v3/kernel/inbox/classify.py` sets `REJECT_UNSAFE_REQUEST` and drops `VENDOR_INVOICE` on prompt injection. `inbox.classify` did not import (`No module named 'models'`). Live mail was not sent.
