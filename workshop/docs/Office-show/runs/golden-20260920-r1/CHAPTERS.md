# Chapters — golden-20260920-r1

Seq from `harness/protocol.jsonl` at lastSeq **164** (Harbor memory `turn.end`). Re-record if the tape grows; bump this table.

| Chapter | Content | Video? | seq | Camera |
| --- | --- | --- | --- | --- |
| A | Onboard. Books discover Maximor. August CLOSED. NS-4410 lands. | desk establishing | 1–18 | books, ap, collect · 4 panes |
| B | Inbox: 19 classified. Quote/statement/newsletter ignored. ING-001..005 HOLD. | yes | 22–45 | email, ap, ctl-pay · 4 panes |
| B′ | ING-006 Slack injection minted clean and CONCUR’d. **Hole, not a win.** | optional / caution | 25–39 | ap, ctl-pay · 2 panes |
| C | INV-001 three-way → ctl-pay CONCUR. AP does not pay. | yes | 4–21 | ap, ctl-pay, books · 4 panes |
| Apply | PAY-001 HUMAN_REVIEW. ctl-cash REFUSE auto-apply. | optional | 34–51 | apply, ctl-cash · 2 panes |
| D | weekly-pay-run. `get_approved_pool` empty. CONCUR empty plan. executed false. | yes | 53–62 | pay, ctl-pay · 2 panes |
| E | Bank lines + Helios overlay. `TXN-2026-09-015` HUMAN_REVIEW, not MATCHED. | yes | 63–98 | bank, cash, ctl-cash · 4 panes |
| Stripe | Payout unpack (parallel with E). | optional | 81–102 | stripe, apply, cash · 4 panes |
| F | close coordinate. ctl-books REJECT_CLOSE. story UNLOCKED. Not CLOSED. | yes | 103–142 | close, ctl-books, story · 4 panes |
| G | Audit sample of the close pack. 11 finding_ids. No ground truth. | yes | 115–141 | audit, close · 2 panes |
| M | Harbor Electric memory. Close `memory_read` MEM-HE-2026-08, writes DEC-2026-09-026 $4,650. ctl-books CONCUR_METHOD. Lock still REJECT_CLOSE. | yes | 143–164 | close, ctl-books · 2 panes |
| H | dun + World | SKIP — collect roster-only; no send | | |

Same cuts are `harness/demo/latest/scenes.json` after record.

`$12.40` is unexplained in E and F. If it is MATCHED anywhere, this recording is not shippable.

Scene M is a show trail written onto protocol/transcripts/Memory after the live close turn. Kernel already had ACC-202609-003 at $4,650. The Bot `memory_read` / `memory_write` rows were planted so Demo can play the recall. Re-run later if you need a live Pi turn.
