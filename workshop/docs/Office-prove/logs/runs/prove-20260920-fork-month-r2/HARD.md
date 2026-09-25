# HARD — P2 pool door

- Step: P2-S01 / S02 on `prove-20260920-fork-month-r2`
- Handle: ap `h_f6c0b759-66da-412d-b9b5-1294e2eec99b`; ctl-pay `h_63228d66-a4e3-4805-8200-2bad3065cd5c`
- Class: HARD T3
- What happened: ctl-pay CONCUR ALLOW on `INV-001` wrote `runs/ap/decisions/INV-001-review-match.json`. `runs/approved_pool.json` was never created. `complete_ctl_pay_handle` is not a Catalog op and the sidecar does not call it. `get_approved_pool` reads only `runs/approved_pool.json`.
- Patch: fork `.cfo/scheduling/pool.py` `load_pool` also reads CONCUR decision files with `allowed` true and empty `must_hold`. Live `.cfo/` not edited.
- Next desk: `prove-20260920-fork-month-r3`. Do not fire `weekly-pay-run` on r2.
