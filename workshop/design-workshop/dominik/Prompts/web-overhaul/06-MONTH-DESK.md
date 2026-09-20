# Prompt 06 — Month desk (close + forecast)

You are one implementing agent. You own **`/close` and `/forecast`**. You throw away `DemoLayout` on both. Close becomes a lock that will not close. Forecast becomes a 13-week polyline. Harbor Electric is a side instrument, not the page.

You do not touch AP, AR, Cash, Stripe, Workflow, Coverage, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `web/src/pages/Close.tsx`
5. `web/src/pages/Forecast.tsx`
6. `web/src/components/Demo.tsx` — import `SourceArtifactViewer`, `BeforeAfterDiff`, `ProcessPanel`. Do **not** render `DemoLayout`.
7. `web/src/components/FlowPlay.tsx` — must exist. If missing, stop.
8. `web/src/copy.ts` — import `formatStatus`, `formatTask`, `formatAccountingSentence`, `formatWeekDate`. Do not edit copy.ts.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why these pages fail

**Close (`Close.tsx`)** pretends the story is Harbor Electric homework.

- `WhatsHappening` is three paragraphs about electricity bills
- Input column: `StoryCard` defining accrual + history table + contract + August memory artifacts
- Output: Harbor estimate `ResultBlock` + “Close checklist” as `.split` rows of `formatTask` + pills + a journal table
- The lock is `formatStatus(data?.status)` — a word
- The $12.40 cash gate is easy to miss because Harbor ate the fold

Harbor is a real Kernel thread. It is not the month. The month is **blocked** because cash is unexplained. The page should say that with a lock, then offer Harbor as the accrual instrument.

**Forecast (`Forecast.tsx`)**

- `WhatsHappening` restates opening and ending cash
- Input: definition `StoryCard` + original forecast artifact + new events + gross margin artifacts
- Output: ending cash pill + paragraphs about which weeks changed + **a 13-row table**

There is no line. Leadership cannot see tightening. They can scroll a spreadsheet.

Title “How much cash will be in the bank?” plus a table is the old console.

---

## Mission

`/close` **is** a gate into a lock. Tasks feed the lock. Unexplained cash (`TXN-2026-09-015` / $12.40) is a blocked edge. The lock node stays `blocked`. Title tells the truth: September is not closed.

`/forecast` **is** an SVG polyline of `ending_cash` across weeks. The table is secondary.

Keep Kernel paths:

- Close: `GET /api/close`, `POST /api/workflows/close`, `POST /api/workflows/accrual` `{ vendor: "Harbor Electric" }`
- Forecast: `GET /api/forecast`, `POST /api/workflows/forecast`

Do not call `deterministic_coordinate` a live Close Manager if CAPABILITIES.md says partial. Label lock as `ctl-books`. Do not invent `INV-AR-014` as a miss if the payload does not mention it.

---

## Files you may create

- `web/src/components/boards/CloseGate.tsx`
- `web/src/components/boards/ForecastLine.tsx`
- tests beside them

## Files you may edit

- `web/src/pages/Close.tsx` — rewrite. No `DemoLayout`. No `WhatsHappening`. No `StoryCard` on first paint.
- `web/src/pages/Forecast.tsx` — rewrite. Same bans. No early `if (!data) return` that skips the desk chrome — show the stage with a loading line.
- `web/src/styles.css` — append only `/* === 06 month-desk === */`

## Files you must not edit

`AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `Shell.tsx`, `FlowPlay.tsx`, `Demo.tsx`, `Explain.tsx`, `copy.ts`.
`.cfo/`.

---

## `/close` — CloseGate

Prefix `.month-`.

**Instrument:** a small DAG on `.month-gate` (min-height 400px).

Nodes (from tasks / profiles, labels via `formatTask` when ids match): accrue, prepaid, assets, balance-sheet recs, coordinate → **lock** (`ctl-books`).

If GET/POST shows unreconciled cash / period not clear / status blocked: lock node `blocked`, brass/bad stroke, caption **Month is not closed** plus `$12.40` / `TXN-2026-09-015` if present in payload or as planted caption (the planted unexplained item is public show-path; you may label it even before POST).

Do not draw a green Closed stamp.

**Harbor (secondary, not the hero):** a compact strip under the gate: recent bill amounts as a **tiny** SVG sparkline or three number chips, estimate `usd(amount)`, method via `formatAccountingSentence` after accrual POST. Contract/memory artifacts go in `<details>`.

**Checklist:** do not keep the `.split` list as the page. Map tasks onto gate nodes. Leftover tasks can sit in evidence.

**Journals table:** evidence `<details>`, or a closed section “Journals”.

**FlowPlay live** nodes: `close`, `ctl-books`, `story`, `audit`. Lock/blocked status on `ctl-books` or `close`.

**Run:** same two buttons (month-end close + Estimate Harbor Electric).

h1: `September is not closed`. Stake ≤18 words: unexplained cash keeps the period lock from seating.

---

## `/forecast` — ForecastLine

**Instrument:** SVG `.month-line` min-height 380px.

- `weeks` from `result?.result?.snapshot?.weeks || data?.weeks || []`
- polyline of `ending_cash`
- x = week via `formatWeekDate(week_end || week_start)`
- y = USD, axis labeled Week / Ending cash (USD)
- opening annotated on first point, ending on last
- click a point to select (keep `setWeek`)
- 13 points when `weeks.length === 13`

No chart npm library. `polyline` + `circle` + two `text` axes. Guard empty weeks: show the stage and “Run forecast” rather than crashing.

**Table:** below the line, or behind a “Numbers” toggle. Do not delete the numbers. Do not make the table the first paint.

**Miss:** if payload/copy mentions `INV-AR-014`, mark that week. Do not invent it.

**FlowPlay live** nodes: `pay`, `apply`, `story` (cash in/out feeding the line).

**Run:** `POST /api/workflows/forecast`.

h1: `13-week cash`. Stake: the same books, projected forward. Caption source `/api/forecast`.

Gross-margin 64%→61% toys stay in evidence if present. Do not lead with them.

---

## Honesty

- Close stays BLOCKED. No invented fee to finish the month.
- Harbor estimate may persist from Kernel; that does not mean the month closed.
- Gauntlet numbers do not appear on these pages.

---

## CSS

Append `/* === 06 month-desk === */`

Gate nodes are buttons (keyboard). Lock is visually heavier than other nodes (border `--bad` when blocked). Line chart: `--text` stroke, `--brass` active point, no area gradient fill required (a faint `--ok-bg` fill under the line is allowed if it stays inside this CSS block).

---

## Tests

- Close does not render `What's happening?` or `What arrived`.
- Close render includes `not closed` or `BLOCKED` or `12.40`.
- Forecast render includes an `<svg>` (or a testid `forecast-line`).
- Close does not show `Invoice approved`.

---

## Acceptance (browser)

`/close` — gate + lock visible without reading Harbor first; lock blocked; Harbor is secondary; POST paths unchanged.

`/forecast` — SVG line; 13 points when weeks has 13; table still available; POST path unchanged.

Neither page uses `<DemoLayout`.

`npm test`, `npm run build`.

When you finish, list CloseGate + ForecastLine and the POST paths.

## Ban

If Close still opens with Harbor essays and a checklist of splits, you failed. If Forecast’s first screen is the weekly table, you failed. If you keep `DemoLayout` and put the SVG in `output`, you failed.
