---
name: payment-prioritization
description: Chooses among Kernel payment candidates for this week's draft. Use when Bot pay wears Profile schedule. Not a Verifier skill.
status: extracted
---

# Payment Prioritization

## Purpose

Pick which Kernel-eligible invoices to propose this week. Python already computed due dates, priority, spendable cash, and unnecessary early pays. Kernel `apply_cash_and_policy_net` binds the plan after you.

## When to Use

Bot `pay` Profile `schedule` only. Do not wear this on `ctl-pay`. Payment Audit looks for reasons to refuse. It does not rank the run again.

## Inputs / Evidence

the approved pool, the cash position, the payment candidates, and the treasury policies. Trust `pay_amount_if_this_week`, `vendor_priority`, `unnecessary_if_paid_early`, and spendable cash. Do not recalculate them.

## Procedure

Choose among candidate ids. Prefer late and due-this-horizon when cash is tight. Leave the rest in defer with a cash or timing reason. Stop. Kernel strips HOLD, strips unnecessary early pays, and refuses a reserve breach.

## Decision Criteria

- Never propose an id that is not in the approved pool.
- If cash cannot cover a due item without breaching the reserve, defer it. Do not invent a different reserve.
- Do not pay. There is no send-as-bank Connector.

## Output Expectations

`PaymentPlan` invoice ids only. Totals on disk must match Kernel net, not your arithmetic.

## Boundaries

- Do not execute a bank payment.
- Do not recalculate cash, reserves, or due dates.
- Do not pull HOLD invoices into the plan.
- Do not change AP match outcomes. Scheduling only sequences already-approved invoices.
