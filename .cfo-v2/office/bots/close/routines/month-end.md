# Routine `month-end`

Owning Bot: `close`.
Profile: `coordinate`.
Cadence: monthly.
Conversation: `room:books-close`.
`approvalLevel`: never.

## Prompt (wake text)

```
profile: coordinate
Run period completeness for this month.
Coordinate has no Catalog ops. Copy Kernel ready_tasks.
Send a new Wake to Bot close with the next treatment Profile.
Do not union Grants. create_accrual stays on accrue. prepaid cannot call it.
Do not mark CLOSED. After treatments, Handle ctl-books / lock with the pack path.
Write pack under Computer workspace/close and runs/month_end.
Never ask a human.

```

Kernel wake body: `close.host.run_close_host`.
Lock door: `close.month_end`. Not `close.orchestrator.run_cfo_close`.
