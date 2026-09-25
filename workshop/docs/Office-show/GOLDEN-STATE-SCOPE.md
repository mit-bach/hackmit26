# Golden state — what a Maximor viewer would actually see

Instance `golden-20260920-r1`. Protocol last seq **164**. Recording copy: `workshop/docs/Office-show/runs/golden-20260920-r1/recording/`. Written 2026-09-24.

This run is live Pi, sixteen Bots, on a real Maximor pack. It is not a month of office work. It is one afternoon of single handoffs. Four gaps matter more than the chapter list.

## 1. World is the outside of the company. The tape used it once.

Bot `world` is not a finance worker. `office/bots/world/BOT.md` says it role-plays whoever finance mailed: a vendor, a customer, a bank, or an employee. It speaks through the simulated mailbox. Finance reaches it by email. It answers in that thread. Email then classifies the reply.

The intended wakes are:

| Who starts | Why | Persona |
| --- | --- | --- |
| email | Missing invoice fields, outbound | vendor |
| collect | A dun the kernel allows | customer |
| ap | A vendor query | vendor |
| a bank notice or employee mail | Outside party writes in | bank or employee |

The golden protocol has **one** of those. Seq 37: email asks World to answer as Acme Supplies on `THR-incomplete`. Seq 42: World replies once (`MSG-INBOX-011-R1`, invoice number, $12,450.00, `PO-101`) and stops. No customer. No bank. No employee. Collect never mailed anyone. AP never queried a vendor. World never opened a thread of its own.

That reply is 470 characters. The World demo transcript is 3 lines. The Pi session behind it is 127 KB of tool trace the viewer does not read.

The inbox itself was a dump of 19 planted messages on install morning, not a mailbox that kept receiving mail through September. After the one Acme reply, nothing else came in from outside.

## 2. The insider skim is in the books. Nobody was sent to find it. Audit did not find it.

The design is in `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md`. Bots must not load that file. The answer key sits in `expected_results.json` under `adversarial_holdout` (109 cases). The unlabeled rows sit in the operational World pack (`.cfo-v2/office/world/maximor`, seed 42). Plant notes: `world/maximor/holdout/ADVERSARIAL-PLANT-NOTES.md`.

Twelve storylines are planted as ordinary registers. The ones that match “someone inside is taking money, and you are not told” are:

| Storyline | What is on disk, unlabeled | Scale |
| --- | --- | --- |
| `SL-ADV-HALYARD` | Ghost `EMP-8891` Tomas Halyard on payroll, absent from badge, Okta, and laptops. Same bank last4 `9022` as vendor `VEND-HAL-01`. | about $146k wages plus facilities AP |
| `SL-ADV-KESTREL` | AP clerk Dana Kestrel. Vendor `VEND-KIS-01` shares a home address and tax id with her spouse. | about $187k related-party remittance |
| `SL-ADV-PROCESSOR` | Luis Redmond. Processor fees above contract, into a connected account that is not on the vendor master. | about $215k |
| `SL-ADV-RESIDUAL` | Eleven months of cash-over-short plugs. September’s plug is missing, which is why `TXN-2026-09-015` is $12.40 over. | $86k plugged, $12.40 left open |
| `SL-ADV-LAPPING` | AR applications that still make the bank tie. | about $413k misapplied |

`CAPABILITIES.md` already says the impressive audit is the join across vendor master, payroll bank accounts, and trailing residuals. It says not to retell the loud decoys, and not to load the holdout.

What audit did on this tape (seq 115, then a second nudge at seq 136):

- Wake text: sample `workspace/close/2026-09/pack.json`. Cite Kernel finding ids. Do not load ground truth. Do not fix the books.
- Kernel run `runs/audit/2026-09-20260920T153114Z.json`. Populations: **3 payments, 4 journals, 5 approvals, 22 invoices, 7 reconciliations.**
- Findings are the loud control fixtures: round-number `PAY-AUD-002` at $50,000, duplicate vendor `VEND-ACME` / `VEND-ACME-DUP`, labeled post-close `JE-AUD-003`, self-approval, duplicate invoice ids `AUD-INV-MISS-*`.
- Interpretation file lists those `AUD-*` controls only.
- Protocol text, workspace JSON, and the audit interpretation contain **no** `Halyard`, `Kestrel`, `Redmond`, `EMP-8891`, or `VEND-KIS-01`.

So the edge case is in the pack. The golden driver never asked anyone to look, and the audit sample is the small labeled control set, not the 73,853-row payroll register or the 340-vendor master. Close `NOTES.md` still says stealth theft “is not planted in operational books.” That sentence is stale. The plant notes say the rows are in the registers and the labels are only in the holdout.

The $12.40 line is the public tip of `SL-ADV-RESIDUAL`. The tape treats it as “leave this unexplained.” It does not show eleven months of plugs, Clearing Solutions, or Nadia Voss. A viewer who hears “the system catches an insider skim without being told” is hearing a design that this recording does not perform.

