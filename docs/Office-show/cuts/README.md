# Cuts

Fill seqs **after** `POST /api/demo/record`. Copy this table into `docs/Office-show/runs/<instance-id>/CHAPTERS.md`.

The ten-minute show in `.cfo-v2/office/final-demo/SCENARIOS.md` is a suggested concatenation. You may ship these as separate videos. You may drop a chapter. You may not re-stage Acme on another instance and splice it in.

| Chapter | Story clock | Content | Seq start | Seq end | Video? |
| --- | --- | --- | --- | --- | --- |
| A | O | Onboard. Books discover Maximor. August CLOSED | | | desk establishing |
| B | W1 | Inbox: bill vs quote / injection / statement | | | yes, short |
| C | W1 | `INV-001` match → `ctl-pay` | | | yes |
| C2 | W1 | One HOLD stays out of the pool | | | optional |
| D | W2 | `weekly-pay-run` → `ctl-pay` → cash executed false | | | yes |
| D2 | W2 | Collect refuses while deposits remain, or aging after apply | | | optional |
| E | W3 | Helios FEE_NETTED; `TXN-2026-09-015` unexplained | | | yes |
| F | ME | month-end, lock BLOCKED, story UNLOCKED | | | yes |
| G | ME | Audit reperform `INV-001`, no ground truth | | | yes |
| H | W4 | Dun + World reply if send existed | | | optional |
| I | texture | Extra bills / bank ticks (scrub, rarely a standalone video) | | | raw slider only |

## Rules

- One tape. Chapters are ranges on that tape.
- If a chapter never happened (stripe costume, send T3), write `SKIP reason` in Seq start. Do not fake it in iMovie with Kernel CLI.
- Operator lines in a chapter must be onboard overlay only.
- `$12.40` MATCHED anywhere → the whole recording is not shippable.

## 10-minute concat (optional)

A (30s) → B (90s) → C (90s) → D (90s) → E (90s) → F (90s) → G (45s) → leftover story GM if F did not include it.

Times are edit targets, not how long Pi took.
