---
name: accrual-evidence-evaluation
description: Judges whether period-end evidence supports accruing a missing vendor invoice, skipping because the bill already arrived, or returning insufficient evidence. Use during month-end close for one vendor.
status: extracted
---

# Accrual Evidence Evaluation

## Purpose

Decide whether an expense was probably incurred this period and remains unbilled, before any estimation method is booked.

## When to Use

Apply for one vendor and one accounting period when closing expense accruals.

## Inputs / Evidence

Load evidence with tools; do not invent it:

- current-period invoices
- invoice history
- vendor contract and usage
- purchase orders and goods receipts
- Python estimate candidates from get_estimate_candidates

## Procedure

1. Load current-period invoices first. If an invoice for the period already exists, no accrual is needed.
2. Look for a reliable signal that work or goods were incurred this period: usage, an active contract cadence, a goods receipt, or a fresh recurring billing history.
3. Open the finance record. Those amounts and applicability flags are authoritative.
4. If evidence is weak, do not stretch a stale or unrelated number into an accrual.
5. Accrue only when the expense was probably incurred this period and the invoice is missing.

## Decision Criteria

- **no_accrual_needed** when a current-period invoice already exists.
- **accrual_required** when evidence shows the expense was incurred and is still unbilled, and an applicable Python candidate exists.
- **insufficient_evidence** when there is no reliable signal that work was incurred. Do not accrue a stale one-off invoice or an unapproved / unreceived draft PO.
- Goods received and not invoiced are a strong incurred signal. Python will enforce an unbilled goods-receipt accrual if the model skips it.
- If evidence is weak, estimated_amount must be null.

## Output Expectations

Return AccrualDecision with status, evidence, confidence, and reasoning. Copy estimated_amount from the chosen Python candidate exactly, including cents. Copy expense_account from the tool output.

## Boundaries

- Never invent invoices, POs, receipts, contracts, usage, amounts, or vendors.
- Do not recalculate arithmetic; use get_estimate_candidates / compute_accrual_estimate.
- Do not handle prepaid amortization, depreciation, or balance-sheet recs.
- Do not book a journal by inventing an amount the Python candidates did not produce.
