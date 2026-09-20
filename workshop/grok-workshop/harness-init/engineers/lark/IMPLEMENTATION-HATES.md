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
| pike report | `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/engineers/pike/DRIVE-REPORT.md` |
| host Pi | pike live TUI `workspace:40` / `surface:41`, agent-room agent id `agent-dhcp-10-31-159-94.dyn.mit.edu-34530` |
| peer Pi | pike live TUI `workspace:41` / `surface:42`, agent-room agent id `agent-dhcp-10-31-159-94.dyn.mit.edu-37318` |
| pike-floor | agent-room bus pike created. Not the sample room `Floor` in `aegis.json` |
| session jsonl | Pi chat log under `~/.pi/agent/sessions/--Users-dominikbach-olympus-hackmit-hackmit26-Harness--/` |
| room events.jsonl | agent-room bus log `~/.pi/agent/rooms/<room>/events.jsonl` |

A child is not a Bot. A handle is not a receipt. An agent-room agent id is not a Bot slug. `getAgentDir()` is Pi's agent directory (live: `/Users/dominikbach/.pi/agent`). Host Pi and peer Pi are two live Pi processes. They are not Atropos and Clio.

---

## How this document was made

Opened, in order:

1. Persona, then the operator prompt, then desk `OPERATOR.md`
2. Every `## Prompt:` in the vision export (nine prompts, timestamps below)
3. The six Foundry extensions, `extensions/lib/manifest.ts`, `skills/foundry/SKILL.md`, `SOURCE.md`, `README.md`, `AGENTS.md`, `package.json`
4. Sample Foundry output `foundry-output/aegis.json`
5. Upstream files the wrappers call: agent-room `extensions/agent-room/index.ts` and README, `pi-subagents` RPC and `registerAgent`
6. Resume: pike report, pike `STOP.md`, then disk paths pike named (handles, receipts, memory, pike-floor events, settings, session jsonl, hephaestus output)

This file now has three layers: vision prompts, TypeScript, live drive. Pane and disk win when they contradict a TypeScript claim. Live no-op does not erase a TypeScript defect.

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

The rest of this file tests those sentences against the TypeScript and against pike's live drive.

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
13. Two live Pi TUIs on `pike-floor` are not Foundry Bots. Their ids are hostname-plus-pid.
14. `/foundry-routine` on Pi 0.85.1 is not a wake. It writes a queued receipt, then throws.

---

## Live vs TypeScript vs vision

Pike drove two Pi TUIs in Harness cwd. Report: `engineers/pike/DRIVE-REPORT.md`. This window re-opened the disk paths below. It did not re-drive Pi.

Live environment pike recorded:

- `pi --version` → `0.85.1`
- `pi list` → `User packages: /Users/dominikbach/olympus/hackmit/hackmit26/Harness`
- Default model `openai-codex` / `gpt-5.4-mini` failed: `The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.`
- Session model `xai` / `grok-4.6` completed turns (`PINGOK`)
- Boot loaded all six Foundry files plus `dist` (`pi-usage`)

### Operator test: did they communicate

| Kind | Live result | That is Foundry? |
| --- | --- | --- |
| agent-room Pi-to-Pi | Yes. Host queued `msg-1789845379482-c8abb38ee911`. Peer replied `PEER-PONG`. Host received `[Agent room message]`. Disk `events.jsonl` has `join` ×2, `enqueue`+`deliver` both ways. | No. Ids are `agent-dhcp-10-31-159-94.dyn.mit.edu-34530` and `...-37318`, not `atropos` / `clio`. Room name is `pike-floor`, not sample `Floor`. |
| parent to child | Yes. `/run clio`, `/run hermes`, `subagent` `hephaestus` completed. Hephaestus output file is `HEPHAESTUS-OK.` | No. These are children. Not Bot lanes. |
| handle protocol | No. No `~/.pi/agent/foundry/handles` directory. Host session jsonl has no `toolName` `bot_send_prompt`, `bot_search_agents`, or `bot_await_turn`. | The Foundry send/await path did not run. |

