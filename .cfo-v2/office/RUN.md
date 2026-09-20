# Run the Office of the CFO Client system

Commands are from the git repo root (`hackmit26`).

Client root: `.cfo-v2/`
Computer: `.cfo-v2/office/computer`
Kernel: `.cfo/`
Harness: `.harness/Harness-v2`

The Computer file `harness/client.json` is the office config: extra Pi `-e`, Client skills, lazy spawn, xAI/Grok 4.5, Kernel sidecar, no auto-Routines. Load that Computer and the office boots. The human Operator shell is an emergency stop and a demo overlay. It is not a worker. Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) own concurrence.

## 0. One-time

```bash
python3 -m venv .cfo/.venv
.cfo/.venv/bin/pip install -r requirements.txt
cd .harness/Harness-v2 && npm install && npm run ui:build && cd ../..
cd .cfo-v2/office/computer/cfo && npm install && cd ../../../..
ln -sfn ../../../.cfo/data .cfo-v2/office/computer/data
mkdir -p .cfo-v2/office/computer/runs
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

`HARNESS_COMPUTER` is the Computer directory. The sidecar remaps Kernel `data/` and `runs/` onto that Computer. Do not point live Bots at `.cfo/runs`.

Keys live in `~/.harness/config.json` or `$HARNESS_CONFIG`. Do not put keys in `client.json`. Default model on this office is `xai` / `grok-4.5`.

## 1. Deploy (live Pi + Kernel sidecar)

From `.harness/Harness-v2`:

```bash
npm run build
node dist/src/cli.js serve \
  --computer ../../.cfo-v2/office/computer \
  --wipe \
  --no-open \
  --port 8800
```

Loopback: `http://127.0.0.1:8800/`

Leave 8792 for the other UI agent. Do not reuse a contested 8795.

`--wipe` clears inboxes, Handles, transcripts, receipts, lanes, and Pi sessions on that Computer. Roster, skills, Catalog, Grants, intercept, and `client.json` stay. Lazy spawn: a Bot starts when it has pending work. Auto-Routines stay off until `--routines`. Transcript detail defaults to **full** (Pi reasoning + tools) from `harness/client.json`.

```bash
curl -s http://127.0.0.1:8800/health
curl -s http://127.0.0.1:8800/api/office
```

`health.sidecar.port` and `office.attach.clientSkills` should be on. Fifteen Bots. Fake workers are off.

Rebuild the Operator SPA only when `ui/` changed: `npm run ui:build`.

## 2. Wipe / reset for a benchmark

Stopped office:

```bash
node dist/src/cli.js wipe --computer ../../.cfo-v2/office/computer
node dist/src/cli.js wipe --computer ../../.cfo-v2/office/computer --wipe-runs
```

Live office:

```bash
curl -s -X POST http://127.0.0.1:8800/api/wipe \
  -H 'content-type: application/json' \
  -d '{"keepMemory":true}'
```

`--keep-memory` keeps `MEMORY.md`. `--wipe-runs` also empties Computer `runs/` (Kernel overlay). Sidecar port file stays while serve is up.

## 3. Compile Catalog and Grants

Constructor `tools=` lists are the Grant source. Skills never grant tools.

