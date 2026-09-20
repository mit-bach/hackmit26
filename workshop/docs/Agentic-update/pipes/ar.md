# AR pipe — money in

Process law: find who owes us, stick money to the right invoices when it arrives, then work what is still open.

Cartoon to avoid: AR is harassment. Harassment is one step. It is not most of the work. It is not where money is recognized as collected.

Three jobs, in order:

1. Put a number on what they owe. Invoice.
2. When money shows up, stick it to the right invoices. Cash application.
3. Whatever is still open, go get it, or admit you will not. Collections and reserves.

If you only build (3), you dun people who already paid, miss people whose money sits in unapplied cash, and your aging is a lie.

Standing Bots: `apply` (unapplied cash), `collect` (open invoice after apply). Verifier `ctl-cash` on material apply. Verifier `ctl-pay` on write-off / reserve. Intake: `email` remittance, `stripe` charges, `bank` customer deposit.

There is no Bot named `ar`. Grain deleted that name on purpose. The Harness fixture slug `ar` is not this pipe.

---

## Intended function

### Stage A — Invoicing (create the debt)

Something happened in the world. Until you invoice, the company has no official “this person owes us $X.”

Grain watch item 7: this tree has no AR invoicing Bot. Open invoices arrive as data. Do not invent a fifteenth-and-a-half Bot until a billing Connector exists.

Intended function for the demo: Maximor already has open customer invoices in the World pack. The office must treat those as real open items, not invent new invoice totals.

### Stage B — Cash application

A wire hits for an amount that does not say which invoices. Until someone applies it, two lies sit on the books: the bank is richer, and the customer still shows as owing.

`apply` owns unapplied cash. One `payment_id` ticket. Kernel builds candidates. The Bot chooses among them. It does not invent a combination.

`AUTO_APPLY` may post through Kernel. `HUMAN_REVIEW` and `UNAPPLIED` stay fail-closed. Queue owner is `ctl-cash` / `review-apply`, never a person.

Done when every deposit dated on or before the as-of is posted, marked unapplied after apply saw it, or sitting in a `ctl-cash` packet. Then collect may run.

### Stage C — Collections

Now the aging is as trustworthy as application made it. `collect` works what is still open.

Kernel already computed eligibility: paid, dispute, cooldown, promise, dirty unapplied cash are hard blocks. The Bot cannot override them.

When a send is Kernel-allowed, finance must actually speak in the simulated mailbox, then World (as that customer) may reply. A draft that never leaves an outbox with `sent=False` is not contact.

Write-off or reserve Handles `ctl-pay`. Collect does not Handle `ctl-cash` to apply cash.

Routine `daily-aging` names `collect` only after apply has drained new deposits for that as-of.

---

## Objects

| Object | Owner | Dies when |
| --- | --- | --- |
| Open customer invoice | books land it; `collect` works it after apply | Applied, credited, written off |
| Unapplied cash / payment | `apply` | Applied or left unapplied with a reason |
| Remittance evidence | landed by Email / Stripe / bank | Consumed into an application packet |
| CollectionDecision | `collect` | Next step taken, including a real send when the action is SEND_* |
| Outbox message | intended: mailbox transport | `sent` true in the simulated inbox, or held |
| Reserve / write-off packet | `collect` writes; `ctl-pay` concurs | Concurrence + Kernel allow |

Who eats AR outputs: cash rec eats the identified deposit; close eats AR total vs aging; forecast eats aging plus how those customers actually pay; audit samples invoices and asks whether you applied to this one.

---

## What exists that is good

- Split `apply` vs `collect` is the most important grain decision on this pipe. Do not merge them.
- Kernel aging, candidate combos, `validate_proposal`, `enforce_collection_decision` are real.
- Dirty aging: collect refuses while `new_deposits(as_of)` is non-empty. That is the rule that stops dunning people who paid.
- Partial payment: draft must cite current outstanding, not original. Tests assert this.
- Ambiguous exact matches must not AUTO_APPLY. Precedent cannot override a live named invoice.
- AR correction → precedent exists in Kernel (`record_human_application`). The idea of learning is here, even if the completion path is still a human CLI.
- Skill `cash-application` correctly says abstain when two explanations are equally good.
- Profile `chase` vs Profile `apply` Grant split is Test C.

---

## What is broken

This is the loudest break in the office. Categories stack.

### No Bot `ar` is not the break (T1, explained)

People hunt slug `ar`. Grain: AR is a Pipe. Operators are `apply` and `collect`. `collect` is on the live Roster. Purpose: “Owns open invoices still owed after application.” Routine `daily-aging` names it.

### Stage A missing (grain watch, not a silent delete)

No billing Connector. Open invoices are planted data. The office does not create the debt. Process law’s Stage A is not implemented as an Agent. That is recorded. Do not fake an invoicing Bot to look complete.

### Send tool does not exist in live Kernel (T3)

`.cfo/ar/agents.py`:

```
from inbox.tools import send_office_outbound
COLLECTION_TOOLS = [..., send_office_outbound]
```

`.cfo/inbox/tools.py` has no `send_office_outbound`.
Kernel venv: `ImportError: cannot import name 'send_office_outbound'`.
Collections Agent cannot construct. `run_collections(live=True)` cannot start.

Instance catalogs include `inbox.tools.send_office_outbound`. Live catalog does not. Live Collections Agent Grants are four read ops.

Python `ar/grants.py` `COLLECT_OPS` already lists `inbox.tools.send_office_outbound`. Compiler tests assert it. Live compile on this Computer never absorbed it because the function is not there.

