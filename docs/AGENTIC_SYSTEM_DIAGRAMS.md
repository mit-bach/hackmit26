# Office of the CFO: System Maps and Decomposition Guide

This guide is a compact map of the implemented HackMIT system. It complements
the [detailed implementation guide](AGENTIC_SYSTEM_WORKFLOW.md), which remains
the source of truth, and maps the system to the
[Maximor challenge](../design-workshop/dominik/Maximor-HackMIT-Track.md).

The system is an **agent-assisted finance operating system** for a synthetic
company. It connects vendor payments, customer collections, cash
reconciliation, month-end close, reporting, forecasting, and audit.

## 1. First: Which Nodes Are Agents?

Not every node in the diagrams is an agent.

```mermaid
flowchart LR
  Ext[/External source or person/]
  Agent([Named agent])
  Py[Deterministic Python]
  Store[(File or persisted state)]
  Gate{Control or decision gate}
  Human{{Human review}}

  Ext --> Py
  Py --> Agent
  Agent --> Gate
  Gate --> Store
  Gate --> Human
```

Use these shapes throughout this document:

- **Rounded node:** a named agent that can use an LLM.
- **Rectangle:** deterministic Python, an orchestrator, or a finance module.
- **Cylinder:** persisted JSON state, a ledger, or a run artifact.
- **Diamond:** a deterministic gate or branch.
- **Hexagon:** a human review point.
- **Slanted node:** an external source or actor.

Four facts prevent a misleading reading of the architecture:

1. The repository defines **43 named agents**.
2. Many runs use deterministic fallbacks instead of live LLM calls.
3. Python owns amounts, candidates, validation, posting, and close gates.
4. Agent handoffs use structured objects in one process or persisted JSON.
   There is no peer-to-peer agent message bus.

## 2. What the Whole System Is

The system turns financial source records into controlled accounting state. It
then uses that state for close, forecasts, reports, and audit.

```mermaid
flowchart TB
  subgraph Sources["1. Source records"]
    Vendor[/Vendor invoices and documents/]
    Customer[/Customer invoices and payments/]
    Bank[/Bank transactions/]
    Provider[/Stripe and Adyen payouts/]
    HumanInput[/Human corrections and evidence/]
  end

  subgraph Operations["2. Finance operations"]
    Ingest[Invoice ingestion]
    AP[Accounts payable]
    Schedule[Payment scheduling]
    AR[Accounts receivable]
    Cash[Cash reconciliation]
  end

  subgraph Accounting["3. Accounting and close"]
    Accrual[Accruals]
    Prepaid[Prepaids]
    Assets[Fixed assets]
    BS[Balance-sheet reconciliations]
    Close{Month-end close gates}
  end

  subgraph Outputs["4. Controlled outputs"]
    Closed[(Closed-period snapshot and lock)]
    Forecast[(13-week cash forecast)]
    Report[(Financial and board reporting)]
    Audit[(Independent audit findings)]
  end

  Vendor --> Ingest --> AP --> Schedule
  Customer --> AR
  Customer --> Cash
  Bank --> Cash
  Provider --> Cash

  AP --> Accrual
  AP --> Prepaid
  AP --> Assets
  AP --> BS
  AR --> BS
  Cash --> BS
  Accrual --> BS
  Prepaid --> BS
  Assets --> BS
  BS --> Close

  Close -->|pass| Closed
  Close -->|blocker| HumanInput
  HumanInput --> Operations
  HumanInput --> Accounting

  Schedule --> Forecast
  AR --> Forecast
  Closed --> Report
  Forecast --> Report
  AP --> Audit
  AR --> Audit
  Cash --> Audit
  Closed --> Audit
  Report --> Audit
```

This is one connected function, not a set of independent demos. Shared
transaction IDs and persisted state connect the modules. The repository does
not have one physical general ledger; several ledgers share IDs and provenance.

## 3. Macro Module Map

