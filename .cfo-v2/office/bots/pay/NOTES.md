# Session 05 notes

Roster, slug-map, and compiled Grants now exist from sessions 00/01.

This slice:

- Bot `pay` Profile `schedule` only. Display name Payment Scheduler.
- Payment Audit stays on `ctl-pay` / `review-pay`. Constructor `tools=` still match today. Session 09 tightens `review-pay` with catalog overrides.
- Kernel host: `.cfo/scheduling/host.py`. Next-wake records are Harness `bot_send_prompt` payloads. Session 01/02 execute them. This session does not invent a second bus.

Handle completion was not live-proven (no bound Pi). Kernel unit tests are the proof layer.
