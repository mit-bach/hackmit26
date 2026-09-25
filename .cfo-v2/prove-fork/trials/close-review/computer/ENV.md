# Computer env — prove-fork Kernel sidecar

Isolated from Golden `.cfo-v2/office`. Do not export the live office Computer.

```bash
HARNESS_COMPUTER=<repo>/.cfo-v2/prove-fork/computer
CFO_KERNEL=<repo>/.cfo-v2/prove-fork/.cfo
CFO_EVAL_PHASE=operational
PYTHONPATH=$CFO_KERNEL
HARNESS_CONFIG=<repo>/.cfo-v2/prove-fork/operator-config.json

python -m cfo_kernel --computer "$HARNESS_COMPUTER"
```

| Root | Path | Role |
| --- | --- | --- |
| Computer | `$HARNESS_COMPUTER` | Roster, Catalog, Grants, slug-map, kernel.port, kernel.log.jsonl, idempotency |
| DATA_DIR | `$HARNESS_COMPUTER/data` | Seed JSON. Symlink to `.cfo-v2/prove-fork/world/maximor` |
| RUNS | `$HARNESS_COMPUTER/runs` | Overlay, cash cases, BS packets, traces, period lock |
| Kernel | `$CFO_KERNEL` | Copied Kernel source (skills, constructors, inbox). Interpreter may symlink `.venv` |

`CFO_EVAL_PHASE` defaults to `operational` if unset. Operational Bots cannot open answer keys or `get_audit_ground_truth`.

The Sidecar is not a Bot. It does not bind `HARNESS_BOT`. It does not drain inboxes.
