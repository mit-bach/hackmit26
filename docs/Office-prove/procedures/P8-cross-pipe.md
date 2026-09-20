# P8 — Cross-pipe identity

**Job.** One vendor bill keeps the same Kernel id through intake → match → pay-run → cash tick → close fact → audit sample. One customer cash event keeps the same id through remittance → apply → collect-or-not → cash tick → forecast actual. If AR and cash both interpret the same deposit from scratch, T11 HARD/SOFT as 02 says. Close locking is still BLOCKED on `$12.40`; that residual must be the same bank line id, not a second story.

**Owns.** Nothing new. Reads the month instance Handle graph.

**Must not.** Start a new company. Merge ids. Demo MSG-S12. Forecast from unreconciled GL while claiming trusted cash.

**Coverage claimed.** T11 rows; pipe INTENDED table G.

**Preconditions.** Month instance with P1–P5 attempted. If a pipe HARD-skipped, P8 can still prove the identities that exist and name the break.

**Instance.** The month instance. Do not clone mid-graph. If you need a clean try, `month-rN+1` replay P1–P5 then P8.

---

## S01 — Pick the vendor identity

- Stimulus: none. From CHECKPOINT.md and Kernel, choose `invoice_id` that `tools.get_invoice` finds
- Must not: INV-S12
- Write: `VENDOR_ID=...` in CHECKPOINT.md
- HARD if: no such id. Replay P1/P2. P8 cannot start on a marker

---

## S02 — Trace vendor Handle chain

Follow files, do not trust chat memory:

1. email or books Handle → ap (bill)
2. ap → ctl-pay review-match
3. pool / pay weekly-pay-run includes or excludes per HOLD
4. pay → ctl-pay review-pay if it was payable
5. pay → cash executed false if released
6. cash tick same id / same wire
7. close pack mentions the id or legitimately omits HOLD
8. audit sample may include it

Each hop: RUNS if Handle or Kernel state exists without throw. INTENDED if the id never forked.

HARD: two Kernel ids for one PDF; pay executed true; cash guessed a different vendor.

SOFT: story packet omits the id but tools returned — reporting remainder.

Ticks: T11 vendor.

---

## S03 — Pick the customer cash identity

- `payment_id` / remittance / bank txn from P3 S01
- Write `CASH_ID=...` and `INVOICE_IDS=...`

---

## S04 — Trace customer chain

1. email remittance or stripe charges → apply
2. apply posted or ctl-cash
3. collect did not dun if this payment was a new deposit at as-of
4. collect send only for still-open other invoices, if any
5. cash ticks the same bank line
6. story/forecast actual uses aging after apply, not pre-apply lie

HARD: cash re-guessed the customer (T11). Collect dunned the paid invoice.

INTENDED: one picture.

Ticks: T11 customer.

---

## S05 — $12.40 is the same line

- `TXN-2026-09-015` in cash rec, close gates, and story (as UNLOCKED/BLOCKED), not MATCHED, not a second txn id
- HARD if close BLOCKED on a different invented residual
- Ticks: T12 product law

---

## S06 — Harbor / cross-period if present

- If Harbor Electric exists in the pack: accrual method reuse only with current evidence (P5 S02). P8 only checks the vendor id is the same as last period’s object, not a renamed cousin
- SKIP if not in pack

---

## S07 — Audit sampled the same ids

- Operational audit lists include VENDOR_ID and/or CASH_ID as samples or explicitly out of sample
- Must not: ground truth
- SOFT: audit never saw them and did not say why
- Ticks: one invoice across pipes (corpus judged demo)

---

## Done-when

- Bare min: S01–S02 RUNS for one vendor id with no fork, even if cash hop SKIP blocked-on-upstream
- INTENDED: vendor chain through cash+close+audit; customer chain through apply+cash; $12.40 same line; no dual interpretation

## Forbidden

New ids to make the graph look complete. Holdout. Board pack as the only artifact (a printout is not a chain).

## Restart

If S02 finds a fork, that is T11 HARD for identity (code/intake) or SOFT (model minted a second id while Kernel had one — if Kernel accepted two, HARD). New month instance after patch. Do not “merge in Memory.”
