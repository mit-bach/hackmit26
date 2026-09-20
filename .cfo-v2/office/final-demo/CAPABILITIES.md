# Capabilities — Office of the CFO

As of 2026-09-20. This is the product account for the website and for judges. Working session notes are not this file.

The office is an agentic finance function for **Maximor Demo Corp** (`CO-MAXIMOR`). It pays vendors, collects from customers, reconciles cash, closes the month, forecasts, answers audit, and explains why the numbers moved. One invoice keeps the same identity in AP, bank, GL, close, forecast, and audit.

Python owns amounts. A model chooses among Kernel candidates. It does not invent totals. Uncertain work goes to a Verifier Bot. The human Operator is an emergency stop and a demo overlay. It is not a worker.

Simulated data only. There is no live Stripe, Gmail, Outlook, or ERP write-back in this demo.

## How to read status

| Status | Meaning |
| --- | --- |
| **Kernel-live** | Engine exists. The World pack plants a case. Python tests or evals exercise it. |
| **Office-live** | A standing Harness Bot can take this work on `http://127.0.0.1:8800/`. |
| **Planted** | Records exist in `.cfo-v2/office/world/maximor`. |
| **Holdout** | A catalog exists. It is not in operational books. Bots must not load it. |
| **Partial** | A real path exists. The demo cannot show the full lifecycle yet. |
| **Not built** | Do not invent a finding or a UI outcome. |

`world/maximor/system_capabilities.json` marks almost every Kernel workflow `IMPLEMENTED_AND_TESTED`. That file is a V1 CLI inventory. It is not the office score. It is not proof that Pi completed the path on 8800. Use this document when those two disagree.

## Four layers

Keep these apart. The website reads them. It does not replace them.

1. **Kernel** — `.cfo/`. Arithmetic, candidates, cents, period-lock math, eval isolation, workflow runners.
2. **Office** — `.cfo-v2/office/`. Named Bots, Profiles, Grants, Handles, Rooms, Routines. Pi is the turn engine inside a Bot.
3. **World pack** — `.cfo-v2/office/world/maximor`. Preexisting Maximor books. The Computer loads this tree (`computer/data` → `../world/maximor`).
4. **Website** — partner UI. Read-and-invoke over Kernel and the World pack. No second invoice store. No hard-coded demo outcomes.

## Company the agents onboard onto

Agents do not create Maximor. They discover registers that already exist.

| Fact | Value |
| --- | --- |
| Legal name | Maximor Demo Corp |
| Trade name | Maximor |
| ID | `CO-MAXIMOR` |
| HQ | Cambridge, MA |
| Currency | USD |
| Closed period | August 2026 |
| Open close | September 2026 |
| Limited follow-through | October 2026 (Harbor Electric / legal bills, forecast actuals) |
| Bank | `BANK-OPERATING` |
| Stripe (simulated) | `acct_maximor_demo` |

Target economics for later adversarial plants: about **$372.4M** annual run-rate, 340 vendors, 2,840 W-2 staff. The World pack is denser than the old 29-invoice toy. It is not yet that $372M company. See [WORLD.md](WORLD.md).

## Bots

Grain law is fifteen finance Bots. World is the sixteenth Source Bot: the simulated outside mailbox. Bot files exist. Inbox Kernel tools exist. The Computer `roster.json` on disk currently lists **15** slugs and omits World Handles. Health can still count 16 because `computer/harness/bots/bot_world` is on disk. The website should treat World as a real lane that is being reattached, not as a missing idea.

