---
name: reconciliation-exception-investigation
description: Investigate unmatched cash without inventing a story. Memory of payout labels cannot override missing fee evidence.
status: new
---

# Reconciliation Exception Investigation

## Purpose

Explain unmatched cash only with evidence Kernel already attached. If the evidence does not support an explanation, leave the break unexplained and Handle `ctl-cash`.

## When to Use

Wear this as Bot `cash` Profile `investigate` when the preparer could not confirm a clean tick, or when Kernel already flagged a duplicate, unexplained difference, or fee without evidence.

## Inputs / Evidence

The unmatched bank line, Kernel candidates, `get_fee_evidence`, `get_pipe_identifier`, and this Bot's Memory of processor payout labels. Precedent is color. It cannot override a live missing fee id.

## Procedure

Restate the Python difference exactly. Say what would count as evidence for a fee, FX, timing, or duplicate story. Do not write that story unless Kernel already computed it. A messy memo is a reading problem, not a new amount.

The planted Northstar residual stays unexplained. Helios-class fee-netted is the cousin that has Kernel fee evidence. Do not collapse them.

## Decision Criteria

- Recommend EXPLAINED_EXCEPTION only when Kernel fee evidence already exists.
- Recommend OUTSTANDING_TIMING_ITEM only when Kernel already named the adjacent-period counterpart.
- Recommend HUMAN_REVIEW for unexplained residuals, duplicates, and missing identifiers.
- Never recommend MATCHED for an unexplained remainder.

## Output Expectations

`InvestigationNote` with findings, supported explanations, unsupported hypotheses, and the dollar difference preserved. Queue owner is `ctl-cash`, not a person.

## Boundaries

- Do not invent a fee, FX rate, discount, or missing invoice to make the rec tie.
- Do not recalculate Python differences.
- Do not treat “it is small” as an explanation.
- Investigators recommend. They do not post.
- Memory of “this processor usually labels payouts this way” cannot mint `FEE-729103` or clear $12.40.
