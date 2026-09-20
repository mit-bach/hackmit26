# Cursor agent launch pack

This file is how you start the repair agents. The rest of `docs/Agentic-update/` is the source corpus. Do not skip the corpus and invent a second office.

Four pipe agents do the work. A fifth Floor agent goes first so the four are not each half-fixing the bus. That is five prompts. The four pipes remain the product.

Repo root: the `hackmit26` checkout. Paths below are relative to that root.

---

## Goal

The Office of the CFO on Harness v2 is deployable: live Pi workers, Client extension attached, Kernel sidecar up, open items moving on Handles, Verifiers concurring, no human in the completion path. Kernel pytest green is not enough. `--fake` echo workers are not enough.

Done for the office (all agents, together):

1. Documented boot is live Pi plus Client `-e` plus sidecar. `--fake` is a demo switch, not the runbook.
2. A real vendor bill (not `INV-S12` marker) can land, match or HOLD, and reach `ctl-pay` with Kernel evidence.
3. Apply drains deposits. Collect chases only after that. A Kernel-allowed SEND_* reaches the simulated mailbox. A customer persona can reply. `sent=False` outbox-only is not done.
4. Cash ticks identifiers apply and pay already wrote. `$12.40` on `TXN-2026-09-015` stays unexplained. Close stays BLOCKED on it.
5. Close treatments and lock run against `$HARNESS_COMPUTER/runs`, not a silent `.cfo/runs` happy path. Story labels UNLOCKED when lock is missing. Audit does not fix books.
6. One Handle store is truth for Verifier unlock. Operator is emergency stop.
7. BOT.md is readable from Computer cwd. Grants match constructors. `send_office_outbound` imports. Collections Agent constructs.

---

## How input is given

Do not paste the corpus into chat. Attach files. Then paste one prompt from this document.

### In Cursor

1. Open a new agent chat per prompt. One agent, one pipe (or Floor).
2. Attach the **Shared pack** with `@` (list below).
3. Attach that agent’s **Pipe pack**.
4. Paste the prompt in the section marked **Copy this**.
5. Do not attach `.cfo-v2/office/instances/**` as gospel. Those snapshots are evidence of a fuller compile, not the live Computer.
6. Do not attach `examples/cfo-floor`. That Roster is not this office.

If `@` attach fails, the prompt tells the agent to `Read` the same paths. Disk always wins over `evidence/live-computer-2026-09-20.md`.

### Shared pack (every agent)

Attach all of these:

- `docs/Agentic-update/README.md`
- `docs/Agentic-update/01-intended-office.md`
- `docs/Agentic-update/02-failure-taxonomy.md`
- `docs/Agentic-update/02b-inadequacy-index.md`
- `docs/Agentic-update/03-novelty-boundary.md`
- `docs/Agentic-update/04-what-is-good.md`
- `docs/Agentic-update/pipes/README.md`
- `docs/Agentic-update/surfaces/README.md`
- `docs/Agentic-update/evidence/live-computer-2026-09-20.md`
- `design-workshop/dominik/cfo-bot-grain.md`
- `design-workshop/dominik/cfo-office-processes.md`
- `.cfo-v2/office/constitution.md`
- `.cfo-v2/office/SUPERSEDES.md`

### What each agent is allowed to conclude from the corpus

The corpus states intended function, breaks, inadequacies, and novelty fence. It does not specify implementation. You invent the specialist behavior inside the fence. You do not freeze a numbered Kernel replay into a new Skill. You do not add a Bot unless Tests A–D fail. You do not put finance types in `.harness/Harness-v2/src`. You do not restore `Runner` as the Bot bus. You do not resolve the planted $12.40.

### Sequencing

| Order | Agent | Why this order |
| --- | --- | --- |
| 1 | Floor | Bind, attach, cwd, Handle store, live boot. The pipes cannot prove office-live without this. |
| 2 | AR and AP in parallel after Floor exists | Mailbox and payables are different objects. AR owns send/World. AP owns bills and pay-run. |
| 3 | Cash after AR and AP have identifiers | Cash must trust apply/pay, not re-guess the counterparty. |
| 4 | Close last | Close is the period pass over the other three. A board pack first is a lie. |

