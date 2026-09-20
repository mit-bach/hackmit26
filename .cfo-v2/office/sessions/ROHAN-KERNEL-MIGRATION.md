# Rohan Kernel migration (inbox, Stripe sim, overlay)

Source branch: `origin/durable-inbox-ap-persistence` (`8d16175`).
Bot `world` is now the simulated outside mailbox. Pi Handle completion was not live-proven.

## What landed

| Rohan piece | Where it lives now | Office wiring |
| --- | --- | --- |
| `.cfo/inbox/` | Kernel Gmail-like front door | Bot `email` classifies/dispatches. Bot `world` composes/sends/replies. `land_inbox_spec` → Handle `ap` or `apply` |
| Durable AP overlay | `tools.register_runtime_invoice` + `configure_runtime_dir` | Shared Computer overlay. Does not edit `invoices.json` |
| `.cfo/simulations/stripe/` | Kernel fixture universe | Bot `stripe`. Constructor Grants stay empty. `invoice_candidates` = 0 |
| `.cfo/data/simulations/stripe/` | Operational sim pack | `evaluation/ground_truth.json` is eval-only |
| `inbox-triage` skill | Kernel + Computer skills | Roster Bot `email` skills[]. Not a Bot |

Rohan’s checkout of `ar/workflow.py`, `ar/models.py`, and `ar/store.py` had dropped the Session 06 apply-before-collect gate and Verifier Handle fields. Those are restored on this tree. Stripe ledger helpers (`learn_stripe_precedent`, refunds, disputes, processor fees) landed in `ar/ledger.py`. Inbox `persist_state` now dumps invoice objects so a wiped overlay can rehydrate.

## What did not land as extra Bots

- Sample-data Display names
- Human review as a completion path
- Replacing planted `$12.40` demo close / cash-recon data
- Wholesale overwrite of `data/invoices.json`
- Live Gmail or live Stripe

Counterparty Message Agent is Bot `world` (default Profile `vendor`). Finance Inbox Agent is Email Profile `triage`. Classify stays on Email.

## Commands

See `office/RUN.md` §6. From `.cfo/`:

```bash
python3 main.py demo-inbox --reset
python3 main.py simulate-stripe
```

`demo-inbox` classifies mail, writes the durable AP overlay, and does not ask a human. Vendor bills Handle `ap` / `prepare`. Remittances Handle `apply` / `apply`.

`simulate-stripe` unpacks payout waterfalls in Python. `invoice_candidates` stays 0.

## Proofs (not live Pi)

Roster has **16** slugs including `world`: `email`, `stripe`, `bank`, `books`, `world`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`. Email skills include `inbox-triage`. `$12.40` remains in `data/demo/close/tasks.json`. Computer `data/` still points at `.cfo/data`. World is talkable. Simulated only.

Isolated `python3 main.py demo-inbox --reset`: `MSG-INBOX-001` → `CREATED` / `ING-001` on `runtime_invoices.json`. Marketing mail `IGNORED`. No `ask_user`.

`python3 main.py simulate-stripe`: 23 scenarios, pack under `data/simulations/stripe/`, visualization under `runs/evals/stripe_simulation/`.

Pytest (Kernel + office): inbox unit/persistence/integration/e2e, skills, source wakes, ingestion overlay, Stripe simulation, AR harness/demo, Session 12 roster/eval isolation. Handle completion was not live-proven.
