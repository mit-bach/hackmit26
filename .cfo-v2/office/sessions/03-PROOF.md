# Session 03 proof — Source Bots

Migrate ingestion onto `email`, `stripe`, `bank`, `books`. They land objects and emit Handle send payloads. They do not match, pay, apply, accrue, or lock. Handle completion was not live-proven (Pi was not bound). Kernel and unit proofs ran.

Client root: `.cfo-v2/`. Computer: `.cfo-v2/office/computer`. Kernel stays in `.cfo/`.

## Commands

Kernel identity, overlay persistence, Stripe fixture, bank `invoice_missing`, and Client Handle payloads:

```bash
cd .cfo
.venv/bin/python -m pytest \
  tests/test_ingestion_idempotency.py \
  tests/test_ingestion_sources.py \
  tests/test_ingestion_registry_persist.py \
  tests/test_ingestion_validate.py \
  tests/test_integrations.py \
  ../.cfo-v2/office/source_wakes/test_wakes.py \
  -q
```

Result: **56 passed**.

Isolated typecheck of Client Handle payload types (no finance types):

```bash
cd .cfo-v2/office/computer/cfo
./node_modules/.bin/tsc --strict --noEmit --target ES2022 \
  --module NodeNext --moduleResolution NodeNext --isolatedModules \
  source-wakes.ts
```

Result: exit 0.

`tsc -p tsconfig.json` still fails on pre-existing `extensions/profile.ts` (`SlugMapFile` missing). That is session 01, not this slice.

Roster has no slug `ingest`:

```bash
python3 -c 'import json; r=json.load(open(".cfo-v2/office/computer/harness/roster.json")); print([b["slug"] for b in r["bots"]]); print("ingest" in [b["slug"] for b in r["bots"]])'
```

Result: `email stripe bank books ap pay apply collect cash close story ctl-pay ctl-cash ctl-books audit` and `False`.

## Disk after the wake host

Artifacts under `.cfo-v2/office/sessions/03-disk/`:

| Path | What it shows |
| --- | --- |
| `computer/workspace/sources/email/MSG-E01.json` | Email invoice packet |
| `computer/workspace/sources/email/MSG-E01.send.json` | Handle to `ap` / `prepare` (`bot_ap`) |
| `computer/workspace/sources/email/MSG-R01.send.json` | Handle to `apply` / `apply` (`bot_apply`) |
| `computer/workspace/sources/stripe/po_1HackMIT97420.json` | `invoice_candidates: 0`, Kernel waterfall |
| `computer/workspace/sources/stripe/po_1HackMIT97420.send.json` | Handles to `cash` and `apply` |
| `computer/workspace/sources/bank/CC-4412.json` | `status: invoice_missing`, `candidate: null` |
| `computer/workspace/sources/bank/CC-4412.send.json` | `[]` (stays on `bank`) |
| `ingestion-state/registry.json` | Canonical `ING-001` AWS INV-9001 on disk |
| `ingestion-state/overlay.json` | AP overlay invoice `ING-001` on disk |

Email invoice send payload (Pi fake; this is what `bot_send_prompt` would accept):

```json
{
  "from": "bot_email",
  "to": "bot_ap",
  "toSlug": "ap",
  "profile": "prepare",
  "kind": "a2a_handoff"
}
```

## Proofs required by the session

1. **Stripe fixture payout does not create an InvoiceCandidate.** Kernel `result.invoice_candidates == 0`. Packet has `"invoice_candidates": 0`. Overlay has AWS from email, not `po_1HackMIT97420`.
2. **Email invoice path writes a file and would address `ap`.** `MSG-E01.json` plus send payload `toSlug: ap`.
3. **Email remittance path addresses `apply`.** `MSG-R01.send.json` `toSlug: apply`. One Bot `email`, two Pipes.
4. **Bank charge without supporting docs stays `invoice_missing`.** WeWork `CC-4412`. No Handle to `ap`.
5. **Canonical identity: same AWS bill from two sources is one invoice.** `test_aws_email_portal_card_is_one_canonical` and `test_aws_bill_from_two_sources_is_one_invoice` stayed green. Registry is now disk-backed so a second process sees the same `canonical_id`.

## What this session wrote

- Full `office/bots/{email,stripe,bank,books}/BOT.md` and Profile md
- Kernel persistence: `.cfo/invoice_ingestion/registry.py`, `.cfo/tools.py` overlay, `.cfo/atomic_json.py`
- Client webhook/poll → packet → Handle intent glue: `office/source_wakes/`
- Slug-map Profile `stripe.payout` remains `""` (Constitution: do not invent a Display name)
- Roster connectors: `bank-feed` on `bank`, `edi` on `books`

## Not live-proven

Pi was not bound. `sendPeerHandle` in the session 01 extension returns null without `HARNESS_V2_ROOT`. Accept ≠ complete was not exercised on a live lane.
