# Office grain — what is a Bot

This file picks the standing identities for the Office of the CFO. The input is the forty-three Cursor `Agent()` Display names and the four Pipes. The output is a Roster of Bots. Fifteen is the count the tests produce. It is not a target.

This file does not implement the Harness extension. It does not rewrite Python. It does not score whether today’s agent prompts contradict each other; that pass comes later.

**`examples/cfo-floor` is not this office.** The six slugs `ingest`, `ap`, `ar`, `cash`, `close`, `audit` under `.harness/Harness-v2/examples/cfo-floor` exist so Harness v2 could prove Handles, Rooms, and bind. They are a protocol placeholder. They are not a Bot surface. Do not copy them. Do not design toward them. Do not treat “not six” as the design problem. The design problem is: which standing identities does this office actually need.

Process shape: [cfo-office-processes.md](cfo-office-processes.md). Maximor brief: [Maximor-HackMIT-Track.md](Maximor-HackMIT-Track.md). Live constructors: `skills/assignments.py` and `**/agent.py`. Attach contract: [docs/CFO_HARNESS_EXTENSION.md](../../docs/CFO_HARNESS_EXTENSION.md). Code wins on amounts: [docs/AGENTIC_SYSTEM_WORKFLOW.md](../../docs/AGENTIC_SYSTEM_WORKFLOW.md).

---

## 1. Name map

One name for one thing.

| Name | Meaning |
| --- | --- |
| Bot | A standing Harness identity. One slug, one lane, one Memory. Bound with `HARNESS_BOT`. Not a child. Not a subagent |
| Display name | A Python `Agent(name=...)` string such as `AP Preparer`. A Grant source. Not a Bot |
| Profile | A named Grant set on one Bot. A Wake names a Profile. Profiles on one Bot are not unioned |
| Pipe | AR, AP, cash, or close. A process. Not a Bot |
| Open item | An unfinished ticket: open invoice, open bill, unapplied cash, unmatched bank line, accrual |
| Source Bot | Lands objects from one outside system. Does not match, pay, apply, or lock |
| Operator Bot | Owns one class of open item and proposes the next state |
| Verifier Bot | Concurrence that used to be a human queue. Cannot hold the Operator Bot’s write Grants |
| Assurance Bot | After-the-fact audit. Reads. Does not concur in the pay path |
| Connector | A provider (Gmail, Stripe, Xero) attached to a Source Bot. Not a Bot |
| Wake | What starts a Bot: webhook, poll, Routine, or Handle |
| Kernel | Existing Python engine. Arithmetic, candidates, hard holds, close gates |
| Handle | Peer work item on the Harness bus |
| Operator | The human at the Harness HTTP control plane. Demo overlay. Not a queue inside the office |

A Pipe is not a Bot. A Display name is not a Bot. A Connector is not a Bot. A Kernel validator is not a Bot.

---

## 2. What constitutes a Bot

A Bot exists when **all four** tests pass. If one test fails, keep the work as a Profile, a Connector, a Routine, or Kernel code.

### Test A — Wake

Something in the world or the office **names this identity**.

- A webhook (`payout.paid`, a Gmail push) addresses this slug.
- A Routine (`weekly-pay-run`, `month-end`) addresses this slug.
- Another Bot sends a Handle **to this slug**, not to a nested child.

If the work only ever runs because the same Bot continued its own turn, it is a Profile or a step, not a new Bot.

### Test B — Object

The Bot is the named owner of **one class of record**:

- a source record type (email message, Stripe payout, bank line, GL row), or
- one open-item class (open bill, unapplied cash, unmatched bank line, …), or
- a concurrence class (money-out yes/no, cash identification yes/no, books lock yes/no), or
- after-the-fact findings.

Maximor’s example processes are **not** objects. “Accounts payable and receivable” is two Pipes. Inside AP there is still match, then pay. Those are different objects. Do not make one Bot named `ap-ar`.

### Test C — Grant particularity

