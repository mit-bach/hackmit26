# What each Bot is actually fed

Read from the code that builds a turn, not from the Bot files as a design. Harness: `.harness/Harness-v2/extensions/index.ts` and `src/prompt.ts`. Client: `.cfo-v2/office/computer/cfo/extensions/index.ts`. Golden roster: `.cfo-v2/office/instances/golden-20260920-r1/harness/roster.json`.

There is no context builder. One hook concatenates strings onto Pi’s own system prompt. The rest of the “agent” is a markdown file on disk that the model may or may not open.

## Every turn, the same four blocks

On `before_agent_start`, Harness appends this to whatever Pi already put in the system prompt:

```255:264:.harness/Harness-v2/extensions/index.ts
  pi.on("before_agent_start", (event) => {
    const extra = [
      identityBlock(bind.bot, bind.roster),
      PROTOCOL_CARD,
      memorySection(bind.computerRoot, bind.bot.id),
      recentWorkSection(bind.computerRoot, bind.bot.id),
    ]
```

The Client extension does not add a system prompt. It registers `search_connected_tools` and `call_connected_tool`, blocks `ask_user`, and returns skill directories from `resources_discover`.

Pi then keeps its own session jsonl. The next wake is a user message, not a new agent. The system prompt is rebuilt and appended again. Old turns stay in the session until Pi compacts them. Nothing in this repo decides what to drop.

### 1. Identity block

`identityBlock` in `src/prompt.ts` is one template for every Bot. The only per-Bot fields are name, id, slug, purpose, the roster `instructions` string, the skill-name list, and the connector-name list. Then it pastes the other fifteen Bots as `slug (id, name): purpose`.

That roster `instructions` string is the standing order. For Email it is one sentence: read `office/bots/email/BOT.md`, obey `office/constitution.md`, and a few bans. The file is not inlined. Constitution is not inlined. If the model does not call `read`, those documents are not in the window.

The template also says “Keep messages short” and “Do not dump Memory or transcripts into a handoff.” That line is in the shared prompt for every Bot, including the ones the showcase wanted to talk at length.

### 2. Protocol card

`PROTOCOL_CARD` in `src/protocol-card.ts` is one string. Harness writes it to `harness/PROTOCOL.md`, to each `harness/bots/<id>/SYSTEM.md`, and into the system prompt. The sixteen `SYSTEM.md` files on the golden Computer are the same card. They are not per-Bot system prompts.

The card teaches channels: Operator text, `ask_bot` for the pair thread, `room_post`, `memory_read` / `memory_write` for this Bot only, `ask_user` rules. It does not teach finance, Catalog use, or how to decide what belongs in memory.

### 3. Memory prefix

`memorySection` calls `injectMemoryPrefix`. If `memory/MEMORY.md` exists for that Bot, the first 200 lines or 24 KB are pasted into the system prompt under a fixed heading. There is no shared module that says what to store, when to read, or how a finance decision differs from a chat note.

`memory/log/<day>.md` is appended by `appendDailyLog` when a turn finishes. That log is not pasted back. `memory/topics/` is listed by an overview helper and is not pasted. The model sees topics only if it calls `memory_read` with a path.

So “a memory module injected into all agents” does not exist. What exists is a file dump of one Bot’s `MEMORY.md`, plus two sentences in the protocol card, copied onto every Bot.

### 4. Recent work

`recentWorkSection` is the last ten protocol events from the last two days that mention this Bot, each cut to 120 characters. It is a scratch index, not the pair thread and not the Pi session.

## What is not in the system prompt

| Material | Where it lives | In the window? |
| --- | --- | --- |
| `office/bots/<slug>/BOT.md` | Disk. Roster says “read this.” | Only if the model calls `read`. |
| `office/constitution.md` | Disk. Same instruction. | Only if the model calls `read`. |
| Profile text (`profiles/*.md`) | Disk. Client swaps the active Grant when the wake contains `profile:`. | Not inlined. The wake names the profile. The tool list changes. The profile’s prose does not. |
| `SKILL.md` | Directories returned by `resources_discover`. Names are the intersection of the Grant’s skill list and the roster’s skill list. | Pi’s skill loader, not this hook. A skill loads when Pi decides to load it. Unused skills are not in the prompt. |
| Catalog and Grants | `cfo/catalog.json`, `cfo/grants.json`. | Not in the prompt. The model discovers ops with `search_connected_tools`. |
| Kernel `memory.tools.get_decision_memories` | A Catalog read. | Separate from Harness `MEMORY.md`. The golden month never called it. |
| Daily memory log and topics | `memory/log`, `memory/topics`. | Not injected. |

The wake itself is the user message, built by `formatWake` in `src/lane.ts`: kind, sender, handle, conversation, paths, then the prompt text. On a peer handoff it appends a required-tool sentence that names `ask_bot`. On some operator DMs it appends a sentence that names `bot_ask`. That is the one place the harness forces a tool by name. It forces the chat tool, not a finance tool.

## Session to session

A Bot process is one Pi session. Wakes append. The system prompt is replaced in the sense that `before_agent_start` runs again, but the transcript of prior wakes stays.

Across a process restart, continuity is:

- the Pi session file under `harness/bots/<id>/pi-session/`, if Pi reloads it
- `MEMORY.md` if someone wrote it, truncated on the way back in
- ten short protocol lines from the last two days

There is no compaction policy in this repo, no scored retrieval, and no shared memory bus. Bot A cannot see Bot B’s memory. A handoff is supposed to point at a path. The golden tapes show the model often answering in one `ask_bot` and stopping, which matches the prompt line that tells it to keep messages short and not dump memory.

## Why this feels like a copied AGENTS.md

The modular pieces that exist are files, not a composer.

- One protocol card, byte-identical, written into sixteen `SYSTEM.md` files.
- One identity template. Personality is a roster string plus a Bot file the model might read.
- Skills are an allowlist of directory names. They are not composed into the system prompt, and they do not grant tools.
- Memory injection is `readFile` of `MEMORY.md` with a line cap. The daily log and the topic tree are unused by that function.
- Finance tools are a second door (`call_connected_tool`) with no prompt module that says when a read is required and when a shell `cat` of `data/` is a miss.

Nothing assembles “constitution + memory policy + this Bot’s object + this profile’s tool rubric + the open item” into one context. The model is pointed at a pile of markdown and a session log. That is why a light edit to one `SKILL.md` does not change the next turn unless the model loads that skill, and why sixteen agents share the same memory instructions without sharing a memory module.
