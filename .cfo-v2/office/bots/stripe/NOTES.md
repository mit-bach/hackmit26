# NOTES

Constitution is at `.cfo-v2/office/constitution.md`. Stripe has no `Agent()` constructor. Profile `payout` maps to an empty Display name. Grants stay empty. Do not emit `InvoiceCandidate`.

Roster merge fields:

- `id`: `bot_stripe`
- `name`: Stripe
- `slug`: `stripe`
- `purpose`: Land processor payouts; hand the deposit to `cash` and charge-level facts to `apply`.
- `instructions`: Read `office/bots/stripe/BOT.md`. Obey the Constitution. Never ask a human. Never produce InvoiceCandidate.
- `skills`: []
- `connectors`: `stripe`, `adyen`
- `approvalLevel`: `never`
