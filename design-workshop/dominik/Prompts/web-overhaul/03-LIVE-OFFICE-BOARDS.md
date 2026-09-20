# Prompt 03 — Live office boards (AP, AR, cash, Stripe, close, forecast)

You are one implementing agent. You own the **function screens** a sponsor clicks after the stories: payables, receivables, bank, Stripe, close, forecast. Each page already runs Kernel workflows. Your job is to put a **specialized visualization above** the IO strip so the run is something you watch, not something you read.

You do not rebuild Home, Workflow tabs, Coverage, Architecture, or the sidebar.

Read first, in this order:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. This file
3. `web/src/components/FlowPlay.tsx` — **must exist**. If missing, stop.
4. `web/src/components/Demo.tsx` (`DemoLayout`, `ProcessPanel`, `SourceArtifactViewer`, `BeforeAfterDiff`)
5. `web/src/hooks.ts`
6. `web/src/pages/AP.tsx`, `AR.tsx`, `Cash.tsx`, `StripePage.tsx`, `Close.tsx`, `Forecast.tsx`
7. `web/src/copy.ts` — `explainCashMatch`, `MATCH_TYPE_COPY`, `AGING_COPY`, `formatStage` (import; do not rewrite the module)
8. `.cfo-v2/office/final-demo/CAPABILITIES.md` show path IDs

Do not read prompts 01, 02, 04 except shared laws + FlowPlay contract.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

Every live office page currently opens with a `WhatsHappening` essay (happening / figure out / why) and then an Input → Process → Output strip. ProcessPanel is a **list of dots**. Forecast is a **table**. Stripe waterfall is **text**. AP does not draw Invoice vs PO vs GR. AR aging is numbers in copy.

You will:

1. Collapse `WhatsHappening` into a one-line summary + `<details>` (“Why this matters”) so the visual leads.
2. Add a **board** unique to that function, then keep DemoLayout IO **below**.
3. Drive `FlowPlay` in `mode="live"` from `useWorkflow()` stages when a run completes (`result.result.stages` or equivalent — inspect a real payload if the API is up; otherwise read `formatStage` ids in `copy.ts`).
4. Keep RunBar and Kernel POST paths unchanged.

---

## Files you may create

Under `web/src/components/boards/`:

- `MatchBoard.tsx` — AP three-way
- `AgingApplyBoard.tsx` — AR aging bar + remittance candidates
- `PairingLanes.tsx` — cash bank vs ledger
- `StripeWaterfall.tsx` — stacked waterfall
- `CloseGate.tsx` — close task DAG + lock gate
- `ForecastLine.tsx` — 13-week polyline
- tests beside them (`MatchBoard.test.tsx`, etc.) as needed

Optional: `CollapsibleHappening.tsx` if you do not want to fork Explain.tsx. Prefer wrapping `WhatsHappening` locally rather than editing `Explain.tsx` (Prompt 04 / others may import it). **Do not edit `Explain.tsx`.** Wrap at the page: put the three paragraphs inside `<details className="happening-details">`.

## Files you may edit

- `web/src/pages/AP.tsx`
- `web/src/pages/AR.tsx`
- `web/src/pages/Cash.tsx`
- `web/src/pages/StripePage.tsx`
- `web/src/pages/Close.tsx`
- `web/src/pages/Forecast.tsx`
- `web/src/styles.css` — append only `/* === 03 live-office-boards === */`

## Files you must not edit

`Overview.tsx`, `Workflow.tsx`, `Coverage.tsx`, `Architecture.tsx`, `Inbox.tsx`, `Audit.tsx`, `Memory.tsx`, `Agents.tsx`, `Simulations.tsx`, `Evaluations.tsx`, `Videos.tsx`, `Shell.tsx`, `FlowPlay.tsx` (import only), `Demo.tsx` (import only), `copy.ts`, `handoffs.ts`, `capabilities.ts`.
`.cfo/`, `.cfo-v2/`.

---

## Shared page skeleton (all six)

```
[PageHead stays, but shorten `task` to one sentence]
[Board — NEW, full width]
[FlowPlay live — compact, nodes for this pipe only, stages from last run]
[RunBar + ErrorBox — existing]
[DemoLayout IO — existing input/process/output]
```

If stacking DemoLayout’s title would double the h1, **stop using DemoLayout’s page-head** and pass empty/short title, **or** keep DemoLayout and put the board in `happening` / `extra`. Cleanest: keep `DemoLayout` but pass `happening={<> board + collapsed details </>}` and put FlowPlay live in `process` **above** ProcessPanel (process column can contain both).

Do not remove SourceArtifactViewer. When a node/invoice/txn is selected, the artifact viewer still shows the document.

---

## AP — MatchBoard (`/ap`)

Kernel: `GET /api/invoices`, `GET /api/invoices/{id}`, `POST /api/workflows/ap/{id}`, `POST /api/workflows/schedule`.

Default featured ID today is `INV-003` (qty exception). Keep the ability to open any invoice. Add a **featured pair**:

- Clean reference: `INV-001` / `PO-101` / `GR-101` (APPROVE path)
- Working exception: keep `INV-003` as the default run target unless the operator already selected another

**MatchBoard visual:** three columns titled Invoice · Purchase order · Goods receipt. Each column shows vendor, amount (`usd()`), qty if present, id in mono. SVG or CSS lines between **matching** fields (amount to amount). Broken fields use `var(--bad)` and no join line (or a dashed bad line). Duplicate peer (`INV-006` style) gets a banner, not a silent skip.

Decision pill: APPROVE / HOLD from Kernel, not from your opinion.

Live FlowPlay nodes: `email` (optional), `ap`, `ctl-pay`, `pay`. Edges from known handoffs (you may hardcode the three AP edges; do not edit `handoffs.ts`).

