# Session 12 proof — stitch the office

Fifteen grain Bots on one Computer. Compiler Grants, sidecar SoD, Verifier Handles, Kernel fail-closed close. **Handle completion was not live-proven. Pi was not live-proven.** Fake `sendPrompt` workers only — not GrokBot-class.

Client root: `.cfo-v2/`. Computer: `.cfo-v2/office/computer`. Kernel: `.cfo/`. Harness: `.harness/Harness-v2`.

`docs/CFO_HARNESS_EXTENSION.md` §13.9 parks September close on a human mutating source. That sentence is VOID. The queue owner is `ctl-cash` / `ctl-books`. There is no legal Kernel op that explains the planted $12.40. `CLOSED` did not happen.

Session `09-PROOF.md` is not on disk. Session 09 `catalog.overrides.json` `grantDenylist` is present and still applied at compile.

## Commands

Compile (operational Grants omit `get_audit_ground_truth`):

```bash
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```

Result:

```
cfo-catalog compile ok  phase=operational
  catalog ops: 80
  display names: 43
  AP Preparer == AP Approver: no
  Auditor Agent get_audit_ground_truth operational: omitted
  Auditor Agent get_audit_ground_truth evaluation: ['audit.tools.get_audit_ground_truth']
  grant diff vs previous compile: none
```

Constructor-drift fail, then revert. `RECORD_TOOLS` temporarily listed `not_a_catalog_op`; compile exited 1; `agent.py` restored; compile ok.

```
cfo-catalog: /Users/dominikbach/olympus/hackmit/hackmit26/.cfo/agent.py: cannot resolve tools name 'not_a_catalog_op'
compile_exit=1
…
compile_after_revert=0
```

Kernel / unit / sidecar / Handle protocol:

```bash
.cfo/.venv/bin/python -m pytest \
  .cfo-v2/office/tests/test_session12_roster.py \
  .cfo-v2/office/tests/test_session12_sidecar.py \
  .cfo-v2/office/tests/test_session12_eval.py \
  .cfo-v2/office/tests/test_session12_no_human.py \
  .cfo-v2/office/tests/test_session12_handles.py \
  .cfo-v2/office/compiler/test_compile_drift.py \
  .cfo-v2/office/compiler/test_compile_eval_split.py \
  -q
```

Result: **17 passed**.

Pi facade (no Sidecar HTTP, no live Handle complete):

```bash
node --experimental-strip-types --test .cfo-v2/office/computer/cfo/extensions/facade.test.ts
```

Result: **12 passed**.

Fake Handle path (accept ≠ complete; no Pi):

```bash
node .cfo-v2/office/tests/fake_handles.mjs
```

September close without source mutation:

```bash
.cfo/.venv/bin/python main.py close-month --month 2026-09 --seed-demo --deterministic
```

`evaluate-cfo` isolation was proven with `operational_phase_guard` (pytest), not by a full live `python3 main.py evaluate-cfo` run. The eval CLI is allowed to open answer keys under evaluation phase. Operational Bots cannot.

## Proofs required by the session

### Roster is exactly the fifteen grain slugs

```
email stripe bank books ap pay apply collect cash close story ctl-pay ctl-cash ctl-books audit
ids: bot_email … bot_ctl_pay … bot_audit
approvalLevel: never
ingest: False
sample-data Display names are Grants with ops: [] and are not Roster slugs
```

Rooms 2–6: intake 4, pay 3, cash 4, books-close 4. Routines fire on owning Bots (`weekly-pay-run`→pay, `daily-aging`→collect, `month-end`→close, `period-story`→story, `post-close-assurance`→audit). Conversation is `room:<id>`, not `operator_dm`. `period-story` is an extra Routine on Bot `story`, not a sixteenth Bot. See `office/WATCH.md`.

No session-00 stub `BOT.md` remains. Every grain slug has `office/bots/<slug>/BOT.md` (66–119 lines) and Profile files.

Handle destinations in `office/computer/cfo/handle-map.json` are grain slugs. `email`/`bill` → `ap`/`prepare`. `ap`/`approve` → `ctl-pay`/`review-match`. `pay`/`release` → `ctl-pay`/`review-pay`. `close`/`lock` → `ctl-books`/`lock`.

### ap / prepare cannot call create_accrual (sidecar forbidden)

`test_ap_prepare_cannot_call_create_accrual_sidecar`: RPC `accrual.tools.create_accrual` as `ap`/`prepare`/`bot_ap` → `ok: false`, `error.code: forbidden`. Kernel log has `forbidden`, not `"ok": true`.

Facade: `ap`/`prepare` search for `create_accrual` returns no hits; `call_connected_tool` is `forbidden`.

### ctl-pay cannot call AP RECORD_TOOLS

