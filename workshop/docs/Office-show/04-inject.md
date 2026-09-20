# What you inject

The World pack is already on `data/`. Injection is **time**: which objects become visible as mail, payouts, or Wakes on which story day. You do not rewrite invoices to make close look CLOSED. You do not plant holdout.

---

## Already on the desk (do not recreate)

Computer `data` → `../world/maximor` (clone preserves the symlink).

Present before any Wake:

- Company, vendors, customers
- AP invoices, POs, GRs, documents
- AR invoices, bank lines including `TXN-2026-09-015`
- 17 inbox specs (planted cards)
- Stripe sim events on disk
- August close pack (CLOSED)
- Policies, prior_cases seed, precedents

Bots **discover** these. The show driver does not paste JSON into chat.

---

## Allowed injects

| Inject | How | When | Looks like |
| --- | --- | --- | --- |
| Overlay DM | `POST /api/bots/books/messages` (and maybe email) | Onboard only | CFO overlay names company |
| Inbox drip | Kernel/demo inject of `full_inbox_specs()` onto **this** Computer’s inbox store, or Email list if already planted | W1 (dump) or spread W1–W4 | Mail arrived |
| Routine fire | `POST /api/routines/<name>/run` | Friday, aging, month-end | Calendar |
| Source Wake | Operator DM in **business** English, `profile:` first line | When a source has new objects | Bank file, Stripe payout |
| World reply | Wake `world` as the named counterparty | After finance sent | Customer/vendor answered |
| Spawn | `POST /api/bots/<id>/spawn` | Before first Handle if lazy | Pane exists |

If `python3 main.py demo-inbox` writes `.cfo/` instead of `$HARNESS_COMPUTER`, do not use it on golden. That is a prove T5 hole. Inject via Client inbox tools or a remap you already fixed.

Log every inject in `runs/<id>/INJECT.md` with story time and ids.

---

## Forbidden injects

- Prove Wakes that name Catalog ops
- SoD negative tests (“call create_accrual”)
- `INV-S12` / `MSG-S12` markers
- Holdout / `expected_results.json` / `ADVERSARIAL-SCENARIOS.md`
- `get_audit_ground_truth`
- close `--resolve`
- Editing `TXN-2026-09-015` or deleting the residual
- `--fake` workers
- Operator CONCUR on a Verifier Handle
- Hand-editing `grants.json`
- Changing SKILL.md mid-run
- Live Gmail/Stripe/ACH

---

## What you modify in the sandbox

| Layer | During golden | After a good record |
| --- | --- | --- |
| Kernel `.cfo/` | no | only if you abort and return to repair |
| Skills / BOT.md | no | only after abort + prove SOFT batch |
| World pack `data/` | no | never to clear `$12.40` |
| Instance inbox / runs / Handles | yes — this is the month | keep |
| Memory | yes — Bots may write | keep; this is T10 texture if it happens |
| intercept / roster | no | Floor repair on live, then new golden |
| protocol.jsonl | grows | record copies it |

The sandbox the Bots live in is the **instance Computer**. You do not modify the company to fit the video. You modify **when** work starts.

---

## Drip vs dump (inbox)

**Dump (faster):** all 17 messages visible at O2. Email classifies in one or two turns. Good if wall time is an afternoon. Risk: one giant Email chapter, then silence.

**Drip (more like a month):**

| Story day | Messages (from SCENARIOS inbox cards) |
| --- | --- |
| W1 | Clean Acme `MSG-INBOX-001`, quote `008`, injection `014`, statement `007` |
| W1–W2 | Price/no-PO style bills, remittance `019` |
| W2 | Duplicate resubmit `013`, PO/GR `005`/`006` |
| W3 | Payment received `009`, lunch `010` (ignore), credit memo `016` |
| W4 | Incomplete `011` / malformed `018` if still unused |

Exact spec function names live in `.cfo/inbox/fixtures.py`. Use planted IDs from `final-demo/SCENARIOS.md`. If a card is missing on disk, skip. Do not invent mail.

---

## Stripe and bank timing

Bank lines can exist from day one (they are in the pack). **Handle cash** in W3 so rec is a chapter, not a W1 pile-up. W1 may land lines without matching.

Stripe unpack: W3 with Helios. Not on install day unless you need a short tape.

---

## Volume without 110 Pi matches

The Computer panel can show `data/` counts. The website can show 110 invoices. The **tape** shows featured + texture. Judges who scrub protocol should see many Handles, not 110 identical APPROVEs.

If you want “large scale” in one extra cut: one Wake to `ap` “work the next open bill in the pack that is not INV-001,” two or three times. Stop. Do not loop 110.
