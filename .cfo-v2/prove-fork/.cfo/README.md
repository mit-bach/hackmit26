# Office of the CFO Agents

This directory is the Python kernel. It is hidden from Obsidian (dot-folder). The git root is the vault; see [`../README.md`](../README.md) and [`../docs/LAYOUT.md`](../docs/LAYOUT.md). Run commands from the repo root (`python main.py …`) or from here.

Autonomous finance agents for HackMIT: a connected Office of the CFO spanning AP, AR, cash reconciliation, month-end close, reporting, forecasting, and audit.

Python computes the facts. Agents decide among those facts. Human review is a first-class state in AR cash application, bank reconciliation, and month-end close. The AP invoice chain itself is autonomous (`APPROVE` or `HOLD` only).

Reusable agent expertise lives in `skills/`. Agents, tools, and Python stay separate: see [`skills/README.md`](skills/README.md).

## System Architecture

For a complete description of the agents, finance workflows, shared state, controls, human-review paths, and end-to-end workflow, see:

`docs/AGENTIC_SYSTEM_WORKFLOW.md`

Do not treat this README as the architecture document.

## Setup

Python 3.10+ is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your key in `.env` as `OPENAI_API_KEY=sk-...`. Do not commit `.env`.

## Run

```bash
python main.py INV-001
python main.py schedule --seed-demo
python accrue.py 2026-09
python main.py ingest 2026-09
python main.py close 2026-09
python main.py demo-close
python main.py close-month --month 2026-09 --seed-demo
python main.py close-trace --month 2026-09
python main.py eval-close --month 2026-09
python close.py run --period 2026-09
python close.py status --period 2026-09
python close.py reviews --period 2026-09
python demo_month_end_close.py --resolve
python main.py skills
python main.py ar-aging --as-of 2026-09-30
python main.py ar-collections --as-of 2026-09-30
python main.py ar-cash-apply PAY-001
python main.py ar-review-list
python main.py ar-review-show PAY-005
python main.py ar-review-correct PAY-005 --apply INV-AR-101:10000 --apply INV-AR-102:15000 --reason "Customer confirmed both invoices"
python main.py cash-forecast --as-of 2026-09-30 --weeks 13
python main.py ar-demo
python main.py ar-forecast-demo
python main.py reconcile-cash --month 2026-09 --seed-demo
python main.py reconcile-trace REC-001
python main.py eval-cash-reconciliation
python main.py audit-demo
python main.py audit --period 2026-09 --seed 26
python main.py eval-audit
python main.py demo-reporting
python -m reporting.demo
python -m invoice_ingestion.demo
python main.py integration-demo
python main.py generate-sample-data --seed 42 --month 2026-09 --output data/demo
python main.py validate-sample-data --data-root data/demo
python main.py sample-data-summary --data-root data/demo
python main.py evaluate-cfo --data-root data/demo --seed 42 --all
python main.py cfo-demo
python demo_web.py          # from repo root: Maximor demo website API on :8765
# then: cd web && npm install && npm run dev
```

Webhook receipt is deterministic. Agents classify messy email/PDF content later; they do not verify signatures or add payout totals.

```
                         OFFICE OF THE CFO

          AP / INVOICE EVENTS             CASH EVENTS

        Gmail        Outlook             Stripe
           \           /                    \
            Email classifier                 \
                 \                              \
        Xero ─────┼──► Canonical Invoice       Provider Payout
        Coupa ────┤           │                /
        NetSuite ─┘           ▼               /
                       Existing AP      Adyen
                           │               │
                           ▼               ▼
                       Accruals      Cash Reconciliation
                           \               /
                            \             /
                             Shared overlay / traces
                                  │
                                  ▼
                    python main.py close / demo-close
```

Gmail and Outlook share `interpret_email`. Stripe and Adyen never become `InvoiceCandidate`. Coupa and NetSuite are official API syncs (no fabricated invoice webhooks). Research notes: [`docs/integrations.md`](docs/integrations.md).

```bash
python main.py integration-demo
python main.py stripe-demo
python main.py webhook-demo stripe
python main.py sync stripe
python main.py webhook-server   # POST /webhooks/{stripe,adyen,gmail,outlook,xero}
```

### Live Stripe (optional)

Stripe is the only live external integration in this repo. Default remains mock (`STRIPE_MODE=mock`); demos and tests need no credentials.

