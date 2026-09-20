# NOTES — AR money in (prompt 02)

Date: 2026-09-20. Disk wins.

There is no Bot `ar`. Operators are `apply` and `collect`. Open invoices are World-pack data. No invoicing Bot.

## Floor

Computer cwd `office/bots/` is a symlink to `.cfo-v2/office/bots`. RUN.md documents live Pi, not `--fake`. Intercept default is Bot `ctl-pay`. Collect override is `ctl-pay`. Handle files live under `harness/bots/*/handles/`. Continue on Kernel send, Grants, World.

## Tests A–D for World — bind

**A Wake.** Handle `email/outbound`, `collect/dun`, `ap/vendor-query`. Operator can address slug `world`. World can originate inbound (`compose_counterparty_message` + `send_inbox_message`). Not a Profile on Email: Email cannot Handle itself to role-play the customer.

**B Object.** Simulated counterparty messages. Not open bills. Once delivered, Email classifies.

**C Grants.** World wears Counterparty Message Agent: compose, send_inbox, reply, list threads/messages, personas. World must not `dispatch_inbox_action`, must not `send_office_outbound`, must not hold AP RECORD_TOOLS. Email must not `send_inbox_message` as a vendor. Union is unsafe.

**D Memory.** Persona voice and this counterparty's delay habit.

Rohan folding Counterparty into Email failed Test A. World is bound on the live Roster as the sixteenth Source Bot. Not Bot `ar`. Not live Gmail.

## One send story

Kernel-allowed SEND_* calls `inbox.tools.send_office_outbound` from `collections@hackmit-cfo.example`. `sent=True` only when the message is in simulated transport. Then Handle `world` / `customer`. Skill, constructor, workflow, BOT.md, Roster, and handle-map agree. Preview-only is deleted.

Write-off stays `ctl-pay` / `review-pay`. No tone Verifier.

Apply still runs first. Dirty aging Handle apply. No peer Handle from apply to collect to chase.

## Dual intake

Email Profiles `invoice` / `employee` / `portal` / `document` stay on `invoice_ingestion.tools.*`. Profile `inbox` / `triage` stays on `inbox.tools.*`. Remittance via inbox is a notice (`RECORD_CUSTOMER_REMITTANCE`), not a second Kernel bill id. Do not mint AR-side duplicates for 03.

## Learning

`ctl-cash` approve writes remittance precedent (`source=verifier`). `ar-review-correct` remains emergency CLI. Precedent is color. It cannot override a live named invoice.

Collect records `collection_contact` habit when a SEND lands. Kernel `enforce_collection_decision` still owns eligibility.

## Proof

Insert `.cfo` first so the repo-root `inbox/tools.py` shadow is not loaded:

```bash
.cfo/.venv/bin/python -c "import sys; from pathlib import Path; root=Path('.').resolve(); sys.path.insert(0, str(root/'.cfo')); import inbox.tools; assert inbox.tools.__file__.endswith('/.cfo/inbox/tools.py'); from inbox.tools import send_office_outbound; from ar.agents import collections_agent; print(inbox.tools.__file__); print(collections_agent.name)"
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
PYTHONPATH=.cfo:.cfo-v2/office .cfo/.venv/bin/python -m pytest .cfo/tests/test_inbox_world.py .cfo/tests/test_ar_harness.py .cfo-v2/office/compiler/test_compile_inbox.py -q
```

World is on the live Roster. Catalog send ops exist after compile. Collections Agent constructs.
