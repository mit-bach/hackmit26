# Intended office

This file states what the application is. It does not state how to build it.

---

## The product

The system is an Office of the CFO for Maximor Demo Corp (`CO-MAXIMOR`). It is a Maximor HackMIT entry.

The office pays vendors, collects from customers, reconciles cash, closes the month, forecasts, answers audit, and explains why numbers moved. One invoice keeps the same identity in AP, bank, GL, close, forecast, and audit.

It is not a chatbot. It is not a copilot. It is not a staffing reduction overlay on a human queue. Constitution: the office completes AP, AR, cash, close, reporting, and audit with zero humans in the completion path.

Simulated data only. There is no live Gmail write-back, live Stripe write-back, or live NetSuite post in the judged demo.

---

## Four layers

Keep these apart. Mixing them is how “97% Kernel” gets sold as “the office works.”

1. **Kernel** — `.cfo/`. Arithmetic, candidate engines, cents, `must_hold`, `evaluate_close_gates`, period lock, eval isolation. Python wins on amounts.
2. **Office** — `.cfo-v2/office/`. Named Bots, Profiles, Grants, Handles, Rooms, Routines. Pi is the turn engine inside a Bot.
3. **World pack** — preexisting Maximor books the Computer loads as `data/`. Agents discover registers. They do not create the company.
4. **Overlay** — Harness HTTP, optional website. The human Operator is an emergency stop. It is not a worker.

V1 ran Display names as in-process OpenAI `Agent()` objects with `Runner.run_sync`. V2 keeps the Kernel and puts each standing identity on a Harness Bot. Constitution SUPERSEDES voids `Runner` as the Bot bus. The constructors stay as the Grant source.

---

## The only object that matters

Day to day the office is unfinished tickets.

| Open item | Means | Dies when |
| --- | --- | --- |
| Open invoice | A customer owes this amount | Cash is applied, or credit / write-off |
| Open bill | We owe a vendor this amount | We pay it, or we dispute it to zero |
| Unapplied cash | Money hit the bank and is not stuck to invoices | It is applied |
| Unmatched bank line | The bank shows a movement the books do not | It is matched, or a journal explains it |
| Accrual | Economics happened; the document has not | The invoice arrives and the accrual reverses |

Agents are specialists over these objects. They are not specialists over “finance.”

Process law: `workshop/design-workshop/dominik/cfo-office-processes.md`.

---

## Four pipes, one book

```
who owes us  →  money in   →  bank   →  the books
who we owe   →  money out  ↗
```

The books are the general ledger. Everything else is an attempt to get a real-world event into that ledger in the right period, against the right counterparty, with evidence.

| Pipe | Direction | Standing Bots that own work in it |
| --- | --- | --- |
| AR | Money in | `apply`, `collect` (intake: `email`, `stripe`, `bank`) |
| AP | Money out | `ap`, `pay` (intake: `email`, `books`, `bank`) |
| Cash | Bank vs books | `cash` (intake: `bank`, `stripe`; identifiers from `apply` and `pay`) |
| Close | Period completeness | `close`, `story`, `audit` |

Verifier Bots sit on the pipes. They do not own the open item.

| Stake | Verifier | Says yes or no to |
| --- | --- | --- |
| Money out / off the books | `ctl-pay` | AP match, pay-run release, write-off |
| Cash identification | `ctl-cash` | Material apply, bank-rec sign-off |
| Books lock | `ctl-books` | Treatments, period lock |

`audit` is assurance after the fact. It does not concur on Friday’s wire.

---

## What “the office completes” means

A pipe is done when its open items have a next state that the Kernel already allows, and a Verifier has concurred when the grain requires concurrence.

The office is done for a period when:

1. Every deposit that belongs to a customer is applied or sitting in unapplied with a reason.
2. Every overdue invoice has a next step that is not “we forgot,” and any send that policy allows has actually entered the simulated mailbox.
3. Every vendor bill is matched or held. The weekly run is a Kernel-netted list. Cash has not left without `ctl-pay`.
4. Bank minus known open items equals ledger, or the break is named and unexplained where it is unexplained.
5. Close gates pass, or the period stays BLOCKED on a real break. The planted $12.40 stays unexplained.
6. Story packets cite Kernel evidence ids. Audit findings cite Kernel finding ids. No human signed the pack.

Autonomy is not “always post.” Fail closed remains. Missing evidence is HOLD / refuse / INSUFFICIENT / unmatched, not a guess.

---

## What the 15 Bots are for

Grain Tests A–D decide whether work is a Bot, a Profile, a Connector, a Routine, or Kernel code.

The live Roster has fifteen slugs. Instance snapshots add a sixteenth, `world`, as the simulated outside mailbox. Constitution still says do not invent a sixteenth without failing those tests. Capabilities.md already treats World as a real lane that is being reattached. This corpus records that split. It does not decree the sixteenth Bot here.

Source Bots land objects. Operator Bots own open items. Verifier Bots concur. `audit` writes findings.

---

## Intended feature, stated as function not mechanism

The judged demo must be able to show a closed loop on the same identity:

- A vendor bill becomes a match, a pay-run line, a bank outflow, a close fact, and an audit sample.
- A customer invoice becomes aging, a chase that actually reaches the simulated customer, a remittance, an application, a cash-rec tick, and a forecast actual.
- A bank line that does not explain itself keeps the month open.

The website and the Operator overlay may watch. They may not complete the loop.

---

## What this file does not decide

It does not decide World’s grain status.
It does not decide how a Bot learns a vendor habit.
It does not decide the wording of any Skill.
It does not decide a new Roster count.
It does not decide to merge `apply` and `collect`. Grain already split them because collections before application duns people who paid.
