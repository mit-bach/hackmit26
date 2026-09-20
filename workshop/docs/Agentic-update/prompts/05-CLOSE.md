# Prompt 05 — Close, story, audit (period pass)

You are one implementing agent. You own the **period pass** over AP, AR, and cash: completeness (`close`), treatments and lock (`ctl-books`), flux/forecast/board (`story`), after-the-fact findings (`audit`). Close is not a fifth transaction pipe. Story does not own the books. Audit does not concur on Friday’s wire and does not fix the books.

If you start here, a board pack is a printout of a lie. If you unlock September by editing the bank line in Memory, you destroyed the product.

Read first, in this order:

1. `docs/Agentic-update/prompts/00-SHARED-LAWS.md`
2. This file
3. `docs/Agentic-update/01-intended-office.md`
4. `docs/Agentic-update/02-failure-taxonomy.md`
5. `docs/Agentic-update/02b-inadequacy-index.md`
6. `docs/Agentic-update/03-novelty-boundary.md`
7. `docs/Agentic-update/04-what-is-good.md`
8. `docs/Agentic-update/pipes/README.md`
9. `docs/Agentic-update/pipes/close-story-audit.md`
10. `docs/Agentic-update/surfaces/grants-and-tools.md`
11. `docs/Agentic-update/surfaces/wakes-and-routines.md`
12. `docs/Agentic-update/surfaces/memory-and-learning.md`
13. `docs/Agentic-update/surfaces/skills.md`
14. `docs/Agentic-update/evidence/live-computer-2026-09-20.md`
15. `workshop/design-workshop/dominik/cfo-bot-grain.md`
16. `workshop/design-workshop/dominik/cfo-office-processes.md`
17. `.cfo-v2/office/constitution.md`
18. `.cfo-v2/office/SUPERSEDES.md`
19. `.cfo-v2/office/bots/close/BOT.md`
20. `.cfo-v2/office/bots/ctl-books/BOT.md`
21. `.cfo-v2/office/bots/story/BOT.md`
22. `.cfo-v2/office/bots/audit/BOT.md`
23. `.cfo-v2/office/bots/close/HOST.md`
24. `.cfo-v2/office/computer/skills/month-end-close-coordination/SKILL.md`
25. `.cfo-v2/office/computer/skills/month-end-close-review/SKILL.md`
26. `.cfo-v2/office/computer/skills/prior-period-precedent/SKILL.md`
27. `.cfo-v2/office/computer/skills/board-financial-reporting/SKILL.md`
28. `.cfo-v2/office/computer/skills/audit-finding-writing/SKILL.md`
29. `.cfo-v2/office/RUN.md` (close demo path — Floor owns live boot; you own close writing Computer `runs`)
30. `.cfo-v2/office/computer/cfo/grants.json`
31. `.cfo-v2/office/computer/harness/roster.json`
32. `.cfo-v2/office/final-demo/CAPABILITIES.md`

Read `.cfo/close/`, `.cfo/reporting/`, `.cfo/audit/` as needed. Do not load adversarial holdout into operational Grants. Do not load `get_audit_ground_truth` on operational Grants.

Then Read live Kernel and live Computer. Disk wins.

Do not read prompts 01–04 except shared laws. If trusted cash does not exist, stay BLOCKED. Do not invent rec. If Floor left autoRoutines false, NOTES. Do not rewrite intercept default.

Repo root: `/Users/dominikbach/olympus/hackmit/hackmit26`

---

## Mission

The month ended. Documents are still arriving. The question: is this month complete enough to lock.

### Close

- Anything that happened this month without a document yet gets an accrual, or SKIP / INSUFFICIENT if evidence is not there.
- Anything paid this month that belongs to a longer window gets deferred (prepaid).
- Capital vs expense, then straight-line depreciation.
- AR total, AP total, cash total must equal their source lists (BS rec).
- Then look at what moved versus last month and write why (that sentence is story, not close math).
- Then lock so next month cannot sneak in.

