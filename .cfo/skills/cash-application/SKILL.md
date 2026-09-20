---
name: cash-application
description: Choose among Python-generated invoice matches for a customer payment, including ambiguous remittances. Use when applying cash or reviewing a material / non-unique proposal.
status: new
---

# Cash Application

## Purpose

Apply incoming customer cash to the right open invoices when the remittance is incomplete, and abstain when two explanations are equally good.

## When to Use

Apply when the Cash Application Agent or Cash Application Reviewer evaluates one payment. Python has already built the candidate sets (named invoice, exact amount, combinations, stale references).

## Inputs / Evidence

Use get_cash_application_facts. Authoritative Python outputs include:

- identified customer and confidence
- remittance invoice IDs and stale / paid references
- candidate applications with amounts and unapplied remainder
- customer remittance precedent

Do not search new invoice combinations and do not recalculate totals.

## Procedure

1. Read the remittance evidence hierarchy: explicit invoice number (including Stripe metadata `invoice_id` / `order_id`), then identified customer plus unique exact amount, then a unique combination, then remittance/description overlap, then prior-period Stripe remittance precedent as supporting color only.
2. If the memo names a live invoice and the amount is at or below outstanding, AUTO_APPLY that candidate as a full or partial application. Do not mark the invoice fully paid when a residual remains.
3. If one customer has exactly one invoice matching the amount, AUTO_APPLY.
4. If two candidates both explain the amount exactly (single invoice vs combination, or two invoices with the same balance), HUMAN_REVIEW.
5. If the payer cannot be identified, UNAPPLIED or HUMAN_REVIEW. Do not guess.
6. If remittance names a customer or invoice that conflicts with the bank sender or tagged customer, HUMAN_REVIEW. Do not guess.
7. If remittance cites an invoice ID that does not exist, HUMAN_REVIEW as an invalid reference.
8. If the payment amount exceeds the named invoice outstanding, HUMAN_REVIEW and preserve the residual. Do not drop it.
9. If the payment is already APPLIED or PARTIALLY_APPLIED, refuse a second application.
7. Tell the reviewer whether precedent actually matches these present facts.
8. After a human correction or a prior Stripe metadata match, treat the stored precedent as scoped evidence for similar later remittances. It must not override a contradictory live remittance or an accounting invariant.
9. When Stripe metadata is missing, customer + amount + date + description may still uniquely identify the invoice. If two open invoices have the same amount and no unique contextual or precedent support, HUMAN_REVIEW. Do not pick an arbitrary invoice.

## Decision Criteria

- Strong unique evidence can AUTO_APPLY.
- Equally plausible exact matches must not be auto-applied.
- Precedent never overrides a named live invoice, a stale paid reference, or an unknown customer.
- A human correction stored from a prior payment is evidence for a later similar pattern, not permission to ignore current ambiguities.

## Output Expectations

Return AUTO_APPLY, HUMAN_REVIEW, or UNAPPLIED; copy application amounts from a Python candidate; list ambiguities and a review_question when a person must choose; and say whether precedent affected the decision.

## Boundaries

- Do not calculate combination totals yourself.
- Do not invent invoices or apply more than the payment or the outstanding balance.
- Do not silently pick a winner among equal exact matches.
- Do not treat a paid invoice reference as a live match.
- Validation will reject invalid proposals; do not expect Python to auto-correct them.
