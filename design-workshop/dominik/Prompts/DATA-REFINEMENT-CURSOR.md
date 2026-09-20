# Cursor agent prompt — Maximor demo-world data refinement

Paste this as the **first message** of a new Cursor agent session in repo `hackmit26`. Do not start until the operator attaches this file. You own **data quality and company-scale simulated records**. You do not own Harness wiring, Pi runtime, or Operator UI.

---

## Who you are

You rebuild the simulated company so a judge can believe a **$300–450 million** software/services business existed **before** any agentic CFO program was installed. Agents onboard onto books, a bank, a vendor master, an AR subledger, payroll, and a processor that already have history. They discover. They do not invent a company from a 29-row JSON toy.

There is **no live Stripe, Gmail, bank feed, Xero, NetSuite, or Coupa**. Every connector is a file on disk. If a number cannot be justified from those files, it does not exist.

A later round (not this first pass) will inject **adversarial** traces: slow theft, duplicate vendors that almost match, money-in ≠ money-out over quarters. Your job now is to make the **preexisting register** so real that those traces can be planted as minute differences in books, invoices, and bank lines — not as labeled `HUMAN_REVIEW` flags.

## Company (do not replace)

- Legal name: **Maximor Demo Corp** (`CO-MAXIMOR`)
- Periods: August 2026 closed; September 2026 is the open close (starts blocked); October 2026 is a thin future tail
- Currency: USD
- Canonical pack path: `.cfo/data/demo/**`
- Operational Computer currently symlinks `.cfo-v2/office/computer/data` → `.cfo/data` (split brain). Your world must become **one picture**. Prefer making `data/demo` the truth and documenting how the office should point at it. Do not leave two competing invoice files.

Plot IDs that must survive (same identity everywhere: AP, cash, GL, close, audit, forecast):

- `INV-001` / PO-101 / GR-101 — clean three-way (STORY-CLEAN)
- `INV-017` — Helios wire, fee-netted $25 (STORY-RESOLVED)
- `INV-AR-013` / `PAY-006` / `TXN-2026-09-015` — unexplained **$12.40**, close blocker (STORY-UNRESOLVED)
- Duplicate vendor, round-number payment, post-close JE, Quiet Harbor late pay, GM 64% → 61% from source transactions

Do **not** swap the company for APEX’s law firm, Invoice Sandbox’s Aster North, or DABstep merchants as the legal entity. Those are **overlays and quality bars**.

## Why the current pack is rejected

Counted 2026-09-19:

- Live office reads `.cfo/data`: 20 invoices, 4 one-sentence emails
- Canonical `data/demo`: 29 invoices, 6 emails whose “PDF” text is 32–71 characters (`INVOICE ACM-2026-4410 / Amount: 12450.00`)
- Documented but **missing**: `lineage.json`, `timeline.json`, `demo_queries.json`, `agent_cases.json`, `expected_outcomes.json`, `system_capabilities.json`, `demo_snapshot.json`, `memory_events.json`
- Stripe sim under `data/simulations/stripe` is the only local pack with intensity (23 scenarios, 114 events). Keep it. Do not shrink it to 3 payouts.
- Inbox fixtures: 17 specs in `.cfo/inbox/fixtures.py` `full_inbox_specs()`. Seed currently uses 2. Upgrade **bodies and attachments**, keep trap types.
- `expected_results.json` is a hidden answer key. Operational agents must never load it. Do not put `HUMAN_REVIEW` in Bot-facing documents. Statuses: `EXCEPTION_OPEN`, `CLOSE_BLOCKED`, `UNEXPLAINED_DIFFERENCE`.
- Kernel eval 97% scores Python on planted JSON. You are not chasing that score. You are making documents and books that a human would not call slop.

## Inputs you must actually open

Read before you write:

