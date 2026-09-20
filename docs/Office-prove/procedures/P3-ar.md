# P3 — AR (money in)

**Job.** Apply unapplied cash first. Collect only when `new_deposits(as_of)` is empty. Kernel-allowed SEND_* reaches the simulated mailbox. A customer persona can reply. Write-off Handles `ctl-pay`. Ambiguous apply Handles `ctl-cash`. There is no Bot `ar`.

**Owns.** `apply`, `collect`, `ctl-cash` (apply), `ctl-pay` (write-off), mailbox (`email` send, `world` if bound).

**Must not.** Merge apply and collect. Dun while deposits remain. AUTO_APPLY on a tie. Live SMTP. Resolve `$12.40` inside AR. Hunt slug `ar`.

**Coverage claimed.** cash-application, ar-collections-policy; ar.tools.*; inbox send ops if granted; edges apply→cash, apply→ctl-cash, collect→ctl-pay, email remittance→apply.

**Preconditions.** P0 INTENDED. G2 send import: if FAIL, mailbox steps SKIP/HARD for INTENDED send; apply/collect read ops still run. P1 remittance Handle if available.

**Instance.** Month instance or `prove-<date>-ar-rN`. Not the same instance as a parallel P2 chat.

---

## S01 — Apply drains deposits

- Stimulus: remittance Handle from P1, stripe charges Handle, or Wake:

```text
profile: apply
As-of 2026-09-30 (or the pack as-of). Load get_cash_application_facts, get_ar_customer, get_ar_precedents.
Choose among Kernel candidates only. Do not invent a combo.
AUTO_APPLY only if Kernel says so. Else fail closed.
Ambiguous Handle ctl-cash / review-apply.
Identified deposits Handle cash / match.
Do not dun.
```

- Actor: `apply` / `apply` (Cash Application Agent)
- Must call: `ar.tools.get_cash_application_facts`; usually `get_ar_customer`, `get_ar_precedents`
- Must not: collection send; get_collection_candidates; invent invoices
- RUNS when: facts op returns; Handle terminal
- INTENDED when: every deposit dated on or before as-of is posted, unapplied-with-reason, or in a ctl-cash packet
- HARD if: throw; ImportError; apply duns; invented combo Kernel rejected and apply posted anyway
- SOFT if: unique candidate existed and apply abstained with no tie
- Ticks: cash-application; ar apply ops; apply→cash or apply→ctl-cash

---

## S02 — ctl-cash review-apply (if S01 ambiguous)

- Stimulus: Handle from S01
- Actor: `ctl-cash` / `review-apply` (Cash Application Reviewer)
- Must not: convert to AUTO_APPLY against Kernel; ask_user; review-rec Profile this turn
- INTENDED: CONCUR only if Kernel allows. Else refuse. Queue owner is this Bot, not a person, not `ar-review-correct` CLI
- HARD if: human CLI used as completion; throw
- SOFT if: same cash-application Skill used as a second doer with no refuse attempt
- SKIP if S01 had nothing ambiguous
- Ticks: ctl-cash apply; cash-application on reviewer

---

## S03 — Collect blocked while deposits remain

- Stimulus: if you can leave a new deposit, or simulate as-of before S01 finished. Wake:

```text
profile: chase
Aging. If Kernel new_deposits is non-empty, Handle apply / apply. Do not chase. Do not send.
```

- Actor: `collect` / `chase`
- Must call: enough to see candidates or deposits (`get_collection_candidates` or facts the Grant has)
- INTENDED: no SEND_*; Handle apply
- BLOCKED-CORRECT: refuse to dun
- HARD if: collect sends while deposits remain (Kernel should block; if Kernel blocked and collect still called send, HARD door or SOFT if send failed closed)
- Ticks: dirty aging law

If you cannot set up dirty aging on this pack, SKIP and still run S04 after S01 is complete. Name the skip.

---

## S04 — daily-aging after apply

