---
name: early-payment-discount-evaluation
description: Decides whether to capture an open early-payment discount this week using Python discount and cash facts. Use when scheduling or auditing approved AP payments.
status: extracted
---

# Early Payment Discount Evaluation

## Purpose

Capture open early-payment discounts on approved invoices when spendable cash allows, without paying invoices early after the discount window has closed.

## When to Use

Apply while building or auditing this week's payment plan whenever candidates include discount_open, discount_deadline, or discount_amount.

## Inputs / Evidence

Use Python candidate facts only:

- discount_open
- discount_percent / discount_amount
- discount_deadline
- pay_amount_if_this_week
- spendable cash and minimum reserve from get_cash_position

Do not recompute the discount math or invent a 2/10 threshold.

## Procedure

1. Identify approved invoices whose discount window is still open as of the cash as_of_date.
2. If paying the discounted amount this week leaves the reserve intact, capture the discount.
3. If capturing the discount would breach the reserve, defer and explain the cash constraint.
4. If the discount has expired, do not pay early unless payment-prioritization already requires payment because the invoice is late or due this horizon.

## Decision Criteria

- Open discount + approved pool + reserve remains intact → pay this week and capture the discount.
- Open discount but cash is insufficient after higher-priority late/due items → defer; do not breach the reserve to chase a discount.
- Closed discount and not due this horizon → do not pay early.
- Discount arithmetic, including pay_amount_if_this_week, is authoritative Python output.

## Output Expectations

Mark capture_discount only when Python says the discount is open and the invoice is in pay_this_week. Auditors should fail a plan that left an affordable open discount uncaptured or that paid a closed-discount invoice early without a due/late reason.

## Boundaries

- Do not calculate discount amounts or due-date arithmetic.
- Do not invent payment terms or a different discount percent.
- Do not override the minimum cash reserve to capture a discount.
- Do not treat payment terms interpretation as a reason to approve an invoice; AP approval already happened.
