# Prompt 07 — Office graph + pitch nav + World honesty

You are one implementing agent. You own **how a sponsor moves** and **the real agent graph**. You replace four columns of buttons with a graph that has edges on first paint. You regroup the sidebar into a five-minute pitch. You stop mapping Counterparty Message Agent to Email.

You do not rebuild Workflow, Coverage, or live desks. You do not edit Overview (Prompt 01).

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file
4. `web/src/layout/Shell.tsx`
5. `web/src/pages/Architecture.tsx`
6. `web/src/components/ArchitectureDiagram.tsx`
7. `web/src/components/AgentPanel.tsx`
8. `web/src/data/handoffs.ts`
9. `web/src/data/agents.ts`
10. `web/src/copy.ts` — `AGENT_ALIASES` and `formatAgent`
11. `web/src/components/FlowPlay.tsx` — must exist. If missing, stop.
12. `web/src/App.tsx` — routes. Do not delete live routes.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Why these surfaces fail

**ArchitectureDiagram** (`ArchitectureDiagram.tsx`):

- `.arch-shared` card: essay “One picture of the company”
- `.arch-rooms`: four columns, each a title, a muted paragraph, and **buttons** (`.arch-node`)
- `.arch-flows`: `PRINCIPAL_FLOWS` as `.chip`s with **no geometry**
- Selected: a card of **paragraphs** (“The X handed this to the Y. {why}”)
- Zero SVG. Zero edges until you imagine them.

`Architecture.tsx` then adds a `grid-2`: directory + `AgentPanel` (responsibilities, skills, profiles, more paragraphs) + a routines list. The graph never happens. The page is an org-chart brochure.

**Nav** (`Shell.tsx`):

PRIMARY (Showcase): Home, Architecture, One invoice, Memory, Simulations, Videos, Coverage, Evidence — eight equal links. The walk is invisible.

SECONDARY (Live office): nine function links + Reset books.

`/scenarios` aliases simulations and is not in the nav (keep that).

**Lie:** `copy.ts` `AGENT_ALIASES["Counterparty Message Agent"] = "email"`. World is not a live Bot. This alias makes outbound mailbox look attached.

---

## Mission

1. `/architecture` **is** a network. Edges visible with nothing selected. World is a dashed not-attached node.
2. Sidebar **Pitch** is the sponsor walk: Home, Office graph, Three stories, Capabilities, Evidence.
3. Live routes stay one click away. Simulations and Videos move to **More**. Memory moves to Live office (it is a desk, not a pitch peer).
4. `formatAgent` no longer reports Counterparty Message Agent as Email Agent. `formatAgent("world")` says it is not on the live roster.

---

## Files you may create

- `web/src/components/OfficeGraph.tsx` — FlowPlay wrapper, 15 Bots + dashed World
- `web/src/data/officeGraph.ts` — nodes/edges from `HANDOFFS` + World extras
- `web/src/data/officeGraph.test.ts`

## Files you may edit

- `web/src/layout/Shell.tsx` — PRIMARY / SECONDARY / add More. Do not redesign the topbar brand or status pills except wrapping.
- `web/src/pages/Architecture.tsx` — rewrite the **layout**. Keep AgentPanel as an **inspector**, not 50% of the first screen.
- `web/src/components/ArchitectureDiagram.tsx` — replace implementation with OfficeGraph. **Keep the export** `ArchitectureDiagram` and props `{ selected, onSelect }` if Architecture still uses those names.
- `web/src/copy.ts` — `AGENT_ALIASES` and `formatAgent` only (see Honesty). Grep `Counterparty Message Agent` first. Update `copy.test.ts` if it asserts the old alias.
- `web/src/data/architecture.test.ts` — if it queried `.arch-node` buttons, update to `.flow-node` / office graph buttons. Do not drop the 15-slug test.
- `web/src/styles.css` — append only `/* === 07 office-graph + shell-nav === */`

**Prefer zero edits to `handoffs.ts`.** Put World edges only in `officeGraph.ts` with `from`/`to` as `string` and `attached: false`. Do **not** add `world` to `GRAIN_SLUGS`.

## Files you must not edit

`Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`, `Inbox.tsx`, `Audit.tsx`, `Memory.tsx`, `Agents.tsx`, `Simulations.tsx`, `Evaluations.tsx`, `Videos.tsx`, `FlowPlay.tsx`, `Demo.tsx`, `eventStories.ts`, `showPath.ts`, `capabilityMatrix.ts`, `components/boards/*`.

Do not delete routes in `App.tsx`. Do not add routes unless you need none. Do not remove `/inbox`, `/agents`, `/videos`, `/simulations`, `/evaluations`, `/memory`, `/audit`.

You may **read** `AgentPanel.tsx`. Edit it only if World click would crash (no `AGENTS_BY_SLUG.world`). Safer: OfficeGraph click on World sets selected to `"world"` and Architecture renders a static panel from `officeGraph.ts`, not `AGENTS_BY_SLUG[world]`.

