---
name: early-payment-discount-evaluation
description: Chooses whether to capture an open 2/10 this week from Kernel discount facts. Use when Bot pay schedules. Not a Verifier skill.
status: extracted
---

# Early Payment Discount Evaluation

## Purpose

Capture an open early-payment discount when Kernel cash facts allow. Do not pay early after the window closed.

## When to Use

Bot `pay` Profile `schedule` while candidates include `discount_open`. Do not use this on `ctl-pay`. The Verifier reads the netted packet. It does not re-score discounts.

## Inputs / Evidence

Kernel candidate fields: `discount_open`, `discount_deadline`, `pay_amount_if_this_week`, spendable cash, minimum reserve. Do not recompute the discount math.

## Procedure

If the window is open and paying the discounted amount leaves the reserve intact, propose the id. If cash is short after late and due items, defer. If the window is closed, do not pay early unless Kernel already requires payment because the invoice is late or due this horizon.

## Decision Criteria

- Open discount + approved pool + reserve intact → propose capture.
- Open discount but cash is gone after higher-priority items → defer. Do not breach the reserve to chase a discount.
- Closed discount and not due → do not pay early. Kernel will strip it if you try.

## Output Expectations

Mark capture only when Python says the discount is open and the id is in your proposal. Kernel net is authoritative.

## Boundaries

- Do not calculate discount amounts or due-date arithmetic.
- Do not invent payment terms.
- Do not override the minimum cash reserve.
- Do not treat discount judgment as AP match. Match already happened.
