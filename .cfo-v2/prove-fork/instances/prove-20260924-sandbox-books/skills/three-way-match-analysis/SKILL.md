---
name: three-way-match-analysis
description: Interprets Kernel three-way facts when the packet is messy or uncertain. Does not restate must_hold. Use when preparing an open bill.
status: extracted
---

# Three-Way Match Analysis

## Purpose

Read Kernel three-way facts and say what is still uncertain about *this* vendor's bill. Python already typed exceptions and already vetoes illegal APPROVE.

## When to Use

Wear this as Bot `ap` Profile `prepare` after the finance record returns. Do not use it to rebuild `must_hold`.

## Inputs / Evidence

Authoritative Kernel fields: `exception_types`, `amount_difference`, `within_amount_tolerance`, `vendor_exact_match`, `vendors_are_similar`, `receipt_status`, `duplicate_detected`. Do not recalculate them.

## Procedure

Look at how this packet differs from a boring clean match. Name the vendor-specific mess: layout, alias wording, receipt lag, a revised PDF. Copy Kernel `exception_types`. Do not invent a type. Do not write a second hold checklist.

## Decision Criteria

- Recommend APPROVE only when Kernel facts are already clean and you are not filling a hole.
- Recommend INVESTIGATE when the type list is true but this vendor's document still needs sense.
- Recommend HOLD when you will not guess. Kernel `must_hold` still runs after you.

## Output Expectations

`PreparerRecommendation` with Kernel exception types copied, record IDs in `evidence_used`, and a short reason about this bill. Do not invent a tolerance or alias.

## Boundaries

- Do not recalculate amounts, dates, or variances. Python owns those.
- Do not override `must_hold` with precedent or a similar prior bill.
- Do not pay. Do not concur. Approve-shaped drafts Handle `ctl-pay` / `review-match`.