| Class | Slug | Display names (Profiles) | Owns |
| --- | --- | --- | --- |
| Source | `email` | Finance Inbox Agent, Email Invoice Agent, plus other intake Profiles | Messages and attachments. Classify. Outbound missing-info. Does not match or pay. |
| Source | `stripe` | (processor unpack) | Simulated payouts, fees, refunds, chargebacks. Not an `InvoiceCandidate`. |
| Source | `bank` | Bank/Card Discovery Agent | Bank lines and card charges. A charge is not a bill. |
| Source | `books` | ERP / procurement / EDI Profiles | GL, subledgers, vendor and customer master, POs, lock state (read). |
| Source | `world` | Counterparty Message Agent (vendor, customer, bank, employee) | Role-play whoever finance mailed. Compose and send inbound mail. Does not classify the finance inbox. |
| Operator | `ap` | AP Preparer, Exception Investigator | Open bills. Three-way match. Hold. Does not pay. Does not concur. |
| Operator | `pay` | Payment Scheduler | Weekly payment-run draft over the approved pool. Does not move money. |
| Operator | `apply` | Cash Application Agent | Unapplied cash. Stick Kernel-valid remittances to invoices. |
| Operator | `collect` | Collections Agent | Open invoices still owed after apply. Dunning is outbound mail then World. |
| Operator | `cash` | Cash Reconciliation Preparer, Cash Exception Investigator | Unmatched bank lines. Does not force MATCHED. |
| Operator | `close` | Accrual, prepaid, fixed asset, BS rec, Close Manager | Period completeness. Accrue, defer, tie, coordinate. |
| Operator | `story` | Variance, board, forecast Profiles | Flux, 13-week forecast, board pack. Does not move money. |
| Verifier | `ctl-pay` | AP Reviewer / Payment Audit shaped Profiles | Concurrence for AP match, pay-run release, write-off. |
| Verifier | `ctl-cash` | Cash / apply reviewers | Concurrence for material cash application and bank-rec sign-off. |
| Verifier | `ctl-books` | Month-end reviewers | Concurrence for close treatments and period lock. |
| Assurance | `audit` | Auditor Agent, Audit Report Agent | After-the-fact sampling, re-performance, findings. Does not concur in the pay path. |

Sample-data Display names are not Bots. A Pipe is not a Bot. The Kernel sidecar is not a Bot.

Hard rules that stay true in every capability below:

1. Skills never grant tools. Grants come from compiled constructor lists.
2. Do not union two Grant sets in one turn. A Wake names one Profile.
3. Fail closed. Missing evidence is HOLD / refuse / INSUFFICIENT, not a guess.
4. Operational Bots never load `expected_results.json`, gauntlet private answers, or the adversarial catalog.
5. `HUMAN_REVIEW` is a Kernel fail-closed outcome. The queue owner is a Verifier Bot. Do not say it to judges as a human queue. Say exception open or close blocked.
6. Handle accept is not complete. Peer Handle is not approval.

## Capability map

Each row is one thing the function can do. **Now** is honest about Kernel vs office. **Next** is planned, not planted.

### Intake

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `inbox.counterparty_to_ap` | World role-plays a vendor or customer and delivers mail. Email classifies and dispatches. | Kernel-live (compose, send, reply, classify, dispatch). Office: World package and inbox tools exist. Roster on disk omits `world`. | Put World back on the roster. Wire `email/outbound` → World, `collect/dun` → World, `world/delivered` → Email `triage`. Run this at inbox scale, not two seeded messages. | 17 inbox messages (`MSG-INBOX-001` …). Quote, statement, newsletter, duplicate copy, prompt-injection, remittance, credit memo. |
| `ingestion.classify_document` | Tell a vendor invoice from a quote, PO, receipt, statement, marketing, or duplicate copy. Extract fields without inventing amounts. | Kernel-live. Email Bot is office-live for classify. | Invoice-Sandbox-grade PDFs on more vendors. Hide answer keys. | `SCN-ING-001` … `SCN-ING-010`, `SCN-AP-012`. 10 ingestion emails plus 385 document files. |
| `ingestion.structured_parse` | Parse ERP / Coupa / EDI into an invoice candidate. | Kernel-live. Books Bot lands structured sources. | Keep simulated. No NetSuite post. | `SCN-ING-001`, `SCN-ING-010`. |
| `ingestion.bank_card_discovery` | A card charge is not a bill. Recover an invoice only when supporting documents exist. | Kernel-live. Bank Bot is office-live. | — | `SCN-AP-012`. |