They may read in parallel. They must not merge Floor last. If AR starts before Floor, it still must not document `--fake` as success.

Write a short `NOTES.md` under `office/bots/<slug>/` or `docs/Agentic-update/evidence/` if you leave a hole. Do not silently claim office-live.

---

## Shared law (included in every Copy-this prompt)

Every prompt below already contains this. Do not weaken it.

- Python wins on amounts. Choose among Kernel candidates.
- Skills never grant tools.
- Fail closed. Missing evidence is not a guess.
- One Profile per Wake. No Grant unions.
- A Bot is not a child.
- Accept is not complete. A peer Handle is not approval.
- Verifiers own concurrence. The Operator is not a worker.
- Operational Bots never load ground truth or `get_audit_ground_truth`.
- Grain Tests A–D decide new Bots.
- Name map in `docs/Agentic-update/README.md`. There is no Bot `ar`. `cfo-floor` is not this office.

---

## Touch map (who may edit what)

| Path / concern | Floor | AR | AP | Cash | Close |
| --- | --- | --- | --- | --- | --- |
| `.harness/Harness-v2/src` generic bus only | yes | no, unless Floor left a hole that blocks your pipe; then generic only | same | same | same |
| `RUN.md`, `client.json`, `extensions.json`, intercept default, Handle unlock | yes | no | no | no | no |
| BOT.md cwd / Computer-visible identity | yes | your slugs only | your slugs only | your slugs only | your slugs only |
| `.cfo/inbox/`, World, collect send, apply | no | yes | Email missing-field only, do not fork a second mailbox | no | no |
| `.cfo/ar/` | no | yes | no | identifiers only | AR snapshot read |
| `.cfo/agent.py`, AP workflow, scheduling | no | no | yes | no | AP aging read |
| `.cfo/cash_recon/`, stripe grants | no | charge-level to apply | identified wires to cash | yes | trusted cash read |
| `.cfo/close/`, reporting, audit | no | no | unreceived → close Handle | trusted cash Handle | yes |
| `computer/harness/roster.json` | yes (bind, extra slug only if Tests A–D) | World/collect/email edges | ap/pay/ctl-pay | stripe/cash/ctl-cash | close/story/audit/ctl-books |
| Instance snapshots | read-only evidence | read-only | read-only | read-only | read-only |

Two agents must not rewrite the same Grant row. If AR adds `send_office_outbound` to Collections Agent, AP does not touch that row.

---

# Agent 0 — Floor (bus and bind)

Launch first.

### Attach (plus Shared pack)

- `docs/Agentic-update/surfaces/harness-protocol.md`
- `docs/Agentic-update/surfaces/bot-md.md`
- `docs/Agentic-update/surfaces/verifiers.md`
- `docs/Agentic-update/surfaces/wakes-and-routines.md`
- `docs/Agentic-update/surfaces/other-prompt-layers.md`
- `docs/Agentic-update/surfaces/grants-and-tools.md`
- `.cfo-v2/office/RUN.md`
- `.cfo-v2/office/computer/harness/roster.json`
- `.cfo-v2/office/computer/harness/client.json`
- `.cfo-v2/office/computer/harness/extensions.json`
- `.cfo-v2/office/computer/harness/intercept.json`
- `.cfo-v2/office/computer/cfo/handle-map.json`
- `.cfo-v2/office/computer/cfo/extensions/intercept.ts`
- `design-workshop/dominik/HARNESS-V2-DEPLOY-PLAN.md`

### Copy this

