# Prompt 01 — FlowPlay engine + Home event board

You are one implementing agent. You own the **visual engine** and the **first ten seconds of the sponsor walk**. Other agents will import your component. If you make FlowPlay vague, they will ship more prose.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. This file
3. `web/src/pages/Overview.tsx`
4. `web/src/components/HowItWorks.tsx`
5. `web/src/data/handoffs.ts`
6. `web/src/data/workflowStory.ts`
7. `web/src/data/agents.ts` (GRAIN_SLUGS, ROOMS, AGENTS)
8. `web/src/components/Demo.tsx` (`DemoLayout`, `ProcessPanel` only — do not rewrite them)
9. `web/src/styles.css` (tokens at top; append at end)

Do not read prompts 02, 03, or 04. Do not edit their files.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

Replace “a hero and five paragraphs” with: **six incoming events**, click one, **a graph plays**. The graph is a real SVG+HTML flowchart: event → Bot → manipulations → Handle.

Ship `web/src/components/FlowPlay.tsx` exactly to the contract in `00-SHARED-LAWS.md`. Then rebuild the Overview hero to use it.

---

## Why the current Home fails

`Overview.tsx` today:

- Serif headline + long lede about “coordinated team.”
- Three text buttons.
- `.hero-flow`: four room boxes of agent **name spans**. No edges. No events. No playback.
- `HowItWorks`: five numbered tiles (Inputs / Finance agents / Shared context / Finance actions / Review).
- More cards: team essay, first five invoice-story `<li>`s, CoverageGrid (six domain cards), simulation cards, videos, then a live CFO-cycle IO strip.

A sponsor’s eye never sees work move. Your job is to make the **first screen** a machine they can drive.

Keep below the fold: the live CFO-cycle `DemoLayout` / metrics / `POST /api/workflows/cfo-cycle` run. That is Kernel-live proof. Do not delete it. Do not put more essays above it.

---

## Files you may create

- `web/src/components/FlowPlay.tsx`
- `web/src/components/FlowPlay.test.tsx`
- `web/src/data/eventStories.ts` — the six Home events as `FlowNode` / `FlowEdge` / `FlowStep` arrays
- `web/src/components/EventBoard.tsx` — the six chips + FlowPlay wiring (may live inside Overview instead if small; prefer a component)

## Files you may edit

- `web/src/pages/Overview.tsx`
- `web/src/styles.css` — **append only** after a final marker `/* === 01 flow-play + event-board === */`
- `web/src/components/HowItWorks.tsx` — only to make it unused, or delete its import from Overview. If nothing else imports it, delete the file.
- `web/src/App.test.tsx` — only if Home copy assertions break. Update them to the new hero, do not weaken tests.

## Files you must not edit

Anything else under `web/src/pages/` except Overview.
`ArchitectureDiagram.tsx`, `CoverageGrid.tsx`, `Demo.tsx`, `Explain.tsx`, `Shell.tsx`, `copy.ts`, `capabilities.ts`, `handoffs.ts`, `agents.ts`, `workflowStory.ts` (read; Prompt 02 extends stories).
`.cfo/`, `.cfo-v2/`, `.harness/`.

You may **read** `handoffs.ts` and `workflowStory.ts` and copy values into `eventStories.ts`. Do not modify those source files (Prompt 02 owns story expansions; Prompt 04 owns handoff World edges).

---

## FlowPlay — implement like a product, not a diagram sketch

### Rendering

- Wrapper: `position: relative`, full width of `.main`, min-height ~320px, class `flow-play`.
- **Nodes** are `<button type="button">` so keyboard works. Not `<div onClick>`.
- Node kinds:
  - `event` — faint fill, label is the incoming thing
  - `source` / `operator` — surface fill
  - `verifier` — brass border (`var(--brass)`), so ctl-* is visibly different
  - `assurance` — muted
