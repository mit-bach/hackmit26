# Shared laws — Maximor website overhaul

Every implementing agent reads this file first. Then it reads only its numbered prompt. It does not read the other numbered prompts. It does not invent extra tickets.

Repo: `/Users/dominikbach/olympus/hackmit/hackmit26`
Website: `web/`
Vite: port 5173, proxies `/api` → `http://127.0.0.1:8765` (`python -m demo_web`).
Canonical capability account: `.cfo-v2/office/final-demo/CAPABILITIES.md`
Website contract: `docs/demo_website_architecture.md`
Visual scope (read, do not edit): the canvas `sponsor-website-viz-scope.canvas.tsx` in the Cursor canvases folder, and this directory.

You are implementing a **sponsor walkthrough**, not a marketing landing, not a new finance engine.

---

## Product in one paragraph

Maximor Demo Corp (`CO-MAXIMOR`), September 2026. An agentic Office of the CFO: standing Bots pay vendors, apply customer cash, reconcile the bank, close the month, forecast, and audit. Python owns amounts. A model chooses among Kernel candidates. Verifier Bots (`ctl-pay`, `ctl-cash`, `ctl-books`) replace a human queue. The website is a **read-and-invoke layer** over Kernel workflows. It does not store a second set of invoices. It does not hard-code success.

---

## The feeling that must replace the current site

Current site: eighteen routes of prose. Architecture is buttons. How-it-works is five paragraphs. One-invoice is nine cards. Coverage is six cards. Zero SVG. Zero motion. A sponsor cannot see work move.

Target: click a real incoming **event** → watch a token travel to a **Bot** → see **manipulations** (match, hold, apply, refuse, block) → see the **Handle** to the next Bot. Same invoice ID stays lit across AP, bank, close, forecast, audit. End on Northstar **$12.40** still unexplained.

Keep the Maximor console: `--bg #0c1014`, `--brass #c9a24a`, IBM Plex Sans / Newsreader / IBM Plex Mono, doc-paper evidence. The stimulation is the moving work, not decoration. No new npm packages. No D3, no Framer Motion, no chart library. React 18 + SVG + CSS only.

---

## Honesty (non-negotiable)

1. Do not resolve `TXN-2026-09-015` / the **$12.40**. Close stays BLOCKED. No invented fee.
2. Do not draw collect → World (or any collection email) as a completed send. Live roster omits Bot `world`. Live catalog omits `inbox.tools.send_office_outbound`. If you draw that hop, it is **dashed** and labeled **not attached**.
3. Do not map Counterparty Message Agent to Bot `email` as if World existed. `copy.ts` currently does that (`AGENT_ALIASES["Counterparty Message Agent"] = "email"`). Prompt 04 owns the fix. Other prompts must not spread the lie.
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

## FlowPlay contract (Prompt 01 ships this)

Path: `web/src/components/FlowPlay.tsx`

Prompts 02–04 import it. If the file is missing when you start, **stop** and say so. Do not invent a second graph engine.

```ts
export type FlowMode = "story" | "live";
export type FlowNodeKind = "event" | "source" | "operator" | "verifier" | "assurance";
export type FlowNodeStatus = "idle" | "active" | "done" | "blocked" | "not-attached";

export type FlowNode = {
  id: string;
  label: string;
  kind: FlowNodeKind;
  room?: "intake" | "pay" | "cash" | "books-close";
};

export type FlowEdge = {
  id: string;
  from: string;
  to: string;
  label: string;
  attached?: boolean; // default true. false → dashed, muted, title "not attached"
};

export type FlowStep = {
  id: string;
  title: string;
  nodeId: string;
  body?: string;
  manipulations: string[];
  handoff?: { to: string; why: string };
  artifactIds?: string[];
  status?: FlowNodeStatus;
};

export function FlowPlay(props: {
  nodes: readonly FlowNode[];
  edges: readonly FlowEdge[];
  steps: readonly FlowStep[];
  activeStepId?: string;
  mode?: FlowMode;
  liveStages?: readonly { id?: string; bot?: string; slug?: string; label?: string; status?: string; detail?: string }[];
  onStepChange?: (stepId: string) => void;
  autoplay?: boolean;
}): JSX.Element;
```

Live mode: map `liveStages[i].bot || liveStages[i].slug` onto `nodes[].id`. Advance `activeStepId` as stages arrive. Verifier slugs use `kind: "verifier"` (brass stroke).

---

## CSS ownership (prevent merge fights)

Single file: `web/src/styles.css`. Each prompt **appends** a named block at the **end**. It does not rewrite `:root`, `.app`, `.topbar`, `.sidebar`, `.demo-page`, `.io-flow`, `.card` unless its prompt explicitly allows a one-line additive change.

| Prompt | Append marker |
| --- | --- |
| 01 | `/* === 01 flow-play + event-board === */` |
| 02 | `/* === 02 story-play + capability-matrix === */` |
| 03 | `/* === 03 live-office-boards === */` |
| 04 | `/* === 04 arch-graph + shell-nav === */` |

You may add `@keyframes` only inside your block. First motion in the app is allowed. Keep it to stroke-dashoffset and a 180–240ms fill change. No gradients beyond what `:root` already uses on `.main`.

---

## Spawn order

1. Run **01** to completion (`FlowPlay.tsx` exists, Home event board plays).
2. Then run **02**, **03**, **04** in parallel. They must not edit each other’s owned files.

---

## Verification (every prompt)

- `cd web && npm test` must pass.
- `npm run build` must pass.
- Open the changed routes in the browser (Cursor browser tools if available). Story-mode graphs must play **even if the API on 8765 is down**.
- A single screenshot is not verification. Click the event/story/node. Confirm the active edge and manipulation chips change.
- If you change how state is written, visit every route that reads it.

---

## Do not

- Do not restyle the whole product.
- Do not add routes without Prompt 04.
- Do not expand `WhatsHappening` essays. Collapse or move below the visual.
- Do not use emoji as UI.
- Do not commit unless the operator asks.
