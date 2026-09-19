---
name: ar-collections-policy
description: Choose the next customer-facing or internal collections action from Python aging and contact facts. Use when deciding whether to remind, hold, escalate a dispute, or leave an overdue invoice alone.
status: new
---

# AR Collections Policy

## Purpose

Turn receivables aging facts into the next reasonable collections action without spamming customers or chasing disputed balances.

## When to Use

Apply when the Collections Agent reviews one overdue or disputed customer invoice. Python has already computed days past due, outstanding balance, reminder count, cooldown, and payment-history facts.

## Inputs / Evidence

Use get_collection_invoice_facts / get_collection_candidates. Trust these Python fields:

- outstanding_amount (never recalculate)
- days_past_due and aging_bucket
- dispute_status / promised_pay_date / cooldown_active
- reminder_count and last_collection_contact
- on_time_rate and payment_behavior

Do not calculate aging buckets or remaining balances.

## Procedure

1. If the invoice is paid, take NO_ACTION.
2. If a billing dispute is open, escalate internally. Do not send a payment demand.
3. If the customer promised to pay on a date that has not passed, HOLD_CONTACT.
4. If a reminder was sent inside the cooldown window, HOLD_CONTACT.
5. Otherwise choose intensity from age and history: gentle for a good payer a few days late; overdue reminder for material 31–60 day balances; final notice after long delinquency and unanswered reminders.
6. Draft customer-facing text only for send actions. Cite the current outstanding amount.

## Decision Criteria

- A 3-day-late on-time customer is a gentle reminder, not a final notice.
- 70+ days with multiple unanswered reminders is stronger escalation.
- Strategic or high-risk flags raise scrutiny but do not override dispute or cooldown blocks.
- Human approval is required for final notices and dispute escalations.

## Output Expectations

Return one CollectionAction, a reason grounded in the supplied facts, confidence, whether human approval is required, and a draft that names the customer, invoice, due date, and outstanding balance when communication is appropriate.

## Boundaries

- Do not recalculate days past due or the outstanding balance.
- Do not demand the original amount after a partial payment.
- Do not send automated collection demands on disputed invoices.
- Do not contact paid invoices.
- Do not invent emails as sent; this is an outbox / preview.
