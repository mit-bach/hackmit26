# NOTES

Constitution: `.cfo-v2/office/constitution.md`. EDI and Coupa stay Connectors. Tests A–D were not failed; no sixteenth Bot.

Roster merge fields:

- `id`: `bot_books`
- `name`: Books
- `slug`: `books`
- `purpose`: Land GL, subledger, PO, and structured bill records; read period lock state; do not close.
- `instructions`: Read `office/bots/books/BOT.md`. Obey the Constitution. Never ask a human. Do not lock the period.
- `skills`: `invoice-source-identification`
- `connectors`: `xero`, `netsuite`, `coupa`, `edi`
- `approvalLevel`: `never`
