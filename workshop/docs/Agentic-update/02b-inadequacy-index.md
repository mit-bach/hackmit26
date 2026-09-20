# Inadequacy index

Lookup from failure category to the files that instance it. Use with `02-failure-taxonomy.md`. Not a fix list.

---

## T1 Identity error

- Hunting Bot `ar`: `pipes/ar.md`
- World folder vs live Roster: `pipes/intake.md`, `surfaces/world-inbox.md`
- Stripe slug, empty Display name: `pipes/intake.md`, `pipes/cash.md`
- cfo-floor slug collision: `01-intended-office.md`

## T2 Split brain

- Four AR send stories: `pipes/ar.md`
- Live catalog 89 vs instance 94: `evidence/live-computer-2026-09-20.md`
- Fifteen vs sixteen grain: `01-intended-office.md`, `surfaces/world-inbox.md`
- handle-map vs intercept for collect: `pipes/ar.md`, `surfaces/verifiers.md`
- Dual inbox stacks: `pipes/intake.md`
- Constructor vs BOT.md vs Skill: `surfaces/other-prompt-layers.md`

## T3 Tool / Grant missing

- `send_office_outbound` ImportError: `pipes/ar.md`, `surfaces/grants-and-tools.md`
- Empty ops Close Manager / lock / audit report: `pipes/close-story-audit.md`
- Stripe empty Grants: `pipes/cash.md`

## T4 Last mile

- Dun never reaches mailbox: `pipes/ar.md`, `surfaces/world-inbox.md`
- Missing-field mail never answered: `pipes/intake.md`

## T5 Bus not attached

- `--fake` in RUN.md: `surfaces/harness-protocol.md`
- No collect/cash/close Handles on 2026-09-20: `evidence/live-computer-2026-09-20.md`
- close-month writes `.cfo/runs`: `pipes/close-story-audit.md`
- Kernel hosts vs Harness inbox: `surfaces/wakes-and-routines.md`

## T6 Prompt / Kernel collision

- Skills restate must_hold / enforce_collection: `surfaces/skills.md`
- BOT.md cwd: `surfaces/bot-md.md`
- ask_user still taught: `surfaces/harness-protocol.md`, `surfaces/verifiers.md`
- Skill says preview, constructor says send: `pipes/ar.md`

## T7 Over-specified procedure

- Skill skeleton: `surfaces/skills.md`
- BOT.md case law and planted ids: `surfaces/bot-md.md`
- Novelty fence: `03-novelty-boundary.md`

## T8 Under-specified done-when

- Collect “contacted” without send: `pipes/ar.md`
- Coordinate ops []: `pipes/close-story-audit.md`

## T9 Verifier / SoD

- Two Handle stores: `surfaces/harness-protocol.md`
- intercept default operator: `surfaces/verifiers.md`
- HUMAN_REVIEW CLI: `pipes/ar.md`
- Shared skills doer/reviewer: `surfaces/skills.md`

## T10 Memory does not change next period

- AP prior_cases static: `pipes/ap.md`, `surfaces/memory-and-learning.md`
- AR learn via voided CLI: `surfaces/memory-and-learning.md`

## T11 Cross-pipe identity

- INV-S12 marker never in Kernel: `pipes/ap.md`, `evidence/live-computer-2026-09-20.md`
- Forecast before trusted cash: `pipes/cash.md`, `pipes/close-story-audit.md`
- Apply identifiers vs cash re-guess: `pipes/cash.md`

## T12 Demo stub as product

- MSG-S12 loop: `evidence/live-computer-2026-09-20.md`
- Loud audit decoys vs holdout: `pipes/close-story-audit.md`

## T13 Leftover V1 bus

- Runner in workflow.py: `01-intended-office.md`, each pipe “what is broken”
- Collections constructor ImportError blocks live=True: `pipes/ar.md`

---

## By pipe, the single loudest inadequacy

| Pipe | Loudest inadequacy | Why it is inadequate even if Kernel tests pass |
| --- | --- | --- |
| Intake | World + send not on live Computer | Mail does not go around. Classification of seeded files is not a mailbox. |
| AP | Match is strong; learning and live bills are not | A Verifier refusing a marker is protocol, not payables. |
| AR | Apply/collect split is right; send is dead | Aging without contact is a report. The office must collect. |
| Cash | Tie-out and $12.40 law are strong; Stripe Bot and identifier handoff are not | Rec without AR/AP identifiers restarts the argument Close inherits. |
| Close / story / audit | Honest BLOCKED is strong; coordinate/lock/report empty ops and `.cfo/runs` demo path are not | A board pack on unlocked, unreconciled numbers is a printout of a lie. |

---

## What is good, do not delete (pointer)

`04-what-is-good.md`. Grain split, Kernel law, fail closed, Verifier idea, Handle protocol, planted $12.40.