### AP and pay

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `ap.three_way_match` | Match invoice to PO and goods receipt. APPROVE or HOLD with exception types. | Kernel-live. AP Bot office-live. ctl-pay concurs. | Quiet near-duplicate vendors and PO splits from the adversarial catalog, after Phase B plant. | `INV-001` clean. `INV-003` qty. `INV-004` price. `INV-005` missing GR. `INV-006` duplicate. `INV-021` August alias precedent. |
| `ap.payment_scheduling` | Rank the approved pool for this week. Capture 2/10 when cash allows. Skip held bills. | Kernel-live. Pay Bot office-live. ctl-pay concurs release. | — | `SCN-AP-009` eligible. `SCN-AP-010` not due. `SCN-AP-011` discount. |
| `ap.self_improvement` | Write a vendor alias into operational AP memory so the next similar bill can retrieve it. Precedent cannot override a live `must_hold`. | **Kernel-live.** `prior_cases.json` remains a seed, not the happy path. Not office-live Pi on 8800. | Keep the store on the Computer. Do not make a human edit the seed file. | Runtime alias pair (INV-LEARN class). `INV-021` August seed still exists. |
| `ap.vendor_bank_change` | Flag a vendor payment-instruction change. | **Not built.** Vendor master now has bank fields. There is no control engine. | Build the control. Adversarial plants need those fields. | Vendor `bank_routing` / `bank_account` exist on 52 vendors. |

### AR

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `ar.aging_collections` | Age open invoices. Choose the next chase action. Collect Handles World after dunning. | Kernel-live. Collect Bot office-live. World reply path partial (see intake). | Full World round-trip on every dun. | Aging buckets `SCN-AR-001` … `005`. Chase `SCN-AR-012`. Quiet Harbor `INV-AR-014`. |
| `ar.cash_application` | Apply a remittance. Exact, partial, batch, unlabeled, ambiguous, overpay. | Kernel-live. Apply Bot office-live. Ambiguous → ctl-cash. | Credit-memo / unapplied-cash subledger (partial today). | `PAY-001` exact. `PAY-004` unlabeled $5,000 → exception. `PAY-007` overpay detection. |
| `memory.self_improvement` | Learn from a structured AR correction. | Kernel-live for AR precedents. AP alias memory is `ap.self_improvement` (Kernel-live, not office-live). | Keep the AR claim narrow. | `SCN-LEARN-001`. |

### Cash

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `cash.bank_reconciliation` | Match bank to ledger only when evidence supports it: exact, grouped ACH, fee-netted, timing, duplicate, unexplained. | Kernel-live. Cash Bot office-live. ctl-cash sign-off. | RecBench-style difficulty already sampled on volume lines. Plant ADV residual explanation without renaming `TXN-2026-09-015`. | `TXN-2026-09-018A` exact. Grouped ACH. `TXN-2026-09-011` FEE_NETTED. **`TXN-2026-09-015` $12.40 unexplained. Close stays blocked.** |
| `cash.stripe_reconciliation` | Unpack charges − fees − refunds − disputes = bank deposit. | Kernel-live on simulated Stripe. 114-event sim pack on disk. Demo payouts in the pack: 3. | Use the sim pack as Stripe Bot world. Sample DABstep volume behind it. Never live keys in the judged demo. | `SCN-CASH-009` … `011`. |