```
You are the Floor agent for the Office of the CFO Client on Harness v2.

Read every attached file. Then Read live disk. The 2026-09-20 evidence snapshot can be stale. Disk wins.

Your job is deployability of the bus, not a finance pipe. When you are done, a later AR/AP/Cash/Close agent can bind a Bot, call Kernel through the Client extension, complete a Handle, and have a Verifier unlock mean the same object.

Categories you close: T5 (bus not attached), T6 (BOT.md cwd; ask_user as Operator), T9 (two Handle stores; intercept default Operator), parts of T12 (--fake as the documented office).

Outcomes (not a design):

1. Documented boot for this office is live Pi workers with Harness -e and Client -e, HARNESS_CLIENT_SKILLS=1, HARNESS_V2_ROOT set, sidecar up. RUN.md must not teach --fake as the happy path. --fake may remain a labeled protocol demo.
2. Identity files BOT.md and constitution are readable from Computer cwd, or Roster instructions name a path that exists under HARNESS_COMPUTER.
3. Verifier unlock reads the same Handle store Harness completeTurn writes. A completed Harness Handle can unlock a consequential Kernel op when the Verifier concured. A second Client-only CONCUR file is not the source of truth.
4. intercept default is not the human Operator for this Client. Grain owners: ctl-pay money-out and write-off; ctl-cash apply and rec; ctl-books treatments and lock. Collect write-off is ctl-pay, not ctl-cash. Align intercept.json with handle-map.json and grain.
5. ask_user cannot complete pay-run, lock, or write-off. Client still blocks it. Harness protocol text must not teach blocked = Operator as the office law.
6. Extra Client extension is persisted on serve/supervisor, not only pi-bot.sh. Prove argv or config on disk.
7. Do not put invoice types, ctl-* constants as finance enums, or close DAGs in Harness src. Generic primitives only (extra -e, skill path filter, approver kind operator|bot).
8. Do not restore Runner as the Bot bus. Do not register Roster slugs as children.

Novelty: you may choose Computer layout (symlink, copy, intercept file shape) as long as outcomes hold. Do not invent a sixteenth Bot here. World bind is the AR agent’s grain Tests A–D problem.

Proof: write what command starts the office without --fake; show that BOT.md is reachable from Computer cwd; show Handle complete path equals Verifier unlock path; show intercept collect → ctl-pay for write-off. Run or extend existing Harness tests if you touch src. Do not claim office-live for AP/AR/cash/close. That is the other agents.

Use grain names. Use failure categories T5/T6/T9/T12 in your notes.
```

---

# Agent 1 — AR (money in)

Launch after Floor, parallel with AP.

Loudest break: apply/collect split is right; send is dead.

### Attach (plus Shared pack)

- `docs/Agentic-update/pipes/ar.md`
- `docs/Agentic-update/pipes/intake.md`
- `docs/Agentic-update/surfaces/world-inbox.md`
- `docs/Agentic-update/surfaces/grants-and-tools.md`
- `docs/Agentic-update/surfaces/skills.md`
- `docs/Agentic-update/surfaces/memory-and-learning.md`
- `docs/Agentic-update/surfaces/other-prompt-layers.md`
- `.cfo-v2/office/bots/apply/BOT.md`
- `.cfo-v2/office/bots/collect/BOT.md`
- `.cfo-v2/office/bots/email/BOT.md`
- `.cfo-v2/office/bots/world/BOT.md`
- `.cfo-v2/office/computer/skills/ar-collections-policy/SKILL.md`
- `.cfo-v2/office/computer/skills/cash-application/SKILL.md`
- `.cfo/ar/agents.py`
- `.cfo/ar/workflow.py`
- `.cfo/ar/grants.py`
- `.cfo/inbox/tools.py`
- `.cfo/inbox/agents.py`
- `.cfo-v2/office/computer/cfo/grants.json`
- `.cfo-v2/office/computer/cfo/slug-map.json`
- `.cfo-v2/office/computer/cfo/handle-map.json`
- `.cfo-v2/office/computer/harness/roster.json`

Optional read-only: `.cfo-v2/office/instances/protocol-proof/harness/roster.json` and that instance `cfo/catalog.json` (fuller compile, not live SoT).

### Copy this

