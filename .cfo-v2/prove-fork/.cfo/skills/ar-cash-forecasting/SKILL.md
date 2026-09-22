---
name: ar-cash-forecasting
description: Interpret a Python receivable schedule for a 13-week cash forecast. Use when judging collection timing, disputed invoices, promises to pay, and uncertain cash.
status: new
---

# AR Cash Forecasting

## Purpose

Explain when open receivables are likely to become cash, using the Python schedule as the only source of dates and amounts.

## When to Use

Apply when Bot `story` Profile `forecast` (Cash Forecast Agent) reviews weekly AR inflows. Python has already assigned expected dates, amounts, confidence, and base-case inclusion.

## Inputs / Evidence

Use the receivable schedule. Trust:

- expected_collection_date / expected_collection_amount
- source_due_date
- promise-to-pay and dispute flags
- customer payment-behavior facts
- whether the item is in the base case

Do not calculate weekly totals or ending cash.

## Procedure

1. Treat an undisputed invoice due next week as a base-case candidate for that week.
2. If the customer promised a date, that date outranks the original due date.
3. Leave disputed invoices out of certain near-term cash.
4. A historically late customer may be shifted later; do not pull them forward.
5. Unapplied or HUMAN_REVIEW cash already received is not a future collection.
6. If confidence is low, keep the item visible as uncertain rather than inventing a better date.

## Decision Criteria

- Promise-to-pay wins over the original due date.
- Disputes are never certain cash.
- Precedent about batch payers or late payers is evidence, not a license to override a paid invoice or a live remittance.
- Do not move an amount into a week Python did not compute.

## Output Expectations

Comment on timing risk and uncertain items. Copy invoice IDs and amounts from the Python schedule. Say which assumptions matter.

## Boundaries

- Do not recalculate aging, weekly cash, or payroll.
- Do not put disputed AR into the base case.
- Do not double count cash that has already been received.
- Accounting invariants stay in Python.
