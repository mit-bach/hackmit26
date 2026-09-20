# HackMIT 26 — Office of the CFO

This directory is the Obsidian vault. Python, skills, run artifacts, and Harness live in hidden folders so Obsidian does not index them.

| Open in Obsidian | Hidden from Obsidian (still in git) |
| --- | --- |
| `docs/` | `.cfo/` — finance kernel, agents, skills, tests, data, runs |
| `design-workshop/` | `.harness/` — Harness v1 / v2 |
| `Operator-workspace/` | |
| this README | |

Layout details: [`docs/LAYOUT.md`](docs/LAYOUT.md).

Architecture: [`docs/AGENTIC_SYSTEM_WORKFLOW.md`](docs/AGENTIC_SYSTEM_WORKFLOW.md).

## Python kernel

The engine README is [`.cfo/README.md`](.cfo/README.md). Copy [`.cfo/.env.example`](.cfo/.env.example) to `.cfo/.env`.

From this repo root, the old commands still work (shims enter `.cfo/`):

```bash
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
python main.py INV-001
python main.py demo-inbox
python main.py skills
pytest
```

## Harness

```bash
cd .harness/Harness-v2
npm install
npm test
```

## Demo website (HackMIT judges)

The operations dashboard is a thin UI over the existing Maximor kernel. It does not invent a second set of books.

```bash
# Backend API (binds a writable copy of data/demo → runs/demo_runtime)
python3 -m venv .cfo/.venv
source .cfo/.venv/bin/activate
pip install -r requirements.txt
python demo_web.py --host 127.0.0.1 --port 8765
```

```bash
# Frontend
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to the API on port 8765.

Vercel hosts the Vite app in `web/` (`vercel.json`). It is not a Python serverless function; ignore the root `main.py` CLI shim. Live agent runs still need the FastAPI process. Without it, the site uses saved demonstration results.

Production-style (API serves `web/dist`):

```bash
cd web && npm install && npm run build
source .cfo/.venv/bin/activate
python demo_web.py
# open http://127.0.0.1:8765
```

### Environment

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional. Kernel deterministic paths run the live demo without it. |
| `DEMO_LIVE_LLM=1` | Only if a key is set: use live agent turns for AP. Default is kernel-deterministic. |
| `STRIPE_MODE` | `mock` (default, simulated Stripe fixtures) or `live`. |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Live Stripe only. Never required for the demo website. |

Copy `.cfo/.env.example` to `.cfo/.env` if you use a key. Do not commit `.env`.

### Sample data and reset

Canonical pack: `.cfo/data/demo/` (Maximor Demo Corp, September 2026).  
Writable workspace: `.cfo/runs/demo_runtime/` (created on API start).

```bash
python main.py reset-demo --dest runs/demo_runtime
# or the Reset Demo button / POST /api/demo/reset
```

Reset copies the pack and clears website run logs. It never writes back to `data/demo`.

### Marquee demos

| UI | Backend |
| --- | --- |
| Inbox → messy / quote / statement | `POST /api/workflows/invoice-ingestion` |
| AP → INV-001 / INV-006 | `decide_ap` / AP policy |
| Stripe page | `integrations.cash.reconcile_payout` + cash recon |
| Cash page | `run_cash_reconciliation` |
| Close / Harbor | `run_month_end` / `run_accrual_workflow` |
| Memory | `memory.scenarios.run_harbor_cross_period` |
| Forecast | `reporting.forecast.build_forecast` |
| Audit | `audit.workflow.run_audit` |
| Full CFO Cycle | `cfo.scenario.run_cfo_scenario` |
| Evaluations | `evals.agent_cases.run_agent_cases` |

### Tests

```bash
source .cfo/.venv/bin/activate
pytest
pytest tests/test_demo_web_api.py tests/test_demo_web_consistency.py
cd web && npm test
```

### Stripe modes

The website labels **simulated** vs **live**. Default is simulated fixtures under `data/demo/integrations/stripe/`. Live Stripe is optional and is never implied when fixtures are in use.

### Known limitations

- Demo books are JSON, not a production ERP.
- Live Pi / Harness Handle completion is separate from this website; the UI calls the Kernel.
- Organizational memory writes when those workflows run; AP `prior_cases` remain a seed file.
- Close September remains BLOCKED on `$12.40` until the cash exception is resolved — that is the intended story.

## HackMIT Demo Script

About four minutes. Do not skip Reset if a previous run dirtied the workspace.

1. **Overview** — cash, AP/AR, 13-week ending cash, `$12.40` unexplained, close BLOCKED, 15 bots. Read the briefing: September cannot close until TXN-2026-09-015 is explained.
2. **Demo Scenarios → Messy Invoice** — run MSG-E-MESSY. Then run Duplicate (INV-006) and show HOLD + duplicate flag. Open AP on INV-001: same $12,450 in PO, GR, PAY-AP-001, TXN-2026-09-018A, JE-AP-INV-001.
3. **Stripe Reconciliation** — run it. Walk gross − refunds − chargebacks − fees = net = bank deposit. Badge says simulated Stripe.
4. **Memory** — run Harbor Electric. August seasonal methodology is retrieved for September; decision IDs are shown, not chat logs.
5. **Audit** — run audit. Findings come from the independent auditor over the same IDs (duplicate vendor/invoice, round-number, self-approval, post-close JE).
6. **Full CFO Cycle** — from Scenarios. Watch grain-bot stages. Close stays honest about the cash blocker unless the cycle resolves it.
7. **Evaluations** — run agent cases. Pass/fail is scored by the existing harness, not by the frontend.

Optional if time: Cash page on TXN-2026-09-015; Forecast week drill-down to INV-AR-014.