One lock door: `close.month_end`. Test packet `close.orchestrator.run_cfo_close` does not lock. `close` does not mark CLOSED. `ctl-books` / `lock` concurs. Kernel `evaluate_close_gates` is the only door that can later mark CLOSED.

Planted `$12.40`, unmatched AR, missing prepaid evidence stay BLOCKED until a Source or Operator Bot mutates source via a legal Kernel op and the host reruns. If no legal op exists, the period stays BLOCKED. September 2026 judged close stays BLOCKED on unexplained cash. That is success.

### Story

Flux, 13-week forecast, forecast miss, board pack. Does not move money. Does not own the books. Every material claim cites a Kernel evidence id. Unlocked drafts label every number `UNLOCKED`. No human signs the pack. `audit` samples it.

Forecast starting balance is trusted cash from 04. Unreconciled GL cash is not trusted cash.

### Audit

Sample, re-perform, write findings. Does not concur on pay-run. Does not fix the books. Operational Grants omit `get_audit_ground_truth`. Cite Kernel finding IDs only. `source_records_mutated` stays false. Path lease before writes.

---

## Why this is a separate agent

Honest BLOCKED is already the product climax. Mixing this with AR send or AP match will either print a fluent board pack on unlocked numbers or plant stealth theft as a wow finding.

You specialize in: Computer `runs` path, empty Profiles made honest, one lock door, UNLOCKED labels, audit isolation, Harbor-class method reuse only when current evidence supports it.

---

## Categories you close

- **T3** — empty ops on coordinate / Month-End Close Reviewer / Audit Report.
- **T5** — `close-month` writes `.cfo/runs`. Routines not office-live.
- **T8** — hollow Profiles. Coordinate `tools=[]`.
- **T11** — forecast before trusted cash.
- **T12** — do not plant stealth theft as operational wow. Do not unlock $12.40.
- **T13** — Close production `deterministic_coordinate()` leftover. Runner in the neighborhood.

---

## Objects you own

| Object | Owner | Dies when |
| --- | --- | --- |
| Period pack | `close` | Lock or honest BLOCKED |
| Accrual | `close` / `accrue`; `ctl-books` review | Invoice arrives, reverses |
| Prepaid schedule | `close` / `prepaid` | Amortized |
| Asset + dep | `close` / `assets` | Schedule posted |
| BS rec packet | `close` / `bs` | Classified; not force-matched |
| Lock | `ctl-books` / `lock` + Kernel gates | CLOSED or refused |
| Flux / forecast / board packets | `story` | Written; audit may sample |
| Findings | `audit` | Written under `workspace/audit/` and `runs/audit/` |

Treatments are separate Wakes, one Profile each. `create_accrual` stays on `accrue` only. No Grant unions. You do not add Bots `accrue`, `prepaid`, `assets`, `bs`. You do not make Close Manager a Bot.

---

## Why the current close fails

### Coordinate has nothing to call (T8, T5)

Profile `coordinate` Grants `ops: []`. Production uses `deterministic_coordinate()`. Demo gap: Close Manager live agent `PARTIALLY_IMPLEMENTED`. Office-live “close Bot coordinates” is Kernel checklist walking, not a specialist.

Grain: orchestration is not an identity. Close Manager is not a Bot. Coordination is Routine + `ready_tasks` + self-Wake. **That can stay.** Then do not pretend the model coordinates by calling ops. Empty Grant + novelist Skill is how close becomes a novelist. Grain already warned: merge `story` into `close` and close becomes a novelist. Keep them split.

Either empty Profiles gain the Catalog ops the constructor is supposed to have, or they stop being claimed as office-live callers. Be honest in BOT.md.

### Month-End Close Reviewer and Audit Report empty ops (T3)

