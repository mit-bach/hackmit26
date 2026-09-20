# Prompt 02 — Three public stories + capability matrix

You are one implementing agent. You own the **sponsor plot** and the **honest capability wall**. You do not build the graph engine (Prompt 01). You do not redesign AP/Cash live pages (Prompt 03). You do not change the sidebar (Prompt 04).

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. This file
3. `.cfo-v2/office/final-demo/CAPABILITIES.md` (capability table + Show path)
4. `web/src/pages/Workflow.tsx`
5. `web/src/pages/Coverage.tsx`
6. `web/src/components/CoverageGrid.tsx`
7. `web/src/data/capabilities.ts`
8. `web/src/data/workflowStory.ts`
9. `web/src/copy.ts` — `CAPABILITY_COPY` only (you may extend that object)
10. `web/src/components/FlowPlay.tsx` — **must already exist**. If it does not, stop.

Do not read prompts 01, 03, 04 except the FlowPlay contract in shared laws.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

`/workflow` is currently nine cards telling one AP invoice story. A sponsor needs **three playable threads** that CAPABILITIES.md already named the public plot:

1. **STORY-CLEAN** — Acme `INV-001` = `PO-101` = `GR-101`, paid `PAY-AP-001`, bank `TXN-2026-09-018A` MATCHED, audit can re-perform, forecast uses the same ID.
2. **STORY-RESOLVED** — Helios `INV-017`, bank `TXN-2026-09-011` is $25 over books, `FEE-729103` supports FEE_NETTED, close accepts the explained exception.
3. **STORY-UNRESOLVED** — Northstar `INV-AR-013` / `PAY-006` books $12,400.00, bank `TXN-2026-09-015` is $12,412.40, no fee evidence, close stays **BLOCKED**.

`/coverage` is six prose cards (`ap, ar, cash, close, audit, forecast`). Replace it with a **matrix of every capability id** in CAPABILITIES.md, each with Kernel-live / Office-live / Not built, linking into the matching story or live route.

---

## Why this is a separate agent

This is narrative + truth-in-labeling. Mixing it with SVG engine work or cash-rec boards produces either pretty lies or another wall of text. You specialize in: planted IDs on screen at all times, status honesty, and a capability map a judge can audit.

---

## Files you may create

- `web/src/data/showPath.ts` — the three stories as FlowPlay `nodes` / `edges` / `steps` plus a `ids: string[]` list
- `web/src/data/capabilityMatrix.ts` — rows derived from CAPABILITIES.md (do not invent new capabilities)
- `web/src/pages/Workflow.test.tsx` and/or `web/src/data/showPath.test.ts`
- `web/src/data/capabilityMatrix.test.ts`

## Files you may edit

- `web/src/pages/Workflow.tsx` — rewrite
- `web/src/pages/Coverage.tsx` — rewrite
- `web/src/components/CoverageGrid.tsx` — replace internals to render the matrix (or a compact slice). Overview may still import `CoverageGrid` if Prompt 01 left a link; keep the export name so you do not break Overview. If Overview no longer imports it, Coverage.tsx can use a new name. **Grep before deleting the export.**
- `web/src/data/capabilities.ts` — replace the 6-domain array **or** leave it and stop using it. Prefer replacing with re-exports from `capabilityMatrix.ts` if anything still imports `CAPABILITIES`.
- `web/src/data/workflowStory.ts` — you may keep `INVOICE_STORY` as the CLEAN spine or migrate callers to `showPath.ts`. Grep `INVOICE_STORY` first. If Overview still maps `INVOICE_STORY.slice(0, 5)`, do not crash Home: keep the export as an alias of CLEAN steps or a thin compatibility array.
- `web/src/copy.ts` — **only** extend `CAPABILITY_COPY` with missing ids (see list below). Do not restyle `formatSummary`. Do not change `AGENT_ALIASES` (Prompt 04).
- `web/src/styles.css` — append only `/* === 02 story-play + capability-matrix === */`

