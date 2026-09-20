---
name: reconciliation-exception-investigation
description: Investigates unmatched cash activity without inventing explanations. Use when a bank or ledger item does not have a unique supported match.
status: new
---

# Reconciliation Exception Investigation

## Purpose

Explain unmatched or mismatched cash activity using only available evidence. If the evidence does not support an explanation, leave the break unexplained and request human review.

## When to Use

Apply when the preparer could not confirm a clean match, when Python flagged a duplicate, unexplained difference, unmatched item, fee without evidence, or counterparty conflict.

## Inputs / Evidence

- the unmatched bank transaction and/or ledger entry
- Python candidates and their listed ambiguities
- fee advice, remittance text, provider payout status
- dates in the current and adjacent periods

## Procedure

1. Restate the Python difference exactly. Do not round it away.
2. Test each ordinary hypothesis only against evidence:
   - bank fee: requires a fee-advice record or a provider fee line
   - rounding: only a one-cent remainder
   - foreign exchange: requires a second currency or FX contract
   - partial payment: requires remittance that names a remaining balance
   - duplicate / missing entry: requires a second identical cash movement or a second identical GL posting
   - timing: requires the same amount in an adjacent period
3. If none of those is supported, say that the difference is unexplained.
4. Do not propose a journal entry unless Python already computed one from evidence.
5. Do not delete, net, or auto-apply the extra item.

## Decision Criteria

- Recommend EXPLAINED_EXCEPTION only when evidence actually supports the explanation Python already computed.
- Recommend OUTSTANDING_TIMING_ITEM when an adjacent-period counterpart exists.
- Recommend HUMAN_REVIEW for duplicates, unexplained differences, unmatched activity, and material unsupported adjustments.
- Never recommend MATCHED for an unexplained remainder.

## Output Expectations

List issues investigated, findings, supported explanations, unsupported hypotheses, and HUMAN_REVIEW when the break is still unexplained. Preserve the dollar difference in the findings.

## Boundaries

- Do not invent a fee, FX rate, discount, or missing invoice to make the rec tie.
- Do not recalculate Python differences.
- Do not treat “it is small” as an explanation.
- Investigators recommend; they do not post.
