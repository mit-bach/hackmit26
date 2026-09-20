# AP pipe — money out

Process law: a vendor claims we owe them. We check we asked for it and we got it. We decide which approved bills get cash this week.

Standing Bots: `ap` (open bill), `pay` (payment-run draft), `ctl-pay` (concurrence).

Intake: `email`, `books`, sometimes `bank` (a charge is not a bill).

---

## Intended function

1. A vendor bill becomes an open bill with Kernel three-way facts.
2. `ap` proposes APPROVE or HOLD. It does not pay. It does not concur.
3. Approve-shaped drafts Handle `ctl-pay` / `review-match`. `must_hold` still wins.
4. Payable bills sit in the approved pool. `pay` drafts this week’s run from Kernel candidates. It does not execute ACH.
5. Every weekly draft Handles `ctl-pay` / `review-pay`. After concurrence, identified wires go to `cash` with `executed` false.
6. Unreceived work that belongs to the period Handles `close` as accrual input. That Handle is not approval.

Done when: every bill is matched or held, the run is a Kernel-netted list a Verifier can refuse, and cash has not left without concurrence.

Cartoon to avoid: “the AP agent pays the invoice.” Match and pay are different objects.

---

## Objects

| Object | Owner | Dies when |
| --- | --- | --- |
| Open bill | `ap` | Paid, or disputed to zero |
| Match packet | `ap` writes; `ctl-pay` concurs | Concurrence + Kernel allow, or HOLD |
| Approved pool row | Kernel pool; `pay` reads | Paid or stripped |
| Payment-run draft | `pay` | `ctl-pay` release + Kernel net; still not a bank send |
| Identified outflow | handed to `cash` | Bank rec ticks it |

---

## What exists that is good

- Split `ap` vs `pay` vs `ctl-pay` matches process law and grain Test C.
- Kernel `collect_case_evidence` + `must_hold` is real: duplicate invoice number, missing PO, missing GR, amount past P-009, unknown vendor, PO over authority.
- APPROVE only enters the pool. HOLD does not become a forecast commitment or a clean close item (`docs/AGENTIC_SYSTEM_WORKFLOW.md`).
- Payment Kernel `apply_cash_and_policy_net` strips HOLD, strips unnecessary early pays, defers for reserve. The model must not breach the reserve.
- Live Pi: `ctl-pay` REFUSEd an incomplete APPROVE packet for INV-S12. Verifier found reasons to refuse. That is the Verifier’s job.
- Grant denylist stops Payment Audit from rebuilding the plan. Shape is right.
- Skills `three-way-match-analysis`, `ap-exception-investigation`, `payment-prioritization`, `early-payment-discount-evaluation` exist as a layer. The idea is right even when the files restate Kernel.

---

## What is broken

### Intake does not produce a Kernel bill (T11, T12)

Completed Handles used `MSG-S12` / `INV-S12`. Email packet was a marker. `tools.get_invoice(INV-S12)` not found. AP HOLD. ctl-pay REFUSE.

The bus moved. The pipe did not match a vendor bill.

### Host still Runner (T13)

Session 04 Kernel host still imports `run_agent`. Constitution voided Runner as the Bot bus. AP pytest is not office-live match.

### BOT.md / cwd (T6)

`ap` and `pay` instructions point at `office/bots/.../BOT.md` from Computer cwd. Path missing.

### No AP learning (T10)

`prior_cases.json` is a static seed. Demo gap `ap.self_improvement` is `NOT_IMPLEMENTED`. The next similar bill does not change. Maximor asked for memory that changes the next period. AP does not have it.

### Vendor bank-change control missing (T3)

Vendor master may now have bank fields. There is no control engine. Planting “wire instructions changed” as an audit find would be fake. Capabilities.md records this.

### Pay-run never proven on the bus (T5)

Routine `weekly-pay-run` is on the Roster. `client.json` has `autoRoutines: false`. No Receipts were on disk in the 09-19 audit. No live Handle `pay` → `ctl-pay` / `review-pay` is in the 09-20 Handle set (those six files are email/ap/ctl-pay stub match, not a weekly run).

### No send-as-bank (intended gap, still a last-mile)

Pay BOT.md: this office has no send-as-bank Connector. Do not add one for the demo. Identified wires must still reach `cash`. That handoff is not proven live.

### Verifier cannot re-perform the bill (T9)

`ctl-pay` / `review-match` denylist strips `RECORD_TOOLS`. It may call `get_case_evidence`. It must not call `get_invoice`. A Verifier that can only read the preparer’s packet can rubber-stamp or refuse for incompleteness. It cannot always re-perform three-way match from source. Live INV-S12 refuse was incompleteness. That is weaker than re-performance.

### Investigate vs prepare over-specified (T7)

BOT.md tells when to wear `investigate`. Kernel `exception_types` already exists. The specialist’s remaining work is how this vendor’s mess differs from the type list. The file also lists `must_hold` cases in prose, which is Kernel’s job.

---

## Inadequacies of things that “work”

Three-way match Kernel is one of the strongest pieces in the repo. The Skill restates clean-match criteria the Python already computed (T6, T7). A later specialist still needs to interpret uncertain exceptions and prior-period aliases (INV-021 class). That judgment should not be a copy of `must_hold`.

Payment Scheduler and Payment Audit historically shared constructor `tools=`. Overrides tightened the Audit Grant. The inadequacy that remains: the two Prompts still share skills `payment-prioritization` and `early-payment-discount-evaluation`. A Verifier wearing the same ranking skill as the doer is a soft SoD hole even when rebuild ops are denylisted.

AP has no Kernel `HUMAN_REVIEW` path (`APPROVE`/`HOLD` only). That is good. Uncertainty is HOLD or investigate, then `ctl-pay`. The inadequacy is that HOLD is a graveyard unless someone works exceptions. There is no proven loop that asks World for a missing PO or a revised PDF and then re-wakes `ap` on the same `invoice_id`.

No-PO bills, in process law, replace the PO leg with approval. Grain puts that approval on `ctl-pay`, not a human. Live office has not shown a no-PO bill through that gate.

---

## Capability this pipe must possess

When AP is adequate:

1. A real Maximor vendor bill (Acme INV-001 class) lands, matches PO and GR, `ctl-pay` concurs because Kernel already allows, and the id enters the approved pool.
2. A quantity, price, missing GR, or duplicate bill HOLDs. It does not pay. It does not vanish.
3. An exception can be investigated with policy and prior cases. A stored alias can apply only when current evidence still supports it.
4. The weekly run captures 2/10 when cash allows, skips held bills, defers when the reserve would break. Totals on disk match Kernel net, not the model’s arithmetic.
5. `ctl-pay` can refuse a complete-looking packet that Kernel forbids. It can also refuse an incomplete packet. It does not execute a wire.
6. After release, `cash` receives identified outflows. Close can see AP aging that ties.
7. The next similar bill can change because last period’s decision is retrievable as operational memory, not because a human edited `prior_cases.json`.

This file does not specify how alias memory is stored. It requires that AP behavior can change.

---

## Novelty fence

Do not merge `ap` and `pay`.
Do not make `ap` release cash.
Do not make `ctl-pay` hold `RECORD_TOOLS` just to make it feel powerful if grain SoD forbids that Grant union. If re-performance needs a read, that is a Grant question, not a new Bot.
Do not add `ap-investigator` as a sixteenth Bot. Same open item. Profile `investigate`.
Do not implement send-as-bank for the judged demo.
Do not freeze a table from exception_type to HOLD sentence. Kernel already typed the exception. The specialist adds vendor-specific sense, not a second taxonomy.
