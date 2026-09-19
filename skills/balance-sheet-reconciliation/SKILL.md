---
name: balance-sheet-reconciliation
description: Classifies ledger-versus-evidence differences using Python packets. Use for cash, AR, AP, accruals, prepaids, and fixed-asset sign-off.
status: new
---

# Balance Sheet Reconciliation

## Purpose

Explain whether a balance-sheet account is supported by independent evidence and whether it can be signed off.

## When to Use

Apply when preparing or reviewing a GL-to-subledger or GL-to-register reconciliation for cash, AR, AP, accrued expenses, prepaids, or fixed assets.

## Inputs / Evidence

Use get_reconciliation_packet and list_reconciling_items. The packet already contains ledger_balance, evidence_balance, difference, and classified items.

## Procedure

1. Read the Python finding implied by the packet. Do not recompute the difference. When a period GL control balance is present, compare it to the subledger or register; a difference is an open reconciling item.
2. Exact match → MATCHED. Explained timing items that fully bridge the difference → EXPLAINED_DIFFERENCE. GL accounts with no supporting evidence stay unsupported.
3. Missing or stale evidence, duplicate support, or arithmetic inconsistency → do not sign off.
4. Unexplained remainder → HUMAN_REVIEW. Never relabel it as a match.

## Decision Criteria

- Ledger equals evidence and no unexplained items → sign-off is allowed after review.
- Timing items that sum to the difference → explained, not forced.
- Missing source documents → BLOCKED / request evidence.
- Unexplained cash or unmatched AR cash → escalate.

## Output Expectations

Return finding, status, explanation, and whether the case should be escalated. Cite packet evidence, not a new story.

## Boundaries

- Do not recalculate ledger or evidence totals.
- Do not silently force a reconciliation to match.
- Do not invent reconciling items that are not in the packet.
- Do not sign off when a supporting document is missing.
