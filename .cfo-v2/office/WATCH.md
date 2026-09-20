# Grain § watch later — still open after session 12

Do not “solve” these by adding a seventeenth Bot. Bot `world` already passed Tests A–D. See `design-workshop/dominik/cfo-bot-grain.md` §11.

1. **Stripe is not an invoice source.** Bot `stripe` Profile `payout` has no constructor. Grants stay empty. `invoice_candidates` stays 0.
2. **No bank webhook.** Bot `bank` still exists. Wake is poll.
3. **Payment Scheduler and Payment Audit share constructor `tools=`.** `ctl-pay` / `review-pay` instructions forbid rebuilding the plan (`get_payment_candidates`, `get_approved_pool`). Compiler still copies the constructor list. Tightening is Grant-override work, not a new Bot.
4. **AP Reviewer and AP Approver share tools.** They share Bot `ctl-pay` Profile `review-match`. They are not unioned onto `ap`.
5. **Two close entrypoints.** Lock door is `close/month_end`. `run_cfo_close` is a test packet.
6. **`HUMAN_REVIEW` fixture strings.** Queue owner is a Verifier Bot. Cases still expect fail-closed, not `MATCHED` / `AUTO_APPLY`.
7. **No AR invoicing Bot.** Open invoices arrive as data.
8. **Email carries two Pipes.** One Source Bot. Destinations are `ap` or `apply`.
9. **Prompt-level contradictions** among Display-name instruction blocks. Later pass.
10. **Harness `ask_user` still exists on the protocol surface.** This Client intercepts it and refuses. Roster `approvalLevel` is `never`. Do not fork Harness to know invoices.

Session 10 also added Routine `period-story` waking Bot `story`. Constitution session 00 listed four Routines. The extra Routine still fires on the owning Bot in Room `books-close` (4 members). It is not a seventeenth Bot.

Rohan `durable-inbox-ap-persistence` inbox and Stripe simulation landed as Kernel under Bots `email` and `stripe`. Bot `world` is the simulated outside mailbox (Counterparty Message Agent). Finance Inbox Agent is Email Profile `triage`. Classify stays on Email.
