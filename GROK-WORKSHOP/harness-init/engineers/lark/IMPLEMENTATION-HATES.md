# IMPLEMENTATION-HATES

Document of defects, missing protocol, and claims the Harness cannot keep.

This is not a redesign. A later engineer can act from this file with no chat.

Author: lark. Part: analysis. Date: 2026-09-19.

---

## Name map

One name for one thing. If two labels exist in the sources, this map picks one.

| Name | Meaning |
| --- | --- |
| Harness | The shipped package `foundry-harness` at `/Users/dominikbach/olympus/hackmit/hackmit26/Harness` |
| Foundry | The GrokBot-class control plane the operator asked for |
| Bot | Named standing identity from Foundry output (`id`, `slug`, `purpose`, `instructions`) |
| child | A `pi-subagents` runtime agent. Disposable. Not a Bot |
| handle | Accept-time record for a send. Returned before the turn ends |
| lane | One in-flight turn per Bot |
| inbox | Durable per-Bot queue of work |
| room | Foundry group with a host and members, from Foundry output |
| agent-room | Upstream package `pi-agents-talk-to-each-other` at commit `e4f162a` |
| agent-room agent id | `agent-${hostname}-${process.pid}`. Live process id. Not a Bot slug |
| supervisor | Process that can start a sleeping Bot and drain that Bot's inbox |
| computer | Shared tenant machine (files, shell, browser). One per client, shared by that client's Bots |
| memory | Per-Bot `MEMORY.md` plane. Not shared files |
| routine | Standing wake on the owning Bot's lane |
| receipt | Record of one routine run |
| transcript | Canonical per-thread event log with a tail API |
| Foundry output | Roster file: `FOUNDRY_OUTPUT`, or `foundry-output.json`, or sample `foundry-output/aegis.json` |
| Pi | `@earendil-works/pi-coding-agent`. The worker loop |
| vision export | `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/Source-material/Grok-Pi Coding Agent GrokBot Extensions Research-20260919-1439.md` |
| operator prompt | `/Users/dominikbach/olympus/hackmit/hackmit26/Operator-workspace/Prompts/Harness analysis.md` |

A child is not a Bot. A handle is not a receipt. An agent-room agent id is not a Bot slug. `getAgentDir()` is Pi's agent directory (agent-room README names `~/.pi/agent/`).

---

## How this document was made

Opened, in order:

1. Persona, then the operator prompt, then desk `OPERATOR.md`
2. Every `## Prompt:` in the vision export (nine prompts, timestamps below)
3. The six Foundry extensions, `extensions/lib/manifest.ts`, `skills/foundry/SKILL.md`, `SOURCE.md`, `README.md`, `AGENTS.md`, `package.json`
4. Sample Foundry output `foundry-output/aegis.json`
5. Upstream files the wrappers call: agent-room `extensions/agent-room/index.ts` and README, `pi-subagents` RPC and `registerAgent`

`engineers/pike/DRIVE-REPORT.md` did not exist when this file was written. Live TUI drive is unobserved in this window.

`## Response:` blocks in the vision export are not the spec. They are used only to recover a requirement the prompt already stated, or to name a Grok plan the shipped files appear to have followed (or failed to follow).

The 11:52 AM prompt attaches `Harness design.md`. That attachment is not in `Source-material/`. This document does not invent its contents.

---

## Operator prompts that are the spec

Read these in the vision export. The operator ordered emphasis on the prompts.

| Time (vision export) | What the operator required |
| --- | --- |
| 7:08:34 AM | Replicate GrokBot on the operator's Harness through Pi extensions. Research which extension types exist. Build the product OS: named persistent Bots, shared computer, per-Bot memory, account-level tools, routines that run while the user is gone, control plane that can create, search, prompt, and wait. |
| 7:22:24 AM | Replicate GrokBot inter-agent communication. Not a research catalog. A detailed spec to emulate. Out-of-box Pi packages vs write-it. MCP is not assumed. |
| 7:37:34 AM | This is a consulting runtime. Clients get an interface. They do not see the interior. It runs on a server the operator owns or rents (AWS). It powers client AI systems. |
| 7:41:29 AM | UI later. Runtime now. Pi is acceptable as the modular worker if it is that flexible. Do not use Claude Agent SDK. Novel client applications need control the operator owns. |
| 7:52:14 AM | Decompose the whole runtime. For each piece: use existing, choose among options, or write it. Bot identity "will 100% not work" out of the box. OpenMausBot docs are the architecture to emulate through extensions. |
| 11:36:59 AM | Empty. Interrupted. No requirement. |
| 11:52:08 AM | Switch to a coding environment. One-shot build the system as a whole. Reverse engineer GrokBot built on Pi. Substantial effort in the extensions. Isolated extensions were not the whole design. "I just want you to do everything." Attachment `Harness design.md` (not in Source-material). |
| 12:02:49 PM | Almost no effort on UI. All effort on system design and the Harness. TUI in CMUX, or headless for clients. |
| 12:27:57 PM | Publish a GitHub repo the operator can install. Install real Pi. Install existing extensions from GitHub. Do not fake that layer. |

