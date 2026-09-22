# World pack — Maximor Demo Corp

This is what the data-refinement agent left under `.cfo-v2/office/world/maximor`. The Computer loads it:

```text
.cfo-v2/office/computer/data -> ../world/maximor
```

Seed 42. Schema `2026.09-cfo-sample-2`. Manifest `validation: PASS`. Period September 2026. Comparison August 2026.

Simulated only. No live Stripe, email, or books connector.

## What changed versus the old toy pack

The live desk used to see leftover `.cfo/data` (about 20 invoices, 4 emails). Canonical `data/demo` had 29 AP invoices and four-line fake PDFs.

This pack is the company the office onboards onto:

| Object | Old demo pack | World pack now |
| --- | --- | --- |
| AP invoices (open/current) | 29 JSON stubs | **325** plus **4,840** historical AP register rows |
| Purchase orders | few | **302** |
| Goods receipts | few | **306** |
| Inbox messages | 2 of 17 seeded on the desk | **18** planted (`MSG-PIN-HOLD-01` is a simulated inbox fixture) |
| Ingestion emails | 6 stubs | **10** |
| September bank lines | 19 | **375** |
| Bank history | tiny | **2,562** |
| Journal lines | thin | **5,714** |
| Payroll register | none | **73,853** |
| Processor card txs | none | **3,000** (DABstep-style columns, Maximor merchants) |
| Stripe sim | leftover | **3** demo payouts. `po_1MaximorFees` still equals its bank deposit |
| Vendors | handful | **340** with legal name, DBA, tax ID, address, bank routing/account, aliases |
| Employees (W-2) | none | **2,840** |
| Customers | few | **17** (`CUST-IC-EU` is a billed customer only) |
| AR invoices | few | **146** |
| Close tasks | 8, blocked | **8**, still blocked on $12.40 |
| Scenarios | 72 advertised | **94** public `SCN-*` in `canonical/scenarios.json` |
| Storylines | 3 | same 3 public threads |
| Adversarial holdout | absent | **109** `ADV-*` in `expected_results.json` `adversarial_holdout` only |
| Invoice documents | 32–71 character stubs | Letterhead + line items. `INV-001.txt` still $12,450.00 |

Catalog scale is in `company.json`: **$372.4M** run-rate, August revenue $30.82M, September $31.14M, biweekly payroll $8,437,291.44, AP open $18.42M, AR open $41.26M, operating cash $14,882,410.18. `holdout/round2_hooks.json` `headroom` records that Phase B plants are in.

## Surviving plot IDs (do not retarget)

Clean: `INV-001`, `PO-101`, `GR-101`, `PAY-AP-001`, `TXN-2026-09-018A`.

Resolved: `INV-017`, `TXN-2026-09-011`, `FEE-729103`.

Unresolved: `INV-AR-013`, `PAY-006`, `TXN-2026-09-015` ($12.40), `GL-AR-NS`.

Also keep: `INV-AR-014` (Quiet Harbor late), `PR-2026-10-02` (payroll identity), `VEND-001` / `VEND-001-DUP` (loud decoy).

## What is in the tree

Operational JSON the office may read: invoices, POs, GRs, vendors, customers, AR, approved pool, cash position, policies, prior cases, historical invoices, later invoices, cash recon (bank, ledger, fees, balances), close (prepaids, assets, tasks, journals, prior-period 2026-08 pack), audit populations, reporting (COA, budget, payroll, forecast weeks), Stripe integrations, inbox, ingestion (email, ERP, procurement, portals, EDI, bank txs), canonical vendors/payments/journals/scenarios/storylines, registers (GL, AP history, bank history, payroll, fiscal calendar, bank accounts, approval matrix), documents (invoices, POs, GRs, packing lists), workpapers under `close/`.

Generator exports the data agent was asked to add: `lineage.json`, `timeline.json`, `demo_queries.json`, `agent_cases.json`, `expected_outcomes.json`, `system_capabilities.json`, `demo_snapshot.json`, `memory_events.json`. Those files exist here. They were missing from the old pack.

## Reference datasets (quality bar, not a second company)

Sampled into this pack, not copied as APEX World 9 or DABstep Q&A:

| Source | What was taken |
| --- | --- |
| Invoice Sandbox | Document letterhead / line-item bar. Gold PDFs not copied. Hide answer keys. |
| APEX-Accounting | Workpaper density. Company remains Maximor. |
| DABstep `data/context/` | Processor column layout and 3,000-tx volume. Merchants remapped. |
| RecBench small | Degraded refs, unbundle legs, fee-inclusive descriptions on volume bank lines. Truth files private. |

Clones live under gitignored `office/reference-datasets/`. Census: `office/sessions/BENCHMARK-IMPORT.md`.

## Phase A vs Phase B

Phase A densified Maximor, kept plot IDs, added vendor-master bank fields, trailing registers, documents, and the export layer.

Phase B (this pack): planted the adversarial catalog through `.cfo/sample_data/` at seed 42. Operational rows stay boring. Hidden answers live only under `expected_results.json` → `adversarial_holdout` (109 `ADV-*`, 12 storylines, 30 stealth-5). Bots must not load that key, `holdout/`, or `office/sessions/ADVERSARIAL-SCENARIOS.md`. Plant notes: `holdout/ADVERSARIAL-PLANT-NOTES.md`.

`holdout/round2_hooks.json` still lists stable ID prefixes, do-not-retarget IDs, and unlabeled near-duplicate vendor pairs (`VEND-003`/`VEND-030`, `VEND-005`/`VEND-031`, `VEND-015`/`VEND-032`). Operational Bots must not load that file.

## Counts from `manifest.json`

```text
ap_invoices 325
purchase_orders 302
goods_receipts 306
ar_customers 17
ar_invoices 146
ar_payments 25
vendor_payments 129
bank_transactions 375
ledger_entries 374
stripe_payouts 3
journal_entries 5714
prepaids 5
fixed_assets 3
accruals 3
close_tasks 8
audit_invoices 326
forecast_weeks 13
reporting_lines 45
scenarios 94
memory_events 5
ingestion_emails 10
inbox_messages 18
documents 1239
historical_ap 4840
bank_history 2562
payroll_register 73853
processor_transactions 3000
vendors 340
employees 2840
workpapers 8
adversarial_holdout 109
```

## Website

Load `demo_snapshot.json` for a company graph. Compose from operational JSON plus `lineage.json` / `timeline.json`. Scenario cards: `final-demo/scenarios.json`. Do not feed `expected_results.json` to a page that Bots or judges can confuse with company state.
