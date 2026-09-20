# Prompt 04 — Office graph, pitch nav, honesty

You are one implementing agent. You own **how a sponsor moves through the site** and the **real agent graph**. You do not rebuild FlowPlay (import it). You do not rewrite Workflow stories or live AP/Cash boards.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. This file
3. `web/src/layout/Shell.tsx`
4. `web/src/pages/Architecture.tsx`
5. `web/src/components/ArchitectureDiagram.tsx`
6. `web/src/components/AgentPanel.tsx`
7. `web/src/data/handoffs.ts`
8. `web/src/data/agents.ts`
9. `web/src/copy.ts` — `AGENT_ALIASES` (you fix the World lie)
10. `web/src/components/FlowPlay.tsx` — **must exist**. If missing, stop.
11. `web/src/App.tsx` (routes — do not delete live routes)

Do not read prompts 01–03 except shared laws.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

Two failures:

1. **ArchitectureDiagram** is four room columns of buttons. Handoffs render as paragraphs after click. No edges. A sponsor cannot see the office as a network.
2. **Nav** is 8 Showcase links + 9 Live office links. There is no five-minute spine. `/scenarios` aliases simulations and is not in the nav. `copy.ts` maps `Counterparty Message Agent` → `email`, which hides that World is not a live Bot.

You will: draw the office with FlowPlay (or a dedicated ArchGraph built on FlowPlay), add World as **not-attached**, regroup the sidebar for a pitch, fix the alias, keep every live route reachable.

---

## Files you may create

- `web/src/components/OfficeGraph.tsx` — FlowPlay wrapper with all 15 Bots + dashed World
- `web/src/data/officeGraph.ts` — nodes/edges compiled from `HANDOFFS` + World extras
- `web/src/data/officeGraph.test.ts`
- `web/src/copy.test.ts` updates if alias tests exist

## Files you may edit

- `web/src/layout/Shell.tsx` — PRIMARY / SECONDARY nav only (and PageHead if needed)
- `web/src/pages/Architecture.tsx`
- `web/src/components/ArchitectureDiagram.tsx` — replace implementation with OfficeGraph, **keep the export name and props** `{ selected, onSelect }` so Architecture.tsx can stay similar
- `web/src/data/handoffs.ts` — add World-related edges with a field the graph uses for `attached: false`. Do not delete existing 25 edges. Suggested extra edges (not attached):
  - `{ from: "email", to: "world", when: "outbound", profile: "vendor", why: "Missing-info mail would wake the simulated counterparty. World is not on the live roster." }`
  - `{ from: "collect", to: "world", when: "dun", profile: "customer", why: "Dunning would send_office_outbound then Handle World. That op is not on the live catalog." }`
  - `{ from: "world", to: "email", when: "delivered", profile: "triage", why: "Inbound persona mail would land on Email triage after deliver." }`
  You will need `world` in the graph even though `AgentSlug` currently excludes it. **Do not add `world` to `GRAIN_SLUGS`** (that array is the live 15). In `officeGraph.ts` use `id: "world"` as a string outside `AgentSlug`. Type edges as `from: string; to: string` in the graph file. If you extend `Handoff.to` typing, use `AgentSlug | "world"` only in `handoffs.ts` if it does not break `agents.ts`. Prefer keeping `HANDOFFS` typed as today and putting World edges only in `officeGraph.ts` to avoid a slug-type war. **Best: World edges live only in `officeGraph.ts`, not in HANDOFFS.** Then you must not edit `handoffs.ts` at all.

**Prefer zero edits to `handoffs.ts`.** Put World edges in `officeGraph.ts` only.

- `web/src/copy.ts` — `AGENT_ALIASES` only: remove `"Counterparty Message Agent": "email"`. If formatAgent needs a name for `world`, add `AGENT_COPY` entry only if `agents.ts` is the right home — **prefer adding a `WORLD_AGENT` constant in `officeGraph.ts`** and a one-line alias `"world": "world"` is wrong. Add to `AGENT_COPY` in `agents.ts` **only if** you can do it without claiming World is in `GRAIN_SLUGS`. Safest: `formatAgent('world')` returns “World (not on live roster)” via a new `AGENT_ALIASES` or a special case in `formatAgent` — **minimal change**:

```ts
// copy.ts AGENT_ALIASES: delete Counterparty → email
// formatAgent: if key is world or World, return "World (simulated mailbox, not on live roster)"
```

Grep `Counterparty Message Agent` before changing.

- `web/src/styles.css` — append `/* === 04 arch-graph + shell-nav === */`
- `web/src/data/architecture.test.ts` if it asserts diagram structure

## Files you must not edit

`Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`, `FlowPlay.tsx` (import only), `Demo.tsx`, `eventStories.ts`, `showPath.ts`, `capabilityMatrix.ts`, board components under `components/boards/`.
Do not delete routes in `App.tsx`. You may add nothing. You may not remove `/inbox`, `/agents`, `/videos`, `/simulations`, `/evaluations`, `/memory`, `/audit`.