---

## Architecture page to build

First paint:

```
h1  The office
one line ≤18 words: fifteen standing Bots, Handles between them, World not attached
OfficeGraph  min-height 480px, full width
inspector    slide-over or right rail ~320px, ONLY after a node click (or a persistent slim rail)
routines     below the graph, muted, “these are not extra Bots”
```

Delete the “older, larger agent list” apology from the first screen. One muted line at the bottom is enough if you need it.

### Graph rules

- 15 grain nodes in 4 room bands (intake / pay / cash / books-close). Bands are labeled backgrounds. This is still a **graph with edges**, not four chip lists.
- Edges = all current `HANDOFFS` (25). Draw them on first paint.
- Default: `PRINCIPAL_FLOWS` related edges full opacity; other edges `opacity: 0.22`.
- Selected: incident edges opacity 1, others 0.12.
- Optional checkbox: “Show all Handles”.
- No force-directed physics. Rank by room columns; order slugs as in `GRAIN_SLUGS`.
- Verifiers `ctl-*` use FlowPlay `kind: "verifier"` (brass).
- `audit` `kind: "assurance"`.
- World sits beside intake, `status: "not-attached"`, dashed edges. Title: not on live roster. Click does not fetch a world bot from `/api/architecture`. If `data.bots` has no world, static copy: simulated mailbox, not bound, `send_office_outbound` not on the live catalog.

Suggested World edges (officeGraph only, `attached: false`):

- `collect` → `world` (dun)
- `email` → `world` (outbound missing-info)
- `world` → `email` (delivered inbound)

### Inspector

Do not lead with the full `AgentPanel` essay stack. Show: name, room, 3–5 outbound Handles as labeled edges (the graph already shows them — inspector lists why). Skills/profiles can live in a nested `<details>`. Directory list is optional; the graph **is** the directory.

---

## Shell nav

Change PRIMARY label **Showcase** → **Pitch**:

```
Home                  /
Office graph          /architecture
Three stories         /workflow
Capabilities          /coverage
Evidence              /evaluations
```

SECONDARY **Live office** (functions, plot order):

```
Inbox                 /inbox
Payables              /ap
Receivables           /ar
Cash                  /cash
Stripe                /stripe
Close                 /close
Forecast              /forecast
Audit                 /audit
Memory                /memory
Team activity         /agents
```

Third group **More**:

```
Simulations           /simulations
Videos                /videos
Reset books           (existing button)
```

“One invoice” becomes **Three stories** even if Prompt 02 has not landed yet (`/workflow` still exists).

Do not add `/scenarios` to nav.

Topbar: Maxi**mor** / Office of the CFO. Status pills stay. Sidebar width: only if Pitch labels wrap, max 248px.

---

## Honesty copy

In `copy.ts`:

- Delete `"Counterparty Message Agent": "email"`.
- `formatAgent`: if the key is `world` or `World`, return `World (simulated mailbox, not on live roster)` (or equivalent that includes “not on live roster”).
- Grain slugs still resolve through `AGENT_COPY`.

Grep `web/src` for `Counterparty Message Agent`, `rubber-stamp`, `human approval`. Fix only files you own (copy.ts, Architecture, AgentPanel if you touch it, Shell). Do not rewrite AgentPanel responsibility lists.

If AgentPanel implies live Gmail/Stripe connectors, one muted line: simulated connectors — only if you are already editing that file.

---

## CSS

Append `/* === 07 office-graph + shell-nav === */`

`.office-graph` min-height ~480px. Room labels 10px uppercase like `.nav-label`. World `.not-attached`. Third nav group uses existing `.nav-label`.

---

## Tests

- `officeGraph.ts`: 15 grain ids present; `world` present; at least one edge `attached: false`; every `HANDOFFS` from/to/when present.
- `formatAgent("world")` includes “not on live roster”.
- `formatAgent("ap")` still returns the AP display name from `AGENT_COPY`.
- Architecture: nodes are buttons; edges exist in the document (svg `path`/`line` or FlowPlay edges) without clicking.
- Nav: Pitch labels include `Three stories` and `Capabilities`.

---

## Acceptance

1. `/architecture` shows edges between Bots with nothing selected.
2. Click `ap`: edges to `ctl-pay`, `pay`, `close` emphasize; inspector shows AP; no crash.
3. World visible, dashed, not on live roster; click does not error.
4. Sidebar Pitch is those five links in order.
5. Every previous live route is one click from Live office or More.
6. `Counterparty Message Agent` no longer formats as Email Agent.
7. `npm test`, `npm run build`. Browser: click three Bots, World, each Pitch link.

When you finish, paste the Pitch labels in order and World’s on-screen label.

## Ban

If Architecture still uses `.arch-rooms` button grids as the graph, you failed. If you only added FlowPlay under the button rooms, you failed. If Pitch is the old eight Showcase links with renamed “One invoice”, you failed — Memory/Simulations/Videos must leave Pitch.
