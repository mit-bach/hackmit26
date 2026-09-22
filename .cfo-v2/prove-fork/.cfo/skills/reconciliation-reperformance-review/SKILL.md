---
name: reconciliation-reperformance-review
description: Compare an independent Python re-performance to the original reconciliation without using the original conclusion as an input.
status: new
---

# Reconciliation Re-performance Review

## Purpose

Review whether an independently recomputed bank, payout, cash-application, or accrual reconciliation agrees with the original recorded result.

## When to Use

Apply after Python has re-run propose_matches, AR cash-application policy, or accrual error math and produced a ReperformanceRecord.

## Inputs / Evidence

Use the re-performance record:

- source IDs
- original result
- independently recomputed result
- differences
- tolerance
- agreed flag
- used_original_as_input, which must be false
- evidence trace

## Procedure

1. Confirm used_original_as_input is false. If it is true, say the test is invalid.
2. Compare match type, status, invoice IDs, or estimation error using the differences list Python already computed.
3. If agreed is true, report that independent re-performance supports the original workflow.
4. If agreed is false, report a finding and cite both results.
5. Do not re-select a match from the original conclusion.

## Decision Criteria

- PASS / AGREE when differences are empty or within the stated tolerance.
- FAIL / DISAGREE when match type, status, invoices, or error differ beyond tolerance.
- HUMAN_REVIEW only when Python already marked the independent result that way.

## Output Expectations

State agreement or disagreement, the tolerance used, and the source IDs that support the conclusion.

## Boundaries

- Do not recalculate bank, ledger, payout, or accrual amounts.
- Do not pass the original final conclusion into the re-performance calculation.
- Stripe and Adyen payout math stays in the existing provider adapters; do not reimplement it.
- Python owns matching, cents arithmetic, and tolerance checks.