Live Grants: `ops: []` for Month-End Close Reviewer and Audit Report Agent. Skills are assigned. Nothing to call. `ctl-books` / `lock` and `audit` / `report` are costume on the Catalog axis even if BOT.md is long.

Lock Grant empty is especially bad: concurrence with nothing to read except a packet you cannot check against `evaluate_close_gates` is a rubber stamp. Prefer: lock Profile can **read** gates / packet. It cannot mark CLOSED except through Kernel. It cannot hold accrue write Grants.

Audit report with `tools=[]` may stay Kernel `ReportStats` on the packet. Then do not pretend it searches the ledger. Interpretation Profile can call audit read ops. Grain kept report as a Profile because output type differs. Empty Grants make it a second prompt on the same slug. Allowed. Easy to treat as a fake Bot. Pick honesty.

### Close demo writes `.cfo/runs`, not the Computer (T5, T2)

`python3 main.py close-month` chdirs into `.cfo/`. RUN.md says do not point live Bots at `.cfo/runs`. The documented close demo does exactly that. September stays BLOCKED. Honest Kernel. Not Routine `month-end`. Not a Verifier Handle.

Live Bots write `$HARNESS_COMPUTER/runs` (and `workspace/close`), not a happy path that chdirs into `.cfo/runs`. RUN.md close demo must not contradict that. Floor owns the live Pi boot section. You own the close output path. If you must edit RUN.md, change **only** the close-month cwd contradiction. Do not revert Floor’s `--fake` demotion.

### HOST.md vs host module was a miss

Close host had to be restored so treatment Handles could be written. Runner still in the neighborhood. Dual bus. Do not restore Runner as the office. Treatment Handles must be Harness Handles when claimed office-live.

### Story forecast vs trusted cash (T11)

Process law: trusted cash is the forecast starting balance. Story may build forecast from AP, AR, payroll Kernel ops without a rec sign-off. Unlocked numbers are supposed to be labeled. Nothing proves the label appears. A confident forecast before rec is a lie.

If lock_status is not CLOSED, every number is labeled `UNLOCKED`. Forecast does not treat unreconciled GL cash as trusted cash. Do not overwrite immutable forecast snapshots.

04 must hand trusted cash. If it has not, stay UNLOCKED / BLOCKED. Do not invent rec.

### Reporting reviewers dropped (intentional, still a hole)

Grain: story does not move money, so a twin with the same tools is a second prompt; audit samples the pack. Nothing in-line refuses a fluent board sentence that cites a real id but implies the wrong causal story. Kernel `flag_unsupported_claims` helps. Fluency remains a risk. Do not add `ctl-story` without Tests A–D. They will fail Test B/C if you are honest: story does not move money.

### Adversarial holdout not planted (T12)

Capabilities.md: 109 scenarios, stealth theft during a CFO sabbatical, not in operational books. Loud decoys are planted (dup vendor, round wire, GM move). Audit that retells decoys looks impressive and is not the product. Do not plant stealth theft into operational books just to have a wow finding.

### Routine cadences

`weekly` / `monthly` now parse. `autoRoutines: false` on live `client.json` (Floor). Month-end still will not fire itself. `period-story` and `post-close-assurance` same. NOTES if Routines still will not auto-fire. You may fix Routine **prompt text** on close/story/audit. You do not flip autoRoutines if Floor left it false for safety.

### BOT.md cwd (T6)

Same as other slugs. Floor owns layout. You own wording. Do not duplicate `ready_tasks` in BOT.md as a checklist novel. Kernel already has the close DAG. Remainder is how this entity’s recurring vendors behave at month-end (memory), not a second DAG.

Audit BOT.md enumerates control IDs. Kernel already attaches those IDs. Specialist remainder is interpretation, not the list.

### Accrual skills vs Harbor

