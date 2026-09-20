# Finance provider integrations

Researched **2026-09-19** from official vendor documentation. Mock mode in this repo does not require credentials. Live mode is opt-in via environment variables.

Two event families are kept separate:

- **Accounts payable invoice sources** (Gmail, Outlook, Xero, Coupa, NetSuite) produce `InvoiceCandidate` records for existing ingestion.
- **Cash / payout sources** (Stripe, Adyen) produce `ProviderPayout` records. They never become invoices.

---

## Stripe

**Workflow fed:** cash / payout reconciliation (not AP). Stripe customer payments never become invoices.

```
Stripe
  → webhook (POST /webhooks/stripe)
  → verify Stripe-Signature on the raw body
  → payout (GET /v1/payouts/:id)
  → balance transactions (GET /v1/balance_transactions?payout=)
  → expected cash (Python integer minor-unit math)
  → bank deposit (independent evidence, never fabricated from Stripe)
  → reconciliation (MATCH / MISMATCH / AWAITING_BANK / NEEDS_REVIEW)
```

| Topic | Official behavior |
|---|---|
| Mechanism | HTTPS webhook endpoint registered in Workbench / `/v2/core/event_destinations`. Snapshot events POST JSON. |
| Auth | Endpoint signing secret `whsec_...`. Header `Stripe-Signature` (`t=...,v1=...`). Verify with official library `stripe.Webhook.construct_event(payload=raw_body, sig_header=signature, secret=secret)` on the **unmodified** raw body. Invalid or missing signature → HTTP 400, no payout, no reconciliation. |
| Delivery | Stripe POSTs to a public HTTPS URL. Local: `stripe listen --forward-to localhost:8000/webhooks/stripe`. |
| Relevant events | Prefer `payout.reconciliation_completed` (balance transactions for an automatic payout are queryable). Also record `payout.created`, `payout.updated`, `payout.paid`, `payout.failed`, `payout.canceled`. Unrelated events such as `payment_intent.created` are acknowledged and ignored. |
| Payload IDs | Event `id` (`evt_...`). Payout `data.object.id` (`po_...`). |
| After event | Retrieve the payout (`GET /v1/payouts/:id`). On `payout.reconciliation_completed` or `payout.paid`, list BalanceTransactions filtered by `payout=po_xxx` (`GET /v1/balance_transactions?payout=`), `expand[]=data.source`, paginate with `starting_after` / `auto_paging_iter()`. Types include `charge`, `refund`, `stripe_fee`, `adjustment` (disputes), `payout`. Unknown types are kept as `other`. Manual payouts cannot be auto-attributed to transactions. |
| Retry | Live: up to three days, exponential backoff. Sandbox: three retries over a few hours. Acknowledge with 2xx quickly. |
| Duplicates | Same `event.id` may be delivered more than once. Track processed event IDs. Distinct Event objects can also describe the same payout; one canonical `ProviderPayout` per `po_...`. |
| Expiration | Webhook endpoints do not expire. No watch renewal. |
| Sandbox | Stripe test mode + Stripe CLI. CLI signing secret differs from Dashboard secret. |

**Mock vs live**

`STRIPE_MODE=mock` (default) uses fixtures under `data/integrations/stripe/`. No Stripe credentials are required. `python main.py integration-demo` and `python main.py stripe-demo` always use the mock provider.

`STRIPE_MODE=live` uses `LiveStripeProvider` and the official Stripe Python SDK (`stripe` 15.x). Requires `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`. Missing live credentials fail cleanly; they do not silently fall back to mock for API/sync calls.

**Bank evidence**

Stripe's payout amount is what Stripe sent. It is not independent bank evidence. If a bank deposit is on file and matches, status is `MATCH`. If no bank record exists, status is `AWAITING_BANK`. A differing bank amount is `MISMATCH` (`bank_amount_differs_from_stripe_payout`). The fixture-backed demo includes `BANK-STRIPE-97420` so the HackMIT example stays `MATCH`.

**Idempotency**

- Same Stripe event twice → one payout, one reconciliation.
- Different events for the same `po_...` → update the canonical payout, no second cash record.
- `python main.py sync stripe` after a webhook (and the reverse) does not duplicate payouts.

**Manual sync**

```bash
python main.py sync stripe
python main.py sync stripe --payout po_123
python main.py stripe-sync
```

Uses the same normalize → cash-math → reconcile path as the webhook.

**Local Stripe CLI**

```bash
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe
```

