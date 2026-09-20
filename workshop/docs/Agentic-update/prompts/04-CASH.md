# Prompt 04 — Cash (bank vs books)

You are one implementing agent. You own **unmatched bank lines** (`cash`) and rec sign-off (`ctl-cash`). You do not own vendor bills. You do not apply AR. You do not move money. You trust identifiers `apply` and `pay` already wrote. You check the bank agrees.

If you re-guess the counterparty, close inherits the argument. If you clear `$12.40`, you destroyed the product.

Read first, in this order:

1. `docs/Agentic-update/prompts/00-SHARED-LAWS.md`
2. This file
3. `docs/Agentic-update/01-intended-office.md`
4. `docs/Agentic-update/02-failure-taxonomy.md`
5. `docs/Agentic-update/02b-inadequacy-index.md`
6. `docs/Agentic-update/03-novelty-boundary.md`
7. `docs/Agentic-update/04-what-is-good.md`
8. `docs/Agentic-update/pipes/README.md`
9. `docs/Agentic-update/pipes/cash.md`
10. `docs/Agentic-update/pipes/intake.md`
11. `docs/Agentic-update/surfaces/grants-and-tools.md`
12. `docs/Agentic-update/surfaces/memory-and-learning.md`
13. `docs/Agentic-update/surfaces/harness-protocol.md`
14. `docs/Agentic-update/evidence/live-computer-2026-09-20.md`
15. `workshop/design-workshop/dominik/cfo-bot-grain.md`
16. `workshop/design-workshop/dominik/cfo-office-processes.md`
17. `.cfo-v2/office/constitution.md`
18. `.cfo-v2/office/SUPERSEDES.md`
19. `.cfo-v2/office/bots/cash/BOT.md`
20. `.cfo-v2/office/bots/ctl-cash/BOT.md`
21. `.cfo-v2/office/bots/stripe/BOT.md`
22. `.cfo-v2/office/bots/bank/BOT.md`
23. `.cfo-v2/office/computer/skills/cash-reconciliation-method-selection/SKILL.md`
24. `.cfo-v2/office/computer/skills/reconciliation-evidence-validation/SKILL.md`
25. `.cfo-v2/office/computer/skills/reconciliation-exception-investigation/SKILL.md`
26. `.cfo-v2/office/computer/skills/bank-reference-interpretation/SKILL.md`
27. `.cfo-v2/office/computer/cfo/slug-map.json`
28. `.cfo-v2/office/computer/cfo/handle-map.json`
29. `.cfo-v2/office/computer/harness/roster.json`
30. `.cfo-v2/office/final-demo/CAPABILITIES.md`

Read Kernel `cash_recon/` and integrations payout math as needed. Do not attach holdout catalogs that operational Bots must never load. Do not put holdout ADV residual into operational books.

Then Read live Kernel and live Computer. Disk wins.

Do not read prompts 01, 02, 03, 05 except shared laws. If apply/pay have not landed identifiers, fail closed. Do not invent the counterparty. NOTES. If Floor outcomes 1–3 are not true: NOTES-floor-hole. Do not rewrite `RUN.md`.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

Process law: cash is not a report. Cash is the argument between the bank and the books.

The bank says one number. The ledger cash account says another. Both can be “right” and still disagree: outstanding checks, deposits in transit, a $12.40 wire fee, a Stripe payout that is one bank line and forty invoices, a double-posted refund.

1. Each unmatched bank line gets Kernel candidates. `cash` copies a `candidate_id`. It does not invent a fee, FX, or residual story.
2. Exact, grouped ACH, fee-netted with evidence, timing, duplicate, provider payout, unexplained: Python typed these. The Bot chooses among them.
3. The pipe that owns the counterparty identified the line. Cash checks the bank agrees. It does not re-interpret Acme vs the remittance from scratch.
4. Fail-closed and unexplained difference Handle `ctl-cash` / `review-rec`. Autonomy is not force MATCHED.
5. Period cannot be RECONCILED when arithmetic does not tie, or when `UNEXPLAINED_DIFFERENCE` remains. That is correct.
6. After Verifier concurrence and Kernel allow, trusted cash Handles `close`.
7. Stripe/Adyen: unpack charges − fees − refunds − disputes = bank deposit. Then one deposit to bank rec, charge-level to `apply`. Never an AP invoice.