Latest operator intent for this analysis job, from the operator prompt file:

> "I feel like all of them are just kind of bullshit. They don't really function at all, they're very lightweight, and they're just lazy"

> "I need to see if they're able to communicate with each other, where their chat logs go, and how all of that functions."

> "There's a much better way that this can work and should work for clients and the foundry as a whole."

The rest of this file tests those sentences against the TypeScript.

---

## This is not Foundry

Aircraft-strict refuse list. A later engineer must not treat these as implemented.

1. This Harness is not a GrokBot replica.
2. This Harness is not a client runtime on a server.
3. A JSON roster plus a system-prompt paragraph is not a Bot.
4. `bot_send_prompt` is not accept-then-execute.
5. `bot_await_turn` is not await.
6. A `pi-subagents` child is not a Bot.
7. Loading agent-room is not a room host.
8. `/foundry-routine` is not a routine.
9. `ask_user` is not a permission broker.
10. One directory under `getAgentDir()/foundry/memory` is not per-Bot memory.
11. Pi's `read` / `bash` / `edit` / `write` in the current cwd is not a tenant computer.
12. `README.md` and `skills/foundry/SKILL.md` are not the protocol. They describe a protocol the TypeScript does not run.

---

## Harness as a whole

### What the prompts asked for

7:08 AM: replicate GrokBot through extensions. Named persistent Bots. Shared computer. Per-Bot memory. Routines that run while the user is gone. Control plane verbs: create, search, prompt, wait.

7:22 AM: inter-agent protocol with durable Bot identity, handle at accept, await until turn end, user preempt vs peer queue, wake of a sleeping process, group host.

7:37 AM and 7:41 AM: a hidden runtime for client systems on the operator's server. Pi may be the worker. The operator owns roster, lanes, mailboxes, routines, isolation, connectors. Clients do not see Pi.

7:52 AM: write the supervisor, roster, inbox, handles, await, lanes, room host, leases, recent-work brief, approval broker, connector facade, computer lifecycle, routine records, canonical transcript, tenant isolation. Use Pi as the turn engine. Choose among options for memory store, child pack, browser, connectors. Do not install three community packages in place of a "write it" layer.

12:02 PM: put the effort in the Harness, not the UI. Headless must be possible.

12:27 PM: real Pi, real GitHub packages, installable repo.

### What shipped

An installable Pi package. `package.json` name `foundry-harness` version `0.1.0`. Peer on Pi. Dependencies: `pi-subagents` `^0.69.0`, `@narumitw/pi-usage` `^0.60.8`, `pi-agents-talk-to-each-other` git pin `e4f162a`.

Custom TypeScript is seven files:

| File | Lines |
| --- | --- |
| `extensions/lib/manifest.ts` | 71 |
| `extensions/foundry-roster.ts` | 76 |
| `extensions/foundry-comms.ts` | 197 |
| `extensions/foundry-subagents.ts` | 67 |
| `extensions/foundry-memory.ts` | 48 |
| `extensions/foundry-routines.ts` | 47 |
| `extensions/foundry-approvals.ts` | 33 |

About 540 lines. Plus `skills/foundry/SKILL.md` (40 lines) and sample `foundry-output/aegis.json`.

`package.json#pi.extensions` loads those six Foundry files and `./node_modules/@narumitw/pi-usage/dist/index.ts`.

There is no supervisor. There is no tenant boundary. There is no `foundry-computer`. There is no connector facade. There is no transcript tool. There is no test tree. `vendor/` holds `SOURCE.txt` and a license. `vendor/agent-room.ts` is absent. `SOURCE.txt` still says that file is a verbatim copy.

The product the operator runs is the Pi TUI with extra tools and two slash commands: `/foundry-roster` and `/foundry-routine`.

### What is missing, fake, or thin

**The protocol is a prompt.** `protocolBlock()` in `manifest.ts` appends rules to the system prompt on `before_agent_start`. `AGENTS.md` and `SKILL.md` repeat the same rules. No scheduler, no inbox drain, no handle completion, no room host, no approval intercept exists to enforce them.

**The control plane is not a process.** 7:52 AM required a supervisor that owns roster, inbox, handles, group host, routines, approvals, and workers. The Harness is in-process Pi extensions. If the TUI dies, routines die. Sleeping Bots do not start.

**Pi is the product, not the worker.** 7:41 AM allowed Pi as `createAgentSession()` inside the operator's process. The Harness ships `pi install` extensions for the CLI. Clients who must not see Pi still see Pi. Headless is "run `pi` and hope the model calls tools."

**Children are the Bot network.** 7:22 AM and 7:52 AM said do not use `pi-subagents` as named teammates. `foundry-comms.ts` dispatches `bot_send_prompt` through `subagents:rpc:v1:request` method `spawn`. `foundry-subagents.ts` registers each Bot slug as a runtime agent. That is delegation, not a lane.

**Identity is split three ways and never joined.**

