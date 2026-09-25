# Story — period pass notes

Story does not own the books. Story does not move money.

If `lock_status` is not `CLOSED`, every number is labeled `UNLOCKED`. Packets live at `workspace/story/packets/<period>.json`.

Forecast starting balance is trusted cash from Bot `cash` (`workspace/cash/trusted/<period>.json`). Unreconciled GL cash is not trusted cash. September 2026 has no trusted cash while `$12.40` is unexplained. The 13-week start stays REFUSED. That is success.

Kernel forecast snapshots are create-only. Do not overwrite.

## Routines

Live `client.json` has `autoRoutines: false`. Routine `period-story` will not fire itself. Floor owns that flag.

## Not claimed

- A fluent board pack on unlocked numbers is a draft, not a closed pack.
- No `ctl-story`. `audit` samples the pack.
