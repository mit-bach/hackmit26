---
name: prior-period-precedent
description: Retrieves prior-period finance decisions, compares them to current evidence, and reuses a treatment only when the current facts support it.
status: new
---

# Prior-Period Precedent

## Purpose

Use organizational memory so a decision made in an earlier accounting period can inform a later similar case without becoming a binding rule.

## When to Use

Apply when investigating a cash payout difference, a prepaid treatment, an AP exception, or a month-end accrual methodology that may have happened before for the same vendor, customer, or payment provider.

## Inputs / Evidence

- get_decision_memories results (decision_id, period, situation, evidence, treatment)
- current Python candidates, amounts, dates, and documents
- current Stripe/provider breakdown or prepaid service period when relevant

## Procedure

1. Retrieve relevant prior decisions with structured filters: workflow, entity, situation type, and prior period.
2. Restate the prior case in one or two sentences. Do not paste unconstrained reasoning.
3. Compare prior evidence to current evidence. Check amounts, dates, fee/chargeback composition, and coverage periods.
4. Treat the prior decision as precedent, not as authoritative truth. Confirm that the current evidence supports the same treatment.
5. Reuse the prior accounting treatment only when the current facts support it.
6. If current evidence contradicts the precedent, record a deviation and decide from current facts.
7. After a reusable decision is completed, a new memory record should be written for this period.

## Decision Criteria

- Same entity + same situation + current evidence agrees → reuse the prior treatment and cite the decision_id.
- Same entity + current evidence disagrees → do not reuse; explain the deviation.
- Different entity or situation → ignore the memory.
- Memory disabled or no retrieval → reason from current evidence only.
- Never invent a fee, chargeback, service period, or vendor alias to force a match to the old case.

## Output Expectations

Name the retrieved decision_id, say whether it was used, state whether current evidence was checked, and give the current decision. Keep rationale short enough to show an auditor.

## Boundaries

- Do not treat precedent as a posted policy or override Python arithmetic.
- Do not store chain-of-thought. Store only the decision, evidence, and concise rationale.
- Do not write a memory for a trivial exact match or an unresolved exception.
- Explicit published policy still beats historical precedent.
