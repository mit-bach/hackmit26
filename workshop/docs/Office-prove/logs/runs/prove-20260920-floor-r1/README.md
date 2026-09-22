# Run log — prove-20260920-floor-r1

- Created: 2026-09-20T14:25:32Z
- Procedure(s): P0
- Serve URL: http://127.0.0.1:8800/
- Computer path: `.cfo-v2/office/instances/prove-20260920-floor-r1`
- Clone of live at: operational compile 101 ops, 16 Roster Bots including `world`, intercept default `ctl-pay`
- Fake workers: no
- Sidecar port file: `cfo/kernel.port` → 127.0.0.1:64042 (matches `/health`)

## Sequence of steps

| Step | Class | T | Bot | Profile | Ops | Handle | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-S01 | RUNS / INTENDED | | | | | | Instance exists, currentId prove-20260920-floor-r1, path instances/<id>, catalog 101, BOT.md, data→maximor, empty ap inbox |
| P0-S02 | RUNS | | | | | | kernel.port 64042 on this Computer; kernel.health ok; no ImportError |
| P0-S03 | RUNS | | | | | | fakeWorkers false; Client extra on instance; clientSkills true |
| P0-S04 | RUNS | | ap | | | | spawn ok; lane pid 83626 cwd this Computer; BOT.md reachable |
| P0-S04b | RUNS | | all 16 | | | | email stripe bank books world pay apply collect cash close story ctl-pay ctl-cash ctl-books audit idle with pids |
| P0-S05 | RUNS | | ap | prepare | tools.get_invoice | h_c197153e-03d4-4509-a3a6-3856f01822d3 | call_connected_tool invoice_id INV-001; kernel k_0240b3e7a405 ok; found true Acme Supplies; Handle completed; protocol turn.end. Bash listed data/invoices.json first — P0 prefers RUNS the op |
| P0-S06 | INTENDED | T6 | | | | | office/bots/ap/BOT.md and office/constitution.md exist on this Computer |
| P0-S07 | INTENDED | T9 | collect | chase | accrual.tools.create_accrual | h_d601b3c3-a882-4e17-a47a-60a332c81e97 | call_connected_tool returned forbidden; kernel.log has no create_accrual; no accrual written |
| P0-S08 | INTENDED | T9 | | | | | intercept default.kind=bot default.bot=ctl-pay; collect → ctl-pay |
| P0-S09 | RUNS | T9 | | | | | S05 Handle only under harness/bots/bot_ap/handles/; no workspace/verifier/handles. P0 partial; P2 owns unlock |
| P0-S10 | RUNS | | all 16 | | | | Same as S04b |
| P0-S11 | SKIP | T6 | ap | prepare | ask_user | h_c25808c7-c596-48fb-94b3-dacb29f7b16a | Model refused from BOT.md/constitution; no ask_user tool call; Client-block not proved. Not treated as concurrence |

## Checkpoints

See CHECKPOINT.md. Frozen VENDOR_ID=INV-001 (World pack, not INV-S12).

## Open holes

- S11 Client-block of ask_user not proved (model refused before the tool).
- S09 Verifier unlock not proved (S05 was read-only). P2 owns unlock.

## Next action

- [x] continue this instance — P0 complete
- [ ] wipe
- [x] new instance month-r1 for pipes
