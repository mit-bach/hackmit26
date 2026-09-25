This directory is a Client system: a Roster plus files.

Six standing Bots map to office roles (intake, payables, receivables, cash, close, assurance). The Harness package does not contain those names in its runtime. Copy this tree, or point `--computer` at it.

## Operator shell (demo)

```bash
cd .harness/Harness-v2
npm run serve -- --computer examples/cfo-floor --fake
```

Opens `http://127.0.0.1:8787/`. Walk the specialists, rooms, Computer files, Handles, and protocol without a model.

`--fake` drains inboxes on disk. Drop it after keys are in Settings to spawn `pi --mode rpc`.

A bound TUI pane is optional:

```bash
HARNESS_BOT=ap HARNESS_COMPUTER=$PWD pi -e ../../extensions/index.ts --name ap
```
