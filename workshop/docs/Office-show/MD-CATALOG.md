# Markdown an office Bot can read
Source of truth for the live template. Instance folders (`.cfo-v2/office/instances/*`, `.cfo-v2/prove-fork/`) clone these files. They are the same texts on another Computer, not a second set of instructions. `node_modules` readmes are omitted.
How a file gets into a turn:
- **Pasted.** `assembleContext` puts it in the system prompt: `office/system.md`, `BOT.md`, the active `profiles/*.md`, and each `SKILL.md` named on that Bot in `harness/roster.json`.
- **Card.** `harness/PROTOCOL.md` and every `harness/bots/<id>/SYSTEM.md` and `pi-session/SYSTEM.md` are the same protocol card, written by Harness. The context module no longer depends on the model opening them.
- **Memory.** `harness/bots/<id>/memory/MEMORY.md` is not pasted. The Bot can `memory_read` it.
- **Desk.** `workspace/<slug>/README.md` sits on the Computer. It is not pasted unless a Bot opens it.
- **On disk only.** NOTES, PROOF, HOST, routines, demo notes, session notes, and the world pack. A Bot with `read` or `bash` can open them. They are not the system prompt. `sessions/ADVERSARIAL-SCENARIOS.md` and `world/maximor/holdout/ADVERSARIAL-PLANT-NOTES.md` are answer keys. Operational Bots must not load them.

`computer/office/bots` is a symlink to `.cfo-v2/office/bots`. Editing either path edits the same files.

## Pasted every wake: office layer
- `.cfo-v2/office/computer/office/system.md` (1562 bytes) — Office system

## Pasted every wake for that Bot: BOT.md
Sixteen standing Bots. `templates/BOT.md` is a blank pattern, not a seventeenth Bot.
- `.cfo-v2/office/bots/ap/BOT.md` (3982 bytes) — ap
- `.cfo-v2/office/bots/apply/BOT.md` (2904 bytes) — apply
- `.cfo-v2/office/bots/audit/BOT.md` (4617 bytes) — audit
- `.cfo-v2/office/bots/bank/BOT.md` (2277 bytes) — bank
- `.cfo-v2/office/bots/books/BOT.md` (2447 bytes) — books
- `.cfo-v2/office/bots/cash/BOT.md` (5598 bytes) — cash
- `.cfo-v2/office/bots/close/BOT.md` (5440 bytes) — close
- `.cfo-v2/office/bots/collect/BOT.md` (3294 bytes) — collect
- `.cfo-v2/office/bots/ctl-books/BOT.md` (3617 bytes) — ctl-books
- `.cfo-v2/office/bots/ctl-cash/BOT.md` (3347 bytes) — ctl-cash
- `.cfo-v2/office/bots/ctl-pay/BOT.md` (3826 bytes) — ctl-pay
- `.cfo-v2/office/bots/email/BOT.md` (3990 bytes) — email
- `.cfo-v2/office/bots/pay/BOT.md` (3927 bytes) — pay
- `.cfo-v2/office/bots/story/BOT.md` (5833 bytes) — story
- `.cfo-v2/office/bots/stripe/BOT.md` (2410 bytes) — stripe
- `.cfo-v2/office/bots/world/BOT.md` (3831 bytes) — world
- `.cfo-v2/office/templates/BOT.md` (1111 bytes) — {slug} (template, not pasted)