```bash
# .env
STRIPE_MODE=live
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

```bash
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe
python main.py webhook-server
python main.py sync stripe
python main.py integrations status
```

Never commit real keys. `integrations status` reports configured/missing, never the secret values. Stripe payouts feed cash reconciliation only; they are not AP invoices.

Each workflow prints the decision, then saves a JSON trace under `runs/`. The ingest demo works without an API key (deterministic extraction). Add `--llm` to run the source agents live.

Inspect assigned skills without an API key:

```bash
python main.py skills
python main.py skills --agent accrual
```

## AP architecture

```
Invoice ID
  → Python evidence
  → AP Preparer
  → Exception Investigator (only if exceptions exist)
  → AP Reviewer
  → AP Approver
  → AP Audit
  → one reconsideration if audit rejects an APPROVE
  → FINAL APPROVE or HOLD
  → approved invoices enter the payment pool
```

## Payment scheduling

AP validation answers whether an invoice is valid enough to pay. The Payment Scheduler answers which approved invoices should actually be paid this week.

```
Approved invoice pool
  → Payment Scheduler Agent
  → cash + due dates + discounts
  → Python policy net (P-012–P-016)
  → Payment Audit
  → this week's plan + metrics
```

```bash
python main.py schedule --seed-demo
```

`--seed-demo` fills `data/approved_pool.json` with invoices that AP policy would allow, so you can demo scheduling without running all 20 AP cases. A live `python main.py INV-001` that ends APPROVE also writes that invoice into the pool.

Python owns the arithmetic:

- Spendable cash = bank + expected receipts − payroll − other commitments − minimum reserve
- Discount open if `early_payment_discount_deadline >= as_of_date`
- Due this week if `0 <= days_until_due <= payment_horizon_days`

The agent proposes a plan. Python then strips HOLD invoices, blocks reserve breaches, captures open discounts when cash allows, pays late/due invoices, and defers unnecessary early payments (closed discount and not due this horizon). No bank payment is executed.

As of 2026-09-19, spendable cash is $115,000. GitHub `INV-009` ($21,000, due October 2, no discount) is affordable but should be deferred. AWS `INV-002` is due this week. Google Cloud `INV-006` is already late. Office Depot / Figma / Stripe / Acme still have open 2/10 discounts.

Metrics on the plan: on-time percent, discounts captured, late fees avoided, reserve violations, unnecessary early payments, cash retained.

## Accounts receivable

Customer invoices age, collections decide who to chase, and incoming cash is applied to the right invoices — including when the remittance does not say which.

```
Customer invoices
  → AR aging engine (Python)
  → Collections candidates (Python)
  → Collections Agent
  → payment arrives
  → cash-application candidates (Python)
  → Cash Application Agent / Reviewer
  → AUTO_APPLY / HUMAN_REVIEW / UNAPPLIED
  → AR subledger + shared close/audit snapshot
```

Python owns aging math, match combinations, posting, and hard rules (no chase on paid or disputed invoices, no over-application, no silent rewrite of a bad proposal). Agents judge tone, remittance ambiguity, and escalation. `ar-demo` is deterministic and does not need an API key. Add `--llm` on `ar-collections` or `ar-cash-apply` to use the live agents.

State persists under `runs/ar/`. A posted application changes invoice outstanding balances, so the next aging run, close snapshot, and audit trail all see the same books.

## Month-end close

`python main.py close 2026-09` and `python main.py demo-close` are compatibility aliases for the same month-end engine as `close-month`. They do not run a second close state machine.

HOLD invoices never enter the scheduler. Accruals never become payables until an invoice arrives. Provider payouts stay off the AP inbox. A bill already received, including Helios via Outlook, is not accrued.

The Accrual Agent is unchanged. Month-end close calls it, then adds prepaid amortization, fixed-asset depreciation, evidence-tied balance-sheet recs, and a real checklist.

```
Ingest → AP / AR / cash
      → Accrual Agent (existing)
      → Prepaid amortization
      → Depreciation / amortization
      → Balance-sheet reconciliations
      → Exception review → final review → mark closed
