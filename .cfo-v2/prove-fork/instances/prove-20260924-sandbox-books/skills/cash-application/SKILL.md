---
name: cash-application
description: Chooses among Kernel remittance-match candidates for one customer payment. Use when Bot apply wakes on a remittance path, including an ambiguous or material deposit.
status: extracted
---

# Cash Application

## Purpose

Stick incoming customer cash to the right open invoices. Abstain when two explanations are equally good. Do not post a guess.

## When to Use

Bot apply, Profile apply, one payment. Kernel already built the candidate sets. ctl-cash / review-apply uses the same remainder on a fail-closed packet.

## Inputs / Evidence

Open the finance record. Trust identified customer, remittance invoice IDs, candidate applications, unapplied remainder, and remittance precedent.

Do not search new invoice combinations. Do not recalculate totals.

## Procedure

1. Copy a Kernel candidate. Do not invent a combination.
2. AUTO_APPLY only when evidence is unique and strong (named live invoice, or one customer with one exact amount).
3. If two explanations both fit exactly, HUMAN_REVIEW. Handle ctl-cash / review-apply. Do not pick a winner to look autonomous.
4. After you post, Handle cash / match with the identified payment id. Cash does not re-guess the customer.

## Decision Criteria

- Unique named invoice may AUTO_APPLY through Kernel.
- Equally plausible exact matches stay fail-closed.
- Unknown payer stays UNAPPLIED or review. Residuals are not dropped.
- Precedent from a prior Verifier concurrence (or emergency CLI) may color a later similar remittance. It cannot override a live named invoice, a stale paid reference, or an unknown customer.
- HUMAN_REVIEW is fail-closed. Queue owner is ctl-cash. `ar-review-correct` is emergency only. It is not how apply finishes.

## Output Expectations

Return CashApplicationProposal. Decision AUTO_APPLY, HUMAN_REVIEW, or UNAPPLIED. Copy application amounts from a Kernel candidate. Say whether precedent affected the decision.

## Boundaries

- Do not dun. That object belongs to Bot collect.
- Do not treat HUMAN_REVIEW as permission to post.
- Do not call create_accrual, pay-run tools, or collection tools.
- Do not ask a person.
- Skills never grant tools.
