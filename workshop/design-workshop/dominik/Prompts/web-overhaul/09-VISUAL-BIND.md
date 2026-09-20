# Prompt 09 — Visual bind pass (do not rebuild the site)

You are one implementing agent. The overhaul already landed. You do **not** replace pages again. You fix what a live browser still shows as empty, $0, Missing, or Loading **after Kernel GET has returned**, and you prove it with screenshots taken **after data is on screen**.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

Read first:

1. `design-workshop/dominik/Prompts/web-overhaul/00-SHARED-LAWS.md`
2. `design-workshop/dominik/Prompts/web-overhaul/00-TARGET.md`
3. This file

Do not read prompts 01–08 except to know file owners. Prefer **minimal edits** to the live desk pages that already exist.

Host:

- Vite `cd web && npm run dev` → `http://127.0.0.1:5173`
- API `.cfo/.venv/bin/python demo_web.py --host 127.0.0.1 --port 8765` (or already running)

If 8765 is down, start it. Do not declare a page “empty because the API is down” until `curl http://127.0.0.1:8765/api/invoices` fails.

---

## Why this prompt exists

A review walked the live site on 2026-09-20. Kernel GETs **work** from the same origin (`/api/invoices` → 34 rows, `/api/stripe` payouts have `gross_payments: 13000`, `/api/forecast` has 13 weeks). Several pages still **first-paint as a corpse**:

| Route | First paint (wrong) | After ~1–2s (better) |
| --- | --- | --- |
| `/ap` | INV-001 / INV-003 with `—`, three sheets **Missing** | 34-bill rail, INV-003 documents + qty mismatch line |
| `/stripe` | every bar **$0.00**, no payout ids | `$13,000` charges, `$390` fees, `$12,610` expected vs deposit, three payout chips |
| `/forecast` | “Loading cash forecast…”, y-axis $0–$1, “Run forecast” | should be a 13-point line ending ~$297,890 |

Agents 04/05/06 claimed browser verification. They screenshotted the empty paint. That is not verification.

Cash (`/cash` $12.40 gap), AR (aging + refused apply), Close (blocked lock), Workflow (three cases), Coverage (wall), Architecture (edges + World dashed), Home (event board) **are good enough**. Do not rebuild them unless you break them.

---

## Mission

1. Make `/ap`, `/stripe`, and `/forecast` show Kernel numbers on the **first meaningful paint**, or show a real loading state that does not look like a finished empty instrument (no $0 waterfall, no three Missing sheets as if the bill has no PO).
2. Walk the sponsor path in the browser **after waiting for GET**. Click. Screenshot. If a number is $0 and curl is not $0, you failed.

---

## Files you may edit

- `web/src/pages/AP.tsx`
- `web/src/pages/StripePage.tsx`
- `web/src/pages/Forecast.tsx`
- `web/src/components/boards/MatchBoard.tsx`
- `web/src/components/boards/StripeWaterfall.tsx`
- `web/src/components/boards/ForecastLine.tsx`
- `web/src/styles.css` — append only `/* === 09 visual-bind === */` (do not rewrite earlier `=== 0N` blocks)
- tests next to files you touch

Optional tiny CSS for `/workflow` FlowPlay overflow (CLEAN graph clips off the right). Prefer a one-block append, not a Workflow rewrite. File: you may edit `web/src/pages/Workflow.tsx` **only** if the graph cannot wrap without clipping IDs. Do not delete the docket.

## Files you must not edit

`Overview.tsx`, `Coverage.tsx`, `Cash.tsx`, `AR.tsx`, `Close.tsx`, `Architecture.tsx`, `Shell.tsx`, `FlowPlay.tsx`, `copy.ts`, `.cfo/`.

---

## Required visual protocol (non-negotiable)

For **each** of `/ap`, `/ar`, `/cash`, `/stripe`, `/close`, `/forecast`, `/workflow?story=unresolved`, `/coverage`, `/architecture`, `/`:

1. `curl` the matching `/api/*` route (or `/` overview). Confirm 200 and that a planted id or amount exists.
2. Open the page in Cursor browser tools. **Lock** the tab.
3. Wait until the instrument shows a Kernel number or id (poll DOM or wait 2s and re-snapshot). Do **not** accept the first screenshot if it says Missing / $0.00 / Loading while curl has data.
4. Click the primary control (INV-001 on AP, Unresolved on workflow, a payout chip on Stripe, a week on forecast).
5. Screenshot **after** the click.
6. Unlock when the whole walk is done.

Fail the task if any of these remain on screen **after** GET has returned:

- AP: “Missing” on Invoice/PO/GR for `INV-003` or `INV-001`
- Stripe: `$0.00` on charges while `gross_payments` is 13000
- Forecast: y-axis max $1.00 while `weeks.length === 13`
- Cash: no `$12.40` gap on `TXN-2026-09-015`
- Close: lock not blocked

---

## Suggested technical fixes (do not gold-plate)

- AP: do not render the three Missing sheets until `open(id)` has settled; if GET failed, show the error, not fake empty documents. Rail should list GET invoices (scroll), not only two placeholders.
- Stripe: do not mount `StripeWaterfall` with an empty breakdown as if it were a real $0 payout. Gate on `data`. Payout strip must be visible without scrolling past a blank stage.
- Forecast: `weeksFromUnknown(data?.weeks)` once GET returns; do not leave the line at $0–$1. “Loading” may show, the axis must not look like a finished $0 forecast.

No new npm packages. Same Kernel POST paths.

`cd web && npm test && npm run build`

When you finish, paste: curl amounts vs on-screen amounts for INV-003, Stripe charges, forecast week-13 ending cash, and Northstar $12.40.