1. `design-workshop/dominik/Maximor-HackMIT-Track.md` — example processes (starting point only)
2. `.cfo-v2/office/DEMO-DESIGN.md` — world target sizes and honesty rules
3. `docs/demo-data.md` and `docs/demo-capability-gaps.md` — do not fake NOT_IMPLEMENTED capabilities
4. `.cfo/sample_data/` — generator. Prefer extending the generator over hand-editing 80 JSON files
5. `.cfo/inbox/fixtures.py` — inbound mail traps
6. `.cfo/data/simulations/stripe/**`
7. `.cfo-v2/office/sessions/BENCHMARK-IMPORT.md` and `.cfo-v2/office/reference-datasets/` (already imported 2026-09-20, gitignored):
   - `invoice-sandbox-benchmark/gold_master/invoices/` — **112 PDFs**. CRM + deposits. **Document quality bar.** Hide `answer_key/` from anything agents read.
   - `apex-accounting/world/` — **90 files** (QBO xlsx, vendor PDFs, workpapers). **Close density bar.** Do not become a law firm.
   - `dabstep/data/context/payments.csv` — **138,236** txs; `fees.json` 1000 schemes. Sample 2–5k as **processor volume** behind Maximor Stripe/Adyen. Do not import 450 Q&A as the product.
   - `recbench/small/csv/` — **73,955** payouts, **75,138** bank lines, plus labels/truth. Overlay **difficulty types** onto ~200 Maximor bank lines. Keep `truth_*` out of Bot-readable paths.
   - `finance-agent-benchmark/` — **do not load**. Equity research.

Do not commit that cache. Do not pull RecBench ledger.csv (1M rows) or DABstep submissions.

## What “preexisting books” means

A real company of this size already has, **before onboarding**:

- Chart of accounts + dimensions
- Fiscal calendar; August locked; September open
- Vendor master (legal name, tax ID, bank, terms, aliases, duplicate-risk keys)
- Customer master
- Open POs, receipts, AP bills, AR invoices
- GL detail for the trailing 12 months (not 19 journal lines)
- Bank statements for operating + at least one other account
- Payroll register
- Processor payout history (Stripe sim + DABstep sample)
- Policy + approval matrix + materiality
- Prepaid and fixed-asset registers
- Prior-period close pack (August) that September can compare against

Agents **discover** these into their own working set. You provide the source registers as files that look like exports (CSV/JSON/text-PDF), not four-line stubs.

Scale targets (still one company, still pageable by Pi):

| Object | Floor | Notes |
| --- | --- | --- |
| AP invoices (open + recent) | ~110 | Invoice-Sandbox line-item density; keep INV-* plot IDs |
| Historical AP (trailing 12 months) | thousands of lines in a register file | Not all need live three-way; they need to exist for audit sampling |
| Inbox messages | all 17 fixtures, real bodies | Plus traps: quote, statement, injection, duplicate scan, remittance |
| GL / journal | multi-thousand lines across 12 months | Balanced. Identity links to INV/PAY/TXN |
| Bank lines | ~200 for September show + history file | RecBench-style fee, duplicate, unbundle, degraded ref |
| Stripe/processor | existing 23-scenario pack + 2–5k sampled txs | Mapped onto Maximor customers, not random merchants as a second company |
| AR | aging in every bucket | Quiet Harbor late remains |
| Close tasks | 8, final blocked | APEX-style workpaper text sitting next to JSON |
| Vendor master | dozens | Include near-duplicate legal names for later adversarial use **without labeling them as fraud** |

Do not generate 1M RecBench ledger rows into the office. Do not generate 100M. Sample.

## Quality bar (fail if any of these are true)

- Invoice “PDF” text under ~400 characters with no line items, addresses, tax, or terms
- Email body is one sentence that restates the JSON fields
- A finding is named in the operational file (`this is the fraud`, `HUMAN_REVIEW`, `planted`)
- Two files disagree on the same ID’s amount, date, or counterparty
- Books for August do not exist, so September close has nothing to compare
- Vendor bank accounts, tax IDs, and aliases are missing (needed for later detective work)
- You invent a live API
- You load `expected_results.json` into a path Email/AP/Audit Bots read
- You replace Maximor with another benchmark’s company

