# Prompt 04 — Pay desk (AP + AR)

You are one implementing agent. You own **`/ap` and `/ar`**. You throw away `DemoLayout` on both routes and replace them with two instruments: a three-way match, and an aging + refused apply.

You do not touch Workflow, Coverage, Cash, Close, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `web/src/pages/AP.tsx`
5. `web/src/pages/AR.tsx`
6. `web/src/components/Demo.tsx` — **import** `SourceArtifactViewer`, `BeforeAfterDiff`, `ProcessPanel`, `ProvenanceLinks`. Do **not** import or render `DemoLayout`.
7. `web/src/components/FlowPlay.tsx` — must exist. If missing, stop.
8. `web/src/hooks.ts`, `web/src/copy.ts` (import `formatDecision`, `formatException`, `formatStatus`, `AGING_COPY`, `formatAgingBucket` — do not edit copy.ts)

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why these pages fail

Both files are the Kernel console template.

**AP (`AP.tsx`)**

- `DemoLayout` eyebrow “Accounts payable”, long `task` lede, `WhatsHappening` about three-way match in words
- `RunBar` “Check this vendor bill” + “Draft this week's payments”
- Invoice **register table stuffed into `runBar`**
- Input column: email artifact + three cards titled Invoice / Purchase order / Delivery record (amounts as text, **no join lines**)
- Duplicate path: two artifact viewers “First copy / Second copy”
- Process: `ProcessPanel` dots
- Output: `OutputHeadline`, `Definition`, `ExceptionCard` or `ResultBlock`, kv, lineage

Default open id is `INV-003` (qty exception). `INV-001` (the CLEAN planted bill) is just another table row. A sponsor never sees a match. They read about one.

**AR (`AR.tsx`)**

- Same skeleton. `WhatsHappening` about Lumen Labs $5,000 “September billing”
- Three run buttons: age / collections / cash-apply `PAY-004`
- Input: `StoryCard` + invoice table
- Output: cash-application `ResultBlock` + aging as **five `.split` rows** + payment list

Aging is a paragraph plus numbers. Apply is an essay. Collect will lie if you describe a send (World is not attached). There is no picture of a payment that cannot snap to an invoice.

---

## Mission

`/ap` **is** Invoice vs PO vs GR, with lines between fields that agree, and a broken line where they do not.

`/ar` **is** a full-width aging bar plus a remittance that **fails to attach** to a Lumen invoice when evidence is thin.

Keep every Kernel path:

- AP: `GET /api/invoices`, `GET /api/invoices/{id}`, `POST /api/workflows/ap/{id}`, `POST /api/workflows/schedule`
- AR: `GET /api/ar`, `POST /api/workflows/ar-aging`, `ar-collections`, `ar-cash-apply` with `{ payment_id: "PAY-004" }`

Do not invent PO/GR the API did not return. Do not claim AUTO_APPLY if Kernel did not. Do not say a collection email was sent.

---

## Files you may create

Under `web/src/components/boards/`:

- `MatchBoard.tsx`
- `AgingApplyBoard.tsx`
- tests beside them

Optional local wrappers in that folder. Do not create a shared `LiveDesk.tsx` for other prompts.

## Files you may edit

- `web/src/pages/AP.tsx` — rewrite (no `DemoLayout`, no `WhatsHappening`)
- `web/src/pages/AR.tsx` — rewrite (no `DemoLayout`, no `WhatsHappening`, no `StoryCard` on first paint)
- `web/src/styles.css` — append only `/* === 04 pay-desk === */`

## Files you must not edit

`Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`, `Inbox.tsx`, `Shell.tsx`, `FlowPlay.tsx`, `Demo.tsx`, `Explain.tsx`, `copy.ts`, `handoffs.ts`.
`.cfo/`.

---

## Shared page shape (both routes)

Follow the Live desk skeleton in shared laws. Prefix classes `.pay-`.

Evidence `<details>` default **closed**. Put `SourceArtifactViewer` there. After a run, `ProcessPanel` may sit under FlowPlay, not in a center IO column.

h1 examples (short):

- AP: `Vendor bills`
- AR: `Customer cash`

Stake ≤18 words. AP: a bill is paid only if it matches the order and the receipt. AR: unmatched cash is safer than a guessed invoice.

---

## `/ap` — MatchBoard

**Instrument:** three document sheets in a row, class `.pay-match`.

