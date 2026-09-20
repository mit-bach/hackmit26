# Operator walkthrough

This Computer is the HackMIT demo floor. Six named Bots. Domain lives in this tree, not in the Harness package.

## Serve the shell

From `.harness/Harness-v2`:

```bash
npm run serve -- --computer examples/cfo-floor --fake --no-open
```

Open `http://127.0.0.1:8787/`. Fake workers complete Handles so you can walk the office without keys.

## What to show

1. Sidebar: Ingest, Payables, Receivables, Cash, Close, Audit, plus Floor and Pay cycle rooms.
2. Message Ingest: `Land INV-1001 and hand the path to Payables.` A Handle is accepted before the Bot runs.
3. Computer panel: `workspace/inbox/INV-1001.md`. Edit and Save on Computer.
4. Inspector: inbox, Handles, Memory (per Bot).
5. Protocol tab: `protocol.jsonl` as it grows.
6. Pay cycle room: post a stand-up. The Host wakes ingest → ap → cash in roster order.
7. Routines: run `morning-brief` onto Close.
8. Settings: spawn policy, write-only keys, roster edit. Secrets never come back from `GET /api/config`.

Drop `--fake` after keys are in Settings to spawn `pi --mode rpc` per Bot.
