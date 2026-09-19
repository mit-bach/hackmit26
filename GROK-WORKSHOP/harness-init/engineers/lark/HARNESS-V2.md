# Harness v2

Design for the runtime. One document. A later engineer can build from this file with no chat.

This is the thing we are making. A client application sits on it. The client application is not this file.

Author: lark. Date: 2026-09-19.

---

## What this is

The Harness is a GrokBot-class control plane with Pi as the per-Bot turn engine.

The operator's words (vision export, 7:08 AM):

> "I am working on replicating XAI's GrokBot architecture entirely on my own Harness. I'm using the open-source Pi coding agent as a way to make this possible, and we'll do all of my replication through extensions."

The operator's words (7:22 AM):

> "I [want] to replicate the communication protocol that GrokBot uses specifically for inter-agent communication, I really like how that works"

The operator's words (7:41 AM):

> "I'm not asking you about, is a UI. I'll figure that out later. I'm just specifically talking about the runtime and how everything's going to be done behind the scenes."

The operator's words (this turn):

> "all of my bots should not be created using subagents. They aren't subagents. They are individual"

> "it does need to be able to have that communication protocol and have that implemented very well"

> "It doesn't need to be headless in a way that I can use for my specific MIT hackathon project"

So: named Bots as standing individuals, one shared computer, a protocol that is real (accept, wake, await, log), Pi under each Bot, a surface that can be a cmux TUI for the hackathon. Headless and a hidden client UI come later. They use the same protocol.

The test of usefulness is: two Bots can hand work off, the handle completes, both transcripts show the handoff, and a human can find the log.

---

## Name map

One name for one thing.

| Name | Meaning |
| --- | --- |
| Harness | This runtime. Roster, lanes, protocol, rooms, memory, approvals, routines |
| Bot | Named standing worker. Durable identity. One process. One lane |
| child | A disposable inner helper a Bot may spawn for a bounded task. Not a Bot |
| Client system | One roster plus skills plus a computer. What a consulting engagement or a hackathon app is |
| Computer | Shared workspace for one client system. Files, shell, cwd. All of that system's Bots share it |
| Roster | Durable list of Bots for one client system |
| Lane | One in-flight turn per Bot |
| Inbox | Durable queue of work for one Bot |
| Handle | Record issued at accept time, before the receiver runs |
| Wake | Async notice that a Bot has new inbox work |
| Room | Group conversation. 2–6 Bots. Shared log. Host is the Harness |
| Host | Harness code that wakes Room members in order. Not a Bot |
| Protocol log | Canonical event stream for sends, wakes, completions, room posts |
| Transcript | One Bot's conversation, plus protocol events mirrored into it |
| Memory | Per-Bot notes. Not the Computer |
| Routine | Standing prompt that wakes the owning Bot's lane |
| Receipt | Record of one Routine run |
| Operator | The human. User DMs come from the Operator |
| Pi | `@earendil-works/pi-coding-agent`. The turn engine inside one Bot process |

A child is not a Bot. A Handle is not a Receipt. Memory is not the Computer. The Host is not a Bot.

---

## Operator intent that binds this design

Quoted from the vision export. These are requirements, not color.

**Replication target.** Reverse-engineer GrokBot on Pi through extensions (7:08 AM). After looking at OpenGrokBot and OpenMausBot, keep reverse-engineering the architecture (7:37 AM). Read OpenMausBot's docs and decompose the runtime into avenues: use existing, choose among options, or write it (7:52 AM). Bot identity "will 100% not work" out of the box. Write that extension.

**Protocol is the center.** Inter-agent communication is the part to get right (7:22 AM). Not MCP as the local bus. Out-of-box Pi packages may poke a live process. The semantics (durable Bot, accept vs complete, await, wake if asleep, group Host) are ours.

**Runtime, not UI.** UI later (7:41 AM, 12:02 PM). For clients, the interior can be hidden later (7:37 AM). For this hackathon cut, a cmux TUI is allowed. Do not spend the design on a product shell.

**Pi as worker, Harness as product.** Build on Pi because it is the modular open loop (7:41 AM). Do not use Claude Agent SDK. The Harness owns roster, lanes, mailboxes, routines, isolation, connectors. Pi owns: model stream, tool dispatch, compaction, `read` / `bash` / `edit` / `write`.

