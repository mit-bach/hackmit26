# NOTES — Floor hole (AP money out)

Date: 2026-09-20. Disk wins.

Floor outcomes 1–3 are true enough to continue:

- `computer/office/bots` is a symlink onto `.cfo-v2/office/bots`. `BOT.md` is on cwd.
- Intercept default is Bot `ctl-pay`, not the Operator.
- Handle files live under `harness/bots/*/handles/`. Accept is not complete.

The remaining Floor hole that blocked a **live** weekly pay-run is `autoRoutines: false` on the Computer `harness/client.json` (and instance snapshots). Roster still names Routine `weekly-pay-run`. The flag is Floor-owned. This agent did not flip it.

So the payment-run Handle to `ctl-pay` / `review-pay` is proven by the Kernel host `run_schedule_workflow` writing `write_peer_handle` into `harness/bots/bot_ctl_pay/handles/`. After `ctl-pay` concurs, identified outflows Handle `cash` with `executed` false. That is not a live Pi Routine fire on 8800. Do not read Kernel pytest as office-live.

Continue on Kernel bills, Grants, and Handle shape.