### Close

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `close.accruals` | Accrue missing bills from history, contract, usage, POs. ACCRUE / SKIP / INSUFFICIENT. | Kernel-live. Close Bot office-live. Harbor Electric is the memory thread. | Wire October actual-bill reversal into the default path. Deterministic planted IDs. | `SCN-CLOSE-001`, `SCN-CLOSE-002`, `SCN-MEM-004`. |
| `close.prepaids` | Spread prepaid software / insurance over the service period. | Kernel-live. | Adversarial Orbit prepaid that never hits P&L is holdout. | `SCN-CLOSE-003`, `004`, `009`. |
| `close.fixed_assets` | Capital vs expense. Straight-line depreciation. | Kernel-live. Dell `INV-018` capitalized on the same identity. | Missing-asset holdout (`SL-ADV-CLOSECOSMETIC`). | `SCN-CLOSE-005`. |
| `close.balance_sheet_recs` | Tie cash, AP, AR, accruals, prepaids, assets to evidence. | Kernel-live. | — | `SCN-CLOSE-006` … `010`. |
| `close.month_end` | Coordinate tasks. Gate the lock. Stay BLOCKED on a material unexplained difference. | Kernel-live. Close Manager SDK path is **partial** (`deterministic_coordinate()` in production). ctl-books owns lock. | Live Close Manager when `live=True`. Do not delete the $12.40 to “close” the month. | `SCN-CLOSE-011`, `015`, `SCN-CFO-001`. |

### Audit, story, memory, orchestration

| ID | Capability | Now | Next | Planted cases |
| --- | --- | --- | --- | --- |
| `audit.controls` | Independent sample, re-perform, control test, write findings. Must not use operational conclusions as inputs. | Kernel-live. Audit Bot office-live. Loud decoys are planted (Acme LLC dup, $50k round wire, labeled post-close JE). | Detective work on stealth holdout: near-duplicate vendors, ghost payroll, 0.1% residual, lapping. Do not retell the loud decoys as the impressive find. | `SCN-AUDIT-001` … `013`. |
| `reporting.variance_board` | Explain GM 64% → 61% from source txs. Board pack from the GL. | Kernel-live. Story Bot office-live. | Keep the loud GM move as a decoy once quieter theft is planted. | `SCN-REPORT-001`, `002`. |
| `forecast.thirteen_week` | Build 13 weeks from AP, AR, payroll. Explain a miss when actuals land. | Kernel-live. | — | Quiet Harbor late (`INV-AR-014`). `SCN-REPORT-003` … `008`. `SCN-CFO-002`. |
| `memory.cross_period` | Retrieve August precedent. Reuse a treatment only when current evidence still supports it. | Kernel-live for AP alias, Stripe pattern, Harbor method, Atlas batch payer. | Semantic graph / RAG is **not built**. Identity links are provenance, not a graph DB. | `SCN-MEM-001` … `004`. |
| `orchestration.cfo` | One September run: intake → AP/AR/cash → close blocked → story. | Kernel-live via `run_cfo_scenario`. Office proof is live Pi Handles on 8800, not the 97% Kernel number. | Two-hour LM-speed operator script, after data and World are stable. Not scoped in this folder yet. | `SCN-CFO-001`, `SCN-HAND-001`, `SCN-HAND-002`. |
| `evaluation.finance_gauntlet` | Same production workflows, public fixtures, hidden gold. Memory on vs off. Shared state on vs off. | Kernel-live. Last core pack cited in `docs/evaluation.md`: 42/42 memory on; shared-state off drops cross-workflow consistency 100% → 50%. | Keep as **our** measure. Caption: Kernel, not the office. | Families: document traps, cash rec, anti-hack, multi-step, rubric close, consistency, long horizon, recovery. |
| `sample_data.generation` | Deterministic Maximor generator. | Kernel-live. World pack is its output (seed 42, September 2026). | Phase B plants from the adversarial catalog into these registers. | Manifest `validation: PASS`. |

## Show path (public)

These three threads are the consistent plot. The website should draw them on every page that touches the IDs.

1. **STORY-CLEAN** — Acme `INV-001` = `PO-101` = `GR-101`. Paid `PAY-AP-001`. Bank `TXN-2026-09-018A` MATCHED. Audit can re-perform it. Forecast actuals use the same ID.
2. **STORY-RESOLVED** — Helios `INV-017`. Bank `TXN-2026-09-011` is $25 over books. `FEE-729103` supports FEE_NETTED. Close accepts the explained exception.
3. **STORY-UNRESOLVED** — Northstar `INV-AR-013` / `PAY-006` books $12,400.00. Bank `TXN-2026-09-015` is $12,412.40. No fee evidence. Close stays **BLOCKED**.