```
You are the AR pipe agent for the Office of the CFO.

Read every attached file. Then Read live Kernel and live Computer. Disk wins over the snapshot. There is no Bot named ar. Operators are apply (unapplied cash) and collect (open invoices after apply). Do not merge them. Do not hunt cfo-floor slug ar.

Categories you close: T1 (World off live Roster if Tests A–D pass), T2 (four send stories), T3 (send_office_outbound ImportError and Grant missing), T4 (dun never reaches mailbox), T5 (no collect Handle), T6 (skill says preview), T9 (write-off owner ctl-pay), T10 (AR precedent without human CLI as completion).

Outcomes on open items (not a design of the specialist brain):

1. from inbox.tools import send_office_outbound succeeds. Collections Agent constructs. Compiler can catalog the send op. Live grants.json Collections Agent includes it. Finance Inbox Grant includes finance send. World/Counterparty Grant does not.
2. Kernel-allowed SEND_GENTLE_REMINDER / SEND_OVERDUE_REMINDER / SEND_FINAL_NOTICE results in a simulated mailbox message from a finance address. sent=False outbox-only is not this outcome. Then a customer persona can reply in-thread. Email classifies the reply. apply may see a remittance. collect does not call cash-application tools.
3. apply still runs first. If new_deposits(as_of) is non-empty, collect does not chase. Kernel enforce_collection_decision still blocks paid, dispute, cooldown, dirty unapplied cash. You cannot override those.
4. Ambiguous apply stays fail-closed for ctl-cash / review-apply. Write-off / reserve Handles ctl-pay / review-pay. Align handle-map, intercept, BOT.md, and constructor. No fourth Verifier for tone.
5. One send story across constructor, Skill, workflow, live BOT.md, live Roster, handle-map. Delete or rewrite the “outbox / preview” law if the office must send. Skills never grant tools. The Skill may name judgment remainder (this customer vs that one) without a bucket→template table.
6. If World is a standing Bot, run Tests A–D in cfo-bot-grain.md and put it on live roster.json and slug-map.json. If you keep World off the Roster, the mailbox round-trip must still exist as a bound identity the office can Handle. Do not leave Counterparty Grants with no wearer.
7. Dual intake (invoice_ingestion vs inbox.tools) must not mint two Kernel ids for one vendor bill. You may not silently drop Email. You own the remittance door and the dun door.
8. AR learning: a later similar remittance can use precedent as color. It cannot override a live named invoice. Do not use ar-review-correct as the happy path.

Novelty: you invent how collect notices a payer habit, how World plays a late customer, Memory schema beyond “your object only.” Do not freeze aging-bucket → email tone as the specialist. Do not add Bot ar. Do not implement live SMTP. Do not AUTO_APPLY to look autonomous. Do not resolve Northstar $12.40 inside AR.

Proof: import send_office_outbound; compile Grants; show Collections Agent ops include send and World ops do not; show a Kernel-allowed dun in the simulated transport (test or live Handle); show collect blocked while deposits remain; show write-off edge to ctl-pay. If you cannot live-bind World, say so in NOTES. Do not claim office-live from pytest of policy_collection_decision alone.

Use grain names. Cite T-categories in notes.
```

---

# Agent 2 — AP (money out)

Launch after Floor, parallel with AR.

Loudest break: match is strong; learning and live bills are not.

### Attach (plus Shared pack)

- `docs/Agentic-update/pipes/ap.md`
- `docs/Agentic-update/pipes/intake.md`
- `docs/Agentic-update/surfaces/skills.md`
- `docs/Agentic-update/surfaces/memory-and-learning.md`
- `docs/Agentic-update/surfaces/grants-and-tools.md`
- `docs/Agentic-update/surfaces/bot-md.md`
- `docs/Agentic-update/surfaces/verifiers.md`
- `.cfo-v2/office/bots/ap/BOT.md`
- `.cfo-v2/office/bots/pay/BOT.md`
- `.cfo-v2/office/bots/ctl-pay/BOT.md`
- `.cfo-v2/office/bots/email/BOT.md`
- `.cfo-v2/office/computer/skills/three-way-match-analysis/SKILL.md`
- `.cfo-v2/office/computer/skills/ap-exception-investigation/SKILL.md`
- `.cfo-v2/office/computer/skills/payment-prioritization/SKILL.md`
- `.cfo-v2/office/computer/skills/early-payment-discount-evaluation/SKILL.md`
- `.cfo/workflow.py`
- `.cfo/agent.py`
- `.cfo-v2/office/computer/cfo/catalog.overrides.json`
- `.cfo-v2/office/computer/cfo/handle-map.json`