| Sheet | Source |
| --- | --- |
| Invoice | `detail.three_way.artifacts.invoice` or `detail.source_document` |
| Purchase order | `...purchase_order` |
| Goods receipt | `...goods_receipt` |

Each sheet uses existing `.doc-paper` language (you may wrap, do not invent a second document style). Show vendor, **id in mono**, amount via `usd()`, qty if present.

**Join lines:** SVG overlay. Connect amount-to-amount when both numbers exist and match. Connect qty-to-qty when both exist and match. Matching lines use `--ok` or `--brass`. Mismatch: `--bad`, dashed, **no** “solved” connector. If a field is missing (no GR), the GR sheet is a hollow slot labeled missing — that is `INV-005` energy; only show it when the API says so.

**Register:** left rail of invoices from `GET /api/invoices` (vendor, amount, id). Not a full-page `<table class="data">`. Selected row brass inset. Clicking calls existing `open(id)`.

**Featured:** keep default run target `INV-003` (exception) so the broken qty line is the first thing a sponsor sees. Put `INV-001` as a pinned rail entry labeled Clean so they can open the happy match without hunting.

**Duplicate:** if `detail.duplicate_peer` exists (`INV-006` style), the stage becomes two overlapping sheets + a HOLD stamp. Do not skip this path.

**Decision:** a large stamp on the stage from Kernel: `formatDecision(inner?.decision?.decision || detail?.match_status)`. You do not decide APPROVE/HOLD in the UI.

**FlowPlay live** nodes: `ap`, `ctl-pay`, `pay` (optional `email`). Edges hardcoded locally. Do not edit `handoffs.ts`. After run, highlight from `liveStages`.

**Run controls:** same two actions, compact, under the board.

---

## `/ar` — AgingApplyBoard

**Instrument, stacked:**

1. **Aging bar** `.pay-aging` — one full-width stacked bar. Five segments `CURRENT`, `1-30`, `31-60`, `61-90`, `90+` from `data.buckets`. Width % of `data.outstanding` (guard divide-by-zero). Labels via `formatAgingBucket`. Click a segment to list invoice ids in that bucket from API rows, as chips. Do not invent ids.

2. **Refused apply** `.pay-apply` — payment tile `PAY-004` (Lumen, $5,000, memo September billing — from API, fallback labels only if fields missing). Opposite: open Lumen (or competing) invoices as tiles. After `ar-cash-apply`, if Kernel does not apply, draw a **gap** between payment and invoices. Copy: more evidence required. Never animate a successful snap unless `applied` ids actually returned.

**Collect:** `POST ar-collections`. Show `CollectionAction` as a chip. `SEND_*` is a **draft**. Caption: “Outbound mailbox is not attached on the live roster.” If you draw World, dashed not-attached. Do not say sent.

**FlowPlay live** nodes: `apply`, `collect`, `ctl-cash` (optional `email`). No attached send edge to World.

**Run controls:** the same three POSTs, compact.

Do not keep the aging explanation paragraph (“An invoice that was due 75 days ago…”) on first paint. Put glossary in evidence `<details>` if needed.

---

## CSS

Append `/* === 04 pay-desk === */`

Sheets feel like paper on `--surface`, not three identical `.card` h2 blocks. Rail ~220px. Stamp uses `.pill` scale-up, not emoji. Aging segments are real widths, not equal columns.

---

## Tests

- AP does not render `What's happening?` or `What arrived`.
- AP render can show `INV-003` (default) and includes a way to see `INV-001`.
- AR render includes aging bucket labels or `CURRENT`.
- AR does not contain `email sent` / `sent the collection` as a success string.

---

## Acceptance (browser)

`/ap` — three sheets visible without running; join lines on a clean match when `INV-001` is opened; `INV-003` still the default and shows a broken qty (or missing) relationship if the API says so; RunBar still hits `/api/workflows/ap/${id}` and `/api/workflows/schedule`.

`/ar` — one stacked aging bar, not five text rows as the hero; PAY-004 run does not claim AUTO_APPLY unless Kernel did; collect does not say email sent.

Neither page uses `<DemoLayout`.

`npm test`, `npm run build`. If 8765 is down, boards must not crash (`|| []`).

When you finish, list MatchBoard + AgingApplyBoard and the POST paths still wired.

## Ban

If you keep `DemoLayout` and pass MatchBoard as `happening`, you failed. If AP match is still three cards inside an input column, you failed. If AR aging is still `.split` rows of `usd()`, you failed.