Grok 4.6 printed `{"error":"Tool bot_send_prompt is not enabled"}`. Pike: that line is model speech, not a Pi `toolResult`. Print-mode also returned `toolResults: []` for `bot_search_agents` and `bot_send_prompt` after a real `bot_get_profile` call. Do not treat "not enabled" as a Foundry runtime error. Treat it as: the handle tools were not invoked live. TypeScript still has no writer for `completed|failed|cancelled`.

### Operator test: where chat logs go

Live paths (this window confirmed the files exist, except handles):

| Log | Path | Role |
| --- | --- | --- |
| Host session jsonl | `/Users/dominikbach/.pi/agent/sessions/--Users-dominikbach-olympus-hackmit-hackmit26-Harness--/2026-09-19T19-08-52-290Z_01a0bb12-46c1-7612-97ba-c8325878a3dd.jsonl` | Pi chat for host Pi. Room injects `[Agent room message]` as a user message. |
| Peer session jsonl | `.../2026-09-19T19-13-48-069Z_01a0bb16-ca25-72a9-92a9-d18c3d0b547c.jsonl` | Pi chat for peer Pi. |
| pike-floor bus | `/Users/dominikbach/.pi/agent/rooms/pike-floor/events.jsonl` | join / enqueue / deliver / leave. This is the Pi-to-Pi log. |
| Child sessions | under the host session dir, `4dd68ab6-.../run-0/session.jsonl` (clio) and `4664a23b-.../run-0/session.jsonl` (hermes) | Parent-child transcripts. |
| Subagent artifacts | `.../subagent-artifacts/` `*_clio_output.md`, `*_hermes_output.md`, `*_hephaestus_output.md` | Child result files. |
| Memory | `/Users/dominikbach/.pi/agent/foundry/memory/` | Shared files `clio-peer.md`, `pike-drive.md`, `secret-test.md`. Not a transcript. |
| Receipts | `/Users/dominikbach/.pi/agent/foundry/receipts/1789845000302.json` | Still `"status": "queued"`. Not a conversation. |
| Handles | `/Users/dominikbach/.pi/agent/foundry/handles` | Missing. Never created this drive. |

There is no Foundry transcript. There is no `Floor` room on disk. `~/.pi/agent/rooms/` has `pike-floor`, `default`, and `control`.

### Live verdict per Foundry extension

Aircraft-strict. Pane and disk.

1. `foundry-roster`: `/foundry-roster` printed `Aegis: atropos, clio, hermes, hephaestus`. `bot_get_profile` returned JSON for hermes, clio, atropos. Slash `/create` and `/register` do not exist. `bot_search_agents` never appeared as a `toolResult`.
2. `foundry-comms` handle layer: no-op this drive. No handle file. No `bot_send_prompt` toolResult. TypeScript still cannot complete a handle.
3. `foundry-comms` agent-room load: works as a live-process bus after a human `/room` create/connect. Not a Foundry host.
4. `foundry-subagents`: overlay listed four `[runtime]` slugs. `/run clio`, `/run hermes`, `subagent` hephaestus completed. `/subagents-doctor` still said `builtin 13`. Overlay and doctor disagree.
5. `foundry-memory`: write/read worked. Secrets redacted on disk. One shared folder. Host and peer both wrote there.
6. `foundry-routines`: `routine_list` returned Morning floor brief. `/foundry-routine` wrote the receipt, then `Extension "command:foundry-routine" error: ctx.sendUserMessage is not a function`. Bogus name warned `No matching routine.`
7. `foundry-approvals`: overlay `Foundry approval` / Yes-No. Result `{"allowed":true,...}`. No extra file. Model must call the tool.
8. `@narumitw/pi-usage`: `/usage` showed xAI SuperGrokPro weekly allowance. Loaded as `dist` at boot.

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

The product the operator runs is the Pi TUI with extra tools and two slash commands: `/foundry-roster` and `/foundry-routine`. Pike live: those two commands exist. A third Foundry slash does not. `/foundry-routine` throws on Pi 0.85.1.

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

