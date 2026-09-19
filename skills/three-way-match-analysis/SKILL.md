---
name: three-way-match-analysis
description: Interprets Python three-way-match facts to identify clean matches versus blocking or uncertain AP exceptions. Use when preparing, reviewing, approving, or auditing an invoice for payment.
status: extracted
---

# Three-Way Match Analysis

## Purpose

Read deterministic AP evidence and decide whether the invoice is a clean three-way match, an obvious hold, or an exception that needs investigation.

## When to Use

Apply to an AP case after get_case_evidence has returned Python facts for the invoice, PO, goods receipt, and duplicates.

## Inputs / Evidence

Use Python facts from get_case_evidence. Do not recalculate them:

- approved PO exists
- amount match / amount difference / within_amount_tolerance
- vendor exact match / vendors_are_similar
- receipt_status (full, partial, missing, not_received)
- duplicate_detected and duplicate invoice IDs
- exception_types

Supporting records may be loaded with get_invoice, get_purchase_order, get_goods_receipt, and find_duplicate_invoices.

## Procedure

1. Copy exception_types from get_case_evidence. Do not invent exceptions.
2. Confirm whether Python shows a clean match: approved PO, exact amount match, exact vendor match, full receipt, no duplicate.
3. If a blocking control is already obvious from those facts, recommend HOLD.
4. If the facts are uncertain rather than blocking, recommend INVESTIGATE rather than stretching to APPROVE.
5. Cite record IDs in evidence_used.

## Decision Criteria

- **APPROVE** only when Python facts show a clean three-way match: approved PO, exact amount match, exact vendor match, full receipt, and no duplicate.
- **HOLD** when a blocking control is already obvious: duplicate vendor invoice number, unapproved PO, missing or not-received goods, or missing PO.
- **INVESTIGATE** when there is uncertainty: vendor-name mismatch, amount variance, partial receipt, conflicting records, or anything unusual.

Exact duplicate detection, amount arithmetic, receipt completeness, and tolerance math are Python's job. This skill only interprets those facts.

## Output Expectations

State the match conclusion, the exception types copied from Python, and the preliminary recommendation. Do not invent a tolerance or alias.

## Boundaries

- Do not recalculate amounts, dates, or variances.
- Do not invent an approval threshold. Use only published policy values.
- Do not make the final payment if another agent owns approval; Preparers recommend, they do not finalize.
- Do not override a must_hold control with historical precedent.
