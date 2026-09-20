# Live Computer snapshot — 2026-09-20

Facts from disk that day. Not a design.

Computer: `.cfo-v2/office/computer`.

---

## Roster

- File: `harness/roster.json`
- Bots: 15 slugs `email,stripe,bank,books,ap,pay,apply,collect,cash,close,story,ctl-pay,ctl-cash,ctl-books,audit`
- Description string: “Fifteen grain Bots”
- Rooms: intake, pay, cash, books-close
- Routines: weekly-pay-run, daily-aging, month-end, period-story, post-close-assurance
- `approvalLevel`: never on all listed
- `world` not in `bots[]`
- `collect` connectors: four `ar.tools.*` reads. No send.
- `stripe` skills: `[]`

Instance `protocol-proof` / `fresh-protocol` rosters: 16 slugs including `world`. Collect connectors include `inbox.tools.send_office_outbound`. Description: “Sixteen grain Bots.”

---

## Grants and Catalog

- `cfo/catalog.json`: 89 ops
- Instance catalog: 94 ops
- Missing on live vs instance: `send_office_outbound`, `list_world_personas`, `list_inbox_threads`, `list_inbox_messages`, `get_inbox_thread`
- `cfo/grants.json`: 45 Display names
- Empty ops: 8 names (Audit Report Agent, Month-End Close Reviewer, Close Manager, five sample-data)
- Collections Agent ops: four AR reads
- Counterparty Message Agent ops: compose, send_inbox, reply (no Bot on live slug-map)
- `cfo/slug-map.json`: no `world` key. Stripe payout Display name `""`

---

## Skills

- Computer `skills/*/SKILL.md`: 33
- Kernel `skills/*/SKILL.md`: 35
- Kernel-only: `synthetic-finance-scenario-design`, `cross-ledger-data-consistency`

---

## Harness attach

- `harness/extensions.json`: extraExtensions → Client `cfo/extensions/index.ts`, clientSkills true
- `harness/client.json`: spawnPolicy lazy, autoRoutines false, sidecar `./cfo/bin/sidecar.sh`, model grok-4.5
- `harness/intercept.json`: default operator; collect → ctl-cash
- `cfo/kernel.port`: present, 127.0.0.1:60440

---

## Handles

Six completed Handle files:

- `bot_email` (2)
- `bot_ap` (3)
- `bot_ctl_pay` (1)

Latest ap result: HOLD on INV-S12, invoice not in Kernel, amounts not invented.
Latest ctl-pay result: REFUSE incomplete APPROVE packet.

`protocol.jsonl`: many `send.accepted` for MSG-S12 / INV-S12. No `turn.end` grep hits.

No Handle files for collect, apply, cash, close, story, world in that completed set.

---

## Kernel import check

`.cfo/.venv` with `sys.path` = `.cfo`:

```
ImportError: cannot import name 'send_office_outbound' from 'inbox.tools'
```

Same error constructing `ar.agents.collections_agent`.

---

## BOT.md path

From Computer cwd, `office/bots/collect/BOT.md` does not exist.
Actual: `.cfo-v2/office/bots/collect/BOT.md`.

---

## handle-map

22 edges. Grain slugs only. No `world`. Collect write-off → ctl-pay. No dun edge.

---

## What this snapshot is not

It is not proof the sidecar was healthy, only that a port file existed.
It is not proof fake vs live workers at the moment of the Handle completes.
It is not a substitute for reading the pipe files.
