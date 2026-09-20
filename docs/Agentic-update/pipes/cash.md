# Cash pipe — bank vs books

Process law: cash is not a report. Cash is the argument between the bank and the books.

The bank says one number. The ledger cash account says another. Both can be “right” and still disagree: outstanding checks, deposits in transit, a $12.40 wire fee, a Stripe payout that is one bank line and forty invoices, a double-posted refund.

Standing Bots: `cash` (unmatched bank line), `ctl-cash` (sign-off). Identifiers should already have been written by `apply` (customer deposits) and `pay` (vendor wires). Stripe unpack is Kernel math; Bot `stripe` is supposed to hand the deposit here.

---

## Intended function

1. Each unmatched bank line gets Kernel candidates. `cash` copies a `candidate_id`. It does not invent a fee, FX, or residual story.
2. Exact, grouped ACH, fee-netted with evidence, timing, duplicate, provider payout, unexplained: Python typed these. The Bot chooses among them.
3. The pipe that owns the counterparty identified the line. Cash checks the bank agrees. It does not re-interpret Acme vs the remittance from scratch.
4. Fail-closed and unexplained difference Handle `ctl-cash` / `review-rec`. Autonomy is not force MATCHED.
5. Period cannot be RECONCILED when arithmetic does not tie, or when `UNEXPLAINED_DIFFERENCE` remains. That is correct.
6. After Verifier concurrence and Kernel allow, trusted cash Handles `close`.
7. Stripe/Adyen: unpack charges − fees − refunds − disputes = bank deposit. Then one deposit to bank rec, charge-level to `apply`. Never an AP invoice.

Trusted cash is the only acceptable starting balance for a 13-week forecast. Starting a forecast from “whatever the GL said before rec” is a thirteen-week lie.

---

## Objects

| Object | Owner | Dies when |
| --- | --- | --- |
| Unmatched bank line | `cash` | Matched, explained exception, timing item, or named unexplained |
| Ledger cash line | `books` / Kernel | Ticked in rec |
| Provider payout waterfall | Kernel; `stripe` should land it | Unpacked; deposit to rec |
| Fee evidence | Kernel | Supports FEE_NETTED or does not |
| Trusted cash | `cash` after `ctl-cash` | Close consumes it |
| $12.40 unexplained | planted break | Stays. Source object change through a legal op only |

Show path STORY-UNRESOLVED: Northstar INV-AR-013 / PAY-006 books $12,400.00. Bank `TXN-2026-09-015` is $12,412.40. No fee evidence. Close stays BLOCKED.

Holdout catalog explains it as a 0.1% remittance residual. That explanation is not in operational books. Do not put it there for the judged demo.

---

## What exists that is good

- Integer-cent tie-out in cash recon. Display can stay major units.
- Candidate engine: exact, grouped, fee-netted, timing, duplicate, unexplained.
- BOT.md states the identification rule in one sentence: trust apply/pay identifiers; do not re-interpret the counterparty from scratch.
- `$12.40` cannot be relabeled as a fee without Kernel fee evidence. Helios `TXN-2026-09-011` is the explained FEE_NETTED cousin. Both stories exist. Do not collapse them.
- `ctl-cash` cannot convert unexplained to MATCHED. Cannot convert ambiguous apply to AUTO_APPLY.
- Skills for method selection, evidence validation, exception investigation, bank-reference interpretation exist as a layer.
- Stripe simulation pack exists. `invoice_candidates` stays 0 on that path. Category error avoided.

---

## What is broken

### Stripe Bot has no tools (T3, T5)

Empty Display name. Empty Grants. Unpack is CLI. Office-live Stripe Bot is costume. Charge-level facts may never Handle `apply`. Deposit may never Handle `cash` as a Bot-to-Bot fact.

### Cash Kernel handles vs Harness Handles (T2, T5)

Session 07 wrote `runs/cash_recon/handles/*.json` (Kernel-shaped). Those are not Harness Handle files. `bot_await_turn` cannot see them.

### bind_case is not a Catalog op (T8)

BOT.md: `bind_case` is Sidecar session setup. The Bot does not call it. A bound Pi that never got a bound case will call `get_bank_transaction` against nothing useful.

### No live cash Handle on 2026-09-20 (T5)

Six completed Handles are AP stub. No `cash` or `ctl-cash` Handle files in that set.

### Identifier handoff not proven (T11)

If apply never posts, cash is tempted to interpret the deposit. Process law says that is how Close inherits the argument. Live office has not shown apply → cash identifier → rec tick on the same bank line as a Harness path.

### Fee journals unposted until Verifier + Kernel (good rule, unproven path)

BOT.md forbids auto-posting fee journals. There is no live proof that a proposed fee entry waits on `ctl-cash` and then posts only if Kernel fee evidence exists.

### intercept default Operator (T9)

`intercept.json` default is Operator. Cash Bot override is `ctl-cash`, which matches grain for rec. Default still parks unnamed consequential ops on a human.

---

## Inadequacies of things that “work”

Cash recon Kernel is strong. The skills again restate match types Python already named (T6, T7). The specialist remainder is messy bank descriptions and “this processor’s usual payout label” as Memory. `bank-reference-interpretation` is the Skill closest to that remainder. It still reads like a procedure not to invent invoice numbers, which Kernel already forbids.

`ctl-cash` wearing the same cash-application read tools as `apply` is honest for review. It must not post. Grants currently look like the same read set. SoD depends on posting staying out of the Reviewer constructor. Keep that. Do not “give the reviewer write so it can fix.”

Grouped ACH and provider payout candidates are Kernel-live. Office-live is not shown. Volume RecBench-style lines exist as a next claim in Capabilities.md, not as a Bot proof.

Forecast must start from trusted cash. Story’s forecast tools can build an in-memory snapshot from AP/AR/payroll without waiting on rec. That is a cross-pipe lie risk. Story BOT.md does not require rec sign-off before forecast. Process law does. This inadequacy is close/story as much as cash.

---

## Capability this pipe must possess

When cash is adequate:

1. A bank line that AR already identified ticks without a second customer guess.
2. A bank line that AP already identified as Friday’s wire ticks the same way.
3. A Stripe-shaped deposit unpacks in Kernel and rec sees PROVIDER_PAYOUT, not EXACT_MATCH to a random ledger row, and not an AP invoice.
4. Helios-class fee-netted matches only with fee evidence.
5. Northstar-class $12.40 stays unexplained. Period stays open. Verifier refuses MATCHED. Close stays BLOCKED.
6. Trusted cash, when Kernel allows and `ctl-cash` concurs, is a path `close` can read.
7. Unmatched lines have owners (this Bot) and a next step that is not “invent a story.”

This file does not specify how the Bot talks about a messy memo line. It requires that no invented fee ever clears a planted break.

---

## Novelty fence

Do not make `cash` own vendor bills or AR application.
Do not make `cash` move money.
Do not add a Bot per match type.
Do not resolve $12.40 in operational books.
Do not start the 13-week forecast from unreconciled GL cash as if rec had run.
Do not freeze a table from match_type to English. Kernel typed it. The specialist explains evidence, not the taxonomy.
