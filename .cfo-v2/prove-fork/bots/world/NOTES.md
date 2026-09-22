# NOTES

Constitution: `.cfo-v2/office/constitution.md`. Grain Tests A–D passed. Bound on the live Roster 2026-09-20. This is the sixteenth Source Bot. Simulated mailbox only. No live Gmail.

## Tests A–D

**A Wake.** Handle from `email` / `outbound` (missing-field mail) and `collect` / `dun`. Operator can address slug `world`. World can originate inbound (`compose_counterparty_message` + `send_inbox_message`, including fixture send). Work does not only run because Email continued its own turn.

**B Object.** One class: simulated counterparty messages (the outside world's mailbox). Not an open bill. Once delivered, Email classifies.

**C Grants.** World may compose, send, and reply as a persona. World must not `dispatch_inbox_action`, must not `send_office_outbound`, must not hold AP RECORD_TOOLS, `create_accrual`, pay-run, or cash post. Email must not `send_inbox_message` as a vendor. Union with Email is unsafe. Profiles `vendor` / `customer` / `bank` / `employee` share one Grant set (Counterparty Message Agent). Instructions change. Tools do not.

**D Memory.** Persona voice and this vendor's or customer's delay habits.

Rohan folded Counterparty into Email Display names. That failed Test A: the Operator could not open it, Email could not Handle it, and dunning had nobody to role-play. It is a Bot.

## Roster merge fields

- `id`: `bot_world`
- `name`: World
- `slug`: `world`
- `purpose`: Simulated counterparty mailbox. Role-play whoever finance mailed.
- `instructions`: Read `office/bots/world/BOT.md`. Obey the Constitution. Never ask a human. Do not write AP.
- `skills`: none (Counterparty Message Agent has an empty skill assignment)
- `connectors`: `inbox.tools.compose_counterparty_message`, `inbox.tools.send_inbox_message`, `inbox.tools.reply_in_thread`, browse + `list_world_personas`
- `approvalLevel`: `never`

Default Profile `vendor` maps to Display name Counterparty Message Agent.

Finance Inbox Agent stays on Email Profile `inbox` / `triage`. Classify is not a second inbox Bot.

Proof: `docs/Agentic-update/evidence/NOTES-ar.md`. Tests A–D are the bind argument.
