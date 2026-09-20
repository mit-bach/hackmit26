# Shared laws — Maximor website overhaul (remaining agents)

Every remaining implementing agent reads this file first, then `00-TARGET.md`, then only its numbered prompt. It does not read the other numbered prompts. It does not invent extra tickets.

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`
Website: `web/`
Vite: port 5173, proxies `/api` → `http://127.0.0.1:8765` (`python -m demo_web`).
Canonical capability account: `.cfo-v2/office/final-demo/CAPABILITIES.md`

Prompt **01 is already in flight**. `web/src/components/FlowPlay.tsx` exists. Home already has `EventBoard`. Do not edit Prompt 01’s files. Do not fork FlowPlay.

You are implementing a **sponsor walkthrough**, not a marketing landing, not a new finance engine, not a restyle of the Kernel console.

---

## Replace. Do not decorate.

The current site is one layout printed on almost every route: `DemoLayout` → `WhatsHappening` (three essays) → `RunBar` → three columns labeled **What arrived / What the agents did / What changed**. Architecture is the exception, and it is four columns of buttons. Workflow is the other exception, and it is nine essay cards.

If a stranger blurs the titles and your page still looks like that console, **you failed this prompt**.

On every page you own:

1. **Delete** the `DemoLayout` call. Do not wrap it. Do not pass a board in `happening={...}`. Do not keep `io-flow` as the page skeleton.
2. **Do not render** `WhatsHappening` or `StoryCard` on first paint.
3. **Do not** keep a `PageHead` lede longer than 18 words. Prefer a one-line title plus the instrument.
4. The unique **instrument** (graph, match, lanes, waterfall, lock, line, wall, docket) is the first thing in `.main` after a short title. Min-height **380px**.
5. Kernel GET/POST paths stay. `useWorkflow` stays. `SourceArtifactViewer` may live in a **collapsed** `<details>` inspector. `ProcessPanel` may live under the instrument **after a run**, never as a middle column of the page.
6. No new npm packages. No D3, no Framer Motion, no chart library. React 18 + SVG + CSS. Keep tokens in `:root` (`--bg`, `--brass`, IBM Plex / Newsreader). You may invent new layout classes in **your** CSS append block.

---

## Product in one paragraph

Maximor Demo Corp (`CO-MAXIMOR`), September 2026. An agentic Office of the CFO: standing Bots pay vendors, apply customer cash, reconcile the bank, close the month, forecast, and audit. Python owns amounts. A model chooses among Kernel candidates. Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) replace a human queue. The website is a **read-and-invoke layer** over Kernel workflows. It does not store a second set of invoices. It does not hard-code success.

---

## Honesty (non-negotiable)

1. Do not resolve `TXN-2026-09-015` / the **$12.40**. Close stays BLOCKED. No invented fee.
2. Do not draw collect → World (or any collection email) as a completed send. Live roster omits Bot `world`. Live catalog omits `inbox.tools.send_office_outbound`. If you draw that hop, it is **dashed** and labeled **not attached**.
3. Do not map Counterparty Message Agent to Bot `email` as if World existed. `copy.ts` currently does that. Prompt **07** owns the fix. Other prompts must not spread the lie.
4. Do not claim AP self-improvement or vendor bank-change as built. CAPABILITIES.md marks them **Not built**.
5. Do not treat Kernel gauntlet 42/42 or “97%” as the office score. Caption: Kernel.
6. Do not add fake video. `/videos` stays honest placeholders unless a real file already exists.
7. Do not write `.cfo/` workflow math. Do not merge World onto `harness/roster.json`. Do not invent Kernel outcomes.
8. `HUMAN_REVIEW` on screen is “unresolved — more evidence required” / a Verifier Bot. Never “waiting for a person.”
9. Skills never grant tools. Do not imply a SKILL.md is a permission.

---

## Public show-path IDs (always visible when that story is on screen)

| Story | IDs | Outcome |
| --- | --- | --- |
| CLEAN | Acme `INV-001` = `PO-101` = `GR-101`. Paid `PAY-AP-001`. Bank `TXN-2026-09-018A` MATCHED | Happy path |
| RESOLVED | Helios `INV-017`. Bank `TXN-2026-09-011` is $25 over books. `FEE-729103` supports FEE_NETTED | Explained exception |
| UNRESOLVED | Northstar `INV-AR-013` / `PAY-006` books $12,400.00. Bank `TXN-2026-09-015` is $12,412.40. No fee evidence | Close BLOCKED |

---

## Fifteen grain Bots (live roster)

`email`, `stripe`, `bank`, `books`, `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story`, `ctl-pay`, `ctl-cash`, `ctl-books`, `audit`.

Rooms: intake (`email,stripe,bank,books`), pay (`ap,pay,ctl-pay`), cash (`apply,collect,cash,ctl-cash`), books-close (`close,ctl-books,story,audit`).

World is a sixteenth identity that exists as `BOT.md` and instance snapshots and **does not** sit on the live Computer roster. Website may show it only as not-attached.

There is no Bot named `ar`. AR is `apply` + `collect`.

---