Copy the printed `whsec_...` into `.env` as `STRIPE_WEBHOOK_SECRET`. Then:

```bash
python main.py webhook-server
```

Trigger a payout-related test event (Dashboard payout, or `stripe trigger payout.created` / `stripe trigger payout.paid`). The handler prefers `payout.reconciliation_completed` for loading balance transactions.

**Deviation from prompt:** Stripe payouts are **not** invoices. This implementation never maps them to `InvoiceCandidate`. Official event `payout.reconciliation_completed` is valid on current Stripe API docs (2026) and is used as-is.

Official URLs:

- https://docs.stripe.com/webhooks
- https://docs.stripe.com/webhooks/signature
- https://docs.stripe.com/payouts/reconciliation
- https://docs.stripe.com/api/payouts
- https://docs.stripe.com/api/balance_transactions/list
- https://docs.stripe.com/api/events/types
- https://docs.stripe.com/cli/webhooks

---

## Adyen

**Workflow fed:** cash / payout reconciliation (not AP).

| Topic | Official behavior |
|---|---|
| Mechanism | Transfer webhooks v4: `balancePlatform.transfer.created`, `balancePlatform.transfer.updated`. Configured in Customer Area. Not the classic payments `eventCode` webhook. |
| Auth | HMAC. Transfer / platform webhooks put the signature in header `hmacsignature` (protocol `HmacSHA256`). Compute HMAC-SHA256 over the **raw** body with the hex-decoded HMAC key, Base64-encode, constant-time compare. Do not deserialize before verify. |
| Delivery | POST JSON to a public URL. Respond 200 or 202 within 10 seconds **before** business logic. |
| Relevant events | `balancePlatform.transfer.created`, `balancePlatform.transfer.updated`. Status on `data.status` (for example received → authorised → booked). `data.category` includes `bank` for bank-side settlement. |
| Payload IDs | Transfer `data.id`. Amount `data.amount.value` (minor units) + `data.amount.currency`. Optional `data.reference`. Environment + `type` on the envelope. Transfer webhooks do **not** use classic `pspReference`/`eventCode` duplicate keys. |
| After event | Track `data.id` across created/updated. Fetch transfer details / related transactions from Transfers API when live. |
| Retry | If no 2xx within 10s, marked Failing and retried. |
| Duplicates | Standard webhooks: same `eventCode` + `pspReference`. Transfer webhooks: treat `type` + `data.id` + `data.status` as the idempotency key; later updates replace status. |
| Expiration | Endpoint configuration does not expire like Gmail watch. |
| Sandbox | Adyen test company / Customer Area test webhooks. |

**Deviation from prompt:** Event names confirmed as `balancePlatform.transfer.created` / `updated`, not invented payout event names. HMAC is in the **header** for this webhook family, not `additionalData` (that pattern is classic payments webhooks).

Official URLs:

- https://docs.adyen.com/api-explorer/transfer-webhooks/latest/overview
- https://docs.adyen.com/api-explorer/transfer-webhooks/4/post/balancePlatform.transfer.updated
- https://docs.adyen.com/development-resources/webhooks/handle-webhook-events
- https://docs.adyen.com/development-resources/webhooks/secure-webhooks/verify-hmac-signatures/

---

## Gmail

**Workflow fed:** AP invoice ingestion via the shared Email classifier (`interpret_email`).

Google does **not** POST the email body to our server.

```
users.watch → Pub/Sub topic → push subscription → POST /webhooks/gmail
→ decode {emailAddress, historyId} → history.list(startHistoryId) → messages.get → attachments
→ existing Email Invoice extraction
```

| Topic | Official behavior |
|---|---|
| Mechanism | Gmail API `users.watch` publishes to Cloud Pub/Sub. Push subscription HTTP POSTs a `PubsubMessage`. `message.data` is Base64URL JSON `{"emailAddress","historyId"}`. |
| Auth | Pub/Sub **authenticated push**: Bearer OIDC JWT in `Authorization`. Validate signature, `iss=https://accounts.google.com`, `email` matches the push service account, `aud` matches the endpoint or configured audience. |
| After notification | `history.list` with stored `startHistoryId`. `messagesAdded` → `messages.get` (+ `users.messages.attachments.get`). 404 on stale historyId requires full sync. |
| Renewal | Watch expires. Response `expiration` is epoch millis. **Must call `watch` at least once every 7 days**; Google recommends daily. |
| Retry | Unacked push (non-2xx / timeout) is retried by Pub/Sub. Max one notification/second/user; extras dropped. Notifications can be delayed or dropped — fall back to periodic `history.list`. |
| Duplicates | Pub/Sub `messageId` plus Gmail `message.id`. Replayed push must not create a second invoice. |
| Env | `GOOGLE_CLOUD_PROJECT`, `GMAIL_PUBSUB_TOPIC` (`projects/{project}/topics/{topic}`), `GOOGLE_APPLICATION_CREDENTIALS`, `GMAIL_ACCOUNT`, `GMAIL_PUSH_AUDIENCE`. Grant publish to `gmail-api-push@system.gserviceaccount.com`. |

