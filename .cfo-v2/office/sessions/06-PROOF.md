# Session 06 proof — Operator Bots `apply` and `collect`

Migrate AR cash application and collections onto two Bots. They are different open items. Collections cannot run ahead of application. Material or ambiguous apply goes to `ctl-cash` / `review-apply`. Write-off or reserve goes to `ctl-pay`. No person in the queue.

Handle completion was **not** live-proven. No Pi turn ran. Proofs are Kernel / unit.

## Commands

From `.cfo/`:

```bash
.venv/bin/pytest tests/test_ar.py tests/test_ar_review.py tests/test_ar_harness.py tests/test_skills.py tests/test_cli.py tests/test_forecast_ar.py -q
```

Result: **75 passed**.

Session 06 proof subset:

```bash
.venv/bin/pytest tests/test_ar_harness.py tests/test_ar.py::test_demo_is_deterministic tests/test_ar.py::test_cash_ambiguous_and_unidentified_do_not_post tests/test_ar.py::test_collections_blocks_paid_dispute_cooldown_and_promise tests/test_ar.py::test_collections_policy_rejects_illegal_agent_action -v
```

Result: **9 passed**.

Kernel facts (isolated AR state):

```text
PAY-AMBIGUOUS / PAY-005 decision=HUMAN_REVIEW posted=False
queue_owner=ctl-cash profile=review-apply human_queue=False
open_human_reviews=[]
Handle toSlug=ctl-cash kernelStatus=HUMAN_REVIEW humanQueue=false
apply cannot call accrual.tools.create_accrual
apply cannot call scheduling.tools.get_approved_pool
apply cannot call ar.tools.get_collection_candidates
collect cannot call ar.tools.get_cash_application_facts
run_collections before drain: blocked=True decisions=0 Handle apply
run_collections after drain: blocked=False INV-AR-020=ESCALATE_DISPUTE INV-AR-045 absent
runs/ar/state.json remains the SoT (atomic replace)
```

`ask_user` is absent from `.cfo/ar/`. `ar-review-correct` remains an emergency Kernel door. It is not the demo success path.

## Disk

```
.cfo-v2/office/bots/apply/BOT.md
.cfo-v2/office/bots/apply/profiles/apply.md
.cfo-v2/office/bots/apply/roster.json
.cfo-v2/office/bots/apply/NOTES.md
.cfo-v2/office/bots/collect/BOT.md
.cfo-v2/office/bots/collect/profiles/chase.md
.cfo-v2/office/bots/collect/roster.json
.cfo-v2/office/bots/collect/NOTES.md
.cfo-v2/office/computer/cfo/grants.apply.json
.cfo-v2/office/computer/cfo/grants-fragments/apply-collect.json
.cfo-v2/office/computer/cfo/slug-map-fragment.json
.cfo-v2/office/computer/harness/roster.json          # apply/collect connectors filled; daily-aging prompt
.cfo-v2/office/computer/skills/cash-application/SKILL.md
.cfo-v2/office/computer/skills/ar-collections-policy/SKILL.md
.cfo-v2/office/sessions/06-PROOF.md
```

Kernel (`.cfo/ar/`):

```
grants.py      # Profile allowlists. Skills never grant tools
drain.py       # new_deposits / mark_apply_drained / dirty-cash check
handles.py     # ctl-cash and collect-drain payloads, atomic JSON
store.py       # atomic state.json via atomic_json.write_json_atomic
workflow.py    # apply then collect; HUMAN_REVIEW enqueues Verifier Handle
review.py      # queue_owner ctl-cash, human_queue false
collections.py # enforce blocks SEND while unapplied cash may be theirs
agents.py      # Display-name prompts; output_type names unchanged
```

Slug-map already maps `apply`/`apply` → Cash Application Agent and `collect`/`chase` → Collections Agent. Cash Application Reviewer stays on `ctl-cash` / `review-apply`.

Room `cash` members: `apply`, `collect`, `cash`, `ctl-cash` (4, within 2–6).

## Not proven live

Pi `bot_send_prompt` / await done against running `apply`, `collect`, or `ctl-cash` lanes. The host writes the Handle payload and stops.
