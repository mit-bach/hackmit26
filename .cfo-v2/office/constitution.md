# Office of the CFO — Client-system Constitution

Session 00 materializes this file. Later sessions treat it as law.

Client-system root on disk: `.cfo-v2/`.
Every `office/…` path in a session write-list lives under `.cfo-v2/office/`.
Computer root: `.cfo-v2/office/computer`.
Bind: `HARNESS_COMPUTER=<repo>/.cfo-v2/office/computer`.
`HARNESS_BOT` is the grain slug (`ctl-pay`, not `bot_ctl_pay`).

This file is the durable copy of the migration Constitution, plus SUPERSEDES, the name map, the fifteen slugs, the id scheme, Rooms, Routines, and slug-map notes. It does not replace `design-workshop/dominik/cfo-bot-grain.md`. Grain remains the test for adding a Bot.

---

## SUPERSEDES

See `office/SUPERSEDES.md`. Short list:

- `.cfo/README.md` language that human review is a first-class completion state
- `docs/CFO_HARNESS_EXTENSION.md` sentences that park pay-run, period lock, or review on the human Operator
- CLI commands whose happy path is a person mutating a review queue (`ar-review-correct`, close `--resolve` as a human). They may remain as eval fixtures / emergency tools. They are not the office’s completion path
- In-process `Runner` as the Bot bus
- Any design that uses `.harness/Harness-v2/examples/cfo-floor` as the Roster

Kernel statuses named `HUMAN_REVIEW` may remain as fail-closed outcomes. The queue owner is a Verifier Bot (`ctl-pay`, `ctl-cash`, `ctl-books`). The Harness Operator is an emergency stop and a demo overlay. It is not a worker.

---

## Product

This Client system on Harness v2 fully replaces an Office of the CFO. Not a copilot. Not a staffing reduction. The office must complete AP, AR, cash, close, reporting, and audit with zero humans in the completion path.

Uncertain or high-stakes work goes to a Verifier Bot (`ctl-pay`, `ctl-cash`, `ctl-books`). It never asks a person. It never calls `ask_user` to get unblocked. It never waits on `HUMAN_REVIEW` as a human queue.

## What we migrate off

The Python tree under `.cfo/` used the OpenAI Agents SDK as a private harness: `Agent()` objects, `Runner`, in-process handoffs, CLI review commands. That control plane is destroyed. Do not port it.

Keep the Kernel: arithmetic, candidates, cents, `must_hold`, `evaluate_close_gates`, period lock math, eval isolation, stores under `.cfo/data` and `.cfo/runs`.

## What we migrate onto

Harness v2 at `.harness/Harness-v2`. Named Bots, one Computer, Handles (accept ≠ complete), inboxes, Rooms, per-Bot Memory, Routines, headless HTTP. Pi is the turn engine inside a Bot. The Client loads as an extension beside Harness. Finance types do not enter Harness core.

Read and obey:

- `design-workshop/dominik/cfo-bot-grain.md` (Roster grain: 15 Bots, four tests)
- `docs/CFO_HARNESS_EXTENSION.md` (compiler, grants, sidecar, facade) except every sentence listed in `office/SUPERSEDES.md`
- `GROK-WORKSHOP/harness-init/engineers/lark/HARNESS-V2.md`
- `docs/LAYOUT.md`
- this file

## Fifteen Bots

Do not invent a sixteenth without failing Tests A–D in the grain.

| Class | Slugs |
| --- | --- |
| Source | `email`, `stripe`, `bank`, `books` |
| Operator | `ap`, `pay`, `apply`, `collect`, `cash`, `close`, `story` |
| Verifier | `ctl-pay`, `ctl-cash`, `ctl-books` |
| Assurance | `audit` |

`.harness/Harness-v2/examples/cfo-floor` is a Harness bind fixture. It is not this office. Ignore those six slugs (`ingest`, `ap`, `ar`, `cash`, `close`, `audit` as that fixture’s Roster). This office’s `ap`, `cash`, `close`, and `audit` slugs come from the grain, not from that example.

