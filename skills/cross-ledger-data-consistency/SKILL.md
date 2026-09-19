---
name: cross-ledger-data-consistency
description: Keep one economic event aligned across AP/AR, GL, bank, forecast, close, audit, and reporting without inventing a second copy.
status: new
---

# Cross-Ledger Data Consistency

## Purpose

Make sure a planted business event keeps the same identity and amount as it moves across finance functions.

## When to Use

Apply when a later sample-data agent consumes AP, AR, cash, or journal objects created upstream.

## Inputs / Evidence

Use the shared context. Authoritative identities include:

- invoice IDs, payment IDs, bank transaction IDs, journal IDs
- integer-cent amounts already stored on those objects
- existing foreign keys (PO, customer, vendor, source document)

Do not create a parallel ledger or a board-pack number that is not summed from GL lines.

## Procedure

1. Locate the canonical source object before writing a downstream record.
2. Copy the ID and amount. Adapt the schema if the consumer uses a different model.
3. Every close evidence row, forecast actual, and audit population item must point at an existing object.
4. If a required consumer field does not exist on the source model, map it explicitly.
5. If validation would fail, stop. Do not silently repair amounts.

## Decision Criteria

- Same economic event → same ID and amount everywhere.
- No orphan foreign keys.
- Operational inputs never include the hidden answer key.

## Output Expectations

Downstream records that reference source IDs. Memos may describe the business event; they may not invent a new total.

## Boundaries

Do not recalculate reconciliation differences, forecast ending cash, or gross-margin percentages. Those stay in Python validators.
