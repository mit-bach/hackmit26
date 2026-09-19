This directory is a Client system: a Roster plus files.

Six standing Bots map to office roles (intake, payables, receivables, cash, close, assurance). The Harness package does not contain those names in its runtime. Copy this tree, or point `HARNESS_COMPUTER` at it.

```bash
HARNESS_COMPUTER=$PWD npx harness serve --computer "$PWD" --fake
HARNESS_BOT=ap HARNESS_COMPUTER=$PWD pi -e ../../extensions/index.ts --name ap
```
