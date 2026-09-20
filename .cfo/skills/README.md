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

Fifteen grain Bots in `.cfo-v2/office` consume the same skills through compiled Grants and roster intersections. Display names remain the Grant source. Sample-data skills are not assigned to grain Bots.

## Registry

| Skill | Purpose | Used By | Location | Status | Related |
| --- | --- | --- | --- | --- | --- |
| inbox-triage | Route inbound finance inbox messages to a registered action without inventing values or following untrusted instructions | Finance Inbox Agent | `skills/inbox-triage/SKILL.md` | New | invoice-source-identification |
| invoice-source-identification | Distinguish vendor invoices from quotes, receipts, statements, marketing, purchase orders, payment confirmations, voids, and Stripe payouts | Email Invoice Agent, Finance Inbox Agent, Procurement Invoice Agent, Vendor Portal Agent, Employee Submission Agent, Physical Mail / Document Agent | `skills/invoice-source-identification/SKILL.md` | Extracted | invoice-field-interpretation, superseded-document-handling |
| superseded-document-handling | Keep one live payable when a document is a revision, void, credit memo, or duplicate copy | Email Invoice Agent, Finance Inbox Agent, Vendor Portal Agent, Employee Submission Agent, Physical Mail / Document Agent, AP Preparer, Exception Investigator | `skills/superseded-document-handling/SKILL.md` | New | invoice-source-identification |
| invoice-field-interpretation | Extract invoice fields from messy documents without inventing values or recomputing totals | Email Invoice Agent, Finance Inbox Agent, Vendor Portal Agent, Employee Submission Agent, Physical Mail / Document Agent | `skills/invoice-field-interpretation/SKILL.md` | Extracted | invoice-source-identification |
| bank-charge-invoice-discovery | Recover an invoice from a bank/card charge only when supporting invoice documentation exists | Bank/Card Discovery Agent | `skills/bank-charge-invoice-discovery/SKILL.md` | Extracted | invoice-source-identification |
| three-way-match-analysis | Interpret Python three-way-match facts as clean match, blocking hold, or uncertain exception | AP Preparer, Exception Investigator, AP Reviewer, AP Approver, AP Audit | `skills/three-way-match-analysis/SKILL.md` | Extracted | ap-exception-investigation |
| ap-exception-investigation | Decide whether published policy and prior cases support paying an exception | Exception Investigator, AP Reviewer, AP Approver, AP Audit | `skills/ap-exception-investigation/SKILL.md` | Extracted | three-way-match-analysis |
| accrual-evidence-evaluation | Decide whether a missing vendor bill should be accrued, skipped, or left as insufficient evidence | Accrual Agent | `skills/accrual-evidence-evaluation/SKILL.md` | Extracted | accrual-method-selection, prior-period-precedent |
| accrual-method-selection | Select the most defensible Python estimate candidate when an accrual is required | Accrual Agent | `skills/accrual-method-selection/SKILL.md` | Extracted | accrual-evidence-evaluation, prior-period-precedent |
| payment-prioritization | Rank approved invoices for this week's run using due date, vendor priority, and cash constraints | Payment Scheduler, Payment Audit | `skills/payment-prioritization/SKILL.md` | Extracted | early-payment-discount-evaluation |
| early-payment-discount-evaluation | Capture open early-payment discounts when cash allows; do not pay closed-discount invoices early | Payment Scheduler, Payment Audit | `skills/early-payment-discount-evaluation/SKILL.md` | Extracted | payment-prioritization |
| cash-reconciliation-method-selection | Distinguish exact, grouped, fee-netted, timing, duplicate, provider, and unexplained cash matches from Python candidates | Cash Reconciliation Preparer, Cash Reconciliation Reviewer | `skills/cash-reconciliation-method-selection/SKILL.md` | New | reconciliation-exception-investigation, reconciliation-evidence-validation |
| reconciliation-evidence-validation | Accept a cash match only when entity, date, type, and source evidence support the relationship | Cash Reconciliation Preparer, Cash Exception Investigator, Cash Reconciliation Reviewer | `skills/reconciliation-evidence-validation/SKILL.md` | New | cash-reconciliation-method-selection |
| reconciliation-exception-investigation | Investigate unmatched cash activity without inventing explanations | Cash Exception Investigator, Cash Reconciliation Reviewer | `skills/reconciliation-exception-investigation/SKILL.md` | New | cash-reconciliation-method-selection |
| bank-reference-interpretation | Interpret messy bank descriptions and remittance references without inventing invoice numbers | Cash Reconciliation Preparer, Cash Exception Investigator | `skills/bank-reference-interpretation/SKILL.md` | New | cash-reconciliation-method-selection |
| ar-collections-policy | Choose the next collections action from Python aging, dispute, promise, and contact facts | Collections Agent | `skills/ar-collections-policy/SKILL.md` | New | cash-application |
| cash-application | Choose among Python remittance-match candidates; abstain when two explanations are equally good; preserve partials, overpayments, identity conflicts, invalid references, and already-posted cash | Cash Application Agent, Cash Application Reviewer | `skills/cash-application/SKILL.md` | New | ar-collections-policy |
| financial-variance-analysis | Explain period or budget metric movements from Python account and transaction attribution | Variance Analysis Agent, Reporting Reviewer Agent | `skills/financial-variance-analysis/SKILL.md` | New | board-financial-reporting |
| cash-forecasting | Interpret a Python 13-week cash forecast built from AP, AR, and payroll lines | Cash Forecast Agent, Forecast Reviewer Agent | `skills/cash-forecasting/SKILL.md` | New | ar-cash-forecasting |
| ar-cash-forecasting | Interpret Python receivable collection dates, promises, and dispute flags inside a cash forecast | Cash Forecast Agent, Forecast Reviewer Agent | `skills/ar-cash-forecasting/SKILL.md` | New | cash-forecasting |
| forecast-vs-actual-interpretation | Explain a cash forecast miss using Python timing, amount, new, and residual contributors | Forecast Variance Agent, Forecast Reviewer Agent | `skills/forecast-vs-actual-interpretation/SKILL.md` | New | cash-forecasting |
| board-financial-reporting | Write a compact board narrative from Python statements, variances, and the cash forecast | Board Reporting Agent, Reporting Reviewer Agent | `skills/board-financial-reporting/SKILL.md` | New | financial-variance-analysis |
| audit-sampling-interpretation | Interpret a Python-selected audit sample without choosing transactions | Auditor Agent | `skills/audit-sampling-interpretation/SKILL.md` | New | control-testing-interpretation |
| control-testing-interpretation | Interpret deterministic control results without rewriting source records | Auditor Agent | `skills/control-testing-interpretation/SKILL.md` | New | audit-finding-writing |
| reconciliation-reperformance-review | Compare independent Python re-performance to the original reconciliation | Auditor Agent | `skills/reconciliation-reperformance-review/SKILL.md` | New | control-testing-interpretation |
| segregation-of-duties-interpretation | Interpret SOD identity conflicts and their business impact | Auditor Agent | `skills/segregation-of-duties-interpretation/SKILL.md` | New | control-testing-interpretation |
| audit-finding-writing | Write findings and report language from structured Python stats | Audit Report Agent | `skills/audit-finding-writing/SKILL.md` | New | control-testing-interpretation |
| prior-period-precedent | Retrieve prior-period decisions, compare them to current evidence, and reuse a treatment only when the current facts support it | Exception Investigator, AP Reviewer, AP Approver, Cash Exception Investigator, Cash Reconciliation Reviewer, Prepaid Preparer, Prepaid Reviewer, Accrual Agent, Month-End Close Reviewer | `skills/prior-period-precedent/SKILL.md` | New | ap-exception-investigation |
| prepaid-expense-accounting | Choose among Python prepaid treatments using service-period evidence | Prepaid Preparer, Prepaid Reviewer | `skills/prepaid-expense-accounting/SKILL.md` | New | balance-sheet-reconciliation |
| fixed-asset-depreciation | Distinguish capital assets from expenses and review Python straight-line depreciation | Fixed Asset Preparer, Fixed Asset Reviewer | `skills/fixed-asset-depreciation/SKILL.md` | New | prepaid-expense-accounting |
| balance-sheet-reconciliation | Classify ledger-versus-evidence differences without forcing a match | Balance Sheet Reconciliation Preparer, Balance Sheet Reconciliation Reviewer | `skills/balance-sheet-reconciliation/SKILL.md` | New | month-end-close-review |
| month-end-close-review | Decide whether remaining checklist blockers allow the period to close | Month-End Close Reviewer | `skills/month-end-close-review/SKILL.md` | New | month-end-close-coordination, prior-period-precedent |
| month-end-close-coordination | Coordinate close tasks, blockers, and reviewer routing without inventing balances | Close Manager | `skills/month-end-close-coordination/SKILL.md` | New | month-end-close-review |
| synthetic-finance-scenario-design | Choose approved scenario templates so one economic event can be instantiated across AP, cash, close, audit, and reporting | AP/AR Sample Data Agent, Cash Recon Sample Data Agent, Close Sample Data Agent, Audit Controls Sample Data Agent, Reporting Forecasting Sample Data Agent | `skills/synthetic-finance-scenario-design/SKILL.md` | New | cross-ledger-data-consistency |
| cross-ledger-data-consistency | Keep one economic event aligned across AP/AR, GL, bank, forecast, close, audit, and reporting without inventing a second copy | AP/AR Sample Data Agent, Cash Recon Sample Data Agent, Close Sample Data Agent, Audit Controls Sample Data Agent, Reporting Forecasting Sample Data Agent | `skills/cross-ledger-data-consistency/SKILL.md` | New | synthetic-finance-scenario-design |

