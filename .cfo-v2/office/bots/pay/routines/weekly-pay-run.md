# Routine `weekly-pay-run`

Owning Bot: `pay`.
Profile: `schedule`.
Cadence: weekly.
Conversation: `room:pay`.
`approvalLevel`: never.

## Prompt (wake text)

```
profile: schedule
Run this week's payment-run draft.
Load pool and cash with Catalog ops. Choose among Kernel candidates only.
Stop after you return PaymentPlan invoice IDs. Kernel apply_cash_and_policy_net binds amounts.
Write the netted plan path. bot_send_prompt to ctl-pay with profile: review-pay. Await the Handle.
Do not ask a human. Do not execute ACH. Do not breach the reserve.
```

Session 00 lands this Routine on `office/computer/harness/roster.json`. Kernel wake body: `scheduling.host.run_schedule_host`.