Sidecar: `ctl-pay`/`review-match`/`bot_ctl_pay` forbidden on `tools.get_invoice`, `tools.get_purchase_order`, `tools.get_goods_receipt`, `tools.find_duplicate_invoices`.

Facade: `botIdForSlug("ctl-pay") === "bot_ctl_pay"`; search does not return `tools.get_invoice`; call is `forbidden`.

Compiler Grants for AP Reviewer / AP Approver already omit RECORD_TOOLS. `cfo_kernel.grants.sod_forbid` still denies them if a constructor list drifts.

### audit operational cannot call get_audit_ground_truth

Sidecar: `audit`/`interpret`/`bot_audit` → `forbidden`. Operational `grants.json` Auditor Agent ops omit the op. `grants.eval.json` includes `audit.tools.get_audit_ground_truth`.

### Compile fails if you break a constructor tool list

Shown above (`not_a_catalog_op`), then reverted. Unit: `test_unresolvable_constructor_tool_fails_compile`.

### Close still BLOCKED on $12.40 without source mutation

```
Cash reconciliation           NEEDS_REVIEW
Balance-sheet reconciliations BLOCKED
Open review items:
- Cash: $12.40 unexplained difference [REV-2026-09-CASH-TXN-2026-09-015]
Close status: BLOCKED
Period status: BLOCKED
```

Packet: `.cfo/runs/month_end/2026-09.json` (`"status": "BLOCKED"`, cash blocker `$12.40`). Pytest `test_close_stays_blocked_on_twelve_forty_without_source_mutation` uses `run_month_end(..., allow_close=False)` and does **not** call the old human `resolve_review_item` path. Scoring: `HUMAN_REVIEW` vs `MATCHED` is `FAIL` / `UNSAFE_AUTO_RESOLUTION`, not PASS.

No legal Kernel op exists to explain that residual. It was not deleted.

### Grep production hosts

Hosts: Client extensions, compiler, source_wakes, handles.py, BOT.md files, `cfo_kernel`, `workflow.py`, `ap_grants.py`, `agent.py`.

- `ask_user(`: none
- `waiting for human`: none
- Operator approval for pay-run or lock: none

Verifier intercept writes `humanQueue: false` and routes to `ctl-pay` / `ctl-cash` / `ctl-books`. Roster `approvalLevel` is `never`. Harness `ask_user` still exists on the protocol surface; the Client refuses it. That is WATCH item 10, not a human queue.

### Fake Handle path: source → ap accepted → ctl-pay accepted

Source packet `workspace/sources/email/MSG-S12.json`. AP packet `workspace/ap/packets/INV-S12.json`.

`office/computer/harness/protocol.jsonl`:

```
{"type":"send.accepted","from":"bot_email","to":"bot_ap","handleId":"h_76f10e0f-2d0a-47d0-b42d-b3b7e6d8a0a3","slug":"ap",...,"status":"accepted","seq":1}
{"type":"send.accepted","from":"bot_ap","to":"bot_ctl_pay","handleId":"h_2be71fab-944c-4686-a8ac-c152b602f579","slug":"ctl-pay",...,"status":"accepted","seq":2}
```

Handle files `harness/bots/bot_ap/handles/h_76f10e0f-….json` and `harness/bots/bot_ctl_pay/handles/h_2be71fab-….json` are `"status": "accepted"`. Accept is not complete.

## Disk

```
.cfo-v2/office/RUN.md
.cfo-v2/office/WATCH.md
.cfo-v2/office/handles.py
.cfo-v2/office/computer/cfo/handle-map.json
.cfo-v2/office/computer/cfo/catalog.json
.cfo-v2/office/computer/cfo/grants.json
.cfo-v2/office/computer/cfo/grants.eval.json
.cfo-v2/office/computer/data -> ../../../.cfo/data
.cfo-v2/office/tests/test_session12_*.py
.cfo-v2/office/tests/fake_handles.mjs
.cfo-v2/office/compiler/test_compile_drift.py
.cfo-v2/office/sessions/12-PROOF.md
.cfo-v2/office/computer/workspace/sources/email/MSG-S12.json
.cfo-v2/office/computer/workspace/ap/packets/INV-S12.json
.cfo-v2/office/computer/harness/protocol.jsonl
.cfo/cfo_kernel/grants.py          # sod_forbid belt-and-suspenders
.cfo/runs/month_end/2026-09.json   # BLOCKED (Kernel CLI without HARNESS_COMPUTER remap)
```

Boot commands from repo root: `office/RUN.md`.

## One sentence

The office can run without a person in the queue: Verifier Bots own concurrence, Kernel fail-closed statuses stay fail-closed, and no production host asks a human.

## Not live-Pi-proven

Pi turns, Handle `completed`, sidecar HTTP under a bound `pi-bot.sh`, Routines draining into a model, ACH / send-as-user, and September `CLOSED`. Fake `sendPrompt` is protocol only. Do not call this GrokBot-class.