The tool list would be **unsafe to union** onto a neighbor.

- Email may read messages. Email may not `create_accrual`.
- AP may load invoice, PO, and receipt. AP may not release a pay run.
- A Verifier may read the packet. A Verifier may not hold the Operator Bot’s record-write Grants.
- Audit may read operational decisions. Audit may not post.

If two Display names already share the same constructor `tools=` and the same object, they are two Profiles or one Profile plus instructions, not two Bots.

### Test D — Durable stance

The Bot keeps Memory that changes the **next** period: this vendor’s invoice layout, this customer’s remittance habit, this account’s usual break. A pure function over one JSON blob is Kernel, not a Bot.

### Fail closed

Do not add a Bot because:

- a folder already has `agent.py`
- a workflow has a “reviewer” step
- Maximor listed a process name
- you want a second prompt on the same tools
- you are afraid to delete a Display name

Display names remain in `cfo/grants.json`. They become Profiles. They do not each get a lane.

---

## 3. What is not a Bot

| Thing in the repo today | Fate |
| --- | --- |
| Kernel candidate engines, cents math, `must_hold`, `evaluate_close_gates` | Stay Python |
| `HUMAN_REVIEW` as a **Kernel status** | Stay. The queue owner changes (see §8) |
| Eight invoice `Agent()` objects that all emit `InvoiceCandidate` | Four Source Bots plus Connectors. Not eight lanes |
| AP Reviewer / Approver / Audit as three lanes | One Verifier Profile set (`ctl-pay`) |
| Prepaid / FA / BS reviewer twins | `ctl-books` |
| Close Manager (`tools=[]`) | Routine + `close` Profile `coordinate`. Orchestration is not an identity |
| Five sample-data Display names | Eval Kernel. Never a floor Bot |
| Skills | Prompt. Skills never grant tools |
| Subagents / agent-room children | Forbidden. Every identity is a surface Bot |

---

## 4. Why forty-three Display names are not the Roster

Forty-three is how the Python tree grew: one `Agent()` per stage, per source format, per reviewer twin, plus five sample-data names. That list is the **Grant catalog**. It is the Compiler’s input. It is not a set of standing Bots.

| Pattern | What it does | Fate |
| --- | --- | --- |
| Source format = identity | EDI vs PDF vs vendor portal vs employee upload all emit `InvoiceCandidate` | Connectors on `email` or `books` |
| Reviewer twin = identity | Many twins share the same `tools=` as the preparer (`Cash Application Reviewer`, both payment agents, reporting reviewers) | A second prompt, or a Verifier Profile — not a second Operator Bot |
| Pipe stage = identity | Accrual, prepaid, fixed assets, and BS recon are components of close | Profiles on `close` / `ctl-books` |
| Sample data = identity | Five scenario-planning Display names | Eval Kernel. Never a floor Bot |
| Missing Stripe identity | Processor payout is a real Wake (`payout.paid`) and a real object (waterfall) with **zero** `Agent()` today | New Source Bot `stripe` |
| Missing Verifier identity | High-stakes yes/no is scattered across reviewer twins, or parked on a human | Three Verifier Bots by stake class, not twelve clones |

The process doc’s “four specialists plus one reviewer” sketch is shape only. It is also not the Roster. Pipes are not Bots. A first-cut diagram is not a surface.

---

## 5. Recommended Roster — fifteen Bots

Four Source Bots, seven Operator Bots, three Verifier Bots, one Assurance Bot.

```
outside world
    │
    ├─ webhook/poll ─► email, stripe, bank, books          Source
    │                         │
    │                         │ files + Handles
    ▼                         ▼
open items ─────────► ap, pay, apply, collect, cash, close, story   Operator
    │                         │
    │                         │ consequential draft
    ▼                         ▼
concurrence ────────► ctl-pay, ctl-cash, ctl-books         Verifier
    │                         │
    ▼                         ▼
period pack ────────► audit                                Assurance
```