After run: ProcessPanel still lists stages; FlowPlay live should highlight `ap` then `ctl-pay`.

**Must not:** invent PO/GR that the API did not return.

---

## AR — AgingApplyBoard (`/ar`)

Kernel: `GET /api/ar`, `POST /api/workflows/ar-aging`, `ar-collections`, `ar-cash-apply` with `{ payment_id: "PAY-004" }`.

Two stacked visuals:

1. **Aging bar** — five segments CURRENT, 1-30, 31-60, 61-90, 90+ from `data.buckets`. Click a bucket to list invoice ids in that bucket (from API rows, not invented). Use `formatAgingBucket`.
2. **Remittance candidates** — for featured payment `PAY-004` (Lumen $5,000, memo September billing). Show the payment card and the competing invoice cards. Outcome after run must remain **unmatched / more evidence required**, never a guessed apply.

Collect run: show the chosen `CollectionAction` as a chip (`SEND_*` is a **draft**, not sent). If you draw World, dashed not-attached. Copy: “Outbound mailbox is not attached on the live roster.”

Live FlowPlay nodes: `email`, `apply`, `collect`, `ctl-cash`. No fake send edge as attached.

---

## Cash — PairingLanes (`/cash`)

Kernel: `GET /api/cash`, `POST /api/workflows/bank-reconciliation`.

Two vertical lanes: Bank · Ledger. Link matched pairs with SVG lines. Color by `match_type` via existing `statusTone` / `explainCashMatch`:

- `EXACT_MATCH` / grouped / FEE_NETTED → ok
- `TXN-2026-09-011` + `FEE-729103` → explained (RESOLVED story). Label the fee id.
- `TXN-2026-09-015` → **unexplained**, `var(--bad)`, difference $12.40, **no connecting “solved” line**. Caption: close cannot finish.

Live FlowPlay: `bank`, `cash`, `ctl-cash`, `close` (block).

**Must not:** draw a fee on Northstar. **Must not:** auto-scroll past $12.40 — that pair should be the default selected exception.

---

## Stripe — StripeWaterfall (`/stripe`)

Kernel: `GET /api/stripe`, `POST /api/workflows/stripe-reconciliation`. Simulated only (pill already).

Replace the monospace equation with **horizontal waterfall bars** (divs with width % or SVG rects):

+ charges · − refunds · − disputes · − fees · = expected payout · vs bank deposit

If tied, deposit bar ok. If not, bad and edge to ctl-cash.

Use `usd()`. Do not connect live Stripe keys. Keep mode pill.

Live FlowPlay: `stripe` → `cash` and `stripe` → `apply`.

---

## Close — CloseGate (`/close`)

Kernel: `GET /api/close`, `POST /api/workflows/close`, `POST /api/workflows/accrual` `{ vendor: "Harbor Electric" }`.

Visual: a small DAG of close profiles — accrue, prepaid, assets, bs, coordinate → ctl-books lock.

Harbor Electric accrual is the memory thread. Dell `INV-018` capitalize if present in payload. Cash rec gate: if unreconciled $12.40 / period not clear, lock node `blocked`. Title: “Month is not closed.”

Do not call `deterministic_coordinate` a live Close Manager if CAPABILITIES says partial — label lock as ctl-books.

Live FlowPlay: `close`, `ctl-books`, `story`, `audit`.

---

## Forecast — ForecastLine (`/forecast`)

Kernel: `GET /api/forecast`, `POST /api/workflows/forecast`.

Draw a **polyline** of `ending_cash` across `weeks` (should be 13). X = week label via `formatWeekDate`. Y = USD. Axes labeled: Week, Ending cash (USD). Caption: source `/api/forecast` weeks.

Keep the table below the chart (sponsor may want the numbers). Highlight miss source `INV-AR-014` if present in payload/copy; do not invent a miss if the API does not mention it.

Live FlowPlay: `pay`, `apply`, `story` (cash in/out feeding the line).

No chart npm library. SVG `polyline` + a few `circle` points. Hover optional; click a week to select (you already have `setWeek`).

---

## Live FlowPlay mapping

On each page, build a **small** node list (4–6), not the whole office. Pass `liveStages` from the workflow result. If stages are empty (API down), FlowPlay still shows idle nodes and the board still shows GET data.

Normalize: `result?.result?.stages || result?.stages || inner?.stages || []`.

---

## CSS

Append `/* === 03 live-office-boards === */`

Boards should feel like instruments: tight grid, mono IDs, brass only on the active pair. Do not restyle `.io-flow`. Do not add drop shadows (site already has `--shadow` on some cards; do not expand it).

Suggested: `.match-board`, `.match-col`, `.aging-bar`, `.aging-seg`, `.lanes`, `.lane`, `.waterfall`, `.wf-bar`, `.close-gate`, `.forecast-line`.

---

## Acceptance (browser, each route)

`/ap` — three columns visible; INV-001 can be selected; join lines exist for a clean match; INV-003 still runnable.

`/ar` — aging bar has five segments; PAY-004 run does not claim AUTO_APPLY success; collect does not say email sent.

`/cash` — pairing lanes visible; `TXN-2026-09-015` selected or clearly marked unexplained $12.40.

`/stripe` — bars, not a single monospace formula, for charges/fees/deposit.

`/close` — lock node blocked while cash unexplained; no “Closed” success.

`/forecast` — SVG line with 13 points when weeks.length is 13; table still there.

All six: RunBar still calls the same `/api/workflows/*` paths as today (grep to confirm you did not rename them).

`npm test`, `npm run build`.

If 8765 is down: GET error states already exist; boards must not crash on missing arrays (use `|| []`).

When you finish, list each board component and the Kernel POST path still wired on that page.
