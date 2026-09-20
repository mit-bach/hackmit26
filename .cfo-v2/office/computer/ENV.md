# Computer env — Kernel sidecar (session 02)

Later sessions must use this env. Do not invent a second data root.

```bash
HARNESS_COMPUTER=<repo>/.cfo-v2/office/computer
CFO_EVAL_PHASE=operational
PYTHONPATH=<repo>/.cfo

python -m cfo_kernel --computer "$HARNESS_COMPUTER"
```

| Root | Path | Role |
| --- | --- | --- |
| Computer | `$HARNESS_COMPUTER` | Roster, Catalog, Grants, slug-map, kernel.port, kernel.log.jsonl, idempotency |
| DATA_DIR | `$HARNESS_COMPUTER/data` | Seed JSON. Symlink to `.cfo/data` |
| RUNS | `$HARNESS_COMPUTER/runs` | Overlay, cash cases, BS packets, traces, period lock |

The Sidecar remaps every Kernel `configure_*` helper onto those two trees at start. Live Bots must not read `.cfo/runs`.

`CFO_EVAL_PHASE` defaults to `operational` if unset. Operational Bots cannot open answer keys or `get_audit_ground_truth`.

The Sidecar is not a Bot. It does not bind `HARNESS_BOT`. It does not drain inboxes.

## Close doors

| RPC `op` | What it is |
| --- | --- |
| `close.month_end.run_month_end` | The lock door. Period lock runs here (`mark_closed` → `period_lock.mark_period`) after `evaluate_close_gates` passes |
| `close.orchestrator.run_cfo_close` | Test packet. AP/accrual/schedule for eval. Not a second period lock |

## Host-only ops (not Catalog, not a Bot)

`slug=_host` `botId=kernel-host` `profile=sidecar`

- `kernel.health`
- `kernel.register_runtime_invoice`
- `kernel.bind_cash_case`
- `kernel.bind_bs_packets`

The model never calls these. Bind is session setup.