- **Edges** are SVG `<path>` under the nodes (`position: absolute; inset: 0; pointer-events: none`). Cubic bezier from source-right-center to target-left-center.
- `attached: false` edges: `stroke-dasharray: 5 5`, `stroke: var(--faint)`, `opacity: 0.7`. Accessible name includes “not attached”.
- Active step: source node `done` or `active`, target `active`, connecting edge `stroke: var(--brass)` and a dashoffset animation (you may add `@keyframes flow-dash` in your CSS block).
- `blocked` node: `var(--bad)` border. Used for close-lock / $12.40. Home default story may not need it; still implement the status.
- Under the graph: a **step rail** — title, one-line body, manipulation chips, optional handoff sentence, artifact ID pills in `.mono`.
- Toolbar: Play, Pause, Step, Restart. Play advances ~1.1s per step and stops on last. Do not loop forever.

### Layout algorithm

Do not add a layout library. For Home events, **rank nodes left-to-right** in `eventStories.ts` with an optional `column: number` if you add it locally, **or** compute columns from a simple longest-path: events column 0, first Bot 1, etc.

If a graph has more than ~8 nodes, wrap to a second row rather than shrinking text below 12px.

Export `FlowPlay` as a named export. Default export optional.

### Live mode (must work even if Home does not use it yet)

When `liveStages` is a non-empty array, ignore story autoplay. For each stage, resolve `bot` / `slug` (also accept `bot_ap` → `ap` via replacing `_` and stripping `bot-`). If that id exists in `nodes`, mark it active in order. Map `formatStage` is in `copy.ts` — **you may import `formatAgent` / `formatStage` from `copy.ts`**. Do not edit `copy.ts`.

Prompts 03 will pass `inner.stages` from workflow POST results. If the shape is `result.result.stages` or `result.stages`, accept both in a tiny normalizer inside FlowPlay.

### Tests (`FlowPlay.test.tsx`)

- Renders node labels from props.
- Clicking Step calls `onStepChange` with the next id.
- An edge with `attached: false` is present in the DOM (title or aria).
- With `liveStages: [{ bot: "ap" }]`, the ap node gets an active class.

---

## `eventStories.ts` — six chips

Each chip is one `FlowPlay` dataset. Keep steps to 4–6. Manipulations are Kernel verbs, not essays.

### 1. Vendor invoice PDF (default)

Event: vendor emails a bill.
Nodes: event → email → ap → ctl-pay → pay
Manipulations:

- email: classify document; extract fields; refuse to treat a quote as a bill
- ap: three-way match invoice / PO / GR; duplicate check
- ctl-pay: concur or refuse; never ask a person
- pay: draft weekly run; still does not move money

Handoffs from `HANDOFFS` (`email/bill/ap`, `ap/approve/ctl-pay`, `ap/payable/pay`).
Artifact IDs on later steps may include `INV-001` as the clean example (Prompt 02 owns the full CLEAN story; you may cite the ID).

### 2. Customer remittance

Event: payment notice with weak memo.
Nodes: event → email → apply → ctl-cash
Manipulations:

- email: classify remittance, not a vendor bill
- apply: choose among Kernel candidates; do not invent a combination
- ctl-cash: only if ambiguous / HUMAN_REVIEW fail-closed

Cite `PAY-004` / Lumen $5,000 “September billing” as the example that must **not** auto-apply.

### 3. Stripe `payout.paid`

Event: processor payout.
Nodes: event → stripe → cash → apply
Manipulations:

- stripe: unpack charges − refunds − disputes − fees = deposit; not an InvoiceCandidate
- cash: tie explained deposit to bank
- apply: charge-level facts for customer cash

If waterfall breaks, a dashed or extra edge stripe → ctl-cash (this one is attached; Kernel does route it).

### 4. Bank line

Event: bank feed line.
Nodes: event → bank → cash → ctl-cash
Manipulations:

- bank: land the line; a card charge is not a bill
- cash: match bank to ledger only with evidence
- ctl-cash: sign-off

