---
name: superseded-document-handling
description: Distinguishes original invoices from revisions, voids, credit memos, and duplicate copies so only the live payable remains.
status: new
---

# Superseded Document Handling

## Purpose

Keep one live vendor payable when several documents refer to the same economic bill.

## When to Use

Apply after invoice-source-identification when a document is a revision, void, credit memo, duplicate copy, or a second thread that repeats an already ingested invoice.

## Inputs / Evidence

- current document text, subject, and filename
- canonical identity (normalized vendor + invoice number)
- prior canonical invoice or AP overlay record for the same key
- Python flags such as supersedes, voided, credit_memo, duplicate

## Procedure

1. Identify whether the document is an original payable, a revision of a named prior invoice, a void, a credit memo, or another copy of an existing bill.
2. If it is a void or credit memo, do not create a payable. Link it to the original if the original exists.
3. If it replaces an earlier invoice number, treat the earlier number as superseded. The revision is the live bill only after validation. Do not pay both.
4. If vendor and invoice number already exist, attach provenance. Do not open a second payable.
5. Same invoice number across two different vendors is not a duplicate. Keep both identities separate.

## Decision Criteria

- Void / cancelled / credit memo → not payable.
- Revision that names the prior invoice → one live bill; prior number is superseded.
- Exact or formatted duplicate of the same vendor+number → collapse; do not pay twice.
- Two vendors sharing a number → two bills.

## Output Expectations

State whether a payable should exist, which prior document is superseded or duplicated, and which records were rejected. Do not invent the prior invoice number.

## Boundaries

- Do not approve payment or book accruals.
- Do not treat a statement total as a new invoice.
- Python owns canonical keys, hashes, and overlay persistence.
