# Adopt the context module across the office

Paste this into the debugging chat. Debugging is paused. Port 8801 is not sacred. Do not resume the P0–P9 checklist. Do not record a golden tape. Do not POST a prove Wake that names a Catalog op.

The harness change is already in the tree. Your job is the office text that the module now pastes into every Bot.

## What already landed

- `.harness/Harness-v2/src/context.ts` builds the system prompt.
- `before_agent_start` in `.harness/Harness-v2/extensions/index.ts` appends that text and nothing else. `MEMORY.md` and recent work are not in the prefix.
- If `office/system.md` is missing, the module falls back to the protocol card plus a memory section and a finance-tool section. It does not throw.
- If `BOT.md` is missing, it falls back to the roster `instructions` string.
- The active profile is `harness/bots/<id>/active-profile.txt`, written by the Client extension when a wake contains `profile:`.
- A hash manifest is written under `harness/bots/<id>/context/` when the text changes. It is not written into Pi’s session jsonl.
- Tests: `.harness/Harness-v2/tests/context.test.ts`. On the live Computer, AP’s suffix contains `BOT.md` and does not contain `Read office/bots/ap/BOT.md`.

Shared text for the live template is `.cfo-v2/office/computer/office/system.md`.

A Bot process that is already running still has the old prompt in memory. Restart serve after the office text is in place. Do not restart in the middle of an edit.

## What you change

The module inlines files. A sentence that says “read BOT.md” is now a bug, because the model never has to open the file, and the sentence is not even in the prompt when `BOT.md` exists.

Work on the live template (`.cfo-v2/office/computer` and the sources it is copied from: `.cfo-v2/office/bots`, `.cfo/skills`). Then copy forward. Do not edit only one prove instance and leave the template stale.

For every slug:

1. `office/bots/<slug>/BOT.md` is the bot layer. It must be the instructions, not a pointer to another file. Remove “read this”, “see constitution”, and “call tools.…”. State the object the Bot owns, who it talks to, and what it must not do.
2. Each `profiles/<name>.md` is pasted under “Active profile” when that profile is selected. Write the profile as the job for that wake. Do not name Catalog ids.
3. Each skill in the roster allowlist is pasted from `skills/<name>/SKILL.md` (Computer `skills/` or `cfo/skills/`). Write the skill as rules for the decision. Do not name Catalog ids. Do not say “read the skill.” A skill still does not grant tools.
4. Roster `instructions` in `harness/roster.json` still say “Read office/bots/…/BOT.md” on the live Computer. Those strings are the fallback when `BOT.md` is missing. Rewrite them so the fallback is a real standing order, not a path to open. Keep them short. The inlined `BOT.md` is what a normal wake sees.
5. Put `office/system.md` on every Computer the office serve can select: the live template, `prove-fork`, and any instance you will boot. Same bytes as the live file. Do not fork a second office policy per instance.

Do not add a memory dump back into the system prompt. Do not put recent-work lines back into `before_agent_start`. If a Bot needs a prior decision, `office/system.md` already tells it to call `memory_read`.

Do not hand-edit `grants.json` ops. Do not put finance types in Harness `src/`.

## How you know it worked

Restart serve on 8801 against the prove-fork Computer after `office/system.md` is there. One new instance. One Bot. One business-English wake with `profile:` set and no tool id in the text.

Then read, do not guess:

- `harness/bots/<id>/context/manifest.jsonl` has one record, and a second wake with the same files does not append another.
- `context/bot-<hash>.txt` contains that Bot’s `BOT.md` text and the profile body.
- `context/office-<hash>.txt` contains the roster and does not say “Keep messages short.”
- The Pi session’s first tool call is not `read` of `BOT.md`.
- The kernel log shows a granted finance op for that situation, or you edit the inlined profile or skill and retry on a new instance. A Wake that names the op does not count.

Leave `golden-20260920-r1` on disk and unselected. Do not merge a tape.