## 3. Close did not leave a report you can open.

Close coordination has no Catalog tools. It copies Kernel task status and hands work to ctl-books, story, and audit. The files it wrote are JSON:

- `workspace/close/2026-09/pack.json` — period `2026-09`, status `BLOCKED`
- `workspace/close/2026-09/coordinate-decision.json` — `can_close: false`, narrative one sentence
- `workspace/close/2026-09/gates.json` and ctl-books verdict JSON

There is **no HTML file** anywhere on `golden-20260920-r1`. Kernel `close/report.py` formats a plain-text packet (`format_close_run`). Nothing in `.cfo/` writes `<html>`.

The pack is also pointed at the wrong tree. `pack.json` evidence for ingest is an absolute path under `.cfo/runs/ingestion/`, not under this Computer’s `runs/`. The sidecar chdirs into `.cfo/` for imports. Close notes already warn that this chdir is not the office destination. The artifact a presenter would click does not exist, and the JSON that does exist cites the kernel checkout.

`coordinate-decision.json` lists “waiting on humans” for the $12.40, a $4,500 AR item, and missing insurance evidence. The same file says “Do not ask a human.” The month is correctly not CLOSED. The status a person can read is a JSON narrative, not a close report.

Harbor (seq 143–164) is worse: `CHAPTERS.md` says the memory rows were written onto the protocol after the live close so Demo could play them. That is not a close report either.

## 4. Worker threads stop after one reply.

Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) are supposed to answer a packet once. That shape is fine.

Everyone else was supposed to keep a business thread. On this protocol they do not. Counts are accepted sends plus replies in `harness/protocol.jsonl`.

| Pair | Messages | What the second message is |
| --- | --- | --- |
| email → world → email | 2 | One vendor reply, then silence |
| books → collect → books | 2 | Collect ack in a **5 second** turn. No dun. |
| books → ap → ctl-pay | one handoff, one concur | No question back to books or to the vendor |
| email → ap | 1 send, 1 reply | Inbox batch, not a bill-by-bill thread |
| email → apply → ctl-cash | one remittance | `PAY-001` left in review |
| bank → cash → ctl-cash | one land, one review | Northstar not MATCHED. No follow-up |
| stripe → cash, stripe → apply | one each | Deposits matched, charges unapplied, stop |
| pay → ctl-pay | 1 | Empty approved pool. `executed` false |
| close → story, close → audit | one sample each | Second close→audit message is a status nudge, not new work |
| close → ctl-books | 3 sends | Three separate lock/method packets, each answered once |

Demo transcripts the UI plays are 3 to 26 lines per Bot. The long Pi sessions (email 381 KB, stripe 389 KB, cash 838 KB) are tool logs. The speech another Bot receives is usually 350–1,000 characters, once.

Operator wakes that started the month are five short overlays (books, email, bank, cash, stripe), plus the later Harbor wake. None of them says “keep talking until the outside party, the auditor, and the close report have something a person can follow.”

## What is still true, and safe to say

- Live Pi, not fake workers. Sixteen Bots. Operator did not complete a verifier Handle.
- `INV-001` / `PO-101` / `GR-101` at $12,450.00 reached ctl-pay and was concurred. AP did not pay it.
- Quote, statement, and newsletter mail were not paid.
- `TXN-2026-09-011` is fee-netted with `FEE-729103`. `TXN-2026-09-015` ($12.40) was not MATCHED. September was not CLOSED.
- Audit did not load `get_audit_ground_truth` and did not edit the books.

## What is unfit for the presentation

1. World appears once, as Acme filling in a missing invoice. The outside of the company never writes again.
2. Insider rows are in the pack. Audit’s sample is the loud `AUD-*` decoys (`PAY-AUD-002` $50,000, Acme LLC duplicate, labeled post-close journal). The ghost payroll, the related-party vendor, and the processor skim are untouched.
3. Close output is JSON status. There is no HTML report. Evidence paths leak into `.cfo/runs/`.
4. Except the verifiers, threads are one send and one reply. Collect, World, pay, bank, stripe, story, and audit do not continue.
5. Friday pay-run concurred an empty pool, because `INV-001` concur did not fill it.
6. Injection mail minted `ING-006`, and ctl-pay concurred it. The fork’s reject patch is not on the live kernel.
7. Harbor seq 143–164 was planted after the live turn.

## Where the other chat left this

Debugging ran on port 8801 under `.cfo-v2/prove-fork/` and was ordered not to touch this desk. Skills and Bot files on the fork still match golden. The only content change is inbox classification on the copied kernel, so injection does not mint. That chat stopped during P1. It did not add World threads, an audit hunt, or a close report.

Next instance, after that work is merged: `golden-20260924-r1`. Leave this instance on disk. Prompt: `workshop/docs/Office-prove/prompts/RESUME-FORK-THEN-MERGE-GOLDEN.md`.
