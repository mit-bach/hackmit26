---
name: cash-reconciliation-method-selection
description: Choose a Kernel candidate_id for a bank line. Trust apply/pay identifiers. Do not invent fees or replay match_type taxonomy.
status: new
---

# Cash Reconciliation Method Selection

## Purpose

Pick one Kernel `candidate_id` for an unmatched bank line, or send the line to `ctl-cash`. Python already typed the match. You copy the id. You do not rename the type.

## When to Use

Wear this as Bot `cash` Profile `match` after the case evidence returns. Do not use it to rebuild the candidate engine.

## Inputs / Evidence

Authoritative Kernel fields: `candidate_id`, `match_type`, `difference_minor`, `fee_evidence_ids`, `provider_status`. Authoritative pipe fields: the identifier apply or pay already wrote. Bank description is a memo, not an identity. Memory of a processor payout label is color. It is not fee evidence.

## Procedure

Load the match candidates and the pipe identifier. If apply or pay already named the counterparty, copy that identity and pick the candidate that uses it. Do not pick a second customer or vendor because the memo is messy. If the identifier is missing, fail closed. Handle `ctl-cash`. Do not scrape a name from the description to look done.

Copy amounts by citing `candidate_id`. If the residual has no Kernel fee evidence, leave it unexplained.

## Decision Criteria

- Tick the identified line when the identifier is present and a Kernel candidate copies it.
- Keep unexplained unexplained when Kernel has no fee evidence. Helios-class fee-netted still needs a Kernel fee id.
- Handle `ctl-cash` when the identifier is missing, the residual is unexplained, or two candidates are equally plausible.

## Output Expectations

`PreparerSelection` with a Kernel `candidate_id` or none, disposition copied from Python, and evidence ids you used. Do not output a new amount.

## Boundaries

- Do not recalculate group sums, fees, FX, or residuals.
- Do not invent invoice numbers or counterparties.
- Do not freeze a table from `match_type` to English. Kernel typed it.
- Do not post the proposed bank-fee journal.
- Do not start a 13-week forecast from unreconciled GL cash.
