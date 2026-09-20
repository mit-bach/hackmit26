# Surface — skills

Canonical registry: `.cfo/skills/README.md` plus `.cfo/skills/assignments.py`.
Computer copies: `.cfo-v2/office/computer/skills/<name>/SKILL.md`.
Loader: Kernel `compose_instructions` injects bodies into Display-name constructors. Office Client intersect: `grant.skills ∩ roster.skills`.

Skills never grant tools. That sentence is law. The live failure is that people treat a copied Skill as a restored Agent.

---

## Intended function of this surface

A Skill is reusable specialized judgment for a recurring task. It is not:

- arithmetic
- hashing
- parsing
- hard policy enforcement
- a tool wrapper
- a one-off implementation note

Kernel README: check the registry before adding. Reuse. Do not load every skill into every agent.

Office: Pi loads skill directories. Allowlist is supposed to be per Bot. Whole-tree dump happens unless `HARNESS_CLIENT_SKILLS=1`. Live `extensions.json` now sets that.

---

## Inventory

Computer: 33 `SKILL.md`.
Kernel: 35. Kernel-only: `synthetic-finance-scenario-design`, `cross-ledger-data-consistency` (sample-data; keep off floor Bots).

Statuses mix `new` and `extracted`. Extracted means pulled from old constructor text. New often means the same skeleton written in a later pass. Neither status means “this is good judgment remainder.”

Assignments are by Display name, not by Bot slug. Compiler copies assigned skills onto Grant rows. Roster skills must intersect or the Client drops them.

---

## What is good

The layer exists. Python vs tools vs skills vs agents is the right split.

Skills that name a real remainder (even when the file currently over-specifies):

- `invoice-source-identification` — what kind of document is this.
- `superseded-document-handling` — which copy is live.
- `cash-application` — abstain on ties.
- `reconciliation-exception-investigation` — do not invent a residual story.
- `prior-period-precedent` — reuse only if current evidence still supports it.
- `audit-finding-writing` — language from stats, not from vibes.

Sample-data skills staying off grain Bots is correct.

---

## What is broken

### 1:1 transfer cannot restore tools (T3)

Skills were copied onto the Computer. Collect still cannot send. Stripe still cannot call anything. Close Manager still has `ops: []`.

### Template clone (T7)

Almost every file: Purpose, When to Use, Inputs / Evidence, Procedure, Decision Criteria, Output Expectations, Boundaries.

`skills/README.md` requires that skeleton. The registry itself freezes procedure shape. A later agent that “writes better skills” inside that skeleton will still ship checklists.

### Kernel replay (T6)

`three-way-match-analysis` Procedure: copy exception_types; clean match is approved PO + exact amount + exact vendor + full receipt + no duplicate. That is `must_hold` / `collect_case_evidence` in English.

`ar-collections-policy` Procedure: paid → NO_ACTION, dispute → ESCALATE, cooldown → HOLD, then intensity from age. That is `enforce_collection_decision` plus a tone table.

`cash-application` Procedure: ten numbered Kernel cases.

When the Skill is the Kernel, the specialist has no job.

### Product contradiction (T2, T6)

`ar-collections-policy` says outbox / preview. Collections Agent says send then Handle world. See `pipes/ar.md`.

### Shared skills across SoD (T9)

Payment Scheduler and Payment Audit share `payment-prioritization` and `early-payment-discount-evaluation`.
Cash Application Agent and Cash Application Reviewer share `cash-application`.
AP Preparer and AP Reviewer share `three-way-match-analysis`.

Same Skill on doer and Verifier is easy SoD mush even when Grants differ. A Verifier’s remainder is “find reasons to refuse,” not “rank the run again.”

### `prior-period-precedent` assigned to a crowd

Investigator, several reviewers, accrual, prepaid, month-end lock. A generic precedent essay is not vendor-layout memory for Email or remittance habit for apply. One Skill cannot be every pipe’s learning.

### Roster intersect drops

Known pattern from the 09-19 gap analysis: Roster-only skills dropped if not on the Grant. If someone adds a skill to BOT.md / Roster and not to `assignments.py`, Pi may not see it under Client intersect. Opposite dump: without `HARNESS_CLIENT_SKILLS=1`, every Bot sees every skill directory.

### Empty Grant + skills

Month-End Close Reviewer: skills listed, `ops: []`.
Close Manager: skill `month-end-close-coordination`, `ops: []`.
Stripe: `skills: []`.

Prompt without a door.

---

## Inadequacies of a “complete” skill tree

Thirty-three files look like coverage. Coverage of Kernel English is not coverage of judgment.

A later agent asked to “improve all skills” will produce thirty-three cleaner checklists. That is how this tree was built. It is the failure mode.

The inadequacy to name: skills were extracted from constructor instructions that were already trying to be the whole agent. Extraction preserved the over-specification. It did not discover the remainder.

---

## Capability this surface must possess

When skills are adequate:

1. Each floor Bot has zero or more skills that name judgment Kernel does not already decide.
2. No skill claims a tool.
3. No skill restates a hard hold as a suggestion.
4. Doer and Verifier do not share a ranking/matching skill unless the remainder is truly the same read of facts (usually it is not).
5. AR send is not described as preview-only if the office must send.
6. Sample-data skills stay off floor Bots.
7. The skeleton in `skills/README.md` is not treated as a requirement to freeze Procedure as numbered Kernel replay.

This file does not write the new skills. It states that most live skills are inadequate as specialist brains, and that copying them was never the migration.
