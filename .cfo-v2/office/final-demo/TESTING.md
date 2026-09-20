# How we test

Three different proofs. Do not mix their numbers.

## 1. Kernel (Python)

The Maximor pack plants cases. Workflows run with `live=False` unless a key is set. Python owns amounts.

| Harness | Command (from `.cfo/`) | What it proves |
| --- | --- | --- |
| Sample-data validate | `python main.py validate-sample-data --data-root <world pack>` | Generator consistency |
| Demo validate | `python main.py validate-demo --data-root <world pack>` | Export layer + planted IDs |
| CFO eval | `python main.py evaluate-cfo --data-root <world pack> --all` | Agent cases vs hidden gold |
| Demo company eval | `python -m evals.demo_company` | Same pack, isolated `runs/demo_eval` |
| Agent cases | 26 `AC-*` in `world/maximor/agent_cases.json` | Per Display name, after workflows |
| Memory | `python main.py eval-memory` | Precedent on vs off |
| Gauntlet | `python main.py eval-gauntlet` and `--modes` | Document traps, cash rec, anti-hack, multi-step, rubric close, cross-workflow, long horizon, recovery |
| Inbox / World unit | `pytest .cfo/tests/test_inbox_*.py` | 44 passed with World compile (2026-09-20) |

Gauntlet gold lives under `.cfo/evals/maximor_finance_gauntlet/private_answers/`. Operational imports of grader answers without `evaluation_phase()` must fail.

Latest gauntlet core pack cited in `docs/evaluation.md`:

- Memory on, shared state on: 42/42
- Memory off: 42/42 (Harbor amount still comes from Python history, not from DecisionMemory)
- Shared state reduced: 41/42. Cross-workflow consistency 100% → 50% on a duplicate bill

That is **our** measure. Inspired by Invoice Sandbox, RecBench / BenchRec, APEX, DABstep, AccountingBench. It is not a claimed score on those public sets. It is not the office score.

## 2. Office (Pi on 8800)

Proof is a Handle that completes, a Kernel RPC Grant check, and Inspector Pi RPC. Fake `--fake` workers are protocol only.

| Check | Pass if |
| --- | --- |
| Health | `curl http://127.0.0.1:8800/health` — system `cfo-agentic-system`, fake workers off, sidecar owned |
| Roster | Fifteen grain slugs addressable. World if reattached |
| SoD | AP prepare cannot `create_accrual`. Email `triage` cannot `send_inbox_message`. World cannot `dispatch_inbox_action` |
| Close | September stays BLOCKED on `TXN-2026-09-015` $12.40 |
| Eval isolation | Operational Grants omit `get_audit_ground_truth` |

Compiler: `PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational`. Catalog on disk at last look: 89 ops, including inbox compose/send/classify.

## 3. Holdout (not scored on the public page yet)

Adversarial catalog: 109 scenarios, 12 storylines, 30 stealth-5. Design only. Not in the GL.

When Phase B plants:

1. Findings go in `expected_results.json` section `adversarial_holdout` only.
2. Operational rows have no `fraud` flag and no `unusual=true` as the tell.
3. Loud decoys stay. Stealth cases are the real test.
4. Website `/evaluations` may show expected vs observed **after** a scored holdout run. Not before.

## Isolation rules (aircraft-strict)

1. Do not load `expected_results.json` in an operational Bot or in a Kernel path that is not inside `evaluation_phase()`.
2. Do not load `holdout/round2_hooks.json` at runtime.
3. Do not load `sessions/ADVERSARIAL-SCENARIOS.md` or its index at runtime.
4. Do not load gauntlet `private_answers/` outside the grader.
5. Do not use `--resolve` on month-end as the office completion path. That flag is an emergency / eval fixture.
6. Do not delete `TXN-2026-09-015` to make close go green.

## What the website should show as “testing”

| Page | Source | Hide until scored |
| --- | --- | --- |
| `/evaluations` | Gauntlet + `evaluate-cfo` artifacts under isolated runs | Gold, private answers |
| `/scenarios` | `final-demo/scenarios.json` | `expected_behavior`, `expected_facts` |
| `/architecture` | `CAPABILITIES.md` + roster | Adversarial insider names |
| `/agents` | Roster + activity log | Nothing from answer keys |

Default website POST is Kernel deterministic. Live model turns only when requested and keyed. The UI must not invent traces.

## Judge prompts (public text)

These prompts are in the World pack. Gold facts stay in `demo_queries.json` / `expected_results.json`. The website may show the prompt. It must not show the gold block as company data.

| ID | Prompt |
| --- | --- |
| `Q-CAN-CLOSE` | Can we close the month? |
| `Q-CASH-RECON` | Reconcile September cash. |
| `Q-TRACE-INV-001` | Trace INV-001 through the entire system. |
| `Q-TRACE-INV-017` | Trace INV-017 through the entire system. |
| `Q-PAY-WEEK` | Which invoices should we pay this week? |
| `Q-AR-OVERDUE` | Show me our overdue receivables. |
| `Q-AR-APPLY` | Apply today's customer payments. |
| `Q-STRIPE` | Reconcile the latest Stripe payout. |
| `Q-CLOSE` | Run the September close. |
| `Q-BLOCKERS` | What's blocking close? |
| `Q-GM` | Why did gross margin fall from August to September? |
| `Q-FORECAST-MISS` | Why did we miss the cash forecast? |
| `Q-AUDIT` | Audit September and tell me what you found. |
| `Q-HISTORY` | Show me the history behind this exception. |
| `Q-LAST-MONTH` | Did we see anything like this last month? |
| `Q-CFO-RUN` | Run the Office of the CFO for September. |

Public correct shape for close: **no**, until `TXN-2026-09-015` is explained. Do not print the adversarial residual story on this page.
