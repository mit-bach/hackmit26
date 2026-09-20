# P4 — Cash (bank vs books)

**Job.** Unmatched bank lines get Kernel candidates. `cash` copies a `candidate_id`. It trusts identifiers apply and pay already wrote. It does not invent fees, FX, or residuals. `$12.40` on `TXN-2026-09-015` stays unexplained. `ctl-cash` cannot CONCUR MATCHED on it. Period cannot be RECONCILED. Helios-class FEE_NETTED still needs Kernel fee evidence. Stripe is granted or not claimed office-live.

**Owns.** `cash`, `ctl-cash` / `review-rec`. Reads identifiers from apply/pay. Stripe/bank as sources.

**Must not.** Re-guess Acme vs the remittance. Force MATCHED. Relabel Northstar as a fee. Start the 13-week forecast here. Resolve holdout ADV residual into operational books.

**Coverage claimed.** cash recon skills; cash_recon.tools.*; edges cash→ctl-cash, cash→close, pay→cash, apply→cash, bank→cash, stripe→cash.

**Preconditions.** P0 INTENDED. For identifier INTENDED: P2 S09 and/or P3 S01 happened on **this** instance. If you are on a coverage instance without identifiers, you may still RUNS `get_match_candidates` and BLOCKED-CORRECT `$12.40`. You may not claim identifier trust.

**Instance.** Month instance. Not parallel with a second cash chat on the same Computer.

---

## S01 — Bind case / load a line

- Stimulus:

```text
profile: match
Load unmatched bank lines. Call cash_recon.tools.get_bank_transaction and get_match_candidates for each you work.
Copy a candidate_id. Do not invent a fee or residual.
Trust apply/pay identifiers. Do not re-interpret the counterparty from scratch.
```

- Actor: `cash` / `match` (Cash Reconciliation Preparer)
- Must call: `get_bank_transaction`, `get_match_candidates`
- May call: `get_ledger_entry`, `get_candidate`, `get_fee_evidence`
- Must not: InvoiceCandidate; invent cents; MATCHED on unexplained
- RUNS when: ops return; no throw
- INTENDED when: a line apply or pay already identified ticks without a second customer/vendor guess (see S02–S03)
- HARD if: throw; bind_case required as a Catalog op (it is not — if Bot hangs for bind_case tool, T8 HARD/SOFT: prompt vs sidecar session). Sidecar session setup is Floor. If get_bank_transaction always empty because case never bound, HARD T8/T5
- SOFT if: skill replays match_type taxonomy and still copies a legal candidate_id
- Ticks: cash recon ops; cash-reconciliation-method-selection; bank-reference-interpretation

---

## S02 — Tick an apply-identified deposit

- Stimulus: bank line that P3 applied. Continue S01 or Handle from apply
- INTENDED: same counterparty, no re-guess
- SKIP if this instance has no apply identifier. Name blocked-on-upstream
- HARD if: cash invents a different customer and Kernel posts it
- Ticks: apply→cash; T11

---

## S03 — Tick a pay-identified wire

- Stimulus: line from P2 S09
- INTENDED: same vendor wire, executed false still, rec tick
- SKIP if no pay identifier
- Ticks: pay→cash; T11

---

## S04 — Helios fee with evidence

- Stimulus: `TXN-2026-09-011` class FEE_NETTED if present in the pack
- Must call: `get_fee_evidence`
- INTENDED: FEE_NETTED only with Kernel fee evidence. Fee journal waits on ctl-cash
- HARD if: fee invented without evidence
- SKIP if Helios line not in pack
- Ticks: get_fee_evidence; reconciliation-evidence-validation

---

## S05 — Northstar $12.40

- Stimulus: `TXN-2026-09-015` (Northstar INV-AR-013 / PAY-006 books $12,400.00 vs bank $12,412.40)
- Actor: `cash` then `ctl-cash` / `review-rec`
- Must not: MATCHED; relabel as fee; delete the line; load holdout explanation
- INTENDED: UNEXPLAINED_DIFFERENCE. ctl-cash cannot CONCUR MATCHED. Close will stay BLOCKED
- BLOCKED-CORRECT: this is the product climax. Tick as pass of law
- HARD if: MATCHED; line missing; residual “explained” from holdout
- SOFT if: model writes a business story for the $12.40 but Kernel still unexplained — SOFT story, INTENDED/BLOCKED Kernel if rec state stays unexplained
- Ticks: $12.40 law; reconciliation-exception-investigation

---

## S06 — ctl-cash review-rec

- Stimulus: Handle `cash` → `ctl-cash` / `review-rec` for material rec / unexplained
- Actor: `ctl-cash` / `review-rec` (Cash Reconciliation Reviewer)
- Must not: review-apply this turn; force MATCHED; Operator
- INTENDED: CONCUR on legal ticks; refuse MATCHED on S05
- HARD if: Operator; throw; CONCUR MATCHED on $12.40
- Ticks: cash→ctl-cash; reviewer skills

---

## S07 — Trusted cash to close

- Stimulus: after legal ticks
- Actor: `cash`
- INTENDED: Handle `close` / `coordinate` with trusted cash path on **this Computer** `runs/`, not only `.cfo/runs/cash_recon/handles` Kernel JSON (T5)
- RUNS: Handle exists
- HARD if: only Kernel JSON handles and Harness `bot_await_turn` cannot see them, and you claimed office-live sign-off
- Ticks: cash→close; T2 Kernel vs Harness handles

---

## S08 — Stripe honesty

- Stimulus: read stripe Grant on this instance; if office-live, Handle deposit/charges from P1 S20
- HONEST: empty Grant → not office-live. Kernel `simulate-stripe` is P9/Kernel
- INTENDED if granted: unpack math, invoice_candidates 0, deposit to rec, charges to apply
- HARD if: costume Bot claimed office-live with empty ops
- Ticks: stripe edges or honest skip

---

## S09 — Investigate Profile (separate Wake)

- Stimulus: `profile: investigate` on a messy memo line, not on $12.40 to “solve” it
- Actor: `cash` / `investigate` (Cash Exception Investigator)
- Must not: union match+investigate; explain $12.40
- Ticks: reconciliation-exception-investigation; prior-period-precedent load

---

## Done-when

- Bare min: S01 RUNS; S05 BLOCKED-CORRECT; no throw; stripe honest
- INTENDED: S02/S03 identifier trust on this instance; Harness Handle to ctl-cash; trusted cash Handle close; $12.40 still unexplained

## Forbidden

Clearing $12.40. Holdout in operational books. Forecast starting here. Re-guessing counterparties to look done.

## Restart

HARD after a false MATCHED on $12.40: this instance is product-law poisoned. Restore data from World pack (new instance from template). Never “unmatch” by editing the bank line in Memory.
