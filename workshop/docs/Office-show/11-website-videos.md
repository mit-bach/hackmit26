# Website Videos vs Harness Demo

The public site page is `web/src/pages/Videos.tsx`. It renders `VIDEOS` from `web/src/data/videos.ts`. Stake on the page: **“Cards are placeholders until a real file exists.”** None of the six cards have `src` or `embedUrl`. That is correct. Do not fill them with Kernel CLI recordings or prove-desk playback.

The showcaser for capturing those files is Harness **Tools → Demo** on `golden-20260920-r1`, documented in `09-director.md` and `06-record-and-cut.md`.

---

## Do not follow the six titles slavishly

They were written against planted Kernel storylines (`STORY-CLEAN` paid, Harbor across periods, Northline duplicate). Golden r1 did not pay Acme, did not close, did not run Harbor, and did not stage Northline. It did run a lived September with fail-closed cash and an honest lock reject.

When MP4s exist, prefer **new ids** that match CHAPTERS, or retitle the old cards so they do not lie:

| Suggested website id | Cut | Why it is interesting |
| --- | --- | --- |
| `desk-mosaic` | A | Sixteen identities, not a chatbot |
| `inbox-traps` | B | Quote / statement / newsletter never become payables |
| `inv-001-concur` | C | AP prepares; ctl-pay concurs; AP does not pay |
| `empty-pay-run` | D | Valid bill, empty pool, executed false |
| `twelve-forty` | E | `$12.40` HUMAN_REVIEW, never MATCHED |
| `close-blocked` | F | REJECT_CLOSE, story UNLOCKED |
| `audit-sample` | G | Independent findings, no ground truth |
| optional `apply-refuse` | Apply | ctl-cash will not auto-apply HUMAN_REVIEW |
| optional `injection-mint` | B′ | ING-006 CONCUR — show as a hole, not a win |

The 10-minute concat in `cuts/README.md` is still a valid edit target. Times are edit targets, not Pi wall clock.

---

## How a card gets a file

1. Record Golden (`harness demo record` or Demo → Record).
2. Select the scene (or set in/out + featured).
3. Screen-record Demo at 1×.
4. Edit. Export MP4.
5. Put the file under `web/public/videos/` (or host it) and set `src` / `embedUrl` / `thumbnail` / `duration` on that card.
6. Until then, `videoHasMedia` stays false and the page stays honest.