## Files you must not edit

`Overview.tsx`, `FlowPlay.tsx`, `EventBoard`, `eventStories.ts`, live office pages (`AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`, `Inbox.tsx`, `Audit.tsx`, `Memory.tsx`, `Agents.tsx`), `ArchitectureDiagram.tsx`, `Shell.tsx`, `handoffs.ts`, `Demo.tsx`.
`.cfo/`, `.cfo-v2/` (except you **read** CAPABILITIES.md).

---

## `/workflow` — Three stories, playable

### UI

- PageHead eyebrow: `Show path`. Title: `Three invoices, one set of books`.
- Lede: one sentence. The same identity must mean the same thing in payables, the bank, close, forecast, and audit.
- **Three tabs** (buttons, not a native `<select>`): Clean · Resolved · Unresolved. Unresolved tab uses `var(--bad)` in a restrained way (active border), not a red page.
- Sticky **ID strip** under tabs: every ID for that story as `.mono` pills. They stay visible while FlowPlay plays.
- `FlowPlay` with `mode="story"` and `autoplay` on tab change (reset to step 0, play once).
- Under the graph: existing-style links into live pages, with the ID in the query or just as visible text:
  - Clean → `/ap` (INV-001), `/cash` (TXN-2026-09-018A)
  - Resolved → `/cash` (TXN-2026-09-011), `/close`
  - Unresolved → `/cash` (TXN-2026-09-015), `/close` — copy: month cannot finish
- Do **not** keep the nine-card `<ol className="story-timeline">` as the primary view. You may offer “Read as a list” collapsed `<details>` using the step titles.

### Story graphs (required beats)

**CLEAN** — event vendor email → email classify → ap three-way APPROVE (`INV-001`/`PO-101`/`GR-101`) → ctl-pay concur → pay includes `PAY-AP-001` → cash MATCHED `TXN-2026-09-018A` → story/forecast same ID → audit can sample. No World node.

**RESOLVED** — bank/cash see Helios `INV-017` / `TXN-2026-09-011` $25 over → fee evidence `FEE-729103` → match type FEE_NETTED → ctl-cash sign-off → close accepts explained exception. Do not call this “unexplained.”

**UNRESOLVED** — `PAY-006` / `INV-AR-013` $12,400.00 vs bank `TXN-2026-09-015` $12,412.40 → cash unexplained difference → close evaluate gates fail → ctl-books does not lock → node `close` or lock step `status: "blocked"`. Copy: Maximor will not invent a $12.40 fee. Do not mention the holdout residual theory (`ADV-CASH-014`) on this page.

Each step `manipulations` array is 1–3 short Kernel verbs. `artifactIds` must include the IDs from the strip as they enter the story.

### Tests

- Workflow render includes the three tab labels.
- CLEAN ID strip includes `INV-001` and `TXN-2026-09-018A`.
- UNRESOLVED copy includes `12.40` or `$12,412.40` and does not include the word `CLOSED` as a success.

---

## `/coverage` — Capability matrix

### Rows (must appear; copy titles from CAPABILITIES.md / CAPABILITY_COPY)

Intake: `inbox.counterparty_to_ap`, `ingestion.classify_document`, `ingestion.structured_parse`, `ingestion.bank_card_discovery`

AP: `ap.three_way_match`, `ap.payment_scheduling`, `ap.self_improvement`, `ap.vendor_bank_change`

AR: `ar.aging_collections`, `ar.cash_application`, `memory.self_improvement`

Cash: `cash.bank_reconciliation`, `cash.stripe_reconciliation`

Close: `close.accruals`, `close.prepaids`, `close.fixed_assets`, `close.balance_sheet_recs`, `close.month_end`

Rest: `audit.controls`, `reporting.variance_board`, `forecast.thirteen_week`, `memory.cross_period`, `orchestration.cfo`, `evaluation.finance_gauntlet`

You may omit `sample_data.generation` from the public wall, or include it as Kernel-live / not a floor Bot. If included, label “generator, not a Bot.”

