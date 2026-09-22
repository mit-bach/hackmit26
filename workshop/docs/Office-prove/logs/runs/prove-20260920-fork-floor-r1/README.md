# Run log — prove-20260920-fork-floor-r1

- Created: 2026-09-20T15:34:19Z
- Procedure(s): P0
- Serve URL: http://127.0.0.1:8801/
- Computer path: `.cfo-v2/prove-fork/instances/prove-20260920-fork-floor-r1`
- Clone of isolated template `.cfo-v2/prove-fork/computer` (Kernel copy `.cfo-v2/prove-fork/.cfo`). Golden 8800 / `.cfo-v2/office` not used.
- Fake workers: no
- Sidecar port file: instance `cfo/kernel.port` 58274 after select

## Sequence of steps

| Step | Class | T | Bot | Profile | Ops | Handle | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-S01 | RUNS | | | | | | Created+selected prove-20260920-fork-floor-r1; catalog 101; BOT.md; data→prove-fork maximor; golden currentId unchanged |
| P0-S02 | RUNS | | | | | | sidecar 58274; kernel.health ok k_440dc015bb5c; .import-path → prove-fork/.cfo |
| P0-S03 | RUNS / INTENDED | | | | | | fakeWorkers false; Client extra this instance; clientSkills true |
| P0-S04 | RUNS | | ap | | | | pid 68300 cwd prove-fork instance |
| P0-S04b | RUNS | | | | | | all 16 idle with pids |
| P0-S05 | RUNS / INTENDED | | ap | prepare | tools.get_invoice | h_a9d2c7c7-6f00-402b-819a-5a6542f0b315 | INV-001 found; k_224db965f05c; Grant door |
| P0-S06 | INTENDED | | | | | | BOT.md + constitution on Computer |
| P0-S07 | INTENDED | | collect | chase | accrual.tools.create_accrual | h_0f26de3b-61b5-4eea-a267-1731edcc76ab | Client forbidden; kernel did not write |
| P0-S08 | INTENDED | | | | | | intercept default ctl-pay |
| P0-S09 | RUNS | | | | | | one Handle store; P2 owns unlock |
| P0-S10 | RUNS | | | | | | bind table = S04b |
| P0-S11 | SKIP | | | | | | ask_user not called |

## Checkpoints

See CHECKPOINT.md.

## Open holes

-

## Next action

- [x] continue this instance
- [ ] wipe
- [ ] new instance rN+1
- [ ] 05 repair agent
- [ ] skill batch edit
