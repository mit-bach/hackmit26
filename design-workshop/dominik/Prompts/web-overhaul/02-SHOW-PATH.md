# Prompt 02 — Show path (three invoices, one set of books)

You are one implementing agent. You own **`/workflow`**. You replace a nine-card AP essay with the public plot CAPABILITIES.md already named: CLEAN, RESOLVED, UNRESOLVED.

You do not build FlowPlay (import it). You do not touch Coverage, live desks, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `.cfo-v2/office/final-demo/CAPABILITIES.md` — section **Show path (public)**
5. `web/src/pages/Workflow.tsx`
6. `web/src/data/workflowStory.ts`
7. `web/src/components/FlowPlay.tsx` — **must already exist**. If it does not, stop.

Do not read prompts 03–08.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why `/workflow` fails

Open `Workflow.tsx`. The entire page is:

- `PageHead` eyebrow “One piece of work”, title “Follow a vendor invoice through the office”, a 50-word lede about “the real handoff graph”
- `<ol className="story-timeline">` mapping `INVOICE_STORY` (nine steps)
- Each step: number, agent display name, title, body paragraph, optional handoff sentence
- Two buttons: “Run a live invoice simulation” / “See the full agent graph”

`workflowStory.ts` is a generic vendor-invoice cartoon. It never names `INV-001`, `FEE-729103`, or `TXN-2026-09-015`. A sponsor who finishes this page has not seen the planted books. They have read a blog post about AP.

Adding tabs on top of those nine cards is **not** this prompt. Deleting the list and putting FlowPlay under a `PageHead` with a long lede is **not** enough. The page must become a **docket + stage**.

---

## Mission

`/workflow` is the second stop on the sponsor walk (after Home). It is a theater for three case files that share one set of books.

When the Unresolved case plays, the room should feel stuck. When Clean plays, the same IDs should travel from AP to bank to forecast to audit **on screen**, not in a paragraph that claims they do.

Support `?story=clean|resolved|unresolved` so Prompt 03 can deep-link. Default: `clean`.

---

## Files you may create

- `web/src/data/showPath.ts` — three stories as FlowPlay `nodes` / `edges` / `steps` plus `ids: string[]` and a short outcome label
- `web/src/pages/Workflow.test.tsx`
- `web/src/data/showPath.test.ts`

## Files you may edit

- `web/src/pages/Workflow.tsx` — **rewrite**. Do not keep the `<ol className="story-timeline">` in the first paint. You may put a “Read as a list” `<details>` **below the stage**, closed by default.
- `web/src/data/workflowStory.ts` — keep exporting `INVOICE_STORY` so `architecture.test.ts` still compiles. Make it the CLEAN spine (same 15-grain slugs). Prefer `INVOICE_STORY` derived from `showPath.ts` CLEAN steps.
- `web/src/styles.css` — append only `/* === 02 show-path === */`

## Files you must not edit

`Overview.tsx`, `FlowPlay.tsx`, `EventBoard.tsx`, `eventStories.ts`, `Coverage.tsx`, `CoverageGrid.tsx`, `capabilities.ts`, live office pages, `Architecture.tsx`, `Shell.tsx`, `copy.ts`, `App.tsx`, `App.test.tsx`, `handoffs.ts`, `Demo.tsx`, `Explain.tsx`.
`.cfo/`, `.cfo-v2/` (except you **read** CAPABILITIES.md).

---

## Page to build (not a suggestion)

Delete the current return. Build this:

```
.docket
  aside.docket-rail
    three <button> case files, stacked, full rail width
      CLEAN     Acme · MATCHED
      RESOLVED  Helios · FEE_NETTED
      UNRESOLVED Northstar · $12.40 · BLOCKED
    each button shows 2–3 mono IDs immediately (not after click)
    Unresolved uses var(--bad) on the amount, not a red page
  section.docket-stage
    .id-ticker  sticky, every ID for the active case as .mono pills
    FlowPlay    mode="story" autoplay on case change (reset to step 0, play once)
                min-height 420px
    .step-now   current step title, 1–3 manipulation chips, handoff line
    .docket-exits  text links into live routes WITH the ID visible
```

No `PageHead` lede. A single h1 is allowed: `Three invoices, one set of books`. One line under it, ≤18 words: the same identity must mean the same thing in payables, the bank, close, forecast, and audit.