Official URLs:

- https://developers.google.com/workspace/gmail/api/guides/push
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/watch
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list
- https://developers.google.com/workspace/gmail/api/guides/sync
- https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions

---

## Microsoft Outlook / Graph

**Workflow fed:** AP invoice ingestion via the **same** Email classifier as Gmail.

```
POST /v1.0/subscriptions (changeType=created, resource=users/{id}/messages)
→ Graph validates notificationUrl (?validationToken=)
→ change notification POST /webhooks/outlook
→ GET message + attachments
→ interpret_email
```

| Topic | Official behavior |
|---|---|
| Handshake | Graph POSTs `notificationUrl?validationToken={opaque}`. Respond **HTTP 200**, `Content-Type: text/plain`, body = **URL-decoded token only**, within 10 seconds. No JSON, no extra newline. |
| Auth of notifications | Compare `clientState` to the secret set at subscription create. Rich notifications also include JWT `validationTokens`. This implementation subscribes **without** resource data and fetches the message (no encryption certificate required). |
| Permissions | `Mail.Read` / `Mail.ReadBasic`. Delegated: signed-in user's mailbox only. Shared/delegated AP mailbox: **application** `Mail.Read`, not `Mail.Read.Shared`. Identify user by OID, not UPN. |
| Lifetime | Outlook message **without** resource data: max **10,080 minutes (under 7 days)**. With resource data: 1,440 minutes. Renew via PATCH subscription `expirationDateTime` before expiry. Values under 45 minutes are raised to 45 minutes. |
| Lifecycle | Optional `lifecycleNotificationUrl` for `subscriptionRemoved`, `reauthorizationRequired`, `missed`. Apps must recover missed notifications (delta query / re-list). |
| After notification | GET `resource` / `@odata.id`. Then GET `$value` attachments. |
| Duplicates | No Stripe-like event id. Idempotency key: `subscriptionId` + `resourceData.id` + `changeType`. |
| Retry | Graph retries failed deliveries. Message latency typically <1 minute, max 3 minutes. |

Official URLs:

- https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview
- https://learn.microsoft.com/en-us/graph/change-notifications-delivery-webhooks
- https://learn.microsoft.com/en-us/graph/api/resources/subscription?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions?view=graph-rest-1.0

---

## Xero

**Workflow fed:** AP invoice ingestion for **ACCPAY bills only**.

| Topic | Official behavior |
|---|---|
| Mechanism | App webhook subscription. POST batched `{events, firstEventSequence, lastEventSequence, entropy}`. Invoice events: `eventCategory=INVOICE`, `eventType=CREATE` or `UPDATE`. |
| Auth | HMAC-SHA256 of raw body with webhook key, Base64, header `x-xero-signature`. Intent to Receive: three unsigned probes must return **401**, correctly signed probe **200** with empty body. |
| Payload | Events contain `resourceId`, `resourceUrl`, `tenantId`, `eventDateUtc` — **not** the invoice fields. Follow up: `GET https://api.xero.com/api.xro/2.0/Invoices/{InvoiceID}` with OAuth 2.0 + `Xero-tenant-id`. |
| AP vs AR | Accounting API `Type`: `ACCPAY` = bill (AP), `ACCREC` = sales invoice (AR). Only `ACCPAY` is ingested. `ACCREC` is stored then ignored. |
| Duplicates / replay | `tenantId` + `resourceId` + `eventType` + `eventDateUtc`. Sequence numbers increase. |
| Expiration | Webhook subscription stays until removed; OAuth access tokens expire and must be refreshed. |
| Sandbox | Xero Demo Company. |

Official URLs:

- https://developer.xero.com/documentation/guides/webhooks/overview/
- https://github.com/XeroAPI/Xero-OpenAPI/blob/master/xero-webhooks.yaml
- https://developer.xero.com/documentation/api/accounting/invoices

