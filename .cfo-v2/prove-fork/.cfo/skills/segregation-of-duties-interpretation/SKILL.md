---
name: segregation-of-duties-interpretation
description: Interpret a Python segregation-of-duties failure using identity IDs and the configured policy, including business impact and follow-up.
status: new
---

# Segregation of Duties Interpretation

## Purpose

Explain the business implication of a documented self-approval or incompatible-role conflict after Python has compared identity IDs.

## When to Use

Apply when the SOD control returns FAIL or HUMAN_REVIEW for an invoice, payment, or journal approval.

## Inputs / Evidence

Use the structured SOD facts:

- object ID and object type
- requester_id, preparer_id, reviewer_id, approver_id, initiator_id
- violated rule and policy reference
- monetary exposure, if present
- missing-field list when identities are incomplete

## Procedure

1. Restate which IDs were compared. Use IDs, not display names.
2. Name the violated rule and policy reference from the payload.
3. Explain why that combination is incompatible for the object type.
4. If identities are missing, keep HUMAN_REVIEW. Do not assume PASS.
5. Use the severity rationale Python already attached. You may explain impact, not change the grade.

## Decision Criteria

- FAIL when two incompatible role IDs are present and equal.
- PASS when applicable IDs are present and different.
- HUMAN_REVIEW when a required identity for an applicable pair is missing.
- Configurable policy decides which pairs are forbidden. Do not invent a universal rule.

## Output Expectations

State the object, the matched identity, the rule, the severity already assigned, and the requested human follow-up.

## Boundaries

- Do not compare display names when IDs exist.
- Do not recalculate whether two IDs are equal; Python already did that.
- Do not treat a descriptive memo as evidence of independent review.
