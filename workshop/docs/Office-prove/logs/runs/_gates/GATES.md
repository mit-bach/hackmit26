# Gates — 2026-09-20 (re-run after live wipe)

Against live template `.cfo-v2/office/computer` plus Kernel `.cfo/`. Selected desk: `prove-20260920-floor-r1` at `http://127.0.0.1:8800/`.

| Gate | Result | Note |
| --- | --- | --- |
| G1 Compiler | PASS | `PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational` exit 0. Catalog **101**. Display names **46**. Grant diff none. Collections Agent and Finance Inbox Agent include `inbox.tools.send_office_outbound`. Month-End Close Reviewer includes `close.tools.get_close_gates` and `close.tools.get_close_packet`. Stripe Payout Agent: payout trio. Close Manager and Audit Report `ops: []`. `get_audit_ground_truth` omitted from operational Grants, present on eval Grants. |
| G2 Kernel import | PASS | `.cfo/.venv`, `sys.path` `.cfo` first. `classify_inbox_message` and `send_office_outbound` import. `collections_agent` constructs (`agents.agent.Agent`). |
| G3 Catalog vs Grants | PASS | 101 ops. 0 Grant ops missing from Catalog. Empty: Audit Report Agent, Close Manager, five Sample Data Agents. |
| G4 Kernel pytest | SKIP this pass | Not required before P0. Prior rollup claimed 40+31 passed. Re-run if a HARD Kernel patch lands. |
| G5 Identity cwd | PASS | `computer/office/bots/ap/BOT.md`, `computer/office/constitution.md`, `.cfo-v2/office/bots/ap/BOT.md`. Clone `office/bots` → `../../../bots`. Prove `office/bots/ap/BOT.md` exists. |
| G6 Intercept | PASS | Live and prove `default.kind=bot` `bot=ctl-pay`. collect → ctl-pay. Not Operator. |
| G7 Live Pi | PASS | `/health` `fakeWorkers: false`, 16 bots, sidecar owned port 64042. Prove `client.json` extra `./cfo/extensions/index.ts`, `clientSkills: true`, `autoRoutines: false`. Prove `extensions.json` extraExtensions is this Computer’s Client path. |
| G8 World pack | PASS | Live and prove `data` → `.cfo-v2/office/world/maximor`. |
| G9 office.json | PASS | `currentId` is `prove-20260920-floor-r1`. Computer path `instances/prove-20260920-floor-r1`. Historical `protocol-proof` / `fresh-protocol` are gone from the registry. Do not prove on `live`. |

Do not prove on `live`.
