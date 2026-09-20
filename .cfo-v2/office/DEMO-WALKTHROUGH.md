# Office demo walkthrough

This is the **target** show. The desk on 8800 is not there yet.

Current seed (do not demo this as the product): 2 inbox handoffs, 4 operational emails, one AP lookup (`ING-001`). Canonical Maximor (`data/demo`, 72 scenarios) is not what the Computer loads. Design: `DEMO-DESIGN.md`.

Simulated data only. No live Gmail, Stripe, or bank.

- Computer: `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer`
- URL: `http://127.0.0.1:8800/`
- Replay: Tools → Demo (slider from wipe; Record before wipe)
- Transcript detail: Full
- Thinking: low

## Plot (one company, September 2026)

1. **STORY-CLEAN** — Acme `INV-001` matches PO-101 / GR-101, gets paid, hits the bank, is sampled by audit, and shows up in forecast actuals.
2. **STORY-RESOLVED** — Helios `INV-017` wire lands $25 over books. Fee evidence explains it.
3. **STORY-UNRESOLVED** — Northstar bank line is **$12.40** over the ledger. Close stays blocked.

## Ten minutes

| When | Lane | Prompt the Bot to do | Pass if |
| --- | --- | --- | --- |
| 0:00 | Desk | Open Email. Full verbosity. | 16 Bots. Not a chatbot. World is talkable. |
| 0:30 | Email | Classify the September inbox. Land vendor invoices. Ignore quotes, statements, newsletters, and prompt-injection. Hand the clean Acme bill to AP. | Traps + a Handle, not a paragraph. |
| 2:00 | AP | Three-way match `INV-001`. Investigate the price-mismatch bill. Draft concurrence to ctl-pay. Do not pay. | Match vs hold. SoD. |
| 4:00 | ctl-pay, then Pay | Concur the match. Build this week’s run. Take the 2/10 on `INV-001`. Skip held bills. | Valid is not paid. |
| 5:30 | Stripe, Bank, Cash | Unpack a payout (charges − fees − refunds). Explain the Helios $25. Do not force-match the $12.40. | Processor math + a real break. |
| 7:30 | Close | Accrue / prepaid that have evidence. Final review stays blocked on the unexplained difference. | Month-end. Close does not lie. |
| 8:30 | Audit | Reperform `INV-001`. Find duplicate vendor, round-number payment, post-close JE. | Independent. |
| 9:15 | Story | Why GM moved 64% → 61%. Quiet Harbor paid late. 13-week miss. | Same IDs as AP and cash. |

## What not to say

- Do not call Kernel 97% “the office score.” That number is Python on planted JSON. Show Inspector → Pi RPC for live proof.
- Do not say HUMAN_REVIEW to judges. The status is exception open / close blocked.
- Do not open live Stripe or a real mailbox. World is simulated. Open slug `world` to role-play vendors.
- Do not load `expected_results.json` into a Bot.

## After the world is rebuilt

Seed must use `full_inbox_specs()` (17 messages), the Stripe sim pack as Stripe Bot input, and `data/demo` as the only company picture. Then delete this “not there yet” banner.
