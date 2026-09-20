# Host — sequence Profiles as separate Wakes

Kernel module: `close.host.run_close_host`.
Routine: `month-end`.
First Profile: `coordinate`.

This host is the month-end control plane for Bot `close`. It is not a seventeenth Bot. It is not `Runner.run_sync`. It does not lock.

## Sequence

1. Wake `close` / `coordinate`. Grants for this turn are empty.
2. Python `ready_tasks` names the next checklist row.
3. If the row is `accruals` / `prepaid` / `depreciation` / `bs_recon`, write a **new Wake** of Bot `close` with that Profile only. Run the Kernel handler for that task id. Do not union Grants.
4. After a treatment, write a Handle payload to `ctl-books` / `review-treatment`.
5. Repeat from coordinate until no treatment or peer row is READY.
6. Write `workspace/close/<period>/pack.json`. Evaluate `evaluate_close_gates`.
7. Handle `ctl-books` / `lock` with the pack path. **Do not** call `mark_closed`. **Do not** call `period_lock.mark_period`.
8. Handle `story` / `flux` and `audit` / `interpret` with the pack path.

Peer checklist rows (`ingest`, `ap`, `ar`, `cash`) still run their Kernel handlers in this session so the demo period can move. The host also writes Handle payloads to those slugs. Live `bot_send_prompt` is session 01/02. Handle completion was not live-proven here.

## One lock door

`close.month_end` (via `close.engine`). `close.orchestrator.run_cfo_close` is a test packet. This host never opens a second lock.

## Fail closed

Default September (`2026-09`, scenario `demo`) stays `BLOCKED` on planted `$12.40`, unmatched AR, and missing prepaid evidence. Verifier concurrence cannot override gates. A later source mutation must be a legal Kernel op, then rerun. If no legal op exists, the books stay open.

## Disk

```
<computer>/workspace/close/<period>/
  pack.json
  host-run.json
  wakes/NNN-coordinate.json
  wakes/NNN-close-<profile>.json
  handles/ctl-books-<task>.json
  handles/story-pack.json
  handles/audit-pack.json
```