Live confirms the split. Pike created `pike-floor` by hand. Host id `...-34530`. Peer id `...-37318`. Overlay listed slugs `atropos`, `clio`, `hermes`, `hephaestus`. Room messages used the pid ids. Sample room title `Floor` is not on disk.

**Docs describe a Grok plan that is not in the tree.** Grok's 12:02 PM table (vision export) listed `foundry-computer`, "JSONL protocol under `comms/`", "supervisor tests" for accept-before-run, peer queue, user supersede. Those files are not in the Harness. The published package is thinner than that table.

**Install provenance is mixed.** 12:27 PM required real GitHub packages. `SOURCE.md` is honest that Pi is a peer, that `pi-subagents` and agent-room and `pi-usage` are dependencies, and that messenger-swarm is not loaded. That part is real. The Foundry layer on top is still a shim. `README.md` then calls the result a "GrokBot-class floor."

**`pi-usage` is a path into `node_modules`.** If `pi install` copies the package without that tree, the usage overlay does not load. Pike live: `pi list` showed the Harness path. Boot listed `dist`. `/usage` showed xAI SuperGrokPro. The overlay loaded on this machine. The path is still fragile for a clean `pi install git:...` without `node_modules`.

### Why it matters for a client Foundry floor

A client floor needs named Bots that keep the job on a machine the client never SSHs into. It needs a handle that means "accepted" and later means "done." It needs logs a human can find. It needs approvals the model cannot talk past. It needs routines that fire when no TUI is open.

This Harness gives a sample JSON of four Greek names, a prompt that tells the model to behave, and tools that write JSON files that never complete. A client system is "a new Foundry manifest" only in `README.md`. The runtime does not consume that manifest as a floor. It prints slugs and hopes.

Live: two humans opened two Pi TUIs, created a room by hand, and spawned children by slug. That is not a client floor. Default Codex model failed until pike switched to `xai/grok-4.6`. Clients who "do not see Pi" still see Pi, model errors, `/room` overlays, and `/subagents`.

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

### Live (pike)

`/foundry-roster` printed:

```
 Aegis: atropos, clio, hermes, hephaestus
```

`bot_get_profile` returned full JSON for hermes, clio, and atropos (`isError: false` in print-mode for atropos).

Slash filter `/foundry` showed only `foundry-roster`, `foundry-routine`, `skill:foundry`. `/create`: no matching command. `/register`: no matching command. Enter sent `/register` as a user prompt.

`bot_search_agents` never appears as a `toolResult` in the host session jsonl. Print-mode: after `bot_get_profile`, the model emitted text "not enabled" with `toolResults: []`. Unproven as a live tool call. The TypeScript tool exists.

Pike: protocol block string is not stored in session jsonl. Child clio still answered as Clio from `registerAgent` instructions. `before_agent_start` inject is unproven in the jsonl.

### Why it matters

Without a Bot that survives process death, every other layer has nothing to address. A client who adds a Bot to Foundry output gets a new slug in a toast. They do not get a worker, a memory tree, a lane, or a status. Live: there is no TUI to add a fifth Bot. Roster identity is the JSON file. `/run` and `subagent` spawn only slugs that already exist.

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

### Live (pike)

Handle layer: no-op this drive.

1. Directory `/Users/dominikbach/.pi/agent/foundry/handles` does not exist. This window confirmed `ls`: no such file or directory.
2. Host session jsonl `toolName` set has `ask_user`, `bash`, `bot_get_profile`, `memory_read`, `memory_write`, `read`, `room_list_agents`, `room_send_message`, `room_whoami`, `routine_list`, `subagent`. It does not have `bot_send_prompt`, `bot_search_agents`, or `bot_await_turn`.
3. Host recap (model speech, not a toolResult): `9. bot_send_prompt clio` then `{"error":"Tool bot_send_prompt is not enabled"}`.
4. Print-mode: real `bot_get_profile` for atropos. Next turn text claims `bot_search_agents` / `bot_send_prompt` not enabled. `toolResults: []`.
5. Pike did not prove `bot_send_prompt` `execute()` runs in-process. TypeScript still never writes `completed|failed|cancelled`. Even a live handle would stay `accepted|queued|running`.

