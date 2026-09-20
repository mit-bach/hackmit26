# Maximor Demo Corp — canonical demo data

One synthetic company, **Maximor Demo Corp** (`CO-MAXIMOR`), is the source of truth for every Office-of-the-CFO workflow. Agents do not get a second set of books.

## Company and periods

| Period | Role |
| --- | --- |
| August 2026 | Prior closed period. Precedent, P&L comparison, accrual history. |
| September 2026 | Main demo / test period. Close starts **BLOCKED**. |
| October 2026 | Limited future context: Harbor Electric / legal invoices arrive; forecast actuals. |

Currency is USD. Operational AP/AR amounts are float dollars (existing models). Cash, Stripe, and journals also carry integer cents.

## Canonical vs generated vs runtime

| Path | Role |
| --- | --- |
| `data/demo/**` | **Canonical** immutable pack. Regenerated only by `generate-sample-data` / `export-demo`. |
| `data/demo/expected_results.json` | Hidden answer key. Operational agents must never load it. |
| `data/demo/expected_outcomes.json`, `agent_cases.json` | Evaluation / visualization facts. Also blocked from operational reads. |
| `data/demo/system_capabilities.json` | Inventory of live agents, skills, workflows, tools. |
| `data/demo/demo_snapshot.json`, `lineage.json`, `timeline.json`, `demo_queries.json` | Frontend layer derived from the same records. |
| `runs/demo_runtime/` | Writable copy created by `reset-demo`. |
| `runs/demo_eval/` | Eval artifacts. `latest.json` is the newest run. |

Hand-written fixtures under `data/` (not `data/demo`) remain the default loaders for unit tests that do not apply a data-root.

## How to run

```bash
# Validate the canonical pack (dataset + export layer)
python main.py validate-sample-data --data-root data/demo
python main.py validate-demo --data-root data/demo

# Reset a writable workspace without touching data/demo
python main.py reset-demo --dest runs/demo_runtime

# Regenerate the canonical pack (deterministic, seed 42)
python main.py generate-sample-data --seed 42 --month 2026-09 --output data/demo

# Agent / workflow evals against the live engines
python main.py evaluate-cfo --data-root data/demo --seed 42 --all
python -m evals.demo_company
python main.py demo-eval
# 24 AC-* cases in data/demo/agent_cases.json run via evals/agent_cases.py

# Visualization / frontend export (same generator; writes lineage, timeline, snapshot)
python main.py export-demo --output data/demo --seed 42 --month 2026-09

# Interactive / narrative demo
python main.py cfo-demo
python main.py demo-close
python main.py ar-demo
python main.py reconcile-cash --month 2026-09 --seed-demo
```

## Seeded scenarios

See `data/demo/canonical/scenarios.json` and `sample_data/registry.py`. Every catalog ID is planted.

Highlights:

- **AP** clean three-way match (`INV-001`), quantity/price/receipt/duplicate/policy holds, payment horizon, Acme alias with August precedent (`INV-021` / `CASE-001`).
- **Ingestion** clean, messy, PO, quote, receipt, statement, marketing, inferable missing vendor, unsafe missing amount, duplicate copy.
- **AR** every aging bucket, exact / partial / batch / unlabeled / ambiguous / overpayment, Quiet Harbor chase.
- **Cash** exact match, three-invoice ACH, fee-netted wire, duplicate refund, **$12.40 unexplained**, timing, Stripe payouts.
- **Close** accruals, prepaids, Dell depreciation, BS recs, blocked final review, planted post-close journal.
- **Audit** duplicate vendor/invoice, round-number, self-approval, paid-while-held, reperformance samples.
- **Reporting / forecast** GM 64% → 61% from source transactions; 13-week roll-forward; late collection miss.
- **Memory** August vendor alias, Atlas batch payer, Stripe settlement pattern, Harbor Electric methodology, Meridian human correction.

## How scenarios connect

`INV-001` is the clean thread: email → AP approve → payment → bank `TXN-2026-09-018A` → close evidence → audit population.

`INV-017` is the resolved exception: Helios invoice → fee-netted wire `TXN-2026-09-011`.

`INV-AR-013` / `PAY-006` / `TXN-2026-09-015` is the unresolved thread: bank is $12.40 above ledger and **blocks September close**.

`INV-021` is the memory thread: August `CASE-001` makes the September Acme alias retrievable.

Lineage: `data/demo/lineage.json`. Timeline: `data/demo/timeline.json`.

## Demo highlights (show these)

1. **Can we close September?** No — `$12.40` on `TXN-2026-09-015`.
2. **Trace INV-001** across AP, cash, GL, close, and audit.
3. **Trace INV-017** as a fee-netted wire, not an exact match.
4. **INV-021 / CASE-001** — August precedent changes the September AP decision.
5. **PAY-004** — two Lumen invoices, one unlabeled $5,000 remittance → `HUMAN_REVIEW`.
6. **Gross margin** 64% → 61% from `TXN-SUP-SEP-001`, hosting, and freight — not a canned story.
7. **13-week forecast miss** — Quiet Harbor (`INV-AR-014`) pays late.
8. **Audit** independently rediscovers planted duplicates, round-number, self-approval, and the post-close journal.
9. **Stripe** payouts tie: charges − fees − refunds − disputes = bank deposit.
10. **Dell `INV-018`** is capitalized and depreciated on the same identity.

Curated judge prompts live in `data/demo/demo_queries.json`.

## Frontend consumption

Load `data/demo/demo_snapshot.json` for a normalized company graph (entities, relationships, timeline, memory, tags).

Or compose from:

- operational files (`invoices.json`, `ar_invoices.json`, `cash_recon/…`, `close/…`)
- `lineage.json` / `timeline.json` / `memory_events.json`
- tags on snapshot entities (`happy_path`, `exception`, `demo_highlight`, …)

Do not treat `expected_results.json` as a UI feed.

## Adding a scenario safely

1. Add a template to `sample_data/registry.py`.
2. Instantiate it in the owning sample-data agent **or** `sample_data/extended.py` if it only labels existing IDs.
3. Keep August/September revenue $1,000,000 and COGS $360k / $390k unless you also update `sample_data/pnl.py`.
4. Use stable IDs (`INV-…`, `TXN-2026-09-…`). No random UUIDs.
5. Put expected structured facts in the answer key / `agent_cases.json`, never inside agent prompts.
6. Run `python main.py generate-sample-data …` then `validate-demo` and `pytest tests/test_sample_data.py tests/test_demo_dataset.py`.