**Client systems on top.** This runtime powers client AI systems (7:37 AM, 11:52 AM). Novel client applications must not be hardcoded into the Harness (this turn). A finance office is one Client system. The Harness does not know invoices, ledgers, or role names from that office.

**Install real Pi and real packages** (12:27 PM). Pin GitHub/npm packages that we actually use. Write the layers that do not exist.

**Effort order.** Protocol and Bot individuality first. Usefulness: can they talk, can you see it, does a Handle finish. Unattended cloud computer and connector marketplace are later.

---

## What we are not making

1. A Bot is not a child. The roster is not `pi-subagents` agent names.
2. The Harness is not a coding-agent skin. Pi is inside a Bot. The Operator talks to Bots.
3. The Harness is not a workflow graph. Routing is roster descriptions, `@` mentions, and a Bot that owns the next step.
4. The Harness is not MCP rooms for local Bot-to-Bot. MCP is for tools on other machines.
5. The Harness is not a Client system. It does not ship finance pipes, a "Chief of Staff" persona, or any other domain roster.
6. This cut is not a multi-tenant AWS product. Same protocol later. Different process supervisor.

---

## What a Client system needs from the Harness

A real Client system (the kind of office that has specialists, a shared book, and a human gate) needs these properties. The Harness supplies them as primitives. The Client system supplies names, instructions, files, and skills.

**Named specialists.** Each Bot owns a class of objects and a "done when" line. Ownership is in the Bot's instructions and in which paths it is allowed to write. The Harness does not interpret the objects.

**Bounded handoffs, not a mesh.** The specialist that owns a counterparty identifies a line of work. The next specialist checks. They do not both invent the same fact. The protocol is: one owner at each stage, a Handle, a path on the Computer, a result. Official GrokBot guidance is the same: ask for a single owner at each stage.

**A shared store.** All Bots in one Client system share one Computer. Artifacts move as files. Messages stay short. Memory does not move.

**A human gate.** Consequential actions (pay, publish, lock, send-as-user, delete-tree) stop on the Operator. A peer Wake is not approval.

**Visible coordination.** A Room when several Bots share one outcome. Direct handoff when one Bot owes another a result. The Operator can watch either.

**Done-when is per Bot.** The Harness completes a Handle when that Bot's turn ends or parks on the Operator. The Client system decides whether the *work* is done.

---

## Process topology (this cut)

Hackathon default: every Bot is a live Pi process in a cmux pane. The Operator can see them. That is allowed.

```
Operator
  │  types in a Bot pane, or in a Room
  ▼
cmux
  ├─ Pi process  HARNESS_BOT=<slug>     ← Bot
  ├─ Pi process  HARNESS_BOT=<slug>     ← Bot
  └─ Pi process  HARNESS_BOT=<slug>     ← Bot
         │
         ▼
    Computer  (one cwd / volume for this Client system)
         ├─ harness/roster.json
         ├─ harness/protocol.jsonl
         ├─ harness/bots/<botId>/inbox.jsonl
         ├─ harness/bots/<botId>/handles/<handleId>.json
         ├─ harness/bots/<botId>/memory/...
         ├─ harness/rooms/<roomId>/log.jsonl
         └─ workspace files the Client system cares about
```

Each Pi process loads the Harness extensions. On start it binds to exactly one Bot from the Roster (`HARNESS_BOT`). It does not bind to "whatever child name the model picks."

Later (consulting, unattended): a supervisor starts `pi --mode rpc` for a Bot whose inbox is nonempty and whose process is down. Same inbox. Same Handle. Same Computer. No protocol change.

---

## Bot

A Bot is a durable record plus a live lane.

### Record (Roster)

```json
{
  "id": "bot_01",
  "name": "Display name",
  "slug": "slug",
  "purpose": "one sentence the others search",
  "instructions": "standing duty, object ownership, done-when, what this Bot must not do",
  "skills": ["optional-skill-names"],
  "connectors": ["optional-connector-names"],
  "approvalLevel": "ask"
}
```

Rules:

1. `id` is opaque and durable. Never reuse it as a display name.
2. `slug` is the bind key for a process (`HARNESS_BOT=slug`).
3. Create a Bot only when the Operator asks and the Roster does not already cover that purpose. The Harness does not auto-spawn duplicates.
4. A Bot is not a Pi session file and not a markdown file under `~/.pi/agent/agents`.
5. One Bot, many conversations (Operator DM, peer DM, Rooms). Membership fans out. Execution stays one lane.

