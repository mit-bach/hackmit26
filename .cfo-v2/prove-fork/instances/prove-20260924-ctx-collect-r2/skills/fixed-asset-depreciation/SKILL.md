---
name: fixed-asset-depreciation
description: Distinguishes capital assets from period expenses and reviews Python straight-line depreciation. Use for equipment, machinery, and capitalized software.
status: new
---

# Fixed Asset Depreciation

## Purpose

Decide whether a purchase should be capitalized and whether the Python depreciation (or intangible amortization) schedule should be posted.

## When to Use

Apply when an AP invoice looks like equipment, a laptop fleet, machinery, or capitalized software rather than a period expense.

## Inputs / Evidence

Use get_capital_candidates and get_depreciation_schedule. Python already computes depreciable basis, monthly amounts, salvage floors, and duplicate flags.

## Procedure

1. If vendor, cost, and acquisition date match an existing register item, choose duplicate_review. Do not create a second asset.
2. If acquisition evidence is missing, do not capitalize.
3. Use the Python capitalization flag (cost and useful life). Do not invent a threshold.
4. Copy depreciation amounts from the Python schedule. Intangible assets use the same schedule with amortization accounts.

## Decision Criteria

- Python python_capitalize true → capitalize.
- Below the Python threshold or short useful life → expense.
- Duplicate vendor + cost + date → escalate; do not silent-add.
- Period before placed-in-service → do not depreciate.

## Output Expectations

Return capitalize, expense, duplicate_review, or insufficient_evidence, plus evidence used and a short reason.

## Boundaries

- Do not recalculate straight-line amounts or book value.
- Do not let accumulated depreciation exceed depreciable basis.
- Do not drop book value below salvage.
- Do not invent useful lives or salvage values.
