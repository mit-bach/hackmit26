---
name: cash-reconciliation-method-selection
description: Distinguishes exact, grouped, fee-netted, timing, duplicate, provider, and unexplained cash matches using Python candidates only.
status: new
---

# Cash Reconciliation Method Selection

## Purpose

Choose the reconciliation method that the Python candidate list actually supports. The model selects a candidate; Python owns the amounts.

## When to Use

Apply when preparing or reviewing a bank-to-ledger match for a period, including ACH, wires, refunds, fees, and processor payouts.

## Inputs / Evidence

- Python match candidates from get_match_candidates / get_candidate
- bank transaction text and ledger counterparties
- fee-advice records when present
- Stripe/Adyen provider status already computed by the existing payout adapters

## Procedure

1. Ignore any story that does not correspond to a Python candidate.
2. Prefer a unique EXACT_MATCH when amount, sign, and dates agree and counterparties are compatible.
3. Prefer GROUPED_MATCH when several ledger entries from the same vendor/customer sum exactly to one bank amount.
4. Prefer FEE_NETTED only when Python attached fee evidence and a proposed (unposted) bank-fee entry.
5. Prefer PROVIDER_PAYOUT when the bank description is a Stripe or Adyen settlement and the existing adapter reports MATCH.
6. Treat TIMING_DIFFERENCE as an outstanding item when the same amount clears in an adjacent period. It is not an accounting error.
7. If two bank refunds or two identical ledger postings compete for one counterpart, match one and leave the extra as a duplicate suspicion.
8. If a small remainder has no supporting evidence, select UNEXPLAINED_DIFFERENCE. Do not relabel it as a fee.

## Decision Criteria

- MATCHED only for EXACT_MATCH, GROUPED_MATCH, or a clean PROVIDER_PAYOUT.
- EXPLAINED_EXCEPTION only for FEE_NETTED with evidence.
- OUTSTANDING_TIMING_ITEM for adjacent-period clearing.
- HUMAN_REVIEW for duplicates, unexplained differences, unmatched items, counterparty conflicts, or multiple similarly scored candidates.

## Output Expectations

Return a candidate_id from the Python list, a disposition, confidence, and the evidence IDs you used. Do not output a new amount.

## Boundaries

- Do not recalculate group sums, fees, or differences.
- Do not invent invoice numbers that are not in the records.
- Do not mark a break MATCHED because the narrative sounds plausible.
- Do not post the proposed bank-fee journal; it remains a recommendation.
