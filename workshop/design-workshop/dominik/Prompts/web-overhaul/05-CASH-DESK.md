# Prompt 05 — Cash desk (bank + Stripe)

You are one implementing agent. You own **`/cash` and `/stripe`**. You throw away `DemoLayout` on both routes. Cash becomes two facing lanes with pairing lines. Stripe becomes a waterfall of bars. The Northstar **$12.40** is a visible broken pair, not a paragraph.

You do not touch AP, AR, Close, Workflow, Coverage, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `web/src/pages/Cash.tsx`
5. `web/src/pages/StripePage.tsx`
6. `web/src/components/Demo.tsx` — import `SourceArtifactViewer`, `ProcessPanel`. Do **not** render `DemoLayout`.
7. `web/src/components/FlowPlay.tsx` — must exist. If missing, stop.
8. `web/src/copy.ts` — import `explainCashMatch`, `formatMatchType`, `formatStatus`. Do not edit copy.ts.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why these pages fail

**Cash (`Cash.tsx`)** is the most important live page in the sponsor walk, and it is an essay.

- `WhatsHappening` states the Northstar $12.40 in three paragraphs
- Three buttons (“The $12.40 Northstar difference” / “Wire with a bank fee” / “One payment, several bills”) swap which `SourceArtifactViewer` you read
- Bank and ledger never sit in two lanes
- Matches appear as a `<table class="data">` in the output column after a run
- Process is dots

A sponsor can **read** that close cannot finish. They cannot **see** an unmatched pair.

**Stripe (`StripePage.tsx`)**

- `WhatsHappening` defines a payout in words
- `.waterfall-eq` is seven stacked text lines: charges, refunds, disputes, fees, expected, deposit, difference
- Payout picker is clickable cards
- Tied vs not is a pill on a sentence

There is no waterfall. There is an equation written in CSS.

---

## Mission

`/cash` **is** Bank vs Ledger. Matched pairs are lines. `TXN-2026-09-015` is selected on first paint, with a **gap** labeled $12.40, and **no** solved connector. Helios `TXN-2026-09-011` + `FEE-729103` is a contrasting explained pair.

`/stripe` **is** horizontal bars that step down from gross to net, then a comparison of expected vs bank deposit.

Keep Kernel paths:

- Cash: `GET /api/cash`, `POST /api/workflows/bank-reconciliation`
- Stripe: `GET /api/stripe`, `POST /api/workflows/stripe-reconciliation`

Do not invent a fee on Northstar. Do not connect live Stripe keys. Keep the simulated-mode pill.

---

## Files you may create

- `web/src/components/boards/PairingLanes.tsx`
- `web/src/components/boards/StripeWaterfall.tsx`
- tests beside them

## Files you may edit

- `web/src/pages/Cash.tsx` — rewrite. No `DemoLayout`. No `WhatsHappening`. No `StoryCard` on first paint.
- `web/src/pages/StripePage.tsx` — rewrite. Same bans.
- `web/src/styles.css` — append only `/* === 05 cash-desk === */`

## Files you must not edit

`AP.tsx`, `AR.tsx`, `Close.tsx`, `Forecast.tsx`, `Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `Shell.tsx`, `FlowPlay.tsx`, `Demo.tsx`, `Explain.tsx`, `copy.ts`, `handoffs.ts`.
`.cfo/`.

---

## `/cash` — PairingLanes

Prefix classes `.cash-`.

**Instrument:** two vertical lanes, Bank | Ledger, filling `.cash-stage` (min-height 420px). Each match from `report.matches` (or GET payload) is a chip on the bank side and chip(s) on the ledger side, connected by SVG.

Color via existing `statusTone` / `explainCashMatch`:

- `EXACT_MATCH` / grouped / `FEE_NETTED` → ok/brass line, solid
- `TXN-2026-09-011` + `FEE-729103` → explained. Label the fee id **on the line**
- `TXN-2026-09-015` → unexplained, `var(--bad)`, difference **$12.40**, **no** connecting solved line. Draw two stubs that do not meet. Caption on the gap: close cannot finish

**Default selection:** the unexplained pair. Do not default to grouped. Do not auto-scroll it out of view. If matches are empty (not yet run), still show featured GET `featured_cases.unexplained` bank vs ledger artifacts as two chips with the broken gap — the planted story must be visible **before** POST.

Replace the three story buttons with **the pairs themselves**. Clicking Helios or grouped re-targets the selection. You may keep a tiny legend: Matched · Explained fee · Unexplained.

**FlowPlay live** nodes: `bank`, `cash`, `ctl-cash`, `close` (close node `blocked` while unexplained exists).

**Run:** one primary button, same POST as today.

**Evidence `<details>`:** `SourceArtifactViewer` for the selected bank row and ledger rows. Default closed.

h1: `Bank vs books`. Stake ≤18 words: every deposit and withdrawal needs an explanation; this one does not have it.

---

## `/stripe` — StripeWaterfall

**Instrument:** `.cash-waterfall` horizontal (or vertical if width is tight) **bars**, not text.

From `current.breakdown` / `bd`:

1. + charges (`gross_payments`)
2. − refunds
3. − disputes / chargebacks
4. − fees
5. = expected payout (`expected_payout` ?? `net`)
6. vs bank deposit (`bank_deposit_amount`)

Each step is a bar whose length is proportional to `usd()` amount (use absolute values; label sign in the caption). Expected vs deposit are **aligned** so a mismatch is a visible overhang, `--bad`. Tie: `--ok`.

Delete `.waterfall-eq` from this page (do not have to delete the CSS global if other files still reference it; this page must not use the class).

Keep payout picker as a compact strip of ids, not a stack of essays. Keep `Pill` for simulated vs live from `data.mode`.

**FlowPlay live** nodes: `stripe` → `cash`, `stripe` → `apply`. Waterfall break may edge to `ctl-cash` dashed if not tied.

**Run:** `POST /api/workflows/stripe-reconciliation`. Same as today.

h1: `Stripe payout`. Stake: gross minus refunds, disputes, and fees should equal the bank deposit.

---

## Honesty

- Do not draw a fee artifact on `TXN-2026-09-015`.
- Do not resolve $12.40 in copy or in geometry.
- Stripe remains simulated unless the API says live — do not imply live keys.

---

## CSS

Append `/* === 05 cash-desk === */`

Lanes: two columns, chips `--surface-2`, selected unexplained `--bad-bg`. SVG lines in a layer above/behind chips; pointer-events on chips. Waterfall bars: height ~28px, labels in `.mono` + `usd()`.

---

## Tests

- Cash does not render `What's happening?` or `What arrived`.
- Cash render includes `12.40` or `TXN-2026-09-015`.
- Stripe render does not depend on `.waterfall-eq` (queryByText of the old “Customer charges” stack is ok if you relabel; **bars** must exist — test for a class `cash-waterfall` or role).
- Neither page claims the month `CLOSED` as success.

---

## Acceptance (browser)

`/cash` — two lanes visible; Northstar pair selected or clearly marked; $12.40 in the gap; Helios pair clickable if present after GET/run; POST path unchanged.

`/stripe` — bars for the waterfall; expected vs deposit comparison is visual; mode pill remains; POST path unchanged.

Neither page uses `<DemoLayout`.

`npm test`, `npm run build`. Empty matches: no crash.

When you finish, list PairingLanes + StripeWaterfall and the POST paths.

## Ban

If Cash still uses three story buttons as the hero and artifact viewers as the stage, you failed. If Stripe still prints a monospace equation as the waterfall, you failed. If you wrap PairingLanes in `DemoLayout`, you failed.
