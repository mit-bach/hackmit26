# Prompt 03 — Capability wall

You are one implementing agent. You own **`/coverage`**. You replace six “Finance team / Maximor” essays with a wall a judge can audit against CAPABILITIES.md.

You do not touch Workflow, live desks, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `.cfo-v2/office/final-demo/CAPABILITIES.md` — the capability **table** (Now column) and “What we will not claim”
5. `web/src/pages/Coverage.tsx`
6. `web/src/components/CoverageGrid.tsx`
7. `web/src/data/capabilities.ts`

Do not read the other numbered prompts. You do not need FlowPlay. If FlowPlay is missing, continue — this page is a wall, not a graph.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why `/coverage` fails

`Coverage.tsx` is a `PageHead` plus `<CoverageGrid intro={false} />`.

`CoverageGrid.tsx` maps `CAPABILITIES` (six rows: ap, ar, cash, close, audit, forecast). Each card is two paragraphs:

- **Finance team.** generic function definition
- **Maximor.** generic product paragraph
- muted agent names

`capabilities.ts` has no Kernel-live / Office-live / not-built. It cannot say World is missing. It cannot say `ap.self_improvement` is not built. It cannot say the gauntlet 42/42 is a Kernel number.

A judge who reads this page learns slogans. They cannot audit the office.

Turning those six cards into a six-row table with the same essays is **not** this prompt. The unit of the wall is a **capability id** from CAPABILITIES.md, not a finance department.

---

## Mission

`/coverage` is a capability **wall**. Status is the picture. Click a cell for the sentence, grain slugs, and an Open link.

First paint: grouped cells, not a blog, not a spreadsheet of essays.

---

## Files you may create

- `web/src/data/capabilityMatrix.ts` — rows derived from CAPABILITIES.md. **Do not invent ids.**
- `web/src/data/capabilityMatrix.test.ts`
- `web/src/pages/Coverage.test.tsx`

## Files you may edit

- `web/src/pages/Coverage.tsx` — rewrite
- `web/src/components/CoverageGrid.tsx` — replace internals. **Keep the export name** `CoverageGrid` and props `{ compact?: boolean; intro?: boolean }` so a leftover import cannot crash. Grep `CoverageGrid` before assuming Overview still uses it (Prompt 01 likely removed it from Home).
- `web/src/data/capabilities.ts` — replace the 6-domain array **or** re-export from `capabilityMatrix.ts`. `architecture.test.ts` does `for (const item of CAPABILITIES) { item.agents }`. Keep `export const CAPABILITIES` with `agents: string[]` on each row.
- `web/src/styles.css` — append only `/* === 03 capability-wall === */`

## Files you must not edit

`copy.ts` (Prompt 07 owns aliases). Put any new one-sentence descriptions **in `capabilityMatrix.ts`**, not in `CAPABILITY_COPY`. You may **import** existing `CAPABILITY_COPY` keys from `copy.ts` if they already cover a row.

`Workflow.tsx`, `Overview.tsx`, `FlowPlay.tsx`, live pages, `Shell.tsx`, `Architecture.tsx`, `App.tsx`, `handoffs.ts`.
`.cfo/` (except read CAPABILITIES.md).

---

## Page to build

```
.cap-wall
  h1  What it can do
  one line ≤18 words: Kernel-live is the engine; Office-live is a standing Bot; not-built is not-built
  .cap-legend  four status swatches: kernel-live, office-live, partial, not-built
  .cap-filters buttons: All | Office-live | Partial | Not built
  .cap-groups  one band per pipe:
      Intake · Pay · Cash · Close · Rest
      each band is a row of .cap-cell buttons
  .cap-drawer  (only when a cell is selected)
      id in mono, one sentence, status pills, grain slugs, Open link(s)
```

No `PageHead` lede essay. No “Finance team.” / “Maximor.” labels.

Each `.cap-cell` shows:

- capability id in `.mono` (small)
- short title (from CAPABILITIES.md)
- status as **fill**, not only a word: office-live uses `--ok-bg`, partial `--warn-bg`, not-built `--surface` + faint text, kernel-live `--info-bg`

The wall is the page. A `<table class="data">` of twenty essays is a fail. Cells should feel like a panel of indicators, like a rack, not like blog cards in `grid-2`.

---

## Rows (must appear)

Copy titles from CAPABILITIES.md. Do not invent.

Intake: `inbox.counterparty_to_ap`, `ingestion.classify_document`, `ingestion.structured_parse`, `ingestion.bank_card_discovery`