### Copy this

```
You are the AP pipe agent for the Office of the CFO.

Read every attached file. Then Read live Kernel and live Computer. Disk wins. You own open bills (Bot ap), the weekly payment-run draft (Bot pay), and concurrence (Bot ctl-pay). You do not pay. You do not execute ACH. You do not merge ap and pay.

Categories you close: T5 (pay-run never proven on the bus; Runner still host), T10 (prior_cases static), T11 (INV-S12 marker never in Kernel), T12 (stub Handles as product), T7 (skills and BOT.md restating must_hold), T9 (Verifier re-performance vs denylist tension — name it, do not union RECORD_TOOLS onto ctl-pay if grain SoD forbids).

Outcomes on open items:

1. A real Maximor vendor bill lands as a Kernel invoice (canonical id), not workspace/sources/email/MSG-S12.json as a marker. Email or books Handle ap / prepare with a path whose tools.get_invoice returns found.
2. Three-way match: Kernel collect_case_evidence and must_hold still win. APPROVE-shaped packets Handle ctl-pay / review-match. HOLD does not enter the pay pool. Duplicate, missing PO, missing GR, amount past policy stay HOLD.
3. After ctl-pay concurs and Kernel still allows, the id sits in the approved pool. Routine weekly-pay-run (or a live Handle) wakes pay / schedule. Kernel apply_cash_and_policy_net binds amounts. The model does not breach the reserve. Draft Handles ctl-pay / review-pay. After concurrence, identified outflows Handle cash with executed false.
4. Unreceived period work Handles close. That Handle is not approval.
5. Next-period AP behavior can change without a human editing prior_cases.json as the happy path. Precedent cannot override a live blocking must_hold. How you store habit is yours. The capability must exist.
6. Skills and BOT.md: standing identity and must-not stay. Do not ship a second must_hold checklist as the specialist. ctl-pay looks for reasons to refuse. Do not give Payment Audit the same ranking Skill as a second doer if that makes SoD mush — you may split remainder without adding a Bot.
7. Do not implement send-as-bank. Do not add ap-investigator as a Bot. Profile investigate stays on ap.
8. Do not restore Runner as the office bus. Kernel constructors remain Grant source. Domain work the office claims as office-live must complete on Harness Handles.

Novelty: how ap notices this vendor’s messy PDF, how pay defers when cash is tight using Kernel candidates, Memory schema. Do not freeze exception_type → English table. Do not invent amounts.

Proof: one live or tested path where get_invoice finds the id Email landed; ctl-pay sees Kernel evidence; HOLD invoice absent from pay_this_week; a payment-run Handle to ctl-pay exists or a honest NOTES why not. INV-S12 stub must not be the judged story.

Use grain names. Cite T-categories.
```

---

# Agent 3 — Cash (bank vs books)

Launch after AR and AP identifiers can exist.

Loudest break: tie-out and $12.40 law are strong; Stripe Bot and identifier handoff are not.

### Attach (plus Shared pack)

- `docs/Agentic-update/pipes/cash.md`
- `docs/Agentic-update/pipes/intake.md`
- `docs/Agentic-update/surfaces/grants-and-tools.md`
- `docs/Agentic-update/surfaces/memory-and-learning.md`
- `docs/Agentic-update/surfaces/harness-protocol.md`
- `.cfo-v2/office/bots/cash/BOT.md`
- `.cfo-v2/office/bots/ctl-cash/BOT.md`
- `.cfo-v2/office/bots/stripe/BOT.md`
- `.cfo-v2/office/bots/bank/BOT.md`
- `.cfo-v2/office/computer/skills/cash-reconciliation-method-selection/SKILL.md`
- `.cfo-v2/office/computer/skills/reconciliation-evidence-validation/SKILL.md`
- `.cfo-v2/office/computer/skills/reconciliation-exception-investigation/SKILL.md`
- `.cfo-v2/office/computer/skills/bank-reference-interpretation/SKILL.md`
- `.cfo-v2/office/computer/cfo/slug-map.json`
- `.cfo-v2/office/computer/cfo/handle-map.json`