## Name map

One name for one thing.

| Name | Meaning |
| --- | --- |
| Bot | Standing Harness identity (slug, lane, Memory). Not a child. Not a subagent. Not a Display name |
| Display name | Python `Agent(name=...)` string. Grant source. Becomes a Profile |
| Profile | One Grant set on one Bot. A Wake names a Profile. Never union two Grant sets in one turn |
| Kernel | Python engine. Sidecar serves it. Sidecar is not a Bot |
| Handle | Accept-time peer work. Write a path, `bot_send_prompt`, await done |
| Connector | Provider or Kernel op, not a Bot |
| Computer | `office/computer/` for this Client. Kernel code stays in `.cfo/` |
| Operator | The human at the Harness HTTP control plane. Emergency stop. Demo overlay. Not a worker |
| Verifier | Concurrence Bot. Queue owner for fail-closed Kernel statuses |
| Pipe | AR, AP, cash, or close. A process. Not a Bot |
| Wake | Webhook, poll, Routine, or Handle that starts a Bot |
| Grant | Catalog ids for one Display name, compiled to `cfo/grants.json` |
| Catalog | `cfo/catalog.json`. Kernel ops. Session 00 leaves `ops: []` |

A Pipe is not a Bot. A Display name is not a Bot. A Connector is not a Bot. A Kernel validator is not a Bot. Sample-data Display names are not Bots.

## Hard rules

1. Do not spawn subagents or children as the Bot network. Every identity is a surface Bot with `HARNESS_BOT` bind.
2. Do not put finance types, close DAGs, or specialist names in `.harness/Harness-v2/src`.
3. Skills never grant tools. Tools/Grants come from constructor lists compiled to `cfo/grants.json`.
4. Python wins on amounts. The model chooses among Kernel candidates. It does not invent totals.
5. Fail closed. Missing evidence is refuse / HOLD / INSUFFICIENT, not a guess.
6. Do not union Grants when two Display names share a slug. Use Profiles.
7. Rooms in this Harness are 2–6 members. Partition Rooms. Do not put 15 Bots in one Room.
8. Roster `approvalLevel` for these Bots is `"never"`. Do not park consequential tools on the human Operator.
9. Eval isolation stays. Operational Bots never load `expected_results.json`, ground truth, or `get_audit_ground_truth`.
10. Sample-data Display names are not Bots.
11. Do not ask a human questions to complete the work of the office. If a session is blocked on a product decision the grain already made, follow the grain. If blocked on a missing file from an earlier session, write the slice against the contracts and leave `NOTES.md` under `office/bots/<slug>/`.
12. One name for one thing. Use the grain’s names.

## Id scheme

Pick once. Stay consistent.

| Field | Rule | Example |
| --- | --- | --- |
| `slug` | Grain slug. Hyphens stay | `ctl-pay` |
| `id` | `bot_` + slug with hyphens replaced by underscores | `bot_ctl_pay` |
| Bind | `HARNESS_BOT=<slug>` | `HARNESS_BOT=ctl-pay` |
| Folder | `office/bots/<slug>/` | `office/bots/ctl-pay/` |

Harness `findBot` matches `id`, `slug`, or `name`. Room `members` and Routine `bot` use **slug**.

## Roster

File: `office/computer/harness/roster.json`.

- `system`: `cfo-agentic-system`
- `computer`: `office/computer` (relative to Client-system root `.cfo-v2`)
- Fifteen Bots. No `ingest`. No `ar` as a Bot (AR is a Pipe; Operator Bots are `apply` and `collect`)
- `approvalLevel`: `"never"` on all fifteen
- `instructions`: two to five sentences. Point at `office/bots/<slug>/BOT.md`. Never ask a human. Name the Verifier slug when the grain names one

### Rooms (2–4 members, never more than 6)

