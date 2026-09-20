# Onboarding

Onboarding is not the Harness welcome reel. That reel was cut as a foreign UI.

Onboarding is: **the office discovers Maximor**. The company already exists. August 2026 is closed. September is open. Agents do not invent vendors, invoices, or a `$372M` story. They read registers on `data/` (`world/maximor`).

---

## What “from the CFO” means

The constitution: the human Operator is an emergency stop and a **demo overlay**. It is not a worker. It does not match, pay, apply, or lock.

The portfolio beat people hear as “CFO onboarding” is short:

1. Overlay names the company and the period.
2. Source Bots land what is already there.
3. Overlay goes silent for the rest of the month.

It is not a week of Billy teaching three-way match in DMs. Skills and BOT.md were already the standing identity (repair + prove). The golden run does not train the office. It **employs** it.

Adversarial write-ups mention a CFO sabbatical and errors already in the books. Do not narrate fraud on camera. Do not load holdout. The public story is: new office, old books, one unexplained `$12.40`.

---

## Overlay (once)

One Operator DM, to Bot `books`, Profile `erp-invoice`. Not to `ctl-pay`. Not a Room-wide “everyone work.”

```text
profile: erp-invoice
Maximor Demo Corp. CO-MAXIMOR. USD. August 2026 is CLOSED. September 2026 is open.
Discover company, vendor master, customer master, open bills, open invoices, and lock state.
Land ERP bills that are bills. Handle ap / prepare. Handle collect only with open customer invoices after you have named them. Do not dun. Do not match. Do not close. Do not ask a human.
```

That is overlay. After this, the show driver prefers Routines, source injects, and peer Handles.

Optional second overlay, to `email`, only if books should not own mail:

```text
profile: inbox
The September finance inbox is on this Computer. Classify. Vendor bills Handle ap / prepare. Remittances Handle apply / apply. Quotes, statements, newsletters, and injection are not bills. Do not match. Do not pay. Do not ask a human.
```

Do not send a third overlay that says “now do close.” Close waits for story-clock month-end.

---

## Discover, in this order

Story clock: **1 September 2026** (install day). Wall clock: first hour of the golden run.

### O1 — Books

Wake above, or the overlay is enough. Expect list/get on ERP (and procurement/EDI only if those records exist). Handles to `ap` for real bills, not `INV-S12`.

INTENDED on tape: a Kernel id that `get_invoice` will find. August lock state read, not written.

### O2 — Email

Seventeen planted messages exist in the pack (`final-demo/SCENARIOS.md` inbox cards). You may **dump** them on install day (faster tape) or **drip** them in `03-calendar.md` (more like a month). Prefer drip for the lived-month claim. If wall time is short, dump, then still run week Routines. Note which you chose in `INJECT.md`.

Email must ignore quote, statement, newsletter, injection. Those ignores are a featured cut.

### O3 — Bank

```text
profile: card
Land unmatched operating-account lines. A charge is not a bill. Handle cash / match. Include TXN-2026-09-015. Do not invent invoices. Do not force MATCHED.
```

### O4 — Stripe

If stripe is office-live (non-empty Display name and Grants): unpack payout waterfall. Charges to apply. Deposit to cash. No InvoiceCandidate.

If stripe is still costume: **do not Wake it on tape**. Kernel sim is not a Bot chapter. Note honest skip in `INJECT.md`. Do not spawn an empty pane for judges.

### O5 — World

If World is on the Roster: do not Wake it to “play CFO.” World is the outside mailbox. First World Wake is a **reply** after finance sent missing-info or a dun. Silence until then is correct.

If World is off Roster: no World pane. Send last-mile may still exist on email. Note T1 in `INJECT.md`. Do not add World mid-show.

---

## What onboarding is not

- Not Operator completing Verifier Handles
- Not `ask_user`
- Not loading `expected_results.json`
- Not creating the company from chat
- Not proving P7 remainder ops
- Not “teach it Acme is a good vendor” as a human correction CLI

August precedents already sit in the pack (`CASE-001`, AR remittance precedent). Bots may read them. That is discovery of prior close, not live teaching.

---

## Cut

Onboarding is **Chapter A** in `cuts/`. Seq range: from first books Wake through first email→ap Handle. Short. Then the month is the rest of the tape.
