# Session 05 proof — Operator Bot `pay`

Migrate payment scheduling onto Bot `pay` Profile `schedule`. Cash leaving the company is high-stakes. This Bot proposes a week. It does not concur. `ctl-pay` / `review-pay` concurs. Kernel policy net still strips illegal pays. No bank execution.

Handle completion was **not** live-proven. No Pi turn ran. Proofs are Kernel / unit.

## Commands

From `.cfo/`:

```bash
.venv/bin/python -m pytest tests/test_scheduling.py -q
```

Result: **17 passed**.

Kernel host against an isolated Computer (seeded demo pool, greedy chooser, then policy net):

```text
Spendable cash: $115,000.00
Approved pool: 13 invoices
paid_has_INV-009 False
defer_has_INV-009 True
audit.passed False
wake.toSlug ctl-pay profile review-pay done False op bot_send_prompt
outflows_before []
executed False
```

`pay_this_week` after policy net: `INV-006`, `INV-002`, `INV-011`, `INV-007`, `INV-004`, `INV-017`.
`INV-009` is in `defer`. HOLD invoices are not in the pool and are stripped if proposed.

`ask_user` is absent from `.cfo/scheduling/*.py`. `run_payment_audit` is not called from the host.

## Disk

```
.cfo-v2/office/bots/pay/BOT.md
.cfo-v2/office/bots/pay/profiles/schedule.md
.cfo-v2/office/bots/pay/roster.fragment.json
.cfo-v2/office/bots/pay/grants.fragment.json
.cfo-v2/office/bots/pay/catalog.fragment.json
.cfo-v2/office/bots/pay/slug-map.fragment.json
.cfo-v2/office/bots/pay/routines/weekly-pay-run.md
.cfo-v2/office/bots/pay/NOTES.md
.cfo-v2/office/computer/harness/bots/bot_pay/memory/MEMORY.md
.cfo-v2/office/computer/harness/roster.json          (pay row: approvalLevel never; schedule connectors only)
.cfo-v2/office/computer/cfo/slug-map.json            (pay.schedule → Payment Scheduler only)
.cfo-v2/office/computer/cfo/grants.json              (Payment Scheduler ops; no tools.get_invoice)
.cfo-v2/office/computer/cfo/grants-fragments/pay.json
.cfo-v2/office/computer/skills/payment-prioritization/SKILL.md
.cfo-v2/office/computer/skills/early-payment-discount-evaluation/SKILL.md
.cfo/scheduling/host.py
.cfo/scheduling/grants.py
.cfo/scheduling/workflow.py
.cfo-v2/office/sessions/05-fixtures/ctl-pay-wake.json
.cfo-v2/office/sessions/05-fixtures/plan-summary.json
```

Isolated Computer tree after the host (then after `ctl-pay` concurrence in the unit test):

```
workspace/pay/plans/plan_2026-09-19_f290ca077456.json
workspace/pay/wakes/h_….json                         (bot_send_prompt → ctl-pay / review-pay, done false)
workspace/cash/expected-outflows/…json               (only after ctl-pay concurs; executed false)
workspace/cash/wakes/h_….json                        (identified wires to cash)
cfo/idempotency/pay-schedule_….json
cfo/idempotency/pay-outflows_….json
```

## Grant SoD

- Profile `schedule` Catalog ops = `scheduling.tools.get_cash_position`, `get_approved_pool`, `get_payment_candidates`, `get_treasury_policies`.
- Those ops are disjoint from AP `RECORD_TOOLS`.
- Slug-map `pay` has one Profile. Payment Audit is `ctl-pay` / `review-pay`, not a Grant union on `pay`.
- Constructor `tools=` for Payment Scheduler and Payment Audit still match in `.cfo/scheduling/agent.py`. Session 09 tightens `review-pay`.

## Not proven live

Pi `bot_send_prompt` / `bot_await_turn` Handle completion. The host writes the next-wake record. Session 01/02 execute it on the Harness bus.