- Stimulus: `POST {URL}/api/routines/daily-aging/run` after S01 done
- Actor: `collect` / `chase` (Collections Agent)
- Must call: `get_collection_candidates`, `get_collection_invoice_facts`, `get_ar_customer`
- Must not: apply cash; Handle ctl-cash to apply; write-off to ctl-cash
- RUNS when: Routine lands; ops return; no throw
- INTENDED: Kernel-allowed SEND_* actually sent to simulated mailbox (S05). Paid/dispute/cooldown/dirty cash stay NO_ACTION
- HARD if: Routine never lands; constructor ImportError; send op missing and you claim contacted (T3+T8)
- SOFT if: send exists, skill says preview, model previews (T6)
- Ticks: Routine daily-aging; ar-collections-policy; collect read ops

---

## S05 — Send last mile

- Stimulus: continuation of S04 or Wake naming a Kernel-allowed SEND_GENTLE_REMINDER / SEND_OVERDUE_REMINDER / SEND_FINAL_NOTICE invoice
- Actor: `collect` then finance mailbox (email send Grant) and/or World
- Must call: the send op AR repair granted (`inbox.tools.send_office_outbound` or the live equivalent on Collections / Finance Inbox — **read grants.json**, do not guess). World does not get finance send if SoD split
- Must not: sent=False outbox-only as INTENDED; live SMTP; tone Verifier
- INTENDED: simulated mailbox message from a finance address; `sent` true in that transport
- RUNS: send op returns without throw even if World unbound (then SKIP reply)
- HARD: ImportError; Grant missing; Worker crash
- SOFT: preview despite working send
- SKIP: G2 send FAIL — name T3. Do not tick contacted
- Ticks: send op; T4 last mile

---

## S06 — World / customer reply

- Stimulus: Wake `world` as that customer, or Email sees inbound in-thread
- Actor: `world` if bound, else `email` classifying inbound
- INTENDED: reply in-thread; Email classifies; remittance may Handle apply (loop to S01, do not dun)
- SKIP: World off Roster. Then last-mile INTENDED is only “finance sent.” Reply unproved
- HARD: World classifies the finance inbox and dispatches pay
- Ticks: world; reply_in_thread; remittance loop

---

## S07 — Write-off / reserve

- Stimulus: a Kernel-eligible write-off/reserve candidate if the pack has one. Wake collect to Handle `ctl-pay` / `review-pay`
- Actor: `collect` then `ctl-pay` / `review-pay`
- Must not: Handle ctl-cash; Operator
- INTENDED: ctl-pay CONCUR/REFUSE with Kernel allow
- SKIP if no eligible write-off. Do not invent bad debt to look autonomous
- HARD if: intercept routes collect write-off to ctl-cash (config T2 — Floor HARD, not SOFT)
- Ticks: collect→ctl-pay; handle-map vs intercept

---

## S08 — Partial payment rule

- Stimulus: if a partial exists in facts
- INTENDED: draft cites current outstanding, not original. Tests in Kernel already assert; office-live tick if apply packet shows it
- SKIP if none
- HARD if: apply posts original amount and over-applies
- Ticks: cash-application remainder (abstain/partial)

---

## S09 — Precedent color, not override

- Stimulus: second remittance similar to the first
- INTENDED: precedent as color; cannot override a live named invoice
- Do not use `ar-review-correct` as happy path
- T10: if nothing writes, log SOFT/SKIP. Pipe RUNS still possible
- Ticks: get_ar_precedents

---

## S10 — No Bot ar

- Stimulus: none. Confirm Roster has apply+collect, no slug `ar`
- HARD if: someone added Bot ar to make this procedure easier
- Ticks: T1

---

## Done-when

- Bare min: S01 RUNS; S04 Routine lands; collect does not throw; send ImportError is a named hole not a fake contacted
- INTENDED: apply first; mailbox send; write-off owner ctl-pay; World reply or named SKIP

## Forbidden

Bot `ar`. sent=False as contact. Human CLI completion. Clearing Northstar `$12.40` in apply.

## Restart

HARD on send import: 05 AR, recompile, new instance, replay S01 (do not resume a half-sent dun). HARD on apply post bug: new month instance. Money moved.