Do not resolve the $12.40 in the judged demo. The holdout catalog explains it as a 0.1% remittance residual (`ADV-CASH-014` / `SL-ADV-RESIDUAL`). That explanation is not in operational books yet.

Loud Kernel audit toys stay as decoys: `VEND-001-DUP`, `PAY-AP-009` $50,000 round wire, `JE-POST-CLOSE-001`, GM 64% → 61%.

## What we will be capable of (not now)

These are real next steps. They are not current UI states.

1. **Adversarial detective audit.** 109 scenarios, 12 storylines, 30 stealth-5. Designed. Not planted. After Phase B, audit must find quiet theft that started during the CFO sabbatical, before this agentic office was installed. See [SCENARIOS.md](SCENARIOS.md) holdout section. Full plant spec: `office/sessions/ADVERSARIAL-SCENARIOS.md` (Bots must never load it).
2. **World mailbox at full scale.** Every outbound AP/collections mail gets a persona reply. Operator can talk to World on 8800. Reattach roster + Handles.
3. **Preexisting $300–450M registers.** Trailing AP, GL, bank, payroll, processor files already have volume hooks (`holdout/round2_hooks.json`). Scale table is not in `company.json` yet (52 vendors, not 340).
4. **Two-hour demo script.** After the books are the books we want. Density of LM-speed messages, not a 10-minute slide. Not written yet.
5. **Vendor bank-change control and AP learning.** Still not built. Do not show fake findings.

## What we will not claim

- The Kernel 97% / gauntlet 42/42 number is not “the office scored 97%.” Show Inspector Pi RPC and Handles for live proof.
- Live Gmail, live Stripe, live NetSuite.
- `HUMAN_REVIEW` as a person in the chair.
- Semantic context-graph memory we do not have.
- Adversarial storylines as already visible in the GL.

## Skills

Thirty-six SKILL.md files under the Computer and Kernel trees. Skills are instructions. They are not Grants.

Intake: `inbox-triage`, `invoice-source-identification`, `invoice-field-interpretation`, `superseded-document-handling`, `bank-charge-invoice-discovery`.

AP / pay: `three-way-match-analysis`, `ap-exception-investigation`, `payment-prioritization`, `early-payment-discount-evaluation`.

AR: `ar-collections-policy`, `cash-application`, `ar-cash-forecasting`.

Cash: `cash-reconciliation-method-selection`, `bank-reference-interpretation`, `reconciliation-evidence-validation`, `reconciliation-exception-investigation`.

Close: `accrual-evidence-evaluation`, `accrual-method-selection`, `prepaid-expense-accounting`, `fixed-asset-depreciation`, `balance-sheet-reconciliation`, `month-end-close-coordination`, `month-end-close-review`.

Audit / story / memory: `audit-sampling-interpretation`, `control-testing-interpretation`, `reconciliation-reperformance-review`, `segregation-of-duties-interpretation`, `audit-finding-writing`, `financial-variance-analysis`, `board-financial-reporting`, `cash-forecasting`, `forecast-vs-actual-interpretation`, `prior-period-precedent`.

Generator (not office Bots): `synthetic-finance-scenario-design`, `cross-ledger-data-consistency`.

## Website contract

Routes and APIs in `docs/demo_website_architecture.md` still say fifteen Bots and `.cfo/data/demo`. Prefer this folder plus the World pack:

- Company graph: World pack `demo_snapshot.json`, `lineage.json`, `timeline.json`.
- Scenario cards: [scenarios.json](scenarios.json). Hide `expected_*` until a scored run.
- Architecture page: this file, not the V1 `system_capabilities.json` as gospel.
- Evaluations page: Kernel gauntlet and `evaluate-cfo` after a run. Gold stays isolated.
- Do not POST invented agent events. Default Kernel path is deterministic (`live=False`).

Related files and deprecation: [DOCUMENTS.md](DOCUMENTS.md). How we test: [TESTING.md](TESTING.md). What exists in the books: [WORLD.md](WORLD.md).