This diagram shows the main module boundaries and the most important
cross-module pathways.

```mermaid
flowchart LR
  subgraph P2P["Procure to pay"]
    ING[Ingestion]
    APM[AP three-way match]
    POOL[(Approved pool)]
    PAY[Payment plan]
    ING --> APM
    APM -->|APPROVE| POOL --> PAY
  end

  subgraph O2C["Order to cash"]
    AGE[AR aging]
    COL[Collections]
    APP[Cash application]
    ARS[(AR state)]
    AGE --> COL
    APP --> ARS
  end

  subgraph Treasury["Treasury and cash"]
    PYM[Provider payout math]
    BREC[Bank reconciliation]
    CREP[(Cash report)]
    PYM --> BREC --> CREP
  end

  subgraph R2R["Record to report"]
    ACC[Accruals]
    PRE[Prepaid amortization]
    FA[Fixed assets and depreciation]
    LED[(Close journal ledger)]
    BSR[Balance-sheet recs]
    GATE{Close gates}
    ACC --> LED
    PRE --> LED
    FA --> LED
    LED --> BSR --> GATE
  end

  subgraph Plan["Plan and explain"]
    FC[13-week forecast]
    REP[Statements and variance]
    BOARD[Board pack]
    FC --> BOARD
    REP --> BOARD
  end

  subgraph Assurance["Assurance"]
    TRACE[(Decision traces)]
    AUD[Independent audit]
    TRACE --> AUD
  end

  CREP --> BSR
  ARS --> BSR
  APM --> BSR

  PAY --> FC
  POOL --> FC
  ARS --> FC
  GATE -->|CLOSED| REP

  APM --> TRACE
  APP --> TRACE
  BREC --> TRACE
  GATE --> TRACE
  REP --> TRACE
```

The cleanest decomposition uses six bounded contexts:

- **Procure to pay:** decide whether and when the company can pay a vendor.
- **Order to cash:** track customer debt and apply incoming cash.
- **Treasury and cash:** explain bank and provider settlement activity.
- **Record to report:** post period adjustments, reconcile accounts, and close.
- **Plan and explain:** forecast cash and explain financial results.
- **Assurance:** challenge the work without changing the source books.

Each context owns one financial question, its deterministic rules, its agent
roles, and its state. Shared IDs, status contracts, and trace artifacts form the
boundaries between contexts.

## 4. Complete Agent Topology

This is the complete inventory of all 43 named agents. These are capability
definitions, not 43 concurrent workers. The arrows show implementation-level
handoffs. They do not imply that every agent runs in every scenario.