No children. A Profile is a Wake of the same Bot with a different Grant set. The Kernel still vetoes illegal amounts.

### 5.1 Source Bots (4)

These are the specialists you named: anyone who imports or sits on a data source. Each has a Connector. Email and Stripe already have webhooks in `integrations/providers/__init__.py` (`WEBHOOK_PROVIDERS`: `gmail`, `outlook`, `stripe`, `adyen`, `xero`).

| Slug | Owns | Wake | Connectors (not extra Bots) | Must not |
| --- | --- | --- | --- | --- |
| `email` | Messages and attachments (vendor invoices **and** customer remittances) | Gmail / Outlook webhook | employee upload, vendor-portal PDF, mailroom scan as extra Connectors on this Bot | Match, pay, apply, accrue |
| `stripe` | Processor payouts, fees, refunds, chargebacks | Stripe webhook; Adyen is a second Connector | `adyen` | Produce `InvoiceCandidate`. Unpack the waterfall, then hand the **deposit** to `cash` and the **charge-level** facts to `apply` |
| `bank` | Bank lines and corporate-card charges | Poll / feed. **No bank provider exists in `WEBHOOK_PROVIDERS` today** | card discovery (`find_related_invoice`) | Invent invoices. A charge is not a bill |
| `books` | GL, subledgers, vendor/customer master, POs, period lock **state** (read) | Xero webhook; NetSuite and Coupa **sync** | `xero`, `netsuite`, `coupa`, EDI structured bills | Close the period. Books-the-system is not close-the-month |

You were not missing a fifth Source Bot for “invoices.” You were missing a clean split of **four different objects**. The leftover invoice Display names hang off `email` or `books` as Connectors:

| Display name | Connector on |
| --- | --- |
| Email Invoice Agent | `email` |
| Employee Submission Agent | `email` |
| Vendor Portal Agent | `email` |
| Physical Mail / Document Agent | `email` |
| ERP Invoice Agent | `books` |
| Procurement Invoice Agent | `books` |
| EDI / Electronic Invoicing Agent | `books` |
| Bank/Card Discovery Agent | `bank` |

If Coupa later grows a live webhook and its native object is a **purchase request**, not a GL row, revisit Test A/B and maybe add `procurement`. Do not add it now. Sync is not a Wake of its own Bot.

### 5.2 Operator Bots (7)

Specialists over open items and period work. Each Pipe has **components**. Those components are Profiles or sibling Bots when Test C says the Grants conflict.

| Slug | Open item / job | Profiles (Display names it may wear) | Hands to |
| --- | --- | --- | --- |
| `ap` | Open bill: three-way match, hold, exception | `prepare` ← AP Preparer; `investigate` ← Exception Investigator | `ctl-pay` on approve-shaped drafts; `pay` when the bill is payable; `close` for unreceived work |
| `pay` | Payment-run draft (cash about to leave) | `schedule` ← Payment Scheduler | `ctl-pay`; identified wires to `cash` |
| `apply` | Unapplied cash | `apply` ← Cash Application Agent | `ctl-cash` when material or ambiguous; identified deposits to `cash` |
| `collect` | Open invoice still owed (aging after application) | `chase` ← Collections Agent | `ctl-pay` only for write-off / reserve (money off the books); never before `apply` has seen the deposit |
| `cash` | Unmatched bank line | `match` ← Cash Reconciliation Preparer; `investigate` ← Cash Exception Investigator | `ctl-cash` for sign-off; trusted cash to `close` |
| `close` | Period completeness: accrue, defer, tie, coordinate | `accrue`, `prepaid`, `assets`, `bs`, `coordinate` | `ctl-books` for treatments and lock; pack to `story` and `audit` |
| `story` | Flux, 13-week forecast, board pack | `flux`, `forecast`, `board` | `audit` samples the pack. No dedicated reporting Verifier (see §6) |