## Pasted when that profile is active
- `.cfo-v2/office/bots/ap/profiles/investigate.md` (1184 bytes) — Profile `investigate`
- `.cfo-v2/office/bots/ap/profiles/prepare.md` (1210 bytes) — Profile `prepare`
- `.cfo-v2/office/bots/apply/profiles/apply.md` (924 bytes) — Profile apply
- `.cfo-v2/office/bots/audit/profiles/interpret.md` (1908 bytes) — Profile `interpret`
- `.cfo-v2/office/bots/audit/profiles/report.md` (1334 bytes) — Profile `report`
- `.cfo-v2/office/bots/bank/profiles/card.md` (768 bytes) — Profile `card`
- `.cfo-v2/office/bots/books/profiles/edi.md` (481 bytes) — Profile `edi`
- `.cfo-v2/office/bots/books/profiles/erp-invoice.md` (689 bytes) — Profile `erp-invoice`
- `.cfo-v2/office/bots/books/profiles/procurement.md` (643 bytes) — Profile `procurement`
- `.cfo-v2/office/bots/cash/profiles/investigate.md` (1673 bytes) — Profile `investigate`
- `.cfo-v2/office/bots/cash/profiles/match.md` (1044 bytes) — Profile `match`
- `.cfo-v2/office/bots/close/profiles/accrue.md` (1503 bytes) — Profile `accrue`
- `.cfo-v2/office/bots/close/profiles/assets.md` (1231 bytes) — Profile `assets`
- `.cfo-v2/office/bots/close/profiles/bs.md` (1274 bytes) — Profile `bs`
- `.cfo-v2/office/bots/close/profiles/coordinate.md` (1158 bytes) — Profile `coordinate`
- `.cfo-v2/office/bots/close/profiles/prepaid.md` (1279 bytes) — Profile `prepaid`
- `.cfo-v2/office/bots/collect/profiles/chase.md` (831 bytes) — Profile chase
- `.cfo-v2/office/bots/ctl-books/profiles/lock.md` (1171 bytes) — Profile `lock`
- `.cfo-v2/office/bots/ctl-books/profiles/review-assets.md` (450 bytes) — Profile `review-bs`
- `.cfo-v2/office/bots/ctl-books/profiles/review-bs.md` (450 bytes) — Profile `review-bs`
- `.cfo-v2/office/bots/ctl-books/profiles/review-treatment.md` (738 bytes) — Profile `review-treatment`
- `.cfo-v2/office/bots/ctl-cash/profiles/review-apply.md` (917 bytes) — Profile `review-apply`
- `.cfo-v2/office/bots/ctl-cash/profiles/review-rec.md` (959 bytes) — Profile `review-rec`
- `.cfo-v2/office/bots/ctl-pay/profiles/review-match.md` (1133 bytes) — Profile `review-match`
- `.cfo-v2/office/bots/ctl-pay/profiles/review-pay.md` (1179 bytes) — Profile `review-pay`
- `.cfo-v2/office/bots/email/profiles/document.md` (513 bytes) — Profile `document`
- `.cfo-v2/office/bots/email/profiles/employee.md` (619 bytes) — Profile `employee`
- `.cfo-v2/office/bots/email/profiles/inbox.md` (1035 bytes) — Profile `inbox`
- `.cfo-v2/office/bots/email/profiles/invoice.md` (828 bytes) — Profile `invoice`
- `.cfo-v2/office/bots/email/profiles/portal.md` (607 bytes) — Profile `portal`
- `.cfo-v2/office/bots/email/profiles/triage.md` (895 bytes) — Profile `triage`
- `.cfo-v2/office/bots/pay/profiles/schedule.md` (1574 bytes) — Profile `schedule`
- `.cfo-v2/office/bots/story/profiles/board.md` (1958 bytes) — Profile `board`
- `.cfo-v2/office/bots/story/profiles/flux.md` (1571 bytes) — Profile `flux`
- `.cfo-v2/office/bots/story/profiles/forecast-miss.md` (1640 bytes) — Profile `forecast-miss`
- `.cfo-v2/office/bots/story/profiles/forecast.md` (1683 bytes) — Profile `forecast`
- `.cfo-v2/office/bots/stripe/profiles/payout.md` (765 bytes) — Profile `payout`
- `.cfo-v2/office/bots/world/profiles/bank.md` (589 bytes) — Profile `bank`
- `.cfo-v2/office/bots/world/profiles/customer.md` (686 bytes) — Profile `customer`
- `.cfo-v2/office/bots/world/profiles/employee.md` (489 bytes) — Profile `employee`
- `.cfo-v2/office/bots/world/profiles/vendor.md` (888 bytes) — Profile `vendor`