Case buttons are **not** a native `<select>` and **not** an underline tab row that looks like the rest of the site’s `.tabs`. They are case files. The active case has a brass inset (reuse `.nav-link.active` language: inset shadow / border), not a filled marketing button.

### Exits (required)

- Clean → `/ap` with `INV-001` visible in the link text; `/cash` with `TXN-2026-09-018A`
- Resolved → `/cash` with `TXN-2026-09-011` and `FEE-729103`; `/close`
- Unresolved → `/cash` with `TXN-2026-09-015`; `/close` — copy: month cannot finish

You do not need query params on `/ap` or `/cash` (those pages are other agents). Visible IDs in the link text are enough.

---

## Story graphs (required beats)

Each story is its own `nodes` / `edges` / `steps` in `showPath.ts`. Do not reuse Home’s `eventStories.ts` (Prompt 01 owns that file; you may **read** it for style). Do not edit it.

**CLEAN** — event vendor email → `email` classify → `ap` three-way APPROVE (`INV-001` / `PO-101` / `GR-101`) → `ctl-pay` concur → `pay` includes `PAY-AP-001` → `cash` MATCHED `TXN-2026-09-018A` → `story` / forecast same ID → `audit` can sample. No World node. End status `done`.

**RESOLVED** — `bank` / `cash` see Helios `INV-017` / `TXN-2026-09-011` $25 over → fee evidence `FEE-729103` → match type FEE_NETTED (use `formatMatchType` from `copy.ts`) → `ctl-cash` sign-off → `close` accepts explained exception. Do not call this “unexplained.” Do not use `status: "blocked"` on close.

**UNRESOLVED** — `PAY-006` / `INV-AR-013` $12,400.00 vs bank `TXN-2026-09-015` $12,412.40 → `cash` unexplained difference → `close` evaluate gates fail → `ctl-books` does not lock. Node `close` or lock step `status: "blocked"`. Copy: Maximor will not invent a $12.40 fee. **Do not** mention holdout residual theory (`ADV-CASH-014`, `SL-ADV-RESIDUAL`) on this page.

Each step `manipulations` array is 1–3 short Kernel verbs (`match three-way`, `refuse unexplained`, `hold lock`). `artifactIds` must include the IDs from the ticker as they enter the story.

FlowPlay `kind`: events `event`, operators `operator`, `ctl-*` `verifier`, `audit` `assurance`.

---

## Query string

On mount, read `useSearchParams()`. `story=resolved` selects RESOLVED. Unknown values fall back to CLEAN. Changing case updates the query with `setSearchParams` so Coverage deep-links stay shareable.

---

## CSS

Append `/* === 02 show-path === */`

`.docket` is a two-column grid: rail ~260px, stage 1fr. On a narrow main column, stack rail on top as a horizontal row of three case files (do not let the rail eat the graph). `.id-ticker` stays visible while scrolling the stage. Manipulation chips are small `.pill`s, not paragraphs.

Do not restyle `.story-timeline` as the primary — you are not using it on first paint.

---

## Tests

- Workflow render includes `Clean` / `Resolved` / `Unresolved` (or Acme / Helios / Northstar — pick one set and use it in the test; the rail must name all three cases).
- CLEAN ticker includes `INV-001` and `TXN-2026-09-018A`.
- UNRESOLVED copy includes `12.40` or `$12,412.40` and does not include the word `CLOSED` as a success.
- `INVOICE_STORY` still exports an array whose `agent` values are grain slugs (architecture.test).
- Optional: `/workflow?story=unresolved` selects the Unresolved case.

---

## Acceptance

1. First paint of `/workflow` is docket + FlowPlay. The nine-card `<ol>` is gone or buried in closed `<details>`.
2. Switching cases changes nodes, ticker IDs, and exits.
3. CLEAN ticker shows `INV-001`, `PO-101`, `GR-101`, `PAY-AP-001`, `TXN-2026-09-018A`.
4. RESOLVED names `FEE-729103` and FEE_NETTED.
5. UNRESOLVED never claims close finished.
6. `npm test`, `npm run build`. Browser: click all three cases; confirm graph + IDs. Open `?story=unresolved` directly.

When you finish, paste the three ticker ID lists as they render.

## Ban

If `Workflow.tsx` still opens with `PageHead` + `INVOICE_STORY.map` as the body, you failed. If you kept the list and added FlowPlay under it, you failed.
