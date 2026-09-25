---
name: ap-exception-investigation
description: Explains how this vendor's mess differs from Kernel exception_types. Use when prepare returned INVESTIGATE or exception_types is non-empty.
status: extracted
---

# AP Exception Investigation

## Purpose

Kernel already typed the exception. Your job is this vendor: why the PDF, name, or receipt lag looks like that, and whether stored alias memory still matches live facts.

## When to Use

Bot `ap` Profile `investigate` only. Same Bot as prepare. Replace the Grant set. Do not union with `ctl-pay`.

## Inputs / Evidence

Kernel `get_case_evidence`, published policies, operational AP memory, `get_prior_cases` as a seed not as the happy path. Current evidence wins.

## Procedure

Say what is distinctive about this counterparty's packet. A stored alias applies only when live names still support it. If World or Email must ask for a missing PO or a revised PDF, leave HOLD. Do not silently approve the original bill.

## Decision Criteria

- Precedent is color. It cannot override a live blocking `must_hold`.
- Recommend APPROVE only when Kernel already allows and current documents still support the story.
- If the mess is just the Kernel type list with no extra sense, HOLD. Do not invent an alias.

## Output Expectations

`InvestigationReport` with findings about this vendor, policy IDs you actually read, memory ids if retrieved, and APPROVE or HOLD. There is no human reviewer.

## Boundaries

- Do not invent policies, tolerances, aliases, or missing records.
- Do not recalculate Python match facts.
- Do not freeze exception_type to an English HOLD sentence. Kernel already typed it.
- Do not pay. Do not concur. Do not wear a second Bot named investigator.
