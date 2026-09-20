# NOTES

Constitution: `.cfo-v2/office/constitution.md`. This Bot follows grain § Source Bots. Verifier Bots own concurrence. The Operator is not a worker.

Bot `world` is talkable on 8800. It is the simulated outside mailbox. Classify and dispatch stay here. Counterparty Message Agent is World's Display name, not "not a Bot."

Roster merge fields for this slug:

- `id`: `bot_email`
- `name`: Email
- `slug`: `email`
- `purpose`: Land mailbox and attachment objects; classify bill vs remittance; send Handles; outbound missing-info to World.
- `instructions`: Read `office/bots/email/BOT.md`. Obey the Constitution. Never ask a human. Outbound missing-info: `send_office_outbound` then Handle `world`.
- `skills`: `invoice-source-identification`, `invoice-field-interpretation`, `inbox-triage`
- `connectors`: `gmail`, `outlook`, `employee-upload`, `vendor-portal`, `mailroom`
- `approvalLevel`: `never`

Profile `triage` maps to Finance Inbox Agent. Do not create a second inbox Bot.

