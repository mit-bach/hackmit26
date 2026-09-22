# Close — period pass notes

September 2026 judged close stays **BLOCKED** on unexplained cash `$12.40` (`TXN-2026-09-015`). That is success. Do not relabel it as timing. Do not edit the bank line in Memory.

## T5 / T8 — coordinate

Profile `coordinate` (Close Manager) has `tools=[]`. That is honest. Coordination is Routine `month-end` + Kernel `ready_tasks` + self-Wake. It is not an office-live Catalog caller.

## T5 — Computer `runs`

When `HARNESS_COMPUTER` is set, `close.host.run_close_host` writes `$HARNESS_COMPUTER/runs/month_end` (period pack, prepaid, FA, BS, journals, identity links) and `$HARNESS_COMPUTER/workspace/close/<period>/`. RUN.md close demo exports that env. The Kernel shim still chdirs into `.cfo/` for imports; that chdir is not the office destination.

## T3 — lock reads gates

Month-End Close Reviewer (`ctl-books` / `lock`) is granted `close.tools.get_close_gates` and `close.tools.get_close_packet`. Read-only. Cannot mark CLOSED. `evaluate_close_gates` is the only door that can later mark CLOSED. `close.orchestrator.run_cfo_close` does not lock.

## Routines (Floor owns autoRoutines)

Live `client.json` has `autoRoutines: false`. Routines `month-end`, `period-story`, and `post-close-assurance` parse, but they will not fire themselves. Prompt text is honest. Do not flip autoRoutines here.

## Harbor

Reuse Harbor Electric’s last accrual method only when current evidence still supports it. October actual-bill reversal is not fully wired in the default demo path. Do not fake that reversal as office-live.

## Not claimed

- September is not CLOSED.
- Live Pi `bot_send_prompt` completion for close Handles is not claimed.
- Stealth theft holdout is not planted in operational books.
