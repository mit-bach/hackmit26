# Website overhaul — four agent prompts

Operator: Billy. These are spawn-ready briefs for **separate** Cursor agents. Do not paste all four into one agent.

The current site is a Maximor console of prose: eighteen routes, zero SVG flowcharts, six coverage cards, nine-card “one invoice.” The target is a five-minute sponsor walk where an incoming event lights a Bot, the Bot’s Kernel manipulations, and the next Handle.

## Spawn order

1. Finish **01** first. It ships `web/src/components/FlowPlay.tsx`. 02–04 import it and will **stop** if the file is missing.
2. Then spawn **02**, **03**, and **04** in parallel. Their file lists do not overlap except `styles.css`, and each appends a **named block at the end** of that file.

Each agent must read `00-SHARED-LAWS.md`, then only its numbered file.

## What to paste

Copy the entire numbered markdown file into a new agent. Tell it: working directory is the repo root `hackmit26`. Then either paste `00-SHARED-LAWS.md` above it, or tell it to read that path first (the numbered prompt already says to).

Prefer: “Read these two files and implement. Do not implement the other numbered prompts.”

| Order | File | Specialization |
| --- | --- | --- |
| laws | [00-SHARED-LAWS.md](00-SHARED-LAWS.md) | Honesty, FlowPlay contract, CSS markers, IDs |
| 1st | [01-FLOWPLAY-AND-HOME.md](01-FLOWPLAY-AND-HOME.md) | Graph engine + Home event board (six incoming events) |
| 2nd | [02-THREE-STORIES-AND-COVERAGE.md](02-THREE-STORIES-AND-COVERAGE.md) | CLEAN / RESOLVED / UNRESOLVED + capability matrix |
| 2nd | [03-LIVE-OFFICE-BOARDS.md](03-LIVE-OFFICE-BOARDS.md) | AP match, AR aging/apply, cash lanes, Stripe waterfall, close gate, forecast line |
| 2nd | [04-ARCHITECTURE-NAV-HONESTY.md](04-ARCHITECTURE-NAV-HONESTY.md) | Office graph with edges, pitch nav, World not-attached, Counterparty alias fix |

## File ownership (do not overlap)

| Path | 01 | 02 | 03 | 04 |
| --- | --- | --- | --- | --- |
| `components/FlowPlay.tsx` | **create** | import | import | import |
| `pages/Overview.tsx` | **edit** | | | |
| `data/eventStories.ts` | **create** | | | |
| `pages/Workflow.tsx` | | **edit** | | |
| `pages/Coverage.tsx` + `CoverageGrid.tsx` + `capabilities.ts` | | **edit** | | |
| `data/showPath.ts` + `capabilityMatrix.ts` | | **create** | | |
| `copy.ts` `CAPABILITY_COPY` | | **extend** | | |
| `pages/AP.tsx` `AR.tsx` `Cash.tsx` `StripePage.tsx` `Close.tsx` `Forecast.tsx` | | | **edit** | |
| `components/boards/*` | | | **create** | |
| `pages/Architecture.tsx` + `ArchitectureDiagram.tsx` | | | | **edit** |
| `layout/Shell.tsx` | | | | **edit** |
| `copy.ts` `AGENT_ALIASES` / `formatAgent("world")` | | | | **edit** |
| `data/officeGraph.ts` | | | | **create** |
| `styles.css` | append `01` block | append `02` block | append `03` block | append `04` block |
| `.cfo/` `.harness/` roster | none | none | none | none |

If two agents append `styles.css` at the same time, rebase by concatenating the four markers. They must not rewrite `:root`.

## Out of scope for all four

- Fake videos
- Resolving $12.40
- Drawing a sent collection email as live
- New npm graph/chart libraries
- Merging Bot `world` onto the live Harness roster
- Kernel workflow math
- Inbox / Audit / Memory / Simulations page redesign (routes stay; 04 only keeps them in nav)

## After all four land — sponsor path

Home (click event) → Three stories (CLEAN, RESOLVED, $12.40) → Capabilities wall → one live board (cash or AP) → Architecture graph. Month still blocked.
