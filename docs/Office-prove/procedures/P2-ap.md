# P2 — AP (money out)

**Job.** A real vendor bill becomes an open bill. `ap` proposes APPROVE or HOLD. `must_hold` wins. Approve-shaped drafts Handle `ctl-pay` / `review-match`. Payable ids sit in the pool. Routine `weekly-pay-run` wakes `pay` / `schedule`. Draft Handles `ctl-pay` / `review-pay`. Identified wires Handle `cash` with executed false. Unreceived period work Handles `close`. Nobody pays. Nobody executes ACH.

**Owns.** `ap`, `pay`, `ctl-pay`.

**Must not.** Merge ap and pay. Operator concurrence. send-as-bank. Bot `ap-investigator` (investigate is a Profile on ap).

**Coverage claimed.** three-way-match-analysis, ap-exception-investigation, superseded-document-handling, payment-prioritization, early-payment-discount-evaluation, prior-period-precedent (AP wearers); AP tools.*; scheduling.tools.*; handle edges ap→ctl-pay, ap→pay, pay→ctl-pay, pay→cash, ap→close.

**Preconditions.** P0 INTENDED. P1 S02 (or S17) produced a Kernel id. If not, P2 S00 injects from World pack (INV-001 class) via books/email, still not INV-S12.

**Instance.** Month instance or `prove-<date>-ap-rN`. Parallel with P3 only on another instance.

---

## S00 — Confirm Kernel bill

- Stimulus: none, or books/email Handle from P1. Prove agent calls nothing as Operator except a Wake if needed
- Observe: pick `invoice_id` where Kernel `tools.get_invoice` finds it. Write the id in CHECKPOINT.md
- HARD if: the only completed email Handle is INV-S12 not found (T11, T12). Inject a real bill. Do not proceed on the marker
- Ticks: identity

---

## S01 — Prepare three-way (clean)

- Stimulus: Handle from email/books, or Wake:

```text
profile: prepare
Open bill {invoice_id}. Load invoice, PO, GR, duplicates, case evidence, policies.
Propose APPROVE or HOLD. You do not pay. You do not concur.
If APPROVE-shaped, Handle ctl-pay / review-match. Await the Handle.
If HOLD, do not enter the pay pool.
```

- Actor: `ap` / `prepare` (AP Preparer)
- Must call: `tools.get_invoice`, and as needed `get_purchase_order`, `get_goods_receipt`, `find_duplicate_invoices`, `get_case_evidence`, `find_relevant_policies`, `get_company_policies`
- Must not: scheduling ops; create_accrual; ask_user; invent cents
- RUNS when: get_invoice returns; Handle complete without throw
- INTENDED when: clean Maximor match (INV-001 class) is APPROVE-shaped and Handled ctl-pay; Kernel evidence in the packet
- HARD if: throw; get_invoice not found and ap invents a total; ap “pays”
- SOFT if: Kernel evidence already APPROVE-shaped and skill restates must_hold for the whole turn (T6,T7) but packet is correct — RUNS tools, SOFT skill
- Ticks: AP tools; three-way-match-analysis; ap→ctl-pay

---

## S02 — ctl-pay review-match

- Stimulus: the Handle from S01. Spawn ctl-pay if lazy
- Actor: `ctl-pay` / `review-match` (AP Reviewer)
- Must call: enough RECORD/read ops the Grant still allows to refuse for a reason. If denylist stripped re-performance, the packet must still carry Kernel evidence; Verifier may only check completeness + Kernel allow
- Must not: rebuild the pay-run; ask_user; union review-pay
- RUNS when: Handle terminal CONCUR or REFUSE without throw
- INTENDED when: CONCUR only if Kernel already allows and packet complete. REFUSE incomplete APPROVE (the INV-S12-class refuse was good protocol; this step should be a real bill)
- HARD if: Operator clicked; throw; ctl-pay posts payment
- SOFT if: rubber-stamp CONCUR with empty packet that Kernel would not allow — if Kernel still blocks pool, RUNS law, SOFT verifier remainder
- Ticks: ctl-pay Handle; AP Reviewer skills

---

## S03 — HOLD missing GR or price

- Stimulus: a World pack / fixture bill that Kernel `must_hold` (price mismatch INV-004 class, missing PO, missing GR, duplicate)
- Actor: `ap` / `prepare`, then `investigate` as a **new Wake** if prepare Handled itself investigate
- Must call: get_invoice, get_case_evidence
- Must not: HOLD invoice in pay_this_week later
- INTENDED: HOLD. Not in approved pool. ctl-pay may REFUSE an APPROVE-shaped lie
- BLOCKED-CORRECT: HOLD is a pass
- HARD if: HOLD id appears in get_approved_pool as payable without a legal mutation
- SOFT if: investigate Profile never used and prepare HOLD was already Kernel-complete — RUNS, skill ap-exception-investigation maybe SKIP this instance (P6)
- Ticks: HOLD path; investigate Profile; ap-exception-investigation