```mermaid
flowchart TB
  subgraph Sample["Sample data — 5 agents"]
    SD1([AP/AR Sample Data Agent])
    SD2([Cash Recon Sample Data Agent])
    SD3([Close Sample Data Agent])
    SD4([Audit Controls Sample Data Agent])
    SD5([Reporting Forecasting Sample Data Agent])
  end

  FIX[(Seeded JSON fixtures)]
  SD1 --> FIX
  SD2 --> FIX
  SD3 --> FIX
  SD4 --> FIX
  SD5 --> FIX

  subgraph Ingestion["Invoice ingestion — 8 agents"]
    I1([Email Invoice Agent])
    I2([ERP Invoice Agent])
    I3([Procurement Invoice Agent])
    I4([Vendor Portal Agent])
    I5([Employee Submission Agent])
    I6([Physical Mail / Document Agent])
    I7([EDI / Electronic Invoicing Agent])
    I8([Bank/Card Discovery Agent])
  end

  IV[Python parse, validate, deduplicate]
  FIX --> I1
  FIX --> I2
  FIX --> I3
  FIX --> I4
  FIX --> I5
  FIX --> I6
  FIX --> I7
  FIX --> I8
  I1 --> IV
  I2 --> IV
  I3 --> IV
  I4 --> IV
  I5 --> IV
  I6 --> IV
  I7 --> IV
  I8 --> IV

  subgraph APTeam["Accounts payable — 5 agents"]
    AP1([AP Preparer])
    AP2([Exception Investigator])
    AP3([AP Reviewer])
    AP4([AP Approver])
    AP5([AP Audit])
  end

  APF[Python AP evidence]
  APS{Python AP safety net}
  IV -. optional in-process overlay .-> APF
  FIX --> APF
  APF --> AP1
  AP1 -. exception .-> AP2
  AP1 --> AP3
  AP2 --> AP3
  AP3 --> AP4 --> AP5 --> APS

  subgraph TreasuryTeam["Payment scheduling — 2 agents"]
    T1([Payment Scheduler])
    T2([Payment Audit])
  end

  POOL[(Approved pool)]
  PNET[Python cash and policy net]
  PLAN[(Weekly payment plan)]
  APS -->|APPROVE| POOL
  POOL --> T1 --> PNET --> T2 --> PLAN

  subgraph ARTeam["Accounts receivable — 3 agents"]
    AR1([Collections Agent])
    AR2([Cash Application Agent])
    AR3([Cash Application Reviewer])
  end

  AGING[Python aging]
  ARCAND[Python application candidates]
  ARVAL{Python AR validator}
  ARSTATE[(AR state)]
  FIX --> AGING --> AR1
  FIX --> ARCAND --> AR2
  AR2 -. material or ambiguous .-> AR3
  AR2 --> ARVAL
  AR3 --> ARVAL
  ARVAL --> ARSTATE

  subgraph CashTeam["Cash reconciliation — 3 agents"]
    C1([Cash Reconciliation Preparer])
    C2([Cash Exception Investigator])
    C3([Cash Reconciliation Reviewer])
  end

  CCAND[Python match candidates]
  CVAL{Python match validator and tie-out}
  CASHREP[(Cash reconciliation report)]
  FIX --> CCAND
  CCAND --> C1
  C1 -. exception .-> C2
  C1 --> C3
  C2 --> C3
  C3 --> CVAL --> CASHREP

  subgraph AccrualTeam["Accruals — 1 agent"]
    AC1([Accrual Agent])
  end

  ACF[Python discovery and estimate candidates]
  ACF --> AC1 --> CLOSELED[(Close journal ledger)]

  subgraph CloseTeam["Close controls — 8 agents"]
    CL1([Prepaid Preparer])
    CL2([Prepaid Reviewer])
    CL3([Fixed Asset Preparer])
    CL4([Fixed Asset Reviewer])
    CL5([Balance Sheet Reconciliation Preparer])
    CL6([Balance Sheet Reconciliation Reviewer])
    CL7([Close Manager])
    CL8([Month-End Close Reviewer])
  end

  FIX --> ACF
  FIX --> CL1 --> CL2 --> CLOSELED
  FIX --> CL3 --> CL4 --> CLOSELED
  CLOSELED --> CL5
  CASHREP --> CL5
  ARSTATE --> CL5
  APS --> CL5
  CHECK[Python close checklist]
  APS --> CHECK
  ARSTATE --> CHECK
  CASHREP --> CHECK
  CLOSELED --> CHECK
  CHECK --> CL7
  CL5 --> CL6 --> CL8
  CL7 --> CL8
  CL8 --> CGATE{Python close gates}
  CGATE --> CLOSED[(Snapshot and period lock)]

  subgraph ReportingTeam["Reporting and forecasting — 6 agents"]
    R1([Variance Analysis Agent])
    R2([Reporting Reviewer Agent])
    R3([Board Reporting Agent])
    R4([Cash Forecast Agent])
    R5([Forecast Reviewer Agent])
    R6([Forecast Variance Agent])
  end

  RFACT[Python statements and variance]
  FBUILD[Python 13-week forecast]
  POOL --> FBUILD
  ARSTATE --> FBUILD
  CLOSED --> RFACT
  RFACT --> R1 --> R2
  RFACT --> R3 --> R2
  FBUILD --> R3
  FBUILD --> R4 --> R5
  FBUILD --> R6 --> R5

  subgraph AuditTeam["Independent audit — 2 agents"]
    AU1([Auditor Agent])
    AU2([Audit Report Agent])
  end

  TRACES[(Operational traces and audit fixtures)]
  APS --> TRACES
  ARVAL --> TRACES
  CVAL --> TRACES
  CGATE --> TRACES
  R2 --> TRACES
  R5 --> TRACES
  TRACES --> AU1 --> AU2
```