agent-room load: works.

Boot loaded `foundry-comms.ts`. `/room` overlay existed. Pike created `pike-floor`. Connect:

```
 Connected to room 'pike-floor' as agent-dhcp-10-31-159-94.dyn.mit.edu-34530
```

`/room control on` enabled `room_control_agent`. Footer `room:pike-floor [control]`. Host `room_send_message` queued `msg-1789845379482-c8abb38ee911` (delivery followUp). Peer pane:

```
 [Agent room message]
 Room: pike-floor
 From: agent-dhcp-10-31-159-94.dyn.mit.edu-34530
 Message ID: msg-1789845379482-c8abb38ee911
 Pike host ping. Reply with room_send_message containing PEER-PONG and your agent id.
```

Peer replied `PEER-PONG`. Host received the reply as `[Agent room message]`. Disk `events.jsonl` matches both message ids. Foundry did not auto-connect. Foundry did not host `Floor`. Pike did not call `room_control_agent`, `room_read_agent_history`, or `room_summarize_agent`.

### Why it matters

This is the test the operator named: can Bots communicate, where do chat logs go, does the protocol function.

Live answer:

- Pi-to-Pi chat works if a human creates a room and uses pid ids.
- Parent-to-child spawn works by slug.
- The Foundry handle protocol did not run. There is no handle file to await.
- A Chief of Staff that obeys `SKILL.md` still cannot get `done: true` from this TypeScript.

Grok's 12:02 PM summary said foundry-comms is "Peer send + room host. JSONL protocol under `comms/`." There is no `comms/` JSONL in this package. There is no room host in this file. Live JSONL is agent-room `events.jsonl` under `pike-floor`, created by hand. That summary is a claim the code cannot keep.

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

### Live (pike)

`/subagents` overlay:

```
Select subagent
→ atropos [runtime] — Chief of Staff — owns the floor, routes work, hosts the room.
  clio [runtime] — Research — reads files, drafts briefs, never sends as the operator.
  hephaestus [runtime] — Computer — the only bot that should write the shared workspace.
  hermes [runtime] — Operations — routines, receipts, standing checks.
```

Builtin scout/researcher did not appear in this overlay.

`/run clio` and `/run hermes` completed with identity-aligned sentences. `subagent` hephaestus async completed. Artifact `/Users/dominikbach/.pi/agent/sessions/--Users-dominikbach-olympus-hackmit-hackmit26-Harness--/subagent-artifacts/8e60e06a-ab5f-4424-8b38-acc3a6cc1cab_hephaestus_output.md` is `HEPHAESTUS-OK.`

Harness `.pi/settings.json` on disk: `disableBuiltins: true`, `agentScanDirs: []`, exclude dirs as TypeScript wrote.

`/subagents-doctor` still counted `agents: total 13 (builtin 13, package 0, user 0, project 0)`. Overlay hid builtins. Doctor still lists them. `disableBuiltins` is not proven to remove builtins from doctor discovery.

`/subagent-cost` listed parent plus Child 1 (clio) and Child 2 (hermes). Hephaestus run `8e60e06a-...` was not in that cost table.

Pike did not show two children talking to each other without the parent.

### Why it matters

A client who thinks Atropos is a standing Chief of Staff gets a subagent template. Live spawn by slug works. That is the choose-among-options child pack doing its job. It is still not a Bot network. Doctor vs overlay is a second lie: settings claim builtins are off, doctor still counts 13.

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

### Live (pike)

Tools ran. Disk `/Users/dominikbach/.pi/agent/foundry/memory/`:

- `clio-peer.md` → `Clio peer ready on pike-floor` (peer Pi)
- `pike-drive.md` → `pike host atropos 2026-09-19` (host Pi)
- `secret-test.md` → `api_key: «redacted» password: «redacted» token: «redacted»`

Redaction works on the regex cases pike wrote. Host and peer share one folder. There is no per-Bot subdirectory. No `MEMORY.md` injection was observed. This confirms the shared-brain defect. The tools are not a no-op.

