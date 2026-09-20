# Prompt 08 — Remaining routes (the rest of the console)

You are one implementing agent. You own every route that would otherwise **still look like the old website** after Prompts 02–07 land: Inbox, Audit, Memory, Agents, Simulations, Evaluations, Videos.

If you skip this prompt, a sponsor who clicks Memory or Inbox falls back into `DemoLayout`. The overhaul is then a thin pitch over a console.

You do not edit Overview, Workflow, Coverage, AP, AR, Cash, Stripe, Close, Forecast, Architecture, or Shell.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. The page files listed below
5. `web/src/App.test.tsx` — **you must rewrite assertions** that freeze the old console
6. `web/src/components/FlowPlay.tsx` — import when a small pipe graph helps; if missing, you may ship Inbox/Audit/Memory without FlowPlay rather than blocking

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why these pages fail

They are not “extra.” They are the same `DemoLayout` disease plus two brochure pages.

| Route | File | First-paint disease |
| --- | --- | --- |
| `/inbox` | `Inbox.tsx` | `DemoLayout` + `WhatsHappening` (quote vs bill) + sample `<table>` in `runBar` + IO columns + artifact viewers |
| `/audit` | `Audit.tsx` | `DemoLayout` + essay that audit is independent + findings as `ResultBlock` text |
| `/memory` | `Memory.tsx` | `DemoLayout` + Harbor August→September essay + artifacts in IO columns |
| `/agents` | `Agents.tsx` | `PageHead` “The finance team” + directory + `AgentPanel` — a second Architecture without edges |
| `/simulations` | `Simulations.tsx` | Card grid + “Live office runners” chips that **duplicate** `/ap` `/cash` etc. |
| `/evaluations` | `Evaluations.tsx` | `DemoLayout` “Evaluation Lab” + `WhatsHappening` + gauntlet as a wall of lists |
| `/videos` | `Videos.tsx` | Honest placeholders under a long lede. Content can stay. The fold should not apologize. |

`App.test.tsx` currently **requires** `/inbox` to contain “What arrived” and “What changed”. That test is part of the disease. Change the test. Do not keep DemoLayout to satisfy it.

The same file requires `/agents` to contain “The finance team” and `/evaluations` to contain “connected finance work” / “Evaluation Lab”. Update those assertions to the new titles you ship.

---

## Mission

Each of these seven routes becomes a **different instrument**, still invoking the same Kernel POSTs. Prefix classes `.rest-`.

Banned on every page you own: `DemoLayout`, `WhatsHappening`, `StoryCard` on first paint, `.io-flow` as the skeleton, `PageHead` lede >18 words.

Allowed: `SourceArtifactViewer` inside `<details>`, `ProcessPanel` after a run, `RunBar` compact, `SimulationCard` internals if you restyle the index, `VideoShowcase` if you keep honest placeholders.

---

## Files you may edit

- `web/src/pages/Inbox.tsx`
- `web/src/pages/Audit.tsx`
- `web/src/pages/Memory.tsx`
- `web/src/pages/Agents.tsx`
- `web/src/pages/Simulations.tsx`
- `web/src/pages/Evaluations.tsx`
- `web/src/pages/Videos.tsx`
- `web/src/App.test.tsx` — assertions named above. Do not remove `test.each(ROUTES)` or the “Invoice approved” guard. Do not delete routes from `App.tsx`.
- `web/src/styles.css` — append only `/* === 08 remaining-routes === */`

You may create components under `web/src/components/rest/` (inbox stage, findings wall, memory periods, activity tape, gauntlet board). Do not put them in `components/boards/` (Prompts 04–06 own that folder).

## Files you must not edit

`Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`, `Architecture.tsx`, `ArchitectureDiagram.tsx`, `Shell.tsx`, `FlowPlay.tsx`, `copy.ts`, `handoffs.ts`, `Demo.tsx` (import only), `eventStories.ts`.
`.cfo/`.

Do not add npm packages. Do not fake videos. Do not treat gauntlet 42/42 as the office score.

---

## `/inbox` — Classify stage

Kernel: `GET /api/inbox`, `POST /api/workflows/invoice-ingestion` `{ sample_id }`, `POST /api/workflows/inbox`.

**Instrument:** two panes. Left: the email/document (use `SourceArtifactViewer` **here** — this page *is* the document). Right: a **stamp** of the Kernel class (invoice / quote / statement / receipt / other) after run, idle hollow before run.

Sample chooser: horizontal chips from `catalog.samples`, not a full-page table in the run bar. Default `MSG-E-MESSY` may stay.

h1: `What arrived`. Stake: a quote is not a bill. (Yes, the word “arrived” may appear as the title. The App.test must not require the **IO column label** “What arrived” plus “What changed” together as DemoLayout. Assert the stamp / chips instead.)

FlowPlay optional: `email` → `ap` on invoice class. Quotes do not edge to `ap` as approved work.

Do not say World sent a reply.

---

## `/audit` — Findings wall

Kernel: `GET /api/audit`, existing audit POST on the page (keep the same path; grep before changing).