```bash
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

Writes:

- `.cfo-v2/office/computer/cfo/catalog.json`
- `.cfo-v2/office/computer/cfo/grants.json` (operational; omits `get_audit_ground_truth`)
- `.cfo-v2/office/computer/cfo/grants.eval.json` (evaluation; may include evalOnly ops)

Exit non-zero if a constructor tool cannot resolve. Do not hand-edit Grant ops.

## 4. Kernel sidecar (started by serve)

`harness serve` runs `cfo/bin/sidecar.sh` unless `--no-sidecar` or `--fake`. Equivalent manual start:

```bash
.cfo-v2/office/computer/cfo/bin/sidecar.sh
```

Does not bind `HARNESS_BOT`. Does not drain inboxes. Writes `cfo/kernel.port` and `cfo/kernel.log.jsonl`.

Period lock RPC name is `close.month_end.run_month_end` (`close/month_end`). `close.orchestrator.run_cfo_close` is a test packet, not lock.

## 5. Fake workers (protocol demo, no model, no Kernel)

```bash
cd .harness/Harness-v2
node dist/src/cli.js serve --computer ../../.cfo-v2/office/computer --fake --no-sidecar --no-open
```

`--fake` completes Handles without a model. That is a protocol demo, not live Pi.

Bind one Bot with Harness protocol tools **and** the CFO facade:

```bash
.cfo-v2/office/computer/cfo/bin/pi-bot.sh ap
```

Equivalent:

```bash
HARNESS_BOT=ap \
HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer" \
HARNESS_V2_ROOT="$PWD/.harness/Harness-v2" \
CFO_EVAL_PHASE=operational \
  pi -e .harness/Harness-v2/extensions/index.ts \
     -e .cfo-v2/office/computer/cfo/extensions/index.ts \
     --name ap
```

Unbound Pi (no `HARNESS_BOT`) is not a finance worker.

## 6. Routines (owning Bots, not Operator DM)

Auto-Routines are off on this office. Fire one:

```bash
npx harness routine weekly-pay-run --computer ../../.cfo-v2/office/computer
npx harness routine daily-aging --computer ../../.cfo-v2/office/computer
npx harness routine month-end --computer ../../.cfo-v2/office/computer
npx harness routine period-story --computer ../../.cfo-v2/office/computer
npx harness routine post-close-assurance --computer ../../.cfo-v2/office/computer
```

Or pass `--routines` to `serve` to arm cadence timers. Monthly cadence is clamped to a 32-bit-safe interval.

Each lands on the owning Bot inbox with `conversation` `room:<roomId>`.

## 7. Eval isolation

```bash
python3 main.py evaluate-cfo
```

Operational phase cannot open `expected_results.json` or `ground_truth.json`. Production Grants omit `get_audit_ground_truth`. Stripe simulation ground truth lives under `.cfo/data/simulations/stripe/evaluation/` and is eval-only.

## 8. Inbox and Stripe simulation (Kernel, not extra Bots)

These come from Rohan's `durable-inbox-ap-persistence` branch. They feed Bot `email` and Bot `stripe`. They are not a sixteenth Bot.

After a wipe, seed the Computer so the desk has invoices, Stripe objects, and a pay pool without a mailbox:

```bash
HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer" \
CFO_EVAL_PHASE=operational \
PYTHONPATH=.cfo \
  .cfo/.venv/bin/python .cfo-v2/office/seed_demo.py
```

That writes `.cfo-v2/office/DEMO-WALKTHROUGH.md` and `computer/runs/demo-seed.json`.

Kernel CLIs still work the same way when `HARNESS_COMPUTER` is set:

```bash
PYTHONPATH=.cfo HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer" \
  .cfo/.venv/bin/python .cfo/main.py demo-inbox --reset
PYTHONPATH=.cfo .cfo/.venv/bin/python .cfo/main.py simulate-stripe
```

`demo-inbox` classifies mail, writes the durable AP overlay (`runtime_invoices.json` / Computer `runs/ingestion/overlay.json`), and does not ask a human. Vendor bills Handle `ap` / `prepare`. Remittances Handle `apply` / `apply`.

`simulate-stripe` unpacks payout waterfalls in Python. `invoice_candidates` stays 0. Bot `stripe` still has empty constructor Grants.

## 9. Close demo (honest $12.40)

```bash
python3 main.py close-month --month 2026-09 --seed-demo --deterministic
```

Default September stays `BLOCKED` on the planted $12.40 cash break until a **legal Kernel source mutation** exists. There is none for that residual. Do not delete it. `demo_month_end_close.py --resolve` is an emergency/eval fixture, not the office completion path.