```

Dependencies are explicit in `close/checklist.py`. A task is READY only when every dependency is COMPLETE. NEEDS_REVIEW, BLOCKED, or FAILED upstream work blocks dependents. Completed journal keys are idempotent, so a rerun does not repost.

| Workflow | What is new vs existing |
|---|---|
| Accruals | Existing Accrual Agent / `accrue.py`. Called, not rewritten. |
| Prepaids | New. Python builds straight-line or daily-prorated schedules. Agents choose treatment. |
| Fixed assets | New. Straight-line depreciation, duplicate detection, intangible amortization. |
| Cash rec | Existing `cash_recon` engine. Wrapped into the cash close task and the Cash BS rec. |
| BS recs | New. Ledger vs evidence for cash, AR, AP, accruals, prepaids, and fixed assets. |
| Orchestrator | New checklist with statuses, blockers, and preparer/reviewer separation. |

Deterministic Python owns amounts, schedules, ceilings, and match math. Agents choose among Python candidates and may escalate. They cannot invent arithmetic or silently force a rec to match.

Preparer agents assemble evidence and propose treatment. Reviewer agents inspect those outputs and may approve, reject, request evidence, or escalate.

```bash
python close.py run --period 2026-09
python close.py status --period 2026-09
python close.py reviews --period 2026-09
python close.py finalize --period 2026-09
python main.py close run --period 2026-09
python main.py close reviews --period 2026-09
python main.py close finalize --period 2026-09
python demo_month_end_close.py
python demo_month_end_close.py --resolve
python close.py eval-live --deterministic
```

The default September close is BLOCKED: cash $12.40 unexplained, unmatched AR $4,500, and a prepaid missing its Northshore policy. Reviewers resolve those cases by mutating the source objects, then `rerun` and `finalize` move the period to CLOSED. `--clean` remains a hidden fixture, not the successful-close path.

Sample demo output:

```
[1/8] AP COMPLETE
[2/8] AR COMPLETE
[3/8] Cash reconciliation NEEDS_REVIEW
[4/8] Accruals COMPLETE
[5/8] Prepaid amortization COMPLETE
[6/8] Depreciation COMPLETE
[7/8] Balance-sheet reconciliations BLOCKED
[8/8] Final review WAITING

SEPTEMBER 2026 CLOSE
--------------------
Cash reconciliation          NEEDS_REVIEW
Balance-sheet reconciliations BLOCKED
Final review                 NOT_STARTED

3 accounts still require attention:
- Cash: $12.40 unexplained difference
- AR: $4,500 customer payment unmatched
- Prepaids: missing insurance policy evidence

Close status: BLOCKED
```

The $60,000 Dell server (`INV-021`) starts as an AP capital invoice, becomes a fixed asset, is depreciated, hits the GL, appears in the fixed-asset rec, and is linked on the close checklist.

Limitations: demo books are JSON files, not a production ERP; live agents are optional and not required for tests; cash rec still uses the existing in-memory store; capitalization policy is a simple cost/useful-life rule.

### Tests

```bash
python -m pytest tests/
```

Live-agent evaluation is local only and is not part of CI:

```bash
python close.py eval-live --deterministic
python accrue.py eval-live 2026-09 --runs 5
```

## Best invoices to test

| Invoice | Branch | Likely final |
|---|---|---|
| `INV-001` | Clean three-way match, investigator skipped | APPROVE |
| `INV-017` | Vendor alias `Acme Supply Co.` vs `Acme Supplies` | APPROVE if CASE-001 + P-007 apply, else HOLD |
| `INV-011` | Amount variance inside P-009 | APPROVE or HOLD after investigation |
| `INV-018` | Duplicate vendor invoice number | HOLD |
| `INV-016` | Missing PO | HOLD |

## Invoice ingestion

Source components collect invoices. They do not approve them, decide accounting treatment, or book accruals. The existing AP workflow still reviews payment. The Accrual Agent still owns missing-invoice accruals.

```
Messy source (email, PDF, employee upload, portal document)
  → agent interpretation where useful
  → InvoiceCandidate

Structured source (ERP, Coupa-style record, EDI 810 / UBL)
  → deterministic Python parser
  → InvoiceCandidate

InvoiceCandidate
  → Python validation
  → Python dedupe + canonical identity
  → Canonical invoice (in-memory registry)
  → existing AP workflow (overlay, once)
