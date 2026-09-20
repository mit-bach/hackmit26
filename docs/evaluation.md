# Maximor Finance Gauntlet

The gauntlet measures the **same production agents and workflows** shown in the Maximor demo. It is not a parallel toy benchmark and it does not implement AccountingBench, APEX, DABstep, BenchRec, or Invoice Sandbox. Those projects inspired the test families.

Run it from the Kernel tree:

```bash
python main.py eval-gauntlet
python main.py eval-gauntlet --modes
python -m pytest .cfo/tests/test_maximor_finance_gauntlet.py
```

The demo Evaluation Lab (`/evaluations`) calls `POST /api/workflows/gauntlet` against that same runner.

## What it tests

| Family | Inspired by | What Maximor must do |
| --- | --- | --- |
| Document traps | [Invoice Sandbox Benchmark](https://github.com/ciru-ai/invoice-sandbox-benchmark) | Classify messy invoices, voids, quotes, statements, Stripe payouts, credit memos, and revisions without creating a false payable |
| Cash reconciliation | [BenchRec](https://www.kaggle.com/datasets/benchmarkteam/benchrec-real-world-cash-reconciliation-dataset) | Match bank lines to ledger rows only when economic evidence supports the relationship |
| Anti-reward-hacking | AccountingBench failure mode | Reject same-dollar, wrong-entity, and historical-journal distractors |
| Multi-step questions | [DABstep](https://huggingface.co/datasets/adyen/DABstep) | Combine AP, Stripe, bank, and aging records into a deterministic answer |
| Rubric-graded close tasks | [APEX-Accounting](https://huggingface.co/datasets/mercor/apex-accounting), [Finance Agent Benchmark](https://huggingface.co/datasets/vals-ai/finance_agent_benchmark) | Score prepaid close on several criteria, not one final number |
| Cross-workflow consistency | Maximor differentiator | A duplicate bill must not enter payment, forecast, close, or spend |
| Long-horizon / memory | [AccountingBench](https://accounting.penrose.com/) | August Harbor Electric treatment still matters in September and October |
| Recovery | operational robustness | Malformed JSON/CSV, duplicate events, and missing Stripe metadata must not invent books |

## Fixture isolation

```
.cfo/evals/maximor_finance_gauntlet/
  fixtures/           # agent-visible documents and questions
  private_answers/    # grader-only gold
  graders live in runner.py, imported only inside evaluation_phase()
```

Operational code is blocked from reading `private_answers` and `gold.json` by `evaluation/isolation.py`. Fixtures never include expected classifications, journal amounts, or reconciliation maps. Tests fail if an operational module imports grader answers without an evaluation-phase guard.

## Metrics

- **Document correctness** — trap classification, payable flag, and supersession
- **Reconciliation correctness** — match type and economic linkage, not amount-only ties
- **Accounting-task rubric score** — share of prepaid-close criteria met
- **Multi-step QA accuracy** — exact IDs/amounts/portions against hidden gold
- **Cross-workflow consistency rate** — every relevant workflow agrees on the same bill
- **Memory correctness** — precedent used when memory is on, unused when it is off
- **Long-horizon accuracy, by period** — August/September, September contamination, October correction
- **Error propagation rate** — whether a poisoned August amount is copied into September
- **Unsupported assertion rate** — anti-hack cases that still forced a match
- **Recovery rate** — recoverable faults that still reach a correct fail-closed state

## Long-horizon simulation

Harbor Electric is the connected multi-period story already in the product:

1. **August** — service consumed, bill missing, accrual booked and written to DecisionMemory
2. **September** — still no bill; memory is retrieved as precedent, not as an override of Python evidence
3. **October** — actual invoice arrives; the open accrual is reversed and the history is kept
4. **Contamination** — a wrong August amount is injected; September must not blindly copy $50,000

Memory is precedent. Current evidence wins when it contradicts an earlier estimate.

## Baselines

`python main.py eval-gauntlet --modes` runs real configuration switches:

| Mode | Configuration | Latest core pack |
| --- | --- | --- |
| A / D | Memory on, shared canonical state on | 42/42 |
| B | Memory disabled | 42/42 |
| C | Shared canonical state reduced | 41/42 |

Measured comparison (core gauntlet, existing invoice/agent packs excluded):

- Memory on vs off: memory correctness 100% vs 100%; long-horizon 100% vs 100%
- Shared state on vs off: cross-workflow consistency **100% vs 50%**
- Error propagation rate: **0%** (the poisoned August amount was not copied)
- Unsupported assertion rate: **0%**

Memory off did **not** reduce Harbor Electric numerical accuracy on this pack. Python still selects the accrual amount from historical invoices; DecisionMemory records and retrieves the method rather than replacing the math. That is a real result, not a restated claim. Shared canonical state **did** change the score: with it reduced, a duplicate invoice is no longer guaranteed to stay out of every downstream workflow view.

## How to add a test

1. Put agent-visible inputs in `fixtures/` (no answers).
2. Put expected outcomes in `private_answers/`.
3. Grade through a production function (`analyze_document`, `run_cash_reconciliation`, `answer_finance_question`, `event_consistency`, Harbor scenarios, `cfo.recovery`).
4. Do not add fixture IDs to prompts, skills, or workflow branches.
5. If the product is wrong, fix the agent, skill, or Python fact layer, then rerun.

## Answer leakage

- Graders import `private_answers` only inside `evaluation_phase()`
- `operational_phase_guard()` blocks those paths during workflow execution
- Demo `GET /api/gauntlet` hides `expected` until a scored run exists in the demo website directory
- Skills teach procedures. They do not name trap IDs or gold amounts

## Current measured results

Core Finance Gauntlet (production workflows, no existing 24-case overlay):

| Family | Score |
| --- | --- |
| Document traps | 14/14 |
| Cash reconciliation | 4/4 |
| Anti-hack | 3/3 |
| Multi-step questions | 9/9 |
| Prepaid rubric | 1/1 |
| Cross-workflow consistency | 2/2 |
| Long horizon | 3/3 |
| Memory | 1/1 |
| Recovery | 5/5 |
| **Total** | **42/42** |

By period: August/September 100%, September contamination contained 100%, October self-correction 100%.

## Attribution

Inspired by, not implementations of:

- [AccountingBench](https://accounting.penrose.com/) ([original thread](https://x.com/yunyu_l/status/1946261507723173935))
- [APEX-Accounting](https://huggingface.co/datasets/mercor/apex-accounting)
- [Finance Agent Benchmark](https://huggingface.co/datasets/vals-ai/finance_agent_benchmark)
- [DABstep](https://huggingface.co/datasets/adyen/DABstep)
- [BenchRec](https://www.kaggle.com/datasets/benchmarkteam/benchrec-real-world-cash-reconciliation-dataset)
- [Invoice Sandbox Benchmark](https://github.com/ciru-ai/invoice-sandbox-benchmark)
