# Data refinement notes — Maximor Demo Corp

Simulated only. Seed **42**. Period **2026-09** open (starts blocked). August **2026-08** closed. Company **Maximor Demo Corp** (`CO-MAXIMOR`). No commit in this pass.

Canonical pack: `.cfo-v2/office/world/maximor/**`. Regenerated with:

```bash
cd .cfo
.venv/bin/python main.py generate-sample-data --seed 42 --month 2026-09
.venv/bin/python main.py validate-sample-data
.venv/bin/python main.py validate-demo
```

Default `--output` / `--data-root` is the office world, not `.cfo/data/demo`. The Kernel generator still lives under `.cfo/`; the files the office uses do not.

## One picture (office pointing)

Computer `data/` is **not** `.cfo/data`. Bind:

```bash
ln -sfn ../world/maximor .cfo-v2/office/computer/data
```

Kernel `DATA_DIR` is then the company pack at the Computer data root (`invoices.json` is the 110-invoice Maximor set). Stripe is `data/simulations/stripe`. Inbox fixtures are `data/inbox/messages.json`.

`.cfo/data/invoices.json` is a Kernel unit-test fixture (20 rows). Do not mount it. `.cfo/data/demo` is leftover Kernel output and is not what 8800 should load.

`reference-datasets/` stays gitignored. Harness `seed_demo.py` still seeds 2 inbox messages unless someone switches it to `full_inbox_specs()`.

## Record counts (2026-09-19 → 2026-09-20)

| Object | Before (canonical `data/demo`) | After |
| --- | --- | --- |
| Legal entity | Maximor Demo Corp | unchanged |
| AP invoices (live) | 29 | **110** |
| Historical AP register | missing | **2,640** (`registers/ap_history.csv`) |
| Invoice/PO/GR/packing documents | stub 32–71 chars | **385** letterhead texts, INV-001 = 1,379 chars |
| Inbox fixtures on disk | 6 stub emails | **10** ingestion emails + **17** `inbox/messages.json` |
| Vendors | ~21 | **52** (legal name, tax ID, bank, aliases, `duplicate_risk_key`) |
| Customers | 10 | **15** (billing address, tax ID) |
| AR invoices | plot set | **66** (aging in every bucket; Quiet Harbor late remains) |
| September bank lines | 19 | **200** |
| Bank history | missing | **748** (`registers/bank_history.csv`) |
| Journal / GL | 47 | **3,153** (`registers/gl_detail.csv`) |
| Close tasks | 8, final blocked | **8**, TASK-CASH / TASK-BS / TASK-FINAL blocked on **$12.40** |
| August close pack | missing | `close/prior_period/2026-08/` + 4 workpapers |
| September workpapers | missing | 4 APEX-style text files under `close/2026-09/` |
| Payroll register | missing | **1,248** rows (48 employees × biweekly from 2025-10) |
| Processor txs | 3 Stripe payouts only | **3,000** DABstep-shaped rows + original 3 payouts |
| Stripe sim pack | 23 scenarios | **untouched** (`data/simulations/stripe`) |
| Forecast weeks | 13 | 13 |
| Export layer | documented, missing | lineage, timeline, demo_queries, demo_snapshot, memory_events, agent_cases, expected_outcomes, system_capabilities |
| Schema | `2026.09-cfo-sample-1` | `2026.09-cfo-sample-2` |

Live office counts from 2026-09-19 (20 invoices / 4 emails / 12 bank lines) were the Computer reading `.cfo/data`, not `data/demo`.

## Plot identities (unchanged amounts)

| ID | Fact |
| --- | --- |
| INV-001 / PO-101 / GR-101 | $12,450.00 clean three-way (STORY-CLEAN) |
| INV-017 | Helios $10,000.00; bank TXN-2026-09-011 fee-netted $25 (STORY-RESOLVED) |
| INV-AR-013 / PAY-006 / TXN-2026-09-015 / GL-AR-NS | unexplained **$12.40**, close blocker (STORY-UNRESOLVED) |
| VEND-001 / VEND-001-DUP | duplicate vendor (audit rediscovers) |
| PAY-AP-009 | round-number $50,000 |
| JE-POST-CLOSE-001 | post-close journal |
| Quiet Harbor | still 90+ aging |
| GM | 64% → 61% from source COGS txs (Aug $360k / Sep $390k on $1,000,000 revenue) |

September volume bank lines are exact MATCHED pairs on non-plot counterparties so they cannot steal Helios grouped/fee matching. RecBench difficulty types live in **descriptions** (`degraded_ref`, `unbundle_leg`, `fee_inclusive`), not as extra unexplained differences.

## P&L scale (honest)

