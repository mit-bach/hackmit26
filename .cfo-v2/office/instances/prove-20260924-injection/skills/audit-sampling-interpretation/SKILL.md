---
name: audit-sampling-interpretation
description: Interpret a Python-selected audit sample without choosing transactions or changing the seed.
status: new
---

# Audit Sampling Interpretation

## Purpose

Explain a reproducible sample that Python already selected so a reviewer can see coverage, risk concentration, and residual unsampled risk.

## When to Use

Apply after the audit sampler has returned population size, eligible IDs, method, seed, risk criteria, and sampled IDs.

## Inputs / Evidence

Use only the SampleRecord facts Python produced:

- population name and size
- eligible IDs
- sampling method (random or risk_based)
- seed
- risk criteria and risk scores
- sampled IDs
- audit run ID and period

## Procedure

1. Restate the population and how many items were eligible.
2. Name the method and seed. Do not propose a different sample.
3. If the method is risk-based, summarize which documented risk signals were present on sampled IDs.
4. Identify high-risk IDs that were eligible but not sampled only when Python's scores show they existed.
5. Cite sample_id and object IDs from the payload.

## Decision Criteria

- The sample is defensible when a reviewer can re-run Python with the same seed and recover the same IDs.
- Residual risk is a coverage observation, not a finding, unless a control later fails on an unsampled item.
- Do not treat an unsampled ordinary item as cleared.

## Output Expectations

State what was sampled, why those IDs were eligible, and which sample metadata a reviewer needs to reproduce the selection.

## Boundaries

- Do not randomly choose transactions.
- Do not recalculate risk scores or invent IDs that are not in the sample record.
- Python owns sampling, seeding, and score arithmetic.
