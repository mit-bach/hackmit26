# Agent skills

Reusable specialized reasoning for Office of the CFO agents lives here.

This is the canonical skill registry. Agents, tools, and Python stay separate:

```text
Python     facts, calculations, validation, hard constraints
Tools      data access and actions exposed to agents
Skills     reusable specialized reasoning and procedures
Agents     decision-makers that apply a selected subset of skills
Orchestrator  routes work
```

There were no `SKILL.md` files in this repository before this registry. The skills below were extracted from existing agent instructions. They are not a second copy of Python match math, EDI parsing, or policy enforcement.

The OpenAI Agents SDK sandbox skill loader is not used. These agents have function tools and structured outputs, not a filesystem sandbox, so skill bodies are injected into the assigned agent's instructions at definition time.

## Maintenance

Whenever a new agent capability is implemented, first check whether an existing skill already covers the required expertise. Reuse or extend that skill when appropriate. If the capability represents genuinely reusable specialized reasoning or procedure, create a new skill. Update the central skill registry whenever a skill is created, renamed, expanded, deprecated, or assigned to another agent.

Do not create a new skill for one-off implementation details, deterministic calculations, simple tool wrappers, or hardcoded policy enforcement.

A skill should answer: “What specialized procedure or domain knowledge does this agent need to perform this recurring task well?”

Keep Python responsible for arithmetic, tax and totals, date math, cash and reserve calculations, accrual candidate amounts, hashes, exact duplicate detection, schema and required-field validation, invoice math validation, and structured ERP/EDI/UBL parsing.

## Layout

```text
skills/
  README.md
  loader.py
  assignments.py
  <skill-name>/SKILL.md
```

Each `SKILL.md` uses YAML frontmatter (`name`, `description`, `status`) and the sections Purpose, When to Use, Inputs / Evidence, Procedure, Decision Criteria, Output Expectations, and Boundaries.

Programmatic assignments live in `skills/assignments.py` and must match this table.

## Registry

| Skill | Purpose | Used By | Location | Status | Related |
| --- | --- | --- | --- | --- | --- |
| invoice-source-identification | Distinguish vendor invoices from quotes, receipts, statements, marketing, purchase orders, and payment confirmations | Email Invoice Agent, Procurement Invoice Agent, Vendor Portal Agent, Employee Submission Agent, Physical Mail / Document Agent | `skills/invoice-source-identification/SKILL.md` | Extracted | invoice-field-interpretation |
| invoice-field-interpretation | Extract invoice fields from messy documents without inventing values or recomputing totals | Email Invoice Agent, Vendor Portal Agent, Employee Submission Agent, Physical Mail / Document Agent | `skills/invoice-field-interpretation/SKILL.md` | Extracted | invoice-source-identification |
| bank-charge-invoice-discovery | Recover an invoice from a bank/card charge only when supporting invoice documentation exists | Bank/Card Discovery Agent | `skills/bank-charge-invoice-discovery/SKILL.md` | Extracted | invoice-source-identification |
| three-way-match-analysis | Interpret Python three-way-match facts as clean match, blocking hold, or uncertain exception | AP Preparer, Exception Investigator, AP Reviewer, AP Approver, AP Audit | `skills/three-way-match-analysis/SKILL.md` | Extracted | ap-exception-investigation |
| ap-exception-investigation | Decide whether published policy and prior cases support paying an exception | Exception Investigator, AP Reviewer, AP Approver, AP Audit | `skills/ap-exception-investigation/SKILL.md` | Extracted | three-way-match-analysis |
| accrual-evidence-evaluation | Decide whether a missing vendor bill should be accrued, skipped, or left as insufficient evidence | Accrual Agent | `skills/accrual-evidence-evaluation/SKILL.md` | Extracted | accrual-method-selection |
| accrual-method-selection | Select the most defensible Python estimate candidate when an accrual is required | Accrual Agent | `skills/accrual-method-selection/SKILL.md` | Extracted | accrual-evidence-evaluation |
| payment-prioritization | Rank approved invoices for this week's run using due date, vendor priority, and cash constraints | Payment Scheduler, Payment Audit | `skills/payment-prioritization/SKILL.md` | Extracted | early-payment-discount-evaluation |
| early-payment-discount-evaluation | Capture open early-payment discounts when cash allows; do not pay closed-discount invoices early | Payment Scheduler, Payment Audit | `skills/early-payment-discount-evaluation/SKILL.md` | Extracted | payment-prioritization |

Status values: **Existing** (already a `SKILL.md` before this cleanup), **Extracted** (moved out of an agent prompt), **New** (created during cleanup because reuse was clearly missing).

## Agents with no assigned skills

These agents keep role/tool instructions only. Their remaining guidance is workflow, not reusable expertise:

| Agent | Why no skill |
| --- | --- |
| ERP Invoice Agent | Structured NetSuite/SAP/Oracle/Workday records are mapped in Python |
| EDI / Electronic Invoicing Agent | Prefer `python_parse`; remap only empty fields. Parsing stays in Python |

## Adding a skill

1. Search this registry and `skills/*/SKILL.md` for an existing procedure.
2. If none fits, add `skills/<skill-name>/SKILL.md` with the standard sections.
3. Assign it in `skills/assignments.py` only to the agents that need it.
4. Add a row to the registry table above.
5. Keep deterministic logic in Python modules such as `tools.py`, `invoice_ingestion/interpret.py`, `accrual/estimation.py`, and `scheduling/cash.py`.
6. Add or update tests in `tests/test_skills.py`.

Traces record skill names, paths, content hashes, and injection flags. They do not store skill bodies. Inspect assignments with `python main.py skills`.