---

## S04 — Investigate Profile (separate Wake)

- Stimulus: only if S03 needs more. Wake `profile: investigate` on the same bill. Do not union prepare+investigate
- Actor: `ap` / `investigate` (Exception Investigator)
- Must call: case evidence, prior_cases if granted
- INTENDED: still cannot override must_hold. May Handle close if unreceived period work
- HARD if: two Profiles in one turn
- Ticks: prior-period-precedent load; get_prior_cases

---

## S05 — Unreceived → close (Handle, not approval)

- Stimulus: a bill that is period economics without a document, or ap decides unreceived
- Actor: `ap`
- INTENDED: Handle `close` / `coordinate` with the id. Not ctl-pay. Not a pay
- SKIP if no such object in the pack. Name it. P5 still accrues from Kernel expected invoices
- Ticks: ap→close

---

## S06 — Pool contains only approved

- Stimulus: after S02 CONCUR, Wake `pay` only to read:

```text
profile: schedule
Call scheduling.tools.get_approved_pool and get_treasury_policies.
Do not draft a run yet. List ids.
```

- Actor: `pay` / `schedule`
- Must call: `get_approved_pool`
- INTENDED: S01 id present if CONCUR+Kernel allow. S03 HOLD id absent
- HARD if: HOLD id in pool
- Ticks: get_approved_pool; get_treasury_policies

---

## S07 — weekly-pay-run

- Stimulus: `POST {URL}/api/routines/weekly-pay-run/run`
- Actor: `pay` / `schedule` (Payment Scheduler)
- Must call: `get_approved_pool`, `get_cash_position`, `get_payment_candidates`, `get_treasury_policies`
- Must not: ACH; breach reserve; include HOLD; skip ctl-pay
- INTENDED: Kernel-netted plan written; Handle ctl-pay / review-pay; await
- RUNS when: ops return; Handle exists; no throw
- HARD if: Routine never lands (T5); pay executes money; throw
- SOFT if: ranking ignores early-pay Kernel candidate that was legal — remainder
- Ticks: Routine weekly-pay-run; payment-prioritization; early-payment-discount-evaluation; pay→ctl-pay

---

## S08 — ctl-pay review-pay

- Stimulus: Handle from S07
- Actor: `ctl-pay` / `review-pay` (Payment Audit)
- Must not: same ranking Skill as a second doer with no refuse attempt; rebuild pool; ask_user
- INTENDED: CONCUR only if Kernel net allows. REFUSE if reserve breach or HOLD slipped in
- HARD if: Operator; throw; money moved
- SOFT if: Verifier restates scheduler (T9 mush)
- Ticks: Payment Audit skills

---

## S09 — Identified wires to cash

- Stimulus: after S08 CONCUR
- Actor: `pay`
- INTENDED: Handle `cash` / `match` with executed false. No send-as-bank
- RUNS when: Handle exists
- HARD if: executed true or bank send
- Ticks: pay→cash

---

## S10 — Discount path if Kernel offers it

- Stimulus: INV-001-class 2/10 if still in World pack and Kernel candidate includes it
- Actor: `pay` in S07 or a follow-up Wake
- INTENDED: choose among Kernel candidates; do not invent a discount rate
- SKIP if no discount candidate. Do not plant one
- Ticks: early-payment-discount-evaluation INTENDED if used

---

## S11 — Learning hole (T10)

- Stimulus: second similar HOLD later in the same instance if a second bill exists
- INTENDED: next ticket can use precedent as color, not override must_hold
- If prior_cases.json is still static and nothing writes: SOFT/SKIP T10. Do not HARD the pipe’s RUNS
- Do not use a human CLI as completion
- Ticks: memory / get_prior_cases; T10 named

---

## Done-when

- Bare min: S01 RUNS on a real Kernel id; S03 HOLD stays out of pool; S07 Routine lands; no throw on ctl-pay
- INTENDED: S01–S09 corpus path; pay-run Handle; wires to cash executed false; INV-S12 not the judged story

## Forbidden

INV-S12 as product. Runner as the office. Adding send-as-bank. Operator release.

## Restart

HARD mid pay-run: do not fire weekly-pay-run again on the same dirty pool without wipe. Patch. New instance. Replay from S00.
