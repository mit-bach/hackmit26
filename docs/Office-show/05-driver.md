# Show driver

The show driver is a Cursor agent (or Billy by hand) that **runs the calendar**. It is not a specialist Bot. It is not the prove operator.

Specialist Bots never read this directory.

---

## What you tell a Bot

Always start with `profile: <key>`. Then **open item language**.

Good:

```text
profile: prepare
Open bill INV-001. Three-way match. You do not pay. APPROVE-shaped drafts Handle ctl-pay / review-match. HOLD stays out of the pool. Never ask a human.
```

Bad (prove leftover):

```text
profile: prepare
Call tools.get_invoice, tools.get_purchase_order, tools.get_goods_receipt, tools.find_duplicate_invoices, tools.get_case_evidence.
Stop after the tool returns.
```

The Bot already has Grants. Naming every op freezes T7 onto the tape and looks like a unit test.

Good Routine: HTTP fire only. The Roster already has the prompt. Do not rewrite weekly-pay-run in a DM.

Good World:

```text
profile: (World default)
You are the customer on thread <id>. Finance mailed you. Reply in-thread as that company. Do not classify the finance inbox. Do not pay Maximor's vendors.
```

---

## What you never tell a Bot

- Call this Catalog op (unless overlay is unsticking a hang **and** you will abort the goose — usually abort instead)
- Concur as Operator
- Mark CLOSED
- MATCHED on `TXN-2026-09-015`
- Load ground truth
- Ask a human
- Union two Profiles
- “Look autonomous” / invent amounts

---

## Operator overlay budget

Maximum overlay DMs on a clean golden run:

1. Books onboard (required)
2. Email onboard (optional if books should not own mail)
3. Bank land lines (if bank will not Wake from a Handle)
4. Stripe unpack (only if office-live)
5. Featured `ap` Wake for `INV-001` **only if** email Handle did not already carry it
6. Featured `cash` Wake for Helios + Northstar **only if** bank Handle did not already carry them

Everything else: Routine or peer Handle.

If you exceed ~8 Operator DMs, you are driving AP by hand. Stop. That tape is a copilot demo.

Verifier Bots: **zero** Operator DMs. They only see peer Handles.

---

## Spawn

Spawn `email`, `ap`, `ctl-pay` before W1. Spawn `pay`, `apply`, `collect`, `cash`, `ctl-cash` before W2/W3. Spawn `close`, `ctl-books`, `story`, `audit` before ME. Spawn `world` only when a reply is due.

Do not eager-bind all 15 at seq 0 unless you want a mosaic of idle faces. Lazy + timely spawn looks like work arriving.

---

## When a Bot does the wrong job (no throw)

This is prove SOFT. On golden:

- If fail-closed still holds (HOLD, BLOCKED, no send while deposits): **keep**. That may be INTENDED.
- If the Bot invented an amount or MATCHED `$12.40`: **abort**.
- If the Bot previewed a dun and send exists: you may fire **one** follow-up Wake in business English (“Kernel allowed SEND_OVERDUE_REMINDER on {id}. Contact the customer in the simulated mailbox.”). If it still previews, skip collect as a cut. Do not edit the Skill on this instance. Note for later prove.

Do not classify 40 SOFT rows into protocol.

---

## Parallel

No. One golden instance. One driver chat. Pipes move in story order. Parallel prove (AP ∥ AR) does not apply here. Cash must see apply/pay identifiers from **this** desk.

---

## Driver checklist per fire

1. Story time written
2. `profile:` present if DM
3. Wait for turn.end
4. Read Handle to/from, not the model’s claim
5. `$12.40` still unexplained
6. Next calendar cell only