Read Kernel cash_recon and integrations payout math as needed. Do not attach holdout catalogs that operational Bots must never load.

### Copy this

```
You are the Cash pipe agent for the Office of the CFO.

Read every attached file. Then Read live Kernel and live Computer. Disk wins. You own unmatched bank lines (Bot cash) and rec sign-off (Bot ctl-cash). You do not own vendor bills. You do not apply AR. You do not move money. You trust identifiers apply and pay already wrote. You check the bank agrees.

Categories you close: T3 (Stripe empty Grants vs office-live claim), T5 (Kernel cash handles vs Harness Handles; no live cash Handle), T11 (re-guessing the counterparty; forecast starting from unreconciled GL is Close’s lie but you must hand trusted cash), T12 (do not clear $12.40).

Outcomes:

1. A bank line AR already identified ticks without a second customer guess. A bank line AP already identified as a wire ticks the same way. If apply/pay have not identified yet, you do not invent the counterparty to look done. Fail closed. Handle ctl-cash.
2. Integer-cent tie-out stays. You copy candidate_id. You do not invent fees, FX, or residuals.
3. TXN-2026-09-015 $12.40 unexplained stays unexplained. ctl-cash cannot concur MATCHED. Period cannot be RECONCILED. Close stays BLOCKED. Helios-class FEE_NETTED still requires Kernel fee evidence. Do not relabel Northstar as a fee.
4. Stripe unpack remains Kernel math and must not emit InvoiceCandidate. Either Bot stripe can call real Grants for the waterfall object, or you stop claiming stripe office-live and keep CLI simulation as Kernel. Empty Display name plus a standing Bot is costume. Pick an honest state. Do not add a Bot per match type.
5. After ctl-cash concurs and Kernel allows, trusted cash is a path close can read. Harness Handle, not only runs/cash_recon/handles Kernel JSON.
6. Skills: do not replay match_type taxonomy as the specialist. Remainder is messy memos and processor habit as Memory, never as override of missing fee evidence.

Novelty: how cash talks about a messy description, Memory of payout labels. Do not freeze match_type → English. Do not start the 13-week forecast here. Do not resolve holdout ADV residual into operational books.

Proof: identifier trust documented in running code or a test; unexplained $12.40 still blocks; Stripe either granted or explicitly not office-live; a cash Handle path exists on Harness or NOTES says blocked on AR/AP not landing identifiers.

Use grain names. Cite T-categories.
```

---

# Agent 4 — Close, story, audit (period pass)

Launch last.

Loudest break: honest BLOCKED is the product; coordinate/lock/report empty ops and `.cfo/runs` demo path are not.

### Attach (plus Shared pack)

- `docs/Agentic-update/pipes/close-story-audit.md`
- `docs/Agentic-update/surfaces/grants-and-tools.md`
- `docs/Agentic-update/surfaces/wakes-and-routines.md`
- `docs/Agentic-update/surfaces/memory-and-learning.md`
- `docs/Agentic-update/surfaces/skills.md`
- `.cfo-v2/office/bots/close/BOT.md`
- `.cfo-v2/office/bots/ctl-books/BOT.md`
- `.cfo-v2/office/bots/story/BOT.md`
- `.cfo-v2/office/bots/audit/BOT.md`
- `.cfo-v2/office/bots/close/HOST.md`
- `.cfo-v2/office/computer/skills/month-end-close-coordination/SKILL.md`
- `.cfo-v2/office/computer/skills/month-end-close-review/SKILL.md`
- `.cfo-v2/office/computer/skills/prior-period-precedent/SKILL.md`
- `.cfo-v2/office/computer/skills/board-financial-reporting/SKILL.md`
- `.cfo-v2/office/computer/skills/audit-finding-writing/SKILL.md`
- `.cfo-v2/office/RUN.md`
- `.cfo-v2/office/computer/cfo/grants.json`

