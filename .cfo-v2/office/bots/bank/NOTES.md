# NOTES

Constitution: `.cfo-v2/office/constitution.md`. No bank provider in `WEBHOOK_PROVIDERS`; poll is the Wake.

Roster merge fields:

- `id`: `bot_bank`
- `name`: Bank
- `slug`: `bank`
- `purpose`: Land bank lines and card charges; keep invoice_missing on this Bot.
- `instructions`: Read `office/bots/bank/BOT.md`. Obey the Constitution. Never ask a human. A charge is not a bill.
- `skills`: `bank-charge-invoice-discovery`
- `connectors`: `bank-feed`
- `approvalLevel`: `never`
