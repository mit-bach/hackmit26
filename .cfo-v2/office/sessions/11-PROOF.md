# Session 11 proof

Assurance Bot `audit` with Profiles `interpret` and `report`. After-the-fact. Not a pay-path Verifier. Production Grants omit `get_audit_ground_truth`. Handle completion was not live-proven. Pi was not live-proven.

Client root: `.cfo-v2/`. Computer: `.cfo-v2/office/computer`.

## Commands

Compile (always writes operational `grants.json` and evaluation `grants.eval.json`):

```bash
PYTHONPATH=.cfo-v2/office/compiler python3 .cfo-v2/office/compiler/__main__.py --phase operational
```

Result (truncated):

```
cfo-catalog compile ok  phase=operational
  catalog ops: 80
  display names: 43
  wrote …/cfo/grants.json (operational)
  wrote …/cfo/grants.eval.json (evaluation)
  AP Preparer == AP Approver: no
  Auditor Agent get_audit_ground_truth operational: omitted
  Auditor Agent get_audit_ground_truth evaluation: ['audit.tools.get_audit_ground_truth']
```

Grant recompile also applied existing session 09 `grantDenylist` on Payment Audit (stripped pool/candidate rebuild ops). Constructor still lists those tools. Denylist is in `catalog.overrides.json`.

Tests (Kernel venv):

```bash
.cfo/.venv/bin/python -m pytest \
  .cfo-v2/office/bots/audit/test_audit_bot.py \
  .cfo-v2/office/compiler/test_compile_eval_split.py \
  .cfo/tests/test_audit.py -q
```

Result: `22 passed`.

Pi facade refuse (no Sidecar, no live Handle):

```bash
cd .cfo-v2/office/computer/cfo/extensions
node --experimental-strip-types --input-type=module -e '…bindBot audit/interpret…refuseConnectedTool…'
```

Result:

```
create_accrual: forbidden
get_audit_ground_truth: forbidden
write path runs/ar/state.json: forbidden
get_operational_decisions (no path): allowed
search "ground_truth": []
grantHasGround: false
```

## Proofs required by the session

| Claim | Evidence |
| --- | --- |
| Operational grant file does not contain `get_audit_ground_truth` | Ripgrep of `office/computer/cfo/grants.json`: no matches. Auditor Agent has nine read ops. Audit Report Agent `ops: []`. |
| Eval Grants keep the tool | `office/computer/cfo/grants.eval.json` Auditor Agent extra op is only `audit.tools.get_audit_ground_truth`. Live Bots bind `grants.json`. |
| Planted issues surface as findings without mutating AP source invoices | `.cfo/tests/test_audit.py` (`test_full_audit_eval_catches_planted_cases`, `test_findings_and_report_counts_stay_linked`) plus `test_planted_issues_surface_without_mutating_ap_invoices`. `invoices.json` bytes unchanged. `source_records_mutated` is false. 10 planted exceptions, 0 false negatives. |
| `audit` cannot `create_accrual` | `GrantError` / TS `forbidden`. Not on interpret or report Grants. |
| `audit` cannot write `runs/ar/state.json` | `PathLeaseError`. Host run left a planted AR state file untouched. Writes only under `workspace/audit/` and `runs/audit/` (plus lease files under `harness/leases/`). |

## Disk (session 11)

```
.cfo-v2/office/bots/audit/BOT.md
.cfo-v2/office/bots/audit/profiles/interpret.md
.cfo-v2/office/bots/audit/profiles/report.md
.cfo-v2/office/bots/audit/routines/post-close-assurance.md
.cfo-v2/office/bots/audit/grants.fragment.json
.cfo-v2/office/bots/audit/grants.eval.fragment.json
.cfo-v2/office/bots/audit/grants.py
.cfo-v2/office/bots/audit/paths.py
.cfo-v2/office/bots/audit/host.py
.cfo-v2/office/bots/audit/test_audit_bot.py
.cfo-v2/office/bots/audit/NOTES.md
.cfo-v2/office/computer/cfo/grants.json
.cfo-v2/office/computer/cfo/grants.eval.json
.cfo-v2/office/computer/cfo/path-leases.json
.cfo-v2/office/computer/cfo/extensions/call.ts
.cfo-v2/office/computer/cfo/extensions/paths.ts
.cfo-v2/office/computer/harness/bots/bot_audit/memory/MEMORY.md
.cfo-v2/office/computer/skills/audit-*/SKILL.md
.cfo-v2/office/sessions/11-PROOF.md
```

Roster Routine `post-close-assurance` still owns Bot `audit`, conversation `room:books-close`, `approvalLevel` never. Wake names Profile `interpret`, the pack path, and `bot_get_agent_transcript_tail`. Self-Handle to Profile `report` is on the host next-wake packet. Peer Handle is not approval. This Bot does not concur for `ctl-*`.

Python still samples and re-performs (`audit.workflow.run_audit`). The Bot interprets Kernel finding IDs (`AuditorInterpretation`) and writes report language from `ReportStats` (`AuditReportAgentOutput`).

## Not live-proven

- Bound Pi (`HARNESS_BOT=audit`)
- Harness `bot_send_prompt` / `bot_await_turn` / `bot_get_agent_transcript_tail` against a running process
- Sidecar RPC (`python -m cfo_kernel`)

Grant refuse and path leases are proven at the Client/Kernel unit layer. See `office/bots/audit/NOTES.md`.