Trusted cash is the only acceptable starting balance for a 13-week forecast. Starting a forecast from “whatever the GL said before rec” is a thirteen-week lie. You hand trusted cash. You do not write the forecast (05).

---

## Why this is a separate agent

Integer-cent tie-out and the $12.40 law are already strong. Mixing this with AR send or AP match will either “helpfully” explain Northstar as a fee or build a Stripe Skill on empty Grants.

You specialize in: identifier trust, Stripe honesty (Grants or not office-live), Harness Handle not only Kernel JSON handles, planted break stays planted.

---

## Categories you close

- **T3** — Stripe empty Grants vs office-live claim.
- **T5** — Kernel cash handles vs Harness Handles. No live cash Handle on 2026-09-20.
- **T8** — `bind_case` is Sidecar session setup, not a Catalog op the Bot can call.
- **T11** — re-guessing the counterparty. Forecast starting from unreconciled GL is 05’s lie; you must hand trusted cash.
- **T12** — do not clear $12.40.

---

## Objects you own

| Object | Owner | Dies when |
| --- | --- | --- |
| Unmatched bank line | `cash` | Matched, explained exception, timing item, or named unexplained |
| Ledger cash line | `books` / Kernel | Ticked in rec |
| Provider payout waterfall | Kernel; `stripe` should land it | Unpacked; deposit to rec |
| Fee evidence | Kernel | Supports FEE_NETTED or does not |
| Trusted cash | `cash` after `ctl-cash` | Close consumes it (05) |
| $12.40 unexplained | planted break | Stays. Source object change through a legal op only |

Show path STORY-UNRESOLVED: Northstar `INV-AR-013` / `PAY-006` books $12,400.00. Bank `TXN-2026-09-015` is $12,412.40. No fee evidence. Close stays BLOCKED.

STORY-RESOLVED cousin: Helios `INV-017`. Bank `TXN-2026-09-011` is $25 over books. `FEE-729103` supports FEE_NETTED. Do not collapse Helios and Northstar.

Holdout catalog explains Northstar as a 0.1% remittance residual. That explanation is not in operational books. Do not put it there for the judged demo.

---

## Why the current cash fails

### Stripe Bot has no tools (T3, T5)

Empty Display name. Empty Grants. Unpack is `python3 main.py simulate-stripe`. Bind refuses Connectors (`missing_display_name`). Office-live Stripe Bot is costume. Charge-level facts may never Handle `apply`. Deposit may never Handle `cash` as a Bot-to-Bot fact.

Stripe unpack remains Kernel math and must not emit `InvoiceCandidate`. `invoice_candidates` stays 0 on that path. Category error avoided. Keep that.

Either Bot `stripe` can call real Grants for the waterfall object, or you stop claiming stripe office-live and keep CLI simulation as Kernel. Empty Display name plus a standing Bot is costume. Pick an honest state. Do not add a Bot per match type. Do not add a Bot per processor.

Wake `payout.paid` is real. Object (waterfall) is real. Constructor Display name is empty. If you create a constructor, compiler is Grant source. Do not hand-edit `grants.json`.

### Cash Kernel handles vs Harness Handles (T2, T5)

Session 07 wrote `runs/cash_recon/handles/*.json` (Kernel-shaped). Those are not Harness Handle files. `bot_await_turn` cannot see them.

After `ctl-cash` concurs and Kernel allows, trusted cash is a path close can read. **Harness Handle**, not only Kernel JSON.

No live cash or ctl-cash Handle files in the 09-20 completed set (six files are AP stub).

### bind_case is not a Catalog op (T8)

BOT.md: `bind_case` is Sidecar session setup. The Bot does not call it. A bound Pi that never got a bound case will call `get_bank_transaction` against nothing useful. Done-when cannot include a Catalog call that does not exist. Fix the identity or the bind. Do not invent a `bind_case` finance op in Harness `src`.

### Identifier handoff not proven (T11)

