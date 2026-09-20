# Run the Office of the CFO Client system

Commands are from the git repo root (`hackmit26`).

Client root: `.cfo-v2/`
Computer: `.cfo-v2/office/computer`
Kernel: `.cfo/`
Harness: `.harness/Harness-v2`

The human Operator shell is an emergency stop and a demo overlay. It is not a worker. Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) own concurrence.

## 0. One-time

```bash
python3 -m pip install -r requirements.txt
cd .harness/Harness-v2 && npm install && cd ../..
cd .cfo-v2/office/computer/cfo && npm install && cd ../../../..
ln -sfn ../../../.cfo/data .cfo-v2/office/computer/data
mkdir -p .cfo-v2/office/computer/runs
```

`HARNESS_COMPUTER` is the Computer directory. Sidecar remaps Kernel `data/` and `runs/` onto that Computer. Do not point live Bots at `.cfo/runs`.

## 1. Compile Catalog and Grants

Constructor `tools=` lists are the Grant source. Skills never grant tools.

```bash
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

Writes:

- `.cfo-v2/office/computer/cfo/catalog.json`
- `.cfo-v2/office/computer/cfo/grants.json` (operational; omits `get_audit_ground_truth`)
- `.cfo-v2/office/computer/cfo/grants.eval.json` (evaluation; may include evalOnly ops)

Exit non-zero if a constructor tool cannot resolve. Do not hand-edit Grant ops.

## 2. Kernel sidecar (not a Bot)

```bash
PYTHONPATH=.cfo \
  HARNESS_COMPUTER="$PWD/.cfo-v2/office/computer" \
  CFO_EVAL_PHASE=operational \
  python3 -m cfo_kernel --computer "$PWD/.cfo-v2/office/computer"
```

Does not bind `HARNESS_BOT`. Does not drain inboxes. Writes `cfo/kernel.port` and `cfo/kernel.log.jsonl`.

Period lock RPC name is `close.month_end.run_month_end` (`close/month_end`). `close.orchestrator.run_cfo_close` is a test packet, not lock.

## 3. Harness (bus) + Client extension (Grants)

Headless, fake workers (no Pi, no model). Operator SPA is optional overlay:

```bash
cd .harness/Harness-v2
npm run serve -- --computer ../../.cfo-v2/office/computer --fake --no-open
```

Loopback: `http://127.0.0.1:8787/`. `--fake` completes Handles without a model. That is a protocol demo, not live Pi.

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

## 4. Routines (owning Bots, not Operator DM)

From `.harness/Harness-v2`:

```bash
npx harness routine weekly-pay-run --computer ../../.cfo-v2/office/computer
npx harness routine daily-aging --computer ../../.cfo-v2/office/computer
npx harness routine month-end --computer ../../.cfo-v2/office/computer
npx harness routine period-story --computer ../../.cfo-v2/office/computer
npx harness routine post-close-assurance --computer ../../.cfo-v2/office/computer
```

Each lands on the owning Bot inbox with `conversation` `room:<roomId>`.

## 5. Eval isolation

```bash
python3 main.py evaluate-cfo
```

Operational phase cannot open `expected_results.json` or `ground_truth.json`. Production Grants omit `get_audit_ground_truth`. Stripe simulation ground truth lives under `.cfo/data/simulations/stripe/evaluation/` and is eval-only.

## 6. Inbox and Stripe simulation (Kernel, not extra Bots)

These come from Rohan's `durable-inbox-ap-persistence` branch. They feed Bot `email` and Bot `stripe`. They are not a sixteenth Bot.

```bash
python3 main.py demo-inbox
python3 main.py simulate-stripe
```

`demo-inbox` classifies mail, writes the durable AP overlay (`runtime_invoices.json` / Computer `runs/ingestion/overlay.json`), and does not ask a human. Vendor bills Handle `ap` / `prepare`. Remittances Handle `apply` / `apply`.

`simulate-stripe` unpacks payout waterfalls in Python. `invoice_candidates` stays 0. Bot `stripe` still has empty constructor Grants.

## 7. Close demo (honest $12.40)

```bash
python3 main.py close-month --month 2026-09 --seed-demo --deterministic
```

Default September stays `BLOCKED` on the planted $12.40 cash break until a **legal Kernel source mutation** exists. There is none for that residual. Do not delete it. `demo_month_end_close.py --resolve` is an emergency/eval fixture, not the office completion path.