```

Python owns structured parsing, arithmetic, validation, hashes, canonical identity, cross-run replay detection, and AP handoff idempotency.

AI source components may classify messy documents, extract unstructured fields, and explain ambiguous records. They may **not** approve invoices, match AP, create accruals, decide payment timing, invent missing fields, or manufacture an invoice from a card charge.

| Source | How it is read |
|---|---|
| Email | Unstructured. Classify inbox mail/attachments; keep message provenance |
| ERP | Structured. Map NetSuite/SAP/Oracle/Workday mock records in Python |
| Procurement | Structured. Coupa-style invoices in Python; keep PO/receiving; no AP matching |
| Vendor Portal | Unstructured. AWS/Microsoft PDFs; skip statements |
| Employee | Unstructured. True vendor invoices vs receipts/reimbursements |
| Document | Unstructured. Scanned PDFs via a replaceable text-extraction layer |
| EDI | Structured. Deterministic 810/JSON/UBL parse; LLM only if mapping is incomplete |
| Bank/Card | Discovery only. A charge is not an invoice. Recover a candidate only if supporting docs exist |

Canonical identity is `normalized vendor + invoice number` (see `canonical_invoice_key`). Document hashes and source IDs are secondary indexes. Amount and date are not part of the primary key, so two different bills can share a round number.

The same AWS bill arriving from Gmail, the AWS portal, and a card charge (`INV-9001`) becomes **one** canonical invoice with all three source refs. It is forwarded to AP once. Re-running ingestion in the same process attaches no second payable. Acme `ACM-2026-4410` maps to existing `INV-001` and is never forwarded again. A WeWork card charge with no invoice stays `invoice_missing`.

New invoices live in an **in-memory overlay and canonical registry** for the process. They are not written to `data/invoices.json` and they do not survive a new Python process. That is a HackMIT demo limit, not a production database.

### Demo

```bash
python -m invoice_ingestion.demo
python -m invoice_ingestion.demo --replay
python main.py ingest 2026-09 --no-ap
python main.py ingest 2026-09 --replay-check
python main.py ingest 2026-09 --llm
```

`--replay` / `--replay-check` runs ingestion twice in one process and prints `New canonical invoices: 0` / `New AP handoffs: 0`. `--llm` uses source agents on unstructured records only; ERP, procurement, and EDI still parse in Python.

Mock source data lives in `data/ingestion/`. Audit traces are written to `runs/ingestion/` and include `canonical_key`, `status` (new invoice, duplicate within run, existing canonical, already in AP, new provenance, source replay, not an invoice, missing documentation), and `ap_handoff`.

To replace a mock with a real API, keep the same `list_*` / `get_*` tool shapes in `invoice_ingestion/store.py` and `invoice_ingestion/tools.py`. Identity, validation, and AP handoff stay in Python.

### Tests

```bash
python -m pytest tests/
```

## Accrual Agent

At month-end, goods or services may already be consumed while the vendor invoice is still missing. Those costs still belong in the period.

**Python** discovers which expenses are expected from cadence, contracts, usage, POs, and receipts, then computes named estimate candidates (last invoice, recent average, trend, usage × rate, seasonal prior year, contract, goods receipt).

**The LLM** estimates only the missing-bill candidates. It chooses among those candidates and decides `ACCRUE`, `SKIP`, or `INSUFFICIENT_EVIDENCE`. It does not invent amounts.

**Safety rules the model cannot override:** a current-period invoice skips the vendor; an unbilled goods receipt must accrue; a malformed decision is rejected instead of silently repaired; journals stay balanced; duplicates and second reconciles are blocked.

Expectation confidence (“is an expense due?”) stays separate from estimate confidence (“how sure is the dollar amount?”).

### Run

```bash
python accrue.py discover 2026-09
python accrue.py 2026-09
python accrue.py compare 2026-09
python accrue.py reconcile 2026-09
python accrue.py backtest
python accrue.py eval-live 2026-09 --runs 5
python accrue.py demo
python -m pytest tests/
```

`discover` infers expected expenses and missing bills from evidence. The normal close command runs discovery first, then the existing Accrual Agent. `compare` records live-agent vs evidence-type policy without forcing agreement. `backtest` hides historical invoices, estimates as-of that close, then scores the reveal. `eval-live` is a local multi-run consistency check (not CI). `demo` is DISCOVER → ESTIMATE → BOOK → MEASURE → RECONCILE.

AWS `INV-002` ($8,320 usage on PO-102) and `INV-016` ($2,775 unplanned overage, no PO) are two distinct September charges. Discovery treats the expected AWS obligation as satisfied when any current-period invoice exists, and reports both bills.

Per-vendor traces land in `traces/accruals/2026-09/<run>/` and are not overwritten. Discovery, accrual, and reconciliation IDs stay linked. Backtest details persist under `traces/accruals/backtest/`.

### Aether example

August bill $12,250. Trend $12,767. Recent average $11,583. September usage × committed rate **$11,849.90**. The useful number is usage, not last month. When the October invoice arrives at $12,100, reconciliation shows a **+$250.10** estimation error, then reverses the accrual and books the actual bill.

## Cash and bank reconciliation

`python main.py reconcile-cash --month 2026-09 --seed-demo` matches a month of bank activity to the cash ledger. Python generates candidates and owns every sum. Stripe and Adyen payouts are delegated to the existing adapters; they are not reimplemented.

```
Bank statement
  → Python normalization and candidate generation
  → Cash Reconciliation Preparer
  → Python validator
  → Cash Exception Investigator (exceptions only)
  → Cash Reconciliation Reviewer
  → monthly report + per-item traces under traces/cash_recon/
