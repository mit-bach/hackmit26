# Gates — 2026-09-20 (prove-fork, isolated from Golden)

Against isolated template `.cfo-v2/prove-fork/computer` plus copied Kernel `.cfo-v2/prove-fork/.cfo`. Serve: `http://127.0.0.1:8801/`. Selected desk after G9: `prove-20260920-fork-floor-r1`.

Golden `http://127.0.0.1:8800/` / `.cfo-v2/office/office.json` `currentId` `golden-20260920-r1` was not selected, compiled, or rewritten. Harness `src/` was not edited. Live `computer/cfo/catalog.json` mtime unchanged. Live `extensions.json` still points at the Golden Client.

Compiler invoked as `PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational --kernel .cfo-v2/prove-fork/.cfo --out .cfo-v2/prove-fork/computer/cfo` (live default `--out` not used).

| Gate | Result | Note |
| --- | --- | --- |
| G1 Compiler | PASS | Fork `--kernel`/`--out` only. Catalog **101**. Display names **46**. Grant diff none. Collections Agent and Finance Inbox Agent include `inbox.tools.send_office_outbound`. Month-End Close Reviewer includes `close.tools.get_close_gates`. Stripe payout trio present. Close Manager and Audit Report `ops: []`. `get_audit_ground_truth` omitted from operational Grants. |
| G2 Kernel import | PASS | Interpreter is the shared `.venv` symlink. `sys.path` fork `.cfo` first. Imports `classify_inbox_message`, `send_office_outbound` from `prove-fork/.cfo/inbox/tools.py`. `collections_agent` constructs (`agents.agent`). `DEFAULT_COMPUTER` is prove-fork/computer. |
| G3 Catalog vs Grants | PASS | 101 ops. 0 Grant ops missing from Catalog. Empty: Audit Report Agent, Close Manager, five Sample Data Agents. |
| G4 Kernel pytest | PASS fork inbox | `prove-fork/.cfo` pytest.ini `pythonpath=.`. `tests/test_inbox_unit.py` + `test_inbox_e2e.py` 15 passed after T12 patch. Live `.cfo/tests` not run (would still expect injection mint). |
| G5 Identity cwd | PASS | Template and clone `office/bots/ap/BOT.md` → `.cfo-v2/prove-fork/bots`. Constitution → `.cfo-v2/prove-fork/constitution.md`. Not live office bots. |
| G6 Intercept | PASS | Template and clone `default.kind=bot` `bot=ctl-pay`. collect → ctl-pay. Not Operator. |
| G7 Live Pi | PASS | `/health` `fakeWorkers: false`, 16 bots, sidecar owned. Fork `client.json` extra `./cfo/extensions/index.ts`, `clientSkills: true`, `autoRoutines: false`. Instance `extensions.json` extra is this instance’s Client path. Sidecar `.import-path` → `prove-fork/.cfo/*`. |
| G8 World pack | PASS | Template and clone `data` → `.cfo-v2/prove-fork/world/maximor`. Not Golden maximor. |
| G9 office.json | PASS | Fork `currentId` is `prove-20260920-fork-floor-r1`. Computer path `instances/prove-20260920-fork-floor-r1`. Golden registry unchanged. Do not prove on fork `live`. |

Fork operator config: `.cfo-v2/prove-fork/operator-config.json` via `HARNESS_CONFIG` so 8801 cannot write `~/.harness/config.json`.

Do not prove on `live`. Do not POST 8800.
