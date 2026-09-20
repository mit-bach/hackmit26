# Session 09 notes — Bot `ctl-pay`

Client intercept for consequential Kernel ops lives in
`.cfo-v2/office/computer/cfo/extensions/intercept.ts` and `call.ts`.
Session 01 already blocked `ask_user` on the Pi `tool_call` hook. This session
routes money-out ops to this slug, not the Harness Operator.

Handle completion was not live-proven. Kernel `complete_ctl_pay_handle` is the
concurrence door. AP Audit is a second Wake of Profile `review-match` with
`audit: true`; it is not a person and not Bot `ap`.

Payment Audit still shares `SCHEDULER_TOOLS` in `.cfo/scheduling/agent.py`.
`catalog.overrides.json` `grantDenylist` strips rebuild ops at compile time.
Do not copy that constructor list onto this Bot.