**Why `pay` is not a Profile on `ap`.** Match answers “do we owe this.” Pay answers “does cash leave this week.” Maximor lists both inside AP. They are still two objects. Union would let the matcher release the wire.

**Why `apply` is not a Profile on `collect`.** Collections that run before application dun people who already paid. The process doc already says this. Two Bots.

**Why accrual is a Profile on `close`, not a sixteenth Bot.** Accrual, prepaid, fixed assets, and BS recon are the month-end pass over the other Pipes. They share a Wake (period-end Routine). They do **not** share Grants: `create_accrual` stays on Profile `accrue` only. The Compiler still fail-closes if a Wake omits `profile`.

**Why Close Manager is not a Bot.** `tools=[]`. It picks the next checklist row. That is a Routine on `close` plus Kernel `ready_tasks`. Giving it a lane creates an identity with nothing to own.

### 5.3 Verifier Bots (3)

Not one Verifier per Operator. That would recreate the reviewer-twin farm (twelve reviewer Display names today). Verifiers partition by **stake class**:

| Slug | Says yes/no to | Replaces these Display names | Must not |
| --- | --- | --- | --- |
| `ctl-pay` | AP match concurrence; payment-run release; bill write-off | AP Reviewer, AP Approver, AP Audit, Payment Audit | Hold `RECORD_TOOLS`; build the pay-run; move cash |
| `ctl-cash` | Material cash application; bank-rec sign-off | Cash Application Reviewer, Cash Reconciliation Reviewer | Apply cash; post fee journals; own the bank Connector |
| `ctl-books` | Close treatments; period lock | Prepaid/FA/BS reviewers, Month-End Close Reviewer | `create_accrual`; flip period lock in Kernel without a passed `evaluate_close_gates` |

Count: three Verifiers, seven Operators. Verifiers are fewer than doers on purpose.

A Verifier is how this office stays **human-reliable without a human in the queue**. The proposing Bot does not approve itself. Harness `blocked` Handles that today park on the human Operator are addressed to the Verifier slug instead.

Kernel hard holds still win. A Verifier cannot talk past `must_hold` or a failed close gate. A Verifier that concurs on a planted trap that the Kernel already marked illegal is a bug in the Verifier, and the Kernel still refuses the post.

### 5.4 Assurance Bot (1)

| Slug | Job | Profiles |
| --- | --- | --- |
| `audit` | Sample, re-perform, write findings | `interpret` ← Auditor Agent; `report` ← Audit Report Agent |

Audit is not a fourth Verifier. It does not sit on Friday’s pay run. It reads what already happened and writes `workspace/audit/` plus `runs/audit/`. Production Grants omit `get_audit_ground_truth`.

---

## 6. What we deliberately did not split

| Temptation | Why not |
| --- | --- |
| Eighth and ninth Source Bots for EDI / portal | Same object as email or books. Connector |
| `ap-investigator` as its own Bot | Same open item as `ap`. Profile `investigate` adds policy tools. Same slug |
| Reporting Reviewer / Forecast Reviewer | `story` does not move money. A twin with the same forecast tools is a second prompt. `audit` samples the pack |
| Fourth Verifier for collections tone | Collections is not cash leaving. Kernel `enforce_collection_decision` already blocks illegal chase. Escalate write-offs to `ctl-pay` |
| One Bot that owns every outside system | Fails Test B and Test C. Email, Stripe, bank, and books are different objects and different Wakes |
| One Bot per Maximor bullet (three-way match, aging, Stripe payouts, $12.40, accruals, board pack, …) | Those are components and eval plants, not identities |

---

## 7. Sensitivity — twelve and eighteen

The tests can land nearby. These are not competing products. They are what you add or drop **after** a later interconnection review.

**Twelve** (more compressed than we want): merge `story` into `close`; merge `ctl-cash` into `ctl-pay` as `ctl-money`. Cost: close becomes a novelist; one Verifier Grant set spans pay-run and bank-rec (Test C gets mushy).