## FlowPlay (already shipped — import it)

Path: `web/src/components/FlowPlay.tsx`

If the file is missing when you start, **stop** and say so. Do not invent a second graph engine. Do not edit FlowPlay.

The shipped component may include extra optional fields (`column`, `row`, node `status`, wrapped `liveStages`). Use it as it exists. Required usage:

```ts
import { FlowPlay } from "../components/FlowPlay";
// nodes, edges, steps as in the shipped types
// mode="story" with autoplay for planted plots
// mode="live" with liveStages from useWorkflow() for Kernel runs
```

Live mode: map `liveStages[i].bot || liveStages[i].slug` onto `nodes[].id`. Verifier slugs use `kind: "verifier"` (brass stroke). Not-attached edges: `attached: false`.

Normalize stages: `result?.result?.stages || result?.stages || []`. If the API is down, FlowPlay still shows idle nodes.

---

## Live desk skeleton (prompts 04, 05, 06, 08)

Each live function page uses this **shape**, implemented **inline in the page** (or a file only you own). Do **not** create a shared `LiveDesk.tsx` that other prompts must import — that would serialize the work.

```
[one-line title]
[one-line stake, ≤18 words]
[INSTRUMENT — unique to this function, min-height 380px]
[compact run controls — same POST paths as today]
[FlowPlay live — 4–6 nodes for THIS pipe only]
[<details> Evidence — SourceArtifactViewer, BeforeAfterDiff, ProcessPanel. Default CLOSED]
```

Prefix your classes so parallel CSS appends do not fight:

| Prompt | Prefix |
| --- | --- |
| 04 | `.pay-` |
| 05 | `.cash-` |
| 06 | `.month-` |
| 08 | `.rest-` |

---

## CSS ownership

Single file: `web/src/styles.css`. Each prompt **appends** a named block at the **end**. It does not rewrite `:root`, `.app`, `.topbar`, `.sidebar`, `.demo-page`, `.io-flow`, `.card`, and it does not edit the `/* === 01 flow-play + event-board === */` block.

| Prompt | Append marker |
| --- | --- |
| 01 (done) | `/* === 01 flow-play + event-board === */` |
| 02 | `/* === 02 show-path === */` |
| 03 | `/* === 03 capability-wall === */` |
| 04 | `/* === 04 pay-desk === */` |
| 05 | `/* === 05 cash-desk === */` |
| 06 | `/* === 06 month-desk === */` |
| 07 | `/* === 07 office-graph + shell-nav === */` |
| 08 | `/* === 08 remaining-routes === */` |

You may add `@keyframes` only inside your block. Motion: stroke-dashoffset and 180–240ms fill change. No extra drop shadows. No gradients beyond what `:root` already uses on `.main`.

If two agents append at once, concatenate the markers. Do not rebase by rewriting earlier blocks.

---

## Spawn order

1. Prompt **01** is already running. Wait until `FlowPlay.tsx` exists (it should).
2. Spawn **02 through 08 in parallel**. File lists do not overlap except `styles.css` (append-only) and a few **compat exports** listed in each prompt.

`copy.ts`: only Prompt **07** may edit it (`AGENT_ALIASES` / `formatAgent("world")`). Everyone else **imports** formatters.

`App.tsx`: do not delete routes. Only Prompt **07** may edit `Shell.tsx`. Prompt **08** may edit `App.test.tsx` assertions that name `/inbox`, `/agents`, `/evaluations`.

---

## Test landmines (do not ignore)

`web/src/App.test.tsx` currently asserts `/inbox` still shows “What arrived” / “What changed”. That is the old console. Prompt **08** must rewrite that test to match the new Inbox instrument.

The same file asserts `/agents` contains “The finance team” and `/evaluations` contains “connected finance work” / “Evaluation Lab”. Prompt **08** owns those pages and those assertions.

`web/src/data/architecture.test.ts` imports `INVOICE_STORY` and `CAPABILITIES`. Prompt **02** keeps an `INVOICE_STORY` export (CLEAN spine is enough). Prompt **03** keeps a `CAPABILITIES` export with `agents: string[]` on each row.

`test.each(ROUTES)` requires every route to render “Office of the CFO” (the Shell brand) and to omit the string `Invoice approved`. Do not put that string on a page.

---

## Verification (every prompt)

- `cd web && npm test` must pass.
- `npm run build` must pass.
- Open the changed routes in the browser (Cursor browser tools if available). Story-mode graphs must play **even if the API on 8765 is down**.
- A single screenshot is not verification. Click the instrument. Confirm the visual changes.
- If you change how state is written, visit every route that reads it.

---

## Do not

- Do not edit Prompt 01 files: `FlowPlay.tsx`, `EventBoard.tsx`, `eventStories.ts`, `Overview.tsx` (except Prompt 07 does not touch Overview either).
- Do not add routes without Prompt 07, and Prompt 07 should not add routes unless a redirect is required. Keep the existing pathnames.
- Do not use emoji as UI.
- Do not commit unless the operator asks.
- Do not restyle the topbar brand. Maxi**mor** / Office of the CFO stays.
