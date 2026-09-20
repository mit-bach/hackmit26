---
name: cash-application
description: Chooses among Kernel remittance-match candidates for one customer payment. Use when Bot apply wakes on a remittance path, including an ambiguous or material deposit.
status: new
---

# Cash Application

## Purpose

Stick incoming customer cash to the right open invoices. Abstain when two explanations are equally good. Do not post a guess.

## When to Use

Use when Bot apply, Profile apply, evaluates one payment. Kernel already built the candidate sets (named invoice, exact amount, combinations, stale references). ctl-cash / review-apply uses the same procedure on a fail-closed packet.

## Inputs / Evidence

Call get_cash_application_facts. Authoritative Kernel outputs include:

- identified customer and confidence
- remittance invoice IDs and stale / paid references
- candidate applications with amounts and unapplied remainder
- customer remittance precedent

Do not search new invoice combinations. Do not recalculate totals. Wake text names a path. Do not paste the remittance into Memory.

## Procedure

1. Read the remittance evidence hierarchy: explicit invoice number, then identified customer plus unique exact amount, then a unique combination, then precedent as supporting color only.
2. If the memo names a live invoice and the amount is at or below outstanding, AUTO_APPLY that candidate as a full or partial application. Do not mark the invoice fully paid when a residual remains.
3. If one customer has exactly one invoice matching the amount, AUTO_APPLY.
4. If two candidates both explain the amount exactly (single invoice vs combination, or two invoices with the same balance), HUMAN_REVIEW. Write the packet. Handle ctl-cash / review-apply. Do not post. Do not ask a person.
5. If the payer cannot be identified, UNAPPLIED or HUMAN_REVIEW. Do not guess.
6. If remittance names a customer or invoice that conflicts with the bank sender or tagged customer, HUMAN_REVIEW. Do not guess.
7. If remittance cites an invoice ID that does not exist, HUMAN_REVIEW as an invalid reference.
8. If the payment amount exceeds the named invoice outstanding, HUMAN_REVIEW and preserve the residual. Do not drop it.
9. If the payment is already APPLIED or PARTIALLY_APPLIED, refuse a second application.
10. After ctl-cash resolves a packet, treat stored precedent as scoped evidence for similar later remittances. It must not override a contradictory live remittance or an accounting invariant.

## Decision Criteria

- Strong unique evidence can AUTO_APPLY.
- Equally plausible exact matches must not be auto-applied.
- Precedent never overrides a named live invoice, a stale paid reference, or an unknown customer.
- HUMAN_REVIEW means fail-closed. Autonomy is not post-anyway.
- A stored correction is evidence for a later similar pattern, not permission to ignore current ambiguities.

## Output Expectations

Return CashApplicationProposal. Decision is AUTO_APPLY, HUMAN_REVIEW, or UNAPPLIED. Copy application amounts from a Kernel candidate. List ambiguities and a review_question as packet text for ctl-cash, not a question to a person. Say whether precedent affected the decision.

## Boundaries

- Do not calculate combination totals yourself.
- Do not invent invoices or apply more than the payment or the outstanding balance.
- Do not silently pick a winner among equal exact matches.
- Do not treat a paid invoice reference as a live match.
- Do not dun customers. That object belongs to Bot collect.
- Do not call create_accrual, pay-run tools, or collection tools.
- Do not ask an AE. There is no AE.
- Validation will reject invalid proposals. Do not expect Python to auto-correct them.
