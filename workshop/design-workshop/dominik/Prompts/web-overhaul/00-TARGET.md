# Target experience — what this website is, why it fails, what to build

Read this after `00-SHARED-LAWS.md`. Then read only your numbered prompt.

This file exists because the first round of remaining-agent prompts told implementers to keep `DemoLayout` and “add a board above it.” That is the current site with a sticker on it. The operator rejected that. The job is to **replace the page**, route by route, until a sponsor can tell the functions apart with the titles blurred.

---

## What the application actually is

`web/` is not Maximor’s product finance OS. It is a **Vite console** over Kernel workflows:

- GET reads Maximor Demo Corp books (`CO-MAXIMOR`, September 2026).
- POST `/api/workflows/*` invokes engines in `.cfo/` (match, apply, rec, close, forecast, audit, memory, gauntlet).
- The 15 grain Bots on the Harness roster are the office. Display names in older docs are Profiles, not extra Bots.
- The site must not invent invoices, fees, sends, or a closed month.

That contract is good. The **presentation** is not. The Kernel already plants three stories (Acme clean, Helios fee, Northstar $12.40) and refuses to close the month. The website hides that machine under essays.

---

## Why the site is bad (read the code, not the nav labels)

Open these files. They are almost the same page:

| Route | File | What is actually on screen |
| --- | --- | --- |
| `/inbox` | `pages/Inbox.tsx` | `DemoLayout` + `WhatsHappening` (quote vs bill essay) + sample table + IO columns + `SourceArtifactViewer` |
| `/ap` | `pages/AP.tsx` | Same skeleton. Default `INV-003`. “Three-way match” is three `.card`s inside the **input** column. Invoice register is a `<table>` stuffed into `runBar`. Process is `ProcessPanel` dots. |
| `/ar` | `pages/AR.tsx` | Same skeleton. Aging is five `.split` rows of label + `usd()`. Lumen $5,000 lives in a `StoryCard`. No bar. No refused-apply picture. |
| `/cash` | `pages/Cash.tsx` | Same skeleton. The $12.40 is a `WhatsHappening` paragraph. Three story **buttons** swap which artifact viewer you read. Matches are a table **after** the essay. Bank and ledger never face each other. |
| `/stripe` | `pages/StripePage.tsx` | Same skeleton. Waterfall is a `.waterfall-eq` stack of monospace lines: “Customer charges … − refunds …”. Not bars. |
| `/close` | `pages/Close.tsx` | Same skeleton. Harbor Electric is three essay cards. Close “gate” is a list of `.split` rows with pills. The lock is a status **word**. |
| `/forecast` | `pages/Forecast.tsx` | Same skeleton. Thirteen weeks are a `<table>`. There is no line. |
| `/audit` | `pages/Audit.tsx` | Same skeleton. Findings are `ResultBlock` essays. |
| `/memory` | `pages/Memory.tsx` | Same skeleton. August→September is prose. |
| `/evaluations` | `pages/Evaluations.tsx` | Same skeleton. Gauntlet is a lab essay plus case lists. |

Shared chrome they all import:

