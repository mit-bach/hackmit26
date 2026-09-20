# Golden inventory — `golden-20260920-r1`

What the desk actually did. Not the website Videos cards. Not the ten-minute table in `.cfo-v2/office/final-demo/SCENARIOS.md`. Those were a wish list. This is the tape.

Computer: `.cfo-v2/office/instances/golden-20260920-r1/`
Serve: `http://127.0.0.1:8800/` with `office.json` `currentId` this instance.
World: Maximor / `CO-MAXIMOR` / USD / August 2026 CLOSED / September OPEN.
Roster: 16 named Bots. Fake workers off. Transcript detail full. Intercept default `ctl-pay`. Operator never completed a Verifier turn. `$12.40` / `TXN-2026-09-015` still unexplained.

Seq numbers below are from `harness/protocol.jsonl` as of seq **164**. Re-record after more turns and bump CHAPTERS.

---

## What it is capable of (Harness + this office)

Harness v2 is named Bots on one Computer, live Pi `--mode rpc`, durable Handles (accept ≠ complete), `protocol.jsonl`, Client extra `-e` (CFO Catalog), Kernel sidecar, office instances that you can select and wipe.

This office can:

- Spawn the sixteen-slug roster and leave idle Bots off the Demo stage until a Handle opens.
- Overlay-wake a Bot in business English (no “Call tools.X”).
- Bot→Bot handoff (`bot_send_prompt` / pair thread). Room host (`books-close`).
- Park a Verifier (`ctl-pay`, `ctl-cash`, `ctl-books`) instead of letting the preparer pay / match / lock.
- Fail closed: empty pay pool, unexplained bank line, refuse auto-apply, reject close.
- Write packets under `workspace/` and `runs/` the Kernel already understands.
- Replay the month on Tools → Demo from a recording that survives wipe.

It cannot (honestly, on this tape):

- Pay `INV-001`. Kernel `get_approved_pool` was empty even after ctl-pay CONCUR on the bill. The pay-run CONCUR’d an empty plan. `executed` false.
- Close September. `REJECT_CLOSE`. Cash `$12.40`, AR `$4500`, prepaid evidence, `bs_recon` BLOCKED.
- Forecast. Story refused; GL cash not trusted.
- Dun. Collect acknowledged the AR roster and stopped. W4 send SKIP.
- Pretend Helios `FEE_NETTED` without Kernel candidates. Overlay 6 asked for it; ctl-cash still had to review.

Emergent (not in the website cards):

- Inbox injection `MSG-INBOX-014` / Slack `ING-006` was classified as a trap, then Kernel **minted a clean three-way** and AP APPROVE’d it; ctl-pay CONCUR’d. Do not feature as the Acme story. It is a mint hole. Prove already called this HARD on a different instance (`ING-002`).
- `ING-001` HOLD because PO-101 is already live on `INV-001` — not a Kernel duplicate, a double-consume.
- Apply linked a remittance to `PAY-001` as `HUMAN_REVIEW`; ctl-cash **REFUSE** auto-apply.
- Close coordinated in room `books-close` after lock reject; story and audit answered the room instead of redoing work; `room_post` hit `host.lock` timeout (serve was wedged). That timeout is a Harness bug, not a finance outcome.

---

## What happened, in order

| Beat | Seq (approx) | Who | What |
| --- | --- | --- | --- |
| O | 1–18 | books, ap, collect | Discover Maximor. Land NS-4410. Map to Kernel `INV-001`. Collect takes the open-invoice roster only. |
| C | 12–21 | ap → ctl-pay | Clean three-way. ctl-pay **CONCUR** `INV-001`. Packet `runs/ap/concurrence/INV-001.json`. AP does not pay. |
| B | 22–45 | email, ap, world | 19 inbox threads classified. Traps ignored (quote / statement / newsletter). Five HOLDs `ING-001..005`. `ING-006` APPROVE (see hole). World handled a peer. |
| Apply | 34–51 | apply, ctl-cash | Remittance `PAY-001` HUMAN_REVIEW. ctl-cash **REFUSE** convert-to-auto. Payment notice MSG-INBOX-009 is not a new bill. |
| D | 53–62 | pay, ctl-pay | Weekly pay-run. `get_approved_pool` count=0. ctl-pay CONCUR empty draft. executed false. |
| Bank | 63–75 | bank, cash | 2026-09 operating lines including `TXN-2026-09-015`. Cash **HUMAN_REVIEW**, not MATCHED. |
| E | 78–98 | cash, ctl-cash | Overlay 6 Helios + `$12.40`. ctl-cash review-rec. `$12.40` stays unexplained. |
| Stripe | 81–102 | stripe, apply | Payout waterfall unpack. Parallel with cash. invoice_candidates 0 on Grants used. |
| F | 103–142 | close, ctl-books, story | Coordinate. Treatments accrue/prepaid/assets COMPLETE. `bs_recon` BLOCKED. ctl-books **REJECT_CLOSE**. Story flux **UNLOCKED**. Period not CLOSED. |
| M | 143–164 | close, ctl-books | Harbor Electric memory trail. `memory_read` MEM-HE-2026-08 ($7,800 method). `memory_write` DEC-2026-09-026 **$4,650**. ctl-books **CONCUR_METHOD**. Lock still REJECT_CLOSE. |
| G | 115–141 | audit | Sample close pack. Did not load ground truth. 11 Kernel finding_ids. Did not fix books. Room ack only on the second wake. |

Operator overlay DMs used: books, email, bank, cash, stripe, plus Routine fires `weekly-pay-run` and `month-end`. Verifiers were never the Operator.

---

## Website cards vs this tape

| Website id (`web/src/data/videos.ts`) | Planted wish | Golden reality |
| --- | --- | --- |
| `invoice-to-close` | Bill → pay → close | Bill → ctl-pay CONCUR → **pay pool empty** → close **BLOCKED** |
| `stripe-reconciliation` | Payout to bank | Stripe ran; not the Helios/$12.40 spine |
| `month-end-across-periods` | Harbor Aug vs Sep | Scene M: retrieve August method, September $4,650, lock still BLOCKED |
| `agent-memory` | Sep recalls Aug | Scene M: `memory_read` / `memory_write` chips on Close and ctl-books |
| `bad-invoice` | Northline dup + quote | Quote ignored. HOLDs are Office Depot mismatch, missing POs, PO-101 double-consume. Not Northline. Scene B. |
| `control-escalation` | `$12.40` + apply | **This is the tape.** Apply refuse + cash HUMAN_REVIEW + REJECT_CLOSE. Scene E. |

Do not rewrite those cards to fake a paid Acme or a closed month. Point new files at chapters C, D, E, F, G, B.

---

## Headed next (desk, not camera)

If a later `golden-r2` is allowed (this r1 stays the goose):

- Why `get_approved_pool` was empty after INV-001 CONCUR (Kernel match-status / pool path). That is the missing “valid is not paid” picture — we have the empty run, not a 2/10.
- Stripe costume vs Helios `TXN-2026-09-011` FEE_NETTED if Kernel candidates exist.
- Do not Operator-concur. Do not MATCH `$12.40`. Do not feature ING-006 as Acme.

Camera next: capture the chapters in `CHAPTERS.md` at 1× from Tools → Demo once serve is healthy. Post-edit the 10-minute concat. Put MP4s on `/videos`.
