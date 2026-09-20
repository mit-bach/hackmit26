# Demo website architecture

The HackMIT demonstration UI is a **read-and-invoke layer** over the existing Maximor Office of the CFO. It does not implement a second finance engine, a second invoice store, or hard-coded demo outcomes.

Canonical company: **Maximor Demo Corp** (`CO-MAXIMOR`), period **September 2026**, with August precedent and limited October follow-through. One identity and amount for each economic event across AP, AR, cash, Stripe, GL, close, forecast, audit, and memory.

## Existing components reused

| Layer | Path | Role |
| --- | --- | --- |
| Kernel workflows | `.cfo/` | AP policy / `run_ap_workflow`, ingestion, inbox, AR, cash recon, Stripe payout math, accruals, prepaids, assets, close, reporting, forecast, audit, memory, CFO scenario |
| Canonical pack | `.cfo/data/demo/` | Immutable Maximor books (`invoices.json`, AR, bank, Stripe, journals, close tasks, lineage, timeline, memory events, agent cases) |
| Demo runtime | `.cfo/runs/demo_runtime/` | Writable copy created by `demo.reset.reset_demo_runtime` |
| Data-root remap | `.cfo/sample_data/paths.py` | Points existing loaders at the runtime pack |
| Run isolation | `.cfo/evaluation/context.py` | Redirects AR / cash / close / audit / memory / reporting stores |
| 15 grain Bots | `.cfo-v2/office/computer/harness/roster.json` + `cfo/slug-map.json` | Current architecture. Display names are Profiles, not extra Bots |
| Skills | `.cfo/skills/README.md`, `assignments.py` | Single skill registry |
| Kernel sidecar | `.cfo/cfo_kernel/server.py` | Harness RPC only. The website does **not** replace it |
| Stripe | `.cfo/integrations/cash.py`, `integrations/providers/stripe.py`, `data/demo/integrations/stripe/` | Simulated payouts by default (`STRIPE_MODE=mock`) |

Do not load `expected_results.json` / `expected_outcomes.json` / `agent_cases.json` expected fields into operational workflow runners. The evaluations page may show expected vs observed **after** a scored run.

## Frontend routes

Served by Vite (`web/`) in development and by FastAPI static files in production.

| Route | Page |
| --- | --- |
| `/` | CFO command center |
| `/inbox` | Finance inbox / document ingestion |
| `/ap` | Accounts payable |
| `/ar` | Accounts receivable |
| `/cash` | Bank reconciliation |
| `/stripe` | Stripe payout reconciliation |
| `/close` | Month-end close |
| `/forecast` | 13-week cash forecast + variance |
| `/audit` | Audit & controls |
| `/memory` | Cross-period decision memory |
| `/agents` | 15-bot activity |
| `/evaluations` | Evaluation harness results |
| `/scenarios` | Demo scenario launcher |
| `/architecture` | System architecture |

## Backend endpoints

Package: `.cfo/demo_web/`. Thin FastAPI app (`python -m demo_web`).

Reads persisted Maximor files on GET. POST invokes Kernel workflows already in `.cfo/`.

| Method | Path | Data source / engine |
| --- | --- | --- |
| GET | `/api/health` | Sidecar-style status, Stripe mode, 15-bot roster |
| GET | `/api/demo/company` | `company.json`, calendar from `demo_snapshot.json` |
| GET | `/api/demo/overview` | Cash position, AP/AR files, close tasks, forecast weeks, timeline |
| GET | `/api/demo/status` | Bind paths, autonomy mode, Stripe mode |
| POST | `/api/demo/reset` | `reset_demo_runtime` — never writes `data/demo` |
| GET | `/api/inbox` | `ingestion/emails.json` + inbox fixtures + last ingest result |
| GET | `/api/invoices` | `tools.all_invoices` + evidence + payments + lineage |
| GET | `/api/invoices/{id}` | Same, plus PO/GR/GL/audit links |
| GET | `/api/ar` | AR invoices/payments + `ar.aging` math |
| GET | `/api/cash` | Bank/ledger files + last recon report if persisted |
| GET | `/api/stripe` | Stripe fixtures + `integrations.cash.reconcile_payout` |
| GET | `/api/close` | Close tasks, journals, prepaids, assets |
| GET | `/api/forecast` | `reporting/forecast_weeks.json` / live `build_forecast` after run |
| GET | `/api/audit` | Last audit run or planted population (no fabricated findings) |
| GET | `/api/memory` | `memory_events.json` + `memory.store` if written |
| GET | `/api/agents` | Roster + slug-map + activity log |
| GET | `/api/traces` | Website run log |
| GET | `/api/traces/{id}` | Persisted workflow result |
| GET | `/api/evaluations` | `runs/demo_eval/latest.json` if present; case catalog without answers until scored |
| GET | `/api/scenarios` | Scenario cards (setup only; planted answers hidden until run) |
| GET | `/api/lineage/{id}` | `lineage.json` + live records |
| GET | `/api/architecture` | Inventory + 15-bot grain |
| POST | `/api/workflows/*` | Existing Kernel entrypoints (see below) |

