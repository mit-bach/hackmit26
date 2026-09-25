# Context module

Proposed replacement for `identityBlock` in `.harness/Harness-v2/src/prompt.ts`. The current block tells the model to read `office/bots/<slug>/BOT.md` and `office/constitution.md`. On the golden AP session that is what happened: the first tool result is the text of `BOT.md`. The instructions were not in the window until the model spent a call to fetch them.

This design puts the text in the window. It also keeps the cached prefix stable. Recent work and `MEMORY.md` stay out of the system prompt. Those two strings change every wake, and today they sit in front of the whole conversation, so the provider reprocesses every prior turn.

## Two layers, both inlined

The module is one function, `assembleContext(computer, bot, profile)`. It returns two strings and their hashes. The hashes are how you know the prefix did not move.

**Office layer.** Same bytes for every Bot. Loaded from one file, `office/system.md`, not copied into sixteen `SYSTEM.md` files. Contents:

- What a Bot is on this Computer: standing worker, one Computer, files are the artifacts.
- Channels: assistant text is the Operator; `ask_bot` is the pair thread; `message_operator` during a peer wake; rooms; intercept. This is today’s protocol card, with the line “Keep messages short” removed.
- Memory policy: this Bot’s `memory/` only; what belongs there (a decision you will need next month, with the id); what does not (a transcript dump, another Bot’s notes). The policy is the module. `MEMORY.md` is not pasted here.
- Tool policy: finance facts come from the Grant door. A shell read of `data/` is not a substitute. The module does not name an op. Naming ops in the prompt is how a trial gets counterfeit tool use.
- Roster: slug, display name, purpose. One list, inlined. Not “go read roster.json.”

**Bot layer.** Bytes for this slug. Changes only when that Bot’s source files change.

- The full text of `office/bots/<slug>/BOT.md`.
- The full text of the active profile file, `office/bots/<slug>/profiles/<profile>.md`, once the wake has selected a profile.
- The body of each skill that profile’s Grant allowlist names. Inlined. Not “skills allowlist: inbox-triage” and not “read SKILL.md.”
- Constitution clauses that are office-wide stay in the office layer. Do not also paste them here.

`before_agent_start` sets the system prompt to:

```text
<Pi base prompt>

<office layer>

<bot layer>
```

Nothing after the bot layer is allowed in the system prompt. If the office hash and the bot hash match the previous request, the prefix is the same bytes and the provider can reuse the cache through the end of the system prompt and through every session message that has not changed.

## What moves to the end of the turn

These change often. They are one user message appended after the existing session, immediately before the new wake. They are not part of the system prompt.

- Active profile name, only if it differs from the profile already baked into the bot layer. A profile switch rebuilds the bot layer and breaks the cache from that point. That is acceptable. It is rare. Do not also restate the profile on every wake.
- `MEMORY.md` is not pasted. The memory policy in the office layer tells the Bot to call `memory_read` when the open item is one it has seen before. A dump of the file on every turn is the cache break we have now.
- Recent work, if you still want it: the ten short protocol lines, as this trailing message, not as a system block. Dropping it is better. The session already contains the prior turns.

The wake text stays the last user message. It stays business English. It does not say “read BOT.md” and it does not name a Catalog op.

## What the session file looks like

Today’s AP file `harness/bots/bot_ap/pi-session/…jsonl` does not contain the system prompt. Pi says so in the protocol card. The file is a header, a model line, then messages. The first user message is the wake. The first tool result is `BOT.md`, because the model obeyed “read this file.”

```json
{"type":"session","version":3,"id":"01a0bf47-…","cwd":"…/golden-20260920-r1"}
{"type":"model_change","provider":"…","modelId":"…"}
{"type":"message","message":{"role":"user","content":[{"type":"text","text":"[harness wake]\nkind: a2a_handoff\nfrom: bot_books\n…"}]}}
{"type":"message","message":{"role":"assistant","content":[{"type":"toolCall","name":"read","arguments":{"path":"…/office/bots/ap/BOT.md"}}]}}
{"type":"message","message":{"role":"toolResult","toolName":"read","content":[{"type":"text","text":"# ap\n\n## Identity\n\nYou are Bot `ap`…"}]}}
```

Under this module the session file gains two records, written when the hash changes, not on every wake. The model does not open `BOT.md`. The instructions are already in the system prompt, and the session records the bytes that were used so a later reader can see them without guessing.

```json
{"type":"session","version":3,"id":"…","cwd":"…/golden-20260920-r1"}
{"type":"model_change","provider":"…","modelId":"…"}
{"type":"context","layer":"office","hash":"sha256:ab12…","bytes":8420}
{"type":"context","layer":"bot","slug":"ap","profile":"prepare","hash":"sha256:cd34…","bytes":6100}
{"type":"message","message":{"role":"user","content":[{"type":"text","text":"[harness wake]\nkind: a2a_handoff\nfrom: bot_books\n… Open bill INV-001. Three-way match. You do not pay."}]}}
{"type":"message","message":{"role":"assistant","content":[{"type":"toolCall","name":"call_connected_tool","arguments":{"name":"…"}}]}}
```

The `context` records store the hash and the byte length in the jsonl. The full office text and the full bot text live beside the session as `context/office.txt` and `context/bot-ap-prepare.txt`, addressed by that hash. Putting the full markdown into every jsonl line would copy the same thousands of tokens onto every turn. The hash is the proof the prefix did not move. If either file changes, a new `context` record appears and the cache breaks once, on purpose.

A turn that only adds a wake does not write a new `context` record. The jsonl grows by the user message, the assistant message, and the tool results. That is the part that should miss the cache. The system prompt should not.

## What this is not

- Not sixteen copies of `SYSTEM.md`.
- Not a roster string that says “Read office/bots/ap/BOT.md”.
- Not `MEMORY.md` or recent work inside `before_agent_start`.
- Not a skill allowlist of names. The skill body is in the bot layer, or it is not in the window.
- Not a second system prompt from the Client extension. One assembler owns the prefix. The Client extension keeps the Grant door and nothing else.
