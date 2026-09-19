---
name: synthetic-finance-scenario-design
description: Choose among approved finance scenario templates so one economic event can be instantiated consistently across AP, cash, close, audit, and reporting.
status: new
---

# Synthetic Finance Scenario Design

## Purpose

Select which approved scenario templates to instantiate for a shared synthetic company. The goal is one internally consistent dataset, not five disconnected fixtures.

## When to Use

Apply when a sample-data agent plans a generation run. Python already owns IDs, dates, amounts, and arithmetic.

## Inputs / Evidence

Use the scenario registry. Authoritative inputs include:

- approved `scenario_id` values
- the shared `CompanyScenarioContext`
- existing domain models and ID conventions
- which earlier agents have already created source IDs

Do not invent a new numeric outcome or a second identity for an existing invoice, payment, or journal.

## Procedure

1. Choose only templates from the registry.
2. Prefer combinations that create a followable demo thread (clean, resolved exception, unresolved review).
3. Later agents must consume IDs created by earlier agents.
4. Narrative text may describe the business story. It must not encode hidden answers such as match IDs.
5. Leave expected machine answers in the isolated answer-key file.

## Decision Criteria

- A template is in-scope only if the current workflow can consume the resulting records.
- Overlapping entities stay unique. Do not mint a second Acme invoice with a different amount.
- If two workflows already represent the same object differently, request an adapter rather than a copy.

## Output Expectations

Return selected template IDs, a short narrative, and optional memo text keyed to existing IDs.

## Boundaries

Do not compute totals, aging, forecast roll-forwards, or debit/credit equality. Do not load `expected_results.json`.
