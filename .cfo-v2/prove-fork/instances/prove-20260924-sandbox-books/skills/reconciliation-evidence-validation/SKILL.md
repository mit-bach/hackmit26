---
name: reconciliation-evidence-validation
description: Accept a bank-to-ledger tick only when Kernel evidence and pipe identifiers support it. Coincident amounts are not enough.
status: new
---

# Reconciliation Evidence Validation

## Purpose

Say whether the selected Kernel candidate has an economic relationship, not just equal dollars. Apply/pay identifiers outrank a memo token.

## When to Use

Wear this when preparing or reviewing a cash tick, including fee-netted and unexplained residuals.

## Inputs / Evidence

Authoritative: Kernel `candidate_id`, `difference_minor`, `fee_evidence_ids`, `provider_status`, and the finance record. Bank description and payout-label Memory may support a reading. They cannot create a fee id.

## Procedure

Name the linkage that already exists: shared invoice/reference, pipe identifier, provider payout membership, or Kernel fee evidence. If the only shared fact is the dollar amount, it is not a tick. If apply named the customer, a look-alike name in the memo is not a second identity.

## Decision Criteria

- Support MATCHED only when Kernel already allows it and the identifier, if present, is copied.
- Missing fee advice is missing. Do not treat a small residual as a fee.
- Two equally plausible counterparts stay on HUMAN_REVIEW for `ctl-cash`.

## Output Expectations

Name the linkage or name the missing evidence. Cite bank and ledger ids. Do not output a new amount.

## Boundaries

- Do not recalculate Python sums.
- Do not treat Stripe gross charges as the bank deposit.
- Do not override a pipe identifier with a narrative.
- Do not load holdout residual explanations into operational books.
