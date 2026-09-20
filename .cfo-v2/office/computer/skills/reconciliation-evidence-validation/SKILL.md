---
name: reconciliation-evidence-validation
description: Accepts a bank-to-ledger match only when entity, date, type, and source evidence support the relationship, not when amounts merely coincide.
status: new
---

# Reconciliation Evidence Validation

## Purpose

Prevent false cash matches. A reconciliation is valid only when the selected records share an economic relationship.

## When to Use

Apply when preparing or reviewing a cash match, including exact, grouped, fee-netted, provider-payout, near-amount, and unexplained-difference candidates.

## Inputs / Evidence

- Python match candidates
- bank counterparty, description, reference, date, type, and provider
- ledger counterparty, reference, date, and entry type
- fee advice and payout membership when present

## Procedure

1. Confirm amount relationship (equal, grouped sum, or fee-netted residual).
2. Confirm date compatibility for the proposed match type.
3. Confirm entity identity: counterparties compatible, shared invoice/reference, or named provider payout.
4. Confirm transaction type is consistent (refund with refund, payout with payout, vendor payment with AP cash).
5. Reject the match if the only shared fact is the dollar amount.
6. Reject unrelated records that happen to close a gap, including old invoices, look-alike customer names, vendor credits, and historical journals with no source link.
7. Never invent a transaction or rewrite source data to force the accounts to tie.

## Decision Criteria

- MATCHED only with amount + date + identity/source linkage.
- HUMAN_REVIEW when two equally plausible counterparts exist.
- UNEXPLAINED_DIFFERENCE when a residual has no fee or timing evidence.
- Do not post adjusting entries automatically.

## Output Expectations

Name the linkage that supports the match, or name the missing evidence. Cite bank and ledger IDs. Do not output a new amount.

## Boundaries

- Do not recalculate Python sums.
- Do not treat Stripe gross charges as the bank deposit.
- Do not override a unique Python candidate with a narrative.