Mention `TXN-2026-09-015` only as “this line can be the unexplained $12.40” in the last step body. Do not mark it matched.

### 5. Daily aging

Event: aging Routine after apply has drained deposits.
Nodes: event → collect → apply (only if dirty cash) and collect → ctl-pay (write-off)
Also a **not-attached** edge collect → world labeled “dun / send_office_outbound”.
Manipulations:

- collect: Kernel `enforce_collection_decision`; do not chase if unapplied cash might be theirs
- world node `status: "not-attached"` if you include it

Do not show an email as sent.

### 6. Month-end

Event: month-end Routine.
Nodes: event → close → ctl-books → story / audit
Manipulations:

- close: accrue / prepaid / assets / BS; do not mark CLOSED
- ctl-books: lock only if `evaluate_close_gates` passed
- Last step **blocked** on unexplained cash $12.40

---

## Overview.tsx rewrite (structure)

Above the fold, in this order:

1. Compact brand line (keep eyebrow `HackMIT · Agentic Systems for the Office of the CFO`). Headline **one sentence**, max ~12 words. Example shape: “An AI finance office that finishes the work.” Not a paragraph.
2. One-line sub: company + period (Maximor Demo Corp · September 2026). You may still fetch `/api/demo/status` for live pills if already there.
3. **EventBoard**: six chips. Selected chip is filled brass/active. Clicking switches the FlowPlay dataset and resets to step 0.
4. **FlowPlay** for the selected event. Autoplay once on first load of the default chip, then stop.
5. Short button row: `Follow three invoices` → `/workflow`, `Office graph` → `/architecture`, `What it can do` → `/coverage`. Do not send people to `/simulations` as the primary CTA.

Then a divider.

Then **keep** the existing live CFO-cycle block (metrics, run cycle, before/after, process panel). If `HowItWorks` and the “The team” two-card essay and the compact CoverageGrid and the five-item invoice `<ol>` fight the hero, **remove them from Home**. Coverage belongs on `/coverage` (Prompt 02). Team directory belongs on `/architecture` (Prompt 04). Invoice list belongs on `/workflow` (Prompt 02).

You may keep a single muted link “Run simulations” to `/simulations`.

Videos on Home: remove the VideoShowcase from Home if it is still placeholders. Do not fake clips. Leave `/videos` route alone (you do not own Videos.tsx).

---

## Visual density bar

If you still have a `lede` longer than two sentences above FlowPlay, you failed. Put extra explanation in the step rail, not in the hero.

---

## CSS

Append only:

```css
/* === 01 flow-play + event-board === */
```

Classes (suggested): `.event-board`, `.event-chip`, `.event-chip.active`, `.flow-play`, `.flow-node`, `.flow-node.verifier`, `.flow-node.active`, `.flow-node.blocked`, `.flow-node.not-attached`, `.flow-edge`, `.flow-toolbar`, `.flow-rail`, `.flow-chip`.

Do not change `--sidebar`, `.nav-link`, `.io-flow`.

---

## Acceptance

1. Load `/`. Within 2 seconds the vendor-invoice graph is visible with **drawn edges**, not a row of names.
2. Click “Customer remittance”. Graph retargets to email → apply → ctl-cash. `PAY-004` appears in the rail.
3. Click Play. Active node and brass edge advance. Pause works.
4. Click “Daily aging”. A World node or edge is visibly dashed / not attached. No “email sent” copy.
5. Click “Month-end”. A blocked state appears. Copy does not say the month closed.
6. Scroll down: CFO-cycle run button still present.
7. `HowItWorks` five-tile block is gone from Home.
8. `npm test` and `npm run build` pass.
9. Keyboard: event chips and graph nodes are focusable buttons.

## Stop conditions

If `FlowPlay` cannot layout without a library, simplify Home graphs (linear ranks) rather than adding npm deps.
If `/api/demo/overview` is down, the event board still plays from `eventStories.ts`.

When you finish, list the files you changed and the six event chip labels as they appear in the UI.
