# Host — sequence Profiles as separate Wakes

Kernel module: `close.host.run_close_host`.
Routine: `month-end`.
First Profile: `coordinate`.

This host is the month-end control plane for Bot `close`. It is not a sixteenth Bot. It is not `Runner.run_sync`. It does not lock.

When `HARNESS_COMPUTER` is set, Kernel state lands under `$HARNESS_COMPUTER/runs/month_end` and the period pack at `$HARNESS_COMPUTER/workspace/close/packets/<period>.json`. That is the office path. `.cfo/runs` is not the office demo destination.

## Sequence

1. Wake `close` / `coordinate`. Grants for this turn are empty. This Profile is not an office-live Catalog caller.
2. Python `ready_tasks` names the next checklist row.
3. If the row is `accruals` / `prepaid` / `depreciation` / `bs_recon`, write a **new Wake** of Bot `close` with that Profile only. Run the Kernel handler for that task id. Do not union Grants.
4. After prepaid, write a Handle payload to `ctl-books` / `review-treatment`. After depreciation, Handle `ctl-books` / `review-assets`. After BS recon, Handle `ctl-books` / `review-bs`. Do not union those Grant sets. Treatment Handles are Harness Handles (`harness/bots/<id>/handles/`) plus workspace copies.
5. Repeat from coordinate until no treatment or peer row is READY.
6. Write `workspace/close/packets/<period>.json`. Evaluate `evaluate_close_gates`.
7. Handle `ctl-books` / `lock` with the pack path and `gates.json`. **Do not** call `mark_closed`. **Do not** call `period_lock.mark_period`.
8. Handle `story` / `flux` and `audit` / `interpret` with the pack path. Story drafts before lock must label numbers `UNLOCKED`.

Peer checklist rows (`ingest`, `ap`, `ar`, `cash`) still run their Kernel handlers in this session so the demo period can move. The host also writes Handle payloads to those slugs. Live `bot_send_prompt` completion is not claimed here.

## One lock door

`close.month_end` (via `close.engine`). `close.orchestrator.run_cfo_close` is a test packet. This host never opens a second lock.

## Fail closed

Default September (`2026-09`, scenario `demo`) stays `BLOCKED` on planted `$12.40`, unmatched AR, and missing prepaid evidence. Verifier concurrence cannot override gates. A later source mutation must be a legal Kernel op, then rerun. If no legal op exists, the books stay open.

## Disk

```
$HARNESS_COMPUTER/runs/month_end/
  <period>.json
  period_lock.json

$HARNESS_COMPUTER/workspace/close/packets/
  pack.json
  gates.json
  host-run.json
  wakes/000-coordinate.json
  wakes/NNN-close-<profile>.json
  handles/ctl-books-lock.json
  handles/story-pack.json
  handles/audit-pack.json
```
