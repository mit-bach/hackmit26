---
name: ar-collections-policy
description: Chooses the next collections action from Kernel aging and contact facts. Use when Bot collect wakes on the aging Routine after apply has drained deposits for that as-of.
status: new
---

# AR Collections Policy

## Purpose

Turn receivables aging facts into the next collections action without spamming customers or chasing disputed or already-paid balances.

## When to Use

Use when Bot collect, Profile chase, reviews one overdue or disputed customer invoice. Kernel already computed days past due, outstanding balance, reminder count, cooldown, and payment-history facts. Do not run this skill until apply has drained new deposits for the as-of date.

## Inputs / Evidence

Call get_collection_invoice_facts or get_collection_candidates. Trust these Kernel fields:

- outstanding_amount (never recalculate)
- days_past_due and aging_bucket
- dispute_status / promised_pay_date / cooldown_active
- reminder_count and last_collection_contact
- on_time_rate and payment_behavior

Do not calculate aging buckets or remaining balances.

## Procedure

1. If apply has not drained new deposits for this as-of, stop. Handle apply. Do not chase.
2. If unapplied cash may belong to this customer, HOLD_CONTACT. Handle apply. Do not invent that they unpaid.
3. If the invoice is paid, take NO_ACTION.
4. If a billing dispute is open, ESCALATE_DISPUTE. Do not send a payment demand.
5. If the customer promised to pay on a date that has not passed, HOLD_CONTACT.
6. If a reminder was sent inside the cooldown window, HOLD_CONTACT.
7. Otherwise choose intensity from age and history: gentle for a good payer a few days late; overdue reminder for material 31–60 day balances; final notice after long delinquency and unanswered reminders.
8. REQUEST_INTERNAL_REVIEW for write-off or reserve is a Handle to ctl-pay. Do not ask a person.
9. Draft customer-facing text only for send actions. Cite the current outstanding amount.

## Decision Criteria

- A 3-day-late on-time customer is a gentle reminder, not a final notice.
- 70+ days with multiple unanswered reminders is stronger escalation.
- Strategic or high-risk flags raise scrutiny but do not override dispute, cooldown, or dirty-cash blocks.
- human_approval_required means ctl-pay for write-off or reserve. It is not a human queue.

## Output Expectations

Return CollectionDecision. One CollectionAction, a reason grounded in the supplied facts, confidence, whether Verifier concurrence is required, and a draft that names the customer, invoice, due date, and outstanding balance when communication is appropriate.

## Boundaries

- Do not recalculate days past due or the outstanding balance.
- Do not demand the original amount after a partial payment.
- Do not send automated collection demands on disputed invoices.
- Do not contact paid invoices.
- Do not call cash-application tools, create_accrual, or pay-run tools.
- Do not ask the AE. There is no AE.
- Do not invent emails as sent. This is an outbox / preview.