If apply never posts, cash is tempted to interpret the deposit. Process law says that is how Close inherits the argument. Live office has not shown apply → cash identifier → rec tick on the same bank line as a Harness path.

A bank line AR already identified ticks without a second customer guess. A bank line AP already identified as a wire ticks the same way. If apply/pay have not identified yet, you do not invent the counterparty to look done. Fail closed. Handle `ctl-cash`.

You may read apply/pay identifier fields. You do not rewrite AR application (02) or AP pay-run (03). If those agents have not landed identifiers, NOTES and fail closed.

### Fee journals unposted until Verifier + Kernel (good rule, unproven path)

BOT.md forbids auto-posting fee journals. There is no live proof that a proposed fee entry waits on `ctl-cash` and then posts only if Kernel fee evidence exists. Helios-class `FEE_NETTED` still requires Kernel fee evidence. Do not relabel Northstar as a fee.

### intercept default Operator (T9)

Floor owns intercept default. Cash Bot override is `ctl-cash`, which matches grain for rec. If Floor left default Operator, do not park unnamed cash ops on a human as your “fix.” NOTES-floor-hole.

### Skills restate match types (T6, T7)

Cash recon Kernel is strong. The skills replay `match_type` taxonomy Python already named. Remainder is messy bank descriptions and “this processor’s usual payout label” as Memory. `bank-reference-interpretation` is closest to that remainder. It still reads like a procedure not to invent invoice numbers, which Kernel already forbids.

Do not freeze match_type → English. Kernel typed it. The specialist explains evidence, not the taxonomy.

### ctl-cash SoD

`ctl-cash` wearing the same cash-application read tools as `apply` is honest for review. It must not post. Grants currently look like the same read set. SoD depends on posting staying out of the Reviewer constructor. Keep that. Do not “give the reviewer write so it can fix.” `ctl-cash` cannot convert unexplained to MATCHED. Cannot convert ambiguous apply to AUTO_APPLY.

### Grouped ACH / provider payout

Kernel-live. Office-live is not shown. Volume RecBench-style lines exist as a next claim in Capabilities.md, not as a Bot proof. Do not claim RecBench office-live unless you prove it.

### Bank Bot

Still a Bot (object + poll Wake). Connector is missing from `WEBHOOK_PROVIDERS`. Card-without-invoice stays `invoice_missing`. That is correct object law. The Bot still cannot poll anything on the live bus. A charge is not a bill. Do not make bank mint AP invoices. Do not add a bank webhook product for the judged demo unless Kernel already has the Connector. Honesty over costume.

### Forecast lie risk (T11, mostly 05)

Story’s forecast tools can build an in-memory snapshot from AP/AR/payroll without waiting on rec. Process law: trusted cash first. You must produce a trusted-cash path 05 can read. You do not start the 13-week forecast here.

---

## What is good (do not delete)

- Integer-cent tie-out. Display can stay major units.
- Candidate engine: exact, grouped, fee-netted, timing, duplicate, unexplained.
- BOT.md identification rule in one sentence: trust apply/pay identifiers; do not re-interpret the counterparty from scratch.
- `$12.40` cannot be relabeled as a fee without Kernel fee evidence. Helios is the explained cousin.
- `ctl-cash` cannot convert unexplained to MATCHED.
- Stripe simulation pack: `invoice_candidates` stays 0.
- Skills as a layer: method selection, evidence validation, exception investigation, bank-reference interpretation.

---

## Files you may create

- Stripe constructor / Display name **or** an explicit not-office-live note in BOT.md and CAPABILITIES-adjacent honesty (do not lie either way)
- Tests: identifier trust (do not re-guess when apply/pay already named the counterparty); unexplained $12.40 still blocks RECONCILED; Stripe unpack emits 0 invoice candidates
- Harness Handle path from cash → ctl-cash → close (trusted cash)
- Memory of payout labels (Computer or Harness Memory). Never as override of missing fee evidence
- `office/bots/cash/NOTES.md`, `stripe/NOTES.md`, or `docs/Agentic-update/evidence/NOTES-cash.md`

## Files you may edit

