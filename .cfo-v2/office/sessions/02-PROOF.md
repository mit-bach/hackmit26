# Session 02 proof — Kernel sidecar

Sidecar is `python -m cfo_kernel`. It is not a Bot. It does not bind `HARNESS_BOT`. It does not drain inboxes. Handle completion was **not** live-proven (no Pi turn).

## Env (later sessions must reuse)

Documented in `office/computer/ENV.md`.

```bash
HARNESS_COMPUTER=<repo>/.cfo-v2/office/computer
CFO_EVAL_PHASE=operational
PYTHONPATH=<repo>/.cfo
python -m cfo_kernel --computer "$HARNESS_COMPUTER"
```

| Root | Path |
| --- | --- |
| DATA_DIR | `$HARNESS_COMPUTER/data` → symlink `../../../.cfo/data` |
| RUNS | `$HARNESS_COMPUTER/runs` |
| Grants / Catalog / idempotency / kernel.port | `$HARNESS_COMPUTER/cfo/` |

## Close RPC names

| `op` | Role |
| --- | --- |
| `close.month_end.run_month_end` | **Lock door.** Period lock (`mark_closed` → `period_lock.mark_period`) after `evaluate_close_gates` |
| `close.orchestrator.run_cfo_close` | Test packet only. Not a second period lock |

Host-only (not Catalog): `kernel.health`, `kernel.register_runtime_invoice`, `kernel.bind_cash_case`, `kernel.bind_bs_packets`. Identity `slug=_host` / `botId=kernel-host` / `profile=sidecar`.

## Commands

From repo root, Kernel venv at `.cfo/.venv` (openai-agents, fastapi, uvicorn):

```bash
PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest .cfo/tests/test_cfo_kernel.py -q
# 14 passed

PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_cfo_kernel.py \
  .cfo/tests/test_bs_recon.py \
  .cfo/tests/test_cash_bind_case.py -q
# 25 passed

PYTHONPATH=.cfo .cfo/.venv/bin/python -m cfo_kernel --help
# "Not a Bot. Does not bind HARNESS_BOT. Does not drain inboxes."
```

Pytest covers:

1. RPC read `tools.get_invoice` / `INV-001` against seeded `invoices.json` (`found: true`, amount `12450` — Kernel cents, not invented).
2. `audit` / `interpret` calling `accrual.tools.create_accrual` → `forbidden`; accrual ledger bytes unchanged.
3. Same idempotency key, different body → `idempotency_mismatch`. Mutating op without key → `idempotency_required`.
4. Overlay persist: host `kernel.register_runtime_invoice`, kill sidecar process, start again, `tools.get_invoice` / `ING-SIDECAR-001` still found. File: `runs/ingestion/overlay.json`.
5. Cash case persist via `kernel.bind_cash_case` into `runs/cash_recon/cases/<id>.json` (store from session 07).
6. Operational phase: `load_ground_truth()` raises `AnswerKeyIsolationError`. `get_audit_ground_truth` RPC is `forbidden` even if listed on Auditor Agent Grants (`evalOnly` + slug deny).
7. Compiled live Grants (session 01, 80 Catalog ops): `ap`/`prepare` may read `tools.get_invoice`; `audit`/`interpret` still cannot `create_accrual`. Production Auditor Agent Grants omit `get_audit_ground_truth`.

## Disk

```
.cfo/cfo_kernel/          # python -m cfo_kernel
.cfo-v2/office/computer/ENV.md
.cfo-v2/office/computer/data -> ../../../.cfo/data
.cfo-v2/office/sessions/02-fixtures/{catalog,grants}.json
.cfo-v2/office/sessions/02-NOTES.md
```

HUMAN_REVIEW / HOLD / BLOCKED stay fail-closed. Sidecar does not auto-post. After mutating ops, `must_hold` and `evaluate_close_gates` still run in Python (`cfo_kernel/validators.py`).
