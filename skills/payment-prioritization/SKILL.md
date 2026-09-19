---
name: payment-prioritization
description: Ranks approved invoices for this week's payment run using Python due-date, priority, and cash facts. Use when building or auditing a weekly AP payment plan.
status: extracted
---

# Payment Prioritization

## Purpose

Decide which approved invoices should be paid this week versus deferred, given spendable cash and published treasury policy.

## When to Use

Apply when the Payment Scheduler builds a plan or Payment Audit reviews that plan. Only invoices already in the approved pool are in scope.

## Inputs / Evidence

Use get_payment_candidates, get_approved_pool, get_cash_position, and get_treasury_policies. Python already computed:

- spendable cash
- days until due / late / due_within_horizon
- vendor_priority
- unnecessary_if_paid_early
- pay_amount_if_this_week

Do not recalculate discounts, due dates, or spendable cash.

## Procedure

1. Confirm every pay candidate is in the approved pool.
2. Pay invoices that are late or due within the horizon, highest vendor_priority first.
3. Stop before breaching the minimum cash reserve.
4. Do not pay invoices whose discount has expired and that are not due this horizon.
5. Leave remaining approved invoices in defer with a cash or timing reason.

## Decision Criteria

- Never pay an invoice that is not in the approved pool or that AP held.
- Late and due-this-horizon invoices outrank invoices that can wait.
- Higher vendor_priority is paid first when cash is tight.
- A distant invoice with a closed discount is an unnecessary early payment and should be deferred.
- If cash cannot cover a due/late invoice without breaching the reserve, defer it and say so. Do not invent a different reserve.

## Output Expectations

Return pay_this_week and defer lists using only candidate invoice IDs, plus total_payout, cash_after_payments, reserve_ok, reasons, and confidence. Auditors should set passed=false when a due/late invoice was skipped without a cash reason or when a non-approved invoice was paid.

## Boundaries

- Do not execute a bank payment.
- Do not recalculate cash, reserves, or due dates.
- Do not pull HOLD invoices into the plan.
- Do not change AP approval outcomes; scheduling only sequences already-approved invoices.
