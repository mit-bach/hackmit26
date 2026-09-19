---
name: ap-exception-investigation
description: Distinguishes payment-blocking AP exceptions from policy-supported exceptions using published policy and prior cases. Use when an invoice is not a clean three-way match.
status: extracted
---

# AP Exception Investigation

## Purpose

Explain each AP exception and decide whether published policy and stored prior cases actually support payment, or whether the invoice must be held.

## When to Use

Apply when exception_types are non-empty, the Preparer recommended INVESTIGATE, or a reviewer/approver/auditor must test whether an exception is acceptable.

## Inputs / Evidence

- Python facts from get_case_evidence
- published policies from get_company_policies / find_relevant_policies
- prior autonomous cases from get_prior_cases
- the Preparer recommendation and any Investigator or Reviewer write-up already in the packet

## Procedure

1. Inspect the records and Python facts for each exception type.
2. Load policies tagged for those exception types. Do not invent company policy.
3. Search prior cases only as supporting evidence for remaining ambiguity, such as a known vendor alias.
4. Distinguish acceptable exceptions from payment-blocking problems.
5. If policy or prior cases do not resolve the ambiguity, HOLD. Do not guess.

## Decision Criteria

- Recommend **APPROVE** only when a published policy and/or a matching prior case actually support payment, and no must_hold policy applies.
- Explicit company policy takes precedence over historical precedent. Prior cases cannot override a must_hold policy.
- Prior cases are evidence, not absolute rules.
- Vendor-name mismatch may be payable only when stored evidence already establishes the two names as the same legal entity. Do not invent an alias.
- Amount variance may be payable only when Python reports it is inside the published P-009 tolerance and other three-way controls still hold.
- Duplicates, missing POs, unapproved POs, missing/not-received goods, and unpaid-in-full partial receipts remain holds under current policy.
- If evidence cannot justify payment, HOLD.

## Output Expectations

Return findings, relevant policy IDs, prior case IDs, unresolved risks, and APPROVE or HOLD. There is no human reviewer. Do not ask a person to decide.

## Boundaries

- Do not invent policies, tolerances, aliases, or missing records.
- Do not recalculate Python match facts.
- Do not approve payment if this agent only investigates; Investigators recommend, they do not finalize.
- Do not treat a prior APPROVE as a blanket waiver of current must_hold controls.