### Live bind

When a Pi process starts:

1. Read `HARNESS_BOT` and the Roster.
2. If the slug is unknown, refuse to start the session tools. Do not invent a Bot.
3. Inject standing instructions, Memory prefix, protocol block, and this Bot's id/slug.
4. Advertise idle on the lane.
5. Drain inbox if work is waiting.

Status the Roster can report: `offline` | `idle` | `running` | `blocked`. Offline means no process holds the bind. Idle means process up, no turn. Running means a turn. Blocked means the turn is waiting on the Operator.

### What a Bot process is allowed to be

Pi with Harness extensions, cwd on the Computer, Memory from `harness/bots/<botId>/memory`. That is a Bot.

A `pi-subagents` runtime agent whose name happens to equal a slug is not a Bot. Do not register Roster slugs as children. If a Bot needs a throwaway helper, it may call a child tool with a *task* description. The child has no Roster id, no Memory, no Routines, no lane of its own.

---

## The protocol

This is the product. Official GrokBot contract, compressed from [Message and collaborate](https://docs.x.ai/grok-bot/chat-and-collaboration):

- The Operator messages a Bot. A new Operator message can redirect the current turn. "Stop now" ends the turn. It does not undo finished work.
- A Bot can send an asynchronous message to another Bot. The receiver wakes, handles it, and can reply later. The handoff is visible in the conversation.
- A group is 2–6 Bots plus the Operator. `@` names who wakes. Bot-to-group body is text. Files live on the Computer or go DM-to-DM.

OpenMausBot's read of the same product, which we implement: membership fans out; execution is serialized per Bot; Bot-to-Bot is a Wake, not a second lane; in a Room the Host wakes members in turn; a busy member is woken later, never skipped; Routines share the Bot's lane.

### Identifiers

```text
BotId        Roster id
Conversation operator_dm(botId) | peer_dm(from, to) | room(roomId)
TurnId       one in-flight turn per Bot
HandleId     issued at accept, before run
Seq          monotonic per Conversation, for tails
```

### Message kinds

| Kind | From → To | Preempts the current turn? | Default busy policy |
| --- | --- | --- | --- |
| `user_dm` | Operator → Bot | Yes. Redirect | `supersede` |
| `user_stop` | Operator → Bot | Yes. Abort. No undo | `supersede` |
| `a2a_handoff` | Bot → Bot | No | `queue` |
| `group_post` | Operator or Bot → Room | No. Host wakes the set | `queue` |
| `group_mention` | Operator or Bot → Room + subset | No. Host wakes mentioned Bots | `queue` |
| `result` | Bot → Conversation that issued the Handle | n/a | n/a |

Do not give Bots `supersede` on each other. Specialists cannot finish if every peer aborts them.

### Tools (names are the product)

Every Bot process exposes:

```text
bot_search_agents(query, status?)
bot_get_profile(bot_id)
bot_send_prompt(bot_id, prompt, mode=async, on_busy=queue, paths?, conversation?)
bot_await_turn(handle_id)
bot_get_agent_transcript_tail(bot_id, limit, before_seq?)
```

`mode`:

| mode | Meaning |
| --- | --- |
| `async` | Accept, return Handle, do not wait. Default |
| `fire_and_forget` | Accept, no Handle |
| `blocking` | Forbidden for real work. Refuse |

`on_busy` for `a2a_handoff` defaults to `queue`. The Operator path is not this tool. The Operator types in the pane. That path is `user_dm`.

### `bot_send_prompt` — accept then run

1. Resolve `bot_id` in the Roster. If missing, return `{ accepted: false, reason: "unknown" }`. Do not search live process lists as identity.
2. Allocate `HandleId`. Write Handle file `{ status: "accepted", from, to, prompt, paths, conversation, createdAt }`. fsync. This is accept.
3. Append one inbox row for the target Bot. fsync.
4. Append one protocol-log row `send.accepted`.
5. If the target process is live, poke it (inbox watch is enough in this cut). If it is not live, Handle stays `accepted` / `queued` until a process binds. For the hackathon, all Bots are live panes. A missing process is an Operator error, not a silent child spawn.
6. Return `{ accepted: true, handle_id, bot_id, slug, status }` immediately.

Do not run the target's turn inside the sender's tool call. Accept is not completion. The sender's model must not be told "dispatch this yourself with another tool."

### Handle states

```text
accepted  →  queued | running | cancelled
queued    →  running | cancelled
running   →  completed | failed | cancelled | blocked
blocked   →  running | cancelled
```

| status | Meaning |
| --- | --- |
| `accepted` | Durable. Receiver may still be idle or offline |
| `queued` | Receiver is busy. Peer work waits |
| `running` | Receiver's turn has started on this Handle |
| `blocked` | Turn parked on Operator approval. Lane still occupied |
| `completed` | Turn ended. `result` is a short text plus paths |
| `failed` | Turn ended in error |
| `cancelled` | Operator stop, or sender cancelled |

Nothing else writes these files. The lane owner (target Bot process) moves `accepted`/`queued` → `running` → terminal. The sender never marks complete.

### `bot_await_turn`

Watch the Handle file (and optionally `turn_end` on the target process).

Return:

```text
{ handle_id, status, done, result?, seq? }
```

`done` is true only for `completed | failed | cancelled`.

`blocked` is not `done`. Keep awaiting, or return `blocked` as a distinct wait outcome so the sender can tell the Operator. Do not treat an acknowledgement message ("got it, working") as `done`.

This tool may poll. It must observe a writer that actually completes the Handle. A read of a file that never changes is not await.

### What moves on the wire

On the message: text, Conversation id, sender BotId, HandleId, optional path list on the Computer, mention list.

Not on the message: the sender's Memory, the sender's full Transcript, raw tool results, tokens. Point at files.

### Visibility

On accept: protocol log + a line in the sender Transcript ("handed to `<slug>`, handle `h_…`").

On complete: protocol log + a line in the sender Transcript and the receiver Transcript. GrokBot: "You can see the handoff in the conversation."

`bot_get_agent_transcript_tail` reads the protocol log and the target Bot's session tail, without screenshot pixels, by `seq`.

---

## Lane

Per Bot, one scheduler, four priorities:

1. `user_stop`
2. `user_dm`
3. `a2a_handoff` / `group_mention` / `group_post`
4. Routine Wake

Only one item is *running*. The others sit in that Bot's inbox on disk.

When a turn ends (including failed, cancelled, or leaving `blocked` after the Operator answers):

1. Write the Handle terminal state and `result`.
2. Append protocol log `turn.end`.
3. Drain the next inbox row. User rows before peer rows.

When the Operator types in a busy Bot's pane: that is `user_dm`. Abort or steer the current turn per Pi's follow-up/steer. Peer work that was running goes back to `queued` unless it already completed.

A turn parked on approval occupies the lane. Status `blocked`. Do not start the next peer Wake until the Operator answers or stops.

---

## Room

A Room is not N DMs. It is one log plus a Host.

Roster may list:

```json
{
  "id": "room_floor",
  "title": "Floor",
  "members": ["slug-a", "slug-b", "slug-c"]
}
```

Members are Bot slugs. 2–6.

### Host algorithm

On `group_post` or `group_mention`:

1. Append the post to `harness/rooms/<roomId>/log.jsonl`.
2. Compute the wake set: mentioned Bots, or all members if unguided. Keep unguided conservative.
3. For each member in roster order:
   - If that Bot is busy, wait. Do not skip. After a wait cap, write a chip on the Room log ("`<slug>` still busy, round continued") and proceed.
   - If idle, enqueue a Wake on that Bot's inbox with the post text and the Room id. Wait until that Handle is `done` or `blocked`, then the next member.
4. Stop the round on Operator supersede, a configured round cap, or every member `done`.

The Host is Harness code in each process, coordinated by the Room log and file locks. It is not "whoever the model thinks is Chief of Staff."

Bot-to-Room body is text. Binary goes to a path on the Computer, and the Room post names the path.

---

## Shared computer

All Bots in one Client system share one cwd tree. That is the GrokBot property that makes handoffs cheap: files, not dumped context.

Layout:

```text
<computer>/
  harness/          Harness state (protocol, inboxes, memory, rooms)
  <client files>    Whatever the Client system stores
```

Rules:

1. Isolation is per Client system, not per Bot. Do not share this tree across consulting clients later.
2. For this cut, the Computer is the project directory the panes start in.
3. If two Bots would write the same path at once, take a lease file `harness/leases/<hash>`. The second Bot queues. Default is still "one owner at each stage" so leases are a backstop.
4. Pi's `read` / `bash` / `edit` / `write` are the computer tools. Do not invent a second filesystem. Do not allowlist a toy shell and call it a computer.

---

## Memory

Memory belongs to the Bot. The Computer is shared. Those are different disks.

Layout (OpenMausBot invariants, scoped to our tree):

```text
harness/bots/<botId>/memory/
  MEMORY.md
  topics/<topic>.md
  log/YYYY-MM-DD.md
```

Rules:

1. Never a shared brain. Bot A cannot `memory_read` Bot B.
2. On every turn, inject the first 200 lines or 24 KB of `MEMORY.md`, whichever cuts first.
3. Topic files and daily logs are not auto-injected. The Bot reads them with tools when it needs them.
4. Writes are atomic (temp file, then rename). Secrets redacted before disk.
5. Compaction must not wipe identity: injection is on `before_agent_start` every turn, from disk, not from the compacted session alone.
6. Recent-work brief (later in this cut if time, required before Rooms feel smart): ~10 lines from this Bot's other conversations in the last two days, not a merge of other Bots' Memory.

Do not install three memory packages. Markdown files plus injection is the store for this cut. Add search later as one index over daily logs and protocol log.

---

## Approvals

Fail closed on a small class: send-as-user, pay, publish, merge, deploy, delete-tree, or whatever the Client system marks consequential.

Rules:

1. A peer Handle is not approval.
2. The model does not get to skip the gate by not calling a tool. The Harness intercepts the dangerous tool (or wraps Pi's permission hook) and sets the Handle `blocked` until the Operator confirms.
3. `ask_user` is the structured question surface. It is backed by that intercept, not a polite guideline.
4. `approvalLevel` on the Bot record selects strictness. `ask` is the default.
5. Waiting on the Operator occupies the lane.

This cut can use Pi's confirm UI in the pane. The mapping Handle → `blocked` → Operator answer → resume is required. A naked confirm that does not touch the Handle is not the broker.

---

## Routines

A Routine is a standing prompt owned by one Bot. It is a Wake on that Bot's lane. It is not an in-session `/loop` into whoever is currently talking.

Record:

```json
{
  "name": "morning-brief",
  "bot": "slug",
  "cadence": "daily",
  "prompt": "text",
  "conversation": "operator_dm | room:room_id"
}
```

Fire:

1. Write a Receipt `{ status: "queued", bot, name, at }`.
2. Enqueue a Wake on that Bot's inbox with the prompt. Same path as `a2a_handoff`.
3. When the Handle completes, Receipt → `completed` (or `failed` / `missed`).

This cut: the Operator (or a simple timer in the owning Bot process) fires a Routine. Cadence strings are data. Do not claim 24/7 unattended until a supervisor exists.

Do not inject the Routine prompt into a random pane. The owning Bot's lane is the only legal destination.

---

## Transcript and logs

The Operator asked where chat logs go. One answer:

| Stream | Path | What it is |
| --- | --- | --- |
| Protocol log | `harness/protocol.jsonl` | send, accept, poke, running, blocked, completed, room post, routine fire |
| Handle | `harness/bots/<botId>/handles/<id>.json` | lifecycle of one send |
| Inbox | `harness/bots/<botId>/inbox.jsonl` | waiting work |
| Room log | `harness/rooms/<roomId>/log.jsonl` | group posts and Host chips |
| Pi session | Pi's session file for that process | the Bot's full turn (tools, model text) |
| Daily log | `harness/bots/<botId>/memory/log/YYYY-MM-DD.md` | short diary, not stuffed into the next prompt |

`bot_get_agent_transcript_tail` reads protocol log + Pi session tail for that BotId.

If a human cannot answer "what did slug-a ask slug-b, and did it finish?" from `protocol.jsonl` and the Handle file, the protocol is not implemented.

---

## Tools and commands (this cut)

### Tools the model may call

| Tool | Who | Does |
| --- | --- | --- |
| `bot_search_agents` | any Bot | Roster search. Optional status filter |
| `bot_get_profile` | any Bot | One Bot record |
| `bot_send_prompt` | any Bot | Accept + inbox + Handle |
| `bot_await_turn` | any Bot | Watch Handle until done |
| `bot_get_agent_transcript_tail` | any Bot | Tail by seq |
| `room_post` | any Bot in a Room | Append + Host wake |
| `room_read_log` | any Bot in a Room | Read Room log |
| `memory_read` / `memory_write` | self only | That Bot's Memory tree |
| `ask_user` | any Bot | Operator question. Brokered |

Pi's `read` / `bash` / `edit` / `write` stay. They run on the Computer.

### Commands the Operator may type

| Command | Does |
| --- | --- |
| `/roster` | Print Bots and live status |
| `/bot` | Show this process's bound slug |
| `/handles` | Open Handles for this Bot |
| `/room` | Attach this Bot to a Room from the Roster (or show current) |
| `/routine run <name>` | Fire a Routine onto its owning Bot's inbox |

No command creates a Bot from a child template. Creating a Bot is editing the Roster (Operator-owned JSON) and starting a pane bound to that slug.

---

## Extension map

The operator asked to decompose the runtime into three avenues (7:52 AM). Frozen choices for this cut:

### Use existing

- Pi as the turn engine in each Bot process (TUI pane now, `pi --mode rpc` later)
- Pi skills, loaded per Bot from that Bot's allowlist
- Pi session files as the worker-local Transcript cache
- OS filesystem as the Computer and as the inbox bus

### Choose among options (frozen)

| Layer | Choice | Why |
| --- | --- | --- |
| Live poke | `fs.watch` on that Bot's inbox directory, plus a 1s poll backup | No extra comms package. Durable file is the source of truth. Socket poke can be added later without changing Handle semantics |
| Memory store | Markdown tree per BotId, injected on turn start | Inspectable. Matches OpenMausBot invariants. No shared brain |
| Inner child | Optional, off by default. If on, official Pi subagent or `pi-subagents` as a *task* helper only | Must not receive Roster slugs |
| Group log | Our Room jsonl | We need a Host. A live-process chat bus without a Host is not a Room |
| Await | Watch Handle file until terminal status | Same disk as accept. Works if we later add `subscribe turn_end` as an accelerator |

### Write it (this is the Harness)

- Roster + bind (`HARNESS_BOT`)
- Inbox, Handles, await, lane, user-preempt vs peer-queue
- Protocol log + transcript tail
- Room Host
- Memory injection, redaction, atomic write, per-Bot path
- Approval intercept + `blocked` Handle
- Routine records that enqueue on the owning Bot
- Pane / process topology for cmux

Do not replace a write-it layer with three community chat packages.

---

## How a handoff works

Example: Bot `alpha` needs Bot `beta` to write a file and return.

1. `alpha` calls `bot_search_agents("…")` and `bot_get_profile("beta")` if it does not already know the owner.
2. `alpha` writes whatever context `beta` needs onto the Computer (a path).
3. `alpha` calls `bot_send_prompt({ bot_id: "beta", prompt: "… see path …", paths: ["…"] })`.
4. Tool returns `{ accepted: true, handle_id: "h_…", status: "accepted" }`. `alpha` does not tell the Operator that `beta` finished.
5. Harness writes Handle + inbox row + protocol log. `beta`'s process wakes.
6. `beta` runs one turn. Reads the path. Writes a result path. Turn ends.
7. Harness sets Handle `completed` with a short `result` and paths. Protocol log `turn.end`.
8. `alpha` calls `bot_await_turn({ handle_id })` and gets `done: true`.
9. Both Transcripts and `protocol.jsonl` show the handoff.

If `beta` is mid-turn on other peer work, the new row is `queued`. `alpha`'s Handle stays not-done until `beta` drains it.

If `beta` needs the Operator, Handle goes `blocked`. Lane stays occupied. `alpha` keeps awaiting or reports blocked.

---

## How a Room round works

1. Operator or a Bot `room_post`s to Room `floor`: "each of you: status in two lines."
2. Host appends the log, then wakes member 1. Waits for that Handle.
3. Member 2 is busy on a DM. Host waits. Does not skip. After the cap, chip and continue, or keep waiting if the cap is "never skip" for this cut (default: wait, cap 60s, then chip).
4. Member 3 runs.
5. Round ends. Room log is the shared brief. Memories stay per Bot.

---

## Client system manifest

The Harness consumes a JSON file. Path: `HARNESS_ROSTER` or `<computer>/harness/roster.json`.

Shape:

```json
{
  "system": "client-system-name",
  "version": "1",
  "description": "one paragraph",
  "computer": ".",
  "bots": [ { "id": "", "name": "", "slug": "", "purpose": "", "instructions": "", "skills": [], "connectors": [], "approvalLevel": "ask" } ],
  "rooms": [ { "id": "", "title": "", "members": [] } ],
  "routines": [ { "name": "", "bot": "", "cadence": "", "prompt": "", "conversation": "" } ]
}
```

The Harness does not ship a domain Roster. A hackathon office, a support desk, or any other Client system is a file like this plus files on the Computer. Swap the file. The protocol does not change.

Do not bake specialist names, object types, or pipe graphs into Harness code.

---

## Starting the floor (hackathon)

1. Write `harness/roster.json` for the Client system.
2. Open one cmux pane per Bot.
3. In each pane: `HARNESS_BOT=<slug> pi` with cwd on the Computer and the Harness package loaded.
4. Confirm `/bot` prints that slug and `/roster` sees live status.
5. Prove the protocol with a two-Bot handoff before any domain work.

If a pane is not bound, it is not a Bot. It is a generic Pi. It must not appear in `bot_search_agents`.

---

## Build order

Matches how GrokBot is designed: identity and computer first, coordination second, autonomy third.

1. Roster + bind + `/bot` + `/roster` with live status. Two panes. Same Computer.
2. Inbox + Handle + `bot_send_prompt` + `bot_await_turn` + protocol log. Prove accept ≠ complete. Prove a Handle reaches `completed` when the receiver's turn ends.
3. Mirror the handoff into both Transcripts. `bot_get_agent_transcript_tail`.
4. User DM preempts. Peer mail queues.
5. Memory injection per BotId.
6. Room Host, three Bots, no skip of a busy member.
7. Approval intercept + `blocked`.
8. Routine fire onto the owning Bot's inbox, Receipt updates.
9. Only then: Client system content (skills, files, domain prompts).

Do not start with a client dashboard, a connector catalog, or a custom UI.

---

## Done when (this cut)

The Harness is useful when all of these are true on disk, not in a prompt:

1. Two bound Bot processes exchange a handoff. The Handle is `accepted` before the receiver runs and `completed` after the receiver's turn ends.
2. `bot_await_turn` returns `done: true` without a human editing JSON.
3. `protocol.jsonl` plus the Handle file answer who sent what, to whom, and whether it finished.
4. Roster search returns Bots by slug and purpose, with `idle` / `running` / `blocked` / `offline`. It does not return child ids or `agent-hostname-pid` strings.
5. A third Bot can sit in a Room. The Host wakes members in order. A busy member is not skipped.
6. Memory files for Bot A are not readable as Memory by Bot B.
7. A consequential tool parks the Handle `blocked` until the Operator answers.
8. A Routine enqueue lands on the owning Bot's inbox, not on the Operator's current pane.
9. No Roster slug is registered as a child.

Until (1)–(3) work, nothing else matters.

---

## Later (same protocol)

- Supervisor that starts a sleeping Bot from inbox
- `pi --mode rpc` workers
- Per-client Computer (container/VM)
- Connector facade (`search_connected_tools` / `call_connected_tool`)
- Out-of-session cadence (launchd/systemd) and catch-up Receipts
- Recent-work brief and `session_search`
- Teach-by-demonstration → skill
- Client UI that never shows Pi

Do not wait on those to implement send/await.

---

## Sources

Operator speech:

- Vision export prompts in `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/Source-material/Grok-Pi Coding Agent GrokBot Extensions Research-20260919-1439.md` (7:08, 7:22, 7:37, 7:41, 7:52, 11:52, 12:02, 12:27)
- This turn's instruction: Bots are individuals, not children; protocol must be real; hackathon need not be headless; Client system content stays out of the Harness

Product protocol (external):

- https://docs.x.ai/grok-bot/overview
- https://docs.x.ai/grok-bot/chat-and-collaboration
- https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md
- https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/memory.md

Client-system *shape* only (domain text must not enter Harness code):

- `/Users/dominikbach/olympus/hackmit/hackmit26/design-workshop/dominik/cfo-office-processes.md`
