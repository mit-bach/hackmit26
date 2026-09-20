# Intake — source edge

Intake is not a fifth pipe. It is how objects enter the four pipes.

Grain Source Bots: `email`, `stripe`, `bank`, `books`. Instance snapshots add `world` as the simulated outside mailbox.

---

## Intended function

Something in the world becomes a path on the Computer, classified, with Kernel identity where a bill is a bill. Then a Handle names the Operator Bot that owns the open item.

| Landed object | Next owner |
| --- | --- |
| Vendor bill | `ap` / `prepare` |
| Customer remittance | `apply` / `apply` |
| Customer invoice record already on books | `collect` / `chase` (after apply drain) |
| Bank line | `cash` / `match` |
| Stripe payout | `cash` (deposit) and `apply` (charge-level) |
| Missing invoice fields | outbound from finance, then a counterparty reply |

Email carries two pipes. Do not split `email-ap` and `email-ar`. Classification is the Source Bot’s job.

A charge is not a bill. A Stripe payout is not an `InvoiceCandidate`.

---

## What exists that is good

- Four different source objects, not one “ingest” Bot. Slug `ingest` is forbidden. It belongs to the Harness fixture.
- Invoice vs remittance vs quote vs statement vs marketing is a real Kernel classification problem. Skills `invoice-source-identification` and `inbox-triage` exist for that judgment.
- Durable AP overlay and canonical invoice identity exist in Kernel.
- Simulated inbox tools exist: compose, send_inbox (as counterparty), classify, extract, dispatch.
- Live Pi proved Email can Handle AP. AP refused an empty marker instead of inventing a bill. That is correct fail-closed on bad intake.

---

## What is broken

### Dual intake stacks (T2)

Email Profiles `invoice` / `employee` / `portal` / `document` call `invoice_ingestion.tools.*`.
Email Profile `inbox` calls `inbox.tools.*`.

Two front doors into AP. Judges and Bots can land the same vendor twice with different ids.

### World off the live Roster (T1, T4)

World BOT.md, profiles, instance Roster, and Counterparty Grants exist.
Live `roster.json` omits `world`.
Live `slug-map.json` omits `world`.
`handle-map.json` has no `world/delivered` → Email `triage`, no `email/outbound` → World, no `collect/dun` → World.

The simulated customer and vendor cannot play.

### Send op missing in live Kernel (T3)

`.cfo/ar/agents.py` imports `send_office_outbound`.
`.cfo/inbox/tools.py` does not define it.
Instance catalogs include it.
Live catalog does not.

Finance cannot speak. World cannot be asked to reply to a missing-field mail that was never sent.

### Email BOT.md contradicts World BOT.md (T2)

Email: “Counterparty Message Agent remains a fixture Display name, not a Roster slug.”
World: “You are Bot `world`.”
Capabilities.md: World is the sixteenth Source Bot.
Constitution: do not invent a sixteenth without Tests A–D.
RUN.md: inbox and Stripe simulation “are not a sixteenth Bot.”

### Stripe is costume (T3, T5)

Wake `payout.paid` is real. Object (waterfall) is real. Constructor Display name is empty. Grants empty. Unpack is `python3 main.py simulate-stripe`. Bot `stripe` cannot `call_connected_tool`.

### No bank webhook (grain watch)

Bot `bank` is still a Bot (object + poll Wake). Connector is missing from `WEBHOOK_PROVIDERS`. Card-without-invoice stays `invoice_missing`. That is correct object law. The Bot still cannot poll anything on the live bus.

### BOT.md path (T6)

Roster instructions: read `office/bots/email/BOT.md` from Computer cwd. That path does not resolve.

### Live stub (T12)

`workspace/sources/email/MSG-S12.json` is a marker. Kernel has no INV-S12. The completed Handles are a protocol demo on empty intake.

---

## Inadequacies of things that “work”

Classification skills tell the model not to invent amounts. Kernel parse already owns amounts. The remaining judgment is “what kind of document is this” and “who owns it next.” Those skills still read like extraction checklists (T7).

Gmail and Outlook are named Connectors. They are not live. Pretending they are live is a product lie. Simulated transport is the intended demo. The inadequacy is that simulated transport is not wired to World on the live Computer.

Employee upload, vendor portal, mailroom scan are extra Connectors on Email, not extra Bots. That compression is good. None of those Connectors is proven office-live.

---

## Capability this edge must possess

When intake is adequate:

1. A vendor can deliver a bill into the simulated mailbox. Email classifies it as a bill. Kernel identity runs. `ap` receives a path to a real invoice, not a marker.
2. A customer remittance can land. Email classifies it as remittance. `apply` receives the payment id.
3. Finance can ask a vendor for a missing field. That outbound exists in the mailbox. A counterparty persona can reply in the same thread. Email classifies the reply. The original bill is not silently approved.
4. Prompt-injection inside a message body does not change Grants or mark a bill paid.
5. A Stripe-shaped payout unpacks to a deposit plus charge-level facts, with zero invoice candidates.
6. A card charge does not become a bill unless supporting documents exist.

How Email notices this vendor’s attachment layout, and how World plays a late customer, is specialist work. This file does not specify the persona algorithm.

---

## Novelty fence

Do not add `email-ap` and `email-ar`.
Do not add a Bot per source format.
Do not make World dispatch the finance inbox.
Do not make Email send as a vendor.
Do not invent live Gmail for the judged demo.

World’s grain status is a product decision already argued in Capabilities.md vs constitution. This file only requires the mailbox round-trip as a function. It does not add the Bot in prose.
