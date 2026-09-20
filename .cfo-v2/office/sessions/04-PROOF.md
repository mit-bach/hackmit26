# Session 04 proof — Operator Bot `ap`

Migrate AP matching off the five-lane in-process chain. Bot `ap` wears Profiles `prepare` and `investigate`. Concurrence is `ctl-pay` / `review-match`. Cash does not leave this Bot.

Handle completion was **not** live-proven. No Pi turn ran. Proofs are Kernel / unit.

## Commands

From `.cfo/`:

```bash
.venv/bin/python -m pytest tests/test_workflow.py tests/test_deterministic.py tests/test_ingestion_ap.py tests/test_scheduling.py tests/test_cfo_integration.py::test_duplicate_invoice_never_becomes_payment tests/test_close.py::test_live_ap_is_limited_to_featured_invoices tests/test_close.py::test_deterministic_close_uses_policy_not_stale_traces tests/test_close.py::test_existing_ap_lookup_unchanged -q
```

Result: **55 passed**.

Kernel facts (same interpreter):

```text
INV-001 exceptions=[] kernel_allow=True must_hold=[]
INV-018 exceptions=['duplicate'] kernel_allow=False must_hold=['P-002 duplicate vendor invoice number']
prepare cannot call tools.get_company_policies / find_relevant_policies / get_prior_cases
ap/prepare and ap/investigate cannot call accrual.tools.create_accrual, accrual.tools.reconcile_accrual_with_invoice, scheduling.tools.release_pay_run
Bot ap does not wear Profile review-match
```

`ask_user(` is absent from `.cfo/workflow.py`, `.cfo/agent.py`, `.cfo/ap_grants.py`, `.cfo/tools.py`. `Runner.run_sync` is absent from `.cfo/workflow.py`.

## Disk

```
.cfo-v2/office/bots/ap/BOT.md                 (93 lines)
.cfo-v2/office/bots/ap/profiles/prepare.md
.cfo-v2/office/bots/ap/profiles/investigate.md
.cfo-v2/office/bots/ap/NOTES.md
.cfo-v2/office/bots/ap/roster.json
.cfo-v2/office/computer/cfo/grants.ap.json
.cfo-v2/office/computer/cfo/slug-map.ap.json
.cfo-v2/office/computer/skills/three-way-match-analysis/SKILL.md
.cfo-v2/office/computer/skills/ap-exception-investigation/SKILL.md
.cfo-v2/office/computer/harness/roster.json   (bot_ap approvalLevel=never; connectors=prepare RECORD ops)
.cfo-v2/office/sessions/04-PROOF.md
```

Kernel host (lives in `.cfo/` so existing tests import it):

```
.cfo/ap_grants.py
.cfo/workflow.py     # wake prepare, maybe investigate, packet, ctl-pay Handle payload, no pool write
.cfo/agent.py        # AP_PROFILE_AGENTS prepare/investigate only
.cfo/models.py       # reviewer/approver/audit optional on DecisionTrace
```

A mocked INV-001 run writes:

- `runs/ap/wakes/INV-001-prepare.json`
- `runs/ap/packets/INV-001.evidence.json`
- `runs/ap/packets/INV-001.json`
- `runs/ap/handles/INV-001.json` with `toSlug=ctl-pay`, `profile=review-match`, `verifier_missing=true`
- `posted_to_pool=false`

A mocked INV-018 run HOLDs under Kernel `must_hold` P-002 and writes **no** approve-shaped Handle.

## Grants

Compiled `cfo/grants.json` already matches constructors. Slug-map `ap` profiles are only `prepare` → AP Preparer and `investigate` → Exception Investigator. Reviewer / Approver / Audit stay on `ctl-pay`.

## Not proven live

Pi `bot_send_prompt` / `bot_await_turn` against a running `ctl-pay` lane. Session 09 owns that Bot. The host writes the Handle payload and stops.
