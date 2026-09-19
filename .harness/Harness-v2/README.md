# Harness v2

Named Bots on one Computer. Pi is the per-Bot turn engine. The Harness owns the Roster, inboxes, Handles, Room Host, Memory isolation, approvals, and Routines.

This is a headless control plane. A UI can sit on the HTTP JSON API later. There is no product shell here.

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
10. Operator stop cancels a running peer Handle.
11. A dead process leaves claimed inbox pending and a running Handle queued.
12. Path leases block a second Bot.

Pi TUI / RPC bind is implemented. It is not required for those tests.

## Layout

```
<computer>/
  harness/roster.json
  harness/protocol.jsonl
  harness/bots/<botId>/inbox.jsonl
  harness/bots/<botId>/handles/<handleId>.json
  harness/bots/<botId>/memory/
  harness/rooms/<roomId>/log.jsonl
  <client files>
```

A Client system is a `roster.json` plus files on that Computer. The Harness does not ship domain specialists.

## Headless

```bash
cd .harness/Harness-v2
npm install
npm test
HARNESS_COMPUTER=/path/to/client-tree npx harness serve --computer /path/to/client-tree --fake
```

`--fake` drains inboxes with disk workers (no model). `--no-workers` is HTTP only. Default `serve` tries to spawn `pi --mode rpc` per Bot.

Loopback JSON:

- `GET /v1/health`
- `GET /v1/roster`
- `GET /v1/bots?query=`
- `POST /v1/bots/:slug/prompt` `{ "text": "..." }`
- `POST /v1/bots/:slug/stop`
- `GET /v1/bots/:slug/inbox`
- `GET /v1/bots/:slug/transcript`
- `GET /v1/handles/:id`
- `POST /v1/handles/:id/await`
- `GET /v1/protocol`
- `GET /v1/protocol/stream`
- `POST /v1/rooms/:id/post`
- `POST /v1/approvals/:id` `{ "allow": true }`
- `POST /v1/routines/:name/run`

## cmux / TUI pane

```bash
HARNESS_BOT=alpha HARNESS_COMPUTER=/path/to/client-tree pi -e /path/to/Harness-v2/extensions/index.ts --name alpha
```

Or `npx harness bot alpha --computer /path/to/client-tree`.

Unbound Pi (no `HARNESS_BOT`) does not register protocol tools.

## Commands (bound pane)

`/bot` `/whoami` `/roster` `/handles` `/room` `/routine run <name>` `/stop` `/protocol`

Creating a Bot is editing the Roster and starting a bound process.

## What this is not

- Not children (`pi-subagents` is not installed as the Bot network).
- Not MCP rooms as the local bus.
- Not a finance office. That is a Client system you attach later.
- Not a GrokBot replica until the disk proofs stay green and live Pi turns complete Handles the same way.
