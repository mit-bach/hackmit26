---
name: bank-reference-interpretation
description: Read messy bank memos and processor payout labels. Do not invent invoice numbers or counterparties. Memory is color, not fee evidence.
status: new
---

# Bank Reference Interpretation

## Purpose

Read a noisy bank string well enough to compare it with Kernel candidates and apply/pay identifiers. The skill interprets labels. It does not create matches.

## When to Use

Wear this when a bank description is truncated, uses a trade name, or looks like a processor payout label (STRP, ADY, STRIPE, ADYEN).

## Inputs / Evidence

Bank description, reference, and counterparty fields. Ledger counterparty and invoice/reference. `get_pipe_identifier`. This Bot's Memory of how this processor usually labels a deposit. Python overlap scores.

## Procedure

Treat the bank string as a memo. Keep distinctive tokens and explicit references. Do not promote them into invoice ids unless the ledger already contains that id. If apply or pay already named the line, the memo cannot rename the customer or vendor.

Processor labels belong to the Stripe/Adyen waterfall, not to an AP invoice. Remember this processor's usual payout wording for next period. That habit cannot override missing fee evidence.

## Decision Criteria

- A memo token may support compatibility when Kernel amounts already agree and the pipe identifier, if present, is the same party.
- Conflicting names with no identifier stay on HUMAN_REVIEW even if amounts agree.
- A payout-shaped label is a deposit for `cash` and charge-level facts for `apply`. It is not a vendor bill.

## Output Expectations

Cite the tokens you used and whether they support, weaken, or are silent on the candidate. Do not output a new amount or a fabricated invoice number.

## Boundaries

- Do not recalculate amounts from the description.
- Do not invent counterparties, invoice numbers, or remittance details that are not in the text.
- Do not treat a truncated merchant descriptor as proof of a grouped ACH. Grouping still requires Python’s exact sum.
- Do not use payout-label Memory as a fee id.