- `components/Demo.tsx` → `DemoLayout` (page-head + happening + runBar + `.io-flow` three columns)
- `components/Explain.tsx` → `WhatsHappening` (“What's happening?” / “What Maximor needs to figure out” / “Why it matters”)
- `ProcessPanel` → formatted stage dots
- `SourceArtifactViewer` → friendly/raw document, useful as an inspector, lethal as the page

The three pages that are **not** `DemoLayout` are still prose:

| Route | File | What is on screen |
| --- | --- | --- |
| `/` | `pages/Overview.tsx` | Prompt 01 is replacing the hero with `EventBoard` + `FlowPlay`. Below the fold the old CFO-cycle IO strip, eight `MetricCard`s, briefing, and operations remain. Do not re-own Home. |
| `/workflow` | `pages/Workflow.tsx` | `PageHead` + `<ol className="story-timeline">` of nine cards from `INVOICE_STORY`. One generic AP invoice. **No planted IDs.** No CLEAN / RESOLVED / UNRESOLVED. No graph. |
| `/coverage` | `pages/Coverage.tsx` | `CoverageGrid`: six cards, each “Finance team. …” / “Maximor. …”. Not the CAPABILITIES.md matrix. Hides `not-built` and World `partial`. |
| `/architecture` | `pages/Architecture.tsx` | `ArchitectureDiagram`: four `.arch-room` columns of **buttons**. `HANDOFFS` (25 edges) render as **paragraphs after click**. `PRINCIPAL_FLOWS` are chips with no geometry. No SVG edges. |
| `/agents` | `pages/Agents.tsx` | Directory + `AgentPanel` — a second architecture page without a graph. |
| `/simulations` | `pages/Simulations.tsx` | Card grid of scenarios plus chips that **duplicate** live office routes. |
| `/videos` | `pages/Videos.tsx` | Honest placeholders. Fine as content, weak as a Showcase peer of Home. |
| `/scenarios` | alias | Same as simulations. Not in the nav. Leave the alias. |

`layout/Shell.tsx` nav is a sitemap, not a walk:

- Showcase: Home, Architecture, One invoice, Memory, Simulations, Videos, Coverage, Evidence (eight peers)
- Live office: Inbox through Team activity (nine peers) + Reset books

A sponsor cannot tell what to click first. “One invoice” is the nine-card AP essay.

`copy.ts` maps `"Counterparty Message Agent"` → `"email"`, which hides that World is not on the live roster.

---

## What “overhauled” means

Not: a FlowPlay widget above the existing IO strip.

Not: `WhatsHappening` collapsed into `<details>` while `DemoLayout` remains.

Not: three tabs on the nine-card list.

Not: a CSS polish of `.card`.

**Yes:** each route is a different **instrument**. If you screenshot `/ap`, `/cash`, `/close`, `/workflow`, `/coverage`, and `/architecture` with the h1 cropped, a person can still name the function.

**Yes:** the instrument is the page. Evidence and run logs are secondary.

**Yes:** planted IDs are visible whenever that story is on screen.

**Yes:** the month stays blocked on $12.40. Collect does not pretend an email left the building.

Keep: Maximor console color, type, `usd()`, Kernel POST paths, `RunBar` behavior, `SourceArtifactViewer` as inspector, Shell brand, all existing pathnames.

---

## Sponsor walk after every prompt has landed

Five minutes. Month still blocked.

1. **Home** (`/`) — Prompt 01. Click an incoming event. Graph plays event → Bot → manipulations → Handle.
2. **Show path** (`/workflow`) — Prompt 02. Three case files: Clean, Resolved, Unresolved. IDs stay on a ticker. Unresolved ends on `TXN-2026-09-015` / $12.40 / close blocked.
3. **Capability wall** (`/coverage`) — Prompt 03. Every CAPABILITIES.md id with Kernel-live / Office-live / partial / not-built. Judge can audit the wall.
4. **One live desk** — Prompt 04, 05, or 06. Prefer Cash (`/cash`): bank vs ledger, Northstar pair selected, broken $12.40 gap. Or Payables (`/ap`): three documents, join lines.
5. **Office graph** (`/architecture`) — Prompt 07. Fifteen Bots, Handle edges visible without a click, World dashed not-attached.

Sidebar Pitch (Prompt 07) is that walk: Home → Office graph → Three stories → Capabilities → Evidence.

Live office remaining routes (Inbox, Audit, Memory, Agents, Simulations, Videos) are Prompt **08**. If 08 does not land, those routes still look like the old console when a sponsor wanders. That is why 08 exists. The site is not overhauled while `/inbox` still says “What arrived.”

---

## Parallel map (file exclusivity)

| Prompt | Replaces these routes | Owns these files | Imports |
| --- | --- | --- | --- |
| 01 (in flight) | `/` hero | `FlowPlay.tsx`, `EventBoard.tsx`, `eventStories.ts`, `Overview.tsx` | — |
| 02 | `/workflow` | `Workflow.tsx`, `workflowStory.ts`, `data/showPath.ts` | FlowPlay |
| 03 | `/coverage` | `Coverage.tsx`, `CoverageGrid.tsx`, `capabilities.ts`, `data/capabilityMatrix.ts` | — |
| 04 | `/ap` `/ar` | `AP.tsx`, `AR.tsx`, `components/boards/MatchBoard.tsx`, `AgingApplyBoard.tsx` | FlowPlay, Demo helpers |
| 05 | `/cash` `/stripe` | `Cash.tsx`, `StripePage.tsx`, `PairingLanes.tsx`, `StripeWaterfall.tsx` | FlowPlay, Demo helpers |
| 06 | `/close` `/forecast` | `Close.tsx`, `Forecast.tsx`, `CloseGate.tsx`, `ForecastLine.tsx` | FlowPlay, Demo helpers |
| 07 | `/architecture` + nav | `Architecture.tsx`, `ArchitectureDiagram.tsx`, `Shell.tsx`, `officeGraph.ts`, `copy.ts` aliases only | FlowPlay |
| 08 | `/inbox` `/audit` `/memory` `/agents` `/simulations` `/evaluations` `/videos` | those page files + `App.test.tsx` assertions | FlowPlay where a pipe graph helps |

Nobody else edits those page files. Nobody edits `.cfo/` or the live roster.

---

## Failure pictures (if you ship these, you failed)

- `/workflow` still has `<ol className="story-timeline">` as the thing you see first.
- `/coverage` still has “Finance team.” / “Maximor.” paragraphs as the body.
- `/ap` still uses `<DemoLayout` .
- `/cash` still explains $12.40 only in a `WhatsHappening` card.
- `/stripe` still uses `.waterfall-eq` text instead of bars.
- `/forecast` still has only a table.
- `/architecture` still has `.arch-rooms` buttons and no SVG edges until click.
- `/inbox` still matches the App.test strings “What arrived” / “What changed” because you kept DemoLayout to protect the test. Change the test.

---

## Voice on the new pages

Short. Active. IDs in `.mono`. Status via existing `.pill`. No “coordinated team of agents” lede. No apology about “an older, larger agent list” above the fold. Harbor Electric, Lumen Labs, Acme, Helios, Northstar are names of **cases**, not essay titles.

HUMAN_REVIEW → “unresolved — more evidence required” (existing `formatStatus`).
Skills are knowledge, not Grants.
World is not on the live roster.
