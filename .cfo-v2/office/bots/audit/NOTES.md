# Session 11 notes

Wrote this slice against the Constitution, grain § audit, and compiled Grants.

Missing at write time (earlier sessions):

- Live Pi bind (`HARNESS_BOT=audit`) and `bot_send_prompt` / `bot_get_agent_transcript_tail` on a running Harness
- Kernel sidecar RPC (`python -m cfo_kernel`). Grant refuse is local in `grants.py` plus the Pi facade `call.ts`

Handle completion was not live-proven. Kernel `run_audit` and unit tests are the proof layer.

Do not use this Bot as the pay-run approver. That object belongs to `ctl-pay`.