Good documents look like Invoice Sandbox / APEX: letterhead, line items, tax, payment instructions, packing lists, workpapers that an accountant would open.

## Generator, not one-off JSON soup

Extend `.cfo/sample_data/` (registry, writers, orchestrator). Deterministic seed **42** unless you document a new seed.

Keep:

```bash
python main.py generate-sample-data --seed 42 --month 2026-09 --output data/demo
python main.py validate-sample-data --data-root data/demo
```

Generate the missing export layer the docs already promise:

```bash
python main.py export-demo --output data/demo --seed 42 --month 2026-09
```

`lineage.json`, `timeline.json`, `demo_queries.json`, `demo_snapshot.json`, `memory_events.json` must exist when you are done.

The adversarial catalog **already exists**. Do not invent a second fraud plot.

- Human: `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` (109 scenarios, 12 storylines, 30 stealth-5)
- Index: `.cfo-v2/office/sessions/adversarial-scenarios.index.json`
- Bots must never load either file.

**Phase A (first):** densify Maximor to the scale table in that markdown (~$372M run-rate, 340 vendors, 12 months of books). Keep surviving plot IDs. Make vendor-master / payroll / bank / GL fields exist so a siphon can hide. A 29-invoice toy cannot hide this catalog.

**Phase B is a separate session.** Do not plant from this prompt. Use `design-workshop/dominik/Prompts/ADVERSARIAL-PLANT-CURSOR.md` with the catalog attached. This file is Phase A history.

## Capabilities you must not fake

From `docs/demo-capability-gaps.md`: do not invent AP self-improvement, vendor bank-change **control engine**, live Stripe, or ERP write-back. You **may** put vendor bank fields and historical change dates in the master so a later control can exist. Planting a “finding” with no engine is fake.

## Simulated mailbox (do not break this)

Kernel inbox lives in `.cfo/inbox/`. A Harness Bot `world` (Counterparty Message Agent) role-plays vendors/customers/banks. Email lands and classifies. Your fixtures and vendor/customer masters are what World speaks as.

- Upgrade `fixtures.py` bodies and attachments to the same document bar
- Keep trap classes (injection, quote, incomplete, duplicate, remittance)
- Counterparties need a voice, an address, and attachments that match the vendor master
- Outbound dunning / missing-info requests must be answerable from the register (invoice number exists, or it genuinely does not)

## Future demo (do not build the script)

Later, the office will simulate on the order of **two hours** of LM-speed activity. Data must support many concurrent threads: inbox traps, pay run, Stripe waterfall, unexplained cash, close block, audit sampling, forecast miss — **the same IDs**. If you cannot say which file a Bot would open for each of those, you under-built.

## Honesty

- `HUMAN_REVIEW` is not a Bot status. Verifier Bots own fail-closed.
- Do not tell anyone Kernel 97% is the office score.
- Simulated only.
- Do not commit unless the operator asks.
- Do not edit `Operator-workspace/`.
- Leave port 8792 alone.
- `reference-datasets/` stays gitignored.

## Done when

1. `data/demo` validates.
2. Documents look like invoices and workpapers, not field dumps.
3. August books exist. September close can be blocked on a real unexplained difference.
4. Export files the docs name actually exist.
5. Stripe sim pack is still the processor plot, with optional DABstep volume behind it.
6. You wrote a short `DATA-REFINEMENT-NOTES.md` in `.cfo-v2/office/sessions/` listing files changed, record counts before/after, which benchmark files you sampled, and where round-2 adversarial hooks live.
7. Phase A only: dense preexisting books and hooks. Do not plant the catalog here. Phase B is `ADVERSARIAL-PLANT-CURSOR.md`.
