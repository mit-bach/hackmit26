# Office of the CFO Agents

Autonomous finance agents for HackMIT: accounts payable matching and period-end expense accruals.

Python computes the facts. Agents decide. There is no human-review step.

Reusable agent expertise lives in `skills/`. Agents, tools, and Python stay separate: see [`skills/README.md`](skills/README.md).

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
python main.py skills
python -m invoice_ingestion.demo
```

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

Email Invoice Agent
  -> invoice-source-identification
  -> invoice-field-interpretation

ERP Invoice Agent
  -> (none)
```

Traces record agent role, assigned skill names, file paths, content hashes, and whether each skill was injected into instructions. They do not dump `SKILL.md` bodies.

The running registry is [`skills/README.md`](skills/README.md). Assignments are in `skills/assignments.py`. Inspect with `python main.py skills`.