---

## Architecture page

Replace the button-grid rooms with **OfficeGraph**:

- 15 grain nodes in 4 room bands (intake / pay / cash / books-close). Room bands are labeled background rows or columns — still a **graph with edges**, not four isolated chip lists.
- Edges = all current `HANDOFFS` (25). Draw them. When nothing is selected, show **PRINCIPAL_FLOWS** as emphasized edges and other edges at low opacity. When a Bot is selected, emphasize incident edges (this already happens in prose; now do it on the SVG).
- Click a node: `onSelect(slug)`, AgentPanel on the right **stays**. You are not deleting the directory/panel; you are putting the graph first.
- World node sits beside intake, `not-attached`, dashed edges from `officeGraph.ts`. Tooltip/title: not on live roster. Clicking World still allowed: panel copy must say it is simulated / not bound. Do not fetch `/api/architecture` expecting a world bot. If `data.bots` has no world, panel uses static copy from officeGraph.

Routines card at the bottom: keep. These are not extra Bots.

Lede: shorten to one sentence. Remove “older larger agent list” apologetics from the first screen; one muted line at the bottom is enough.

### Density

25 edges will look like a hairball if all are equal. Required technique:

- Default: principal flows full opacity; other edges `opacity: 0.25`.
- Selected: incident edges opacity 1, others 0.12.
- Optional toggle: “Show all Handles” checkbox.

Do not draw a force-directed physics sim. Rank by room (4 columns) and order slugs as in GRAIN_SLUGS.

Verifier nodes (`ctl-*`) brass border via FlowPlay `kind: "verifier"`.

---

## Shell nav — five-minute spine without deleting the office

Current PRIMARY:

```
Home, Architecture, One invoice, Memory, Simulations, Videos, Coverage, Evidence
```

Change PRIMARY (Showcase → **Pitch**):

```
Home                  /
Office graph          /architecture
Three stories         /workflow
Capabilities          /coverage
Evidence              /evaluations
```

Current SECONDARY (Live office) — keep all live functions, order for the plot:

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

Move **Simulations** and **Videos** to a third nav group **More** (or under Live office at the bottom):

```
Simulations           /simulations
Videos                /videos
Reset books           (existing button)
```

Do not drop Videos; they stay honest placeholders.

Nav labels: “One invoice” becomes **Three stories** because Prompt 02 ships three tabs. If Prompt 02 has not landed yet, the route `/workflow` still exists (nine cards). Label can still be Three stories.

`/scenarios` remains an alias; do not add it to nav.

Topbar brand stays Maxi**mor** / Office of the CFO. Do not redesign the topbar except to keep status pills wrapping.

---

## Honesty copy sweep (limited)

Grep `web/src` for:

- `Counterparty Message Agent`
- `rubber-stamp`
- `human approval`
- `World`

Fix only files you own (`copy.ts`, Architecture, AgentPanel if it prints aliases, Shell). If AgentPanel lists connectors that imply live Gmail/Stripe, add one muted line: simulated connectors. Do not rewrite AgentPanel responsibilities lists.

If AgentPanel is too large to touch, only fix `copy.ts` + Architecture World panel.

---

## CSS

Append `/* === 04 arch-graph + shell-nav === */`

`.office-graph` min-height ~420px. Room labels 10px uppercase like `.nav-label`. World node `.not-attached`. Nav group `.nav-label` for Pitch / Live office / More.

Do not change `--sidebar` width unless Pitch labels wrap badly; if you must, 248px max.

---

## Tests

- `officeGraph.ts`: 15 grain ids present; `world` present; at least one edge with `attached: false`; every HANDOFFS edge present (from/to/when).
- `formatAgent("world")` includes “not on live roster” (or equivalent).
- `formatAgent` of a grain slug still returns `AGENT_COPY` name.
- Architecture test: if it queried `.arch-node` buttons, update to `.flow-node` / office graph buttons. Do not delete the test file.

---

## Acceptance

1. `/architecture` shows SVG/HTML **edges** between Bots without clicking.
2. Click `ap`: edges to `ctl-pay`, `pay`, `close` emphasize; AgentPanel shows AP.
3. World is visible, dashed, labeled not on live roster. Clicking it does not error if API bots omit world.
4. Sidebar Pitch group is five links: Home, Office graph, Three stories, Capabilities, Evidence.
5. All previous live routes still reachable in one click from Live office / More.
6. `Counterparty Message Agent` no longer formats as Email Agent.
7. Keyboard: graph nodes are buttons.
8. `npm test`, `npm run build`. Browser: click three Bots, World, and each Pitch nav link.

When you finish, paste the Pitch nav labels in order and confirm World’s on-screen label.