### Why it matters

Clio's research and Hephaestus's computer notes land in the same folder. Live they already did: host and peer both wrote the same tree. A second client on the same Unix user shares `getAgentDir()`. 7:37 AM: sharing a disk across consulting clients is a data-leak product. This memory plane is that leak, even for Bots inside one tenant.

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

### Live (pike)

`routine_list` returned the Morning floor brief JSON.

`/foundry-routine` (match) pane:

```
 Extension "command:foundry-routine" error: ctx.sendUserMessage is not a function
```

Receipt still written. This window opened `/Users/dominikbach/.pi/agent/foundry/receipts/1789845000302.json`:

```json
{
  "name": "Morning floor brief",
  "bot": "hermes",
  "status": "queued",
  "at": "2026-09-19T19:10:00.302Z"
}
```

Wake did not enter the session as a user message. `/foundry-routine does-not-exist` warned `No matching routine.`

TypeScript claimed `ctx.sendUserMessage(..., { deliverAs: "followUp" })`. Live on Pi 0.85.1 that function is missing. Pane and disk win: fire errors. List and receipt write work. The receipt stays `queued`. Hermes's lane was not involved.

### Why it matters

A client who buys "ops watches the floor every morning" gets a command the operator must type. Live the operator typed it and the command died. Hermes did not run. The receipt still says queued. Foundry output `cadence: "daily"` is decoration. SKILL.md "It is not `/loop`" is worse live: it is a broken `/loop`.

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

### Live (pike)

Overlay appeared when the model called the tool:

```
 Foundry approval
 test-approval
 Live harness probe only. Allow this test.
 → Yes
   No
```

After enter: `{"allowed":true,"action":"test-approval","detail":"Live harness probe only. Allow this test."}`

No extra approval file on disk. Confirm works as a TUI dialog. It does not intercept other tools. Hephaestus still completed `HEPHAESTUS-OK.` as a child with no approval card.

### Why it matters

Hephaestus's instructions say consequential writes must ask the operator. Live, a child named `hephaestus` finished without `ask_user`. Nothing stops that child from `bash rm -rf`. A client floor that can publish or send-as-user without a broker is not safe to hide behind a clean UI (7:37 AM).

---

## Missing extensions the prompts required

These are not lazy files. They are absent.

| Layer (7:52 AM decomposition) | Avenue the prompt set | In the Harness |
| --- | --- | --- |
| Supervisor / process topology | Write it | Absent |
| Inbox, lanes, user-preempt vs peer-queue | Write it | Comments and prompt bullets only |
| Room host + goal parking | Write it | agent-room loaded. Live: human `/room` create `pike-floor`. Host not written. Sample `Floor` absent on disk |
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

The operator asked to see whether Bots communicate and where chat logs go. Pike drove that. This section is TypeScript plus live disk. Pane and disk win.

### What the TypeScript says should happen

**Foundry handle files.** `bot_send_prompt` writes `getAgentDir()/foundry/handles/{handle.id}.json`. Fields: `id`, `bot` (slug), `from` (always `"peer"`), `prompt`, `status`, `createdAt`, optional `runId`, `result`, `note`. `bot_await_turn` reads that file. Nothing else updates it. These files are not a chat log. They are stuck status objects.

**Routine receipts.** `/foundry-routine` writes `getAgentDir()/foundry/receipts/{timestamp}.json` with `status: "queued"`. Not a conversation.

**Memory files.** `getAgentDir()/foundry/memory/{path}`. Shared. Not a transcript.

**agent-room logs, if a human connects.** Upstream writes under `getAgentDir()/rooms/`: per-room `agents/`, `inbox/{agent-id}/`, JSONL-style message appends. Agent ids are `agent-${hostname}-${process.pid}`. Foundry does not auto-connect. Foundry does not create room `Floor` from `aegis.json`.

**Pi session files.** Pi stores sessions under the agent dir. Foundry does not index them. There is no `bot_get_agent_transcript_tail`.