**Eighteen** (less compressed): split `close` into `accrue` vs `adjust` (prepaid/FA/BS); promote `procurement` to a Source Bot; split `ap` investigator. Cost: investigator and procurement fail Test A unless they grow their own Wake.

Stay on fifteen unless a later pass shows a failed test.

---

## 8. Autonomy — Verifier replaces the human queue

Product rule for this build: **no human gate is required to complete the office.** No pay-run, period lock, or write-off waits on a person.

What that means in mechanism:

1. Kernel statuses such as `HUMAN_REVIEW` remain as **fail-closed outcomes** (ambiguous remittance, $12.40 unexplained, must-hold). They mean “do not auto-post.”
2. The **queue owner** for those statuses is a Verifier Bot, not the Harness human Operator.
3. The Operator (human) can still inspect, stop, and prompt through Harness HTTP. That is a demo overlay and an emergency brake. The happy path does not park there.
4. Peer Handles are still not approval. `ap` sending to `pay` is not concurrence. Only `ctl-*` concurrence plus a passing Kernel gate posts.

Maximor judging text still mentions “human review when the system is uncertain.” Show the Verifier packet and the Kernel veto in the demo. Do not re-introduce a human queue to chase the sentence.

Eval warning, not solved here: several fixtures **expect** the string `HUMAN_REVIEW`. Remapping the queue owner must not convert those cases into `MATCHED` / `AUTO_APPLY`. The Verifier is allowed to refuse. The Kernel is allowed to refuse. Autonomy is not “always post.”

---

## 9. Wakes — how work starts

| Event | Who wakes | Next Handle |
| --- | --- | --- |
| Gmail / Outlook invoice or remittance | `email` | `ap` (bill) or `apply` (remittance). Classification is the Source Bot’s job |
| Stripe / Adyen `payout.paid` | `stripe` | `cash` (deposit) and `apply` (charge-level) |
| Bank file / card feed | `bank` | `cash`; card-without-invoice stays on `bank` as `invoice_missing` |
| Xero webhook / NetSuite or Coupa sync | `books` | `ap` / `collect` / `close` depending on the record |
| Weekly Routine | `pay` | `ctl-pay` |
| Daily aging Routine | `collect` | only after `apply` has drained new deposits |
| Month-end Routine | `close` | treatment Profiles, then `ctl-books` |
| Close pack written | `story`, `audit` | none required |

Source Bots write a path on the Computer, then `bot_send_prompt`. They do not call Operator Bots as children.

---

## 10. Display names → Profiles (informative)

The Compiler still emits Grants from constructors. This table is the first slug-map the office should load. It is not frozen if constructors change.

| Display name | Bot | Profile |
| --- | --- | --- |
| Email Invoice Agent | `email` | `invoice` |
| Employee Submission Agent | `email` | `employee` |
| Vendor Portal Agent | `email` | `portal` |
| Physical Mail / Document Agent | `email` | `document` |
| ERP Invoice Agent | `books` | `erp-invoice` |
| Procurement Invoice Agent | `books` | `procurement` |
| EDI / Electronic Invoicing Agent | `books` | `edi` |
| Bank/Card Discovery Agent | `bank` | `card` |
| *(no Display name today)* | `stripe` | `payout` |
| AP Preparer | `ap` | `prepare` |
| Exception Investigator | `ap` | `investigate` |
| AP Reviewer | `ctl-pay` | `review-match` |
| AP Approver | `ctl-pay` | `review-match` |
| AP Audit | `ctl-pay` | `review-match` |
| Payment Scheduler | `pay` | `schedule` |
| Payment Audit | `ctl-pay` | `review-pay` |
| Cash Application Agent | `apply` | `apply` |
| Cash Application Reviewer | `ctl-cash` | `review-apply` |
| Collections Agent | `collect` | `chase` |
| Cash Reconciliation Preparer | `cash` | `match` |
| Cash Exception Investigator | `cash` | `investigate` |
| Cash Reconciliation Reviewer | `ctl-cash` | `review-rec` |
| Accrual Agent | `close` | `accrue` |
| Prepaid Preparer | `close` | `prepaid` |
| Prepaid Reviewer | `ctl-books` | `review-treatment` |
| Fixed Asset Preparer | `close` | `assets` |
| Fixed Asset Reviewer | `ctl-books` | `review-treatment` |
| Balance Sheet Reconciliation Preparer | `close` | `bs` |
| Balance Sheet Reconciliation Reviewer | `ctl-books` | `review-treatment` |
| Close Manager | `close` | `coordinate` (or a Routine, no Profile) |
| Month-End Close Reviewer | `ctl-books` | `lock` |
| Variance Analysis Agent | `story` | `flux` |
| Board Reporting Agent | `story` | `board` |
| Cash Forecast Agent | `story` | `forecast` |
| Forecast Variance Agent | `story` | `forecast-miss` |
| Reporting Reviewer Agent | *(drop as lane)* | `audit` samples |
| Forecast Reviewer Agent | *(drop as lane)* | `audit` samples |
| Auditor Agent | `audit` | `interpret` |
| Audit Report Agent | `audit` | `report` |
| Five sample-data agents | *(not Bots)* | Kernel / eval |

