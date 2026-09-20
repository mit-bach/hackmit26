# Website overhaul — spawn pack

Operator: Billy. These are spawn-ready briefs for **separate** Cursor agents. Do not paste them into one agent.

Prompt **01 is already in flight**. Do not respawn it. Do not edit `01-FLOWPLAY-AND-HOME.md`.

The first remaining-agent pack asked implementers to keep `DemoLayout` and add a board on top. That was wrong. The current site is one Kernel console printed on almost every route. The remaining prompts **replace those pages**.

## What to paste

New agent. Working directory: repo root `hackmit26`.

> Read `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`, `00-TARGET.md`, and this numbered file. Implement only that prompt. Do not implement the other numbered prompts.

## Spawn order

1. **01** — already running (FlowPlay + Home event board).
2. Spawn **02 through 08 in parallel** as soon as `web/src/components/FlowPlay.tsx` exists.

They do not share page files. `styles.css` is append-only with named markers. `copy.ts` is Prompt **07** only.

| File | Specialization | Replaces |
| --- | --- | --- |
| [00-SHARED-LAWS.md](00-SHARED-LAWS.md) | Honesty, FlowPlay import, bans, CSS markers | — |
| [00-TARGET.md](00-TARGET.md) | Why the site fails; whole-site target | — |
| [01-FLOWPLAY-AND-HOME.md](01-FLOWPLAY-AND-HOME.md) | **In flight.** Engine + Home | `/` hero |
| [02-SHOW-PATH.md](02-SHOW-PATH.md) | Docket + three playable cases | `/workflow` |
| [03-CAPABILITY-WALL.md](03-CAPABILITY-WALL.md) | Capability wall vs CAPABILITIES.md | `/coverage` |
| [04-PAY-DESK.md](04-PAY-DESK.md) | Three-way match + aging/refused apply | `/ap` `/ar` |
| [05-CASH-DESK.md](05-CASH-DESK.md) | Bank vs ledger lanes + Stripe bars | `/cash` `/stripe` |
| [06-MONTH-DESK.md](06-MONTH-DESK.md) | Close lock + 13-week line | `/close` `/forecast` |
| [07-OFFICE-GRAPH-AND-NAV.md](07-OFFICE-GRAPH-AND-NAV.md) | Graph with edges, Pitch nav, World | `/architecture` + sidebar |
| [08-REMAINING-ROUTES.md](08-REMAINING-ROUTES.md) | Inbox, audit, memory, agents, sims, evals, videos | leftover console |

## File ownership

| Path | Owner |
| --- | --- |
| `FlowPlay.tsx` `EventBoard.tsx` `eventStories.ts` `Overview.tsx` | 01 (do not touch) |
| `Workflow.tsx` `workflowStory.ts` `data/showPath.ts` | 02 |
| `Coverage.tsx` `CoverageGrid.tsx` `capabilities.ts` `capabilityMatrix.ts` | 03 |
| `AP.tsx` `AR.tsx` `boards/MatchBoard.tsx` `boards/AgingApplyBoard.tsx` | 04 |
| `Cash.tsx` `StripePage.tsx` `boards/PairingLanes.tsx` `boards/StripeWaterfall.tsx` | 05 |
| `Close.tsx` `Forecast.tsx` `boards/CloseGate.tsx` `boards/ForecastLine.tsx` | 06 |
| `Architecture.tsx` `ArchitectureDiagram.tsx` `Shell.tsx` `officeGraph.ts` `copy.ts` (aliases only) | 07 |
| `Inbox.tsx` `Audit.tsx` `Memory.tsx` `Agents.tsx` `Simulations.tsx` `Evaluations.tsx` `Videos.tsx` `App.test.tsx` | 08 |
| `styles.css` | each **appends** its marker at the end |
| `.cfo/` `.harness/` roster | nobody |

If CSS appends collide, concatenate the `=== 0N` blocks. Do not rewrite `:root` or the `=== 01` block.

## Why seven remaining agents (not three)

The old 02 mixed stories + coverage. The old 03 asked one agent to put boards on six `DemoLayout` pages — that produces six stickers. The old 04 was nav + graph + copy. Leftover routes were declared out of scope, so the site stayed a console.

Now: one agent per instrument family, plus 08 so Inbox/Memory/Evals do not remain the old product.

They **can** run in parallel. If you must cut, cut nothing from 02, 05, and 07 (plot, $12.40 lanes, graph+nav). 08 is what makes the **whole** site change when someone wanders.

## Out of scope for every agent

- Fake videos or a resolved $12.40
- Drawing a sent collection email as live
- New npm graph/chart libraries
- Merging Bot `world` onto the live roster
- Kernel workflow math
- Editing Prompt 01’s files

## After all land — sponsor path

Home (click event) → Three stories (CLEAN, RESOLVED, $12.40) → Capability wall → Cash lanes or AP match → Office graph. Month still blocked.

Pitch nav (07): Home, Office graph, Three stories, Capabilities, Evidence.
