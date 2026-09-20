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
| AP invoices | 29 JSON stubs | **110** plus 385 document files |
| Purchase orders | few | **93** |
| Goods receipts | few | **91** |
| Inbox messages | 2 of 17 seeded on the desk | **17** planted |
| Ingestion emails | 6 stubs | **10** |
| September bank lines | 19 | **200** |
| Bank history | tiny | **748** |
| AP history | tiny | **2,640** |
| Journal lines / GL detail | thin | **3,153** |
| Payroll register | none | **1,248** |
| Processor card txs | none | **3,000** (DABstep-style columns, Maximor merchants) |
| Stripe sim events | 114 unused | **114** events on disk. **3** demo payouts in the integrations slice |
| Vendors | handful | **52** with legal name, DBA, tax ID, address, bank routing/account, aliases |
| Customers | few | **15** |
| AR invoices | few | **66** |
| Close tasks | 8, blocked | **8**, still blocked on $12.40 |
| Scenarios | 72 advertised | **94** in `canonical/scenarios.json` |
| Storylines | 3 | same 3 public threads |
| Invoice documents | 32–71 character stubs | Letterhead + line items. `INV-001.txt` is 1,379 bytes (desks + monitors, PO-101, $12,450.00) |

Target scale for adversarial plants was ~$372.4M run-rate, 340 vendors, 2,840 W-2. **That scale is not in `company.json`.** Volume files exist so a later plant can hide. `holdout/round2_hooks.json` says do not plant the slow-theft story in this round.

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

Phase A (this pack): densify Maximor, keep plot IDs, add vendor-master bank fields, trailing registers, documents, export layer.

Phase B (not done): plant the adversarial catalog starting with `SL-ADV-RESIDUAL` / `ADV-CASH-014` as the true $12.40 explanation. Hidden findings only under `expected_results.json` → `adversarial_holdout` (that key is **absent** today). No `fraud` labels on operational rows.

`holdout/round2_hooks.json` lists stable ID prefixes, do-not-retarget IDs, and unlabeled near-duplicate vendor pairs (`VEND-003`/`VEND-030`, `VEND-005`/`VEND-031`, `VEND-015`/`VEND-032`). Operational Bots must not load that file.

## Counts from `manifest.json`

```text
ap_invoices 110
purchase_orders 93
goods_receipts 91
ar_customers 15
ar_invoices 66
ar_payments 8
vendor_payments 6
bank_transactions 200
ledger_entries 200
stripe_payouts 3
journal_entries 3153
prepaids 2
fixed_assets 1
accruals 2
close_tasks 8
audit_invoices 110
forecast_weeks 13
reporting_lines 25
scenarios 94
memory_events 5
ingestion_emails 10
inbox_messages 17
documents 385
historical_ap 2640
bank_history 748
payroll_register 1248
processor_transactions 3000
vendors 52
workpapers 8
```

## Website

Load `demo_snapshot.json` for a company graph. Compose from operational JSON plus `lineage.json` / `timeline.json`. Scenario cards: `final-demo/scenarios.json`. Do not feed `expected_results.json` to a page that Bots or judges can confuse with company state.