1. Foundry output: `bot_atropos` / slug `atropos`
2. `pi-subagents` child name: the slug
3. agent-room agent id: `agent-${hostname}-${process.pid}`

`bot_send_prompt` talks to (2) if RPC answers. Room tools talk to (3) if someone typed `/room connect`. Nothing maps (1) to (3). Manifest `rooms` are a TypeScript type plus sample JSON. No extension reads them except the type.

**Docs describe a Grok plan that is not in the tree.** Grok's 12:02 PM table (vision export) listed `foundry-computer`, "JSONL protocol under `comms/`", "supervisor tests" for accept-before-run, peer queue, user supersede. Those files are not in the Harness. The published package is thinner than that table.

**Install provenance is mixed.** 12:27 PM required real GitHub packages. `SOURCE.md` is honest that Pi is a peer, that `pi-subagents` and agent-room and `pi-usage` are dependencies, and that messenger-swarm is not loaded. That part is real. The Foundry layer on top is still a shim. `README.md` then calls the result a "GrokBot-class floor."

**`pi-usage` is a path into `node_modules`.** If `pi install` copies the package without that tree, the usage overlay does not load. This window did not observe `pi list` or a live install.

### Why it matters for a client Foundry floor

A client floor needs named Bots that keep the job on a machine the client never SSHs into. It needs a handle that means "accepted" and later means "done." It needs logs a human can find. It needs approvals the model cannot talk past. It needs routines that fire when no TUI is open.

This Harness gives a sample JSON of four Greek names, a prompt that tells the model to behave, and tools that write JSON files that never complete. A client system is "a new Foundry manifest" only in `README.md`. The runtime does not consume that manifest as a floor. It prints slugs and hopes.

---

## foundry-roster (`extensions/foundry-roster.ts` + `extensions/lib/manifest.ts`)

### What the prompts asked for

7:08 AM Type A, restated by the operator at 7:52 AM: a Bot is identity + instructions + memory + approved skills + connected tools + computer preference. Durable id. Search by name, description, status (`idle` / `running`). Create when the user asks. Standing purpose. No silent duplicates. Not a Pi session file. Not `~/.pi/agent/agents` markdown.

7:52 AM: **Write it.** `/sessions`, oh-my-pi agent markdown, `agents/*.md` are not a roster.

### What the TypeScript implements

`loadManifest()` reads the first existing path among `FOUNDRY_OUTPUT`, `cwd/foundry-output.json`, `cwd/foundry-output/aegis.json`, package `foundry-output/aegis.json`. JSON parse. No schema check.

`resolveBot()` matches `id`, lowercased `slug`, or lowercased `name`.

`protocolBlock()` builds a markdown roster list and nine protocol bullets. Injected on `before_agent_start`. If `loadManifest()` throws, the hook returns `{}` and the session starts with no roster and no warning.

`bot_search_agents({ query })` substring-filters name, slug, purpose. Returns `id`, `slug`, `name`, `purpose`. No status. No idle/running. Empty query returns every Bot.

`bot_get_profile({ bot_id })` dumps the Bot JSON or `unknown bot`.

`/foundry-roster` calls `ctx.ui.notify` with `system` and a comma-separated slug list.

### What is missing, fake, or thin

1. There is no `bot_create_agent`. There is no `bot_list_agents` with status.
2. There is no durable Bot record beyond the JSON file. No pid. No socket. No last handle. No last status.
3. `skills`, `connectors`, and `approvalLevel` sit on the type and in `aegis.json`. Roster does not enforce them.
4. Manifest `rooms` and `routines` are loaded as JSON. Roster does not use them.
5. Search is a string includes. It is not roster policy (no duplicate purpose, no domain owner).
6. `/foundry-roster` is a notify toast. It is not a floor view.
7. Swallowing `loadManifest()` errors on `before_agent_start` hides a missing Foundry output.

This is a JSON file reader plus a prompt prefix plus two lookup tools. It is honest as a lookup. It pretends to be standing identity.

### Why it matters

Without a Bot that survives process death, every other layer has nothing to address. A client who adds a Bot to Foundry output gets a new slug in a toast. They do not get a worker, a memory tree, a lane, or a status. The model is told "Roster (standing identity; not ~/.pi/agent/agents)" while the only persistence is the same JSON the operator dropped in cwd.

---

## foundry-comms (`extensions/foundry-comms.ts`)

This is the core failure. The operator's 7:22 AM prompt is the spec.

### What the prompts asked for