**Instrument:** a wall of finding tiles (severity as fill: `--bad-bg` / `--warn-bg`). Each tile: title, `formatControlResult`, record ids in `.mono` (`TraceIds`). Featured self-approval / duplicate / round-wire become tiles, not `explainFinding` essays as the page body. You may keep `explainFinding` **inside** a selected tile.

h1: `Independent tests`. Stake: audit samples after the fact; it does not pay bills.

Do not invent findings. Empty wall + Run is honest.

---

## `/memory` — Two periods

Kernel: keep `POST /api/workflows/memory` `{ story: "harbor" | "stripe" }` and `memory-eval`.

**Instrument:** two columns **August | September**. Retrieval is an arrow. Harbor Electric is the default thread: August decision chip → September re-check chip. If Kernel reused the method, the arrow is solid; if it deviated, dashed + deviation text.

Memory-eval comparison (on vs off) is a second view toggle, not three `WhatsHappening` paragraphs.

h1: `August still matters`. Stake: reuse a treatment only when current evidence still supports it. Semantic graph / RAG is not built — do not draw a graph DB.

---

## `/agents` — Activity tape

This page must **stop being Architecture**. Prompt 07 owns the graph.

**Instrument:** a vertical tape of `data.activity` (workflow, bots via `formatHandoff`, status). Empty: “Run a simulation to append real agent activity. Events are not fabricated.”

A compact directory of 15 slugs may sit as a filter for the tape. Clicking a slug filters the tape; it does not open the full `AgentPanel` essay stack as the page. One-line role max. Link to `/architecture` “Open office graph”.

h1: `What the Bots just did`.

Update App.test: it currently looks for `/The finance team/i`. Change it to your new h1 or `/What the Bots just did/i`. Keep the guards that reject “Fifteen bots” and “43 autonomous agents”.

---

## `/simulations` — Catalog, not a second office

Index: drop or demote the “Live office runners” chip row that duplicates `/ap` `/cash` `/close`. One muted line may say live desks live in the office nav.

Keep `SIMULATIONS` cards. Status remains honest: Runnable until this machine scored the case. Do not show expected answers before a run (`friendlyExpected` only after score, as today).

Detail: keep Run + ProcessPanel + artifacts, but **not** DemoLayout. Stage: title, run, FlowPlay live if stages exist, artifacts in `<details>`.

---

## `/evaluations` — Scoreboard

Kernel: keep `POST /api/workflows/gauntlet` and `evaluate`.

**Instrument:** a scoreboard. Families as rows or cells. After a scored run, pass/fail marks from the payload. Before a run: hollow cells, **hidden gold**. Caption on any 42/42 or 97%: **Kernel measure, not the office score.**

Delete `WhatsHappening`. Delete “Evaluation Lab” as a three-paragraph product. h1: `Kernel gauntlet` (or `Measured work`). Stake: same workflows, hidden expected outcomes.

Trap / Harbor / Stripe / correction stories: compact links or a secondary strip, not four essays above the fold.

Update App.test that looks for `/connected finance work/i` and `/Evaluation Lab/i`.

---

## `/videos`

Keep honest placeholders (`VIDEOS`, `VideoShowcase`). Short h1: `Recordings`. Stake ≤18 words: cards are placeholders until a real file exists. Do not fake success clips. Do not add stock video.

---

## App.test.tsx (required edits)

Replace:

```ts
test("demo layout exposes what arrived and what changed", ...)
```

with a test that Inbox renders without `Invoice approved`, and that a classify/sample control exists (chip, button, or heading `What arrived` as **h1** is fine — do not require both IO labels).

Update agents + evaluations tests to the new copy. Keep:

- `ROUTES` arrayContaining the existing paths
- `test.each(ROUTES)` Office of the CFO + no `Invoice approved`

---

## CSS

Append `/* === 08 remaining-routes === */`

Each instrument uses `.rest-inbox`, `.rest-findings`, `.rest-memory`, `.rest-tape`, `.rest-gauntlet`. Do not restyle `.io-flow` globally (other agents may still be landing). You are not using it.

---

## Tests (yours)

- Inbox, Audit, Memory do not render `What's happening?`.
- Agents does not render a full Architecture-style “Who it works with” essay as the first screen (link to graph instead).
- Evaluations caption, if it mentions 42 or 97, includes `Kernel`.
- Videos still have no fake `HARDCODED_PASS` (architecture.test blob).

---

## Acceptance (browser)

Visit `/inbox`, `/audit`, `/memory`, `/agents`, `/simulations`, `/evaluations`, `/videos`. None of them show three IO columns as the page. Each has a distinct instrument. Kernel buttons that existed still call the same `/api/workflows/*` paths (grep to confirm).

`npm test`, `npm run build`.

When you finish, list each route and the instrument name you shipped, plus the App.test tests you changed.

## Ban

If you “collapse WhatsHappening into details” and keep `DemoLayout` on Inbox/Audit/Memory/Evaluations, you failed this prompt. If Agents is still a duplicate of Architecture, you failed. If you leave App.test requiring “What arrived” + “What changed”, you failed.