## Pasted when the Bot’s roster lists the skill
Path is `.cfo-v2/office/computer/skills/<name>/SKILL.md`. The same names exist under `.cfo/skills/` except two kernel-only skills that no roster Bot lists.
- `.cfo-v2/office/computer/skills/accrual-evidence-evaluation/SKILL.md` (2484 bytes) — ---. Roster: close.
- `.cfo-v2/office/computer/skills/accrual-method-selection/SKILL.md` (2497 bytes) — ---. Roster: close.
- `.cfo-v2/office/computer/skills/ap-exception-investigation/SKILL.md` (1716 bytes) — ---. Roster: ap.
- `.cfo-v2/office/computer/skills/ar-cash-forecasting/SKILL.md` (2016 bytes) — ---. Roster: story.
- `.cfo-v2/office/computer/skills/ar-collections-policy/SKILL.md` (2504 bytes) — ---. Roster: collect.
- `.cfo-v2/office/computer/skills/audit-finding-writing/SKILL.md` (1230 bytes) — ---. Roster: audit.
- `.cfo-v2/office/computer/skills/audit-sampling-interpretation/SKILL.md` (1750 bytes) — ---. Roster: audit.
- `.cfo-v2/office/computer/skills/balance-sheet-reconciliation/SKILL.md` (1936 bytes) — ---. Roster: close, ctl-books.
- `.cfo-v2/office/computer/skills/bank-charge-invoice-discovery/SKILL.md` (2102 bytes) — ---. Roster: bank.
- `.cfo-v2/office/computer/skills/bank-reference-interpretation/SKILL.md` (2096 bytes) — ---. Roster: cash, ctl-cash.
- `.cfo-v2/office/computer/skills/board-financial-reporting/SKILL.md` (1105 bytes) — ---. Roster: story.
- `.cfo-v2/office/computer/skills/cash-application/SKILL.md` (2177 bytes) — ---. Roster: apply, ctl-cash.
- `.cfo-v2/office/computer/skills/cash-forecasting/SKILL.md` (2523 bytes) — ---. Roster: story.
- `.cfo-v2/office/computer/skills/cash-reconciliation-method-selection/SKILL.md` (2170 bytes) — ---. Roster: cash, ctl-cash.
- `.cfo-v2/office/computer/skills/control-testing-interpretation/SKILL.md` (2042 bytes) — ---. Roster: audit.
- `.cfo-v2/office/computer/skills/early-payment-discount-evaluation/SKILL.md` (1691 bytes) — ---. Roster: pay.
- `.cfo-v2/office/computer/skills/financial-variance-analysis/SKILL.md` (2581 bytes) — ---. Roster: story.
- `.cfo-v2/office/computer/skills/fixed-asset-depreciation/SKILL.md` (1754 bytes) — ---. Roster: close, ctl-books.
- `.cfo-v2/office/computer/skills/forecast-vs-actual-interpretation/SKILL.md` (2018 bytes) — ---. Roster: story.
- `.cfo-v2/office/computer/skills/inbox-triage/SKILL.md` (3388 bytes) — ---. Roster: email.
- `.cfo-v2/office/computer/skills/invoice-field-interpretation/SKILL.md` (2650 bytes) — ---. Roster: email.
- `.cfo-v2/office/computer/skills/invoice-source-identification/SKILL.md` (3960 bytes) — ---. Roster: email, books.
- `.cfo-v2/office/computer/skills/month-end-close-coordination/SKILL.md` (1001 bytes) — ---. Roster: close.
- `.cfo-v2/office/computer/skills/month-end-close-review/SKILL.md` (1153 bytes) — ---. Roster: ctl-books.
- `.cfo-v2/office/computer/skills/payment-prioritization/SKILL.md` (1660 bytes) — ---. Roster: pay.
- `.cfo-v2/office/computer/skills/prepaid-expense-accounting/SKILL.md` (1904 bytes) — ---. Roster: close, ctl-books.
- `.cfo-v2/office/computer/skills/prior-period-precedent/SKILL.md` (1308 bytes) — ---. Roster: ap, cash, close, ctl-pay, ctl-cash, ctl-books.
- `.cfo-v2/office/computer/skills/reconciliation-evidence-validation/SKILL.md` (1660 bytes) — ---. Roster: cash, ctl-cash.
- `.cfo-v2/office/computer/skills/reconciliation-exception-investigation/SKILL.md` (2094 bytes) — ---. Roster: cash, ctl-cash.
- `.cfo-v2/office/computer/skills/reconciliation-reperformance-review/SKILL.md` (1909 bytes) — ---. Roster: audit.
- `.cfo-v2/office/computer/skills/segregation-of-duties-interpretation/SKILL.md` (1819 bytes) — ---. Roster: audit.
- `.cfo-v2/office/computer/skills/superseded-document-handling/SKILL.md` (2051 bytes) — ---. Roster: email, ap.
- `.cfo-v2/office/computer/skills/three-way-match-analysis/SKILL.md` (1732 bytes) — ---. Roster: ap.

Kernel skills with no Computer copy and no roster Bot:
- `.cfo/skills/cross-ledger-data-consistency/SKILL.md` (1704 bytes) — ---.
- `.cfo/skills/synthetic-finance-scenario-design/SKILL.md` (1886 bytes) — ---.

