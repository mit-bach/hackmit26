---
name: financial-variance-analysis
description: Explain period, budget, or forecast financial variances from Python account and transaction attribution. Use when a preparer or reviewer must say why a metric moved.
status: new
---

# Financial Variance Analysis

## Purpose

Turn Python-computed metric movements, account deltas, and transaction contributors into a controller-quality explanation without inventing causes.

## When to Use

Apply when Bot `story` Profile `flux` (Variance Analysis Agent) receives a computed `VarianceExplanation`. Python has already totaled the ledger, ranked contributors, and isolated the residual. Reporting Reviewer Agent is a Kernel constructor only, not a Bot.

## Inputs / Evidence

Use get_variance_facts and get_variance_trace. Authoritative Python outputs include:

- current and comparison metric values
- dollar variance
- named contributors with transaction IDs, journal IDs, and source documents
- quantity / rate / mix effects when present
- unexplained residual

Do not search the raw ledger and do not recalculate margins or contributor shares.

## Procedure

1. Read the metric, periods, and dollar variance first.
2. Treat `kind=verified` contributors as established causes. Cite their transaction IDs. Gross-margin explanations must include revenue as well as COGS contributors.
3. Treat `kind=likely` contributors as possible, not proven.
4. Leave the residual unexplained. Say that it is unexplained.
5. If quantity and rate effects exist, describe them as Python computed them.
6. Flag any narrative impulse that is not backed by a contributor. Reject a supplier-cost story when a larger verified driver (hosting, freight, or revenue / discounting) exists.
7. If an initial explanation omits a material contributor so the remaining amounts do not reconcile to the variance, return the case. Do not approve an incomplete attribution.

## Decision Criteria

- A material move can be explained only by Python contributors plus residual.
- Residual is not a license to guess hosting, freight, mix, FX, or demand.
- Missing transaction IDs on a named contributor is a review failure, not something to paper over.

## Output Expectations

Write a short narrative that names verified contributors, marks likely ones, and states the unexplained amount. Keep evidence IDs. Do not add unsupported claims.

## Boundaries

- Do not recalculate totals, percentages, or shares.
- Do not invent vendors, invoices, or quantities.
- Do not explain residual amounts.
- Python reconciliation is authoritative; a broken tie must be escalated.
