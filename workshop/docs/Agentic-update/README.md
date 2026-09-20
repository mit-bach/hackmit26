# Agentic update — source corpus

This directory is source material plus one launch file. Files `01`–`04`, `02b`, `pipes/`, `surfaces/`, and `evidence/` are not prompts. They do not tell a later agent how to implement. They exist so that agent can see what is broken, why it is broken, what still works, and what a finished pipe must be able to do.

The Cursor agent prompts live in `prompts/`. Same spawn shape as `design-workshop/dominik/Prompts/web-overhaul`: read `prompts/00-SHARED-LAWS.md`, then one numbered file. Do not paste this README as the mission. Do not attach the corpus with `@`. The numbered prompt lists every path.

Date of the live snapshot behind this corpus: 2026-09-20.

Office under audit: `.cfo-v2/office`.
Kernel under audit: `.cfo/`.
Harness under audit: `.harness/Harness-v2`.
Computer: `.cfo-v2/office/computer`.

---

## What this corpus is

1. A taxonomy of failure. Categories of wrong, not a single complaint.
2. A product account. What the Office of the CFO is for.
3. Four pipe analyses: AP, AR, cash, close/story/audit. Intake sits in front of all four.
4. Surface analyses: BOT.md, skills, Grants/tools, Harness protocol, World/inbox, Verifiers, memory, wakes, other prompt layers.
5. An evidence snapshot of the live Computer on 2026-09-20.
6. A launch pack under `prompts/`: shared laws plus five self-contained Cursor briefs.

Each corpus file (`01`–`04`, `02b`, `pipes/`, `surfaces/`, `evidence/`) states:

- intended function (what must be true when the pipe is done)
- what exists
- what is good
- what is broken, with a reason
- inadequacies of things that already “work”
- capability the office must possess
- what this corpus refuses to specify, so a later agent can still invent

---

## What this corpus is not

Do not treat `01`–`04`, `02b`, `pipes/`, `surfaces/`, or `evidence/` as:

- prompts to paste into Cursor (that is `prompts/`)
- a rewrite of BOT.md
- a rewrite of SKILL.md
- a procedure the model must follow
- a list of new Bots to add
- a Harness fork
- a claim that 43 Display names should come back as 43 lanes

Grain law still holds. A Display name is a Grant source. A Bot is a standing Harness identity. A Pipe is a process. A Skill is a prompt. Skills never grant tools.

---

## How to read

Read in this order the first time:

1. This file.
2. `01-intended-office.md`
3. `02-failure-taxonomy.md`
4. `03-novelty-boundary.md`
5. `04-what-is-good.md`
6. `02b-inadequacy-index.md` when you need the loudest break per pipe
7. `pipes/` for the pipe you will work
8. `surfaces/` for the artifact class you will touch
9. `evidence/live-computer-2026-09-20.md` when you need a fact from disk
10. `prompts/README.md` when you are starting the Floor and pipe agents. Paste or point at one numbered file plus `prompts/00-SHARED-LAWS.md`.
11. `docs/Office-prove/` when Bots must be tasked on instances. That directory is the prove loop, not this corpus.
12. `docs/Office-show/` when prove has a verdict and you need one golden desk to live a September and record. That is the tape. Prove Wakes are not that tape.

Process law for the four pipes lives in `design-workshop/dominik/cfo-office-processes.md`. Grain law lives in `design-workshop/dominik/cfo-bot-grain.md`. Constitution and SUPERSEDES live under `.cfo-v2/office/`.

When two documents disagree, this corpus records the disagreement. It does not pick a silent winner except where grain Tests A–D already picked one.

---

## Name map

Use these names only.

| Name | Meaning |
| --- | --- |
| Pipe | AP, AR, cash, or close. A process. Not a Bot. |
| Bot | Standing Harness identity. One slug. One lane. `HARNESS_BOT`. |
| Display name | Python `Agent(name=...)`. Grant source. Becomes a Profile. |
| Profile | One Grant set on one Bot. A Wake names it. Do not union two in one turn. |
| Kernel | Python engine under `.cfo/`. Arithmetic, candidates, hard holds, close gates. |
| Skill | `SKILL.md`. Prompt. Never a tool. |
| Grant | Catalog op ids for one Display name. |
| Catalog | Named Kernel ops in `cfo/catalog.json`. |
| Handle | Accept-time peer work on the Harness bus. Accept is not complete. A peer Handle is not approval. |
| Verifier | `ctl-pay`, `ctl-cash`, `ctl-books`. Concurrence. Not a human. |
| Operator | Human at the Harness HTTP shell. Emergency stop. Not a worker. |
| Computer | `.cfo-v2/office/computer`. Harness cwd. |
| World | Simulated outside mailbox. Written as Bot `world`. Not on the live Roster. |
| Open item | Unfinished ticket: open invoice, open bill, unapplied cash, unmatched bank line, accrual. |

