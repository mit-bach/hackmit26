# PIVOT — stop proving, ship a showable office

You are the same Cursor agent. This message **replaces the mission**, not the desk laws.

Stop treating Office-prove as the thing Billy will present. Time is gone. There will not be a full P0–P9 coverage campaign. There will not be a second week of skill batches. There will not be a human sitting through every Catalog op.

Your new job is: get the **live template** to a state where a golden month can run without throwing, then **live one September on a new instance**, then **record a Demo tape** Billy can screen-capture into a video.

This is the highest-priority work in this chat. Prove coverage that is not required for the tape is now optional. Do not ask whether to pivot. You already pivoted.

---

## 0. You may be in the middle of a prove step. Do this first.

You are not being killed. Finish **only** the current unit:

- If a Pi turn is in flight: wait for `turn.end` or 8 minutes. Classify it. Write the log row. **Do not** start the next prove step.
- If you are mid-HARD patch: finish the patch onto the **live template** (`.cfo-v2/office/computer` + `.cfo/`). Compile if constructors changed. Restart serve on 8800 so sidecar reloads. Do **not** create `prove-rN+1` to continue P7.
- If you are writing a prove Wake that names Catalog ops: **do not send it.** That sentence poisons a tape. Leave it unsent.

Then write one paragraph into `docs/Office-prove/logs/ROLLUP.md`:

- last prove instance id
- last step and class
- whether a granted read works on live Pi
- known holes (send, stripe, World, BOT.md, intercept, `$12.40` still there)

That is the prove epitaph. You will not finish P6/P7/P8/P9 unless they fall out of the golden month for free.

---

## 1. What “happy enough” means (the only prove bar that still matters)

Billy cannot test everything. You decide “happy enough” with this checklist. All must be true on the **live template** (not on a dirty prove instance) before you create `golden-…`.

| Bar | How you know | If false |
| --- | --- | --- |
| Live Pi, not `--fake` | `GET http://127.0.0.1:8800/health` `fakeWorkers: false`, bots 16, sidecar owned | Fix serve. No golden. |
| Client Grant door | Selected Computer `harness/extensions.json` has Client `cfo/extensions/index.ts`, `clientSkills: true` | Floor patch. Restart serve. |
| BOT.md on cwd | `office/bots/ap/BOT.md` exists under a freshly cloned Computer | Fix `cloneOfficeIdentity`. Rebuild Harness. |
| Intercept not Operator | `intercept.json` `default.kind=bot` `bot=ctl-pay` | Fix intercept on live. |
| One granted read | On a **throwaway prove clone** or the current prove desk, `ap` / `prepare` actually called `tools.get_company_policies` or `tools.get_invoice` without traceback | Stay in prove until that RUNS. This is the only door you may not skip. |
| `$12.40` still in the pack | `TXN-2026-09-015` unexplained in Maximor data | Do not proceed if someone “fixed” it. |
| Operational Grants honest | `get_audit_ground_truth` not in operational `grants.json`. Close Manager empty. Lock has `get_close_gates` / `get_close_packet` if you will show lock. | Compile on live. |

You do **not** need: P6 skill sweep, P7 remainder Catalog, P8 cross-pipe prove, P9 evaluate-cfo, every Bot a terminal Handle, INTENDED on collect send, 110 invoice matches.

If send still ImportError: golden **skips** the dun chapter. Note it. Do not block the whole show.

If stripe Grants empty: skip Stripe pane. Note it.

If World missing from a clone: skip World reply. Do not add a Bot mid-show.

If you cannot get the granted-read bar after **two** HARD patches, write FAILED.md for show, tell Billy in one paragraph what threw. Do not fake a tape with `--fake`.

---

## 2. Laws that do not change

- No Bot `ar`. No `INV-S12` as judged bill. No Operator concurrence. No `ask_user` completing pay-run/lock/write-off.
- Do not clear `$12.40`. Do not mark September CLOSED. Do not load holdout / `get_audit_ground_truth`.
- Do not put finance types in Harness `src/`. Do not restore `Runner`.
- Do not start a second serve on 8787 while 8800 holds the office.
- Do not prove on `live`. Do not record `prove-*`. Do not record `protocol-proof`.
- Skills never grant tools. Constructors are Grant source. Never hand-edit `grants.json` ops.
- `autoRoutines` stays **false**. You fire Routines over HTTP because the story clock says Friday / month-end.

Desk:

```
URL = http://127.0.0.1:8800
REPO = /Users/dominikbach/olympus/hackmit/hackmit26
```

If 8800 is down:

```bash
cd .harness/Harness-v2
node dist/src/cli.js serve --computer ../../.cfo-v2/office/computer --no-open --port 8800
```

