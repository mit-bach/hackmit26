# Pipes

There are not fifteen features. There are four pipes and one book they all write into.

Process law: `workshop/design-workshop/dominik/cfo-office-processes.md`.

This folder analyses each pipe as it exists on the live office, against that process law. Intake is not a fifth pipe. It is the source edge that feeds the four.

---

## Picture

```
AR — money in     invoice, apply, collect
AP — money out    bill, match, pay-run
Cash              bank vs books
Close             period pass, then story and audit
```

AR dumps into open invoices and into the bank.
AP dumps into open bills and out of the bank.
Cash is the fight to make the bank and the books say the same thing.
Close is the fight to make the whole month internally consistent and explainable.

Do not start with a board pack. A board pack is a printout of the other four working.

---

## Four handoffs (not a mesh)

1. AR identifies a customer deposit. Cash ticks the same bank line. Close sees AR down and cash up.
2. AP identifies a vendor payment. Cash ticks the outgoing wire. Close sees AP down and cash down.
3. If AR and Cash both interpret the same $48,192.17 from scratch, they disagree and Close inherits the argument.
4. Close locking January means February invoices do not sneak into January.

---

## Standing Bots on each pipe

| Pipe | Source | Operator | Verifier | Assurance |
| --- | --- | --- | --- | --- |
| Intake (edge) | `email`, `stripe`, `bank`, `books`, (`world` disputed) | — | — | — |
| AP | those sources | `ap`, `pay` | `ctl-pay` | `audit` later |
| AR | those sources | `apply`, `collect` | `ctl-cash` (apply), `ctl-pay` (write-off) | `audit` later |
| Cash | `bank`, `stripe` | `cash` | `ctl-cash` | `audit` later |
| Close | `books` | `close`, `story` | `ctl-books` | `audit` |

---

## Honest build order from process law

If you implement one pipe well, you still have a serious system. Process law’s order:

1. AR application + aging, because that is the part a cartoon collections model misses, and it feeds cash.
2. Bank rec against those identified deposits.
3. AP match + proposed pay run.
4. Close tie-out + accruals over the month you just produced.

Live office priority is inverted in the demo trail: AP stub Handles completed first. AR send did not. That is a product risk. The Kernel is stronger on AP match than on AR last-mile. The judged story still needs AR to move.

---

## How to use these files

Each pipe file states intended function, objects, what is good, what is broken, inadequacies, required capability, and novelty fence for that pipe.

Do not merge the four files. A later agent should be able to specialize in one pipe without swallowing the other three.