A Pipe is not a Bot. The six-slug tree `examples/cfo-floor` is not this office. Slug `ar` on that fixture is not Bot `collect`.

---

## Index

### Law and product

| File | Contents |
| --- | --- |
| `01-intended-office.md` | What the application is. What “the office completes” means. |
| `02-failure-taxonomy.md` | Categories of broken. Use these labels in later prompts. |
| `02b-inadequacy-index.md` | Category → file pointers. Loudest inadequacy per pipe. |
| `03-novelty-boundary.md` | What a later agent may invent. What it must not freeze. |
| `04-what-is-good.md` | What to keep. Do not “fix” these by deleting them. |
| `05-cursor-agent-prompts.md` | Stub. Real briefs are in `prompts/`. |
| `prompts/README.md` | Spawn order. One numbered file per Cursor agent. Same pattern as web-overhaul. |
| `prompts/00-SHARED-LAWS.md` | Grain, honesty, T-categories, file ownership. Every agent reads this first. |
| `prompts/01-FLOOR.md` … `prompts/05-CLOSE.md` | Self-contained implementing briefs. Floor, AR, AP, cash, close. |

### Pipes

| File | Contents |
| --- | --- |
| `pipes/README.md` | How the four pipes connect. Four handoffs, not a mesh. |
| `pipes/intake.md` | Source objects that feed every pipe. Email, Stripe, bank, books, World. |
| `pipes/ap.md` | Open bills, three-way match, payment-run draft. |
| `pipes/ar.md` | Open invoices, cash application, collections, the missing send. |
| `pipes/cash.md` | Unmatched bank lines, trusted cash, the $12.40. |
| `pipes/close-story-audit.md` | Period completeness, flux, forecast, board pack, assurance. |

### Surfaces

| File | Contents |
| --- | --- |
| `surfaces/README.md` | The artifact classes a later agent will actually edit. |
| `surfaces/bot-md.md` | Standing identity files. Template vs live quality. |
| `surfaces/skills.md` | Prompt procedures. Why a 1:1 copy cannot restore an Agent. |
| `surfaces/grants-and-tools.md` | Catalog, Grants, denylist, empty ops, missing send. |
| `surfaces/harness-protocol.md` | Bind, Handles, Rooms, Routines, two Handle stores, cwd. |
| `surfaces/world-inbox.md` | Simulated mailbox. Dual inbox stacks. World off Roster. |
| `surfaces/verifiers.md` | Concurrence vs rubber stamp vs leftover human queue. |
| `surfaces/memory-and-learning.md` | Precedent that changes the next period. What is not a graph. |
| `surfaces/wakes-and-routines.md` | How work starts. What never starts. |
| `surfaces/other-prompt-layers.md` | Roster, constructors, SAFETY, Routine prompts. BOT.md and skills are not the whole brain. |

### Evidence

| File | Contents |
| --- | --- |
| `evidence/live-computer-2026-09-20.md` | Counts and paths from disk that day. |

### Prove (after repair)

| File | Contents |
| --- | --- |
| `docs/Office-prove/` | Instance loops that task standing Bots. HARD vs SOFT. Skills, pipes, Catalog ops. Not a demo script. |
| `docs/Office-show/` | One golden instance. Onboard, lived September, Demo record, cut videos. |

---

## Constraint for every later writer

The launch prompts already live in `prompts/`. If you write another:

- Point at a pipe and a failure category.
- State the intended function as an outcome on an open item.
- Do not paste a step-by-step reasoning procedure into the new Skill.
- Do not add a Bot unless Tests A–D fail on the current Roster.
- Do not put finance types in Harness `src/`.
- Do not restore `Runner` as the Bot bus.
- Do not resolve the planted $12.40 to make close look finished.