`AP Reviewer`, `AP Approver`, and `AP Audit` share one Verifier Bot. They do **not** union with `AP Preparer`. Match tools and concurrence tools stay on different slugs.

---

## 11. Watch later (do not solve in this pass)

These are interconnection and constructor problems. Keep them visible. Do not silently “fix” them by adding Bots.

1. **Stripe is not an invoice source.** A Stripe Bot that emits `InvoiceCandidate` would be a category error. Payout waterfall stays cash math.
2. **No bank webhook.** `bank` is still a Bot (object + poll Wake). The Connector is missing.
3. **Payment Scheduler and Payment Audit share the same `tools=` today.** `ctl-pay` Profile `review-pay` needs a **stricter** Grant than the constructor currently encodes (read the plan, do not rebuild it). The Compiler will copy the identical list unless `cfo/catalog.overrides.json` tightens it. That is Grant work, not a sixteenth Bot.
4. **AP Reviewer and AP Approver already share tools.** Collapsing them onto `ctl-pay` is honest. Collapsing them onto `ap` is not.
5. **Two close entrypoints** (`close/month_end` vs `close/orchestrator.run_cfo_close`). The `close` Bot must have one Kernel door that can lock. The other door is a test packet.
6. **`HUMAN_REVIEW` fixture strings.** Autonomy remaps the queue owner. It must not auto-resolve planted traps (`SCN-AR-010`, `$12.40`, Stripe fee plants).
7. **No AR invoicing Bot.** Maximor Stage A (create the customer invoice) has no `Agent()` in this tree. Open invoices arrive as data. Do not invent a fifteenth-and-a-half Bot until a billing Connector exists.
8. **Email carries two Pipes.** One Source Bot, two downstream Operators. Do not split `email-ap` and `email-ar`.
9. **Prompt-level contradictions** among the forty-three instruction blocks. Later pass. Grain does not wait on that review.
10. **Harness approvals are Operator-shaped.** Mapping `blocked` to a Verifier slug is Client-system work on top of Harness, not a Harness fork.

---

## 12. What this pass is not

- Not a Harness v2 change.
- Not `cfo-catalog compile` or the Python sidecar.
- Not a compaction of Kernel modules.
- Not a verdict on which agent instructions are wrong.
- Not a frozen Bot count if Tests A–D later fail on a new Connector.
- Not `.harness/Harness-v2/examples/cfo-floor`. That roster is a Harness bind test. When this office gets a Computer, it gets its own `harness/roster.json`.

When the Roster is written, it will list these fifteen slugs. Access still comes from compiled Grants and an operator-owned slug-map. The office can grow a Connector without growing a Bot.