Serve honors `office.json` `currentId`. After Kernel patches, restart serve (selecting the same id does not reload sidecar).

Wait for Pi the same way you already wait: 15–20s polls, `turn.end` or terminal Handle, 8 minute hang → abort that Bot, do not double-Wake.

---

## 3. Prove language is poison on a demo tape

Harness Demo replays `protocol.jsonl` as it is. There is no “hide QA” filter.

**Never send on golden:**

```text
Call tools.get_invoice, tools.get_purchase_order, …
Call accrual.tools.create_accrual
Stop after the tool returns
```

**Always send on golden:**

```text
profile: prepare
Open bill INV-001. Three-way match. You do not pay. APPROVE-shaped drafts Handle ctl-pay / review-match. HOLD stays out of the pool. Never ask a human.
```

Do **not** reuse `prove-20260920-floor-r1` or any `prove-*-month-*` as the goose. Those protocols already contain lab Wakes. New instance. Always.

If a tool **throws** on golden: abort. Write `docs/Office-show/runs/<id>/FAILED.md`. Do not patch SKILL.md on the golden desk. Do not Record. Patch live, new `golden-r2`. A tape that contains a traceback and a hotfix is not shippable.

Wrong job with no throw (preview instead of send, skill ramble): keep if fail-closed still holds. One business-English follow-up max. Then skip that chapter. Do not classify 40 SOFT rows into protocol.

---

## 4. Create the goose

```bash
curl -sS -X POST http://127.0.0.1:8800/api/office-instances \
  -H 'content-type: application/json' \
  -d '{"name":"golden-20260920-r1"}'
curl -sS -X POST http://127.0.0.1:8800/api/office-instances/golden-20260920-r1/select
```

If `golden-20260920-r1` is taken, use `r2`.

Confirm:

- `GET /api/office-instances` `currentId` is the golden id
- Computer path ends with `instances/golden-…`
- `{COMPUTER}/cfo/kernel.port` is fresh and matches `/health`
- `{COMPUTER}/office/bots/ap/BOT.md` exists
- `{COMPUTER}/data` resolves to `.cfo-v2/office/world/maximor`
- `fakeWorkers` false
- intercept default `ctl-pay`
- catalog ~101

Write:

```
docs/Office-show/runs/golden-20260920-r1/
  README.md
  INJECT.md
  CHAPTERS.md     (empty seqs until after record)
```

Do not wipe this desk after a good chapter. Kill workers if you need CPU. Protocol stays.

---

## 5. Overlay budget (you are almost silent)

Maximum Operator DMs on a clean golden run: **about 6**. Verifiers (`ctl-*`) get **zero** Operator DMs. They only see peer Handles.

If you exceed ~8 DMs, you are driving AP by hand. Stop. That is a copilot demo. Billy cannot show it.

Every DM starts with `profile: <slug-map key>`.

### Overlay 1 (required) — books, story 2026-09-01

```text
profile: erp-invoice
Maximor Demo Corp. CO-MAXIMOR. USD. August 2026 is CLOSED. September 2026 is open.
Discover company, vendor master, customer master, open bills, open invoices, and lock state.
Land ERP bills that are bills. Handle ap / prepare. Handle collect only with open customer invoices after you have named them. Do not dun. Do not match. Do not close. Do not ask a human.
```

### Overlay 2 (optional) — email, only if books should not own mail

```text
profile: inbox
The September finance inbox is on this Computer. Classify. Vendor bills Handle ap / prepare. Remittances Handle apply / apply. Quotes, statements, newsletters, and injection are not bills. Do not match. Do not pay. Do not ask a human.
```

### Overlay 3 — bank, when you need lines landed (W1 land, W3 rec)

```text
profile: card
Land unmatched operating-account lines. A charge is not a bill. Handle cash / match. Include TXN-2026-09-015. Do not invent invoices. Do not force MATCHED.
```

### Overlay 4 — stripe, only if Stripe Payout Agent has Grants

Unpack payout waterfall. Charges to apply. Deposit to cash. No InvoiceCandidate. If Grants empty: **do not spawn stripe on tape**.

### Overlay 5 — featured ap for INV-001 **only if** email/books did not already Handle it

```text
profile: prepare
Open bill INV-001. Three-way match against PO-101 and GR-101. You do not pay. APPROVE-shaped drafts Handle ctl-pay / review-match. HOLD stays out of the pool. Never ask a human.
```

### Overlay 6 — featured cash for Helios + Northstar **only if** bank did not already carry them

