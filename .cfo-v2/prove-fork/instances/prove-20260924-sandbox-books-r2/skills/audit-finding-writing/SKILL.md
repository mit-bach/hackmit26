---
name: audit-finding-writing
description: Write audit findings from Kernel ReportStats without inventing counts, IDs, or severity.
status: new
---

# Audit Finding Writing

## Purpose

Turn structured findings and ReportStats into language that stays tied to Kernel finding IDs.

## When to Use

After the deterministic audit run. Profile `interpret` may call audit read ops. Profile `report` has `tools=[]` and writes from `ReportStats` on the packet. Report is not an office-live ledger searcher.

## Remainder

Copy passed, failed, exception, human-review, and finding counts from ReportStats. Restate each finding’s condition, expected control, IDs, and severity as Python attached them. If a finding ID is missing, omit the sentence.

Loud decoys are not the product. Do not retell a duplicate vendor, round wire, or GM move as the impressive find.

`HUMAN_REVIEW` on a finding is fail-closed, not a ticket to a person.

## Boundaries

- Do not invent counts, finding IDs, invoice IDs, or monetary exposure.
- Do not recalculate totals.
- Do not load the finance record in operational phase.
- Do not fix the books. `source_records_mutated` stays false.
- Do not concur on a pay-run. That object belongs to `ctl-pay`.