## Same protocol card, written once per Bot
These files are copies of one string. They are not per-Bot instructions.
- `.cfo-v2/office/computer/harness/PROTOCOL.md` (2725 bytes) — How to use tools on this Computer
- `.cfo-v2/office/computer/harness/bots/bot_ap/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ap/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_apply/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_apply/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_audit/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_audit/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_bank/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_bank/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_books/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_books/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_cash/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_cash/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_close/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_close/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_collect/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_collect/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_books/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_books/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_cash/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_cash/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_pay/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_ctl_pay/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_email/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_email/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_pay/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_pay/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_story/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_story/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_stripe/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_stripe/pi-session/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_world/SYSTEM.md` (2725 bytes)
- `.cfo-v2/office/computer/harness/bots/bot_world/pi-session/SYSTEM.md` (2725 bytes)

## Memory files the Bot can open
Not pasted. `memory_read` returns them.
- `.cfo-v2/office/computer/harness/bots/bot_ap/memory/MEMORY.md` (47 bytes) — AP
- `.cfo-v2/office/computer/harness/bots/bot_apply/memory/MEMORY.md` (50 bytes) — Apply
- `.cfo-v2/office/computer/harness/bots/bot_audit/memory/MEMORY.md` (50 bytes) — audit
- `.cfo-v2/office/computer/harness/bots/bot_bank/memory/MEMORY.md` (49 bytes) — Bank
- `.cfo-v2/office/computer/harness/bots/bot_books/memory/MEMORY.md` (50 bytes) — Books
- `.cfo-v2/office/computer/harness/bots/bot_cash/memory/MEMORY.md` (49 bytes) — Cash
- `.cfo-v2/office/computer/harness/bots/bot_close/memory/MEMORY.md` (50 bytes) — Close
- `.cfo-v2/office/computer/harness/bots/bot_collect/memory/MEMORY.md` (52 bytes) — Collect
- `.cfo-v2/office/computer/harness/bots/bot_ctl_books/memory/MEMORY.md` (54 bytes) — ctl-books
- `.cfo-v2/office/computer/harness/bots/bot_ctl_cash/memory/MEMORY.md` (53 bytes) — ctl-cash
- `.cfo-v2/office/computer/harness/bots/bot_ctl_pay/memory/MEMORY.md` (52 bytes) — ctl-pay
- `.cfo-v2/office/computer/harness/bots/bot_email/memory/MEMORY.md` (50 bytes) — Email
- `.cfo-v2/office/computer/harness/bots/bot_pay/memory/MEMORY.md` (48 bytes) — Pay
- `.cfo-v2/office/computer/harness/bots/bot_story/memory/MEMORY.md` (50 bytes) — Story
- `.cfo-v2/office/computer/harness/bots/bot_stripe/memory/MEMORY.md` (51 bytes) — Stripe
- `.cfo-v2/office/computer/harness/bots/bot_world/memory/MEMORY.md` (50 bytes) — World

## Desk readmes
- `.cfo-v2/office/computer/workspace/ap/README.md` (231 bytes) — ap
- `.cfo-v2/office/computer/workspace/apply/README.md` (234 bytes) — apply
- `.cfo-v2/office/computer/workspace/audit/README.md` (234 bytes) — audit
- `.cfo-v2/office/computer/workspace/bank/README.md` (233 bytes) — bank
- `.cfo-v2/office/computer/workspace/books/README.md` (234 bytes) — books
- `.cfo-v2/office/computer/workspace/cash/README.md` (233 bytes) — cash
- `.cfo-v2/office/computer/workspace/close/README.md` (234 bytes) — close
- `.cfo-v2/office/computer/workspace/collect/README.md` (236 bytes) — collect
- `.cfo-v2/office/computer/workspace/ctl-books/README.md` (238 bytes) — ctl-books
- `.cfo-v2/office/computer/workspace/ctl-cash/README.md` (237 bytes) — ctl-cash
- `.cfo-v2/office/computer/workspace/ctl-pay/README.md` (236 bytes) — ctl-pay
- `.cfo-v2/office/computer/workspace/email/README.md` (234 bytes) — email
- `.cfo-v2/office/computer/workspace/pay/README.md` (232 bytes) — pay
- `.cfo-v2/office/computer/workspace/story/README.md` (234 bytes) — story
- `.cfo-v2/office/computer/workspace/stripe/README.md` (235 bytes) — stripe
- `.cfo-v2/office/computer/workspace/world/README.md` (234 bytes) — world

