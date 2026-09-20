---
name: bank-reference-interpretation
description: Interprets messy bank descriptions and remittance references without inventing invoice numbers or counterparties.
status: new
---

# Bank Reference Interpretation

## Purpose

Read noisy bank statement text well enough to compare it with ledger counterparties and Python candidates. The skill interprets labels; it does not create matches.

## When to Use

Apply when a bank description is incomplete, truncated, or uses a trade name that is not the legal ledger name. Use for ACH memos, wire references, card refund descriptors, and processor payout labels.

## Inputs / Evidence

- bank description, reference, and counterparty fields
- ledger counterparty, invoice/reference, and memo
- Python overlap scores already computed from those strings

## Procedure

1. Treat the bank string as evidence, not as a complete identity.
2. Keep tokens that look like counterparties (ACME INDUSTRIAL, NORTHLINE FAB, NORTHSTAR LLC).
3. Keep explicit references (8391, 729103, STRP-97420, CARD 8892). Do not promote them into invoice IDs unless the ledger already contains that ID.
4. Recognize processor labels: STRIPE / STRP and ADYEN / ADY refer to existing payout adapters, not to AP invoices.
5. Recognize refund language (REFUND CARD) as a possible customer refund, not a vendor payment.
6. If the bank text and ledger name share a distinctive token, that supports compatibility. If they name different parties, that is a conflict.
7. Missing invoice numbers in the bank text are normal. Do not invent INV- IDs to force a match.

## Decision Criteria

- Compatible names may still match when Python amounts and dates already agree.
- Conflicting names with no alias evidence should stay on HUMAN_REVIEW even if amounts agree.
- Processor payout text should be handed to the named Stripe or Adyen adapter rather than treated as a customer receipt.

## Output Expectations

Cite the tokens you used and whether they support, weaken, or are silent on the candidate. Do not output a new amount or a fabricated invoice number.

## Boundaries

- Do not recalculate amounts from the description.
- Do not invent counterparties, invoice numbers, or remittance details that are not in the text.
- Do not treat a truncated merchant descriptor as proof of a three-invoice group; grouping still requires Python’s exact sum.