```

Deterministic statuses: `MATCHED`, `EXPLAINED_EXCEPTION`, `OUTSTANDING_TIMING_ITEM`, `HUMAN_REVIEW`. The period may not report `RECONCILED` if the arithmetic does not tie, or if unexplained / duplicate items remain. Proposed bank-fee journals are never auto-posted.

```bash
python main.py reconcile-cash --month 2026-09 --seed-demo
python main.py reconcile-trace REC-001
python main.py eval-cash-reconciliation
```

The seeded September 2026 statement includes an exact vendor payment, one ACH covering three invoices, a wire net of a $25 bank fee, a duplicate card refund, a $12.40 unexplained deposit difference, a month-end timing item, a duplicate GL posting, Stripe and Adyen payouts, a clean customer receipt, and unmatched miscellaneous activity.

## Shared sample-data generation

Five specialized sample-data agents write **one** internally consistent synthetic company (Maximor Demo Corp) for September 2026. They do not emit five disconnected fixture packs. The same economic event keeps the same identity and amount from AP through GL, bank, cash reconciliation, forecast actuals, month-end close, audit population, and reporting.

```
                 AP / AR
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
         GL       Cash     Forecast
          │         │         │
          ├─────────┴─────────┤
          ▼                   ▼
        Close              Reporting
          │                   ▼
          └─────────┬─────────┘
                    ▼
                  Audit
