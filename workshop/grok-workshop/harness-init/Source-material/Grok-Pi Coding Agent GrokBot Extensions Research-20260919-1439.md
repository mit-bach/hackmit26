# Pi Coding Agent GrokBot Extensions Research

**User:** Anonymous  
**Created:** 9/19/2026 7:06:17  
**Updated:** 9/19/2026 12:27:57  
**Exported:** 9/19/2026 14:39:10  
**Link:** [https://grok.com/c/f8739b04-167f-4502-a8df-22a3c6e2f67f?rid=9a1e552c-be37-4e11-8bfc-5e74a7986612](https://grok.com/c/f8739b04-167f-4502-a8df-22a3c6e2f67f?rid=9a1e552c-be37-4e11-8bfc-5e74a7986612)  

## Prompt:
9/19/2026, 7:08:34 AM

I am working on replicating XAI's GrokBot architecture entirely on my own Harness. I'm using the open-source Pi coding agent as a way to make this possible, and we'll do all of my replication through extensions.
What I want you to do is perform an insanely massive research operation on the current extensions that are available for Pi coding agent and determine what I would need. First off, what types of extensions would I need in order to make this possible? I know, for example, for communication protocol or whatever, there are multiple different extensions that could fit this and work very well. I want to observe all of this and see, as a whole, which ones could potentially work, and be very thorough.
I want you to put an extreme amount of effort into this operation, into reverse engineering GrokBot through Pi coding agent.

## Response:
9/19/2026, 7:08:34 AM

> **Thoughts:**
>
> - Thinking about your request
> - Researching Pi coding agent extensions
> - Searched web - Pi coding agent extensions
> - Searched web - "Pi coding agent" open source extensions
> - Searched web - pi-agent coding agent github extensions
> - Searched web - GrokBot architecture xAI Grok bots agents computer memory routines
> - Searched web - pi-acp Agent Communication Protocol pi coding agent
> - Searched web - pi-tick pi-loop pi-schedule-prompt scheduled routines extension
> - Searched web - composio-x-pi pi coding agent connectors slack gmail
> - Searched web - oh-my-pi multi-agent orchestration pi extension
> - Searched web - pi coding agent RPC mode inter-session control socket crosstalk
> - Searched web - pi-agent-browser-native computer use browser automation pi extension

I'll start by mapping GrokBot's architecture against the Pi coding agent extension ecosystem so the research is grounded in both sides, not just a catalog.Pi’s extension surface and Grok Bot’s public design docs are the two sources I’ll map next, then I’ll pull the packages that actually implement those primitives.The remaining gaps are the packages that actually implement bot-to-bot comms, scheduling, computer-use, and connectors — those are the GrokBot primitives Pi does not ship natively.Pi will not give you GrokBot. It gives you a thin harness and an in-process TypeScript plugin surface. GrokBot is a product OS: named persistent agents, one shared computer, per-bot memory, account-level tools, routines that run while you are gone, and a control plane that can create, search, prompt, and wait on those agents. The replication job is to reconstruct that OS as Pi extensions plus a small amount of code you write yourself. [X](https://x.ai/news/designing-grok-bot)

What follows is the architecture map, then every extension class that can implement a layer, then the protocol options (the part you called out), then a recommended stack and the pieces that do not exist yet.

---

## 1. GrokBot, decomposed into primitives

xAI’s public design collapses the product to five nouns: **Bots, Chats, Prompts, Tools, Artifacts**. Routines are Prompts that fire on a clock or an event. Skills are Prompts saved as reusable how-to. Memory and Routines belong to a Bot. Tools and Skills belong to the account. All Bots share one cloud computer; each Bot gets its own screen; files, browser sessions, and logins are not a security boundary between Bots. Isolation is per user, not per Bot. Work continues when the laptop is closed. Bots message each other, run in parallel, and pass ownership. Limits in the design writeup: ~50 Bots per account, 6 per group chat. [X](https://x.ai/news/designing-grok-bot)

From the live product contract (not just the marketing essay), the control plane is more specific than “they can talk”:

| GrokBot verb | What it actually is |
|---|---|
| Create | Named agent + standing purpose. No first prompt. Cannot be deleted. |
| Search / list | Roster by name/description/status (`idle` / `running`) |
| Send | Prompt + optional files + `async` / `blocking` / `fire_and_forget` + busy policy (`supersede` / `queue` / `reject`) |
| Await | Wait on a handle until the turn ends; acknowledgements are not the answer |
| Transcript tail | Read last N entries without polling as a wait loop |
| Connectors | Discover tools on connected services, then call one by schema |
| Computer | Shared FS + shell + browser; not the user’s laptop |
| Routine | Prompt + cadence or event, owned by one Bot, runs unattended |
| HITL | Structured questions; connector auth cards; fail-closed on send-as-user / pay / merge / deploy |

That table is the spec you are implementing. Pi ships almost none of it.

---

## 2. What Pi actually is

Pi’s own philosophy is the inverse of GrokBot: primitives, not features. Default tools are `read`, `write`, `edit`, `bash`. No subagents, no MCP, no plan mode, no todos, no background jobs, no memory store, no scheduler. All of that is supposed to be extensions. [News](https://news.qiniu.com/archives/1787103478559)

The extension API is strong enough to build an OS on:

- `registerTool` / `registerCommand` / `registerShortcut` / `registerFlag` / `registerProvider`
- Lifecycle events: `session_start`, `turn_start`, `agent_end`, `tool_call`, `before_agent_start`, `session_before_compact`, `session_shutdown`, …
- `sendMessage` / `sendUserMessage` / `appendEntry` (persist data the model never sees)
- `pi.events` (in-process bus between extensions in the same session)
- `ctx.mode`: `tui` | `rpc` | `json` | `print`
- RPC mode: NDJSON over stdin/stdout so a host process can own sessions
- Skills as `SKILL.md` files
- Sessions as files under `~/.pi/agent/sessions/`

What it does **not** give you: a roster of long-lived named peers, a shared cloud VM, out-of-process scheduling that survives the TUI dying, account-level OAuth connectors, computer-use screens, or `bot_await_turn` semantics.

So the replication is: **keep Pi as the per-Bot runtime; put GrokBot’s control plane, roster, routines, connectors, and computer around it.**

---

## 3. Extension types you need

These are types, not packages. Each type has multiple packages that can fill it. Do not install one of everything. Pick one winner per type and write glue.

### Type A — Bot identity and roster

**Need:** A Bot is not a Pi session. A Bot is a durable record: name, standing purpose, memory path, tool allowlist, routine list, last status, last handle. Sessions are conversations with that Bot.

**Existing pieces:**
- Official-style session pickers: `sessions` in `pi-agent-extensions` (`/sessions`)
- `pi.setSessionName` / session files
- `oh-my-pi` agent definitions + `.oh-my-pi.jsonc`
- `agent-pi` `agents/*.md` + `teams.yaml`
- `@tifan/pi-rename`, `auto-rename`

**Gap:** None of these enforce GrokBot’s roster rules (no near-duplicate purpose, standing duty goes to one owner, create only when the user asks and nothing covers the domain). You write a `bots` registry extension: JSON/SQLite under the shared computer, tools that look like `bot_create_agent`, `bot_search_agents`, `bot_list_agents`.

### Type B — Persistent runtime / “the computer”

**Need:** One machine all Bots share. Files, browser profiles, CLI logins live there. Each Bot has a logical screen (one computer-use task at a time per Bot). The process must outlive your laptop session.

**Existing pieces:**
- Pi itself on a box that stays up (this is the whole point of “your Harness”)
- Official `ssh.ts` example: delegate all tools to a remote machine
- `gondolin/` official example: route tools into a micro-VM
- `sandbox/` official example: OS-level sandbox
- Herdr / tmux / worktree extensions: “screens” as panes
- `pi-worktree`, `pi-herdr-worktree-jump`

**Gap:** Pi will not provision the cloud VM. That is infrastructure: a persistent Linux box, a browser profile directory, a secrets store, a process supervisor (`systemd`, launchd, or a small daemon that keeps `pi --mode rpc` children alive). Treat Herdr/tmux as the screen multiplexer, not as the computer.

### Type C — Per-bot memory

**Need:** Memory belongs to the Bot. Shared files are not memory. Compaction must not wipe identity.

**Candidates (pick one memory plane, not five):**

| Package | Shape | Fit for GrokBot |
|---|---|---|
| `pi-hermes-memory` | SQLite FTS5, policy-only by default, consolidation, session search | Strong. Scope it per bot id. |
| `@amaster.ai/pi-memory-mem0` | Semantic capture/recall, hosted or self-hosted | Good if you want embeddings. |
| `pi-memory` | qmd semantic search over daily logs + long-term + scratchpad | Fine for a single agent; weaker multi-bot isolation. |
| `gentle-engram` | One brain across sessions/MCP | Opposite of GrokBot’s per-bot memory unless you namespace. |
| `@henryqw/pi-memory` | Capped MEMORY.md / USER.md | Simple, inspectable, easy to scope per bot directory. |
| `context-mode` | Tool-output sandbox + SQLite memory | Context hygiene first, memory second. |

Recommendation: **directory-scoped markdown + SQLite index**, one tree per Bot (`~/computer/bots/<id>/memory/`), injected on `before_agent_start`. Use hermes-memory or a thin custom writer. Do not use a single shared “brain” unless you want the legal Bot to remember the finance Bot’s ledger.

### Type D — Multi-agent runtime (children vs peers)

This is the most crowded category and the easiest place to pick the wrong abstraction.

**Child / subagent packages** (spawn, wait, die — good for “go research this,” bad as the Bot roster):

- `pi-subagents` — the default. ~450k npm downloads/month. Single delegation + scripted multi-agent workflows. [Raw](https://raw.githubusercontent.com/shaftoe/awesome-pi-coding-agent/main/README.md)
- `@tintinweb/pi-subagents` — Claude Code-like, parallel, fleet view, mid-run steering
- `@ogulcancelik/pi-codex-subagents` — session-scoped, templates, waits, overlay
- `@arhen/pi-core-subagent` — in-process, dependency-graph scheduler, **intercom + agent-to-agent messages**
- `@everyx/pi-subagent` — three primitives: spawn / stop / send (closest mini-API to GrokBot send)
- Official example `subagent/` — isolated context windows
- Dozens of forks (`@henryqw`, `@d3ara1n`, `@ferris1225`, `pi-cohort`, `pi-vigil`, …)

**Orchestrator suites** (replace the prompt with a coordinator):

- `oh-my-pi` + swarm-extension — YAML DAGs, specialist agents, shared filesystem as the bus
- `agent-pi` — 43 extensions, modes NORMAL/PLAN/SPEC/PIPELINE/TEAM/CHAIN
- `@groeponline/pi-agent-orchestrator` — subagents, swarms, worktrees, **schedules and handoffs**, live TUI
- `pi-messenger-swarm` — file-based mesh, channels, tasks, spawn
- `pi-cmux` — local workspace of terminal + browser surfaces
- `pi-fusion` / `advisor-pi` — cheap persistent sidekick + stronger advisor model

Use subagents **inside** a Bot for bounded work. Do not treat a subagent as a Bot. GrokBot Bots are long-lived named peers with their own memory and routines. Subagents are disposable context windows.

### Type E — Communication protocol (the layer you asked about)

There is no single “Pi comms extension.” There are five different protocols. They solve different problems. You will probably use two.

#### E1. Pi RPC — host ↔ agent

`pi --mode rpc`: NDJSON commands on stdin, events on stdout. This is how an IDE or your Harness drives one session: prompt, abort, switch session, compact, set model. `pi-acp` wraps this as Agent Client Protocol for Zed and other ACP clients. [GitHub](https://github.com/svkozak/pi-acp)

**Use for:** your control plane talking to a Bot process.  
**Do not use for:** Bot ↔ Bot. ACP is client↔agent, not agent↔agent.

Related: `pi-server` (tryingET) multiplexes N `AgentSession` instances over WebSocket + stdio. That is a Harness-shaped piece.

#### E2. Per-session control sockets — peer or host injection

Official-adjacent pattern: Armin Ronacher’s `control.ts` / the `control` extension in `pi-agent-extensions`. Each session opens a Unix socket under `~/.pi/session-control`. Commands: `send` (steer | follow_up), `get_message`, `get_summary`, `clear`, `abort`, `subscribe turn_end`. Flags like `--session-control`, `--send-session-message`.

`crosstalk` in `@byteowlz/pi-agent-extensions` is the same idea, adapted from Ronacher.

**Use for:** `bot_send_prompt` + `bot_await_turn` against a live process. Steer vs follow-up maps onto GrokBot’s “don’t clobber a running turn” vs “queue after idle.” Subscribe-on-`turn_end` is `bot_await_turn`.

#### E3. Discovery + message passing — true peers

`pi-cross-session`: same-machine discovery and plain-text messages over per-instance IPC. Tools: `list_pi`, `send_pi_message`. Commands: `/peers`. Busy/idle is delivery state. Optional EventBus RPC is off by default. No daemon. [Npmjs](https://www.npmjs.com/package/pi-cross-session?activeTab=code)

Implicator’s “Pi-to-Pi communication bus” tutorial: a local mailbox broker + five tools (join, list, send, read, ack) with TTL and tokens. Explicitly peer-not-parent. [Implicator](https://www.implicator.ai/professional-tutorial-build-a-pi-to-pi-agent-communication-bus-2/)

`pi-messenger-swarm`: channel-first file bus (`#memory`, session channels), task claim/progress/done. Survives without a daemon because the filesystem is the computer.

**Use for:** group chat / “ping the research bot.” File/channel buses are the most GrokBot-like for shared artifacts; sockets are better for low-latency steer/await.

#### E4. In-process event bus

`pi.events.emit/on` only works inside one process. Useful for extensions cooperating inside one Bot (memory writer listening to `agent_end`). Useless as the Bot network.

#### E5. MCP / Composio as a side channel

You can stand up an MCP server that is the mailbox, then attach it to every Bot via `pi-mcp-adapter`. That is how you get Bot A on machine 1 talking to Bot B on machine 2. Heavier than Unix sockets; right if the Harness is multi-host.

**Protocol recommendation for a GrokBot replica**

```
Harness (your control plane)
    │  RPC or Unix socket
    ▼
Bot process (pi --mode rpc + extensions)
    │  list/send over IPC or file mailbox
    ▼
Other Bot processes on the same computer
```

Implement four tools that match the product verbs, regardless of transport:

1. `bot_search_agents(query, status?, limit?)`
2. `bot_send_prompt(agent_id, prompt, mode=async, on_busy=supersede, paths?)`
3. `bot_await_turn(agent_id, handle?)`
4. `bot_get_agent_transcript_tail(agent_id, limit, before_seq?)`

Transport can be control sockets today and a small daemon tomorrow. Do not leak `pi-subagents` child IDs as Bot IDs.

Busy policy mapping:

| GrokBot `on_busy` | How to implement on Pi |
|---|---|
| `supersede` | control-socket `abort` then `send` |
| `queue` | write to a per-bot inbox file; drain on `agent_end` / idle |
| `reject` | return error if `ctx.isIdle()` is false |

`async` = write handle, return immediately. `blocking` = forbidden for long work (GrokBot is right about this; Pi turns outlive naive waits). `fire_and_forget` = send, do not keep a handle.

### Type F — Routines (schedule + event)

GrokBot routines are the feature that makes Bots coworkers instead of chat windows. Two subproblems: **in-session loops** and **runs while the user is away**.

**In-session (TUI or RPC process must be alive):**

- `pi-scheduler` — `/loop`, `/remind`, LLM tool `schedule_prompt`, interval or cron
- `pi-schedule-prompt` — “heartbeat,” natural language, optional per-task model in a side session
- `pi-scheduled-tasks` — one-shot NL time, cron, queued while busy, session snapshot restore
- `@koltmcbride/pi-loop` — timer-driven, **event and hybrid triggers** (`tool_execution_end`, `turn_end`)
- `@pi-agents/loop` — Claude Code `/loop` port + `cron_*` tools + idle gating
- Official issue #2368 pattern: `appendEntry` + restore on `session_start`

**Out of session (the actual GrokBot requirement):**

- `pi-tick` — launchd (macOS) or cron (Linux). This is the one that still fires when no TUI is open.
- `@amaster.ai/pi-task-scheduler` — cron + LLM tools
- `@trevonistrevon/pi-loop` — scheduled/event re-wakes + durable workflows
- `pi-wake` — timers, container watches, completion-file conditions that wake the same session
- `@llblab/pi-wakeup` — singleton wake-up scheduler
- Composio **triggers** (email, Slack, GitHub) as the event bus

**Gap:** Almost every `/loop` package dies when the session process dies. GrokBot routines do not. Your Harness needs a supervisor: cron/launchd/systemd starts `pi --mode rpc -p "<routine prompt>"` (or sends on the control socket if the Bot process is already up). Persist routine records on the Bot (`prompt`, `cron` or `event`, `last_run`, `last_result`). Event triggers come from Composio webhooks or a tiny HTTP listener on the computer.

### Type G — Connectors (account-level tools)

GrokBot prefers connectors over clicking through a site. Shared across Bots.

**Candidates:**

| Approach | What you get | Cost |
|---|---|---|
| **Composio** (`composio-x-pi` / `@composio/experimental` Pi provider) | 1000+ apps, managed OAuth, 7 meta-tools (`SEARCH_TOOLS`, execute, manage connections), triggers, optional remote sandbox | Best analog to Grok connectors. Auth is their problem. |
| **`pi-mcp-adapter`** (~987k/mo) | Any MCP server as tools without dumping the whole catalog into context | You run/host the servers. |
| `pi-mcp-extension`, `@pi-unipi/mcp`, `@hyav/pi-mcp` | Alternate MCP hosts | Overlap with the adapter; pick one host. |
| Skills wrapping `gh`, Linear SDK, etc. (`NelsonBrandao`, `agent-pi`) | Cheap, local, no OAuth platform | Per-app glue, no unified search. |

Implement two tools that match the product:

- `search_connected_tools(query)` → ranked tools + JSON schemas
- `call_connected_tool(name, arguments)`

Plus an auth path: if Composio returns “connect this app,” surface it the way Grok surfaces `request_connector_auth`. Do not also bind raw Gmail MCP and Composio Gmail. One route.

### Type H — Computer use and browser (the screen)

GrokBot: connectors first; computer use for everything else; one computer-use task per Bot screen; shared logins.

**Browser (web apps without a connector):**

- `pi-agent-browser-native` — native `agent_browser` tool, persistent profiles, scripts
- `pi-agent-browser` — Chromium + snapshot/`@ref` click loop
- `pi-browser-use` — **your real logged-in browser over CDP** (closest to “Marketplace bot already has Facebook open”)
- `pi-puppeteer` — attach to installed Chrome/Edge, record/replay workflows
- Playwright folder extensions (`browser_goto`, `browser_eval`, …)

**Desktop:**

- `@amaster.ai/pi-computer-use` — `cua-driver-rs`, screenshot + click/type on the actual desktop

**Remote computer:**

- official `ssh.ts`
- official `gondolin/` micro-VM

For a replica: persistent Chromium profile on the shared computer + one lock per Bot so two Bots do not fight the same screen. `pi-browser-use` / native agent-browser with a shared profile directory is the right default. Full desktop computer-use is a later layer and a security problem.

### Type I — Skills and demonstration learning

Pi already has skills. GrokBot adds “watch me do it once, save as skill, optionally promote to routine.”

**Existing:** Pi skills, `mention-skills` autocomplete, `pi-repo-skills` toggles, `prompt-save` / `prompt-stash`, `pi-puppeteer` workflow record/replay, Plannotator plan files.

**Gap:** No extension records a 10-minute human demonstration on the computer and compiles it into a skill. That is custom: trace browser + bash + file ops during a “teach” mode, write `SKILL.md`, optionally attach a routine.

### Type J — HITL, permissions, approvals

GrokBot fails closed on send-as-user, pay, merge, deploy.

**Candidates:**
- `ask_user` / `@juicesharp/rpiv-ask-user-question` / official `questionnaire.ts` — structured questions (maps to `ask_user_question`)
- official `permission-gate.ts`, `protected-paths.ts`, `confirm-destructive.ts`, `dirty-repo-guard.ts`, `project-trust.ts`
- `pi-auto-permissions` — guardian review of bash
- `pi-security` (VTSTech) — command/path/SSRF
- `sudo` tool with masked prompt (`byteowlz`)

You want a policy extension that tags tools as `read` / `write-local` / `side-effect-external` and blocks the last class until the user confirms.

### Type K — Context, compaction, todos, plans

Not GrokBot-core, but you will drown without them once Bots run unattended.

- Todos: official `todo.ts`, `rpiv-todo`, file-based todos in several collections
- Plan mode: official `plan-mode/`, himorishige, ferologics, Plannotator
- Compaction: `session_before_compact` hook, `pi-codex-compaction`, SoL-Pi / `@hypabolic/pi-hypa`
- Handoff: official `handoff.ts`, `@tifan/pi-handoff` — useful for “pass ownership,” which GrokBot does between Bots

### Type L — Presence, notify, observability

GrokBot’s avatar states: idle, thinking, working, waiting, blocked, done.

- `notify` / `pi-notify` / `@herbertgao/pi-bark` — turn-end notifications
- footers: powerline, focus-ui, statusline-pi, token-speed
- `@groeponline/pi-agent-orchestrator` dashboard
- `herdr-integration` blocked-state reporting

Your Harness should expose status from `ctx.isIdle()`, last tool name, and last error. The TUI widgets are optional.

### Type M — Model / provider (so the replica can run Grok)

- `grok-pi` — Grok CLI models inside Pi
- `claude-code-pi`, `cursor-pi`, `opencode-pi`, `pi-free`
- `pi.registerProvider` if you want a first-party xAI HTTP provider

Irrelevant to architecture; relevant to “it feels like Grok.”

---

## 4. What you should install vs what you should write

Community packages get you 60% of the runtime. The GrokBot product is the other 40%, and it is policy + control plane.

**Install (one per type):**

1. Runtime children: `pi-subagents` (or `@tintinweb/pi-subagents` if you want the fleet UI)
2. Peer comms: `pi-cross-session` **or** Ronacher `control` — not both as sources of truth
3. Host embedding: Pi RPC + optionally `pi-server` or `pi-acp` if you want an IDE/desktop shell
4. Memory: `pi-hermes-memory` scoped per bot directory
5. Connectors: Composio via MCP adapter **or** native Pi provider — plus `pi-mcp-adapter` for everything Composio does not cover
6. Browser screen: `pi-agent-browser-native` or `pi-browser-use` with a shared profile on the computer
7. In-session loops: `@koltmcbride/pi-loop` (event + cron) 
8. Out-of-session routines: `pi-tick` + your supervisor
9. HITL: `rpiv-ask-user-question` + official permission-gate / protected-paths
10. Notify: whatever matches the desktop you use

**Write yourself (this is the replica):**

1. **`bots` registry** — id, name, description, memory path, tools, routines, status, pid/socket
2. **Four control tools** — search / send / await / transcript, with async handles and `on_busy`
3. **Roster policy** — domain coverage, no silent duplicates, standing duty assignment rules
4. **Routine store + supervisor** — cron/event records that wake a Bot process on the shared computer
5. **Connector facade** — `search_connected_tools` / `call_connected_tool` so Bots do not see Composio vs MCP
6. **Screen lock** — one computer-use task per Bot
7. **Teach-to-skill** (later)

That custom package *is* the GrokBot extension. Everything else is a dependency.

---

## 5. Honest reverse-engineering limits

You can replicate the **architecture**. You cannot replicate the **hosted product** from extensions alone.

- xAI does not publish the Bot model, the memory compressor, the demonstration-learning model, or the exact routine scheduler.
- The shared computer is a persistent cloud VM with a desktop, not a folder on your laptop. Pi on a box you already own is the honest equivalent.
- Group chats with six Bots and heterogeneous transcripts (messages + events + artifacts + visualizations) are a UI product. Pi gives you sessions and custom entry renderers; the group surface is yours.
- Approval cards and connector OAuth UX are product. Composio covers auth links; you still need a place to show them when the user is on a phone.
- “Work continues when the laptop is closed” is process supervision + a computer that is not the laptop. No npm package does that by itself.

If the goal is a working replica on your Harness, optimize for the control plane and the shared machine, not for collecting every subagent fork on npm. The ecosystem is badly duplicated: there are easily 40 packages that all say “subagents for Pi.” One good one plus your roster is enough.

---

## 6. Build order that will not thrash

**Phase 0 — computer.** One always-on host. Shared workspace directory. Browser profile. systemd/launchd unit that can start `pi --mode rpc --name <bot>`.

**Phase 1 — one named Bot.** Session name + description + per-bot memory injection + skills. Prove compaction does not wipe identity.

**Phase 2 — control plane.** Registry + send/await over the control socket. Talk to that Bot from a second Pi session the way this Grok instance talks to GrokBots.

**Phase 3 — second Bot + shared files.** Handoff a file. No second computer.

**Phase 4 — connectors.** Composio or MCP behind two facade tools. Auth once, all Bots reuse it.

**Phase 5 — routines.** Persist on disk; supervisor fires them; results land in the Bot transcript.

**Phase 6 — browser screen + HITL policy.** Then demonstration skills. Then group channel.

That order matches how GrokBot is designed: identity and the computer first, coordination second, autonomy third. The extension catalog is large because Pi left every feature on the floor. You only need the floorboards that correspond to those five nouns.

> **Sources:**
>
> 1. [pi-agent-extensions · Packages · Pi](https://pi.dev/packages/pi-agent-extensions)
> 2. [pi/packages/coding-agent/examples/extensions at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/extensions)
> 3. [GitHub - TianZuo555/pi-extensions: pi coding agent extensions: per-repo model, per-repo skill toggles, image cache · GitHub](https://github.com/TianZuo555/pi-tian-extensions)
> 4. [GitHub - himorishige/pi-coding-agent-extensions: Pi coding agent extensions for focused daily development · GitHub](https://github.com/himorishige/pi-coding-agent-extensions)
> 5. [GitHub - sids/pi-extensions: Extensions for pi coding agent · GitHub](https://github.com/sids/pi-extensions)
> 6. [Extensions · Documentation · Pi](https://pi.dev/docs/latest/extensions)
> 7. [GitHub - ogulcancelik/pi-extensions: Extensions for pi, the terminal-based coding agent · GitHub](https://github.com/ogulcancelik/pi-extensions)
> 8. [pi-agent-extensions/AGENTS.md at main · jayshah5696/pi-agent-extensions · GitHub](https://github.com/jayshah5696/pi-agent-extensions/blob/main/AGENTS.md)
> 9. [GitHub - HerbertGao/pi-extensions: HerbertGao maintained extensions for the Pi coding agent · GitHub](https://github.com/HerbertGao/pi-extensions)
> 10. [Top 10 Pi Agent Extensions Every Developers Must Install | Composio](https://composio.dev/content/top-pi-extensions)
> 11. [GitHub - ferologics/pi-extensions: Custom pi-coding-agent extensions · GitHub](https://github.com/ferologics/pi-extensions)
> 12. [pi-extensions/extensions/claude-code-pi/README.md at main · luongnv89/pi-extensions · GitHub](https://github.com/luongnv89/pi-extensions/blob/main/extensions/claude-code-pi/README.md)
> 13. [GitHub - NelsonBrandao/pi-agent-extensions: A collection of extensions, skills and themes for the pi coding agent · GitHub](https://github.com/NelsonBrandao/pi-agent-extensions)
> 14. [GitHub - VTSTech/pi-coding-agent: Extensions I've written for Pi Coding Agent · GitHub](https://github.com/VTSTech/pi-coding-agent)
> 15. [GitHub - byteowlz/pi-agent-extensions: extensions for pi-agent · GitHub](https://github.com/byteowlz/pi-agent-extensions)
> 16. [GitHub - luongnv89/pi-extensions: Collection of extensions and themes for Pi Coding Agent · GitHub](https://github.com/luongnv89/pi-extensions)
> 17. [GitHub - apmantza/pi-free: All-in-one free/freemium/paid model providers for Pi · GitHub](https://github.com/apmantza/pi-free)
> 18. [https://raw.githubusercontent.com/shaftoe/awesome-pi-coding-agent/main/README.md](https://raw.githubusercontent.com/shaftoe/awesome-pi-coding-agent/main/README.md)
> 19. [9.3万星开源神器Pi Agent完整指南：极简终端编程助手，从安装到Extension开发 | 七牛云](https://news.qiniu.com/archives/1787103478559)
> 20. [Pi Agent Extensions: Change the Harness, Not Just the Prompt (2026)](https://www.aibuilderclub.com/blog/pi-agent-extensions-guide)
> 21. [pi/packages/coding-agent/docs/extensions.md at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)
> 22. [agent-pi/README.md at main · ruizrica/agent-pi · GitHub](https://github.com/ruizrica/agent-pi/blob/main/README.md)
> 23. [GitHub - jayshah5696/pi-agent-extensions: Collection of extensions for pi coding agent (sessions, ask_user, handoff) · GitHub](https://github.com/jayshah5696/pi-agent-extensions)
> 24. [GitHub - tifandotme/pi-extensions: A collection of Pi coding agent extensions · GitHub](https://github.com/tifandotme/pi-extensions)
> 25. [GitHub - charles-cooper/pi-extensions: personal extensions to pi agent · GitHub](https://github.com/charles-cooper/pi-extensions)
> 26. [https://r.jina.ai/https:/x.ai/news/designing-grok-bot](https://r.jina.ai/https:/x.ai/news/designing-grok-bot)
> 27. [Grok Bot | SpaceXAI Docs](https://docs.x.ai/grok-bot/overview)
> 28. [Grok Bot Architecture: Shared Cloud Computer, Named Teammates, and Approval Boundaries — The Architecture DeepDive](https://thearchitecturedeepdive.blog/articles/grok-bot-architecture.html)
> 29. [GitHub - tiagovilasboas/grok-bot-architecture: Staff reference for Grok Bot / desktop multi-agent assistants — architecture, crew, routines, HITL, connectors. Pattern first; product as example host. · GitHub](https://github.com/tiagovilasboas/grok-bot-architecture)
> 30. [What is Grok Bot? xAI’s always-on AI agents explained](https://continuumcode.ai/guides/what-is-grok-bot/)
> 31. [Grok Bot: xAI's AI Teammates Get Their Own Computer](https://www.digitalapplied.com/blog/grok-bot-ai-teammates-launch-cloud-computer-2026)
> 32. [xAI Introduces New Grok Bot Design for Persistent AI Agents - AI Agent Blog | AgentLocker](https://agentlocker.ai/news/xai-introduces-new-grok-bot-design-for-persistent-ai-agents)
> 33. [Grok Bot 101 · Grok Bot Guides](https://x.ai/bot/guides/grok-bot-101)
> 34. [Grok Bot: xAI's Always-On AI Agents, Explained (September 2026) - AIToolsReview](https://aitoolsreview.co.uk/insights/grok-bot-agent-launch)
> 35. [xAI Launches Grok Bot: How Its Multi-Agent Architecture Works - Opoinstall](https://www.opoinstall.com/blog/xai-launches-grok-bot)
> 36. [Designing Grok Bot for a world of persistent agents](https://x.ai/news/designing-grok-bot)
> 37. [GitHub - svkozak/pi-acp: ACP adapter for pi coding agent · GitHub](https://github.com/svkozak/pi-acp)
> 38. [https://raw.githubusercontent.com/svkozak/pi-acp/main/README.md](https://raw.githubusercontent.com/svkozak/pi-acp/main/README.md)
> 39. [Pi - ACP Agent | Zed](https://zed.dev/acp/agent/pi)
> 40. [pi-acp/AGENTS.md at main · regadas/pi-acp · GitHub](https://github.com/regadas/pi-acp/blob/main/AGENTS.md)
> 41. [How to Build a Pi Agent Communication Bus](https://www.implicator.ai/professional-tutorial-build-a-pi-to-pi-agent-communication-bus-2/)
> 42. [@automatalabs/pi-acp - npm](https://www.npmjs.com/package/@automatalabs/pi-acp)
> 43. [GitHub - victor-software-house/pi-acp: ACP adapter for pi coding agent · GitHub](https://github.com/victor-software-house/pi-acp)
> 44. [pi-acp/README.md at main · 0xSero/pi-acp · GitHub](https://github.com/0xSero/pi-acp/blob/main/README.md)
> 45. [pi-scheduler · Packages · Pi](https://pi.dev/packages/pi-scheduler)
> 46. [pi-scheduled-tasks · Packages · Pi](https://pi.dev/packages/pi-scheduled-tasks?page=59)
> 47. [pi-schedule-prompt · Packages · Pi](https://pi.dev/packages/pi-schedule-prompt)
> 48. [@koltmcbride/pi-loop · Packages · Pi](https://pi.dev/packages/@koltmcbride/pi-loop)
> 49. [@pi-agents/loop · Packages · Pi](https://pi.dev/packages/@pi-agents/loop)
> 50. [pi-ate-scheduler · Packages · Pi](https://pi.dev/packages/pi-ate-scheduler)
> 51. [Feature: /loop extension — recurring prompt scheduler · Issue #2368 · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/issues/2368)
> 52. [nuggets/.pi/extensions/proactive.ts at main · NeoVertex1/nuggets · GitHub](https://github.com/NeoVertex1/nuggets/blob/main/.pi/extensions/proactive.ts)
> 53. [Build a Slack bot that can do work with you and your team | Composio](https://docs.composio.dev/examples/general-agent-with-pi)
> 54. [How to integrate Gmail with Pi | Composio](https://composio.dev/toolkits/gmail/framework/pi-agent)
> 55. [https://docs.composio.dev/docs/providers/pi.md](https://docs.composio.dev/docs/providers/pi.md)
> 56. [Composio (App Integrations) | Pickaxe Learn](https://pickaxe.co/learn/composio-integration)
> 57. [https://docs.composio.dev/docs/composio-connect.md](https://docs.composio.dev/docs/composio-connect.md)
> 58. [oh-my-pi · Packages · Pi](https://pi.dev/packages/oh-my-pi)
> 59. [https://cdn.jsdelivr.net/npm/@oh-my-pi/swarm-extension@latest/README.md](https://cdn.jsdelivr.net/npm/@oh-my-pi/swarm-extension@latest/README.md)
> 60. [GitHub - ruizrica/agent-pi: An extension suite that turns Pi into a multi-agent orchestration platform · GitHub](https://github.com/ruizrica/agent-pi)
> 61. [GitHub - monotykamary/pi-messenger-swarm: Swarm-first multi-agent messaging and task orchestration extension for Pi · GitHub](https://github.com/monotykamary/pi-messenger-swarm)
> 62. [GitHub - GroepOnline/pi-agent-orchestrator: Multi-agent orchestration for Pi: subagents, swarms, worktrees, schedules, handoffs and live TUI observability. · GitHub](https://github.com/GroepOnline/pi-agent-orchestrator)
> 63. [GitHub - gtwatts/pi-cmux: Pi CMUX extension family: local CMUX multi-agent orchestration, Pi session bridge, browser intelligence, and design workflows for Pi. · GitHub](https://github.com/gtwatts/pi-cmux)
> 64. [https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/rpc.md](https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/rpc.md)
> 65. [Pi Coding Agent Documentation · Grok Docs](https://grok-wiki.com/public/docs/earendil-works-pi-7860a70e44d1)
> 66. [https://raw.githubusercontent.com/mitsuhiko/agent-stuff/main/extensions/control.ts](https://raw.githubusercontent.com/mitsuhiko/agent-stuff/main/extensions/control.ts)
> 67. [pi/packages/coding-agent/src/modes/rpc at main · earendil-works/pi · GitHub](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent/src/modes/rpc)
> 68. [GitHub - tryingET/pi-server: Session multiplexer for pi-coding-agent — WebSocket + stdio, the protocol IS the architecture · GitHub](https://github.com/tryingET/pi-server)
> 69. [pi-cross-session - npm](https://www.npmjs.com/package/pi-cross-session?activeTab=code)
> 70. [pi/packages/coding-agent/docs/rpc.md at main · earendil-works/pi · GitHub](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/rpc.md)
> 71. [https://npm.io/package/pi-cross-session.md](https://npm.io/package/pi-cross-session.md)
> 72. [https://raw.githubusercontent.com/fitchmultz/pi-agent-browser-native/main/README.md](https://raw.githubusercontent.com/fitchmultz/pi-agent-browser-native/main/README.md)
> 73. [pi-agent-browser/README.md at main · coctostan/pi-agent-browser · GitHub](https://github.com/coctostan/pi-agent-browser/blob/main/README.md)
> 74. [https://raw.githubusercontent.com/amosblomqvist/pi-config/main/extensions/browser/README.md](https://raw.githubusercontent.com/amosblomqvist/pi-config/main/extensions/browser/README.md)
> 75. [pi-puppeteer - npm](https://www.npmjs.com/package/pi-puppeteer)
> 76. [@amaster.ai/pi-computer-use · Packages · Pi](https://pi.dev/packages/@amaster.ai/pi-computer-use?page=2)
> 77. [GitHub - longweekendprojects/pi-browser-use: Drive your real, logged-in Arc browser from pi over CDP: primitives plus a library of hardened multi-step shortcuts (AWS SSO login, wait-for). · GitHub](https://github.com/longweekendprojects/pi-browser-use)
> 78. [https://raw.githubusercontent.com/fitchmultz/pi-agent-browser-native/HEAD/docs/ARCHITECTURE.md](https://raw.githubusercontent.com/fitchmultz/pi-agent-browser-native/HEAD/docs/ARCHITECTURE.md)
> 79. [pi-agent-browser-native/docs/REQUIREMENTS.md at main · fitchmultz/pi-agent-browser-native · GitHub](https://github.com/fitchmultz/pi-agent-browser-native/blob/main/docs/REQUIREMENTS.md)

## Prompt:
9/19/2026, 7:22:24 AM

Okay, specifically, when you're talking about my situation where I'm trying to replicate the communication protocol that GrokBot uses specifically for inter-agent communication, I really like how that works, and I want you to go deeper and to explore. You can say what GrokBot has officially said about how their communication protocol works, but they're probably not going to be very open about it. Go into forums and say what other people are speculating, and get a really detailed spec, and then confirm what the possible ways are that I can emulate that? You kind of did that, but not really. Are you saying that E5, the MCP, is the only way that I'm going to be able to go, and I'll have to essentially create this myself, or is there something out of the box that I can use?

## Response:
9/19/2026, 7:22:24 AM

> **Thoughts:**
>
> - Thinking about your request
> - Exploring GrokBot inter-agent communication protocols
> - Searched web - Grok Bot bots message each other protocol group chat handoff site:docs.x.ai
> - Searched web - Grok Bot inter-agent communication how bots talk to each other speculation
> - Searched web - "Grok Bot" OR GrokBot "message each other" OR "bot to bot" OR "group chat" architecture
> - Searched web - site:reddit.com Grok Bot agents communicate OR multi-agent protocol
> - Searched web - pi-cross-session vs pi-subagents vs control socket peer messaging
> - Researching GrokBot inter-agent communication protocols
> - Searched web - pi-agents-talk-to-each-other npm rooms control

I’ll go after the protocol itself: what xAI has published, what people infer from the live product, and which Pi packages actually implement peer messaging versus which ones only look like they do.Official collab docs and the reverse-engineered replicas are the remaining sources for the wire-level behavior people think is happening.MCP is not the path. I over-weighted it last time. For Bots on **one computer talking to each other**, MCP is the wrong layer. There are installable Pi packages that already do peer discovery and send. None of them is GrokBot’s protocol. The gap is semantics and lifecycle, not “you must invent a wire format.”

---

## What xAI has actually published

They have not published a wire spec, RPC schema, handle format, or queue algorithm. What they published is a **product protocol**: who can talk, how a message is treated, what is visible, and what is serialized. That is enough to emulate the behavior. It is not enough to clone the bytes. [Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)

Official facts, compressed:

1. **Three conversation kinds.** User↔Bot DM. Bot↔Bot direct handoff. Group of 2–6 Bots plus you. One Bot can sit in many groups; the Bot is a persona, not a copy per chat. [Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)
2. **Handoff is async wake.** “A Bot can send an asynchronous message to another Bot. The receiving Bot wakes, handles the request, and can reply later. You can see the handoff in the conversation.” That sentence is the whole published A2A contract. [Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)
3. **User DMs preempt.** A message from you outranks background work and can redirect the current turn. “Stop now” ends the turn. It does not roll back work already done. [Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)
4. **One turn per Bot.** Parallelism is N Bots, not N turns on one Bot. Each Bot has one screen and one computer-use task at a time. Routines run on that same lane, which is why staff tell people to give schedules their own Bot. [Docs](https://docs.x.ai/grok-bot/overview)
5. **Payload split.** Context that must persist across Bots goes through **shared files** (`/workspace`), **browser sessions**, **direct handoffs**, and **group messages**. Memory does not. Memory stays with the Bot. Group handoffs are text-only; images go DM-to-DM. Your group messages can carry attachments. [Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)
6. **Routing is descriptions + mentions, not a workflow graph.** `@Researcher` / `@Writer` / `@everyone`. Unguided group messages let participating Bots decide who answers. Docs tell you to keep a single owner at each stage so parallel handoffs do not duplicate work. [Docs](https://docs.x.ai/grok-bot/bots)
7. **Visibility is first-class.** Handoffs show up in the transcript. Sidebar states: needs attention, unread, working/typing. Notifications fire when a Bot finishes or needs input. Groups do not get the per-Bot notification switch. [Docs](https://docs.x.ai/grok-bot/settings-and-notifications)
8. **No public A2A API.** Someone on X asked them to open the bot communication protocol so Codex/Claude Code could talk to Grok Bots. That request exists because the protocol is closed. Third parties who need *cross-product* A2A bolt on MCP rooms (AgentCouch) or a two-bot shared inbox Worker. That is a different problem from your same-Harness replica. [Agentcouch](https://agentcouch.dev/agents/connect-grok-bot-to-other-agents)

Do not confuse this with xAI’s **multi-agent research** model (`chatroom_send` + `wait`, 4 or 16 internal agents, encrypted sub-agent traces). That is a single inference graph, not GrokBot. People mix them constantly. [X](https://x.ai/docs/developers/model-capabilities/text/multi-agent)

---

## What people are inferring (not official)

This is forum / replica / operator reconstruction. Treat it as a working theory that matches the docs and the live app, not as leaked source.

**OpenMausBot’s “verified against docs” read** is the cleanest public model I found: membership fans out; execution is serialized per Bot; Bot→Bot is a wake, not a second lane; in a group the host wakes members in turn; there is no queue UI; messaging a busy Bot redirects it; routines share the Bot’s lane. [Raw](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md)

**OpenGrokBot** goes further and implements a guessed internals stack. Useful as a design catalog, not as evidence they saw xAI’s code:

- three priority lanes: user > agent > background
- A2A = fire-and-forget + wake + optional priority steer
- delivery ack ≠ work-done ack
- both transcripts mirror the exchange
- group chat = bounded rounds, @mention routing, pass-convergence, user supersede
- idempotent accept ledger (nonce + digest) so send is durable before the receiver runs
- DM preemption re-drives at-least-once, with a loop guard

That last cluster (lanes, accept-then-execute, ack vs result) is what almost every serious replica converges on, because the product *behaves* that way even though the docs never say “JSON-RPC” or “handle.” [GitHub](https://github.com/LING71671/open-grokbot/blob/main/README.md)

**Operators on X** are not talking about sockets. They talk about: typed route/kind/urgency sitting in front of handoffs; a ledger of receipts so a silent Bot is visible; outer-loop Bot writes a prompt, inner-loop Bot executes; “one job per Bot, every receipt graded.” That is policy on top of the same wake primitive. [X](https://x.com/ssbrouhard/status/2101192698539511985)

**MindStudio-style writeups** claim a Bot “scans descriptions and forwards.” Official docs never say there is an automatic matcher. What exists is: roster with name + description, tools the model can use to message another Bot, and group @mentions. The “scan” is the model reading the roster, not a hidden router. Don’t build a magic dispatcher unless you want one. GrokBot’s design essay is explicit that coordinating Bots should do the routing so the user does not get a dashboard. [Mindstudio](https://www.mindstudio.ai/blog/grok-bot-ai-agent-fleet)

**Cross-user** is a separate product surface (templates, team accounts, Firecracker isolation per user). Ignore it for your Harness replica. [Docs](https://docs.x.ai/grok-bot/security-faq)

---

## The spec you should emulate

This is a behavioral spec. Implement these invariants and you have GrokBot-shaped A2A. The transport can be files, sockets, or Redis.

### Identities

```text
BotId        durable, opaque, never reused as a display name
Conversation DM(bot) | Group(groupId, members[2..6]) | System
TurnId       one in-flight turn per Bot, globally
Handle       returned to sender at accept time, not at completion
Seq          per-conversation monotonic id for transcript tails
```

A BotId survives process death. A live socket id does not. That is the first place Pi packages fail GrokBot.

### Message kinds

| Kind | From → To | Preempts current turn? | Visible where |
|---|---|---|---|
| `user_dm` | you → Bot | Yes. Redirects. | That Bot’s DM |
| `user_stop` | you → Bot | Yes. Abort turn. No undo. | That Bot’s DM |
| `a2a_handoff` | Bot → Bot | No by default. Wake or queue. | Sender transcript + receiver transcript |
| `group_post` | you or Bot → group | No. Host wakes members. | Group transcript |
| `group_mention` | you or Bot → group + subset | Wake only mentioned Bots | Group transcript |
| `steer` | you or privileged Bot → busy Bot | Soft inject, do not reset goal | Receiver transcript |
| `result` | Bot → original conversation | n/a | Wherever the handle was issued |

Official docs only name user DM, stop, async handoff, and group/@. `steer` vs `handoff` is the replica community’s split of “user can redirect” vs “Bot cannot steal the lane.” Keep that split. If every A2A message aborts the receiver, specialists cannot finish work.

### Accept vs complete

This is the piece people miss, and it is why Grok-side tools look like `send` + `await` instead of one blocking call.

```text
send(to, body, files?, mode, on_busy)
  → { handle, accepted: true }     // durable. receiver may still be asleep
  → { handle, accepted: false, reason: busy|unknown|refused }

await(handle)
  → pending | blocked(question|auth) | done(result) | failed
```

An acknowledgement (“got it, working”) is **not** `done`. Keep awaiting until the receiver’s turn ends or it parks on HITL. If you only copy `send_pi_message`, you will think the protocol works and then lose every long job.

Modes that match the product:

| mode | meaning |
|---|---|
| `async` | accept, return handle, do not wait |
| `fire_and_forget` | accept, no handle |
| `blocking` | wait in-process — do not use for real work |

Busy policy:

| on_busy | GrokBot-like behavior |
|---|---|
| `queue` | closest to “wakes later” |
| `supersede` | closest to user DM redirect; **do not give this to peer Bots by default** |
| `reject` | honest “I am mid-turn” |

Default for Bot→Bot: `queue`. Default for you→Bot: `supersede`.

### Priority lanes (inferred, implement anyway)

Per Bot, one scheduler:

1. `user_dm` / `user_stop`
2. `steer` from you
3. `a2a_handoff` / `group_mention`
4. routine / event wake

Only one of these is *running*. The others sit in a durable inbox on disk. That inbox is the protocol. The socket is just how you poke a live process.

### What moves across the wire vs what does not

**On the message:** text, conversation id, sender BotId, handle, optional path list on the shared computer, mention list.

**Not on the message:** the sender’s memory, the sender’s transcript, raw tokens, tool results. Point at `/workspace/...` instead. Official docs say this in different words: files and handoffs move context; memory stays. Replicas that dump full transcripts into A2A recreate the “swollen context” problem GrokBot was designed to avoid. `pi-peer` is explicit: “A message is text and nothing else.” That constraint is correct. [GitHub](https://github.com/shift-labs-ai/pi-peer)

### Group chat is not N DMs

A group needs a **host** (your Harness, not a Bot):

1. Append the post to the group log.
2. Compute wake set (`@Bot` subset, or all members if unguided — keep this conservative).
3. Wake members **one at a time** or with a round cap. Official text does not specify round-robin, but every replica that skipped a host got ping-pong.
4. Stop the round on user supersede, pass-convergence, or cap.
5. Bot→group body is text. Binary goes DM + a path in the group post.

### Wake of a sleeping Bot

This is the GrokBot property Pi packages almost never have. If Researcher is not running, a handoff still accepts. The supervisor starts `pi --mode rpc --name researcher` (or sends on its control socket if the process is up), drains the inbox, runs one turn, writes `result` against the handle, goes idle.

Without that supervisor, you only have “chat windows that happen to be open,” which is not GrokBot.

---

## Out of the box on Pi — ranked for *this* protocol

Not E5. These are the real options. All of them assume **processes already running on one machine**, unless noted.

### Closest: install and use

**`pi-cross-session`**  
Discovery file + Unix socket per instance. Tools: `list_pi`, `send_pi_message`. Busy/idle is real. Inbound accept/refuse. Inspired by Claude Code cross-session, not GrokBot. No durable BotId, no handle, no await-until-done, no wake-if-asleep, no group host. Best **data plane** if both Bots are live. [Npmjs](https://www.npmjs.com/package/pi-cross-session?activeTab=code)

**`@shift-labs/pi-peer`**  
Same idea, file inbox. Same-machine default; Redis if you later split hosts. Status includes `not running`, which is closer to a roster. Still text-only send, no handle/await. Strong choice if you want one package and maybe multi-host later. [GitHub](https://github.com/shift-labs-ai/pi-peer)

**`pi-agents-talk-to-each-other`**  
File rooms under `~/.pi/agent/rooms/`. `room_list_agents`, `room_send_message`, heartbeats (idle/busy/tool/offline), **follow-up queue if the target is busy**. Optional `room_read_agent_history` behind a control flag. This is the closest *shape* to group + roster + queue. Agent ids die on process restart. File polling, not sockets. No supervisor. [Pi](https://pi.dev/packages/pi-agents-talk-to-each-other)

**Ronacher `control` / `crosstalk`**  
Per-session Unix socket with `send(steer|follow_up)`, `abort`, `subscribe turn_end`, `get_message`. This is the right primitive for **`await`**. Pair it with a roster. Do not use it as the only discovery mechanism.

### Useful but the wrong abstraction

**`pi-subagents` and every fork**  
Parent spawns a child, child dies, result returns. That is delegation, not a teammate. Use it *inside* a Bot. Never as the Bot network.

**`pi-subagents` intercom / `contact_supervisor`**  
1:1 broker between live sessions plus child→parent escalate. Fine as an extra channel. Still live-process-only.

**`pi-messenger-swarm`**  
Durable channels (`#memory` + per-session rooms), task claim/progress/done, no daemon. Excellent as the **group log and artifact bus**. Weak as DM+handle+wake.

**`pi-mesh`**  
Peers + file reservations + `mesh_send`. Coordination for not stepping on the same files. Not a Bot roster.

**`@giladbarnea/pi-simple-team`**  
Spawns a talking team from one session, then gets out of the way. Demo-friendly. Not long-lived named Bots.

### When MCP *is* appropriate (E5)

Only if the other party is **not** a Pi process on your computer: another user’s Grok Bot, Claude Code on a laptop, a phone agent, a Cloudflare Worker inbox. That is AgentCouch / `grok-bot-mcp-connector` territory. You do not need it to replicate GrokBot-on-your-Harness. Using MCP for local A2A adds auth, tool-schema tax, and another failure domain for no semantic gain. [Agentcouch](https://agentcouch.dev/agents/connect-grok-bot-to-other-agents)

ACP is also the wrong comparison. ACP is editor ↔ agent. GrokBot A2A is agent ↔ agent on one account.

---

## What you actually do

Install one live-process bus. Write a thin control plane that sits in front of it. That control plane *is* the GrokBot protocol.

Recommended pairing:

| Layer | Use |
|---|---|
| Roster + handles + inbox + supervisor | You write. SQLite or JSON under the shared computer. |
| Live poke | `pi-cross-session` or `control` sockets |
| Group log | `pi-agents-talk-to-each-other` rooms or `pi-messenger-swarm` channels |
| Sleeping Bot | systemd/launchd starts `pi --mode rpc` and drains inbox |
| Bulk artifacts | shared filesystem, never the message body |

Minimum tools on every Bot, named after the product not after Pi:

```text
bot_search_agents(query, status?)
bot_send_prompt(agent_id, prompt, mode=async, on_busy=queue, paths?)
bot_await_turn(agent_id, handle)
bot_get_agent_transcript_tail(agent_id, limit, before_seq?)
```

`bot_send_prompt` implementation:

1. Resolve `agent_id` in the roster (not in the live peer list).
2. Append `{handle, from, body, paths, conversation}` to that Bot’s inbox file. fsync. This is accept.
3. If a live socket exists, poke it (`send` follow_up, or `steer` only for user DMs).
4. Else mark `needs_wake`. Supervisor starts the process.
5. Return `{handle}` immediately.

`bot_await_turn` implementation:

1. Watch that handle’s state file, or `subscribe turn_end` on the control socket.
2. If the transcript grows by an ack-only assistant message, keep waiting.
3. Return when the turn ends, or when the Bot posts a question/approval (that is a terminal outcome for this wait).

That is the protocol. `pi-cross-session` already does step 3 for live peers. `pi-agents-talk-to-each-other` already does a sloppy version of step 2 (busy → follow-up). Nobody does 1+4+await-until-done+durable BotId together. That bundle is small. It is not a new comms stack.

---

## Direct answer to your last question

You are not stuck creating a protocol from nothing, and you should not use MCP as the local bus.

- **Out of the box:** several Pi extensions already let live sessions list each other and send text. Best starting installs: `pi-cross-session` or `@shift-labs/pi-peer`, plus `pi-agents-talk-to-each-other` if you want rooms.
- **Not out of the box:** durable Bot identity, accept-vs-complete handles, await-until-turn-end, user-preempt vs bot-queue, wake of a process that is off, group host with 2–6 members, text-only group + file DM for binaries.
- **What GrokBot is, underneath the UI:** a per-Bot serial lane, a durable mailbox, a supervisor that can start the lane, and transcripts that mirror the handoff. The unpublished part is the hosted scheduler and the desktop/mobile surface, not a magic transport.

If you want a next concrete step, it is: stand up two named Pi RPC processes on the Harness, install `pi-cross-session`, wrap it with a 100-line inbox+handle file, and get `send`/`await` working before you touch group chat or MCP.

> **Sources:**
>
> 1. [Message and collaborate | SpaceXAI Docs](https://docs.x.ai/grok-bot/chat-and-collaboration)
> 2. [Grok Bot | SpaceXAI Docs](https://docs.x.ai/grok-bot/overview)
> 3. [Frequently asked questions | SpaceXAI Docs](https://docs.x.ai/grok-bot/faq)
> 4. [https://docs.x.ai/llms-full.txt](https://docs.x.ai/llms-full.txt)
> 5. [Settings and notifications | SpaceXAI Docs](https://docs.x.ai/grok-bot/settings-and-notifications)
> 6. [Create and manage Bots | SpaceXAI Docs](https://docs.x.ai/grok-bot/bots)
> 7. [Grok Bot security FAQ | SpaceXAI Docs](https://docs.x.ai/grok-bot/security-faq)
> 8. [Grok Bot for Mobile | SpaceXAI Docs](https://docs.x.ai/grok-bot/mobile)
> 9. [Approvals, security, and privacy | SpaceXAI Docs](https://docs.x.ai/grok-bot/approvals-security-and-privacy)
> 10. [How can Grok Bot talk to other AI agents? | AgentCouch](https://agentcouch.dev/agents/connect-grok-bot-to-other-agents)
> 11. [Multi Agent | SpaceXAI Docs](https://x.ai/docs/developers/model-capabilities/text/multi-agent)
> 12. [Grok Bot | SpaceXAI Docs](https://x.ai/docs/grok-bot)
> 13. [OpenGrokBot/docs/multi-bot.md at main · wolfqing/OpenGrokBot · GitHub](https://github.com/wolfqing/OpenGrokBot/blob/main/docs/multi-bot.md)
> 14. [Grok Bot 101 · Grok Bot Guides](https://x.ai/bot/guides/grok-bot-101)
> 15. [The Outer Loop / Inner Loop Trick That Makes Grok Bot 10x More Effective | SMF Clearinghouse](https://www.smfclearinghouse.com/blog/grok-bot-outer-loop-inner-loop-workflow)
> 16. [Grok 4.20: The Four-Agent Parallel Architecture That Changes Inference | AI Daily PhD](https://aidaily.phd/briefing/e2b5/)
> 17. [Meet Grok Bot: xAI's Answer to the Agent Problem](https://blog.openreplay.com/grok-bot-xai-agent-problem/)
> 18. [What Is Grok Bot? xAI's Multi-Agent Assistant Explained | MindStudio](https://www.mindstudio.ai/blog/grok-bot-ai-agent-fleet)
> 19. [Grok Bot for mobile app development · Grok Bot Guides](https://x.ai/bot/guides/grok-bot-for-mobile-app-development)
> 20. [https://r.jina.ai/https:/docs.x.ai/grok-bot/chat-and-collaboration](https://r.jina.ai/https:/docs.x.ai/grok-bot/chat-and-collaboration)
> 21. [open-grokbot/README.md at main · LING71671/open-grokbot · GitHub](https://github.com/LING71671/open-grokbot/blob/main/README.md)
> 22. [What Grok Bot is (and what it isn’t) — grokbot.guru](https://grokbot.guru/what-grok-bot-is/)
> 23. [grok-bot-discord/docs/architecture.md at main · davefmurray/grok-bot-discord · GitHub](https://github.com/davefmurray/grok-bot-discord/blob/main/docs/architecture.md)
> 24. [GitHub - chipherndon/grok-bot-mcp-connector: Shared inbox MCP so two Grok Bots can message each other · GitHub](https://github.com/chipherndon/grok-bot-mcp-connector)
> 25. [grok-bot/README.md at main · grok-bot-app/grok-bot · GitHub](https://github.com/grok-bot-app/grok-bot/blob/main/README.md)
> 26. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md)
> 27. [Reddit - The heart of the internet](https://www.reddit.com/r/whaaat_ai/comments/1w43o6n/grok_bots_own_docs_say_all_your_bots_share_one/)
> 28. [New open-source tool: hdp-grok – Add cryptographically verifiable human delegation to Grok agents](https://www.reddit.com/r/agenticthreats/comments/1s5vymu/new_opensource_tool_hdpgrok_add_cryptographically/)
> 29. [Reddit - The heart of the internet](https://www.reddit.com/r/grok/comments/1uve57p/i_built_a_telegram_bot_that_drives_grok_build/)
> 30. [Reddit - The heart of the internet](https://www.reddit.com/r/quo/comments/1wi0v0e/new_in_quo_connect_quo_to_grok_bot)
> 31. [Reddit - The heart of the internet](https://www.reddit.com/r/coolgithubprojects/comments/1v5s6v3/agent_disco_run_a_team_of_codex_and_grok_agents)
> 32. [Grok 4.20: Four Minds, One Voice : r/AIGuild](https://www.reddit.com/r/AIGuild/comments/1r8ktxx/grok_420_four_minds_one_voice/)
> 33. [Reddit - The heart of the internet](https://www.reddit.com/r/AISEOInsider/comments/1vmkouw/grok_bot_ai_makes_multiagent_automation_crazy_easy/)
> 34. [Reddit - The heart of the internet](https://reddit.com/r/OpenSourceAI/comments/1wjm6sd/the_real_agent_lockin_isnt_the_model_its_the/)
> 35. [pi-cross-session - npm](https://www.npmjs.com/package/pi-cross-session?activeTab=code)
> 36. [https://npm.io/package/pi-cross-session.md](https://npm.io/package/pi-cross-session.md)
> 37. [pi-subagents/README.md at main · nicobailon/pi-subagents · GitHub](https://github.com/nicobailon/pi-subagents/blob/main/README.md)
> 38. [GitHub - monotykamary/pi-messenger-swarm: Swarm-first multi-agent messaging and task orchestration extension for Pi · GitHub](https://github.com/monotykamary/pi-messenger-swarm)
> 39. [GitHub - shift-labs-ai/pi-peer: A pi extension that lets your pi sessions find and message each other · GitHub](https://github.com/shift-labs-ai/pi-peer)
> 40. [pi-cross-session | npm.io](https://npm.io/package/pi-cross-session)
> 41. [pi-agents-talk-to-each-other · Packages · Pi](https://pi.dev/packages/pi-agents-talk-to-each-other)
> 42. [pi-subagents/docs/intercom.md at main · fitchmultz/pi-subagents · GitHub](https://github.com/fitchmultz/pi-subagents/blob/main/docs/intercom.md)
> 43. [https://raw.githubusercontent.com/Timur00Kh/pi-agents-talk-to-each-other/main/README.md](https://raw.githubusercontent.com/Timur00Kh/pi-agents-talk-to-each-other/main/README.md)
> 44. [@giladbarnea/pi-simple-team - npm](https://www.npmjs.com/package/@giladbarnea/pi-simple-team)
> 45. [pi-mesh · Packages · Pi](https://pi.dev/packages/pi-mesh)

## Prompt:
9/19/2026, 7:37:34 AM

Okay, right now, after looking at projects like OpenGrokBot and OpenMausBot, I feel like something that is becoming more and more of a possibility is that I should make my own Harness completely from scratch and just reverse engineer it. Instead of creating and building something off of Pi Coding Agent, this wouldn't really be that difficult per se, because I'd still be using a model to try and one-shot it and then refine it after the fact. This would be a high-performing coding model or whatever.
What I am concerned about, and what I want your opinion on, is: do you think this is a good idea, or do you think I should build it on top of Pi Coding Agent? Just some insight: I do not plan on running this on my computer. This is something that I'm using for my AI consulting business, and I'm essentially going to be creating an application and able to serve my clients a way to not give them a Grok interface. I'm giving them something where they have an interface and access to these agentic systems, but they don't get to really see what's going on behind the scenes. They'll have access in their own way that I give them.
This thing that I'm trying to make is essentially going to be the runtime that powers all of my client AI systems that are servicing me. They're going to be running on either a server that I own or a server that I'm paying for through AWS.

## Response:
9/19/2026, 7:37:34 AM

> **Thoughts:**
>
> - Thinking about your request
> - Evaluating the feasibility of building a custom AI harness
> - Assessing the feasibility of building a custom AI harness
> - Architecting the custom AI runtime

Build the **product** yourself. Do not one-shot a **harness**. Those are different jobs, and mixing them up is how a consulting runtime turns into an unpaid infrastructure company.

Pi is the wrong *product* for what you described. A greenfield agent loop is the wrong *bet* for what you described. The thing you actually need to own is the control plane that GrokBot treats as the product: roster, lanes, handoffs, routines, per-client computer, approvals, and a UI that never looks like a coding agent.

## What you are actually selling

Clients will not pay you for a better `/handoff` or a Unix socket. They pay for: named workers that keep doing the job on a machine they never SSH into, hand work to each other without the client becoming the router, stop at approval boundaries, and show a clean surface. That surface is yours. The tool loop behind it is a commodity.

Pi is a single-user terminal coding agent with a plugin ABI. OpenGrokBot and OpenMausBot are architectural studies of GrokBot’s concurrency and A2A behavior. Neither is a multi-tenant runtime you put on AWS and bill against. Using either as the thing clients “run on” means you inherit someone else’s session file format, trust model, and release cadence, then spend the next year fighting it in front of people who should never know it exists.

## Why “one-shot a harness” is the attractive bad idea

A strong coding model will give you a demo in a weekend: send prompt, call tools, stream tokens, save JSONL. That demo is not the harness. The harness is everything that breaks on the second client and the third week:

- Provider differences (tool-call IDs, partial JSON, cache breakpoints, abort mid-stream)
- Compaction that does not destroy Bot identity
- One-turn-per-Bot scheduling when two handoffs and a routine hit at once
- Durable accept vs complete (handles that survive process death)
- Tool timeouts, hung browsers, leaked child processes
- Approval gates that cannot be socially engineered by a Bot-to-Bot message
- Per-tenant secrets that never appear in transcripts
- Replay, idempotency, and “which receipt is missing”
- Compaction / context accounting you can bill and debug

OpenGrokBot’s README is a map of that list. It is also a warning: they needed a coordinator process, three planes, a scheduler with lanes, an accept ledger, group-round caps, a cloud-agent bridge, supervision with exit codes. That is months of systems work even when you already know the design. A one-shot produces the nouns and none of the failure handling. You will then debug the loop instead of shipping client interfaces.

You already know the protocol you want. Rewriting `read`/`write`/`bash` does not get you closer to it.

## Why “just extend Pi” is the other trap

Pi is excellent if *you* are the user and the computer is one box. Your case is the opposite:

- You are not the end user. The client is. They should not see Pi, sessions, `/reload`, or extension errors.
- It will not run on their laptop. It runs on a server you own or rent. Pi’s TUI, OSC notifications, Ghostty footers, and `~/.pi/agent/` layout are dead weight.
- “Shared computer” is correct **inside one client workspace**. It is malpractice **across clients**. xAI isolates users with a Firecracker microVM per account. If two consulting clients share a Pi process or a disk, you have built a data-leak product.
- Pi’s extension ecosystem optimizes for a developer’s personal agent. You would spend your time turning off coding-agent assumptions (repo cwd, git guards, plan mode) instead of building roster/A2A/routines.
- Your availability now depends on `@earendil-works/pi-coding-agent` minors. That is a bad dependency for a billed runtime.

Use Pi as a **reference implementation and, optionally, as an embeddable session object**. Do not use it as the application.

## The split that actually fits the business

Three layers. Only one of them should be novel.

**1. Client UI and policy (you own this)**  
Whatever they are allowed to see: Bots, group threads, approvals, artifact links, “needs attention.” No tool traces unless you choose to show a sanitized action log. This is the product they think they bought.

**2. Control plane (you own this — this is the GrokBot replica)**  
Durable Bot records, per-Bot serial lane, inbox + handles, supervisor that can start a sleeping worker, group host (2–6), routines as wakes on that lane, connector facade, approval bus. Persist it in Postgres or SQLite with object storage for artifacts. This is small, well-specified, and you already have the spec from the last two turns. This is also the only piece competitors cannot npm-install.

**3. Worker runtime (borrow, do not invent)**  
Each in-flight turn is: system + memory + tools + model stream + tool execution on **that tenant’s computer**. Candidates, in order of sanity:

- Embed Pi’s `AgentSession` SDK *inside your worker process* and ignore the CLI/TUI entirely. You get a battle-tested loop without shipping Pi to clients.
- Or use any other mature loop you already trust (Claude Agent SDK, a thin custom runner on the Responses/Anthropic APIs). Pick one and freeze it.
- Do not vendor OpenGrokBot as the production runner. Steal its *invariants* (lanes, accept-then-execute, group caps, ack ≠ done). Leave their process topology alone unless you want to maintain it.

**4. Computer (infrastructure, not an extension)**  
Per client, not per Bot: a container or small VM, a volume, a browser profile, secrets injected at start. All of that client’s Bots share that computer — that is the GrokBot property that makes handoffs cheap. Different clients never share it. On AWS that is ECS/Fargate or a warm pool of VMs plus a network policy, not a clever Pi package.

## Opinion, stated plainly

For a consulting runtime on your metal or AWS, with a hidden interior and a client-facing shell:

- **Do not** start a new harness from a one-shot. You will recreate Pi’s first year of bugs with none of the users who already found them.
- **Do not** ship Pi-the-CLI as the system. You will spend the engagement explaining why a terminal agent is the backend.
- **Do** write the control plane and the client UI from scratch. That is the company.
- **Do** treat OpenGrokBot / OpenMausBot as design notes for lanes and wakes, not as a foundation.
- **Do** put one mature tool loop under the workers so you can charge for outcomes next month instead of debugging streaming JSON.

The communication protocol you like is not a reason to rewrite the model adapter. It is a mailbox, a scheduler, and a supervisor. That is a few thousand lines if you are disciplined about what a message is allowed to contain. The danger is letting “from scratch” expand until it includes providers, browsers, compaction, and a desktop. That expansion is how this stops being a consulting product and becomes an unpaid xAI.

If you want a decision rule: if a component is visible to the client or defines how Bots relate, you write it. If a component turns tokens into tool calls on a filesystem, you import it and pin the version.

## Prompt:
9/19/2026, 7:41:29 AM

Okay, what I'm getting from this, and what I'm not asking you about, is a UI. I'll figure that out later. I'm just specifically talking about the runtime and how everything's going to be done behind the scenes.
Should I run this on Pi? Is that how you're saying I should make it? Is that the best idea? I don't think there's any other open-source, very modular existing harnesses out there that I think would be a good basis to create this product on and that are as flexible as Pine. If I'm wrong, tell me about that.
Otherwise, I have to build it from scratch just because of the amount of customizability and control that I want to have and that I require in order for my client applications, novel client applications, to be built in the way that I want them to. It requires me to not be able to use something out of the box like Claude Agent SDK. That's terrible, and I don't use anything by that. I want something very complex and capable.

## Response:
9/19/2026, 7:41:29 AM

> **Thoughts:**
>
> - Thinking about your request
> - Searched web - open source agent harness comparison 2026 pi coding agent opencode openclaw goose
> - Searched web - earendil-works pi-coding-agent SDK AgentSession embed programmatic
> - Searched web - best open source coding agent harness extensible runtime 2026
> - Researching open-source agent harnesses for 2026

I’ll compare Pi to the other open harnesses that are actually modular enough to be a runtime, not a chat app, so the recommendation is about the worker loop—not the UI.You are not wrong that Pi is the most modular *open* loop in this category. You are mixing two different “use Pi” decisions. Only one of them is a good idea for a server-side consulting runtime.

## Direct answer

Do **not** run the product as the Pi CLI (`pi` TUI, `~/.pi/agent/`, community extension soup, one process per engineer).

Do **use Pi as the worker library**: `@earendil-works/pi-coding-agent` → `createAgentSession()`. One session object per Bot turn, on that tenant’s computer. Your process owns roster, lanes, mailboxes, routines, isolation, connectors. Pi owns: model adapters, streaming, tool dispatch, compaction, session tree, extension hooks. [Raw](https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/sdk.md)

That is the best basis that exists in the open. It is not the same as “building the product on Pi.” OpenClaw, Kimi Code, and Prime Agent already treated Pi that way — they are products sitting on Pi’s packages, not Pi reskins. [Tyolab](https://www.tyolab.com/blog/2026/06/13-the-coding-agent-shootout-and-the-best-harness-we-could-not-read)

Building the tool loop from scratch is the worse idea unless you have a concrete loop behavior Pi cannot express with `registerTool`, `on("tool_call")`, `on("session_before_compact")`, custom `SessionManager`, and a custom system prompt. GrokBot-style A2A is not such a behavior. It lives *above* the loop.

## You were not missing a secret better harness

The field is crowded. Almost all of it is the wrong shape for “hidden runtime under novel client apps.”

| Thing | What it actually is | Fit as *your* worker |
|---|---|---|
| **Pi SDK** | Tiny core (4 tools, short prompt), TypeScript extension ABI, embeddable `AgentSession`, RPC if you want a subprocess | Best open fit |
| **OpenCode** | Full coding *product* (TUI + desktop + IDE), 75+ providers, biggest star count | Strong agent, weak embed. Built as an app, not a library you hide. |
| **OpenClaw / Hermes** | Personal assistant platforms (channels, voice, gateway). OpenClaw already embeds Pi. | You would be inheriting a messenger product, then tearing it out. |
| **Goose** | LF-governed, Rust, MCP-heavy, desktop+CLI | Good automation engine, not a minimal embeddable loop. |
| **OpenHands** | Autonomous SWE agent, event stream, containers | Good if the only job is “repo agent in a sandbox.” Heavy and coding-shaped. |
| **Codex CLI** | Best open sandbox story (Seatbelt/Landlock), Apache-2.0 | Fine worker if you accept its session/tool conventions. Less of an extension ABI than Pi. |
| **Cline SDK** | Extracted coding-agent runtime, Apache-2.0, plugins | Real alternative to Pi-as-library. Still a *coding* harness with IDE DNA. |
| **DeepSeek DSH** | Plugin-everything monorepo, presets, sandbox, web UI | Capable, new, DeepSeek-centered defaults. More product than scalpel. |
| **Claude Agent SDK** | You already rejected it | Correct rejection for model-lock and shape. |

Nothing else in the open has Pi’s combination of: smallest default surface, in-process TypeScript extensions that can replace tools and intercept every lifecycle event, and a documented embed path that does not drag a TUI with it. That is why people who *build harnesses* keep forking or embedding Pi instead of OpenCode. OpenCode wins as a daily driver. Pi wins as infrastructure. [Tyolab](https://www.tyolab.com/blog/2026/06/13-the-coding-agent-shootout-and-the-best-harness-we-could-not-read)

If you later hate Pi’s session file format or compaction, you replace `SessionManager` and the compact hook. You do not rewrite Anthropic-stream-to-tool-call.

## What “customizability I require” actually maps to

Most of what you have been specifying is **not harness-core**:

- Named Bots, search, send, await, handles  
- Per-Bot serial lane and busy policy  
- Group host  
- Routines that wake a sleeping worker  
- Per-client computer + shared-within-tenant FS  
- Connector facade and approval bus  
- Novel tools per client engagement  

All of that is your code either way. Pi does not block it. A from-scratch loop does not accelerate it. The loop only needs to: accept a prompt, emit tool calls, run *your* tools in *that tenant’s* cwd, stream events, compact when you say so.

Pi’s extension API is how you inject client-novel tools without forking the runner. That is the flexibility you were pointing at. You do not get more of it by writing `while (true) { const r = await model.stream(...) }` again.

You *would* outgrow Pi if you needed, for example:

- A non-Node worker (Rust/Go only)  
- A radically different context representation (not messages + tool results)  
- Multi-model debate inside one turn as a first-class runtime primitive  
- Hard real-time or GPU-side tool execution  

None of that is required for GrokBot-class client systems.

## How to run it on a server you own

Per tenant: one computer (container/VM + volume).  
Per Bot: one durable inbox + one `AgentSession` when a turn is running.  
Supervisor: if inbox nonempty and no live session, start a worker, `session.prompt(...)`, persist events, exit or idle.  
Handoff: write mailbox row, poke or start the other worker. Do not use `pi-subagents` as the Bot network.

Pin `@earendil-works/pi-coding-agent`. Load **your** extensions only — roster tools, connectors, policy gates — from a path you control. Do not `pi install npm:oh-my-pi`. That is how the CLI ecosystem leaks into a billed runtime.

RPC mode (`pi --mode rpc`) is the alternative if you want process isolation per Bot without linking the SDK. Same loop, subprocess boundary. Use that when you do not want a hung browser in worker A to kill worker B. SDK in-process is simpler to start.

## When from-scratch would be justified

Only after you have shipped two client systems on the embedded loop and hit a wall the hooks cannot absorb. At that point you have a real spec for “our loop.” One-shotting it now, because OpenGrokBot looks complete in a README, gives you a second-rate Pi plus a year of provider edge cases.

So: yes, Pi — as the hidden worker, not as the product. There is not a more flexible open modular basis that is actually a library. The complexity you want lives in the control plane and the per-client tools. Put it there.

> **Sources:**
>
> 1. [OpenCode vs pi: A Detailed Comparison of AI Coding Agents in 2026](https://openalternative.co/compare/opencode/vs/pi)
> 2. [Agent Harness 2026: OpenClaw vs Hermes vs Pi Compared | Blog](https://claw4science.org/blog/agent-harness-three-way)
> 3. [OpenCode vs Goose (June 2026): 172k-Star Terminal Agent vs Linux Foundation's Rust Platform](https://www.morphllm.com/comparisons/opencode-vs-goose)
> 4. [The Harness, Not the Model: Ten Coding Agents Compared](https://rohitghumare.com/blog/coding-agent-harnesses/)
> 5. [AI Agent Harness Comparison: DeepSeek Harness vs Pi vs OpenCode vs Hermes vs Claude Code - Tencent Cloud](https://www.tencentcloud.com/techpedia/147665)
> 6. [AI Coding Harnesses in 2026: Claude Code, Codex, Antigravity, Goose, OpenCode, and Pi](https://danoprean.com/posts/claude-code-vs-goose-vs-opencode-vs-pi-2026/)
> 7. [Best Open Source Agent Harness: Top 5 Projects Compared for 2026](https://www.truefoundry.com/blog/best-open-source-agent-harness)
> 8. [Top 10 AI Agent Harnesses — Open vs Closed 2026 | explainx.ai Blog | explainx.ai](https://explainx.ai/blog/top-10-open-closed-source-agent-harnesses-2026)
> 9. [The Coding Agent Shootout and the Best Harness We Could Not Read](https://www.tyolab.com/blog/2026/06/13-the-coding-agent-shootout-and-the-best-harness-we-could-not-read)
> 10. [State of Agentic Harnesses — June 2026 · zero8.dev](https://zero8.dev/blog/state-of-agentic-harnesses-june-2026)
> 11. [8 Best Open Source CLI Coding Agents (2026)](https://thelinter.dev/articles/open-source-cli-coding-agents)
> 12. [OpenCode vs Pi Agent: Which Terminal Coding Agent Should You Use?](https://www.bitdoze.com/opencode-vs-pi-agent/)
> 13. [https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/sdk.md](https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/sdk.md)
> 14. [pi/packages/coding-agent/examples/sdk at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/sdk)
> 15. [pi/packages/coding-agent/examples/sdk/01-minimal.ts at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/sdk/01-minimal.ts)
> 16. [pi/packages/coding-agent/docs/sdk.md at main · earendil-works/pi · GitHub](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md)
> 17. [pi/packages/coding-agent/examples/sdk/13-session-runtime.ts at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/sdk/13-session-runtime.ts)
> 18. [pi/packages/coding-agent/examples at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples)
> 19. [pi/packages/coding-agent/examples/sdk/11-sessions.ts at main · earendil-works/pi · GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/sdk/11-sessions.ts)
> 20. [Cline SDK Review 2026: Open-Source Agent Runtime](https://blog.buildfastwithai.com/cline-sdk-review-agent-runtime-2026)
> 21. [Best Agent Harnesses 2026: A Builder's Field Guide](https://futureagi.com/blog/best-agent-harness/)
> 22. [Best Agent Harness in 2026: Top 5 Options Compared](https://www.truefoundry.com/blog/best-agent-harness-in-2026)
> 23. [DeepSeek Harness Explained: The Agent Runtime Behind DSH](https://www.orcarouter.ai/blog/deepseek-harness-explained)
> 24. [GitHub - RyanAlberts/best-of-Agent-Harnesses: 🏆 Curated, ranked list of AI agent harnesses (100+) — plus an MCP server, llms.txt & JSON so agents can recommend them too. Rescored weekly. · GitHub](https://github.com/RyanAlberts/best-of-Agent-Harnesses)
> 25. [8 Best AI Agent Harnesses in 2026: Performance, Cost, and Speed Compared | Composio](https://composio.dev/content/best-ai-agent-harnesses)

## Prompt:
9/19/2026, 7:52:14 AM

Now I want you to go back to the first chat where you gave me the response with the Type A through Type M extensions. You don't have to copy that structure at all because I think you were faulty in the reasoning and how you did that. What I do want to happen is revisit this, and we need to identify, based on the architecture that OpenMOS bot describes and implements, the different avenues that will have to be emulated through extensions.
I want you to read its documentation thoroughly because it has really good docs. I want to understand all of the different avenues that will have to be emulated through extensions. Some of those extensions exist already and can be used out of the box. Some of them have options like memory. I see memory is a really good avenue. There are a bunch of different ways that I could go on this, and I will have to explore those individually and find the ones that I want.
Some of these, maybe something like the bot identity rush, are very specific to the type of thing that I'm trying to create. It just will 100% not work if I want this to happen using something out of the box, so I will be required to make my own extension. I want you to compartmentalize and decompose the entire application and runtime that I'm aiming to create, then perform this operation on this and treat each decomposition as one of those three avenues. 

I want you to put a lot of effort into this operation.

## Response:
9/19/2026, 7:52:14 AM

> **Thoughts:**
>
> - Thinking about your request
> - Decomposing the OpenMausBot runtime architecture
> - Searched web - OpenMausBot milind-soni github documentation architecture
> - Searched web - site:github.com milind-soni OpenMausBot
> - Searched web - OpenMausBot docs grok bot concurrency messaging routines

I’ll start from OpenMausBot’s own docs and use that architecture as the decomposition, then classify each piece as reuse, choose-among-options, or write-it.The public docs map the product layers; next I’ll pull the harness, computer, rooms, approvals, and goal-mode specs so the decomposition matches what they actually implemented.OpenMausBot is useful here because it already split the problem the way a GrokBot replica has to split it: a **harness that owns processes**, and **drivers that run turns**. Their public model is six layers. Their implementation notes add the ones that actually hurt: a per-bot lane, wakes not second lanes, a permission broker, a recent-work brief that is not shared memory, routines that are wakes with receipts, computers that lease, goals that park instead of failing. That is the decomposition. UI is out. What follows is only runtime. [Docs](https://docs.openmausbot.com/docs)

Three avenues, used the same way every time:

- **Use existing** — pin it and configure it. Do not rewrite.
- **Choose among options** — several real implementations exist; the choice is product, not invention.
- **Write it** — nothing off the shelf implements the invariant you need. An extension or a harness module, not a prompt.

Pi itself is not an extension. It is the **engine driver** for a turn. Almost everything else sits around it.

---

## 0. Process topology

OpenMausBot is two processes: a renderer that speaks HTTP + one SSE stream, and a harness bound to loopback that owns every agent child, normalizes driver events to one NDJSON stream per thread, and runs the permission broker. Drivers are one file each (Claude stream-JSON, Codex JSON-RPC, ACP, Pi, …). Unknown drivers become “unavailable”; they do not take down the fleet. [GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/README.md)

Your version of this, on a server you own:

```
supervisor
  ├─ control plane   roster, inbox, handles, group host, routines, approvals
  ├─ event log       one canonical stream per thread
  └─ workers         one live AgentSession (Pi) per in-flight Bot turn
                         on that tenant's computer
```

**Write it.** There is no Pi package that is this supervisor. `pi --mode rpc` is a single worker, not a fleet. `pi-server` multiplexes sessions in one process; it is not multi-tenant and not a Bot roster. Steal OpenMausBot’s idea (canonical events, drivers degrade, loopback-trust if you ever expose a local sidecar). Do not vendor their Electron app.

---

## 1. Bot identity and roster

OpenMausBot: a Bot is identity + instructions + memory + approved skills + connected tools + computer preference. Threads hang off the Bot. Folders are labels, not sandboxes. Rooms are shared context, not folders. One Bot, many conversations. Membership fans out; the Bot is not copied per room. [Docs](https://docs.openmausbot.com/docs/features/bots-and-tasks)

You need the same record, plus GrokBot policy: standing purpose, no silent duplicates, search by name/description/status, durable id that survives process death.

**Write it.**  
`/sessions`, auto-rename, oh-my-pi agent markdown, `agent-pi` `agents/*.md` are session or prompt files. They are not a roster with idle/running, handles, and “this domain already has an owner.” The control-plane tools (`list_bots`, `create_bot`, `send_bot_message`, `wait_for_conversation` in OpenMausBot’s MCP server) are the shape. You implement that shape against your store. [GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/mcp-server.md)

---

## 2. Agent engine (the turn)

OpenMausBot does not run models itself for the main engines. It spawns CLIs and normalizes them. Pi is already one of those engines. ACP is how most others plug in. `openai-compat` covers a raw endpoint. Per-bot model, changeable when idle. [Docs](https://docs.openmausbot.com/docs/providers)

You already decided the worker is Pi’s `createAgentSession()`, not Claude’s SDK.

**Use existing:** `@earendil-works/pi-coding-agent` as the in-process (or RPC) turn runner. Compaction, streaming, tool dispatch, session tree come with it.

**Write it (thin):** a driver wrapper that (a) pins *your* extension set, (b) sets cwd to the tenant computer / working folder, (c) maps Pi events onto your canonical stream, (d) refuses to load random npm extensions. That wrapper is yours. The loop is not.

If a future client demands Codex-sandbox or Claude-CLI parity as the worker instead of Pi, that is a second driver behind the same wrapper. OpenMausBot’s SPI is the right pattern. You do not need it on day one.

---

## 3. Working folder vs computer vs memory directory

OpenMausBot separates three disks:

| Path | Whose | For |
|---|---|---|
| Working folder | thread or bot, often a repo | file tools for that job |
| Computer | per bot, changeable | browser / desktop / VPS / Box |
| `workspaces/<botId>/` | per bot | `MEMORY.md`, topic notes, daily log |

Contention on a physical computer, browser session, or shared project folder is reported, not interleaved. New local threads get separate working folders by default. Memory is single-writer; they require atomic temp→rename before they will even consider concurrent turns. [Raw](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md)

**Write it** (layout + leases).  
Pi’s `cwd` is one directory. It will not invent this split. Your supervisor sets `cwd` per turn and holds a lease: computer lock, working-folder lock, memory write lock. Without leases you will get two Bots editing one profile or one `MEMORY.md`.

The folders themselves are just directories. No extension required for “a folder exists.”

---

## 4. Conversations: DM threads, rooms, delegation

OpenMausBot’s current product language:

- **Thread** — independent conversation on one Bot. Own model snapshot, own approvals, own Stop. Up to three direct threads per Bot in their newer model; default concurrency plan is still *serial per Bot* with extra threads as opt-in behind leases.  
- **Room / group** — several Bots, shared brief, @mentions, host wakes members.  
- **Delegation** — bounded subtask, own activity, result returns to the originator. Not a new Bot.  
- **Goal** — durable objective on a Bot or a room; busy is `waiting.onBotId`, not failure; resume on idle. [Docs](https://docs.openmausbot.com/docs/features/bots-and-tasks)

That is three different runtimes people keep collapsing into “multi-agent”:

1. Peer handoff (Bot → Bot, durable teammates)  
2. Child delegation (task → result → die)  
3. Room round (host-sequenced wakes)

### 4a. Peer handoff and the lane

OpenMausBot’s documented GrokBot read, which they implemented toward: one current turn per Bot; user DM preempts; Bot→Bot is an async wake; group host wakes in turn; busy Bot is woken later, never skipped; wait cap then the round continues with a chip; routines share the Bot’s lane. [Raw](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md)

**Write it.** This is the product.  
Existing Pi buses (`pi-cross-session`, `pi-peer`, `pi-agents-talk-to-each-other`, control sockets) only move text between *live* processes. They do not: durable BotId, accept≠complete handle, wake a sleeping worker, user-preempt vs peer-queue, group host, wait caps, receipts.

You may **use existing** as the *live poke* under your mailbox (`send_pi_message` or a control-socket `follow_up` once the process is up). That is a transport adapter, not the protocol.

### 4b. Delegation (child)

**Choose among options.**  
`pi-subagents` (or `@tintinweb/pi-subagents` if you want fleet UI inside a worker) is the right primitive for “review this draft and return.” Official `subagent/` example is the minimal version. Do not use this for named teammates.

### 4c. Room host

**Write it.**  
`pi-agents-talk-to-each-other` rooms and `pi-messenger-swarm` channels are usable as the **append-only group log**. They are not a host that computes the wake set, bounds the round, and parks on a busy member. Goal-mode parking (`waiting.onBotId`) is the same module.

---

## 5. Scheduler / inbox / handles

OpenMausBot’s control verbs from their MCP surface are the spec: send to bot or channel, wait until settled or needs help, interrupt. Receipts on automations: queued, active, waiting, completed, missed, failed, cancelled. Acknowledgement is not completion. A turn parked on an approval card still occupies the lane. [GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/mcp-server.md)

**Write it.**  
Durable inbox per Bot, handle at accept time, `await` until turn-end or HITL, `on_busy` = queue for peers and supersede for the user. Persist in SQLite/Postgres on the tenant volume.  
`subscribe turn_end` on a control socket is an optional accelerator when the worker is live.

In-session `/loop` packages (`pi-scheduler`, `pi-schedule-prompt`, `@koltmcbride/pi-loop`) fire prompts inside an already-open session. They are not this scheduler. Do not confuse them.

---

## 6. Memory

OpenMausBot’s memory is the best published design in this family and you should copy the *invariants*, not necessarily their files:

- Per Bot, never a shared brain  
- `MEMORY.md` prefix loaded every turn (they cap 200 lines / 24 KB)  
- Topic files read on demand  
- Daily log the Bot writes, not stuffed into the prompt  
- Secret redaction before disk  
- Atomic writes  
- **Recent-work brief**: ~10 lines from *other* conversations in the last two days, so a room does not require merging memories  
- Journal outside the workspace so undo does not fight the Bot  
- `session_search` rather than pasting transcripts into A2A messages [Raw](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/memory.md)

**Choose among options** for the store and retrieval. The invariants above are yours either way.

| Option | What you get | Cost |
|---|---|---|
| Port their layout (`MEMORY.md` + `memory/*.md` + daily log) as a small Pi extension | Inspectable, matches OMB, easy to scope per `botId` | You write injection + redaction + cap |
| `pi-hermes-memory` | SQLite FTS5, consolidation, session search, secret scanning | Scope it per bot path or you get a shared brain |
| `@henryqw/pi-memory` | Capped MEMORY.md / USER.md | Closest to OMB with less code |
| `@amaster.ai/pi-memory-mem0` | Embeddings, hosted or self-hosted | Better recall, worse audit, another vendor |
| `gentle-engram` / shared brains | Cross-session one brain | Wrong isolation model |

Recommendation: start with the OpenMausBot file layout plus a `before_agent_start` injector and a redaction writer. Add FTS (`pi-hermes-memory` or a tiny SQLite index) when `session_search` is a real tool the model needs. Do not install three memory packs.

The recent-work brief is **write it** — no extension does “newest line from each other thread, 350 tokens, chip if a room would see a private DM.”

---

## 7. Permission broker and approvals

OpenMausBot: agents request; a broker turns that into Allow / Deny / answer; levels map onto the *engine’s* modes (Ask, auto-accept edits, approve-for-me, full access). Full access is elevated and not offered over the generic HTTP API. Read-only MCP tools stay non-bypassable. Delegation can carry Full access from a Chief of Staff onto the child thread only. A peer message is not user approval. Waiting-on-you still holds the lane. [Raw](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/approval-levels.md)

**Write it** (policy + broker API).  
Your clients will have different “consequential” sets (send-as-user, pay, publish, prod). That matrix is the business.

**Use existing** for the cheap gates inside a Pi worker:

- official `permission-gate.ts`, `protected-paths.ts`, `confirm-destructive.ts`
- `rpiv-ask-user-question` / official `questionnaire` for structured HITL
- `pi-auto-permissions` if you want a second model to review bash

Wire those so a deny or a question becomes `handle = blocked`, not a swallowed tool error. That last mapping is yours.

---

## 8. Connected apps (connectors)

OpenMausBot: Composio session, OAuth once, tools available across Bots, marketplace UI. Custom MCP servers as an escape hatch. Approvals still apply to writes. [GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/README.md)

**Choose among options.**

| Option | When |
|---|---|
| Composio via their Pi provider or via `pi-mcp-adapter` | You want 500+ apps and managed OAuth. Same choice OMB made. |
| `pi-mcp-adapter` only + servers you run | You want fewer apps and no Composio bill. |
| Per-engagement custom `registerTool` | Novel client system with an API that is the product |

**Write it:** a facade with two tools (`search_connected_tools`, `call_connected_tool`) and one auth path. Bots must not see Composio slugs in one tenant and raw MCP in another. Account-level connection, Bot-level allowlist — same split GrokBot and OMB both use.

---

## 9. Computer and browser

OpenMausBot placements: this machine, local VM, hardened container over SSH (BYO VPS), hosted Box desktop. Preview is not control; takeover is opt-in. Placement is per Bot and can change without changing the model. One computer-use task per screen. Shared logins inside one user are expected. [Docs](https://docs.openmausbot.com/docs/computers)

On your AWS/self-host story this becomes: **one computer per client tenant**, all of that tenant’s Bots share it, leases per screen.

**Write it** (lifecycle + lease + which worker gets which display). ECS/Fargate/VM + volume + browser profile is infrastructure, not a Pi extension.

**Choose among options** for the browser tool the worker calls:

- `pi-agent-browser-native` / `pi-agent-browser` — dedicated Chromium  
- `pi-browser-use` — attach to a real logged-in profile (closest to “the Marketplace bot already has the site open”)  
- official `ssh.ts` — tools execute on the remote computer  
- `@amaster.ai/pi-computer-use` — desktop-level click/type, later and sharper

Official `gondolin/` / `sandbox/` are isolation for a *coding* agent, not a tenant desktop. Use containers for tenants; use these only if a Bot needs an extra inner jail.

Teach-by-demonstration (GrokBot yes, OpenMausBot “not yet”) is **write it**, later. Do not block the runtime on it.

---

## 10. Automations: routines and webhooks

OpenMausBot: schedule or webhook → same queued executor → Bot’s current model/tools/computer → fresh execution context → report lands on a chosen thread. Receipts include missed. Catch-up: at most one missed run inside 12 hours, then mark missed and advance. Cron is five-field plus IANA timezone. Local executor dies if the app dies; they tell you to put the harness on a VPS for 24/7. Webhook receiver is a *separate* loopback port with only health + secret hooks — not the main API. [GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/routine-schedules.md)

GrokBot’s version of this is the same primitive (wake the owning Bot’s lane) with a computer that never sleeps.

**Write it** (routine record + receipts + destination thread + catch-up policy).  
This is standing duty ownership. Out-of-box `/loop` tools will double-fire and die with the process.

**Use existing** only as the OS timer that pokes your supervisor:

- `pi-tick` (launchd/cron) or systemd OnCalendar  
- a tiny HTTP listener for webhooks (OMB’s 8800 pattern is correct: do not hang hooks on the control API)

`@koltmcbride/pi-loop` event triggers are useful *inside* a live worker (fire on `turn_end`). They do not replace the supervisor.

---

## 11. Event log and transcript

OpenMausBot: one canonical stream per thread, NDJSON on disk, SSE out. MCP tools page transcripts and search them without screenshot pixels. Interrupt is a first-class verb.

**Write it** (schema + store + tail API).  
This is `bot_get_agent_transcript_tail` and every await implementation. Pi session files are a fine *worker-local* cache. They are not the product log (no handle, no from-bot/to-bot, no receipt states).

Search across transcripts: **choose among options** — Pi session FTS in hermes-memory, or your own index on the NDJSON. One search plane.

---

## 12. Skills

Pi skills (`SKILL.md`) already exist. OpenMausBot treats approved skills as part of the Bot profile. GrokBot adds demonstration→skill.

**Use existing:** Pi skills, loaded per Bot from that Bot’s skill directory. `pi-repo-skills` toggles if you want a checkbox UI later.

**Write it:** the allowlist (which skills this Bot may see) and, later, teach-mode compilation. Do not share one global skill dump across tenants or across Bots with different approval boundaries.

---

## 13. Isolation and tenancy

OpenMausBot is single-user: `~/.openmausbot`, config `0600`, companion sidecar if a phone must reach loopback. xAI isolates *users* with Firecracker; Bots inside a user share a computer.

Your consulting runtime is multi-user.

**Write it.**  
Per-client: volume, secrets, network policy, process namespace. Bots inside a client share that computer on purpose. Nothing in the Pi ecosystem is a tenant boundary. If you skip this, connectors and browser profiles leak across clients.

---

## How the three avenues look as a build list

**Use existing (pin, do not rewrite)**  
- Pi `createAgentSession` / `pi --mode rpc` as the turn engine  
- Pi skills  
- Official permission-gate / protected-paths / questionnaire (wired into your broker)  
- One live-poke bus if you want it: `pi-cross-session` or control sockets  
- OS cron/systemd or `pi-tick` as the wake clock  
- `agent-browser` (or the Pi wrapper you pick) for the screen tool  
- Composio or `pi-mcp-adapter` as the raw connector transport  

**Choose among options (decide per layer, then freeze)**  
- Memory store: OMB-style markdown vs hermes-memory vs mem0  
- Child delegation pack: `pi-subagents` vs official example  
- Browser backend: native agent-browser vs CDP-to-real-profile  
- Connector vendor: Composio vs self-hosted MCP  
- Worker isolation: in-process SDK vs RPC subprocess per turn  
- Group log substrate: your NDJSON vs messenger-swarm channels  

**Write it (this is the runtime)**  
- Supervisor / process topology  
- Roster + policy  
- Inbox, handles, await, lanes, user-preempt vs peer-queue  
- Room host + goal parking  
- Working-folder / computer / memory leases  
- Recent-work brief  
- Approval broker and tenant policy matrix  
- Connector facade  
- Computer lifecycle per tenant  
- Routine records, receipts, catch-up, webhook receiver  
- Canonical event log and transcript tail  
- Tenant isolation  

That last list is OpenMausBot’s harness, minus the desktop and minus their multi-CLI driver zoo, plus tenancy. It is also the GrokBot control plane. It is not forty extensions. If a layer is in “write it,” installing three community packages for it will give you live-process chat and none of the invariants.

A sane order on a server: tenant computer → Pi worker with cwd + memory injector → roster + inbox + await → second Bot + file handoff → approval broker → connectors → routines. Rooms and goals after two Bots can already complete a handle.

> **Sources:**
>
> 1. [OpenMausBot/apps/docs at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/tree/main/apps/docs)
> 2. [OpenMausBot/Dockerfile at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/Dockerfile)
> 3. [OpenMausBot documentation · OpenMausBot Docs](https://docs.openmausbot.com/docs)
> 4. [OpenMausBot/docs at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/)
> 5. [OpenMausBot/docs/memory.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/memory.md)
> 6. [OpenMausBot/docs/mcp-server.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/mcp-server.md)
> 7. [OpenMausBot/companion at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/tree/main/companion)
> 8. [OpenMausBot/docs/plans at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/tree/main/docs/plans)
> 9. [OpenMausBot/docs/voice-mode.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/voice-mode.md)
> 10. [OpenMausBot/README.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/README.md)
> 11. [OpenMausBot/docs/custom-engines.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/custom-engines.md)
> 12. [0.1.65 · Releases · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/releases?q=0.1.65)
> 13. [OpenMausBot/android/README.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/android/README.md)
> 14. [Routines and webhooks · OpenMausBot Docs](https://docs.openmausbot.com/docs/features/automation)
> 15. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-bot-concurrency.md)
> 16. [Bots, folders, and threads · OpenMausBot Docs](https://docs.openmausbot.com/docs/features/bots-and-tasks)
> 17. [OpenMausBot/docs/routine-schedules.md at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/docs/routine-schedules.md)
> 18. [OpenMausBot/server/drivers/grok.ts at main · milind-soni/OpenMausBot · GitHub](https://github.com/milind-soni/OpenMausBot/blob/main/server/drivers/grok.ts)
> 19. [Agent engines · OpenMausBot Docs](https://docs.openmausbot.com/docs/providers)
> 20. [Grok Bot vs OpenMausBot: a feature-by-feature comparison](https://www.openmausbot.com/blog/grok-bot-vs-openmausbot)
> 21. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/memory.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/memory.md)
> 22. [https://docs.openmausbot.com/docs/computers](https://docs.openmausbot.com/docs/computers)
> 23. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/approval-levels.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/approval-levels.md)
> 24. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-goal-mode-v2.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/docs/plans/2026-09-02-goal-mode-v2.md)
> 25. [https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/README.md](https://raw.githubusercontent.com/milind-soni/OpenMausBot/main/README.md)