7:22 AM, operator: replicate GrokBot inter-agent communication. Official product facts the operator wanted emulated (from that prompt's job, not from a Grok essay as law):

- User DM, Bot-to-Bot handoff, group of 2–6
- Handoff is an async wake
- User DMs preempt
- One turn per Bot
- Visibility of handoffs in the transcript

The same prompt asked for a detailed spec and a real emulation path. The behavioral spec that prompt was driving toward, as the operator's required verbs from 7:08 AM:

```text
bot_search_agents(query, status?)
bot_send_prompt(agent_id, prompt, mode=async, on_busy=queue, paths?)
bot_await_turn(agent_id, handle)
bot_get_agent_transcript_tail(agent_id, limit, before_seq?)
```

Accept is durable before the receiver runs. Acknowledgement is not done. Default Bot-to-Bot: queue. Default user-to-Bot: supersede. If the Bot is not running, the handle still accepts and a supervisor starts the process.

7:52 AM 4a: **Write it.** Existing Pi buses move text between live processes. They do not give durable BotId, accept≠complete handle, wake a sleeping worker, user-preempt vs peer-queue, group host.

7:52 AM 4c: agent-room and messenger-swarm may be the append-only group log. They are not the host.

Operator prompt: see if Bots communicate, where chat logs go, how that functions.

### What the TypeScript implements

On load, `foundry-comms` resolves agent-room from `pi-agents-talk-to-each-other/extensions/agent-room/index.ts`, else `vendor/agent-room.ts` (missing). It `await`s that default export. That registers `/room` and `room_*` tools on this Pi process. Foundry does not call `/room connect`. Foundry does not pass Foundry output rooms into agent-room.

`bot_send_prompt({ bot_id, prompt })`:

1. Resolves the Bot from Foundry output.
2. Builds a handle: `id = h_` + first 8 chars of a UUID, `from: "peer"`, `status: "accepted"`.
3. Writes `getAgentDir()/foundry/handles/{id}.json`.
4. Emits `subagents:rpc:v1:request` method `spawn` with `{ agent: slug, task: prompt, async: true, context: "fresh" }`.
5. Waits up to 4000 ms for `subagents:rpc:v1:reply:{requestId}`.
6. If the reply succeeds: `status = "running"`, stores `runId`, note about RPC spawn.
7. If the reply fails or times out: `status = "queued"`, note tells the model to call `subagent({ agent: "<slug>" })` or `room_send_message`.
8. Returns JSON `{ accepted: true, handle_id, bot, bot_id, slug, status, run_id, note }`.

`bot_await_turn({ handle_id })` reads that JSON. Sets `done` if status is `completed`, `failed`, or `cancelled`. Returns the object. It does not wait. It does not watch a socket. It does not subscribe to `subagent:async-complete`.

No other writer of handle JSON exists in `extensions/`.

### What is missing, fake, or thin

**Nothing completes a handle.** `HandleStatus` includes `completed | failed | cancelled`. Grep of `extensions/` shows those strings only in the type, in `protocolBlock()`, and in `bot_await_turn`'s `done` check. No `writeHandle` after spawn sets them. A successful send stays `running` forever. A failed RPC stays `queued` forever. `bot_await_turn` will never return `done: true` unless a human edits the JSON.

**`bot_await_turn` is a file read.** The name says await. The body is `readHandle`. The model must poll. Polling a status that cannot change is a dead loop.

**Accept is not the protocol accept.** The file is written before spawn. That is the one honest moment. Then the function tries to run the work in the same tool call (RPC spawn, 4 s). If spawn works, the handle is already `running` when the tool returns, so "accepted immediately" is already overwritten. If spawn fails, the handle is `queued` with no inbox drain.

**The fallback is an instruction to the model.** Queued note:

```text
Handle accepted. Dispatch via subagent({ agent: "${bot.slug}" }) or room_send_message.
```

The control plane is "please do it yourself." If the model then calls `room_send_message`, the target is an agent-room agent id, not `clio`. If the model calls `subagent`, that is a new child, unbound to the handle file.

**User supersede is a comment.** File header: "user supersede, peer queue." `from` is always `"peer"`. There is no user_dm path. There is no abort of a running child on operator DM. There is no per-Bot inbox. There is no busy check. Tool text says "busy targets are queued." The code does not inspect busy state. RPC spawn either starts a child or it does not.

**Parameters the spec named are absent.** No `mode`. No `on_busy`. No `paths`. No files. No conversation id. No seq.

**`bot_get_agent_transcript_tail` does not exist.**

**agent-room is loaded, not bound.** Upstream is a real live-process bus: file rooms under `getAgentDir()/rooms/`, heartbeats, follow-up if busy, `room_send_message`. Foundry never connects, never creates the sample room `Floor`, never wakes members in order, never parks on a busy member. Manifest rooms stay unused.

**RPC is in-process.** `pi-subagents` docs: `pi.events` does not reach separate Pi processes. Spawn, when it works, starts a child inside this TUI session. That is not a peer Bot on a lane. It is a subagent. 7:22 AM: do not leak child ids as Bot ids. The handle stores `runId` from that child.

**Handle id is weak.** Eight hex characters. Not a durable ledger. Writes are not atomic (agent-room's own helper is `writeJsonAtomic`. Foundry uses `writeFileSync`).

**Load order.** `package.json` lists `foundry-comms.ts` before `foundry-subagents.ts`. `spawnViaSubagents` does not wait for `subagents:rpc:v1:ready`. If RPC is late, every send queues.

### Why it matters

This is the test the operator named: can Bots communicate, where do chat logs go, does the protocol function.

As written:

- Communication is either a child spawn inside one Pi session, or a hope that the model will call a different tool.
- The handle cannot finish. A Chief of Staff Bot that obeys `SKILL.md` ("Do not tell the operator a teammate finished unless `bot_await_turn` says `done: true`") waits forever.
- Chat logs are not a Foundry transcript. See the Communication and chat logs section.
- A client floor cannot hand work Atropos → Clio → Hephaestus as named teammates. It can spawn children named after those slugs, if RPC is up, and then lose the result off the handle.

Grok's 12:02 PM summary said foundry-comms is "Peer send + room host. JSONL protocol under `comms/`." There is no `comms/` JSONL in this package. There is no room host in this file. That summary is a claim the code cannot keep.

---

## foundry-subagents (`extensions/foundry-subagents.ts`)

### What the prompts asked for

7:08 AM Type D and 7:52 AM 4b: children are for bounded work ("go research this and return"). Do not treat a child as a Bot. Bots are long-lived named peers with memory and routines.

7:41 AM: load **your** extensions only. Do not leak the CLI ecosystem into a billed runtime.

7:52 AM: **Choose among options** for the child pack (`pi-subagents` vs official example). **Write** the Bot network separately.

### What the TypeScript implements

On load and on `session_start`, writes `cwd/.pi/settings.json`:

- `subagents.disableBuiltins = true`
- `subagents.agentScanDirs = []`
- `subagents.agentExcludeDirs` = home `~/.pi/agent/agents`, `~/.agents`, project `.pi/agents`, `.agents`, `agents`

Then `registerSubagents(pi)`.

On `session_start`, for each Foundry Bot, `registerAgent({ name: bot.slug, definition: { description: purpose, systemPrompt: instructions, systemPromptMode: "replace", inheritProjectContext: true, inheritGlobalContext: false, inheritSkills: true, skills: bot.skills } })`.

### What is missing, fake, or thin

**The choose-among-options layer was used as the write-it layer.** Binding slugs to `registerAgent` is a real `pi-subagents` call. Using those slugs as the floor is the wrong abstraction. 7:22 AM: never as the Bot network.

**Settings mutation is a side effect.** The extension writes project `.pi/settings.json` in `process.cwd()` at import time. A client repo gets Foundry policy as a silent file write.

**Skills on the sample Bots do not exist as Pi skills.** `aegis.json` lists `routing`, `briefing`, `ops`, `computer`. The package ships one skill: `skills/foundry/SKILL.md`. `inheritSkills: true` plus missing skill names is a no-op or a miss, not a Bot tool allowlist.

**No per-Bot cwd, computer, or memory path.** `inheritProjectContext: true` shares the operator project with every child.

**Registration is `session_start` only.** If `loadManifest()` throws here, the handler throws. Roster's matching hook swallows the same error. One path hides the miss. The other crashes the start.

**This is a thin config wrapper.** 67 lines. The comment says "CHOOSE (nicobailon/pi-subagents)" and then "children are roster bots, not Pi sessions." That sentence is the design error. Children are still children. They die. They do not own routines. They do not own a lane.

### Why it matters

A client who thinks Atropos is a standing Chief of Staff gets a subagent template. Builtins are off, which is correct. Filesystem markdown agents are excluded, which is correct. The roster is still not a floor. It is a set of child names.

---

## foundry-memory (`extensions/foundry-memory.ts`)

### What the prompts asked for

7:08 AM Type C: memory belongs to the Bot. Shared files are not memory. Compaction must not wipe identity.

7:52 AM: copy OpenMausBot invariants. Per Bot, never a shared brain. `MEMORY.md` prefix loaded every turn (cap). Topic files on demand. Daily log not stuffed into the prompt. Secret redaction. Atomic writes. Recent-work brief from other conversations. `session_search`. **Choose among options** for the store. The invariants are write-it either way. Recent-work brief is write-it.

### What the TypeScript implements

Directory: `getAgentDir()/foundry/memory` (one tree for the whole Pi user).

`memory_read({ path })` joins that directory with `path` after stripping `..`. Missing file returns `(empty)`.

`memory_write({ path, content })` writes `redact(content)`. Redact is one regex for `api_key` / `password` / `secret` / `token` / `sk-...`.

No `before_agent_start` injection. No cap. No per-Bot subdirectory. No daily log. No atomic rename. No `session_search`. No recent-work brief.

### What is missing, fake, or thin

1. This is a shared brain. Opposite of the invariant "per Bot, never a shared brain."
2. Identity is not injected. Compaction can wipe the Bot because the Bot never had memory in the prompt unless the model called `memory_read`.
3. Absolute `path` values can escape. `path.join(memDir, "/etc/passwd")` on POSIX yields `/etc/passwd`. Stripping `..` does not stop that.
4. Redaction is a regex. It is not a secret scanner.
5. Writes are not atomic. 7:52 AM called out temp→rename as required before concurrent turns.
6. No hermes-memory, no FTS, no topic convention. The "choose among options" step was skipped. A 48-line pair of tools was written instead.

Honest and small: two tools that read and write files, with a weak redact. That is all it is. It is not Bot memory.

### Why it matters

Clio's research and Hephaestus's computer notes land in the same folder. The next Bot can read them. A second client on the same Unix user shares `getAgentDir()`. 7:37 AM: sharing a disk across consulting clients is a data-leak product. This memory plane is that leak, even for Bots inside one tenant.

---

## foundry-routines (`extensions/foundry-routines.ts`)

### What the prompts asked for

7:08 AM Type F: routines are what make Bots coworkers. In-session loops are not enough. GrokBot routines fire when no TUI is open. Persist prompt, cadence or event, last_run, last_result. Supervisor starts `pi --mode rpc` or pokes a live socket.

7:52 AM section 10: schedule or webhook → same queued executor → owning Bot's current model/tools/computer → fresh context → report on a chosen thread. Receipts: queued, active, waiting, completed, missed, failed, cancelled. Catch-up policy. **Write it.** Out-of-box `/loop` will double-fire and die with the process. OS cron/`pi-tick` is only the wake clock.

12:02 PM: standing checks as wakes on the owner's lane, with receipts.

### What the TypeScript implements

`routine_list` returns `manifest.routines ?? []` as JSON. Sample has one row: name `Morning floor brief`, bot `hermes`, cadence `daily`, a prompt string.

`/foundry-routine [name]` finds a row by name or bot. Writes `getAgentDir()/foundry/receipts/{Date.now()}.json` with `{ name, bot, status: "queued", at }`. Then:

```ts
ctx.sendUserMessage(`[routine:${r.bot}] ${r.prompt}`, { deliverAs: "followUp" })
```

That injects the prompt into the **current** Pi session as a follow-up.

`cadence` is never parsed. No cron. No launchd. No systemd. No webhook. No destination thread. No catch-up. No missed. The receipt stays `queued`.

### What is missing, fake, or thin

**This is `/loop` with a JSON souvenir.** The skill says "It is not `/loop`." The handler is follow-up into the open session. That is `/loop`.

**It does not wake Hermes.** The sample owner is `hermes`. The message is prefixed `[routine:hermes]` and given to whoever is at the keyboard. If that is Atropos or the operator's Pi, Hermes's lane is not involved.

**A receipt that never leaves `queued` is a fake receipt.** 7:52 AM named the receipt states. Only `queued` is written.

**No unattended run.** Close the TUI. The morning brief does not fire. 7:08 AM called that the actual GrokBot requirement.

47 lines. Slash command plus list tool. Pretends to be standing duty.

### Why it matters

A client who buys "ops watches the floor every morning" gets a command the operator must type. Hermes does not run it. No receipt proves it ran. Foundry output `cadence: "daily"` is decoration.

---

## foundry-approvals (`extensions/foundry-approvals.ts`)

### What the prompts asked for

7:08 AM Type J: fail closed on send-as-user, pay, merge, deploy. Policy that tags tools `read` / `write-local` / `side-effect-external`. Block the last class until the user confirms.

7:52 AM section 7: agents request, a broker turns that into Allow / Deny / answer. A peer message is not user approval. Waiting-on-you still holds the lane. Wire official permission-gate / protected-paths / questionnaire so a deny becomes `handle = blocked`, not a swallowed tool error. **Write it** (policy + broker). Use existing for cheap gates inside the worker.

### What the TypeScript implements

One tool `ask_user({ action, detail })`. Calls `ctx.ui.confirm("Foundry approval", action + detail)`. Returns `{ allowed, action, detail }`.

`promptGuidelines` tell the model to call it before consequential actions, and that a handle is not approval.

`approvalLevel` on the Bot record is unused.

No intercept of `bash`, `write`, `edit`, or room send. No permission-gate. No protected-paths. No handle status `blocked`. No lane occupancy.

### What is missing, fake, or thin

**This is a yes/no dialog the model may skip.** Fail-closed means the dangerous tool does not run without a ticket. Here the dangerous tools are Pi defaults. They run. `ask_user` runs only if the model chooses it.

**Peer handoff is not blocked from counting as approval.** The guideline is text. There is no broker.

**Confirm does not occupy the lane.** 7:52 AM: a turn parked on an approval card still occupies the lane. This tool returns. The turn continues.

33 lines. Honest as a confirm wrapper. Fake as Foundry approvals.

### Why it matters

Hephaestus's instructions say consequential writes must ask the operator. Nothing stops Hephaestus, or a child named `hephaestus`, from `bash rm -rf`. A client floor that can publish or send-as-user without a broker is not safe to hide behind a clean UI (7:37 AM).

---

## Missing extensions the prompts required

These are not lazy files. They are absent.

| Layer (7:52 AM decomposition) | Avenue the prompt set | In the Harness |
| --- | --- | --- |
| Supervisor / process topology | Write it | Absent |
| Inbox, lanes, user-preempt vs peer-queue | Write it | Comments and prompt bullets only |
| Room host + goal parking | Write it | agent-room loaded, host not written |
| Working-folder / computer / memory leases | Write it | Absent. Grok 12:02 listed `foundry-computer`. No file |
| Recent-work brief | Write it | Absent |
| Connector facade `search_connected_tools` / `call_connected_tool` | Write it | `connectors` field on Bots is unused |
| Computer lifecycle per tenant | Write it | Absent |
| Canonical event log + `bot_get_agent_transcript_tail` | Write it | Absent |
| Tenant isolation | Write it | Absent |
| Teach-to-skill | Write it, later | Absent (allowed later) |
| Browser / screen lock | Choose among options | Absent |
| Out-of-session wake clock (`pi-tick` / systemd) | Use existing | Absent |

7:52 AM: "If a layer is in write it, installing three community packages for it will give you live-process chat and none of the invariants." That is what shipped: three packages (`pi-subagents`, agent-room, `pi-usage`) plus prompt invariants.

---

## Communication and chat logs

The operator asked to see whether Bots communicate and where chat logs go. Live drive was pike's job. `engineers/pike/DRIVE-REPORT.md` was not on disk. This section is TypeScript-only. Live paths were not observed in this window.

### What the TypeScript says should happen

**Foundry handle files.** `bot_send_prompt` writes `getAgentDir()/foundry/handles/{handle.id}.json`. Fields: `id`, `bot` (slug), `from` (always `"peer"`), `prompt`, `status`, `createdAt`, optional `runId`, `result`, `note`. `bot_await_turn` reads that file. Nothing else updates it. These files are not a chat log. They are stuck status objects.

**Routine receipts.** `/foundry-routine` writes `getAgentDir()/foundry/receipts/{timestamp}.json` with `status: "queued"`. Not a conversation.

**Memory files.** `getAgentDir()/foundry/memory/{path}`. Shared. Not a transcript.

**agent-room logs, if a human connects.** Upstream writes under `getAgentDir()/rooms/`: per-room `agents/`, `inbox/{agent-id}/`, JSONL-style message appends (`appendJsonLine`). Agent ids are `agent-${hostname}-${process.pid}`. Foundry does not auto-connect. Foundry does not create room `Floor` from `aegis.json`. If nobody runs `/room connect`, this tree may not exist.

**Pi session files.** Pi stores sessions under its own session directory (agent-room README and Pi docs: under the agent dir). Foundry does not index them. Foundry does not page them. There is no `bot_get_agent_transcript_tail`.

**Child artifacts.** If RPC `spawn` works, `pi-subagents` owns async run status and its own artifacts. Foundry stores `runId` on the handle and never reads the child transcript back onto the handle as `result`.

**Handoff mirroring.** 7:22 AM required the exchange visible on sender transcript and receiver transcript. Foundry does not append a handoff entry to any Bot transcript. The only "log" of a send is the handle JSON and whatever the current model wrote in the current session.

### What a later engineer should look for on a live drive

Unobserved here. If pike later writes `DRIVE-REPORT.md`, fold these checks:

1. After `bot_send_prompt`, open the handle JSON. See whether `status` ever leaves `running` or `queued`.
2. After `bot_await_turn`, see whether `done` is ever true without hand-editing the file.
3. List `getAgentDir()/rooms/`. See whether Foundry created a room or only Pi sessions that someone connected by hand.
4. List Pi session files. See whether Clio has a session, or only the operator TUI plus child runs.
5. Search for `Floor` on disk. The sample room title should appear if a host exists. The TypeScript never writes that string except inside `aegis.json`.

### Why the log gap matters

A client cannot be shown "the Bots talked." There is no Foundry transcript to sanitize into an action log (7:37 AM). There is no handle history to bill or debug (7:37 AM list: replay, idempotency, which receipt is missing). The operator's test — where do chat logs go — has this answer from static code: scattered Pi files, optional agent-room files if a human connected, and handle JSON that does not complete. There is no one place.

---

## Claims the docs cannot keep

Leave these strings in the repo only if the runtime is rewritten. Until then they are false.

From `README.md`:

- "turns Pi into a GrokBot-class floor"
- "handles that accept before they run, rooms, memory, routines, and operator approvals" as a list of things "you get"
- Handle protocol "on top of agent-room" — the handle tools do not call agent-room
- `/foundry-routine [name]` "fire a standing wake onto the owning bot's lane"

From `SOURCE.md`:

- "`bot_send_prompt` accepts before run, `bot_await_turn`, ack ≠ complete"
- "Dispatch of accepted work goes through pi-subagents RPC `spawn` when that bus is up, otherwise the model is told to use the real `subagent` / `room_send_message` tools" — the second half admits the fallback is a model instruction. That is not a control plane.
- `vendor/agent-room.ts` "is a verbatim copy" — the file is not there

From `AGENTS.md` and `skills/foundry/SKILL.md`:

- "The JSON you get back is a handle, not a result" — true as a return shape, false as a lifecycle
- "Do not tell the operator a teammate finished unless `bot_await_turn` says `done: true`" — `done` never becomes true
- "User DMs outrank peer wakes. Peer mail queues when the target is busy." — no code
- "Rooms: the host wakes members in order. Never skip a busy member." — no host
- "Standing checks are Foundry routines, not `/loop`." — the command is `/loop` behavior
- "Room presence, inbox, and `room_send_message` come from Timur00Kh `agent-room` (vendored)." — loaded from `node_modules` if install worked, not vendored as `vendor/agent-room.ts`, and not bound to Foundry rooms

From `protocolBlock()` injected into every turn:

- The nine bullets are rules for the model. They are not rules the process implements.

From `package.json` description:

- "GrokBot-class control plane as a Pi package"

From Grok 12:02 PM in the vision export (plan the coding pass claimed):

- `foundry-computer` tenant FS + allowlisted bash + lease
- JSONL protocol under `comms/`
- Supervisor tests for accept-before-run, peer queue, user supersede, complete → idle

Those are not in the Harness tree this window opened.

---

## What is honest and small

Say this so a later pass does not rip out the few true seams.

1. `loadManifest()` path search is a real, small loader. `FOUNDRY_OUTPUT` override is real.
2. `resolveBot()` id/slug/name match is real.
3. Disabling `pi-subagents` builtins and excluding markdown agent dirs is a real settings write. Correct direction. Not sufficient.
4. `registerAgent()` for each slug is a real upstream call. Wrong abstraction for Bots. Real glue for children.
5. agent-room default export is actually invoked. The upstream room bus is real. Foundry does not use it as a host.
6. `pi-usage` is listed as a real package, not rewritten. Fragile path.
7. `ask_user` really calls `ctx.ui.confirm`. Small and honest. Not a broker.
8. `SOURCE.md` is right that this package does not reimplement Pi, and that messenger-swarm is not included.
9. Sample `aegis.json` is a clear four-Bot fixture. The names and purposes are usable as test data once a real floor exists.
10. The 12:27 PM demand to depend on real GitHub packages, not a fake Pi SPI, is partly met at the npm layer. The fake SPI was the earlier browser demo Grok admitted. The remaining fake is the Foundry protocol.

---

## Why the operator's "lightweight / lazy / non-functional" read is correct

Not insults. Mapping:

**Lightweight.** Seven custom files, ~540 lines, two slash commands, prompt-as-protocol. The 7:52 AM write-it list is a control plane. This is a package manifest around three npm dependencies.

**Lazy.** Wrong abstraction on purpose of convenience: children as Bots, `/loop` as routines, confirm dialog as approvals, shared folder as memory, load agent-room and do not host, write a handle and do not complete it, tell the model to call another tool when RPC misses. Each is the shortest path that still lets `README.md` name the noun.

**Non-functional (from static code).** Handle completion has no writer. Room host has no code. Routine cadence has no clock. Approval has no intercept. Memory has no injection and no Bot scope. Transcript tail does not exist. Tenant computer does not exist. Live function was not observed. The TypeScript already shows the happy path cannot fulfill `bot_await_turn`.

**Underperforming for clients.** 7:37 AM sold named workers on a machine the client never sees. This Harness is a developer TUI plugin. A second Foundry output JSON does not create a second tenant.

**Underperforming for Foundry.** Foundry output is treated as a prompt and a child template, not as architecture the runtime instantiates. Rooms and routines in that JSON are almost dead fields.

---

## Sources opened

Vision prompts (authority):

- `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/Source-material/Grok-Pi Coding Agent GrokBot Extensions Research-20260919-1439.md` — all nine `## Prompt:` sections
- `/Users/dominikbach/olympus/hackmit/hackmit26/Operator-workspace/Prompts/Harness analysis.md`

Harness TypeScript and docs:

- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/lib/manifest.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-roster.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-comms.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-subagents.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-memory.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-routines.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/extensions/foundry-approvals.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/skills/foundry/SKILL.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/SOURCE.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/README.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/AGENTS.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/package.json`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/foundry-output/aegis.json`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/vendor/SOURCE.txt`

Upstream (to verify wrappers, not as spec):

- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/node_modules/pi-agents-talk-to-each-other/extensions/agent-room/index.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/node_modules/pi-agents-talk-to-each-other/README.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/node_modules/pi-subagents/src/extension/rpc.ts`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/node_modules/pi-subagents/docs/extension-api.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/Harness/node_modules/pi-subagents/src/agents/runtime-agent-registry.ts`

Not opened: `engineers/flint/`. Not opened: `Harness design.md` (missing from Source-material). Not observed: live Pi TUI.

---

## For the next engineer

Do not start from the README noun list. Start from the 7:52 AM prompt in the vision export and from the refuse list in this file.

Do not treat a passing `/foundry-roster` toast as a floor.

Do not add more prompt bullets to `protocolBlock()` and call that a fix.

If you implement one seam first, implement handle completion bound to a real turn end, with a transcript tail. Without that, communication cannot be shown to the operator.

This document does not pick the architecture to ship. The gap that must not be renamed: the Harness still needs a control plane. Extensions that wrap npm packages are not that plane.