Status values: **Existing** (already a `SKILL.md` before this cleanup), **Extracted** (moved out of an agent prompt), **New** (created during cleanup because reuse was clearly missing).

## Agents with no assigned skills

These agents keep role/tool instructions only. Their remaining guidance is workflow, not reusable expertise:

| Agent | Why no skill |
| --- | --- |
| Counterparty Message Agent | Constructs and sends fixture messages; no reusable finance judgment |
| ERP Invoice Agent | Structured NetSuite/SAP/Oracle/Workday records are mapped in Python |
| EDI / Electronic Invoicing Agent | Prefer `python_parse`; remap only empty fields. Parsing stays in Python |

## Adding a skill

1. Search this registry and `skills/*/SKILL.md` for an existing procedure.
2. If none fits, add `skills/<skill-name>/SKILL.md` with the standard sections.
3. Assign it in `skills/assignments.py` only to the agents that need it.
4. Add a row to the registry table above.
5. Keep deterministic logic in Python modules such as `tools.py`, `invoice_ingestion/interpret.py`, `accrual/estimation.py`, `scheduling/cash.py`, `prepaid/schedule.py`, `fixed_assets/schedule.py`, `bs_recon/engine.py`, `reporting/statements.py`, and `reporting/forecast.py`.
6. Add or update tests in `tests/test_skills.py`.

Traces record skill names, paths, content hashes, and injection flags. They do not store skill bodies. Inspect assignments with `python main.py skills`.