Accrual Kernel (history, contract, usage, PO candidates) is real. Skills `accrual-evidence-evaluation` and `accrual-method-selection` restate those candidates (T7). Remainder: Harbor-class “same vendor, new period, evidence still supports last method” vs “evidence changed, do not copy last month.” Skill `prior-period-precedent` is aimed at that. It is assigned to many Display names. If it becomes a generic essay, it stops being specialist. Accrual method reuse only when current evidence supports it. October actual bill can reverse the accrual. That reversal is not fully wired in the default demo path (gap recorded). Do not fake the reversal as office-live if Kernel does not.

Prepaid and FA Kernel schedules are deterministic. Profiles `prepaid` and `assets` have no write Catalog ops. The Bot chooses among treatments; Kernel posts schedules. That is good ownership. A Bot with only get_* ops can still narrate a capitalization Kernel already flagged. The narration is the judgment. Do not make the narration a procedure. Dell-class capital invoice depreciates on the same identity as AP. Do not mint a second asset id.

BS rec `classify_packet` must not force a match. Same shape as cash unexplained. Skill `balance-sheet-reconciliation` restates that. Do not force-match $12.40.

### Eval isolation

Operational phase cannot load `get_audit_ground_truth`. Eval Grants may. Keep the split. Audit is not `ctl-pay`.

---

## What is good (do not delete)

- Accrual, prepaid, FA, BS as Profiles on `close`, not four extra Bots. Same month-end Wake. Different Grants. `create_accrual` stays on `accrue` only.
- Close Manager is not a Bot. Coordination is Routine + `ready_tasks` + self-Wake.
- Two close entrypoints are named. One lock door is named.
- `$12.40` fail-closed close is the demo’s honest climax.
- Story forbids re-summing. Forbids filling a residual with a business story. Forbids overwriting forecast snapshots.
- Audit is not a fourth Verifier. Path lease before writes. `source_records_mutated` stays false.
- Harbor Electric memory thread is a real cross-period object.

---

## Files you may create

- Tests: Computer `runs` path when `HARNESS_COMPUTER` is set; gates BLOCKED on $12.40; operational Grants omit ground truth; story UNLOCKED when lock missing
- Story packet fixtures that label UNLOCKED
- Close/story/audit Memory for vendor month-end habit (Harbor rule: current evidence must still support it)
- `office/bots/close/NOTES.md`, `story/NOTES.md`, `audit/NOTES.md`, or `docs/Agentic-update/evidence/NOTES-close.md`

## Files you may edit

- `.cfo/close/**`, `.cfo/reporting/**`, `.cfo/audit/**`, related tests
- Live Grants via compiler: Close Manager / coordinate, Month-End Close Reviewer / lock, Audit Report, treatment Profiles. Empty ops become honest: ops that match constructor, or stop claiming office-live
- `roster.json` close / story / audit / ctl-books. Routines `month-end`, `period-story`, `post-close-assurance` prompt text. Floor owns autoRoutines
- `handle-map.json` close / ctl-books / story / audit edges
- `.cfo-v2/office/bots/close/BOT.md`, `HOST.md`, `ctl-books/BOT.md`, `story/BOT.md`, `audit/BOT.md`
- Close/story/audit skills listed in Read first, plus accrual/prepaid/FA/BS skills if you touch those Profiles. Do not freeze the DAG
- `.cfo-v2/office/RUN.md` **only** the close-month output path contradiction (Computer `runs` vs `.cfo/runs`). Do not restore `--fake` as happy path

## Files you must not edit

- `.cfo/inbox/`, `.cfo/ar/` (02)
- `.cfo/workflow.py` AP host (03)
- `.cfo/cash_recon/` except you **read** trusted cash (04)
- Intercept default, extra `-e`, Handle store unification (Floor)
- `apply` / `collect` / `ap` / `pay` / `cash` BOT.md
- Holdout catalogs into operational Grants
- `web/`, `examples/cfo-floor`
- Bank line `TXN-2026-09-015` facts in Memory to clear the break

---

## Outcomes

