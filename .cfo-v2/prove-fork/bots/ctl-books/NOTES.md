# ctl-books — period pass notes

Profile `lock` now reads `close.tools.get_close_gates` and `close.tools.get_close_packet`. It still cannot mark CLOSED. CONCUR is ignored when `evaluate_close_gates` fails. September 2026 stays BLOCKED on `$12.40`.

`create_accrual` stays off every ctl-books Profile.

Routines will not auto-fire (`autoRoutines: false`). Floor owns that flag.
