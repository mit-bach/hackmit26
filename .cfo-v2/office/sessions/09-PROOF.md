# Session 09 — Verifier Bots

Date: 2026-09-19. Kernel/unit proofs. Handle completion was **not** live-proven. Pi was not driven.

This session removes people from the completion path. Queue owner for fail-closed `HUMAN_REVIEW` is `ctl-pay`, `ctl-cash`, or `ctl-books`. The Harness Operator is not a worker.

## Commands

```bash
python3 .cfo-v2/office/compiler/prove.py
.cfo/.venv/bin/python -m pytest \
  .cfo/tests/test_verifier_session09.py \
  .cfo/tests/test_workflow.py \
  .cfo-v2/office/compiler/test_compile_denylist.py \
  .cfo/tests/test_scheduling.py::test_pay_host_never_calls_ask_user \
  -q
cd .cfo-v2/office/computer/cfo && npm test
```

Results:

- `prove.py`: compile SoD passed. 80 Catalog ops. 43 Display names. Payment Audit lacks `get_payment_candidates` / `get_approved_pool` / `create_accrual`. Only Accrual Agent holds `create_accrual`.
- pytest: **21 passed** (7 session-09 proofs + workflow + denylist + pay-host grep).
- `npm test`: **12 passed** (includes ctl-pay Grant refuse, ctl-books Grant refuse, `create_accrual` → `verifier_required` to `ctl-books`, completed Handle proceeds past intercept to sidecar).

## Proofs

| Claim | Result |
| --- | --- |
| Wrong Bot: `ap` cannot finalize APPROVE without a completed `ctl-pay` Handle | `commit_to_pay_pool(..., ctl_pay_concurred=False)` is false. `complete_ctl_pay_handle(..., source_slug="ap")` raises. Pay pool write happens only after ctl-pay CONCUR on the AP Audit second Wake. |
| `ctl-pay` cannot call RECORD_TOOLS / cannot `create_accrual` | Kernel `assert_op_allowed` raises. Client `search_connected_tools` / `call_connected_tool` return forbidden. |
| `ctl-books` cannot `create_accrual`; cannot lock if gates fail | Grant refuse on both Profiles. `apply_ctl_books_lock` CONCUR with no state or failed `evaluate_close_gates` stays REFUSE; period is not CLOSED. |
| Planted `$12.40` | Seeded cash recon stays unexplained. `apply_ctl_cash_rec(..., CONCUR)` is REFUSE. Period is not RECONCILED. |
| Grep production hosts | `ask_user(`, `waiting on human`, `ar-review-correct` absent from AP/pay/apply/cash/close hosts and Client intercept. `ar-review-correct` remains emergency CLI only. |
| No fourth Verifier | Roster has `ctl-pay`, `ctl-cash`, `ctl-books` only. `approvalLevel` is `never`. |

## Disk

```
.cfo-v2/office/bots/ctl-pay/BOT.md
.cfo-v2/office/bots/ctl-pay/profiles/review-match.md
.cfo-v2/office/bots/ctl-pay/profiles/review-pay.md
.cfo-v2/office/bots/ctl-pay/NOTES.md
.cfo-v2/office/bots/ctl-cash/BOT.md
.cfo-v2/office/bots/ctl-cash/profiles/review-apply.md
.cfo-v2/office/bots/ctl-cash/profiles/review-rec.md
.cfo-v2/office/bots/ctl-cash/NOTES.md
.cfo-v2/office/bots/ctl-books/BOT.md
.cfo-v2/office/bots/ctl-books/profiles/review-treatment.md
.cfo-v2/office/bots/ctl-books/profiles/lock.md
.cfo-v2/office/bots/ctl-books/NOTES.md
.cfo-v2/office/computer/cfo/catalog.overrides.json
.cfo-v2/office/computer/cfo/queue-owners.json
.cfo-v2/office/computer/cfo/extensions/intercept.ts
.cfo/verifier/queue_owners.py
.cfo/verifier/grants.py
.cfo/verifier/handles.py
.cfo/verifier/concurrence.py
```

Payment Audit constructor still lists `SCHEDULER_TOOLS`. Compiler `grantDenylist` strips rebuild ops. Do not union Verifier Grants with Operator Grants.

AP Audit is a second Wake of `ctl-pay` / `review-match` (`audit: true`). Not a person. Not `ap` approving itself.