| Room id | Members (slugs) |
| --- | --- |
| `intake` | `email`, `stripe`, `bank`, `books` |
| `pay` | `ap`, `pay`, `ctl-pay` |
| `cash` | `apply`, `collect`, `cash`, `ctl-cash` |
| `books-close` | `close`, `ctl-books`, `story`, `audit` |

### Routines (wake the owning Bot; not a human ticket)

Harness encodes a Room conversation as `room:<roomId>`. Do not use default `operator_dm` for these Routines.

| Routine | Bot | Cadence | Conversation |
| --- | --- | --- | --- |
| `weekly-pay-run` | `pay` | weekly | `room:pay` |
| `daily-aging` | `collect` | daily | `room:cash` |
| `month-end` | `close` | monthly | `room:books-close` |
| `post-close-assurance` | `audit` | monthly | `room:books-close` |

## Slug map

File: `office/computer/cfo/slug-map.json`. Operator-owned topology. No list-unions. `defaultProfile` required on every slug.

Each Profile value is exactly one Display name (or empty string when no Display name exists yet). Two Display names never become one `ops` array.

### Stripe Profile `payout`

Grain Test A/B: Stripe `payout.paid` is a real Wake and a real object. There is **no** Python `Agent(name=...)` for it today. Slug-map still has Bot `stripe`, Profile `payout`, `defaultProfile` `payout`. The Display-name string is empty. Grants stay empty until session 03. Do not invent a Display name. Do not emit `InvoiceCandidate`.

### Shared grain Profile names (not Grant unions)

Grain maps several reviewer Display names onto one Profile **name**. The slug-map stores **one** Grant-source Display name per Profile. Session 09 may tighten Grants with catalog overrides. Session 00 does not union `ops` arrays.

| Bot | Profile | Grant-source Display name | Other grain Display names (identity only, not unioned) |
| --- | --- | --- | --- |
| `ctl-pay` | `review-match` | AP Reviewer | AP Approver (same constructor tools); AP Audit (stricter: no `get_prior_cases`) |
| `ctl-pay` | `review-pay` | Payment Audit | — |
| `ctl-books` | `review-treatment` | Prepaid Reviewer | — |
| `ctl-books` | `review-assets` | Fixed Asset Reviewer | — |
| `ctl-books` | `review-bs` | Balance Sheet Reconciliation Reviewer | — |
| `ctl-books` | `lock` | Month-End Close Reviewer | — |

Reporting Reviewer Agent and Forecast Reviewer Agent are not lanes. `audit` samples the pack. They are not slug-map rows.

Five sample-data Display names are not Bots and are not slug-map rows.

Close Manager is Profile `coordinate` on `close` (and Routine `month-end`). It is not its own Bot.

## BOT.md

Template: `office/templates/BOT.md`.
Stubs: `office/bots/<slug>/BOT.md`. Later sessions replace the body. Session 00 must not overwrite a later session’s `BOT.md` if that file already exists.

Required headings:

```
# {slug}
## Identity
## Wake
## Object
## Profiles
## Catalog ops
## Kernel
## Handoffs
## Verifier
## Memory
## Must not
## Done when
```

Identity first line: `You are Bot `{slug}`. You own {object}.`

Prompt rules: no “helpful assistant”. No “ask the user”. Uncertainty is operational: call the Kernel op; on fail-closed status, Handle to the Verifier with the packet path. Do not chat. Do not paste full evidence into instructions. SAFETY lives on BOT.md once. Skills never grant tools.

## Computer files

```
office/computer/
  harness/roster.json
  cfo/catalog.json      # version 1, ops: [] until session 01
  cfo/grants.json       # version 1, agents: {} until session 01 / 03
  cfo/slug-map.json
```

Kernel code stays in `.cfo/`. Sidecar is not a Bot. Catalog ops are not a Bot.

## Stop conditions

If you are about to add a Bot, run Tests A–D from the grain. If you are about to ask a human to approve a bill, stop and route to `ctl-pay`. If you are about to edit Harness core to know what an invoice is, stop.

Session 00 does not migrate Kernel workflows. It does not write the Pi facade. It does not copy `examples/cfo-floor`.