1. One lock door: `close.month_end`. Test packet `close.orchestrator.run_cfo_close` does not lock. `close` does not mark CLOSED. `ctl-books` / `lock` concurs. Kernel `evaluate_close_gates` is the only door that can mark CLOSED.
2. Live Bots write `$HARNESS_COMPUTER/runs` (and `workspace/close`), not a happy path that chdirs into `.cfo/runs`. RUN.md close demo must not contradict that.
3. Treatments are separate Wakes, one Profile each. `create_accrual` stays on `accrue` only. No Grant unions. No Bots `accrue`, `prepaid`, `assets`, `bs`. Close Manager is not a Bot.
4. Empty Grant Profiles: either they gain the Catalog ops the constructor is supposed to have, or they stop being claimed as office-live callers. Coordinate with `tools=[]` may stay Kernel `ready_tasks` plus self-Wake — then do not pretend the model coordinates by calling ops. Audit report with `tools=[]` may stay Kernel `ReportStats` — then do not pretend it searches the ledger.
5. September 2026 judged close stays BLOCKED on unexplained cash $12.40. You do not relabel it as timing. You do not edit the bank line in Memory. BS recs tie or name the break. They do not force-match $12.40.
6. Story packets cite Kernel evidence ids. If lock_status is not CLOSED, every number is labeled UNLOCKED. Forecast does not treat unreconciled GL cash as trusted cash. Do not overwrite immutable forecast snapshots.
7. Audit cites Kernel finding IDs. Operational phase cannot load `get_audit_ground_truth`. `source_records_mutated` stays false. Audit is not `ctl-pay`. Loud decoys are not the product.
8. Accrual method reuse (Harbor class) only when current evidence supports it. `prior-period-precedent` is remainder, not a second close DAG. Do not duplicate `ready_tasks` in BOT.md as a checklist novel.
9. Month-end walks treatments as separate Wakes, one Profile each.

---

## Novelty fence

You invent flux sentence choice among Kernel contributors, how close remembers this vendor’s month-end habit, finding language from stats.

Do not:

- Add Bots `accrue`, `prepaid`, `assets`, `bs`
- Make Close Manager a sixteenth Bot
- Make `story` a Verifier
- Make `audit` concur on pay-run
- Merge `story` into `close`
- Unlock the period by editing the bank line in Memory
- Plant stealth theft into operational books
- Freeze a close checklist order in BOT.md that duplicates `ready_tasks`
- Fill a residual with a business story
- Re-sum amounts the Kernel already produced

---

## Proof / acceptance

1. When `HARNESS_COMPUTER` is set, close output lands under Computer `runs` (show path). Not a silent chdir into `.cfo/runs` as the office demo.
2. `evaluate_close_gates` still BLOCKED on $12.40. ctl-books cannot talk past a failed gate.
3. No operational ground truth on audit Grants. Grep operational grants for `get_audit_ground_truth`.
4. Story UNLOCKED behavior exists if you claim drafts before lock. Show a packet or a test.
5. Empty Profiles are either granted or explicitly not office-live in BOT.md.
6. NOTES if Routines still will not auto-fire (Floor owns autoRoutines).
7. Do not claim September CLOSED.

When you finish, list files changed, lock_status for September 2026, and where `runs` landed.

---

## Stop conditions

- If 04 has not produced trusted cash, forecast stays UNLOCKED / refused. Do not start thirteen weeks from GL cash.
- If 02 never sent, AR aging used for close is still post-apply aging. You do not dun. You do not invent collections activity.
- If 03 never landed a real bill, do not invent AP totals. Gates stay blocked on missing completeness where Kernel says so.
- If you cannot grant lock without SoD mush, lock reads gates and refuses. Kernel still marks CLOSED, or does not.
- If HOST.md and host module still disagree, prefer Kernel law + Harness Handles. Do not revive Runner as the month-end office.

## Out of scope

AR send. World bind. AP match. Cash identifier inventing. `--fake` as happy path. Website. Commits unless the operator asks.