## Routines
Fired by HTTP or the host. The prompt text is the wake, not the system prompt.
- `.cfo-v2/office/bots/audit/routines/post-close-assurance.md` (836 bytes) — Routine `post-close-assurance`
- `.cfo-v2/office/bots/close/routines/month-end.md` (712 bytes) — Routine `month-end`
- `.cfo-v2/office/bots/pay/routines/weekly-pay-run.md` (683 bytes) — Routine `weekly-pay-run`

## Author notes next to the Bots
On disk beside `BOT.md`. Not pasted. A Bot can still open them.
- `.cfo-v2/office/bots/ap/NOTES.md` (1459 bytes) — Session 04 notes — Bot `ap`
- `.cfo-v2/office/bots/apply/NOTES.md` (523 bytes) — Session 06 notes — Bot apply
- `.cfo-v2/office/bots/apply/PROOF.md` (302 bytes) — Session 06 proof
- `.cfo-v2/office/bots/audit/NOTES.md` (730 bytes) — Audit — period pass notes
- `.cfo-v2/office/bots/bank/NOTES.md` (486 bytes) — NOTES
- `.cfo-v2/office/bots/books/NOTES.md` (555 bytes) — NOTES
- `.cfo-v2/office/bots/cash/NOTES.md` (2279 bytes) — NOTES — Cash (prompt 04)
- `.cfo-v2/office/bots/cash/PROOF.md` (659 bytes) — Bot `cash` proof
- `.cfo-v2/office/bots/close/HOST.md` (2627 bytes) — Host — sequence Profiles as separate Wakes
- `.cfo-v2/office/bots/close/NOTES.md` (1751 bytes) — Close — period pass notes
- `.cfo-v2/office/bots/collect/NOTES.md` (614 bytes) — NOTES — collect
- `.cfo-v2/office/bots/collect/PROOF.md` (229 bytes) — Session 06 proof
- `.cfo-v2/office/bots/ctl-books/NOTES.md` (379 bytes) — ctl-books — period pass notes
- `.cfo-v2/office/bots/ctl-books/PROOF.md` (188 bytes) — ctl-books proof
- `.cfo-v2/office/bots/ctl-cash/NOTES.md` (661 bytes) — Session 09 notes — Bot `ctl-cash`
- `.cfo-v2/office/bots/ctl-cash/PROOF.md` (200 bytes) — ctl-cash proof
- `.cfo-v2/office/bots/ctl-pay/NOTES.md` (712 bytes) — Session 09 notes — Bot `ctl-pay`
- `.cfo-v2/office/bots/ctl-pay/PROOF.md` (243 bytes) — ctl-pay proof
- `.cfo-v2/office/bots/email/NOTES.md` (620 bytes) — NOTES
- `.cfo-v2/office/bots/pay/NOTES.md` (937 bytes) — Session 05 notes
- `.cfo-v2/office/bots/pay/PROOF.md` (262 bytes) — pay proof
- `.cfo-v2/office/bots/story/NOTES.md` (798 bytes) — Story — period pass notes
- `.cfo-v2/office/bots/stripe/NOTES.md` (725 bytes) — NOTES — Stripe (prompt 04)
- `.cfo-v2/office/bots/world/NOTES.md` (2115 bytes) — NOTES
- `.cfo-v2/office/bots/world/PROOF.md` (2863 bytes) — World proof

## Office policy on the Computer, not pasted except system.md
- `.cfo-v2/office/computer/office/constitution.md` (10922 bytes) — Office of the CFO — Client-system Constitution
- `.cfo-v2/office/computer/office/SUPERSEDES.md` (4972 bytes) — SUPERSEDES
- `.cfo-v2/office/constitution.md` (10922 bytes) — Office of the CFO — Client-system Constitution
- `.cfo-v2/office/SUPERSEDES.md` (4972 bytes) — SUPERSEDES
- `.cfo-v2/office/RUN.md` (6625 bytes) — Run the Office of the CFO Client system
- `.cfo-v2/office/WATCH.md` (1839 bytes) — Grain § watch later — still open after session 12
- `.cfo-v2/office/DEMO-DESIGN.md` (6832 bytes) — HackMIT demo world — design
- `.cfo-v2/office/DEMO-WALKTHROUGH.md` (2907 bytes) — Office demo walkthrough
- `.cfo-v2/office/computer/ENV.md` (1517 bytes) — Computer env — Kernel sidecar (session 02)

