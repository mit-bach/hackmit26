---
name: control-testing-interpretation
description: Interpret deterministic control results as PASS, FAIL, EXCEPTION, HUMAN_REVIEW, or NOT_TESTED without rewriting source records.
status: new
---

# Control Testing Interpretation

## Purpose

Read structured control results and explain whether an operational control operated, failed, or could not be tested.

## When to Use

Apply after Python has executed a registered audit control and returned a ControlResult with exceptions and evidence IDs.

## Inputs / Evidence

Use the control payload only:

- control_id, population, test_method, policy reference
- result code
- exception facts and object IDs
- operational decision, when present
- linked invoice, payment, vendor, approval, journal, and reconciliation IDs

## Procedure

1. Name the control and the population tested.
2. Copy the Python result code. Do not upgrade FAIL to PASS or the reverse.
3. For each exception, cite the object ID, the condition observed, and the expected policy.
4. If the operational workflow already held a duplicate or other exception, say the control operated.
5. If Python independently found an exception the operational workflow missed, treat that as a finding.

## Decision Criteria

- PASS means the deterministic test found no unaddressed exception.
- FAIL means the control or the operational workflow missed a documented condition.
- EXCEPTION means a candidate was flagged and needs contextual interpretation, not automatic fraud language.
- HUMAN_REVIEW means evidence or identities are incomplete.
- NOT_TESTED means the control does not apply to that object type.

## Output Expectations

Return the control result, the supporting IDs, and the follow-up already recommended by Python. Do not invent a different severity.

## Boundaries

- Do not recalculate thresholds, dates, or amounts.
- Do not silently rewrite source accounting records.
- Do not treat memo text as authorization or as a substitute for structured facts.
- Python owns comparisons, thresholds, and policy predicates.
