# Office world — Maximor Demo Corp

This directory is the company the live Computer loads. It is not `.cfo/data`.

| Path | Role |
| --- | --- |
| `maximor/` | Kernel `DATA_DIR`. AP/AR/bank/GL/inbox/documents live at this root (`invoices.json`, not a nested `demo/` folder). |
| `maximor/simulations/stripe/` | Stripe Bot file connector (23 scenarios). |
| `maximor/holdout/` | Private round-2 hooks. Bots must not load this. |
| `maximor/expected_results.json` | Kernel answer key. Operational Grants omit it. |

Computer bind (from the repo root):

```bash
ln -sfn ../world/maximor .cfo-v2/office/computer/data
```

Harness `--wipe` does not delete `computer/data`. Do not `rm -rf` the symlink target.

Regenerate (Kernel generator, write here):

```bash
cd .cfo
.venv/bin/python main.py generate-sample-data --seed 42 --month 2026-09
.venv/bin/python main.py validate-demo
```

Default output is this folder. `.cfo/data/invoices.json` remains a Kernel unit-test fixture. Do not mount it as the office.