## Workflow POST → existing engines

| Website action | Kernel call |
| --- | --- |
| Invoice ingestion | `invoice_ingestion.interpret` + `ingest_candidates` / `ingest_invoices` |
| Inbox sample | `inbox.workflow.handoff` |
| Run AP | `close.orchestrator.decide_ap` (policy) or `workflow.run_ap_workflow` if live LLM |
| Payment schedule | `scheduling.workflow.run_schedule_workflow` or deterministic net |
| AR aging / collections / apply | `ar.workflow.run_aging`, `run_collections`, `run_cash_apply` |
| Bank reconciliation | `cash_recon.workflow.run_cash_reconciliation` |
| Stripe reconciliation | `integrations.cash.reconcile_payout` + cash recon (provider payouts) |
| Close | `close.month_end.run_month_end` |
| Accrual | `accrual.workflow.run_accrual_workflow` / `memory.scenarios.run_harbor_cross_period` |
| Forecast | `reporting.forecast.build_forecast` + `reporting.workflow.run_reporting_workflow` |
| Audit | `audit.workflow.run_audit` / `audit.demo.run_audit_demo` |
| Memory | `memory.scenarios` + `memory.eval.run_memory_evaluation` |
| Full CFO cycle | `cfo.scenario.run_cfo_scenario` |
| Evaluations | `evals.demo_company` / `evals.agent_cases` (scores after workflows; answer keys stay isolated) |

Default execution is the Kernel’s **deterministic** path (`live=False`, `use_llm=False`). That is still the real engine: Python owns amounts; grain Bots own lanes. Live OpenAI turns run only when `OPENAI_API_KEY` is set **and** the operator requests live mode. The UI never invents agent events.

## Source of each demo’s data

| Demo | Records |
| --- | --- |
| Messy / quote / statement / receipt / duplicate invoice | `data/demo/ingestion/emails.json`, inbox fixtures |
| Three-way match / AP table | `invoices.json`, `purchase_orders.json`, `goods_receipts.json` |
| Payment decision | `approved_pool.json`, `cash_position.json` |
| Stripe | `integrations/stripe/payouts.json`, `balance_transactions.json`, `bank_deposits.json` |
| Bank recon | `cash_recon/bank_statement.json`, `ledger.json`, `fee_evidence.json` |
| Close / accrual | `close/tasks.json`, Harbor Electric via accrual discovery + `memory_events.json` MEM-004 |
| Forecast / miss | `reporting/forecast_weeks.json`, `INV-AR-014`, `INV-012` |
| Audit | `data/demo/audit/*` populations; findings from `run_audit` |
| Memory | `memory_events.json`, `prior_cases.json`, `ar_precedents.json`, `runs/memory/decisions.json` after a memory workflow |

## Source of agent traces

- Kernel traces already written under isolated `runs/demo_runtime/runs/` (AP, cash, close, inbox, ingestion, audit, reporting).
- Website activity log: `runs/demo_runtime/runs/website/activity.jsonl`.
- Structured workflow payloads: `runs/demo_runtime/runs/website/results/`.
- Timeline seed: `data/demo/timeline.json` (same IDs as operational files).

Traces shown in the UI are structured (inputs, facts, policy, memory refs, tools, handoffs, resulting records). They do not dump model chain-of-thought.

## Source of decision memory

1. Seeded August precedents: `prior_cases.json` (CASE-001), `ar_precedents.json`, `memory_events.json`.
2. Organizational store: `memory.store` → `decisions.json` after cash / prepaid / Harbor / Stripe stories.
3. Close identity links: `close/identity_links.json` (provenance, not a graph database).

## Source of evaluation results

- Catalog: `data/demo/agent_cases.json` (IDs and domains only until scored).
- Live score: `python main.py evaluate-cfo` / `python -m evals.demo_company` → `runs/demo_eval/`.
- Memory ON vs OFF: `memory.eval`.
- Stripe three-mode: `simulations.stripe.modes`.
- Website `POST /api/workflows/evaluate` runs the existing harness against a copy of the pack and never mutates `data/demo`.

## New components introduced

| Component | Why it is new |
| --- | --- |
| `.cfo/demo_web/` | HTTP façade for judges; calls Kernel, does not reimplement it |
| `web/` | React + Vite operations shell (no prior frontend in the repo) |
| `docs/demo_website_architecture.md` | This note |
| `.cfo/tests/test_demo_web_*.py` | API, consistency, Stripe waterfall, planted cases, reset |

## Current agent architecture (post-migration)

Fifteen grain slugs only: `email`, `stripe`, `bank`, `books`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

The website must not call removed Display-name constructors as if they were standing Bots. Profiles remain visible as skills/handoffs on those fifteen identities.