### Four send stories (T2)

| Artifact | Story |
| --- | --- |
| Collections Agent instructions | Call send from collections@. Handle `world` / `customer`. |
| `ar-collections-policy` | Draft text. Do not invent emails as sent. Outbox / preview. |
| `run_collections` | `add_outbox(..., sent=False)`. Never send. Never Handle world. |
| Live collect BOT.md + live roster connectors | Four AR reads. No send. No world. |
| Instance roster `protocol-proof` | Dunning is send then Handle world. Connector includes send. World is a slug. |

A later agent that “fixes the Skill” will still fight the workflow, the constructor, and the Roster.

### World not on live Roster (T1, T4)

See `pipes/intake.md` and `surfaces/world-inbox.md`. Collect has no Handle destination for a dun in `handle-map.json`.

### Intercept vs grain on write-off (T2, T9)

`handle-map.json`: collect write-off → `ctl-pay` / `review-pay`.
`intercept.json`: Bot `collect` → `ctl-cash`.
Grain: write-off is money off the books. `ctl-pay`. Collect does not Handle `ctl-cash` to apply.

If send ever becomes a consequential op (`side-effect-external`), verifier.ts would also route it to `ctl-pay` by pattern, then intercept.json would override the Bot to `ctl-cash`. Wrong owner.

### Outbox is not the mailbox (T4)

`CollectionMessage.sent=False` is a preview object. Process law’s collections output is activity on the invoice: emailed, promised, disputed. Preview is not emailed.

### Skill forbids the product (T6)

`ar-collections-policy` Boundaries: “Do not invent emails as sent. This is an outbox / preview.”

The intended office function is that Kernel-allowed SEND_* actions reach the simulated customer. A Skill that forbids that as “invention” trains the model to stop at a draft.

### No live collect Handle (T5)

Handle files on 2026-09-20 are email/ap/ctl-pay stubs. None are `collect`. Routine `daily-aging` has not fired a proven Receipt.

### Credit-memo / overpay lifecycle partial (demo gap)

Named overpay goes to `HUMAN_REVIEW`. No customer-credit subledger or refund cycle. `PAY-007` tests detection, not settlement.

### HUMAN_REVIEW CLI still looks like completion (T9)

`ar-review-correct` is void as the office path. It still exists. Models and operators can still treat it as how apply finishes.

---

## Inadequacies of things that “work”

Kernel collections policy without a model still picks actions and drafts text. That is good for tests. It is not an office. It will never Handle World. It will never learn a customer’s delay habit in Bot Memory.

`cash-application` Skill is one of the less dishonest skills: it tells the model to copy a Kernel candidate and abstain on ties. It still enumerates ten Kernel cases as a procedure (T7). The specialist remainder is: this payer’s remittance habit as color, never as override.

Apply BOT.md forbids dunning. Good. It also forbids calling collection tools. Good. The inadequacy: apply never tells collect “I drained.” Collect’s Routine is supposed to know via Kernel `new_deposits`. That Kernel gate is the right coupling. A peer Handle from apply to collect is explicitly forbidden (“Do not Handle collect to chase. Collect wakes after you drain.”). Keep that. Do not add a mesh.

No AR Verifier for tone (grain §6). Kernel `enforce_collection_decision` already blocks illegal chase. Escalating every gentle reminder to `ctl-pay` would recreate a human-shaped queue. Keep tone as specialist work. Do not add a fourth Verifier for manners.

Forecast eats AR. `ar-cash-forecasting` is assigned to story, not to collect. That is a cross-pipe read. Collect must not own the 13-week forecast. Story must not dun. The inadequacy is that if collect never sends, forecast “promises” are fiction.

---

## Capability this pipe must possess

When AR is adequate:

1. Unapplied cash is worked before aging is chased. If deposits remain, collect stops and apply runs.
2. A unique named remittance AUTO_APPLYs through Kernel. An ambiguous exact match stays fail-closed for `ctl-cash`. An unknown payer stays UNAPPLIED or review. Residuals are not dropped.
3. Identified deposits are handed to `cash` as identifiers. Cash does not re-guess the customer.
4. Aging used for close is post-apply aging. Close can tie AR.
5. For each overdue invoice that Kernel allows to contact: a message exists in the simulated mailbox from a finance address, the invoice’s last-contact fields update, and World can reply as that customer. `sent=False` outbox-only is not this capability.
6. Disputes are not dunned. Cooldown is not spammed. Paid invoices are NO_ACTION. Dirty unapplied cash is HOLD_CONTACT.
7. Write-off / reserve is a packet to `ctl-pay`, not a person, not `ctl-cash`.
8. A later similar remittance can use stored apply precedent as color. It cannot override a contradictory live remittance.

This file does not specify the email prose, the Memory schema, or how World plays the customer. It requires that contact is real inside the simulation, and that apply stays ahead of collect.

---

## Novelty fence

Do not merge `apply` and `collect`.
Do not add Bot `ar`.
Do not add a collections-tone Verifier.
Do not make collect call cash-application tools.
Do not make apply dun.
Do not freeze aging-bucket → template-email as the specialist.
Do not implement live SMTP.
Do not treat `HUMAN_REVIEW` as AUTO_APPLY to look autonomous.
Do not resolve Northstar $12.40 inside AR to make close look clean. That break is a cash unexplained difference.

The specialist on `collect` should be able to tell a 3-day-late on-time customer from a 70-day silent strategic account using Kernel facts plus habits it learned. Kernel still owns eligibility. The specialist owns the next legal step and the words, once send exists.
