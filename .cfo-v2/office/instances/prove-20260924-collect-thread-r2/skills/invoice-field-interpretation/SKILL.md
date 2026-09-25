---
name: invoice-field-interpretation
description: Interprets messy invoice documents and extracts vendor, invoice number, dates, currency, amounts, PO, and provenance without inventing fields. Use when reading email attachments, scans, portal PDFs, or employee uploads.
status: extracted
---

# Invoice Field Interpretation

## Purpose

Extract a vendor invoice into InvoiceCandidate fields from unstructured or semi-structured text.

## When to Use

Apply after invoice-source-identification has classified the record as an invoice, or when a document is clearly a vendor invoice and fields must be read from text.

## Inputs / Evidence

Use only the loaded document text and source metadata:

- labeled fields such as Invoice Number, Invoice Date, Due Date, Amount Due, Total, PO Number, Vendor ID
- vendor name on the document or a source-provided vendor hint
- email from/subject, portal name, filename, document hash, and page references

Python may already have parsed structured ERP/EDI records. Prefer those parsed fields when present.

## Procedure

1. Copy values from labeled fields. Do not guess an unlabeled number is the invoice total.
2. Capture vendor, vendor invoice number, invoice date, due date, currency, subtotal, tax, amount due, PO number, and line items when they are present.
3. Preserve provenance on the candidate: source_type, source_id, source_uri, filename, attachment id, document hash, and page refs.
4. If a field is absent or unreadable, leave it empty. Downstream Python validation decides whether the candidate is complete.
5. Keep extraction_confidence lower when fields are sparse or the text is noisy.

## Decision Criteria

- Prefer explicit labels ("Invoice Number", "Amount Due", "PO") over incidental numbers in the body.
- A vendor hint from the portal or email may be used only when it appears consistent with the document.
- Do not normalize or recompute tax, subtotal, or total. If the document states conflicting totals, extract what is labeled and let Python validation reject inconsistent math.
- Do not invent a PO, currency, or invoice number to make the candidate look complete.

## Output Expectations

Return an InvoiceCandidate with extracted fields and evidence snippets that show where each important value came from. Keep classification.reason short and factual.

## Boundaries

- Do not approve payment or perform two-/three-way matching against POs and receipts.
- Do not calculate totals, tax, hashes, or date arithmetic.
- Do not overwrite Python-parsed EDI/ERP fields unless a field was empty or Python flagged a parse error.
- Do not create accruals or decide accounting treatment.
