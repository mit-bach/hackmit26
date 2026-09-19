---
name: invoice-source-identification
description: Distinguishes vendor invoices from quotes, receipts, statements, marketing, purchase orders, payment confirmations, and reimbursements. Use when classifying messy AP source records.
status: extracted
---

# Invoice Source Identification

## Purpose

Give an ingestion agent a consistent way to decide whether a source record is a vendor invoice that should become an InvoiceCandidate.

## When to Use

Apply when inspecting emails, attachments, employee uploads, vendor-portal files, scanned mail, or procurement documents that may or may not be invoices.

## Inputs / Evidence

Inspect only tool-loaded content:

- subject, body, filename, and attachment text
- declared document_type when the source provides one
- employee notes and channel metadata
- extracted document text and page markers

Do not invent missing attachments or filenames.

## Procedure

1. Read the specific record the agent was asked about.
2. For emails, inspect each attachment separately. Body-only marketing or a quote must not create an invoice candidate.
3. Classify using document language and required invoice fields, not sender reputation.
4. If the record is not an invoice, set classification to the matching non-invoice label and leave candidate null.
5. If multiple attachments exist, return a candidate only for attachments that are actually invoices.

## Decision Criteria

- **marketing**: unsubscribe, newsletter, limited-time offer, or other promotional language with no request for payment against an invoice number.
- **quote**: quotation, quote number, quoted amount, or estimate-valid language. Quotes are not invoices.
- **payment_confirmation**: payment received, thank-you-for-your-payment, or similar confirmation that money already moved.
- **statement**: account statement, statement of account, or explicit "this is not an invoice". Portal statements are not invoices even if they list charges.
- **purchase_order** / requisition: purchase request, requisition, or procurement document_type that is not invoice / vendor_invoice.
- **receipt** / reimbursement: employee receipts (rides, meals), reimbursement documentation, or screenshots that lack invoice fields.
- **invoice**: the document is a vendor request for payment and includes a vendor, an invoice number, an invoice date, and an amount due / total.
- **unreadable**: no usable extracted text.
- **not_invoice**: invoice language appears but required invoice fields are missing, or nothing supports an invoice classification.

A bank or card charge is not classified here; use bank-charge-invoice-discovery.

## Output Expectations

Return a short factual classification and reason. If classification is not invoice, candidate must be null. Do not expose hidden chain-of-thought.

## Boundaries

- Do not approve invoices, decide accounting treatment, or create accruals.
- Do not invent vendors, amounts, invoice numbers, or attachments.
- Do not treat a structured ERP/EDI python_parse as a messy document; those sources already mapped fields in Python.
- Do not re-implement regex parsing, hashes, or schema validation in prose.