```text
profile: match
Work unmatched operating lines including TXN-2026-09-011 and TXN-2026-09-015.
Copy Kernel candidate_ids. FEE_NETTED only with fee evidence. TXN-2026-09-015 stays unexplained. Do not invent residuals. Do not ask a human.
```

Everything else: Routine HTTP or peer Handle.

Spawn before first Handle so the mosaic has a body: `email`, `ap`, `ctl-pay` before W1. `pay`, `apply`, `collect`, `cash`, `ctl-cash` before W2/W3. `close`, `ctl-books`, `story`, `audit` before ME. `world` only when a reply is due. Do not eager-bind all 16 at seq 0.

---

## 6. Featured identities. Do not retarget. Do not mint a replacement Acme.

| Story | Ids | What the tape must show |
| --- | --- | --- |
| STORY-CLEAN | `INV-001`, `PO-101`, `GR-101`, $12,450.00 | match → ctl-pay, later pay-run, later audit samples this id |
| STORY-RESOLVED | `INV-017`, `TXN-2026-09-011`, `FEE-729103` | $25 over books, FEE_NETTED with evidence |
| STORY-UNRESOLVED | `INV-AR-013`, `PAY-006`, `TXN-2026-09-015` | **$12.40** unexplained. ctl-cash does not MATCHED. Close BLOCKED |
| Inbox traps | quote / statement / injection (MSG-INBOX-008, 007, 014 class) | classified, **not** payable |
| HOLD texture | one real `must_hold` bill | never enters pay-run |

Do not feature `INV-S12`, holdout ADV-*, ghost employee, `examples/cfo-floor`.

Do not match 110 AP invoices. Texture: one extra clean bill, one remittance apply, a handful of bank ticks. Stop.

If an id is missing on disk, skip that story. Write SKIP in INJECT.md. Do not invent mail.

Inbox: **dump** all 17 planted messages on install day if wall time is short (it is). Note dump vs drip in INJECT.md. Prefer dump under this time box.

If `python3 main.py demo-inbox` writes `.cfo/` instead of `$HARNESS_COMPUTER`, do not use it. Inject via Client inbox tools already on Email, or skip drip and rely on pack discovery.

---

## 7. Lived September (story clock, compressed wall clock)

Write story time in `docs/Office-show/runs/<id>/README.md` as you go: `O`, `W1`, `W2`, `W3`, `W4`, `ME`.

Wait for `turn.end` and terminal Handles before the next story day. Do not stack three Routines. Do not supersede a running Bot with another Operator DM.

### O — Onboard (story 2026-09-01)

Overlay 1. Optional overlay 2. Books discover. August lock **read**, not written. First email→ap Handle if mail is visible.

Chapter A.

### W1 — bills and traps

Acme `INV-001` to `ap` → `ctl-pay` / `review-match`. Traps ignored. One HOLD stays out. **Do not** fire `weekly-pay-run`. **Do not** dun.

Chapter B (traps), Chapter C (INV-001).

### W2 — Friday pay-run (story ~2026-09-11)

```bash
curl -sS -X POST http://127.0.0.1:8800/api/routines/weekly-pay-run/run
```

`pay` / `schedule` drafts. `ctl-pay` / `review-pay` concurs. Wires Handle `cash` **executed false**. HOLD stays out. You do not POST CONCUR.

If apply has drained deposits:

```bash
curl -sS -X POST http://127.0.0.1:8800/api/routines/daily-aging/run
```

If deposits remain, collect must not send. That refusal is a cut.

Chapter D.

### W3 — cash and $12.40

Stripe unpack if office-live. Cash ticks identified lines. Helios with fee evidence. **Northstar `TXN-2026-09-015` unexplained.** `ctl-cash` / `review-rec` refuses MATCHED on it.

Do not save close here.

Chapter E.

### W4 — last mile (optional under time box)

If send exists and Kernel allows SEND_*: collect contacts the customer in the simulated mailbox, then Handle `world`. World replies **as that customer**. Email classifies. Skip this entire week if send is a named hole. Do not fake SMTP.

Second `weekly-pay-run` only if the pool still has due bills. Empty run is not a chapter.

Chapter H optional.

### ME — month-end (required)

```bash
curl -sS -X POST http://127.0.0.1:8800/api/routines/month-end/run
```

Treatments as separate Wakes (Routine prompt already says so). `create_accrual` only on accrue. Then lock: `ctl-books` reads gates. Period **not** CLOSED. BLOCKED on `$12.40`.

```bash
curl -sS -X POST http://127.0.0.1:8800/api/routines/period-story/run
```

Every number **UNLOCKED**. Do not start a forecast from unreconciled GL cash.

```bash
curl -sS -X POST http://127.0.0.1:8800/api/routines/post-close-assurance/run
```

