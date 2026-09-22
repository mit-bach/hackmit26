# World proof

Grain Tests A–D passed. Bot `world` is the sixteenth Source Bot. Simulated mailbox only. No live Gmail.

## Tests

From repo root:

```bash
PYTHONPATH=.cfo:.cfo-v2/office .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_inbox_world.py \
  .cfo/tests/test_inbox_integration.py \
  .cfo/tests/test_inbox_unit.py \
  .cfo/tests/test_inbox_persistence.py \
  .cfo/tests/test_inbox_e2e.py \
  .cfo-v2/office/tests/test_session12_roster.py \
  .cfo-v2/office/compiler/test_compile_inbox.py \
  -q --tb=short
```

Result: **44 passed** (2026-09-20).

Ingestion after invoice-number regex (digit required so "invoice number and" is not `AND`):

```bash
PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_ingestion_sources.py \
  .cfo/tests/test_ingestion_validate.py -q
```

Result: **25 passed**.

```bash
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
PYTHONPATH=.cfo-v2/office python3 .cfo-v2/office/compiler/prove.py
```

Result: compile ok, 94 catalog ops, grant diff none, `prove.py: compile SoD assertions passed`.

Catalog includes `inbox.tools.send_inbox_message` (write-local, `runs/inbox/`, sodClass `inbox`). Counterparty Message Agent has compose/send/reply/browse/personas and does not have `dispatch_inbox_action` or `send_office_outbound`. Finance Inbox Agent has classify/dispatch/`send_office_outbound` and does not have `send_inbox_message`.

## Kernel CLI

From `.cfo/`:

```bash
.venv/bin/python -c "from inbox.tools import _list_world_personas, _compose_counterparty_message, _send_inbox_message, _send_office_outbound, _reply_in_thread"
```

Proof run: `list_world_personas` returned 73 rows (vendor/customer/bank/employee). `compose_counterparty_message` + `send_inbox_message` delivered `MSG-CLI-ACME-SEP`. `classify_inbox_message` → `VENDOR_INVOICE`. `send_office_outbound` from collections@ then `reply_in_thread` as `ap@northwindlabs.example`.

## Talk path (port 8800)

1. Open `http://127.0.0.1:8800/`.
2. Select Bot **World** (slug `world`, default Profile `vendor`).
3. Prompt: `Send Acme's September invoice into the finance inbox`.
4. World must call `compose_counterparty_message` then `send_inbox_message`.
5. Handle `email` / `triage` (`delivered`) so Finance Inbox Agent can classify. Do not union Email `invoice` Grants in that turn.

A Handle that includes an outbound thread: World `get_inbox_thread` then `reply_in_thread` as that persona.

Health at proof time: `bots: 16`, sidecar port 54441. New `@function_tool` ops need a sidecar restart after compile. Do not kill 8792.

## Roster

- `bot_world`, slug `world`, approvalLevel `never`
- Room `intake`: `email`, `stripe`, `bank`, `books`, `world` (5 members)
- Handles: `email/outbound` → `world/vendor`; `collect/dun` → `world/customer`; `ap/vendor-query` → `world/vendor`; `world/delivered` → `email/triage`