### Status enum (one pill per row)

Use CAPABILITIES.md “Now” column, compressed:

| Status | When |
| --- | --- |
| `kernel-live` | Engine exists and is tested |
| `office-live` | A standing Harness Bot can take the work (CAPABILITIES says office-live) |
| `partial` | Real path, demo cannot show full lifecycle (World mailbox, Close Manager live=True) |
| `not-built` | `ap.self_improvement`, `ap.vendor_bank_change`. Semantic graph/RAG is not built — do not put it on this wall as a capability row unless CAPABILITIES lists it (it is a next-step under memory; keep memory.cross_period as kernel-live and do not claim a graph DB) |

`inbox.counterparty_to_ap`: **partial** (Kernel-live tools; roster omits World).
`ar.aging_collections`: office-live collect, World reply **partial**.
`evaluation.finance_gauntlet`: kernel-live; caption “Kernel measure, not the office score.”

### Columns

ID (mono, small) · What it does (one sentence from CAPABILITY_COPY, which you will extend) · Status pills · Agents (grain slugs) · Open (link)

Links:

- `ap.three_way_match` → `/workflow` clean tab if you support `?story=clean`, else `/ap`
- `cash.bank_reconciliation` / unresolved → `/workflow?story=unresolved` and `/cash`
- `cash.stripe_reconciliation` → `/stripe`
- `ar.cash_application` → `/ar`
- `close.month_end` → `/close`
- `forecast.thirteen_week` → `/forecast`
- `audit.controls` → `/audit`
- `orchestration.cfo` → `/` (cycle run) or `/simulations`
- `evaluation.finance_gauntlet` → `/evaluations`
- `inbox.counterparty_to_ap` → `/inbox` plus muted “World Bot not on live roster”

Implement `?story=clean|resolved|unresolved` on Workflow so Coverage links land on the right tab.

### CAPABILITY_COPY keys to add in `copy.ts`

Add only missing ones, same voice as existing entries (plain English, no Kernel jargon):

- `inbox.counterparty_to_ap`
- `ingestion.structured_parse`
- `ingestion.bank_card_discovery`
- `ap.self_improvement`
- `ap.vendor_bank_change`
- `memory.self_improvement`
- `cash.stripe_reconciliation`
- `orchestration.cfo`
- `evaluation.finance_gauntlet`

Do not add holdout/adversarial catalog rows.

### CoverageGrid compact mode

If `compact` is still used, render a **small matrix** of the six function groups (intake, AP, AR, cash, close, story/audit) with a count of live vs not-built, plus link to `/coverage`. Do not bring back six essay cards.

---

## CSS

Append `/* === 02 story-play + capability-matrix === */`

Suggested: `.story-tabs`, `.id-strip`, `.cap-table` (use a real `<table>` or CSS grid; this is a matrix, not cards). Status pills reuse existing `.pill.ok|.warn|.bad|.info`. Map: kernel-live → info or ok, office-live → ok, partial → warn, not-built → faint/neutral. Unresolved tab active → bad border.

---

## Acceptance

1. `/workflow` shows three tabs. Switching tabs changes FlowPlay nodes and the ID strip.
2. CLEAN strip shows `INV-001`, `PO-101`, `GR-101`, `PAY-AP-001`, `TXN-2026-09-018A`.
3. RESOLVED names `FEE-729103` and FEE_NETTED (use existing `formatMatchType` if you import it).
4. UNRESOLVED never claims close finished. `$12.40` or `$12,412.40` visible.
5. `/coverage` lists `ap.self_improvement` as not-built and `inbox.counterparty_to_ap` as partial. No six-card finance/maximor essays as the page body.
6. `/coverage` row click or Open link to `/workflow?story=unresolved` opens the Unresolved tab.
7. `npm test`, `npm run build`. Browser: click all three tabs; confirm graph + IDs.

When you finish, paste the capability row count and the three ID strips as they render.
