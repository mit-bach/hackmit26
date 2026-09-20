# Close, story, audit — period pass

Process law: close is not another pipe for transactions. Close is the period-end pass over the other three.

The month ended. Documents are still arriving. The question: is this month complete enough to lock.

Standing Bots: `close` (completeness), `ctl-books` (treatments and lock), `story` (flux, forecast, board pack), `audit` (after-the-fact findings).

Do not start here. A board pack is a printout of AP, AR, and cash working.

---

## Intended function

### Close

- Anything that happened this month without a document yet gets an accrual, or SKIP / INSUFFICIENT if evidence is not there.
- Anything paid this month that belongs to a longer window gets deferred (prepaid).
- Capital vs expense, then straight-line depreciation.
- AR total, AP total, cash total must equal their source lists (BS rec).
- Then look at what moved versus last month and write why (that sentence is story, not close math).
- Then lock so next month cannot sneak in.

One lock door: `close.month_end`. `close.orchestrator.run_cfo_close` is a test packet. It does not lock.

`close` does not mark CLOSED. `ctl-books` / `lock` concurs. Kernel `evaluate_close_gates` is the only door that can later mark CLOSED.

Planted `$12.40`, unmatched AR, missing prepaid evidence stay BLOCKED until a Source or Operator Bot mutates source via a legal Kernel op and the host reruns. If no legal op exists, the period stays BLOCKED.

### Story

Flux, 13-week forecast, forecast miss, board pack. Does not move money. Does not own the books. Every material claim cites a Kernel evidence id. Unlocked drafts label every number `UNLOCKED`. No human signs the pack. `audit` samples it.

### Audit

Sample, re-perform, write findings. Does not concur on pay-run. Does not fix the books. Operational Grants omit `get_audit_ground_truth`. Cite Kernel finding IDs only.

---

## Objects

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

---

## What exists that is good

- Accrual, prepaid, FA, BS as Profiles on `close`, not four extra Bots. Same month-end Wake. Different Grants. `create_accrual` stays on `accrue` only.
- Close Manager is not a Bot. `tools=[]`. Coordination is Routine + `ready_tasks` + self-Wake. Grain: orchestration is not an identity.
- Two close entrypoints are named. One lock door is named. That honesty is recent and correct.
- `$12.40` fail-closed close is the demo’s honest climax. Do not delete it.
- Story forbids re-summing. Forbids filling a residual with a business story. Forbids overwriting forecast snapshots.
- Audit is not a fourth Verifier. Path lease before writes. `source_records_mutated` stays false.
- Harbor Electric memory thread is a real cross-period object (accrual method reuse only when current evidence still supports it).

---

## What is broken

### Coordinate has nothing to call (T8, T5)

Profile `coordinate` Grants `ops: []`. Production uses `deterministic_coordinate()`. Demo gap: Close Manager live agent `PARTIALLY_IMPLEMENTED`. Office-live “close Bot coordinates” is Kernel checklist walking, not a specialist.

### Month-End Close Reviewer and Audit Report empty ops (T3)

Live Grants: `ops: []` for Month-End Close Reviewer and Audit Report Agent. Skills are assigned. Nothing to call. `ctl-books` / `lock` and `audit` / `report` are costume on the Catalog axis even if BOT.md is long.

### Close demo writes `.cfo/runs`, not the Computer (T5, T2)

`python3 main.py close-month` chdirs into `.cfo/`. RUN.md says do not point live Bots at `.cfo/runs`. The documented close demo does exactly that. September stays BLOCKED. Honest Kernel. Not Routine `month-end`. Not a Verifier Handle.

### HOST.md vs host module was a miss (migration audit)

Close host had to be restored so treatment Handles could be written. Runner still in the neighborhood. Dual bus.

### Story forecast vs trusted cash (T11)

Process law: trusted cash is the forecast starting balance. Story may build forecast from AP, AR, payroll Kernel ops without a rec sign-off. Unlocked numbers are supposed to be labeled. Nothing proves the label appears. A confident forecast before rec is a lie.

### Reporting reviewers dropped without a replacement critique (intentional, still a hole)