```

Generation order is fixed: shared `CompanyScenarioContext` → AP/AR Sample Data Agent → Cash Recon Sample Data Agent → Close Sample Data Agent → Audit Controls Sample Data Agent → Reporting Forecasting Sample Data Agent → cross-domain validators → `manifest.json`.

Python owns IDs, dates, amounts, aging, balanced journals, forecast roll-forwards, and expected numerical outcomes. Agents may choose approved scenario templates and narrative text. They do not perform arithmetic and they never load the answer key.

```bash
python main.py generate-sample-data --seed 42 --month 2026-09 --output data/demo
python main.py validate-sample-data --data-root data/demo
python main.py sample-data-summary --data-root data/demo
```

`--seed 42` is deterministic. A second run with the same seed produces the same canonical records (generation timestamps are fixed). Output goes to `data/demo/` so the hand-written fixtures under `data/` stay intact. Existing workflows consume the generated files through the same models; `sample_data/paths.py` remaps loaders when a data-root is applied.

| Artifact | Purpose |
| --- | --- |
| `data/demo/*.json` and domain subfolders | Operational inputs in the exact schemas already used by AP, AR, cash recon, close, audit, reporting, Stripe, and ingestion |
| `data/demo/canonical/` | Shared vendor payments, journals, scenario registry, and storylines |
| `data/demo/manifest.json` | Seed, period, file list, record counts, planted scenario IDs |
| `data/demo/expected_results.json` | Hidden answer key for tests only. Operational agents must never load it |

Planted cases live in `sample_data/registry.py` (`SCN-AP-001` clean three-way match, `SCN-CASH-005` unexplained $12.40, `SCN-AUDIT-005` self-approval, `SCN-REPORT-001` gross-margin decline, and the rest of the catalog). Three demo storylines follow one transaction across functions: clean (`INV-001`), resolved exception (`INV-017` fee-netted wire), and unresolved review (`INV-AR-013` / `$12.40`).

Adapters in `sample_data/adapters.py` convert a canonical object into a consumer schema (AP invoice → audit invoice, Stripe payout → bank deposit, journal → reporting line). They copy identity and amount; they do not invent a second copy.

## CFO evaluation harness

`python main.py evaluate-cfo` runs the **existing** finance workflows against generated operational files, then scores them. The answer key is loaded only after workflows finish. Agents never receive `expected_results.json`, planted labels, or `ground_truth.json`.

```bash
python main.py evaluate-cfo --data-root data/demo --seed 42 --all
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain ap
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain ar
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain cash
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain close
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain audit
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain reporting
python main.py evaluate-cfo --data-root data/demo --seed 42 --domain forecasting
python main.py evaluate-cfo --data-root data/demo --seed 42 --compare-to runs/evaluation/baseline/benchmark.json
```

Artifacts land in `runs/evaluation/<run_id>/` (`benchmark.json`, `cases.json`, `failures.json`, `summary.md`, `raw_outputs/`). Scoring is deterministic Python. An LLM is not used to grade amounts, matches, or findings.

## Reporting and 13-week cash forecast

`python main.py demo-reporting` (or `python -m reporting.demo`) builds financial statements from the reporting ledger, explains the September gross-margin move at transaction level, rolls a 13-week cash forecast from the existing AP pool, AR invoices, and payroll schedule, compares that snapshot with later actuals, and writes a board pack with evidence IDs.

Python owns every total. Agents only narrate. Forecast snapshots under `runs/reporting/forecasts/` are immutable. Architecture: [`docs/reporting.md`](docs/reporting.md).

```
Reporting ledger
  → statements + variances
  → Variance Analysis Agent
  → Reporting Reviewer
  → Board Reporting Agent

AP + AR + payroll
  → forecast lines
  → weekly cash roll-forward
  → Cash Forecast Agent
  → Forecast Reviewer
  → snapshot
  → actuals
  → Forecast Variance Agent
```

The August/September P&L demo is synthetic. AP, AR, and payment IDs are the same canonical records used by the other workflows.

## Independent audit

After AP, AR, cash reconciliation, close, and payment work is recorded, a separate Auditor Agent reviews that work. Python samples the population, reruns existing controls and reconciliation engines, and builds findings. The agent interprets severity and writes report language from those facts. Source invoices, payments, journals, and reconciliations are not rewritten.

```
Operational AP / AR / cash / close
  → recorded IDs and traces
  → Auditor Agent (independent)
  → deterministic sampling + controls + re-performance
  → structured findings + report
```

```bash
python main.py audit-demo
python main.py audit --period 2026-09 --seed 26
python main.py eval-audit
```

`audit-demo` does not need an API key. Dedicated fixtures live in `data/audit/` so the normal AP and cash-recon datasets stay stable.

## Agent skills

```
Agent
  + selected tools
  + selected skills

Python     facts, calculations, validation, hard constraints
Tools      data and actions available to agents
Skills     reusable model reasoning and procedures
```

Agents receive only the skills relevant to their job. Adding a skill does not grant new external permissions; tools still control data access and actions. Python still owns calculations and policy enforcement.

Skill assignment examples:

```
Accrual Agent
  -> accrual-evidence-evaluation
  -> accrual-method-selection

Payment Scheduler
  -> payment-prioritization
  -> early-payment-discount-evaluation

Collections Agent
  -> ar-collections-policy

Cash Application Agent
  -> cash-application

Variance Analysis Agent
  -> financial-variance-analysis

Cash Forecast Agent
  -> cash-forecasting
  -> ar-cash-forecasting

Board Reporting Agent
  -> board-financial-reporting

Cash Reconciliation Preparer
  -> cash-reconciliation-method-selection
  -> bank-reference-interpretation

Auditor Agent
  -> audit-sampling-interpretation
  -> control-testing-interpretation
  -> reconciliation-reperformance-review
  -> segregation-of-duties-interpretation

Audit Report Agent
  -> audit-finding-writing

Email Invoice Agent
  -> invoice-source-identification
  -> invoice-field-interpretation

ERP Invoice Agent
  -> (none)

Prepaid Preparer / Reviewer
  -> prepaid-expense-accounting

Fixed Asset Preparer / Reviewer
  -> fixed-asset-depreciation

Balance Sheet Reconciliation Preparer / Reviewer
  -> balance-sheet-reconciliation

Month-End Close Reviewer
  -> month-end-close-review

Close Manager
  -> month-end-close-coordination

AP/AR Sample Data Agent
Cash Recon Sample Data Agent
Close Sample Data Agent
Audit Controls Sample Data Agent
Reporting Forecasting Sample Data Agent
  -> synthetic-finance-scenario-design
  -> cross-ledger-data-consistency
```

Traces record agent role, assigned skill names, file paths, content hashes, and whether each skill was injected into instructions. They do not dump `SKILL.md` bodies.

The running registry is [`skills/README.md`](skills/README.md). Assignments are in `skills/assignments.py`. Inspect with `python main.py skills`.
