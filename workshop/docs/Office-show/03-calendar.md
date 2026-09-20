# Calendar — lived September

Wall clock is however long Pi takes (hours). Story clock is **September 2026**, compressed.

You do not wait seven real days between Fridays. You **say** it is Friday and fire `weekly-pay-run`. That is the manner change from prove: Routines are time, not coverage ticks.

Write story time in `runs/<id>/README.md` as you go: `W1-Mon`, `W2-Fri`, `ME`.

---

## Shape

```
O  Onboard          story 2026-09-01
W1 Week of Sep 1    bills, first match, first remittance, ignore traps
W2 Week of Sep 8    first Friday pay-run, wires, apply leftovers, aging
W3 Week of Sep 15   Stripe/Helios, cash rec, $12.40 unexplained
W4 Week of Sep 22   second pay-run if pool has more, collect send + World reply
ME Month-end        treatments, lock BLOCKED, story UNLOCKED, audit
```

October Harbor (`later_invoices.json`, `PR-2026-10-02`) is **optional Chapter G**, not required for the goose. If you run it, it is a new story week after ME, still on the same instance.

---

## Featured vs texture

**Must move (featured):**

| Story | IDs |
| --- | --- |
| STORY-CLEAN | `INV-001`, `PO-101`, `GR-101`, then pay/bank/audit/forecast |
| STORY-RESOLVED | `INV-017`, `TXN-2026-09-011`, `FEE-729103` |
| STORY-UNRESOLVED | `INV-AR-013`, `PAY-006`, `TXN-2026-09-015` ($12.40) |
| Inbox traps | quote, statement, newsletter, injection — classified, not payable |
| Quiet Harbor | `INV-AR-014` late pay, for story |
| Duplicate vendor decoy | `VEND-001` / `VEND-001-DUP` for audit, not as a “gotcha” you planted mid-show |

**Texture (a few, not 110):**

- One HOLD bill (price / missing GR) that never enters the pay-run
- One remittance apply
- One extra clean bill besides Acme so the pool is not a single line
- A handful of bank ticks that trust apply/pay identifiers

**Do not:**

- Match all 110 AP invoices
- Rec every 200 bank lines on camera
- Force every skill
- Second month-end to “retry CLOSED”

---

## W1 — bills and traps

Story: mail arrives. Email classifies. Acme lands. Traps ignored. `ap` matches `INV-001`. HOLD on a real `must_hold`. `ctl-pay` concurs the clean packet only.

Driver: drip or dump inbox (see `04-inject.md`). Do **not** fire `weekly-pay-run` yet. Do **not** dun. If a remittance is in the drip, `apply` may run. Collect still waits.

Wait for Handles to complete before W2.

---

## W2 — Friday pay-run and aging

Story: it is Friday 2026-09-11 (or the first Friday after enough CONCUR).

Fire:

```text
POST {URL}/api/routines/weekly-pay-run/run
```

`pay` drafts. `ctl-pay` / `review-pay` concurs. Wires Handle `cash` executed false. HOLD stays out.

If apply has drained deposits:

```text
POST {URL}/api/routines/daily-aging/run
```

If deposits remain, collect must Handle apply, not send. That refusal is a featured cut (dirty aging).

---

## W3 — cash and the $12.40

Story: mid-month rec.

Stripe unpack if office-live. Bank already handed lines. `cash` ticks identified deposits/wires. Helios FEE_NETTED only with `get_fee_evidence`. `TXN-2026-09-015` stays unexplained. `ctl-cash` refuses MATCHED on it.

Do not “save close” here.

---

## W4 — collect last mile and second Friday

If Kernel allows SEND_* and send exists: collect sends. World replies as that customer if bound. Email classifies the reply. Maybe apply.

Second `weekly-pay-run` only if the pool still has due bills. Skip if empty. An empty run is not a chapter.

---

## ME — close

Story: 30 September / 1 October close.

```text
POST {URL}/api/routines/month-end/run
```

Treatments as separate Wakes (the Routine prompt already says so). Then lock Handle. Kernel gates BLOCKED on `$12.40`.

```text
POST {URL}/api/routines/period-story/run
```

UNLOCKED on every number.

```text
POST {URL}/api/routines/post-close-assurance/run
```

Audit samples `INV-001`. No ground truth. Does not fix books.

---

## Waiting

After each fire: wait for `turn.end` and terminal Handles before the next story day. Do not stack three Routines. The mosaic should show one or two awake Bots, then handoff, then Verifier.

If a Bot is running, do not supersede with another Operator DM. Overlay stays silent.

---

## Abort

Throw, CLOSED with `$12.40` gone, Operator concurrence, `--fake`, ground truth: stop. `FAILED.md`. New golden instance. Do not record a poisoned protocol as the goose.
