---
name: bank-charge-invoice-discovery
description: Treats bank and corporate-card charges as non-invoices and recovers an invoice candidate only when supporting invoice documentation exists. Use when inspecting card or bank transactions for missing vendor bills.
status: extracted
---

# Bank Charge Invoice Discovery

## Purpose

Decide whether a bank or corporate-card charge can be tied to actual invoice documentation. A charge itself is never an invoice.

## When to Use

Apply to one bank or card transaction during invoice ingestion / discovery.

## Inputs / Evidence

- the bank/card transaction from get_bank_transaction
- related invoice documentation from find_related_invoice
- any source refs or supporting document fields those tools return

## Procedure

1. Load the transaction. Do not manufacture invoice fields from the charge description, merchant name, or amount.
2. Search for supporting invoice documentation with find_related_invoice.
3. If supporting documentation is found, copy invoice fields from that documentation onto the candidate. Set source_type to bank_card and source_id to the transaction_id.
4. If nothing is found, return no candidate.

## Decision Criteria

- **invoice_found**: supporting invoice documentation exists. Candidate is copied from that documentation, not from the charge.
- **invoice_missing**: no supporting invoice documentation.
- **needs_follow_up**: the charge may relate to a vendor bill, but documentation is incomplete and no candidate should be invented.

Amount, merchant, and posted date on the charge are not sufficient to create an InvoiceCandidate.

## Output Expectations

Return BankAgentOutput. candidate is non-null only when status is invoice_found. Keep reasons short and factual.

## Boundaries

- Do not treat a charge as an invoice.
- Do not invent invoice numbers, vendors, or amounts from the transaction.
- Do not calculate invoice totals or dates from the charge.
- Do not approve payment, match PO/receipts, or book accruals.
- Do not decide that a missing invoice should be accrued; that belongs to the Accrual Agent.
