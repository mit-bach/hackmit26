# Session 00 proof

Law and Computer skeleton for Client system `cfo-agentic-system`. Kernel workflows not migrated. Pi facade not written. `examples/cfo-floor` not copied. Handle completion was not live-proven. Pi was not live-proven.

Client root: `.cfo-v2/`. Computer: `.cfo-v2/office/computer`.

## Commands

Python parse of roster JSON:

```bash
python3 -c 'import json; from pathlib import Path
p=Path(".cfo-v2/office/computer/harness/roster.json")
r=json.loads(p.read_text())
print(r["system"], len(r["bots"]), [(x["id"],len(x["members"])) for x in r["rooms"]])
print(sorted({b["approvalLevel"] for b in r["bots"]}))
print([b["id"] for b in r["bots"]])'
```

Result:

```
cfo-agentic-system 15 [('intake', 4), ('pay', 3), ('cash', 4), ('books-close', 4)]
['never']
['bot_email', 'bot_stripe', 'bot_bank', 'bot_books', 'bot_ap', 'bot_pay', 'bot_apply', 'bot_collect', 'bot_cash', 'bot_close', 'bot_story', 'bot_ctl_pay', 'bot_ctl_cash', 'bot_ctl_books', 'bot_audit']
```

Harness `parseRoster` (Node 26, type-strip import of `.harness/Harness-v2/src/roster.ts`):

```bash
cd .harness/Harness-v2
node --experimental-strip-types --input-type=module -e '
import { readFileSync } from "node:fs";
import { parseRoster } from "./src/roster.ts";
const raw = JSON.parse(readFileSync("../../.cfo-v2/office/computer/harness/roster.json","utf8"));
const roster = parseRoster(raw);
console.log(roster.system, roster.bots.length, roster.rooms.map(r => [r.id, r.members.length]));
'
```

Result: `system=cfo-agentic-system`, 15 bots kept, 0 rooms/bots/routines dropped, room sizes 4/3/4/4 (all in 2–6). All `approvalLevel` `"never"`. No slug `ingest`.

Grep of the roster file (Cursor ripgrep; shell `rg` not on PATH):

- no `"slug": "ingest"`
- no `cfo-floor`
- no `"approvalLevel": "ask"`
- no `"approvalLevel": "always"`

Every grain slug has `office/bots/<slug>/BOT.md` and a roster row.

## Disk (session 00)

```
.cfo-v2/office/constitution.md
.cfo-v2/office/SUPERSEDES.md
.cfo-v2/office/templates/BOT.md
.cfo-v2/office/computer/harness/roster.json
.cfo-v2/office/computer/cfo/slug-map.json
.cfo-v2/office/computer/cfo/catalog.json
.cfo-v2/office/computer/cfo/grants.json
.cfo-v2/office/bots/{email,stripe,bank,books,ap,pay,apply,collect,cash,close,story,ctl-pay,ctl-cash,ctl-books,audit}/BOT.md
.cfo-v2/office/sessions/00-PROOF.md
```

Id scheme: slug keeps hyphens (`ctl-pay`); `id` is `bot_` + underscores (`bot_ctl_pay`). Bind uses slug.

Rooms: `intake` (email, stripe, bank, books), `pay` (ap, pay, ctl-pay), `cash` (apply, collect, cash, ctl-cash), `books-close` (close, ctl-books, story, audit).

Routines wake the owning Bot via `room:<roomId>` (not `operator_dm`): `weekly-pay-run` → pay, `daily-aging` → collect, `month-end` → close, `post-close-assurance` → audit.

## Parallel sessions (not reverted)

Session 00 placeholders for `catalog.json` (`ops: []`) and `grants.json` (`agents: {}`) were replaced on disk by a parallel compile (session 01) before this proof. Session 00 did not write them back to empty.

`office/bots/ap/BOT.md` is a later-session body (93 lines, session 04). Session 00 created the stub first, then did not overwrite the replacement.

`slug-map.json` at proof time is richer than the session 00 skeleton: `stripe` Profile `payout` has Display name `Stripe Payout Agent`; `ctl-pay` has extra Profiles `approve-match` / `audit-match`; `ctl-books` has `review-assets` / `review-bs`. Those are not list-unions. Session 00 did not revert them.

Other files present and not owned by session 00: `office/compiler/**`, `office/bots/ap/{NOTES.md,profiles,roster.json}`, `grants.ap.json`, `slug-map.ap.json`, `catalog.overrides.json`, Computer skills copies, `office/source_wakes/destinations.py`.