- `.cfo/cash_recon/**`, Stripe/payout Kernel modules you need for Grants, cash tests
- Live Grants via compiler: cash rec Display names, Stripe if you add a constructor
- `slug-map.json` stripe / cash / ctl-cash
- `handle-map.json` cash / ctl-cash / trusted-cash → close. Identifiers from apply/pay as **reads**, not rewrites of AR/AP maps
- `roster.json` stripe / cash / ctl-cash / bank connectors. Do not add World (02). Do not fill collect send (02)
- `.cfo-v2/office/bots/cash/BOT.md`, `ctl-cash/BOT.md`, `stripe/BOT.md`, `bank/BOT.md`
- The four cash skills listed in Read first. Kernel copies if compiler source

## Files you must not edit

- `.cfo/ar/`, `.cfo/inbox/` send (02)
- `.cfo/workflow.py` AP host (03)
- `.cfo/close/` except you emit trusted cash Handle
- `RUN.md`, intercept default (Floor)
- `collect` / `apply` / `ap` / `pay` / `close` / `story` / `audit` BOT.md
- Holdout catalogs → operational Grants
- `web/`, `examples/cfo-floor`, instance snapshots as SoT
- Forecast snapshot files 05 owns

---

## Outcomes

1. A bank line AR already identified ticks without a second customer guess. A bank line AP already identified as a wire ticks the same way. If apply/pay have not identified yet, fail closed. Handle `ctl-cash`.
2. Integer-cent tie-out stays. You copy `candidate_id`. You do not invent fees, FX, or residuals.
3. `TXN-2026-09-015` $12.40 unexplained stays unexplained. `ctl-cash` cannot concur MATCHED. Period cannot be RECONCILED. Close stays BLOCKED. Helios-class FEE_NETTED still requires Kernel fee evidence. Do not relabel Northstar as a fee.
4. Stripe unpack remains Kernel math and must not emit `InvoiceCandidate`. Either Bot `stripe` can call real Grants, or you stop claiming stripe office-live. Pick an honest state.
5. After ctl-cash concurs and Kernel allows, trusted cash is a path close can read. Harness Handle, not only `runs/cash_recon/handles` Kernel JSON.
6. Skills: do not replay match_type taxonomy as the specialist. Remainder is messy memos and processor habit as Memory, never as override of missing fee evidence.
7. Unmatched lines have owners (this Bot) and a next step that is not “invent a story.”

---

## Novelty fence

You invent how cash talks about a messy description, Memory of payout labels.

Do not:

- Make `cash` own vendor bills or AR application
- Make `cash` move money
- Add a Bot per match type
- Resolve $12.40 in operational books
- Start the 13-week forecast from unreconciled GL cash
- Freeze match_type → English
- Resolve holdout ADV residual into operational books
- Give ctl-cash posting tools so it can “fix”

---

## Proof / acceptance

1. Identifier trust documented in running code or a test (do not re-guess when identifier present).
2. Unexplained $12.40 still blocks. Show the gate. Helios still matches only with `FEE-729103` (or current Kernel fee id).
3. Stripe either granted (constructor + compile) or explicitly not office-live in BOT.md / NOTES. Empty Display name with an office-live claim fails this.
4. A cash Handle path exists on Harness, or NOTES says blocked on AR/AP not landing identifiers / Floor hole.
5. `invoice_candidates == 0` on Stripe unpack still holds.
6. Do not claim RecBench or volume grouped-ACH office-live without proof.

When you finish, list files changed, Stripe’s honest state (granted vs not office-live), and the command or test that still blocks $12.40.

---

## Stop conditions

- If 02/03 have no identifiers, fail closed. Do not scrape memos into fake customers to look done.
- If you cannot Grant Stripe without a constructor, keep CLI Kernel-live and strip office-live claims.
- If unifying Kernel JSON handles with Harness Handles requires invoice types in Harness `src`, stop. NOTES. Floor owns generic Handle primitives.
- If a holdout file explains $12.40, do not load it operationally.

## Out of scope

AR send. AP match. Close lock. Board pack. `--fake` runbook. Website. Commits unless the operator asks.