## Demo and reference notes under the office tree
Not pasted. Readable if the working directory can see the repo.
- `.cfo-v2/office/final-demo/CAPABILITIES.md` (19291 bytes) — Capabilities — Office of the CFO
- `.cfo-v2/office/final-demo/DOCUMENTS.md` (6409 bytes) — Document map
- `.cfo-v2/office/final-demo/README.md` (1282 bytes) — Final demo
- `.cfo-v2/office/final-demo/SCENARIOS.md` (8770 bytes) — Scenarios to draw
- `.cfo-v2/office/final-demo/TESTING.md` (5370 bytes) — How we test
- `.cfo-v2/office/final-demo/WORLD.md` (5909 bytes) — World pack — Maximor Demo Corp
- `.cfo-v2/office/reference-datasets/README.md` (2571 bytes) — Reference datasets (gitignored)
- `.cfo-v2/office/reference-datasets/apex-accounting/README.md` (17933 bytes) — ---
- `.cfo-v2/office/reference-datasets/dabstep/data/context/manual.md` (22127 bytes) — Merchant Guide to Optimizing Payment Processing and Minimizing Fees
- `.cfo-v2/office/reference-datasets/dabstep/data/context/payments-readme.md` (1719 bytes) — This is documentation for the payments.csv dataset
- `.cfo-v2/office/reference-datasets/finance-agent-benchmark/README.md` (657 bytes) — ---
- `.cfo-v2/office/reference-datasets/invoice-sandbox-benchmark/README.md` (2569 bytes) — Invoice Sandbox Benchmark
- `.cfo-v2/office/sessions/00-PROOF.md` (3734 bytes) — Session 00 proof
- `.cfo-v2/office/sessions/01-PROOF.md` (5937 bytes) — Session 01 — Client attach (compiler + Pi facade)
- `.cfo-v2/office/sessions/02-NOTES.md` (863 bytes) — Session 02 notes
- `.cfo-v2/office/sessions/02-PROOF.md` (3140 bytes) — Session 02 proof — Kernel sidecar
- `.cfo-v2/office/sessions/03-PROOF.md` (4144 bytes) — Session 03 proof — Source Bots
- `.cfo-v2/office/sessions/04-PROOF.md` (3107 bytes) — Session 04 proof — Operator Bot `ap`
- `.cfo-v2/office/sessions/05-PROOF.md` (3361 bytes) — Session 05 proof — Operator Bot `pay`
- `.cfo-v2/office/sessions/06-PROOF.md` (3522 bytes) — Session 06 proof — Operator Bots `apply` and `collect`
- `.cfo-v2/office/sessions/07-PROOF.md` (2447 bytes) — Session 07 proof — Bot `cash`
- `.cfo-v2/office/sessions/08-PROOF.md` (3548 bytes) — Session 08 proof
- `.cfo-v2/office/sessions/09-PROOF.md` (3369 bytes) — Session 09 — Verifier Bots
- `.cfo-v2/office/sessions/10-PROOF.md` (4196 bytes) — Session 10 proof — Bot `story`
- `.cfo-v2/office/sessions/11-PROOF.md` (4583 bytes) — Session 11 proof
- `.cfo-v2/office/sessions/12-PROOF.md` (8210 bytes) — Session 12 proof — stitch the office
- `.cfo-v2/office/sessions/ADVERSARIAL-SCENARIOS.md` (170856 bytes) — Adversarial scenario catalog — Maximor Demo Corp
- `.cfo-v2/office/sessions/BENCHMARK-IMPORT.md` (1161 bytes) — Track benchmark import — 2026-09-20
- `.cfo-v2/office/sessions/DATA-REFINEMENT-NOTES.md` (8476 bytes) — Data refinement notes — Maximor Demo Corp
- `.cfo-v2/office/sessions/ROHAN-KERNEL-MIGRATION.md` (2735 bytes) — Rohan Kernel migration (inbox, Stripe sim, overlay)
- `.cfo-v2/office/world/README.md` (1007 bytes) — Office world — Maximor Demo Corp
- `.cfo-v2/office/world/maximor/holdout/ADVERSARIAL-PLANT-NOTES.md` (9187 bytes) — Adversarial plant notes — Phase B