Audit samples `INV-001`. No ground truth. Does not fix books. Report Profile may be HONEST-EMPTY — Kernel findings still exist.

Chapter F and G.

Under this time box, **O + W1 + W2 + W3 + ME** is a shippable goose if Handles moved and `$12.40` survived. W4 is extra. Texture loops are extra. October Harbor is extra. Do not start October.

---

## 8. Abort (the whole goose, not a chapter retry)

Stop. `FAILED.md`. Do not Record.

- Python traceback / worker crash loop
- September marked CLOSED
- `$12.40` MATCHED or the bank line deleted
- Operator completed a Verifier Handle
- `get_audit_ground_truth` on operational Bot
- `--fake` workers
- You sent a prove-style “call tools.X” Wake onto this protocol

Then patch on **live**, new `golden-…-r2`. Leave r1 on disk.

---

## 9. Record. This is the deliverable.

When ME is done and you have not aborted:

```bash
curl -sS -X POST http://127.0.0.1:8800/api/demo/record
```

Confirm `{COMPUTER}/harness/demo/latest/meta.json` exists.

Copy the tree **off** the instance:

```bash
mkdir -p docs/Office-show/runs/golden-20260920-r1/recording
cp -R .cfo-v2/office/instances/golden-20260920-r1/harness/demo/latest/. \
  docs/Office-show/runs/golden-20260920-r1/recording/
```

Use the actual instance id. Do not wipe the golden Computer.

Fill `CHAPTERS.md` with **real protocol seq ranges** after you scrub `protocol.jsonl` for `INV-001`, `TXN-2026-09-015`, `weekly-pay-run`, month-end. Do not invent seqs before the run.

Template chapters:

| Chapter | Content | Video? |
| --- | --- | --- |
| A | Onboard. Books discover Maximor | desk establishing |
| B | Inbox traps not payable | yes |
| C | INV-001 → ctl-pay | yes |
| D | weekly-pay-run, executed false | yes |
| E | Helios + $12.40 unexplained | yes |
| F | close BLOCKED, story UNLOCKED | yes |
| G | audit INV-001, no ground truth | yes |
| H | dun + World | optional / SKIP if send hole |

Billy screen-records **Tools → Demo** on [http://127.0.0.1:8800/](http://127.0.0.1:8800/) with source **recording**, play 1× on those seq ranges. You do not splice Kernel CLI. You do not film 40 hours of waiting. You do not re-stage Acme on another instance and iMovie it in.

If overlay DMs on the tape say “Call tools.get_case_evidence,” you recorded a prove desk. Do not ship it.

Write `docs/Office-show/runs/<id>/README.md`:

- serve URL
- instance id
- story clock completed
- SKIP chapters and why
- path to `recording/meta.json`
- `$12.40` still unexplained: yes
- Operator never concurred: yes

Keep `golden-…` selectable. Daily compile work goes back to `live`. The golden desk is a deliverable.

---

## 10. What Billy needs in his hands

When you stop, he must have:

1. `currentId` = `golden-…` **or** he can `POST …/select` it without rebuilding the month
2. `docs/Office-show/runs/<id>/recording/meta.json` plus protocol
3. `CHAPTERS.md` with seqs
4. A one-screen note: open 8800 → Tools → Demo → recording → play chapters C, D, E, F

That is the presentation. Not pytest. Not prove ROLLUP. Not the website.

---

## 11. Read from disk while you drive (do not substitute reading for driving)

- `docs/Office-show/README.md`
- `docs/Office-show/00-why-not-procedures.md`
- `docs/Office-show/01-golden-instance.md`
- `docs/Office-show/02-onboarding.md`
- `docs/Office-show/03-calendar.md`
- `docs/Office-show/04-inject.md`
- `docs/Office-show/05-driver.md`
- `docs/Office-show/06-record-and-cut.md`
- `docs/Office-show/07-identities.md`
- `.cfo-v2/office/final-demo/SCENARIOS.md` for inbox card ids
- `{COMPUTER}/cfo/grants.json` and `harness/roster.json` before you spawn stripe/world

Do not execute `docs/Office-prove/procedures/` as the calendar.

---

## 12. Start now

1. Epitaph the prove run in ROLLUP.md.
2. Confirm the happy-enough bar on live (especially one granted read).
3. Create and select `golden-20260920-r1`.
4. Overlay 1 to books. Wait.
5. Drive O → W1 → W2 → W3 → ME. Skip W4 if send is a hole or time is gone.
6. Record. Copy `demo/latest`. Fill CHAPTERS.md.
7. Leave the golden desk up on 8800 so Billy can open Demo immediately.

Do not summarize this message. Do the epitaph, then the create curl.