The large graph is useful as a roster and boundary map. The next diagrams are
better for reasoning about behavior because each one isolates one financial
cycle.

## 5. Isolated Decomposition: Procure to Pay

```mermaid
sequenceDiagram
  participant Source as Vendor source
  participant Ingest as Ingestion agents
  participant Parse as Python normalization
  participant AP as AP agent team
  participant Safety as Python safety net
  participant Pool as Approved pool
  participant Sched as Scheduler agents
  participant Policy as Python payment policy
  participant Down as Forecast and close

  Source->>Ingest: Invoice or source record
  Ingest->>Parse: Extracted candidate
  Parse->>Parse: Validate and deduplicate
  Parse->>AP: Invoice plus PO, receipt, and policy facts
  AP->>Safety: APPROVE or HOLD
  alt supported approval
    Safety->>Pool: Add approved invoice once
    Pool->>Sched: Eligible payment candidates
    Sched->>Policy: Proposed weekly plan
    Policy->>Down: Legal plan and forecast outflow
  else hold or failed safety check
    Safety->>Down: Held item; no committed payment
  end
```

This unit answers two separate questions:

1. **AP:** Is this invoice valid enough to pay?
2. **Treasury:** Should the company pay it this week?

The split matters. Approval does not execute a payment, and scheduling cannot
rescue a held invoice.

## 6. Isolated Decomposition: Order to Cash

```mermaid
sequenceDiagram
  participant Invoice as Customer invoice
  participant Aging as Python aging
  participant Collect as Collections Agent
  participant Payment as Customer payment
  participant Cand as Python candidates
  participant Apply as Cash Application Agent
  participant Review as Agent reviewer
  participant Valid as Python validator
  participant Human as Human reviewer
  participant State as AR state

  Invoice->>Aging: Open balance and due date
  Aging->>Collect: Collection facts
  Collect-->>State: Draft action or no action

  Payment->>Cand: Amount and remittance
  Cand->>Apply: Named application candidates
  Apply->>Review: Material or ambiguous proposal
  Apply->>Valid: Low-risk proposal
  Review->>Valid: Reviewed proposal

  alt AUTO_APPLY and valid
    Valid->>State: Post application and journals
  else HUMAN_REVIEW
    Valid->>Human: Candidate set and evidence
    Human->>State: Approve, correct, or reject
  else UNAPPLIED
    Valid->>State: Keep cash visible and unmatched
  end
```

AR aging does not need an agent. Python computes it. Agents choose collection
actions and select from application candidates. Only a valid application
changes invoice balances, close inputs, and forecast collections.

## 7. Isolated Decomposition: Cash Reconciliation

```mermaid
sequenceDiagram
  participant Bank as Bank and provider data
  participant Engine as Python candidate engine
  participant Prep as Cash Preparer
  participant Investigate as Exception Investigator
  participant Review as Cash Reviewer
  participant Valid as Python validator
  participant Tie as Python tie-out
  participant Human as Human review
  participant Close as Close cash task

  Bank->>Engine: Bank, ledger, Stripe, and Adyen records
  Engine->>Prep: Allowed match candidates
  Prep->>Valid: Selected candidate ID
  alt exception or failed validation
    Valid->>Investigate: Evidence and failed checks
    Investigate->>Review: Explanation or escalation
  else supported match
    Valid->>Review: Validated match
  end
  Review->>Tie: Reviewed dispositions
  alt arithmetic fails
    Tie->>Close: FAILED_TIE
  else ties with unexplained item
    Tie->>Human: HUMAN_REVIEW
    Tie->>Close: OPEN and NEEDS_REVIEW
  else all items explained
    Tie->>Close: RECONCILED
  end
```