Validators and tests lock August/September board pack at **$1,000,000 revenue**, **$360,000 / $390,000 COGS**. This pass does **not** rescale ARR to $300–450 million. Company scale is register density (AP, GL, bank, payroll, processor) so a later $2,400/month siphon or 0.08% fee skim can hide. Trailing months sit on GL with categories `volume_revenue` / `volume_cogs` / `volume_opex` so they do not move GM.

## Benchmarks sampled (cache not committed)

Local cache: `.cfo-v2/office/reference-datasets/` (gitignored). Presence recorded in `data/demo/registers/reference_sample_note.json`.

| Source | What we took | What we did not |
| --- | --- | --- |
| Invoice Sandbox (`gold_master/invoices`, 112 PDFs) | Letterhead / line items / Tax ID / remittance / `Invoice Number` + `Amount Due` + `PO Number` labels | Did not copy PDFs or `answer_key/` |
| APEX-Accounting (`world/`, 90 files) | Workpaper voice and August/September tie files | Did not become a law firm |
| DABstep `payments.csv` (138,236) | Column layout + **3,000** synthetic txs mapped onto Maximor customers | Did not import 138k rows or 450 Q&A |
| RecBench small labels/payouts/bank | Difficulty types overlaid on ~181 volume September lines | Did not load `truth_*` into Bot paths; did not pull 1M `ledger.csv` |
| Finance Agent Benchmark | **Not loaded** | Equity research |

## Round-2 adversarial hooks (not planted)

Private file: `data/demo/holdout/round2_hooks.json` (same privacy class as `expected_results.json`). Operational Email/AP/Audit Bots must not load it.

Hooks:

- Stable IDs: `INV-`, `HAP-`, `TXN-` / `TXN-VOL-` / `TXN-HIST-`, `JE-`, `VEND-`, `GL-` / `GL-VOL-`, `CUST-`, `EMP-`.
- Scenario registry still `canonical/scenarios.json` — add rows, do not rewrite the company.
- Vendor near-duplicates **without fraud labels**: VEND-030 Northline Fab Group, VEND-031 Helios Hardware Supply, VEND-032 Harbor Power & Light (different tax ID and bank from the plot vendors).
- Vendor master fields for a later bank-change **control**: `bank_routing`, `bank_account`, `bank_changed_on`, `aliases`, `duplicate_risk_key`. The control engine is still `NOT_IMPLEMENTED` (`docs/demo-capability-gaps.md`). Fields exist; no planted “finding.”
- Dense AP/GL/bank/processor history so a slow siphon is not obvious on 19 lines.

Do **not** wait for `ADVERSARIAL-SCENARIOS.md`. Plant into these registers.

## Files changed (generator)

- `.cfo/sample_data/documents.py` — letterhead invoice/quote/PO/GR/statement/workpaper renderers; plot line items that sum to plot amounts.
- `.cfo/sample_data/world.py` — vendor/customer enrichment, ≥110 live AP, historical AP, trailing GL, 200 September bank lines, bank history, payroll, 3,000 processor txs, fiscal calendar, August pack, round-2 hooks.
- `.cfo/sample_data/context.py`, `writers.py`, `validators.py`, `orchestrator.py`, `report.py`, `ids.py`, `schema_map.py`.
- `.cfo/sample_data/agents/reporting_forecasting.py` — board pack stays Aug/Sep P&L categories only.
- `.cfo/ar/models.py` — optional customer legal/billing/tax fields.
- `.cfo/inbox/fixtures.py` — all 17 trap specs, real bodies/attachments; trap keywords kept (quote, statement, remittance, injection, incomplete, duplicate, unknown vendor).
- `.cfo/demo/export.py` — EVT-031 status `EXCEPTION_OPEN`; snapshot exception statuses `UNEXPLAINED_DIFFERENCE` / `EXCEPTION_OPEN`.
- `.cfo/demo/cli.py` already had export/validate/reset; `.cfo/main.py` now exposes them.
- `.cfo/tests/test_sample_data.py` — scale floors + export files; historical COGS sources allowed as `INV-COGS-HIST-*`.

Bot-facing documents under `data/demo/documents/**` contain no `HUMAN_REVIEW`, `this is the fraud`, or `planted`. Engine answer keys still use `HUMAN_REVIEW` where Python workflows emit it (`expected_results.json`, `cash_recon/ground_truth.json`, some `agent_cases.json` expected fields). That is the Kernel status, not a Bot lane status.

## Capabilities not faked

Still `NOT_IMPLEMENTED` / not invented: AP self-improvement, vendor bank-change **control engine**, live Stripe, ERP write-back. Demo Stripe payouts remain 3; the 23-scenario sim pack is a file connector.

## Checks run

- `validate-sample-data` PASS
- `validate-demo` PASS
- `pytest tests/test_sample_data.py tests/test_inbox_*.py tests/test_discrepancies.py` — 81 passed (sample + inbox + discrepancies)

Port 8792 not touched. `Operator-workspace/` not edited. `reference-datasets/` not committed. Slow-theft story not planted.