**Child artifacts.** If RPC `spawn` or `/run` works, `pi-subagents` owns async run status and artifacts. Foundry never copies a child transcript onto a handle as `result`.

**Handoff mirroring.** 7:22 AM required the exchange visible on sender transcript and receiver transcript. Foundry does not append a handoff entry to any Bot transcript.

### What actually happened live

Pike's five checks, with disk from this window:

1. After `bot_send_prompt`: there was no call. Handle JSON does not exist. Directory `~/.pi/agent/foundry/handles` is missing. Status never left a file because no file was written.
2. After `bot_await_turn`: no `toolResult`. `done` was never produced by the runtime.
3. `~/.pi/agent/rooms/` contains `pike-floor`, `default`, and `control`. Foundry did not create a room. Pike created `pike-floor` in the `/room` overlay.
4. Pi session files exist for host Pi, peer Pi, leftover verify session, and child runs under the host session dir. Clio the Bot has no standing session. Clio the child has `.../4dd68ab6-c316-4a82-b53f-86d66b4a47c0/run-0/session.jsonl`.
5. Sample room title `Floor` is not a directory. The TypeScript never writes that string except inside `aegis.json`. Live room log is `pike-floor/events.jsonl`.

Room bus log this window opened:

```json
{"type":"join","room":"pike-floor","agentId":"agent-dhcp-10-31-159-94.dyn.mit.edu-34530",...}
{"type":"join","room":"pike-floor","agentId":"agent-dhcp-10-31-159-94.dyn.mit.edu-37318",...}
{"type":"enqueue","id":"msg-1789845379482-c8abb38ee911","from":"...-34530","to":"...-37318","text":"Pike host ping. ... PEER-PONG ..."}
{"type":"deliver","id":"msg-1789845379482-c8abb38ee911",...}
{"type":"enqueue","id":"msg-1789845384909-fdf635625f72","from":"...-37318","to":"...-34530","text":"PEER-PONG agent-dhcp-10-31-159-94.dyn.mit.edu-37318"}
{"type":"deliver","id":"msg-1789845384909-fdf635625f72",...}
{"type":"leave",...-34530...}
{"type":"leave",...-37318...}
```

Session jsonl is the chat log. Roles `user` / `assistant` / `toolResult`. Room injects `[Agent room message]` as a user message. Inbox dirs existed and were empty after deliver.

### Why the log gap matters

A client cannot be shown "the Bots talked" as Foundry Bots. They can be shown two Pi processes with pid ids on `pike-floor`, plus child output files. There is no Foundry transcript to sanitize into an action log (7:37 AM). There is no handle history to bill or debug. The operator's test now has a live answer: logs scatter across session jsonl, room `events.jsonl`, child artifacts, memory files, and a queued receipt. There is no one place. The handle directory is not even one of those places. It was never created.

---

## Claims the docs cannot keep

Leave these strings in the repo only if the runtime is rewritten. Until then they are false.

From `README.md`:

- "turns Pi into a GrokBot-class floor"
- "handles that accept before they run, rooms, memory, routines, and operator approvals" as a list of things "you get"
- Handle protocol "on top of agent-room" — the handle tools do not call agent-room. Live: agent-room worked. Handle tools did not run. No handle file.
- `/foundry-routine [name]` "fire a standing wake onto the owning bot's lane" — live throws `ctx.sendUserMessage is not a function`

From `SOURCE.md`:

- "`bot_send_prompt` accepts before run, `bot_await_turn`, ack ≠ complete" — live never produced a handle. TypeScript still cannot mark complete.
- "Dispatch of accepted work goes through pi-subagents RPC `spawn` when that bus is up, otherwise the model is told to use the real `subagent` / `room_send_message` tools" — the second half admits the fallback is a model instruction. Live, pike used `/run` and `subagent` and `room_send_message` by hand. That is not a control plane.
- `vendor/agent-room.ts` "is a verbatim copy" — the file is not there. Pike: live load used `node_modules/pi-agents-talk-to-each-other/extensions/agent-room/index.ts`.

From `AGENTS.md` and `skills/foundry/SKILL.md`:

- "The JSON you get back is a handle, not a result" — true as a return shape, false as a lifecycle
- "Do not tell the operator a teammate finished unless `bot_await_turn` says `done: true`" — `done` never becomes true. Live never called await.
- "User DMs outrank peer wakes. Peer mail queues when the target is busy." — no code. Live room delivery was `followUp` because pike passed that flag.
- "Rooms: the host wakes members in order. Never skip a busy member." — no host. Live: two pids on `pike-floor`, not roster members in order.
- "Standing checks are Foundry routines, not `/loop`." — live the command errors after writing a queued receipt.
- "Room presence, inbox, and `room_send_message` come from Timur00Kh `agent-room` (vendored)." — live loaded from `node_modules`, not `vendor/agent-room.ts`, and not bound to Foundry rooms

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
6. `pi-usage` is listed as a real package, not rewritten. Fragile path. Live `/usage` worked on this install.
7. `ask_user` really calls `ctx.ui.confirm`. Small and honest. Not a broker. Live overlay worked when the model called it.
8. `SOURCE.md` is right that this package does not reimplement Pi, and that messenger-swarm is not included.
9. Sample `aegis.json` is a clear four-Bot fixture. The names and purposes are usable as test data once a real floor exists.
10. The 12:27 PM demand to depend on real GitHub packages, not a fake Pi SPI, is partly met at the npm layer. The fake SPI was the earlier browser demo Grok admitted. The remaining fake is the Foundry protocol.

---

## Why the operator's "lightweight / lazy / non-functional" read is correct

Not insults. Mapping:

**Lightweight.** Seven custom files, ~540 lines, two slash commands, prompt-as-protocol. The 7:52 AM write-it list is a control plane. This is a package manifest around three npm dependencies.

**Lazy.** Wrong abstraction on purpose of convenience: children as Bots, `/loop` as routines, confirm dialog as approvals, shared folder as memory, load agent-room and do not host, write a handle and do not complete it, tell the model to call another tool when RPC misses. Each is the shortest path that still lets `README.md` name the noun.

**Non-functional (live plus TypeScript).** Handle layer no-op this drive. TypeScript still has no completion writer. Room host has no code. Human `/room` is the only bus that talked. `/foundry-routine` throws on Pi 0.85.1. Approval has no intercept. Memory tools work and share one folder. Transcript tail does not exist. Tenant computer does not exist. Default Codex model failed until pike switched to grok-4.6. The TypeScript already shows the happy path cannot fulfill `bot_await_turn`. Live never reached that path.

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

Pike live (this resume):

- `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/engineers/pike/DRIVE-REPORT.md`
- `/Users/dominikbach/olympus/hackmit/hackmit26/GROK-WORKSHOP/harness-init/engineers/pike/STOP.md`
- Disk: `foundry/handles` (missing), `foundry/receipts/1789845000302.json`, `foundry/memory/{clio-peer,pike-drive,secret-test}.md`, `rooms/pike-floor/events.jsonl`, Harness `.pi/settings.json`, hephaestus artifact, host session jsonl

Not opened: `engineers/flint/`. Not opened: `Harness design.md` (missing from Source-material). This resume did not re-drive Pi.

---

## For the next engineer

Do not start from the README noun list. Start from the 7:52 AM prompt in the vision export and from the refuse list in this file.

Do not treat a passing `/foundry-roster` toast as a floor.

Do not treat pike-floor ping/pong as Foundry Bot-to-Bot.

Do not add more prompt bullets to `protocolBlock()` and call that a fix.

If you implement one seam first, implement handle completion bound to a real turn end, with a transcript tail. Live communication that can be shown today is agent-room pid chat plus child artifacts. That is not the handle protocol.

This document does not pick the architecture to ship. The gap that must not be renamed: the Harness still needs a control plane. Extensions that wrap npm packages are not that plane. Live proved the wrappers that call upstream (`/room`, `/run`, `memory_*`, `ask_user`, `/usage`) can move. Live proved the Foundry protocol (`bot_send_prompt`, await, routine wake, room host, create-bot) did not.