Agents can choose and explain candidates. They cannot invent transactions,
fees, or amounts. A reconciliation can tie arithmetically and still remain
`OPEN`; the seeded $12.40 difference demonstrates this rule.

## 8. Isolated Decomposition: Month-End Close

```mermaid
flowchart TB
  Ingest[Ingest] --> AP[AP]
  Ingest --> AR[AR]
  Ingest --> Cash[Cash]

  AP --> Accrual[Accruals]
  AP --> Prepaid[Prepaids]
  AP --> Assets[Depreciation]

  AP --> BS[Balance-sheet recs]
  AR --> BS
  Cash --> BS
  Accrual --> BS
  Prepaid --> BS
  Assets --> BS

  BS --> Exceptions[Resolve exceptions]
  Exceptions --> Review([Month-End Close Reviewer])
  Review --> Gates{Python close gates}
  Gates -->|fail| Human{{Human correction}}
  Human --> Rerun[Invalidate and rerun affected tasks]
  Rerun --> Cash
  Rerun --> AR
  Rerun --> Prepaid
  Gates -->|pass| Snapshot[(Snapshot)]
  Snapshot --> Lock[(Period lock)]
```

Close is the main long-horizon coordinator. A task starts only after its
dependencies complete. Reviewers can recommend closure, but Python rejects the
recommendation if tasks, reconciliations, evidence, reviews, or journals fail a
gate.

## 9. The Real Feedback Loop

The apparent “back-and-forth between agents” is usually a controlled rerun
through source state, not an open conversation between agents.

```mermaid
flowchart LR
  Source[(Source object)]
  Facts[Python facts and candidates]
  Agent([Agent decision])
  Validator{Python validator}
  State[(Posted state and trace)]
  Human{{Human review}}
  Correct[Correct source or attach evidence]
  Down[Downstream module]

  Source --> Facts --> Agent --> Validator
  Validator -->|valid| State --> Down
  Validator -->|uncertain or invalid| Human
  Down -->|new blocker| Human
  Human --> Correct --> Source
```

This loop preserves auditability:

- The original discrepancy stays visible.
- A human changes the source object or supplies missing evidence.
- The system rebuilds facts and reruns the affected workflow.
- The new decision gets a new trace.
- Downstream close, forecast, and report state changes only after validation.

## 10. How to Divide the Work

A practical implementation split follows the bounded contexts in section 3:

1. **Foundation:** shared IDs, money rules, structured outputs, traces, and
   idempotent persistence.
2. **Procure to pay:** ingestion, AP, approved pool, and scheduling.
3. **Order to cash:** aging, collections, cash application, and AR review.
4. **Treasury:** bank candidates, provider payouts, validation, and tie-out.
5. **Record to report:** accruals, prepaids, assets, balance-sheet recs, and
   close gates.
6. **Plan and explain:** statements, variance, forecast, and board output.
7. **Assurance:** independent sampling, controls, re-performance, and findings.
8. **Integration:** cross-workflow fixtures, close scenario, discrepancy tests,
   and the judge demo.

Keep these contracts stable between units:

- One economic event keeps one ID across workflows.
- Agents select from Python-produced candidates.
- Validators control all state changes.
- Human review changes source state, then causes a rerun.
- Audit reads operational artifacts but does not rewrite the books.
- Close consumes module results and does not duplicate their accounting logic.

This division lets teams build modules in parallel while preserving one company
story and one defensible chain of evidence.
