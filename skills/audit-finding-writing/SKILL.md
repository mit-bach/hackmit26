---
name: audit-finding-writing
description: Write audit findings and report language from structured Python facts without inventing counts, IDs, or severity.
status: new
---

# Audit Finding Writing

## Purpose

Turn structured findings and ReportStats into reviewer-facing language that stays tied to evidence.

## When to Use

Apply when the deterministic audit run has already produced findings, unresolved items, and report statistics.

## Inputs / Evidence

Use only:

- ReportStats counts and finding IDs
- each finding's title, condition, expected policy, result, severity, and rationale
- affected object IDs and evidence IDs
- re-performance agreement counts
- unresolved HUMAN_REVIEW items

## Procedure

1. Copy passed, failed, exception, human-review, and finding counts from ReportStats.
2. For each finding, restate the condition, expected control, IDs, and severity rationale.
3. List evidence and source trace IDs. Do not add IDs that are not in the payload.
4. Separate unresolved HUMAN_REVIEW items from failed controls.
5. If asked for a narrative report, use the deterministic report draft as the source of counts.

## Decision Criteria

- A finding exists only when Python created one.
- Severity stays at the documented level unless the payload itself changes.
- Report totals must equal the structured counts.

## Output Expectations

A finding-by-finding explanation and a report that cites the same IDs and totals Python computed.

## Boundaries

- Do not invent counts, finding IDs, invoice IDs, or monetary exposure.
- Do not recalculate totals or exposure.
- Do not classify every failure as high severity.
- Python owns statistics, exposure, and ID linkage.
