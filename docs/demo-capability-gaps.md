# Demo capability gaps

The Maximor pack only tests behavior the repository actually implements. Gaps are recorded here instead of being faked in fixtures.

| Capability | Status | Current state | Why it cannot be fully tested | Files | Next step |
| --- | --- | --- | --- | --- | --- |
| AP self-improvement from new decisions | `NOT_IMPLEMENTED` | `prior_cases.json` is a static seed. `run_ap_workflow` does not append cases. | A second similar invoice cannot learn from a first-run correction unless a human edits the seed file. | `tools.py`, `data/prior_cases.json`, `workflow.py` | Persist APPROVE/HOLD traces into a writable prior-case store, then reload on the next invoice. |
| Vendor bank / payment-instruction change control | `NOT_IMPLEMENTED` | No vendor-master bank account, dual control, or wire-instruction diff. | There is no engine to flag “bank details changed.” Planting a finding would be fake. | (absent) | Add vendor payment-instrument records and a control comparable to `AUD-DUP-VEND-001`. |
| Close Manager live agent | `PARTIALLY_IMPLEMENTED` | `close_manager` exists with `month-end-close-coordination`. Production uses `deterministic_coordinate()`. | We can test coordination facts, not the unused SDK path, without an API key. | `close/agents.py`, `close/month_end.py` | Call `run_agent(close_manager, …)` when `live=True`. |
| AR overpayment / credit-memo lifecycle | `PARTIALLY_IMPLEMENTED` | Named overpay goes to `HUMAN_REVIEW`. No customer-credit subledger or refund cycle. | `PAY-007` tests detection, not settlement of the residual. | `ar/cash.py`, `ar/ledger.py` | Post unapplied cash / credit memo and expose it to forecast and close. |
| Accrual reversal lifecycle in close | `PARTIALLY_IMPLEMENTED` | `accrual/ledger.reconcile_accrual()` can reverse when the October bill arrives. Demo close does not auto-run that for every vendor. | October Harbor/legal invoices are planted (`later_invoices.json`) and can be reconciled via `accrue.py reconcile`. | `accrual/ledger.py`, `accrual/workflow.py` | Wire featured reconcile into the default September→October close path. |
| Stable planted accrual IDs | `PARTIALLY_IMPLEMENTED` | Discovery finds Harbor Electric. `create_accrual()` mints `ACC-{stamp}` instead of reusing `ACC-HE-2026-09`. | `AC-ACCRUAL` can prove need + planted JE identity, not that the live engine emits the demo ID. | `accrual/ledger.py` | Optional deterministic ID from vendor+period when a planted open accrual exists. |
| Insufficient-evidence accrual skip | `PARTIALLY_IMPLEMENTED` | Agent output allows `INSUFFICIENT_EVIDENCE`. Demo vendors used for close have enough history to accrue. | Adding a no-evidence vendor would change close eval in ways we did not want to invent. | `accrual/agent.py`, `accrual/workflow.py` | Plant a vendor with no contract/history and assert SKIP / INSUFFICIENT_EVIDENCE. |
| Semantic context graph / RAG memory | `NOT_IMPLEMENTED` | Closest mechanisms: `prior_cases`, `ar_precedents`, `close/context` identity links. | There is no graph database or embedding store. | `close/context.py`, `ar/ledger.py` | Keep identity_links; add retrieval over traces if needed. |
| AP learning from corrections | `NOT_IMPLEMENTED` | Only AR `record_human_application()` → `_learn_precedent()`. | `SCN-LEARN-001` proves the AR correction is **retrievable**, not that AP behavior changes. | `ar/ledger.py` | Do not pretend AP fine-tunes. |
| Live Stripe credentials | `IMPLEMENTED_AND_TESTED` (mock) / live optional | `STRIPE_MODE=mock` is default. Live path is separate. | Demo evals must stay deterministic without secrets. | `integrations/providers/stripe.py` | Keep live demo as `python main.py stripe-demo` with env keys. |
| Production ERP write-back | `NOT_IMPLEMENTED` | Coupa/NetSuite/Xero are ingest/sync mocks. | No NetSuite post of JEs. | `integrations/providers/*` | Out of demo scope. |

## Status legend

- **IMPLEMENTED_AND_TESTED** — engine exists; Maximor plants a case; eval/tests exercise it.
- **IMPLEMENTED_BUT_FAILING** — none currently recorded for the canonical pack; see `runs/demo_eval/latest.json` after a run.
- **PARTIALLY_IMPLEMENTED** — real code path exists, but the demo cannot honestly show the full lifecycle.
- **NOT_IMPLEMENTED** — do not invent findings or agent answers.

Skills remain registered only in `skills/README.md` and `skills/assignments.py`. No competing skill registry was added.