Grain: story does not move money, so a twin with the same tools is a second prompt; audit samples the pack. Audit samples after the fact. Nothing in-line refuses a fluent board sentence that cites a real id but implies the wrong causal story. Kernel `flag_unsupported_claims` helps. Fluency remains a risk.

### Adversarial holdout not planted (T12)

Capabilities.md: 109 scenarios, stealth theft during a CFO sabbatical, not in operational books. Loud decoys are planted (dup vendor, round wire, GM move). Audit that retells decoys looks impressive and is not the product.

### Audit report Profile tools=[] (T8)

Interpretation can call audit read ops. Report language comes from `ReportStats` on the packet. That can be correct Kernel ownership. It can also mean the report Bot never needs to exist as a lane. Grain kept it as a Profile because output type differs. Empty Grants make the Profile a second prompt on the same slug. That is allowed. It is also easy to treat as a fake Bot.

### Routine cadences were broken, then fixed in Harness (T5 remainder)

`weekly` / `monthly` now parse. `autoRoutines: false` on live `client.json`. Month-end still will not fire itself. `period-story` and `post-close-assurance` same.

### BOT.md cwd (T6)

Same as other slugs. Close, story, audit instructions miss the Computer.

---

## Inadequacies of things that “work”

Accrual Kernel (history, contract, usage, PO candidates) is real. Skills `accrual-evidence-evaluation` and `accrual-method-selection` restates those candidates (T7). The specialist remainder: Harbor-class “same vendor, new period, evidence still supports last method” vs “evidence changed, do not copy last month.” Skill `prior-period-precedent` is aimed at that. It is assigned to many Display names. If it becomes a generic essay, it stops being specialist.

Prepaid and FA Kernel schedules are deterministic. Profiles `prepaid` and `assets` have no write Catalog ops. The Bot chooses among treatments; Kernel posts schedules. That is good ownership. The inadequacy: a Bot with only get_* ops can still narrate a capitalization that Kernel already flagged. The narration is the judgment. The files try to make the narration a procedure.

BS rec `classify_packet` must not force a match. Same shape as cash unexplained. Good. Skill `balance-sheet-reconciliation` restates that.

Close checklist DAG in Kernel is the real coordinator. Putting a language model on `coordinate` without tools is how you get a novelist. Grain already warned: merge `story` into `close` and close becomes a novelist. Keep them split.

---

## Capability this pass must possess

When close/story/audit are adequate:

1. Month-end walks treatments as separate Wakes, one Profile each. No Grant union.
2. Accrue / skip / insufficient is a Kernel-legal choice with evidence. Harbor can reuse a method only when current evidence supports it. October actual bill can reverse the accrual. That reversal is not fully wired in the default demo path (gap recorded).
3. Prepaids spread over the service period. Fake P&L on an adversarial prepaid stays holdout, not operational.
4. Dell-class capital invoice depreciates on the same identity as AP.
5. BS recs tie or name the break. They do not force-match $12.40.
6. `ctl-books` / `lock` sees `evaluate_close_gates`. It cannot talk past a failed gate. CLOSED is Kernel.
7. Story packets exist with evidence ids. Unlocked drafts say UNLOCKED. Forecast miss uses Kernel actuals vs an immutable snapshot.
8. Audit findings cite control IDs the Kernel attached. Operational run cannot see ground truth. Books are unchanged by audit.
9. The judged close of September 2026 stays BLOCKED on unexplained cash. That is success.

This file does not specify flux prose, board tone, or how audit phrases a finding. It requires citations, isolation, and an honest lock.

---

## Novelty fence

Do not add Bots `accrue`, `prepaid`, `assets`, `bs`.
Do not make Close Manager a sixteenth Bot.
Do not make `story` a Verifier.
Do not make `audit` concur on pay-run.
Do not merge `story` into `close`.
Do not unlock the period by editing the bank line in Memory.
Do not plant stealth theft into operational books just to have a wow finding, if Capabilities.md still marks that as holdout.
Do not freeze a close checklist order in BOT.md that duplicates `ready_tasks`. Kernel already has the DAG. The specialist remainder is how this entity’s recurring vendors behave at month-end, which is memory, not a second DAG.