AP: `ap.three_way_match`, `ap.payment_scheduling`, `ap.self_improvement`, `ap.vendor_bank_change`

AR: `ar.aging_collections`, `ar.cash_application`, `memory.self_improvement`

Cash: `cash.bank_reconciliation`, `cash.stripe_reconciliation`

Close: `close.accruals`, `close.prepaids`, `close.fixed_assets`, `close.balance_sheet_recs`, `close.month_end`

Rest: `audit.controls`, `reporting.variance_board`, `forecast.thirteen_week`, `memory.cross_period`, `orchestration.cfo`, `evaluation.finance_gauntlet`

You may omit `sample_data.generation`, or include it labeled “generator, not a Bot.”

### Status (Now column, compressed)

| Status | When |
| --- | --- |
| `kernel-live` | Engine exists and is tested |
| `office-live` | A standing Harness Bot can take the work |
| `partial` | Real path, demo cannot show full lifecycle |
| `not-built` | Marked not built in CAPABILITIES.md |

Required honesty:

- `inbox.counterparty_to_ap`: **partial** (Kernel-live tools; roster omits World)
- `ar.aging_collections`: office-live collect, World reply **partial**
- `ap.self_improvement`, `ap.vendor_bank_change`: **not-built**
- `evaluation.finance_gauntlet`: kernel-live; caption “Kernel measure, not the office score”
- `close.month_end`: partial if CAPABILITIES says Close Manager SDK path is partial; lock owner is `ctl-books`
- `memory.cross_period`: kernel-live. Do **not** add a semantic graph / RAG row. It is not built and not a capability id.

Do not put holdout/adversarial catalog rows on this wall.

### Open links

- `ap.three_way_match` → `/workflow?story=clean` and `/ap`
- `cash.bank_reconciliation` → `/workflow?story=unresolved` and `/cash`
- `cash.stripe_reconciliation` → `/stripe`
- `ar.cash_application` → `/ar`
- `close.month_end` → `/close`
- `forecast.thirteen_week` → `/forecast`
- `audit.controls` → `/audit`
- `orchestration.cfo` → `/` or `/simulations`
- `evaluation.finance_gauntlet` → `/evaluations`
- `inbox.counterparty_to_ap` → `/inbox` plus muted “World Bot not on live roster”

Workflow query support is Prompt 02’s job. Link it anyway. The route exists today.

---

## CoverageGrid compact mode

If `compact` is true, render **four pipe counts** (live vs not-built) plus a link to `/coverage`. Do not bring back six essay cards. If `intro` is true, do not restore the old “Finance functions, not one agent per function” section title as a long lede.

---

## CAPABILITIES export (compat)

`architecture.test.ts` requires `CAPABILITIES` items to have `agents` arrays of grain slugs. After your change, either:

- keep `capabilities.ts` as a re-export of matrix rows with `{ id, title, agents }`, or
- map department groups to agents and keep six rows **in addition** to the wall data (worse). Prefer: `CAPABILITIES` becomes the full matrix rows, each with grain slugs.

Do not leave the old six-essay `finance` / `maximor` strings as the page body even if they remain on the type for a release or two.

---

## CSS

Append `/* === 03 capability-wall === */`

`.cap-wall` full width of `.main`. `.cap-cell` min-height ~72px, left border 2px using status color. Drawer is a panel under the groups, not a modal. Filters use existing `.btn` / `.btn.primary`.

---

## Tests

- Coverage render includes `ap.self_improvement` and `inbox.counterparty_to_ap`.
- `ap.self_improvement` is labeled not-built (case insensitive).
- `inbox.counterparty_to_ap` is labeled partial.
- Blob of the matrix does not contain `100% accurate` (architecture.test already checks catalogs).
- `CAPABILITIES` still has `.agents` arrays of grain slugs.

---

## Acceptance

1. `/coverage` is a wall of capability ids. The six-card `grid-2` essays are gone.
2. `ap.self_improvement` is not-built. `ap.vendor_bank_change` is not-built.
3. `inbox.counterparty_to_ap` is partial. World is not claimed live.
4. Gauntlet row captions Kernel, not the office.
5. Filter “Not built” leaves only the not-built cells visible.
6. `npm test`, `npm run build`. Browser: click not-built, partial, and `cash.bank_reconciliation`; confirm drawer + links.

When you finish, paste the row count and the not-built ids as they render.

## Ban

If the page still leads with “Finance team.” / “Maximor.” paragraphs, you failed. If you only added a status pill to the six cards, you failed.