Xero HTML docs pages sometimes require a developer login; event schema was confirmed from the official OpenAPI (`xero-webhooks.yaml`) and Accounting API invoice types.

---

## Coupa

**Workflow fed:** AP invoice ingestion (procurement / three-way match **inputs only**).

**No suitable official invoice webhook** is documented for this use case. Coupa Core API is request/response. ERP integration guidance is poll `GET /api/invoices` (often `exported=false`) or hourly CSV export. This project **does not invent a Coupa webhook**.

| Topic | Official behavior |
|---|---|
| Mechanism | `GET/POST/PUT https://{instance}/api/invoices` and `GET /api/invoices/:id`. |
| Auth | Coupa Core API OIDC / OAuth 2.0 client credentials (instance-specific). Header `Authorization: Bearer`. |
| Incremental sync | Query by `updated-at`, status, supplier, `exported=false`. Idempotency: Coupa invoice `id`. |
| Fields | id, invoice-number, supplier, amount, currency, invoice-date, po-number / order lines, status, receipts where expanded. |
| Three-way match | **Not** performed in the adapter. Existing AP workflow owns matching. |

Official URLs:

- https://docs.coupa.com/en/developer-documentation/the-coupa-core-api/resources/transactional-resources/invoices-api-invoices
- https://docs.coupa.com/en/developer-documentation/the-coupa-core-api/orchestration-documents/invoices-integration-into-your-erp
- https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/the-coupa-core-api/resources/transactional-resources/invoices-api-(invoices)

---

## NetSuite

**Workflow fed:** AP invoice ingestion (vendor bills).

SuiteTalk **REST** `vendorBill` is the current record API. SOAP is not used.

Official REST does **not** push HTTP webhooks to an external URL. Oracle documents:

- REST GET/POST/PATCH `/services/rest/record/v1/vendorBill`
- SuiteScript **Event Subscriber** (2026.2) runs **inside** NetSuite (`handle(options)` with `recordId`) — it is not an inbound webhook we can expose as `POST /webhooks/netsuite` without custom SuiteScript `N/https` posting out.

This project uses **incremental REST sync**, not a fabricated NetSuite webhook.

| Topic | Official behavior |
|---|---|
| Mechanism | `GET {account}/services/rest/record/v1/vendorBill/{id}?expandSubResources=true` and collection query. |
| Auth | REST OAuth 2.0 (client credentials / TBA as configured on the integration record). |
| IDs | Internal `id`. `tranId` / vendor invoice number, entity (vendor), dueDate, amount, purchase order links. |
| Idempotency | Internal ID. Repeat sync updates provenance, does not mint a second payable. |
| Sandbox | NetSuite sandbox account. |

Official URLs:

- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_164484956387.html
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_0504045254.html
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_47180719123.html (Event Subscriber — in-account script, not used here)

---

## Local development

| Provider | Documented local path |
|---|---|
| Stripe | `stripe listen --forward-to localhost:8000/webhooks/stripe`. Put the CLI `whsec_` in `STRIPE_WEBHOOK_SECRET`. Then `python main.py webhook-server`. Optional: `python main.py sync stripe`. |
| Adyen | Customer Area test webhooks / library HMAC validator. Public HTTPS URL required. |
| Gmail | Pub/Sub push to a public HTTPS URL (generic tunnel if needed). Not a hard ngrok dependency. |
| Outlook | Graph requires HTTPS `notificationUrl`. Handshake must succeed. |
| Xero | Intent to Receive against a public URL. |
| Coupa / NetSuite | Call mock `python main.py sync coupa` / `sync netsuite`, or live GET with credentials. |

Start the webhook server:

```bash
python main.py webhook-server
# POST http://127.0.0.1:8000/webhooks/{stripe,adyen,gmail,outlook,xero}
```

---

## Mock vs live

`INTEGRATIONS_MODE=mock` (default) uses fixtures under `data/integrations/`. Live adapters run only when `INTEGRATIONS_MODE=live` **and** the provider secret/token is set. Missing live credentials fall back to mock rather than crashing the HackMIT demo.

Stripe is the exception that has a first-class live path:

- `STRIPE_MODE=mock` (default) — fixtures, no credentials.
- `STRIPE_MODE=live` — official Stripe SDK. Missing `STRIPE_SECRET_KEY` fails cleanly on sync/API; it does not invent payouts.

