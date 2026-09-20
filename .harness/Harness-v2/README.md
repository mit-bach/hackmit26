# Harness v2

Named Bots on one Computer. Pi is the per-Bot turn engine. The Harness owns the Roster, inboxes, Handles, Room Host, Memory isolation, approvals, and Routines.

The Operator surface is the OpenMausBot frontend, served unchanged from `ui/`, talking to this host over HTTP and one SSE stream. Pi runs headless as `pi --mode rpc`. You do not need the Pi TUI for demos.

## Operator shell (demo)

```bash
cd .harness/Harness-v2
npm install
npm run ui:install
npm test
npm run serve -- --computer examples/cfo-floor --fake
```

Opens `http://127.0.0.1:8787/`. `--fake` completes Handles without a model so you can walk the office immediately. Drop `--fake` after keys are in Settings (or `~/.harness/config.json`) to spawn real Pi RPC children.

`--no-open` skips launching a browser. Bind is loopback only.

What the shell includes:

- Sidebar of specialists and Rooms (cfo-floor: ingest, ap, ar, cash, close, audit)
- Chat with Handle-backed prompts, Stop, approval cards
- Room posts (Host still serializes wakes)
- Computer panel: workspace files, not a VM screenshot
- Inspector: Handles and lane
- Routines and receipts
- Office map of bounded contexts
- Developer settings: spawn policy, model, write-only keys, roster edit, spawn/kill sessions

## What is proven

`npm test` (no model, no API key) checks:

1. `bot_send_prompt` writes `accepted` before the receiver runs.
2. The receiver's turn end writes `completed`.
3. `awaitTurn` returns `done: true`.
4. `protocol.jsonl` plus the Handle file answer who sent what, to whom, and whether it finished.
5. Roster search returns Bot slugs and live status, not child ids.
6. Memory of Bot A is not readable as Memory by Bot B.
7. Room Host waits on a busy member and chips instead of skipping silently.
8. A consequential gate can park a Handle `blocked` until the Operator answers.
9. A Routine enqueue lands on the owning Bot's inbox.
10. Operator stop cancels the running peer Handle.
11. A dead process leaves claimed inbox pending and a running Handle queued.
12. Path leases block a second Bot.
13. `/api/snapshot`, `/api/bots/:slug/messages`, SSE hello, Computer path escape, and Operator file writes.

Pi TUI / RPC bind is implemented. It is not required for those tests.

## Layout

```
<computer>/
  harness/roster.json
  harness/protocol.jsonl
  harness/bots/<botId>/inbox.jsonl
  harness/bots/<botId>/handles/<handleId>.json
  harness/bots/<botId>/memory/
  harness/bots/<botId>/pi-session/
  harness/rooms/<roomId>/log.jsonl
  <client files>
```

A Client system is a `roster.json` plus files on that Computer. The Harness does not ship domain specialists.

## Headless JSON

`--fake` drains inboxes with disk workers (no model). `--no-workers` is HTTP only. Default `serve` tries to spawn `pi --mode rpc` per Bot.

Loopback:

- `GET /` Operator SPA (after `npm run ui:build`)
- `GET /api/snapshot` `GET /api/events` (SSE)
- `POST /api/bots/:slug/messages` `{ "text": "..." }`
- `POST /api/rooms/:id/messages`
- `GET /api/computer/tree` `GET /api/computer/file?path=`
- `PATCH /api/config` (keys are write-only)
- Existing `/v1/*` control-plane routes stay stable

## cmux / TUI pane

Optional. The Operator shell does not need it.

```bash
HARNESS_BOT=alpha HARNESS_COMPUTER=/path/to/client-tree pi -e /path/to/Harness-v2/extensions/index.ts --name alpha
```

Or `npx harness bot alpha --computer /path/to/client-tree`.

Unbound Pi (no `HARNESS_BOT`) does not register protocol tools.

## What this is not

- Not children (`pi-subagents` is not installed as the Bot network).
- Not MCP rooms as the local bus.
- Not a finance office hardcoded into `src/`. cfo-floor is one Client system.
- Not OpenMausBot's Electron, Box, CUA, or Composio stack. The shell copies that product's local-first chat architecture.