Read `.cfo/close/`, `.cfo/reporting/`, `.cfo/audit/` as needed. Do not load adversarial holdout into operational Grants.

### Copy this

```
You are the Close / story / audit agent for the Office of the CFO.

Read every attached file. Then Read live Kernel and live Computer. Disk wins. Close is the period pass over AP, AR, and cash. It is not a fifth transaction pipe. Story does not own the books. Audit does not concur on Friday’s wire and does not fix the books.

Categories you close: T3 (empty ops on coordinate / Month-End Close Reviewer / Audit Report), T5 (close-month writes .cfo/runs; Routines not office-live), T8 (hollow Profiles), T11 (forecast before trusted cash), T12 (do not plant stealth theft as operational wow; do not unlock $12.40).

Outcomes:

1. One lock door: close.month_end. Test packet close.orchestrator.run_cfo_close does not lock. close does not mark CLOSED. ctl-books / lock concurs. Kernel evaluate_close_gates is the only door that can mark CLOSED.
2. Live Bots write $HARNESS_COMPUTER/runs (and workspace/close), not a happy path that chdirs into .cfo/runs. RUN.md close demo must not contradict that.
3. Treatments are separate Wakes, one Profile each. create_accrual stays on accrue only. No Grant unions. You do not add Bots accrue, prepaid, assets, bs. You do not make Close Manager a Bot.
4. Empty Grant Profiles: either they gain the Catalog ops the constructor is supposed to have, or they stop being claimed as office-live callers. Coordinate with tools=[] may stay Kernel ready_tasks plus self-Wake — then do not pretend the model coordinates by calling ops. Audit report with tools=[] may stay Kernel ReportStats — then do not pretend it searches the ledger.
5. September 2026 judged close stays BLOCKED on unexplained cash $12.40. You do not relabel it as timing. You do not edit the bank line in Memory.
6. Story packets cite Kernel evidence ids. If lock_status is not CLOSED, every number is labeled UNLOCKED. Forecast does not treat unreconciled GL cash as trusted cash. Do not overwrite immutable forecast snapshots.
7. Audit cites Kernel finding IDs. Operational phase cannot load get_audit_ground_truth. source_records_mutated stays false. Audit is not ctl-pay.
8. Accrual method reuse (Harbor class) only when current evidence supports it. prior-period-precedent is remainder, not a second close DAG. Do not duplicate ready_tasks in BOT.md as a checklist novel.

Novelty: flux sentence choice among Kernel contributors, how close remembers this vendor’s month-end habit, finding language from stats. Do not merge story into close. Do not add ctl-story. Do not freeze the close DAG in a Skill.

Proof: Computer runs path used when HARNESS_COMPUTER is set; gates still BLOCKED on $12.40; no operational ground truth on audit Grants; story UNLOCKED behavior exists if you claim drafts before lock; NOTES if Routines still will not auto-fire (Floor owns autoRoutines).

Use grain names. Cite T-categories.
```

---

## After all five have run

Someone (human or a later merge agent) checks the office done list at the top of this file. Gaps stay in NOTES. Do not demo `--fake` MSG-S12 as the product.

If two agents conflict on `roster.json` or `grants.json`, grain Tests A–D and SoD denylist win. World belongs to AR. Extra `-e` and Handle store belong to Floor. `$12.40` belongs to Cash and Close together: both must refuse to clear it.

---

## Prompt hygiene

- One chat per agent. Do not paste all five prompts into one chat.
- Attach Shared pack every time. The agent will not remember another chat.
- If Floor is not finished, say so in the pipe prompt follow-up: “Floor left this hole: …”
- Do not attach this launch file as a requirement to implement the other prompts. This file is for the operator who starts chats.
